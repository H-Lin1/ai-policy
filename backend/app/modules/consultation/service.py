from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import request_db_session
from app.core.errors import AppError
from app.modules.historical_qa.models import HistoricalQa
from app.modules.iam.service import IdentityContext
from app.modules.intelligence.adapters import ClassifierError, ClassifierInput, DepartmentClassifier

from .repository import ConsultationRecord, ConsultationRepository, DepartmentRecord
from .schemas import ConsultationDepartmentResponse, ConsultationPrediction, ConsultationResponse

logger = logging.getLogger("ai_policy.consultation")
_REQUESTER_ROLES = frozenset({"individual", "enterprise"})


def consultation_repository_dependency(
    settings: Settings = Depends(get_settings), session: Session | None = Depends(request_db_session)
) -> Iterator[ConsultationRepository | None]:
    if session is None or not settings.database_url:
        yield None
        return
    yield ConsultationRepository(session)


def _subject_id(identity: IdentityContext) -> UUID:
    try:
        return UUID(identity.subject)
    except (ValueError, TypeError) as exc:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc


def _ensure_sz(identity: IdentityContext) -> None:
    if identity.development_bypass or identity.region_code == "sz":
        return
    raise AppError("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内", status_code=403)


def _ensure_requester(identity: IdentityContext) -> UUID:
    _ensure_sz(identity)
    if not identity.development_bypass and not set(identity.role_codes).intersection(_REQUESTER_ROLES):
        raise AppError("ROLE_FORBIDDEN", "当前身份无权提交咨询", status_code=403)
    return _subject_id(identity)


def _ensure_government(identity: IdentityContext) -> UUID:
    _ensure_sz(identity)
    if not identity.development_bypass and "government" not in identity.role_codes:
        raise AppError("ROLE_FORBIDDEN", "当前身份无权办理咨询", status_code=403)
    return _subject_id(identity)


def _store(repository: ConsultationRepository | None) -> ConsultationRepository:
    if repository is None:
        raise AppError("CONSULTATION_STORE_UNAVAILABLE", "咨询服务暂不可用", status_code=503)
    return repository


def _predictions(classifier: DepartmentClassifier, question: str) -> tuple[str, list[ConsultationPrediction]]:
    try:
        result = classifier.classify(ClassifierInput(text=question, region_id="sz"))
        department_name = getattr(classifier, "department_name", None)
        if not callable(department_name) or result.region_id != "sz":
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果不可用")
        predictions = [
            ConsultationPrediction(
                department_id=item.department_id,
                department_name=department_name(item.department_id),
                confidence=item.confidence,
            )
            for item in result.predictions[:3]
        ]
        if not predictions:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果不可用")
        return result.model_version, predictions
    except ClassifierError as exc:
        if exc.code in {"TEXT_REQUIRED", "REGION_REQUIRED", "REGION_INVALID"}:
            raise AppError(exc.code, exc.message, status_code=422) from exc
        raise AppError("CLASSIFIER_INFERENCE_FAILED", "部门分类暂不可用", status_code=503) from exc
    except Exception as exc:
        logger.error("consultation_classification_failed")
        raise AppError("CLASSIFIER_INFERENCE_FAILED", "部门分类暂不可用", status_code=503) from exc


def list_departments(*, identity: IdentityContext, repository: ConsultationRepository | None) -> list[ConsultationDepartmentResponse]:
    _ensure_sz(identity)
    try:
        departments = _store(repository).list_departments()
    except SQLAlchemyError as exc:
        raise AppError("CONSULTATION_STORE_UNAVAILABLE", "咨询服务暂不可用", status_code=503) from exc
    return [ConsultationDepartmentResponse(department_id=item.department_id, department_name=item.department_name) for item in departments]


def create_consultation(*, identity: IdentityContext, repository: ConsultationRepository | None, classifier: DepartmentClassifier, question: str, selected_department_id: str) -> ConsultationResponse:
    requester_user_id = _ensure_requester(identity)
    store = _store(repository)
    question = question.strip()
    model_version, predictions = _predictions(classifier, question)
    try:
        department = store.department_for_selection(selected_department_id)
        if department is None:
            raise AppError("CONSULTATION_DEPARTMENT_NOT_AVAILABLE", "所选部门当前不可办理咨询", status_code=422)
        prediction_payload = {"items": [item.model_dump() for item in predictions]}
        record = store.create(requester_user_id=requester_user_id, department=department, question=question, model_version=model_version, predictions=prediction_payload)
        store.session.commit()
        store.session.refresh(record)
        return _response_from_create(record, department, predictions)
    except AppError:
        store.session.rollback()
        raise
    except SQLAlchemyError as exc:
        store.session.rollback()
        raise AppError("CONSULTATION_STORE_UNAVAILABLE", "咨询服务暂不可用", status_code=503) from exc


def _response_from_create(record, department: DepartmentRecord, predictions: list[ConsultationPrediction]) -> ConsultationResponse:
    return ConsultationResponse(
        id=record.id, selected_department=ConsultationDepartmentResponse(department_id=department.department_id, department_name=department.department_name),
        status="assigned", question_text=record.question_text, recommendations=predictions,
        created_at=record.created_at, assigned_at=record.created_at,
    )


def _response(record: ConsultationRecord) -> ConsultationResponse:
    predictions = [ConsultationPrediction.model_validate(item) for item in record.classification_predictions.get("items", [])]
    if not predictions:
        raise AppError("CONSULTATION_STORE_UNAVAILABLE", "咨询服务暂不可用", status_code=503)
    return ConsultationResponse(
        id=record.id, selected_department=ConsultationDepartmentResponse(department_id=record.selected_department_id, department_name=record.selected_department_name),
        status="closed" if record.status == "closed" else "assigned", question_text=record.question_text,
        recommendations=predictions[:3], created_at=record.created_at, assigned_at=record.created_at,
        answer_text=record.answer_text, publish_to_history=record.publish_to_history,
        historical_qa_id=record.historical_qa_id, replied_at=record.replied_at, closed_at=record.closed_at,
    )


def list_consultations(*, identity: IdentityContext, repository: ConsultationRepository | None) -> list[ConsultationResponse]:
    _ensure_sz(identity)
    store = _store(repository)
    user_id = _subject_id(identity)
    try:
        if identity.development_bypass or set(identity.role_codes).intersection(_REQUESTER_ROLES):
            records = store.list_for_requester(user_id)
        elif "government" in identity.role_codes:
            if not store.assert_dedicated_government_account(user_id=user_id, organization_code=identity.organization_code):
                raise AppError("CONSULTATION_ACCOUNT_NOT_BOUND", "当前政府账号未绑定可办理部门", status_code=403)
            records = store.list_for_assignee(user_id)
        else:
            raise AppError("ROLE_FORBIDDEN", "当前身份无权查看咨询", status_code=403)
        return [_response(item) for item in records]
    except AppError:
        raise
    except SQLAlchemyError as exc:
        raise AppError("CONSULTATION_STORE_UNAVAILABLE", "咨询服务暂不可用", status_code=503) from exc


def get_consultation(*, identity: IdentityContext, repository: ConsultationRepository | None, consultation_id: UUID) -> ConsultationResponse:
    _ensure_sz(identity)
    store = _store(repository)
    user_id = _subject_id(identity)
    try:
        record = store.get(consultation_id)
        if record is None:
            raise AppError("CONSULTATION_NOT_FOUND", "咨询工单不存在", status_code=404)
        if record.requester_user_id != user_id and record.assigned_user_id != user_id and not identity.development_bypass:
            raise AppError("CONSULTATION_FORBIDDEN", "当前身份无权查看该咨询", status_code=403)
        return _response(record)
    except AppError:
        raise
    except SQLAlchemyError as exc:
        raise AppError("CONSULTATION_STORE_UNAVAILABLE", "咨询服务暂不可用", status_code=503) from exc


def reply_to_consultation(*, identity: IdentityContext, repository: ConsultationRepository | None, consultation_id: UUID, answer: str, publish_to_history: bool, public_question: str | None, public_answer: str | None) -> ConsultationResponse:
    actor_user_id = _ensure_government(identity)
    store = _store(repository)
    try:
        if not identity.development_bypass and not store.assert_dedicated_government_account(user_id=actor_user_id, organization_code=identity.organization_code):
            raise AppError("CONSULTATION_ACCOUNT_NOT_BOUND", "当前政府账号未绑定可办理部门", status_code=403)
        record = store.get(consultation_id, lock=True)
        if record is None:
            raise AppError("CONSULTATION_NOT_FOUND", "咨询工单不存在", status_code=404)
        if not identity.development_bypass and record.assigned_user_id != actor_user_id:
            raise AppError("CONSULTATION_FORBIDDEN", "仅被指派部门账号可以办理该咨询", status_code=403)
        if record.status != "assigned":
            raise AppError("CONSULTATION_NOT_ACTIONABLE", "该咨询已办结，不能重复答复", status_code=409)
        question_for_public = public_question.strip() if isinstance(public_question, str) else None
        answer_for_public = public_answer.strip() if isinstance(public_answer, str) else None
        if publish_to_history and (not question_for_public or not answer_for_public):
            raise AppError("CONSULTATION_PUBLIC_PROJECTION_REQUIRED", "公开前须提供去标识化的问题和答复版本", status_code=422)
        historical = _public_projection(record, answer_for_public, question_for_public) if publish_to_history else None
        completed = store.complete_reply(consultation_id=consultation_id, actor_user_id=actor_user_id, answer=answer.strip(), public_question=question_for_public, public_answer=answer_for_public, historical_qa=historical)
        store.session.commit()
        return _response(completed)
    except AppError:
        store.session.rollback()
        raise
    except SQLAlchemyError as exc:
        store.session.rollback()
        raise AppError("CONSULTATION_STORE_UNAVAILABLE", "咨询服务暂不可用", status_code=503) from exc


def _public_projection(record: ConsultationRecord, answer: str | None, question: str | None) -> HistoricalQa:
    assert question is not None and answer is not None
    payload = f"{question}\n{answer}".encode()
    digest = hashlib.sha256(payload).hexdigest()
    # This stable internal source reference is deliberately the only provenance exposed:
    # it contains no requester, actor, organization account, or history details.
    return HistoricalQa(
        region_id=UUID("10000000-0000-4000-8000-000000000001"), region_code="sz",
        topic=question[:120], question_text=question, answer_text=answer,
        source_url=f"consultation://public/{record.id}", question_at=record.created_at,
        replied_at=datetime.now(UTC), publishing_organization=record.selected_department_name,
        collected_at=datetime.now(UTC), contains_legal_basis=False, legal_basis_name=None,
        legal_basis_citation=None, adjudication_result="published", content_sha256=digest,
    )
