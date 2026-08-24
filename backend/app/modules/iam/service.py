from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import Principal, get_current_principal
from app.core.config import Settings, get_settings
from app.core.database import request_db_session
from app.core.errors import AppError

from .repository import IdentityRecord, IdentityRepository, RoleRecord
from .schemas import ROLE_CODES, RoleSummary

logger = logging.getLogger("ai_policy.iam")

ROLE_TITLES = {
    "individual": "个人服务工作区",
    "enterprise": "企业服务工作区",
    "government": "政府办理工作区",
    "admin": "平台管理工作区",
}
ROLE_ORGANIZATION_TYPES = {
    "enterprise": "enterprise",
    "government": "government",
    "admin": "platform",
}


@dataclass(frozen=True)
class IdentityContext:
    subject: str
    email: str | None
    display_name: str
    roles: tuple[RoleRecord, ...]
    region_code: str | None
    region_name: str | None
    organization_code: str | None
    organization_name: str | None
    organization_type: str | None
    development_bypass: bool = False

    @property
    def role_codes(self) -> tuple[str, ...]:
        return tuple(role.code for role in self.roles)


def identity_repository_dependency(
    settings: Settings = Depends(get_settings),
    session: Session | None = Depends(request_db_session),
) -> Iterator[IdentityRepository | None]:
    """Bind identity reads to the shared request-scoped database session."""

    if not settings.auth_required and not settings.is_production:
        yield None
        return
    if session is None:
        yield None
        return
    yield IdentityRepository(session)


def _inactive_scope_error(code: str, message: str) -> AppError:
    return AppError(code, message, status_code=403)


def _validate_record(record: IdentityRecord) -> tuple[RoleRecord, ...]:
    if record.profile_status != "active":
        raise _inactive_scope_error("ACCOUNT_DISABLED", "当前应用身份已停用")
    if record.region_code != "sz" or not record.region_active:
        raise _inactive_scope_error("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内")
    if record.organization_code is not None and (
        not record.organization_active or record.organization_region_id != record.profile_region_id
    ):
        raise _inactive_scope_error("IDENTITY_SCOPE_INACTIVE", "当前组织范围不可用")

    active_roles = tuple(
        role for role in record.roles if role.is_active and role.assignment_active and role.code in ROLE_CODES
    )
    if not active_roles:
        raise AppError("ROLE_NOT_ASSIGNED", "当前应用身份尚未分配有效角色", status_code=403)

    for role in active_roles:
        expected_type = ROLE_ORGANIZATION_TYPES.get(role.code)
        if expected_type and (
            record.organization_type is None or record.organization_type != expected_type
        ):
            raise _inactive_scope_error("IDENTITY_SCOPE_INACTIVE", "当前角色缺少匹配的组织范围")
    return active_roles


def resolve_identity(
    principal: Principal,
    repository: IdentityRepository | None,
) -> IdentityContext:
    if principal.development_bypass:
        return IdentityContext(
            subject=principal.subject,
            email=principal.email,
            display_name="本地开发身份",
            roles=(RoleRecord("developer", "本地开发", True, True),),
            region_code=None,
            region_name=None,
            organization_code=None,
            organization_name=None,
            organization_type=None,
            development_bypass=True,
        )
    try:
        user_id = UUID(principal.subject)
    except (TypeError, ValueError) as exc:
        raise AppError("AUTH_INVALID", "登录令牌缺少有效主体", status_code=401) from exc
    if repository is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)

    try:
        record = repository.load(user_id)
    except SQLAlchemyError as exc:
        logger.error("identity_store_query_failed")
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc
    except Exception as exc:
        logger.error("identity_store_query_failed")
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc
    if record is None:
        raise AppError("PROFILE_NOT_PROVISIONED", "当前登录身份尚未完成应用配置", status_code=403)

    active_roles = _validate_record(record)
    return IdentityContext(
        subject=str(record.user_id),
        email=principal.email,
        display_name=record.display_name,
        roles=active_roles,
        region_code=record.region_code,
        region_name=record.region_name,
        organization_code=record.organization_code,
        organization_name=record.organization_name,
        organization_type=record.organization_type,
    )


def get_current_identity(
    principal: Principal = Depends(get_current_principal),
    repository: IdentityRepository | None = Depends(identity_repository_dependency),
) -> IdentityContext:
    return resolve_identity(principal, repository)


def require_role(role_code: str):
    def dependency(identity: IdentityContext = Depends(get_current_identity)) -> IdentityContext:
        if role_code not in identity.role_codes:
            raise AppError("ROLE_FORBIDDEN", "当前身份无权进入该工作区", status_code=403)
        return identity

    return dependency


def role_title(role_code: str) -> str:
    return ROLE_TITLES.get(role_code, "受保护工作区")


def role_summaries(identity: IdentityContext) -> list[RoleSummary]:
    return [RoleSummary(code=role.code, name=role.name) for role in identity.roles]
