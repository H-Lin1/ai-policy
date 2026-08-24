from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    COMMON_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
    error_response,
)
from app.core.errors import AppError
from app.modules.iam.service import IdentityContext, get_current_identity
from app.modules.intelligence.adapters import DepartmentClassifier
from app.modules.system.router import classifier_dependency

from .repository import ConsultationRepository
from .schemas import (
    ConsultationDepartmentResponse,
    ConsultationResponse,
    CreateConsultationRequest,
    ReplyConsultationRequest,
)
from .service import (
    consultation_repository_dependency,
    create_consultation,
    get_consultation,
    list_consultations,
    list_departments,
    reply_to_consultation,
)

NO_STORE = "no-store"
router = APIRouter(prefix="/consultations", tags=["consultation"])
ERRORS = {
    **COMMON_ERROR_RESPONSES, **AUTH_ERROR_RESPONSES, **IDENTITY_ERROR_RESPONSES,
    404: error_response("咨询工单不存在", code="CONSULTATION_NOT_FOUND"),
    409: error_response("咨询工单不可重复办理", code="CONSULTATION_NOT_ACTIONABLE"),
    503: error_response("咨询服务暂不可用", code="CONSULTATION_STORE_UNAVAILABLE"),
}


@router.get("/departments", response_model=list[ConsultationDepartmentResponse], responses=ERRORS, operation_id="consultationDepartments")
def consultation_departments(response: Response, identity: IdentityContext = Depends(get_current_identity), repository: ConsultationRepository | None = Depends(consultation_repository_dependency)) -> list[ConsultationDepartmentResponse]:
    response.headers["Cache-Control"] = NO_STORE
    return list_departments(identity=identity, repository=repository)


@router.post("", response_model=ConsultationResponse, responses=ERRORS, operation_id="createConsultation")
def create_consultation_route(payload: CreateConsultationRequest, response: Response, identity: IdentityContext = Depends(get_current_identity), repository: ConsultationRepository | None = Depends(consultation_repository_dependency), classifier: DepartmentClassifier = Depends(classifier_dependency)) -> ConsultationResponse:
    response.headers["Cache-Control"] = NO_STORE
    try:
        return create_consultation(identity=identity, repository=repository, classifier=classifier, question=payload.question, selected_department_id=payload.selected_department_id)
    except AppError as exc:
        exc.headers = {**(exc.headers or {}), "Cache-Control": NO_STORE}
        raise


@router.get("", response_model=list[ConsultationResponse], responses=ERRORS, operation_id="consultationList")
def consultation_list(response: Response, identity: IdentityContext = Depends(get_current_identity), repository: ConsultationRepository | None = Depends(consultation_repository_dependency)) -> list[ConsultationResponse]:
    response.headers["Cache-Control"] = NO_STORE
    return list_consultations(identity=identity, repository=repository)


@router.get("/{consultation_id}", response_model=ConsultationResponse, responses=ERRORS, operation_id="consultationDetail")
def consultation_detail(consultation_id: UUID, response: Response, identity: IdentityContext = Depends(get_current_identity), repository: ConsultationRepository | None = Depends(consultation_repository_dependency)) -> ConsultationResponse:
    response.headers["Cache-Control"] = NO_STORE
    return get_consultation(identity=identity, repository=repository, consultation_id=consultation_id)


@router.post("/{consultation_id}/reply", response_model=ConsultationResponse, responses=ERRORS, operation_id="replyConsultation")
def consultation_reply(consultation_id: UUID, payload: ReplyConsultationRequest, response: Response, identity: IdentityContext = Depends(get_current_identity), repository: ConsultationRepository | None = Depends(consultation_repository_dependency)) -> ConsultationResponse:
    response.headers["Cache-Control"] = NO_STORE
    try:
        return reply_to_consultation(identity=identity, repository=repository, consultation_id=consultation_id, answer=payload.answer, publish_to_history=payload.publish_to_history, public_question=payload.public_question, public_answer=payload.public_answer)
    except AppError as exc:
        exc.headers = {**(exc.headers or {}), "Cache-Control": NO_STORE}
        raise
