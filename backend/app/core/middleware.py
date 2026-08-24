from __future__ import annotations

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .context import reset_request_id, set_request_id

logger = logging.getLogger("ai_policy.http")


def _safe_request_id(value: str | None) -> str:
    if value and len(value) <= 128 and all(char.isalnum() or char in "-_." for char in value):
        return value
    return uuid4().hex


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _safe_request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        token = set_request_id(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            # The error boundary above this middleware sets the response header.
            raise
        else:
            response.headers["X-Request-ID"] = request_id
            settings = getattr(request.app.state, "settings", None)
            api_prefix = getattr(settings, "api_prefix", "/api/v1")
            if request.url.path == f"{api_prefix}/me" or request.url.path.startswith(
                f"{api_prefix}/iam/"
            ) or request.url.path.startswith(f"{api_prefix}/policy-answers"):
                response.headers["Cache-Control"] = "no-store"
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            return response
        finally:
            reset_request_id(token)
