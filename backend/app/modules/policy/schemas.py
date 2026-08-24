from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from app.api.contracts import ApiModel, PageResponse, UtcDateTime


class PolicyListItem(ApiModel):
    id: UUID
    title: str
    document_no: str | None = None
    issuing_organization: str | None = None
    source_url: str
    published_date: date | None = None
    effective_status: str | None = None


class PolicyDetail(PolicyListItem):
    document_url: str | None = None
    collected_at: UtcDateTime
    content_text: str
    content_sha256: str
    requested_title: str | None = None
    reference_count: int | None = Field(default=None, ge=0)
    source_years: str | None = None


PolicyPage = PageResponse[PolicyListItem]
