from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.contracts import ApiErrorDetail, ApiErrorResponse
from app.core.context import NO_REQUEST, get_request_id

logger = logging.getLogger("ai_policy.errors")

_HTTP_ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "ROUTE_NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_CONTENT: "VALIDATION_ERROR",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_ERROR",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
}


class AppError(Exception):
    """Expected application failure with a stable public error code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers


def _request_id(request: Request) -> str:
    """Prefer the request object: the 500 boundary runs after the context reset."""

    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    context_id = get_request_id()
    return context_id if context_id != NO_REQUEST else "unknown"


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build an error response whose header always matches the body request ID."""

    request_id = _request_id(request)
    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=status_code,
        content=ApiErrorResponse(
            error=ApiErrorDetail(code=code, message=message, details=_json_safe(details)),
            request_id=request_id,
        ).model_dump(mode="json"),
        headers=response_headers,
    )


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    try:
        encoded = jsonable_encoder(value)
        json.dumps(encoded)
        return encoded
    except (TypeError, ValueError):
        # Validation details must never turn an expected 4xx into a 500.
        return {"message": "错误详情无法序列化"}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="请求参数校验失败",
        details=exc.errors(),
    )


async def http_error_handler(
    request: Request,
    exc: HTTPException | StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        code = str(detail.get("code", "HTTP_ERROR"))
        message = str(detail.get("message", "请求失败"))
        details = detail.get("details")
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = _HTTP_ERROR_CODES[status.HTTP_404_NOT_FOUND]
        message = "请求的接口不存在"
        details = None
    else:
        code = _HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
        message = str(detail)
        details = None
    return _error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
        headers=dict(exc.headers) if exc.headers else None,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Do not expose stack traces or secrets in the public response.
    request_id = _request_id(request)
    logger.exception("unhandled_error", exc_info=exc, extra={"request_id": request_id})
    return _error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="服务内部错误",
    )
