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
        CheckConstraint("length(btrim(source_url)) > 0", name="ck_policy_documents_source_url"),
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
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    document_url: Mapped[str | None] = mapped_column(Text)
    published_date: Mapped[date | None] = mapped_column(Date)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_status: Mapped[str | None] = mapped_column(String(32))
    requested_title: Mapped[str | None] = mapped_column(Text)
    reference_count: Mapped[int | None] = mapped_column(Integer)
    source_years: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
