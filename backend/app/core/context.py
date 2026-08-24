"""Request-scoped identity that cross-cutting code can read without a Request.

Logging, error handlers, and future services need the current request ID but must
not depend on the ASGI request object, which is unavailable outside the request
middleware frame.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

NO_REQUEST = "-"

_request_id: ContextVar[str] = ContextVar("request_id", default=NO_REQUEST)


def set_request_id(request_id: str) -> Token[str]:
    """Bind the request ID to the current context and return its reset token."""

    return _request_id.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    """Restore the previous context value so IDs never leak between requests."""

    _request_id.reset(token)


def get_request_id() -> str:
    return _request_id.get()
