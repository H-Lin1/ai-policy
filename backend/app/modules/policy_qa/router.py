from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    COMMON_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
    error_response,
)
from app.core.errors import AppError
from app.modules.iam.service import IdentityContext, get_current_identity

from .adapters import PolicyAnswerEngine, build_policy_answer_engine
from .schemas import PolicyAnswerRequest, PolicyAnswerResponse
from .service import answer_policy_question

NO_STORE = "no-store"
router = APIRouter(prefix="/policy-answers", tags=["policy-qa"])
ERRORS = {
    **COMMON_ERROR_RESPONSES,
    **AUTH_ERROR_RESPONSES,
    **IDENTITY_ERROR_RESPONSES,
    503: error_response("政策智能问答暂不可用", code="POLICY_ANSWER_UNAVAILABLE"),
}


def policy_answer_engine_dependency() -> PolicyAnswerEngine:
    return build_policy_answer_engine()


@router.post(
    "",
    response_model=PolicyAnswerResponse,
    summary="政策智能问答",
    operation_id="answerPolicyQuestion",
    responses=ERRORS,
)
def create_policy_answer(
    payload: PolicyAnswerRequest,
    response: Response,
    identity: IdentityContext = Depends(get_current_identity),
    engine: PolicyAnswerEngine = Depends(policy_answer_engine_dependency),
) -> PolicyAnswerResponse:
    response.headers["Cache-Control"] = NO_STORE
    try:
        return answer_policy_question(identity=identity, engine=engine, question=payload.question)
    except AppError as exc:
        exc.headers = {**(exc.headers or {}), "Cache-Control": NO_STORE}
        raise
