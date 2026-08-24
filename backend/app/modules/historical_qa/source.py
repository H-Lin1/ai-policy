from __future__ import annotations

import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ALLOWED_REGION = "sz"
ALLOWED_HOST = re.compile(r"^(?:gov\.cn|[a-z0-9.-]+\.gov\.cn)$", re.IGNORECASE)
SHANGHAI = ZoneInfo("Asia/Shanghai")

# Matching text is rejected as a whole.  We deliberately do not attempt to
# redact it, because a partial redaction could preserve identifying context.
SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("SENSITIVE_EMAIL", re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)),
    ("SENSITIVE_PR_CITIZEN_ID", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("SENSITIVE_LONG_CARD_NUMBER", re.compile(r"(?<!\d)(?:\d[ -]?){15,18}\d(?!\d)")),
    ("SENSITIVE_PHONE", re.compile(r"(?<!\d)(?:1[3-9]\d[ -]?\d{4}[ -]?\d{4}|0\d{2,3}[ -]?\d{7,8})(?!\d)")),
    ("SENSITIVE_CONTACT_LABEL", re.compile(r"(?:联系(?:电话|方式|人)|请(?:致电|拨打)|微信(?:号)?|QQ(?:号)?|邮箱)\s*[:：]?", re.IGNORECASE)),
)


@dataclass(frozen=True)
class SourceValidationError(ValueError):
    reason: str

    def __str__(self) -> str:
        return self.reason


@dataclass(frozen=True)
class HistoricalQaSourceRecord:
    topic: str
    question_text: str
    answer_text: str
    source_url: str
    question_at: datetime | None
    replied_at: datetime | None
    publishing_organization: str
    collected_at: datetime
    contains_legal_basis: bool
    legal_basis_name: str | None
    legal_basis_citation: str | None
    adjudication_result: str
    content_sha256: str
    region_code: str = ALLOWED_REGION


def _text(value: object) -> str:
    return str(value or "").replace("\x00", "").strip()


def normalize_text(value: object) -> str:
    return _text(value).replace("\r\n", "\n").replace("\r", "\n")


def _parse_source_url(value: object) -> str:
    candidate = _text(value)
    parsed = urlsplit(candidate)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not host or not ALLOWED_HOST.fullmatch(host):
        raise SourceValidationError("SOURCE_HOST_NOT_ALLOWED")
    if parsed.username or parsed.password or parsed.fragment:
        raise SourceValidationError("SOURCE_URL_UNSAFE")
    return candidate


def _parse_datetime(value: object, *, field: str, required: bool) -> datetime | None:
    candidate = _text(value)
    if not candidate:
        if required:
            raise SourceValidationError(f"{field}_REQUIRED")
        return None
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SourceValidationError(f"{field}_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=SHANGHAI)
    return parsed.astimezone(UTC)


def _parse_boolean(value: object) -> bool:
    candidate = _text(value)
    if candidate == "是":
        return True
    if candidate == "否":
        return False
    raise SourceValidationError("LEGAL_BASIS_FLAG_INVALID")


def _select_legal_basis(row: dict[str, object], adjudication: str) -> tuple[str | None, str | None]:
    if adjudication == "规则对":
        return (
            normalize_text(row.get("法律依据名称")) or None,
            normalize_text(row.get("法律依据完整引文")) or None,
        )
    if adjudication == "大模型清洗对":
        return (
            normalize_text(row.get("模型识别法律依据名称")) or None,
            normalize_text(row.get("模型识别法律依据完整引文")) or None,
        )
    if adjudication == "无法确认":
        return None, None
    raise SourceValidationError("ADJUDICATION_INVALID")


def _ensure_public_text(*values: str) -> None:
    for reason, pattern in SENSITIVE_PATTERNS:
        if any(pattern.search(value) for value in values):
            raise SourceValidationError(reason)


def normalize_source_row(row: dict[str, object]) -> HistoricalQaSourceRecord:
    topic = normalize_text(row.get("留言主题"))
    question = normalize_text(row.get("留言内容"))
    answer = normalize_text(row.get("答复内容"))
    publisher = normalize_text(row.get("发布机构"))
    if not topic or not question or not answer or not publisher:
        raise SourceValidationError("MANDATORY_TEXT_REQUIRED")
    source_url = _parse_source_url(row.get("来源链接"))
    adjudication = _text(row.get("分歧仲裁结果"))
    contains_legal_basis = _parse_boolean(row.get("是否含法律依据"))
    legal_basis_name, legal_basis_citation = _select_legal_basis(row, adjudication)
    if not contains_legal_basis:
        legal_basis_name, legal_basis_citation = None, None
    _ensure_public_text(topic, question, answer, publisher, legal_basis_name or "", legal_basis_citation or "")
    content = f"{topic}\n{question}\n{answer}\n{source_url}"
    return HistoricalQaSourceRecord(
        topic=topic,
        question_text=question,
        answer_text=answer,
        source_url=source_url,
        question_at=_parse_datetime(row.get("留言时间"), field="QUESTION_AT", required=False),
        replied_at=_parse_datetime(row.get("答复时间"), field="REPLIED_AT", required=False),
        publishing_organization=publisher,
        collected_at=_parse_datetime(row.get("抓取时间"), field="COLLECTED_AT", required=True),
        contains_legal_basis=contains_legal_basis,
        legal_basis_name=legal_basis_name,
        legal_basis_citation=legal_basis_citation,
        adjudication_result=adjudication,
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def read_csvs(paths: tuple[Path, ...], *, limit: int | None = None) -> tuple[list[HistoricalQaSourceRecord], dict[str, int]]:
    accepted: list[HistoricalQaSourceRecord] = []
    rejected: dict[str, int] = {}
    seen: set[tuple[str, str]] = set()
    csv.field_size_limit(sys.maxsize)
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
            for row in csv.DictReader(handle):
                try:
                    record = normalize_source_row(row)
                    identity = (record.source_url, record.content_sha256)
                    if identity in seen:
                        raise SourceValidationError("DUPLICATE_SOURCE_VERSION")
                    seen.add(identity)
                    if limit is None or len(accepted) < limit:
                        accepted.append(record)
                except SourceValidationError as exc:
                    rejected[exc.reason] = rejected.get(exc.reason, 0) + 1
    return accepted, rejected
