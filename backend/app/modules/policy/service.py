from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import request_db_session
from app.core.errors import AppError
from app.modules.iam.service import IdentityContext

from .repository import FixturePolicyRepository, PolicyQuery, PolicyRecord, PolicyRepository

logger = logging.getLogger("ai_policy.policy")


def policy_repository_dependency(
    settings: Settings = Depends(get_settings),
    session: Session | None = Depends(request_db_session),
) -> Iterator[PolicyRepository | FixturePolicyRepository | None]:
    if settings.policy_fixture_path and not settings.database_url:
        try:
            yield FixturePolicyRepository.from_jsonl(Path(settings.policy_fixture_path))
        except Exception:  # noqa: BLE001 - fixture failures stay generic.
            logger.error("policy_fixture_unavailable")
            yield None
        return
    if session is None:
        yield None
        return
    yield PolicyRepository(session)


def _ensure_policy_scope(identity: IdentityContext) -> None:
    if identity.development_bypass:
        return
    if identity.region_code != "sz":
        raise AppError("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内", status_code=403)


def list_policies(
    *,
    identity: IdentityContext,
    repository: PolicyRepository | FixturePolicyRepository | None,
    offset: int,
    limit: int,
    query: str | None,
) -> PolicyQuery:
    _ensure_policy_scope(identity)
    if repository is None:
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503)
    try:
        return repository.list(offset=offset, limit=limit, query=query)
    except SQLAlchemyError as exc:
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503) from exc
    except Exception as exc:
        if isinstance(exc, AppError):
            raise
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503) from exc


def get_policy(
    *,
    identity: IdentityContext,
    repository: PolicyRepository | FixturePolicyRepository | None,
    policy_id: UUID,
) -> PolicyRecord:
    _ensure_policy_scope(identity)
    if repository is None:
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503)
    try:
        record = repository.get(policy_id)
    except SQLAlchemyError as exc:
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503) from exc
    except Exception as exc:
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503) from exc
    if record is None:
        raise AppError("POLICY_NOT_FOUND", "政策记录不存在", status_code=404)
    return record
