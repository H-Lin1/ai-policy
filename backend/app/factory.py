from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.contracts import (
    ApiErrorDetail,
    ApiErrorResponse,
    PageResponse,
    PaginationMeta,
    PaginationParams,
)
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import warm_database_connection
from app.core.errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

logger = logging.getLogger("ai_policy.app")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info(
            "application_starting",
            extra={"service": settings.app_name, "version": settings.app_version},
        )
        warmup_status, warmup_duration_ms = warm_database_connection(settings)
        if warmup_status == "ok":
            logger.info(
                "database_connection_warmed",
                extra={"duration_ms": warmup_duration_ms},
            )
        elif warmup_status == "unavailable":
            logger.warning(
                "database_connection_warmup_failed",
                extra={"duration_ms": warmup_duration_ms},
            )
        yield
        logger.info("application_stopped", extra={"service": settings.app_name})

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI 政策服务平台模块化单体 API",
        openapi_tags=[
            {
                "name": "system",
                "description": "服务存活、依赖就绪、模型状态和当前身份检查",
            },
            {
                "name": "identity-access",
                "description": "数据库身份、组织地区范围和角色工作区访问",
            },
            {
                "name": "policy-library",
                "description": "政府来源政策只读列表和详情",
            },
            {
                "name": "historical-qa",
                "description": "经隐私筛选的政府历史问答只读列表和详情",
            },
            {
                "name": "classification",
                "description": "经身份范围保护的深圳部门分类",
            },
            {
                "name": "policy-qa",
                "description": "受身份范围保护的政策智能问答",
            },
            {
                "name": "consultation",
                "description": "部门自动分派、答复与可选公开的咨询闭环",
            },
        ],
        lifespan=lifespan,
    )
    app.state.settings = settings
    # Keep factory-created apps (tests, smoke checks, workers) on one config object.
    app.dependency_overrides[get_settings] = lambda: settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parsed_cors_origins,
        allow_credentials=settings.parsed_cors_origins != ["*"],
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    # Add this last so even CORS preflight responses receive a request ID.
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router, prefix=settings.api_prefix)

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=settings.app_name,
            version=settings.app_version,
            description="AI 政策服务平台模块化单体 API",
            routes=app.routes,
            tags=[
                {
                    "name": "system",
                    "description": "服务存活、依赖就绪、模型状态和当前身份检查",
                },
                {
                    "name": "identity-access",
                    "description": "数据库身份、组织地区范围和角色工作区访问",
                },
                {
                    "name": "policy-library",
                    "description": "政府来源政策只读列表和详情",
                },
                {
                    "name": "historical-qa",
                    "description": "经隐私筛选的政府历史问答只读列表和详情",
                },
                {
                    "name": "classification",
                    "description": "经身份范围保护的深圳部门分类",
                },
                {
                    "name": "policy-qa",
                    "description": "受身份范围保护的政策智能问答",
                },
                {
                    "name": "consultation",
                    "description": "部门自动分派、答复与可选公开的咨询闭环",
                },
            ],
        )
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        for model in (ApiErrorDetail, ApiErrorResponse, PaginationMeta, PaginationParams):
            components.setdefault(model.__name__, model.model_json_schema())
        page_schema = PageResponse[dict[str, Any]].model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        page_schema.pop("$defs", None)
        page_schema["title"] = "PageResponse"
        components.setdefault("PageResponse", page_schema)
        schema["x-api-version"] = "v1"
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"service": settings.app_name, "docs": "/docs", "api_prefix": settings.api_prefix}

    return app
