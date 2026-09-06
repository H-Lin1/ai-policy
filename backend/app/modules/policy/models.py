from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    __table_args__ = (
        UniqueConstraint("source_url", "content_sha256", name="uq_policy_documents_source_hash"),
        CheckConstraint("length(btrim(title)) > 0", name="ck_policy_documents_title"),
        CheckConstraint("length(btrim(content_text)) > 0", name="ck_policy_documents_content"),
        CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name="ck_policy_documents_hash"),
        CheckConstraint("region_code = 'sz'", name="ck_policy_documents_region"),
        Index("ix_policy_documents_region_published", "region_code", "published_date"),
        Index("ix_policy_documents_title", "title"),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    region_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("app.regions.id", ondelete="RESTRICT"), nullable=False)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False, default="sz", server_default=text("'sz'"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    document_no: Mapped[str | None] = mapped_column(Text)
    issuing_organization: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    document_url: Mapped[str | None] = mapped_column(Text)
    published_date: Mapped[date | None] = mapped_column(Date)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_status: Mapped[str | None] = mapped_column(String(32))
    requested_title: Mapped[str | None] = mapped_column(Text)
    reference_count: Mapped[int | None] = mapped_column(Integer)
    source_years: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="external_url", server_default=text("'external_url'"))
    publication_status: Mapped[str] = mapped_column(String(32), nullable=False, default="published", server_default=text("'published'"))
    raw_markdown: Mapped[str | None] = mapped_column(Text)
    raw_markdown_sha256: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="RESTRICT"))
    published_by: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="RESTRICT"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_by: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="RESTRICT"))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class PolicyDocumentEvent(Base):
    __tablename__ = "policy_document_events"
    __table_args__ = (
        CheckConstraint("event_type IN ('drafted', 'published', 'withdrawn')", name="ck_policy_document_events_type"),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("app.policy_documents.id", ondelete="RESTRICT"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="RESTRICT"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
