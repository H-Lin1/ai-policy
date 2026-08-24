from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .models import HistoricalQa
from .source import HistoricalQaSourceRecord


@dataclass(frozen=True)
class HistoricalQaListRecord:
    id: UUID
    topic: str
    source_url: str
    replied_at: datetime | None
    publishing_organization: str
    contains_legal_basis: bool


@dataclass(frozen=True)
class HistoricalQaRecord(HistoricalQaListRecord):
    question_text: str
    answer_text: str
    question_at: datetime | None
    collected_at: datetime
    legal_basis_name: str | None
    legal_basis_citation: str | None
    adjudication_result: str
    content_sha256: str


@dataclass(frozen=True)
class HistoricalQaQuery:
    items: list[HistoricalQaListRecord]
    total: int


def _list_from_row(row: dict[str, object]) -> HistoricalQaListRecord:
    return HistoricalQaListRecord(
        id=UUID(str(row["id"])), topic=str(row["topic"]), source_url=str(row["source_url"]),
        replied_at=row["replied_at"] if isinstance(row["replied_at"], datetime) else None,
        publishing_organization=str(row["publishing_organization"]),
        contains_legal_basis=bool(row["contains_legal_basis"]),
    )


def _record_from_model(model: HistoricalQa) -> HistoricalQaRecord:
    return HistoricalQaRecord(
        id=model.id, topic=model.topic, question_text=model.question_text, answer_text=model.answer_text,
        source_url=model.source_url, question_at=model.question_at, replied_at=model.replied_at,
        publishing_organization=model.publishing_organization, collected_at=model.collected_at,
        contains_legal_basis=model.contains_legal_basis, legal_basis_name=model.legal_basis_name,
        legal_basis_citation=model.legal_basis_citation, adjudication_result=model.adjudication_result,
        content_sha256=model.content_sha256,
    )


class HistoricalQaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, *, offset: int, limit: int, query: str | None) -> HistoricalQaQuery:
        statement = select(
            HistoricalQa.id, HistoricalQa.topic, HistoricalQa.source_url, HistoricalQa.replied_at,
            HistoricalQa.publishing_organization, HistoricalQa.contains_legal_basis,
            func.count().over().label("_total"),
        ).where(HistoricalQa.region_code == "sz")
        count = select(func.count()).select_from(HistoricalQa).where(HistoricalQa.region_code == "sz")
        if query:
            pattern = f"%{query.strip()}%"
            clause = or_(HistoricalQa.topic.ilike(pattern), HistoricalQa.question_text.ilike(pattern), HistoricalQa.publishing_organization.ilike(pattern))
            statement, count = statement.where(clause), count.where(clause)
        rows = list(self._session.execute(statement.order_by(HistoricalQa.replied_at.desc().nullslast(), HistoricalQa.topic.asc()).offset(offset).limit(limit)).mappings().all())
        total = int(rows[0]["_total"]) if rows else (int(self._session.execute(count).scalar_one()) if offset else 0)
        return HistoricalQaQuery(items=[_list_from_row(row) for row in rows], total=total)

    def get(self, qa_id: UUID) -> HistoricalQaRecord | None:
        record = self._session.execute(select(HistoricalQa).where(HistoricalQa.id == qa_id, HistoricalQa.region_code == "sz")).scalar_one_or_none()
        return _record_from_model(record) if record is not None else None


def _record_from_source(record: HistoricalQaSourceRecord, record_id: UUID) -> HistoricalQaRecord:
    return HistoricalQaRecord(
        id=record_id, topic=record.topic, question_text=record.question_text, answer_text=record.answer_text,
        source_url=record.source_url, question_at=record.question_at, replied_at=record.replied_at,
        publishing_organization=record.publishing_organization, collected_at=record.collected_at,
        contains_legal_basis=record.contains_legal_basis, legal_basis_name=record.legal_basis_name,
        legal_basis_citation=record.legal_basis_citation, adjudication_result=record.adjudication_result,
        content_sha256=record.content_sha256,
    )


class FixtureHistoricalQaRepository:
    def __init__(self, records: list[HistoricalQaRecord]) -> None:
        self._records = tuple(records)

    @classmethod
    def from_jsonl(cls, path: Path) -> FixtureHistoricalQaRepository:
        records: list[HistoricalQaRecord] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                source = HistoricalQaSourceRecord(
                    topic=payload["topic"], question_text=payload["question_text"], answer_text=payload["answer_text"],
                    source_url=payload["source_url"], question_at=datetime.fromisoformat(payload["question_at"]) if payload.get("question_at") else None,
                    replied_at=datetime.fromisoformat(payload["replied_at"]) if payload.get("replied_at") else None,
                    publishing_organization=payload["publishing_organization"], collected_at=datetime.fromisoformat(payload["collected_at"]),
                    contains_legal_basis=payload["contains_legal_basis"], legal_basis_name=payload.get("legal_basis_name"),
                    legal_basis_citation=payload.get("legal_basis_citation"), adjudication_result=payload["adjudication_result"],
                    content_sha256=payload["content_sha256"], region_code=payload.get("region_code", "sz"),
                )
                records.append(_record_from_source(source, UUID(payload["id"])))
        return cls(records)

    def list(self, *, offset: int, limit: int, query: str | None) -> HistoricalQaQuery:
        records = list(self._records)
        if query:
            needle = query.strip().casefold()
            records = [item for item in records if needle in item.topic.casefold() or needle in item.question_text.casefold() or needle in item.publishing_organization.casefold()]
        records.sort(key=lambda item: (item.replied_at or datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo), item.topic), reverse=True)
        return HistoricalQaQuery(items=records[offset:offset + limit], total=len(records))

    def get(self, qa_id: UUID) -> HistoricalQaRecord | None:
        return next((item for item in self._records if item.id == qa_id), None)
