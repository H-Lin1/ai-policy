from __future__ import annotations

import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_REGION = "sz"
ALLOWED_HOST = re.compile(r"^(?:gov\.cn|[a-z0-9.-]+\.gov\.cn)$", re.IGNORECASE)
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceValidationError(ValueError):
    reason: str

    def __str__(self) -> str:
        return self.reason


@dataclass(frozen=True)
class PolicySourceRecord:
    title: str
    document_no: str | None
    issuing_organization: str | None
    source_url: str
    document_url: str | None
    published_date: date | None
    collected_at: datetime
    content_text: str
    content_sha256: str
    region_code: str
    requested_title: str | None = None
    effective_status: str | None = None
    reference_count: int | None = None
    source_years: str | None = None


def _text(value: object) -> str:
    return str(value or "").replace("\x00", "").strip()


def normalize_content(value: object) -> str:
    return _text(value).replace("\r\n", "\n").replace("\r", "\n")


def _parse_source_url(value: object, *, required: bool = True) -> str | None:
    candidate = _text(value)
    if not candidate and not required:
        return None
    parsed = urlsplit(candidate)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not host or not ALLOWED_HOST.fullmatch(host):
        raise SourceValidationError("SOURCE_HOST_NOT_ALLOWED")
    if parsed.username or parsed.password or parsed.fragment:
        raise SourceValidationError("SOURCE_URL_UNSAFE")
    return candidate


def _parse_date(value: object) -> date | None:
    candidate = _text(value)
    if not candidate:
        return None
    try:
        return date.fromisoformat(candidate[:10])
    except ValueError as exc:
        raise SourceValidationError("PUBLISHED_DATE_INVALID") from exc


def _parse_datetime(value: object) -> datetime:
    candidate = _text(value)
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SourceValidationError("COLLECTED_AT_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SourceValidationError("COLLECTED_AT_TIMEZONE_REQUIRED")
    return parsed


def normalize_source_row(row: dict[str, object]) -> PolicySourceRecord:
    if _text(row.get("crawl_status")) != "success":
        raise SourceValidationError("CRAWL_STATUS_NOT_SUCCESS")
    title = _text(row.get("title"))
    content = normalize_content(row.get("content_text"))
    if not title:
        raise SourceValidationError("TITLE_REQUIRED")
    if not content:
        raise SourceValidationError("CONTENT_REQUIRED")
    if _text(row.get("region_code")) != ALLOWED_REGION:
        raise SourceValidationError("REGION_NOT_SUPPORTED")
    source_url = _parse_source_url(row.get("source_url"))
    document_url = _parse_source_url(row.get("document_url"), required=False)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    supplied = _text(row.get("content_sha256")).lower()
    if supplied and (not HEX_SHA256.fullmatch(supplied) or supplied != digest):
        raise SourceValidationError("CONTENT_HASH_MISMATCH")
    reference_count = _text(row.get("reference_count"))
    try:
        parsed_reference_count = int(reference_count) if reference_count else None
    except ValueError as exc:
        raise SourceValidationError("REFERENCE_COUNT_INVALID") from exc
    if parsed_reference_count is not None and parsed_reference_count < 0:
        raise SourceValidationError("REFERENCE_COUNT_INVALID")
    return PolicySourceRecord(
        title=title,
        document_no=_text(row.get("document_no")) or None,
        issuing_organization=_text(row.get("issuing_organization")) or None,
        source_url=source_url or "",
        document_url=document_url,
        published_date=_parse_date(row.get("published_date")),
        collected_at=_parse_datetime(row.get("collected_at")),
        content_text=content,
        content_sha256=digest,
        region_code=ALLOWED_REGION,
        requested_title=_text(row.get("requested_title")) or None,
        effective_status=_text(row.get("effective_status")) or None,
        reference_count=parsed_reference_count,
        source_years=_text(row.get("source_years")) or None,
    )


def read_csv(path: Path, *, limit: int | None = None) -> tuple[list[PolicySourceRecord], dict[str, int]]:
    accepted: list[PolicySourceRecord] = []
    rejected: dict[str, int] = {}
    seen: set[tuple[str, str]] = set()
    csv.field_size_limit(sys.maxsize)
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                record = normalize_source_row(row)
                key = (record.source_url, record.content_sha256)
                if key in seen:
                    raise SourceValidationError("DUPLICATE_SOURCE_VERSION")
                seen.add(key)
                if limit is None or len(accepted) < limit:
                    accepted.append(record)
            except SourceValidationError as exc:
                rejected[exc.reason] = rejected.get(exc.reason, 0) + 1
    return accepted, rejected
