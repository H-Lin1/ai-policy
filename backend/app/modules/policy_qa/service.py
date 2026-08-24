from __future__ import annotations

import logging

from app.core.context import get_request_id
from app.core.errors import AppError
from app.modules.iam.service import IdentityContext

from .adapters import (
    PolicyAnswerEngine,
    PolicyAnswerError,
    PolicyQuestion,
    normalize_question,
)
from .schemas import PolicyAnswerResponse, PolicyAnswerSourceResponse

logger = logging.getLogger("ai_policy.policy_qa")
_ELIGIBLE_ROLES = frozenset({"individual", "enterprise"})


def _ensure_scope(identity: IdentityContext) -> tuple[str, ...]:
    if identity.development_bypass:
        return ("individual",)
    if identity.region_code != "sz":
        raise AppError("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内", status_code=403)
    role_codes = tuple(role for role in identity.role_codes if role in _ELIGIBLE_ROLES)
    if not role_codes:
        raise AppError("ROLE_FORBIDDEN", "当前身份无权使用政策智能问答", status_code=403)
    return role_codes


def _engine_error(exc: PolicyAnswerError) -> AppError:
    if exc.code in {"QUESTION_REQUIRED", "REGION_NOT_SUPPORTED"}:
        return AppError(exc.code, exc.message, status_code=422)
    return AppError("POLICY_ANSWER_UNAVAILABLE", "政策智能问答暂不可用", status_code=503)


def answer_policy_question(
    *, identity: IdentityContext, engine: PolicyAnswerEngine, question: str
) -> PolicyAnswerResponse:
    role_codes = _ensure_scope(identity)
    try:
        normalized_question = normalize_question(question)
        result = engine.answer(
            PolicyQuestion(
                question=normalized_question,
                region_id="sz",
                role_codes=role_codes,
            )
        )
    except PolicyAnswerError as exc:
        raise _engine_error(exc) from exc
    except Exception as exc:  # an engine cannot expose provider internals.
        logger.error("policy_answer_engine_failed")
        raise AppError(
            "POLICY_ANSWER_UNAVAILABLE", "政策智能问答暂不可用", status_code=503
        ) from exc

    return PolicyAnswerResponse(
        request_id=get_request_id(),
        region_id=result.region_id,
        answer_mode=result.answer_mode,
        answer=result.answer,
        sources=[
            PolicyAnswerSourceResponse(
                source_type=source.source_type,
                source_id=source.source_id,
                title=source.title,
                source_url=source.source_url,
                published_date=source.published_date,
                excerpt=source.excerpt,
            )
            for source in result.sources
        ],
        notices=list(result.notices),
    )
