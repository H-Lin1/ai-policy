from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.api.contracts import ApiModel, PageResponse, UtcDateTime


class PolicyListItem(ApiModel):
    id: UUID
    title: str
    document_no: str | None = None
    issuing_organization: str | None = None
    source_url: str | None = None
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


class AdminPolicyInput(ApiModel):
    title: str = Field(min_length=1, max_length=500)
    document_no: str | None = Field(default=None, max_length=300)
    issuing_organization: str = Field(min_length=1, max_length=300)
    source_url: str | None = Field(default=None, max_length=2000)
    document_url: str | None = Field(default=None, max_length=2000)
    published_date: date
    effective_status: Literal["active", "pending", "expired", "repealed", "unknown"]
    content_text: str = Field(min_length=1, max_length=2_000_000)
    source_type: Literal["manual", "markdown"] = "manual"
    original_filename: str | None = Field(default=None, max_length=200)
    raw_markdown: str | None = Field(default=None, max_length=2_097_152)

    @field_validator("source_url", "document_url")
    @classmethod
    def validate_optional_http_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        from urllib.parse import urlsplit

        candidate = value.strip()
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("URL must be an HTTP(S) address without credentials or fragment")
        return candidate


class AdminPolicyCreateRequest(AdminPolicyInput):
    action: Literal["draft", "publish"]


class AdminPolicyRecord(ApiModel):
    id: UUID
    title: str
    document_no: str | None = None
    issuing_organization: str | None = None
    source_url: str | None = None
    document_url: str | None = None
    published_date: date | None = None
    effective_status: str | None = None
    content_text: str
    source_type: Literal["external_url", "manual", "markdown"]
    raw_markdown: str | None = None
    publication_status: Literal["draft", "published", "withdrawn"]
    content_sha256: str
    created_at: UtcDateTime
    published_at: UtcDateTime | None = None
    withdrawn_at: UtcDateTime | None = None


class MarkdownFileInput(ApiModel):
    filename: str = Field(min_length=1, max_length=200)
    content: str = Field(max_length=2_097_152)


class MarkdownBatchRequest(ApiModel):
    files: list[MarkdownFileInput] = Field(min_length=1, max_length=20)


class MarkdownParseItem(ApiModel):
    filename: str
    status: Literal["ready", "warning", "failed"]
    fields: AdminPolicyInput | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MarkdownBatchResponse(ApiModel):
    items: list[MarkdownParseItem]


class PolicyWithdrawRequest(ApiModel):
    reason: str = Field(min_length=1, max_length=2000)
