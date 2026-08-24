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

from .repository import (
    FixtureHistoricalQaRepository,
    HistoricalQaQuery,
    HistoricalQaRecord,
    HistoricalQaRepository,
)

logger = logging.getLogger("ai_policy.historical_qa")


def historical_qa_repository_dependency(
    settings: Settings = Depends(get_settings),
    session: Session | None = Depends(request_db_session),
) -> Iterator[HistoricalQaRepository | FixtureHistoricalQaRepository | None]:
    if settings.historical_qa_fixture_path and not settings.database_url:
        try:
            yield FixtureHistoricalQaRepository.from_jsonl(Path(settings.historical_qa_fixture_path))
        except Exception:  # noqa: BLE001 - fixture errors must not expose source text.
            logger.error("historical_qa_fixture_unavailable")
            yield None
        return
    if session is None:
        yield None
        return
    yield HistoricalQaRepository(session)


def _ensure_scope(identity: IdentityContext) -> None:
    if identity.development_bypass:
        return
    if identity.region_code != "sz":
        raise AppError("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内", status_code=403)


def list_historical_qa(
    *, identity: IdentityContext, repository: HistoricalQaRepository | FixtureHistoricalQaRepository | None,
    offset: int, limit: int, query: str | None,
) -> HistoricalQaQuery:
    _ensure_scope(identity)
    if repository is None:
        raise AppError("HISTORICAL_QA_STORE_UNAVAILABLE", "历史问答暂不可用", status_code=503)
    try:
        return repository.list(offset=offset, limit=limit, query=query)
    except SQLAlchemyError as exc:
        raise AppError("HISTORICAL_QA_STORE_UNAVAILABLE", "历史问答暂不可用", status_code=503) from exc
    except Exception as exc:
        raise AppError("HISTORICAL_QA_STORE_UNAVAILABLE", "历史问答暂不可用", status_code=503) from exc


def get_historical_qa(
    *, identity: IdentityContext, repository: HistoricalQaRepository | FixtureHistoricalQaRepository | None,
    qa_id: UUID,
) -> HistoricalQaRecord:
    _ensure_scope(identity)
    if repository is None:
        raise AppError("HISTORICAL_QA_STORE_UNAVAILABLE", "历史问答暂不可用", status_code=503)
    try:
        record = repository.get(qa_id)
    except SQLAlchemyError as exc:
        raise AppError("HISTORICAL_QA_STORE_UNAVAILABLE", "历史问答暂不可用", status_code=503) from exc
    except Exception as exc:
        raise AppError("HISTORICAL_QA_STORE_UNAVAILABLE", "历史问答暂不可用", status_code=503) from exc
    if record is None:
        raise AppError("HISTORICAL_QA_NOT_FOUND", "历史问答记录不存在", status_code=404)
    return record
