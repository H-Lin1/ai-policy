"""Shared HTTP contracts used by every V1 API module.

Business modules should import these types instead of inventing their own
pagination, error, or timestamp shapes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from math import ceil
from typing import Annotated, Any, Generic, TypeVar

from fastapi import status
from pydantic import AfterValidator, BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    """Base model for shared request/response contracts."""

    model_config = ConfigDict(extra="forbid")


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must include timezone information")
    return value.astimezone(UTC)


UtcDateTime = Annotated[datetime, AfterValidator(_normalize_utc)]


def utc_now() -> datetime:
    """Return an aware UTC timestamp for persistence and API responses."""

    return datetime.now(UTC)


class ApiErrorDetail(ApiModel):
    code: str
    message: str
    details: Any | None = None


class ApiErrorResponse(ApiModel):
    error: ApiErrorDetail
    request_id: str


class PaginationParams(ApiModel):
    """Common one-based pagination query parameters."""

    page: int = Field(default=1, ge=1, description="1-based page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (maximum 100)",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginationMeta(ApiModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool

    @classmethod
    def from_total(cls, params: PaginationParams, total: int) -> PaginationMeta:
        if total < 0:
            raise ValueError("total must be non-negative")
        total_pages = ceil(total / params.page_size) if total else 0
        return cls(
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1 and total_pages > 0,
        )


ItemT = TypeVar("ItemT")


class PageResponse(ApiModel, Generic[ItemT]):
    items: list[ItemT]
    meta: PaginationMeta


def error_response(
    description: str,
    *,
    code: str,
) -> dict[str, Any]:
    """Build one OpenAPI response entry for the shared error envelope."""

    return {
        "model": ApiErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "example": {
                    "error": {"code": code, "message": description, "details": None},
                    "request_id": "request-id",
                }
            }
        },
    }


COMMON_ERROR_RESPONSES: dict[int, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: error_response(
        "请求的接口不存在", code="ROUTE_NOT_FOUND"
    ),
    status.HTTP_422_UNPROCESSABLE_CONTENT: error_response(
        "请求参数校验失败", code="VALIDATION_ERROR"
    ),
    status.HTTP_500_INTERNAL_SERVER_ERROR: error_response(
        "服务内部错误", code="INTERNAL_ERROR"
    ),
    status.HTTP_405_METHOD_NOT_ALLOWED: error_response(
        "请求方法不被允许", code="METHOD_NOT_ALLOWED"
    ),
}

AUTH_ERROR_RESPONSES: dict[int, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: error_response(
        "需要有效的 Bearer 登录令牌", code="AUTH_REQUIRED"
    ),
    status.HTTP_503_SERVICE_UNAVAILABLE: error_response(
        "认证服务尚未配置或暂不可用", code="AUTH_NOT_CONFIGURED"
    ),
}

IDENTITY_ERROR_RESPONSES: dict[int, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: error_response(
        "当前应用身份或角色无权访问该资源", code="ROLE_FORBIDDEN"
    ),
    status.HTTP_503_SERVICE_UNAVAILABLE: error_response(
        "应用身份服务暂不可用", code="IDENTITY_STORE_UNAVAILABLE"
    ),
}

NOT_READY_ERROR_RESPONSES: dict[int, dict[str, Any]] = {
    status.HTTP_503_SERVICE_UNAVAILABLE: error_response(
        "服务依赖尚未就绪", code="SERVICE_NOT_READY"
    ),
}
