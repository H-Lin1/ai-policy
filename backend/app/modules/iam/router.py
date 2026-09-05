from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    COMMON_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
)
from app.core.errors import AppError
from app.core.config import Settings, get_settings
from app.core.database import request_db_session
from app.core.local_auth import issue_token, verify_password

from .models import User
from .schemas import LocalLoginRequest, LocalLoginResponse, RoleCode, WorkspaceResponse
from .service import IdentityContext, get_current_identity, role_title

NO_STORE = "no-store"

router = APIRouter(prefix="/iam", tags=["identity-access"])


@router.post(
    "/login",
    response_model=LocalLoginResponse,
    summary="本地账号登录",
    operation_id="localLogin",
    responses=COMMON_ERROR_RESPONSES,
)
def local_login(
    payload: LocalLoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    session: Session | None = Depends(request_db_session),
) -> LocalLoginResponse:
    response.headers["Cache-Control"] = NO_STORE
    if settings.auth_mode != "local":
        raise AppError("ROUTE_NOT_FOUND", "请求的接口不存在", status_code=404)
    if session is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    username = payload.username.strip()
    account = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if account is None or not account.is_active or not verify_password(payload.password, account.password_hash):
        raise AppError("AUTH_INVALID", "账号或密码错误", status_code=401)
    token, expires_in = issue_token(user_id=account.id, username=account.username, settings=settings)
    return LocalLoginResponse(access_token=token, expires_in=expires_in)


@router.get(
    "/workspaces/{role}",
    response_model=WorkspaceResponse,
    summary="角色工作区访问检查",
    operation_id="iamWorkspaceAccess",
    responses={**COMMON_ERROR_RESPONSES, **AUTH_ERROR_RESPONSES, **IDENTITY_ERROR_RESPONSES},
)
def workspace_access(
    response: Response,
    role: RoleCode = Path(description="请求进入的稳定角色代码"),
    identity: IdentityContext = Depends(get_current_identity),
) -> WorkspaceResponse:
    response.headers["Cache-Control"] = NO_STORE
    if role not in identity.role_codes:
        raise AppError("ROLE_FORBIDDEN", "当前身份无权进入该工作区", status_code=403)
    return WorkspaceResponse(
        role=role,
        title=role_title(role),
        subject=identity.subject,
        region=(
            {"code": identity.region_code, "name": identity.region_name}
            if identity.region_code and identity.region_name
            else None
        ),
        organization=(
            {
                "code": identity.organization_code,
                "name": identity.organization_name,
                "organization_type": identity.organization_type,
            }
            if identity.organization_code and identity.organization_name and identity.organization_type
            else None
        ),
    )
