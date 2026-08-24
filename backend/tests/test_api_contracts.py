from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.contracts import (
    ApiModel,
    PageResponse,
    PaginationMeta,
    PaginationParams,
    UtcDateTime,
)
from app.core.config import Settings
from app.core.errors import AppError
from app.main import create_app


class _Event(ApiModel):
    occurred_at: UtcDateTime


def _contract_client() -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="development",
        app_version="test",
        auth_required=False,
        database_url=None,
        supabase_url=None,
    )
    app = create_app(settings)

    @app.get(
        "/api/v1/_contract-page",
        response_model=PageResponse[dict[str, str]],
        operation_id="contractPageProbe",
    )
    def contract_page(params: PaginationParams = Depends()) -> PageResponse[dict[str, str]]:
        return PageResponse(
            items=[{"value": "one"}],
            meta=PaginationMeta.from_total(params, 21),
        )

    @app.get("/api/v1/_contract-error", operation_id="contractErrorProbe")
    def contract_error() -> dict[str, str]:
        raise AppError("CONTRACT_ERROR", "测试错误", details={"bad": object()})

    return TestClient(app)


def test_pagination_defaults_and_navigation_metadata() -> None:
    with _contract_client() as client:
        response = client.get("/api/v1/_contract-page")

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"value": "one"}],
        "meta": {
            "page": 1,
            "page_size": 20,
            "total": 21,
            "total_pages": 2,
            "has_next": True,
            "has_previous": False,
        },
    }


def test_pagination_bounds_use_standard_validation_error() -> None:
    with _contract_client() as client:
        response = client.get(
            "/api/v1/_contract-page?page=0&page_size=101",
            headers={"X-Request-ID": "pagination-check"},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["request_id"] == "pagination-check"
    assert response.headers["X-Request-ID"] == "pagination-check"


def test_empty_pagination_metadata_has_no_navigation() -> None:
    meta = PaginationMeta.from_total(PaginationParams(), 0)

    assert meta.model_dump() == {
        "page": 1,
        "page_size": 20,
        "total": 0,
        "total_pages": 0,
        "has_next": False,
        "has_previous": False,
    }


def test_utc_datetime_normalizes_offsets_and_rejects_naive_values() -> None:
    event = _Event.model_validate({"occurred_at": "2026-08-06T08:00:00+08:00"})

    assert event.occurred_at.isoformat() == "2026-08-06T00:00:00+00:00"
    assert event.model_dump_json() == '{"occurred_at":"2026-08-06T00:00:00Z"}'
    with pytest.raises(ValidationError):
        _Event.model_validate({"occurred_at": "2026-08-06T08:00:00"})


def test_error_details_are_json_safe_and_method_errors_are_stable() -> None:
    with _contract_client() as client:
        error_response = client.get(
            "/api/v1/_contract-error", headers={"X-Request-ID": "error-check"}
        )
        method_response = client.post(
            "/api/v1/health/live", headers={"X-Request-ID": "method-check"}
        )

    assert error_response.status_code == 400
    assert json.dumps(error_response.json(), ensure_ascii=False)
    assert error_response.json()["error"]["code"] == "CONTRACT_ERROR"
    assert error_response.json()["request_id"] == "error-check"
    assert error_response.headers["X-Request-ID"] == "error-check"

    assert method_response.status_code == 405
    assert method_response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert method_response.headers["X-Request-ID"] == "method-check"
    assert "Allow" in method_response.headers


def test_openapi_has_stable_operations_and_shared_contract_schemas() -> None:
    with _contract_client() as client:
        schema: dict[str, Any] = client.get("/openapi.json").json()

    paths = schema["paths"]
    assert all(path.startswith("/api/v1/") for path in paths)
    operation_ids = [
        operation["operationId"]
        for path in paths.values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))
    schemas = schema["components"]["schemas"]
    assert {"ApiErrorResponse", "PaginationMeta", "PaginationParams", "PageResponse"} <= set(
        schemas
    )
    for path in paths.values():
        for operation in path.values():
            if not isinstance(operation, dict):
                continue
            for response in operation.get("responses", {}).values():
                if not isinstance(response, dict) or "content" not in response:
                    continue
                if "application/json" not in response["content"]:
                    continue
                content_schema = response["content"]["application/json"].get("schema", {})
                if response.get("description") in {
                    "请求的接口不存在",
                    "请求参数校验失败",
                    "服务内部错误",
                    "请求方法不被允许",
                    "需要有效的 Bearer 登录令牌",
                    "认证服务尚未配置或暂不可用",
                    "服务依赖尚未就绪",
                }:
                    assert content_schema.get("$ref", "").endswith("/ApiErrorResponse")
