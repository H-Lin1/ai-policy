"""Structured logging with request correlation and redaction by construction.

Every record carries the request ID of the request being served, and credential
bearing fields are replaced before they reach any handler, so the readable local
format cannot become the leaky one.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from .context import NO_REQUEST, get_request_id

# Matched case-insensitively as substrings of the field name. Key names are used
# instead of value patterns: value matching both misses rotated credential
# formats and flags legitimate content.
REDACTED_KEY_PARTS = (
    "authorization",
    "token",
    "password",
    "secret",
    "api_key",
    "apikey",
    "cookie",
    "database_url",
    "dsn",
    "credential",
    "jwt",
)
REDACTED_VALUE = "***"
MAX_VALUE_LENGTH = 500
UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi")

# Structured fields are the primary boundary. These patterns cover credentials
# that reach a message, exception, URL, or nested value before it is formatted.
_KEY_VALUE_PATTERN = re.compile(
    r"(?i)(\b(?:authorization|access[_-]?token|refresh[_-]?token|id[_-]?token|"
    r"token|password|passwd|pwd|secret|api[_-]?key|apikey|cookie|database[_-]?url|"
    r"dsn|credential|jwt)\b\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;}&]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+")
_CONNECTION_URL_PATTERN = re.compile(
    r"(?i)\b(?:postgres|postgresql(?:\+[a-z0-9_]+)?|mysql|mongodb(?:\+[a-z0-9_]+)?|"
    r"redis)://[^\s'\"<>]+"
)
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){2}\b")

_BASE_RECORD_FIELDS = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__
) | {
    "asctime",
    "message",
    "taskName",
    "request_id",
}


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in REDACTED_KEY_PARTS)


def redact_text(value: str) -> str:
    """Remove common credential representations from free-form log text."""

    # Redact Bearer values first: a generic key/value replacement would otherwise
    # consume only the "Bearer" word and leave the actual credential behind.
    redacted = _BEARER_PATTERN.sub(r"\1" + REDACTED_VALUE, value)
    redacted = _CONNECTION_URL_PATTERN.sub(REDACTED_VALUE, redacted)
    redacted = _JWT_PATTERN.sub(REDACTED_VALUE, redacted)
    return _KEY_VALUE_PATTERN.sub(r"\1" + REDACTED_VALUE, redacted)


def _bounded_text(value: str) -> str:
    value = redact_text(value)
    return value if len(value) <= MAX_VALUE_LENGTH else value[:MAX_VALUE_LENGTH] + "…"


def _safe_value(value: Any, seen: set[int] | None = None) -> Any:
    """Return a bounded, JSON-safe value without leaking nested credentials."""

    seen = seen if seen is not None else set()
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, str):
        return _bounded_text(value)
    if isinstance(value, Mapping):
        if id(value) in seen:
            return "<recursive>"
        seen.add(id(value))
        try:
            return {
                str(key): REDACTED_VALUE if _is_sensitive(str(key)) else _safe_value(item, seen)
                for key, item in value.items()
            }
        finally:
            seen.remove(id(value))
    if isinstance(value, (list, tuple, set, frozenset)):
        if id(value) in seen:
            return "<recursive>"
        seen.add(id(value))
        try:
            return [_safe_value(item, seen) for item in value]
        finally:
            seen.remove(id(value))
    try:
        json.dumps(value)
    except (TypeError, ValueError, OverflowError):
        # A logging call must never raise and never emit an unbounded blob.
        try:
            return _bounded_text(repr(value))
        except Exception:  # noqa: BLE001 - arbitrary __repr__ must not break logging.
            return "<unrenderable>"
    return value


def extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    """Return the caller-supplied fields of a record, redacted and JSON-safe."""

    fields: dict[str, Any] = {}
    for key, value in record.__dict__.items():
        if key in _BASE_RECORD_FIELDS or key.startswith("_"):
            continue
        fields[key] = REDACTED_VALUE if _is_sensitive(key) else _safe_value(value)
    return fields


class RequestContextFilter(logging.Filter):
    """Attach the current request ID to every record, including startup records."""

    def filter(self, record: logging.LogRecord) -> bool:
        existing = getattr(record, "request_id", None)
        if not isinstance(existing, str) or not existing:
            record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat().replace(
                "+00:00", "Z"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_text(record.getMessage()),
            "request_id": getattr(record, "request_id", NO_REQUEST),
        }
        payload.update(extra_fields(record))
        if record.exc_info:
            payload["exception"] = redact_text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable local format using the same redaction as JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", NO_REQUEST)
        base = (
            f"{self.formatTime(record)} {record.levelname} {record.name} "
            f"request_id={request_id} {redact_text(record.getMessage())}"
        )
        fields = extra_fields(record)
        if fields:
            rendered = " ".join(f"{key}={value}" for key, value in sorted(fields.items()))
            base = f"{base} {rendered}"
        if record.exc_info:
            base = f"{base}\n{redact_text(self.formatException(record.exc_info))}"
        return base


def configure_logging(level: str = "INFO", log_format: str = "json") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(
        TextFormatter() if log_format.strip().lower() == "text" else JsonFormatter()
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Uvicorn installs dedicated handlers before importing the application.
    # Route them through the same formatter so a real server process does not
    # mix unstructured access/startup lines into the JSON stream.
    for logger_name in UVICORN_LOGGERS:
        server_logger = logging.getLogger(logger_name)
        server_logger.handlers.clear()
        server_logger.setLevel(logging.NOTSET)
        server_logger.propagate = True
        # The application access logger already records the same request with
        # correlation fields. Uvicorn emits its duplicate after the request
        # context is reset, so it cannot carry the request ID and is disabled.
        server_logger.disabled = logger_name == "uvicorn.access"
