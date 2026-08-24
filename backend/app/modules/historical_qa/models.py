from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HistoricalQa(Base):
    __tablename__ = "historical_qa"
    __table_args__ = (
        UniqueConstraint("source_url", "content_sha256", name="uq_historical_qa_source_hash"),
        CheckConstraint("length(btrim(topic)) > 0", name="ck_historical_qa_topic"),
        CheckConstraint("length(btrim(question_text)) > 0", name="ck_historical_qa_question"),
        CheckConstraint("length(btrim(answer_text)) > 0", name="ck_historical_qa_answer"),
        CheckConstraint("length(btrim(source_url)) > 0", name="ck_historical_qa_source_url"),
        CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name="ck_historical_qa_hash"),
        CheckConstraint("region_code = 'sz'", name="ck_historical_qa_region"),
        Index("ix_historical_qa_region_replied", "region_code", "replied_at"),
        Index("ix_historical_qa_topic", "topic"),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    region_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("app.regions.id", ondelete="RESTRICT"), nullable=False)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'sz'"))
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    question_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    publishing_organization: Mapped[str] = mapped_column(Text, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    contains_legal_basis: Mapped[bool] = mapped_column(nullable=False)
    legal_basis_name: Mapped[str | None] = mapped_column(Text)
    legal_basis_citation: Mapped[str | None] = mapped_column(Text)
    adjudication_result: Mapped[str] = mapped_column(String(32), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
