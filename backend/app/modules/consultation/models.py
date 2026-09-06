from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConsultationDepartment(Base):
    """The persisted, authorized directory behind the classifier label map."""

    __tablename__ = "consultation_departments"
    __table_args__ = (
        CheckConstraint("length(btrim(department_id)) > 0", name="ck_consultation_department_id"),
        CheckConstraint("length(btrim(department_name)) > 0", name="ck_consultation_department_name"),
        {"schema": "app"},
    )

    department_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(160), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("app.organizations.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    government_user_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="RESTRICT"),
        unique=True,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class Consultation(Base):
    __tablename__ = "consultations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('submitted', 'assigned', 'replied', 'published', 'closed')",
            name="ck_consultations_status",
        ),
        CheckConstraint("length(btrim(question_text)) > 0", name="ck_consultations_question"),
        CheckConstraint(
            "answer_text IS NULL OR length(btrim(answer_text)) > 0",
            name="ck_consultations_answer",
        ),
        Index("ix_consultations_requester_created", "requester_user_id", "created_at"),
        Index("ix_consultations_assignee_created", "assigned_user_id", "created_at"),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    requester_user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="RESTRICT"), nullable=False
    )
    selected_department_id: Mapped[str] = mapped_column(
        String(96), ForeignKey("app.consultation_departments.department_id", ondelete="RESTRICT"), nullable=False
    )
    assigned_organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.organizations.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="RESTRICT"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'assigned'"))
    classification_model_version: Mapped[str] = mapped_column(String(160), nullable=False)
    classification_predictions: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text)
    publish_to_history: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    public_question_text: Mapped[str | None] = mapped_column(Text)
    public_answer_text: Mapped[str | None] = mapped_column(Text)
    historical_qa_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.historical_qa.id", ondelete="RESTRICT"), unique=True
    )
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class ConsultationEvent(Base):
    __tablename__ = "consultation_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('submitted', 'assigned', 'replied', 'published', 'closed')",
            name="ck_consultation_events_type",
        ),
        Index("ix_consultation_events_consultation_created", "consultation_id", "created_at"),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    consultation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.consultations.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
