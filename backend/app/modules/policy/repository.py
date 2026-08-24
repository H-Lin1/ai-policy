from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .models import PolicyDocument
from .source import PolicySourceRecord


@dataclass(frozen=True)
class PolicyQuery:
    items: list[PolicyListRecord]
    total: int


@dataclass(frozen=True)
class PolicyListRecord:
    id: UUID
    title: str
    document_no: str | None
    issuing_organization: str | None
    source_url: str
    published_date: date | None
    effective_status: str | None


@dataclass(frozen=True)
class PolicyRecord(PolicyListRecord):
    document_url: str | None
    collected_at: datetime
    content_text: str
    content_sha256: str
    requested_title: str | None
    reference_count: int | None
    source_years: str | None


def _record_from_model(model: PolicyDocument) -> PolicyRecord:
    return PolicyRecord(
        id=model.id,
        title=model.title,
        document_no=model.document_no,
        issuing_organization=model.issuing_organization,
        source_url=model.source_url,
        document_url=model.document_url,
        published_date=model.published_date,
        collected_at=model.collected_at,
        content_text=model.content_text,
        content_sha256=model.content_sha256,
        effective_status=model.effective_status,
        requested_title=model.requested_title,
        reference_count=model.reference_count,
        source_years=model.source_years,
    )


def _list_record_from_row(row: dict[str, object]) -> PolicyListRecord:
    return PolicyListRecord(
        id=UUID(str(row["id"])),
        title=str(row["title"]),
        document_no=row["document_no"] if isinstance(row["document_no"], str) else None,
        issuing_organization=(
            row["issuing_organization"]
            if isinstance(row["issuing_organization"], str)
            else None
        ),
        source_url=str(row["source_url"]),
        published_date=(
            row["published_date"] if isinstance(row["published_date"], date) else None
        ),
        effective_status=(
            row["effective_status"] if isinstance(row["effective_status"], str) else None
        ),
    )


class PolicyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, *, offset: int, limit: int, query: str | None) -> PolicyQuery:
        statement = select(
            PolicyDocument.id,
            PolicyDocument.title,
            PolicyDocument.document_no,
            PolicyDocument.issuing_organization,
            PolicyDocument.source_url,
            PolicyDocument.published_date,
            PolicyDocument.effective_status,
            func.count().over().label("_total"),
        ).where(PolicyDocument.region_code == "sz")
        count = (
            select(func.count())
            .select_from(PolicyDocument)
            .where(PolicyDocument.region_code == "sz")
        )
        if query:
            pattern = f"%{query.strip()}%"
            clause = or_(
                PolicyDocument.title.ilike(pattern),
                PolicyDocument.issuing_organization.ilike(pattern),
            )
            statement = statement.where(clause)
            count = count.where(clause)
        rows = list(
            self._session.execute(
                statement.order_by(
                    PolicyDocument.published_date.desc().nullslast(),
                    PolicyDocument.title.asc(),
                )
                .offset(offset)
                .limit(limit)
            )
            .mappings()
            .all()
        )
        total = int(rows[0]["_total"]) if rows else 0
        if not rows and offset:
            total = int(self._session.execute(count).scalar_one())
        return PolicyQuery(
            items=[_list_record_from_row(row) for row in rows],
            total=total,
        )

    def get(self, policy_id: UUID) -> PolicyDocument | None:
        model = self._session.execute(
            select(PolicyDocument).where(
                PolicyDocument.id == policy_id,
                PolicyDocument.region_code == "sz",
            )
        ).scalar_one_or_none()
        return _record_from_model(model) if model is not None else None


def _record_from_source(record: PolicySourceRecord, *, record_id: UUID) -> PolicyRecord:
    return PolicyRecord(
        id=record_id,
        title=record.title,
        document_no=record.document_no,
        issuing_organization=record.issuing_organization,
        source_url=record.source_url,
        document_url=record.document_url,
        published_date=record.published_date,
        collected_at=record.collected_at,
        content_text=record.content_text,
        content_sha256=record.content_sha256,
        effective_status=record.effective_status,
        requested_title=record.requested_title,
        reference_count=record.reference_count,
        source_years=record.source_years,
    )


class FixturePolicyRepository:
    """Read-only local fixture repository used only for development and tests."""

    def __init__(self, records: list[PolicyRecord]) -> None:
        self._records = tuple(records)

    @classmethod
    def from_jsonl(cls, path: Path) -> FixturePolicyRepository:
        records: list[PolicyRecord] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                source = PolicySourceRecord(
                    title=payload["title"],
                    document_no=payload.get("document_no"),
                    issuing_organization=payload.get("issuing_organization"),
                    source_url=payload["source_url"],
                    document_url=payload.get("document_url"),
                    published_date=date.fromisoformat(payload["published_date"]) if payload.get("published_date") else None,
                    collected_at=datetime.fromisoformat(payload["collected_at"]),
                    content_text=payload["content_text"],
                    content_sha256=payload["content_sha256"],
                    region_code=payload.get("region_code", "sz"),
                    requested_title=payload.get("requested_title"),
                    effective_status=payload.get("effective_status"),
                    reference_count=payload.get("reference_count"),
                    source_years=payload.get("source_years"),
                )
                records.append(_record_from_source(source, record_id=UUID(payload["id"])))
        return cls(records)

    def list(self, *, offset: int, limit: int, query: str | None) -> PolicyQuery:
        filtered = list(self._records)
        if query:
            needle = query.strip().casefold()
            filtered = [
                item for item in filtered
                if needle in item.title.casefold()
                or needle in (item.issuing_organization or "").casefold()
            ]
        filtered.sort(key=lambda item: (item.published_date or date.min, item.title), reverse=True)
        return PolicyQuery(items=filtered[offset : offset + limit], total=len(filtered))

    def get(self, policy_id: UUID) -> PolicyRecord | None:
        return next((item for item in self._records if item.id == policy_id), None)
