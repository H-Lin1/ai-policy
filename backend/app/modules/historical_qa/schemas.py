from __future__ import annotations

from uuid import UUID

from app.api.contracts import ApiModel, PageResponse, UtcDateTime


class HistoricalQaListItem(ApiModel):
    id: UUID
    topic: str
    source_url: str
    replied_at: UtcDateTime | None = None
    publishing_organization: str
    contains_legal_basis: bool


class HistoricalQaDetail(HistoricalQaListItem):
    question_text: str
    answer_text: str
    question_at: UtcDateTime | None = None
    collected_at: UtcDateTime
    legal_basis_name: str | None = None
    legal_basis_citation: str | None = None
    adjudication_result: str
    content_sha256: str


HistoricalQaPage = PageResponse[HistoricalQaListItem]
