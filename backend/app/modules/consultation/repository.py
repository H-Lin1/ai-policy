from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.historical_qa.models import HistoricalQa
from app.modules.iam.models import Organization, Profile, Role, UserRole

from .models import Consultation, ConsultationDepartment, ConsultationEvent


@dataclass(frozen=True)
class DepartmentRecord:
    department_id: str
    department_name: str
    organization_id: UUID
    government_user_id: UUID


@dataclass(frozen=True)
class ConsultationRecord:
    id: UUID
    requester_user_id: UUID
    selected_department_id: str
    selected_department_name: str
    assigned_organization_id: UUID
    assigned_user_id: UUID
    question_text: str
    status: str
    classification_predictions: dict[str, object]
    answer_text: str | None
    publish_to_history: bool
    historical_qa_id: UUID | None
    created_at: datetime
    replied_at: datetime | None
    closed_at: datetime | None


class ConsultationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_departments(self) -> list[DepartmentRecord]:
        rows = self.session.execute(
            select(ConsultationDepartment)
            .join(Organization, ConsultationDepartment.organization_id == Organization.id)
            .join(Profile, ConsultationDepartment.government_user_id == Profile.user_id)
            .where(ConsultationDepartment.is_active.is_(True), Organization.is_active.is_(True), Profile.status == "active")
            .order_by(ConsultationDepartment.department_name.asc())
        ).scalars()
        return [self._department(item) for item in rows]

    def department_for_selection(self, department_id: str) -> DepartmentRecord | None:
        item = self.session.execute(
            select(ConsultationDepartment)
            .join(Organization, ConsultationDepartment.organization_id == Organization.id)
            .join(Profile, ConsultationDepartment.government_user_id == Profile.user_id)
            .where(
                ConsultationDepartment.department_id == department_id,
                ConsultationDepartment.is_active.is_(True),
                Organization.is_active.is_(True),
                Profile.status == "active",
            )
            .with_for_update()
        ).scalar_one_or_none()
        return self._department(item) if item else None

    @staticmethod
    def _department(item: ConsultationDepartment) -> DepartmentRecord:
        return DepartmentRecord(
            department_id=item.department_id,
            department_name=item.department_name,
            organization_id=item.organization_id,
            government_user_id=item.government_user_id,
        )

    def create(self, *, requester_user_id: UUID, department: DepartmentRecord, question: str, model_version: str, predictions: dict[str, object]) -> Consultation:
        record = Consultation(
            requester_user_id=requester_user_id,
            selected_department_id=department.department_id,
            assigned_organization_id=department.organization_id,
            assigned_user_id=department.government_user_id,
            question_text=question,
            status="assigned",
            classification_model_version=model_version,
            classification_predictions=predictions,
        )
        self.session.add(record)
        self.session.flush()
        self.session.add_all([
            ConsultationEvent(consultation_id=record.id, event_type="submitted", actor_user_id=requester_user_id),
            ConsultationEvent(consultation_id=record.id, event_type="assigned", actor_user_id=None),
        ])
        return record

    def get(self, consultation_id: UUID, *, lock: bool = False) -> ConsultationRecord | None:
        statement = (
            select(Consultation, ConsultationDepartment.department_name)
            .join(ConsultationDepartment, Consultation.selected_department_id == ConsultationDepartment.department_id)
            .where(Consultation.id == consultation_id)
        )
        if lock:
            statement = statement.with_for_update()
        row = self.session.execute(statement).one_or_none()
        return self._consultation(*row) if row else None

    def list_for_requester(self, requester_user_id: UUID) -> list[ConsultationRecord]:
        rows = self.session.execute(
            select(Consultation, ConsultationDepartment.department_name)
            .join(ConsultationDepartment, Consultation.selected_department_id == ConsultationDepartment.department_id)
            .where(Consultation.requester_user_id == requester_user_id)
            .order_by(Consultation.created_at.desc())
        ).all()
        return [self._consultation(*row) for row in rows]

    def list_for_assignee(self, user_id: UUID) -> list[ConsultationRecord]:
        rows = self.session.execute(
            select(Consultation, ConsultationDepartment.department_name)
            .join(ConsultationDepartment, Consultation.selected_department_id == ConsultationDepartment.department_id)
            .where(Consultation.assigned_user_id == user_id)
            .order_by(Consultation.created_at.desc())
        ).all()
        return [self._consultation(*row) for row in rows]

    def assert_dedicated_government_account(self, *, user_id: UUID, organization_code: str | None) -> bool:
        if organization_code is None:
            return False
        statement = (
            select(ConsultationDepartment.department_id)
            .join(Organization, ConsultationDepartment.organization_id == Organization.id)
            .join(Profile, ConsultationDepartment.government_user_id == Profile.user_id)
            .join(UserRole, UserRole.user_id == Profile.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                ConsultationDepartment.government_user_id == user_id,
                Organization.code == organization_code,
                Organization.is_active.is_(True),
                Profile.status == "active",
                Role.code == "government",
                Role.is_active.is_(True),
                UserRole.is_active.is_(True),
            )
        )
        return self.session.execute(statement).scalar_one_or_none() is not None

    def complete_reply(self, *, consultation_id: UUID, actor_user_id: UUID, answer: str, public_question: str | None, public_answer: str | None, historical_qa: HistoricalQa | None) -> ConsultationRecord:
        record = self.session.get(Consultation, consultation_id, with_for_update=True)
        assert record is not None
        now = datetime.now().astimezone()
        record.answer_text = answer
        record.replied_at = now
        record.publish_to_history = historical_qa is not None
        record.public_question_text = public_question
        record.public_answer_text = public_answer
        self.session.add(ConsultationEvent(consultation_id=record.id, event_type="replied", actor_user_id=actor_user_id))
        if historical_qa is not None:
            self.session.add(historical_qa)
            self.session.flush()
            record.historical_qa_id = historical_qa.id
            self.session.add(ConsultationEvent(consultation_id=record.id, event_type="published", actor_user_id=actor_user_id))
        record.status = "closed"
        record.closed_at = now
        self.session.add(ConsultationEvent(consultation_id=record.id, event_type="closed", actor_user_id=actor_user_id))
        self.session.flush()
        return self.get(consultation_id)  # type: ignore[return-value]

    @staticmethod
    def _consultation(model: Consultation, department_name: str) -> ConsultationRecord:
        return ConsultationRecord(
            id=model.id, requester_user_id=model.requester_user_id, selected_department_id=model.selected_department_id,
            selected_department_name=department_name, assigned_organization_id=model.assigned_organization_id,
            assigned_user_id=model.assigned_user_id, question_text=model.question_text, status=model.status,
            classification_predictions=model.classification_predictions, answer_text=model.answer_text,
            publish_to_history=model.publish_to_history, historical_qa_id=model.historical_qa_id,
            created_at=model.created_at, replied_at=model.replied_at, closed_at=model.closed_at,
        )
