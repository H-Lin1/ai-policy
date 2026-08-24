from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app
from app.modules.intelligence.adapters import (
    ClassifierError,
    ClassifierInput,
    build_department_classifier,
)

CHECK_NAMES = (
    "live",
    "ready",
    "auth",
    "iam_auth",
    "identity_not_cacheable",
    "model",
    "model_not_cacheable",
    "classifier_no_mock",
    "classifier_region_boundary",
    "legacy_route_absent",
    "health_not_cacheable",
    "features_snapshot",
    "error_request_id_header",
    "cors_preflight_request_id",
)


def smoke_settings() -> Settings:
    """Build isolated settings so an ambient shell cannot change local smoke behavior."""

    return Settings(
        _env_file=None,
        app_name="AI Policy Service",
        app_env="development",
        app_version="smoke",
        api_prefix="/api/v1",
        log_level="INFO",
        log_format="json",
        host="127.0.0.1",
        port=8000,
        auth_required=True,
        supabase_url=None,
        supabase_jwks_url=None,
        supabase_jwt_issuer=None,
        supabase_jwt_audience="authenticated",
        supabase_jwt_leeway_seconds=30,
        database_url=None,
        cors_origins="http://localhost:5173",
        allow_cors_wildcard=False,
        enable_mocks=False,
        classifier_model_path=None,
        classifier_tokenizer_path=None,
        classifier_label_bindings_path=None,
        classifier_department_embeddings_path=None,
        classifier_supported_regions="sz",
    )


def _response_body(response: Any) -> dict[str, Any]:
    try:
        body = response.json()
    except (TypeError, ValueError):
        return {}
    return body if isinstance(body, dict) else {}


def _error_code(body: dict[str, Any]) -> str | None:
    error = body.get("error")
    return error.get("code") if isinstance(error, dict) else None


def classifier_failure_code(settings: Settings, *, region_id: str) -> str | None:
    try:
        classifier = build_department_classifier(settings)
        classifier.classify(ClassifierInput(text="政策咨询", region_id=region_id))
    except ClassifierError as exc:
        return exc.code
    except Exception:  # noqa: BLE001 - a smoke failure must not print an implementation traceback.
        return None
    return None


def _report_checks(checks: dict[str, bool]) -> int:
    for name in CHECK_NAMES:
        print(f"{name}: {'ok' if checks.get(name, False) else 'FAIL'}")
    return 0 if all(checks.get(name, False) for name in CHECK_NAMES) else 1


def main() -> int:
    try:
        settings = smoke_settings()
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            live = client.get("/api/v1/health/live")
            ready = client.get("/api/v1/health/ready")
            me = client.get("/api/v1/me")
            iam_workspace = client.get("/api/v1/iam/workspaces/individual")
            model = client.get("/api/v1/ai/readiness")
            features = client.get("/api/v1/system/features")
            boom = client.post(
                "/classify",
                json={"text": "test"},
                headers={"X-Request-ID": "smoke-id"},
            )
            preflight = client.options(
                "/api/v1/health/live",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                    "X-Request-ID": "preflight-smoke-id",
                },
            )
    except Exception:  # noqa: BLE001 - emit named failures instead of an application traceback.
        return _report_checks({})

    ready_body = _response_body(ready)
    me_body = _response_body(me)
    model_body = _response_body(model)
    features_body = _response_body(features)
    boom_body = _response_body(boom)
    checks = {
        "live": live.status_code == 200,
        "ready": ready.status_code == 200 and ready_body.get("status") == "degraded",
        "auth": me.status_code == 401 and _error_code(me_body) == "AUTH_REQUIRED",
        "iam_auth": (
            iam_workspace.status_code == 401
            and _error_code(_response_body(iam_workspace)) == "AUTH_REQUIRED"
        ),
        "identity_not_cacheable": all(
            response.headers.get("Cache-Control") == "no-store"
            for response in (me, iam_workspace)
        ),
        "model": model.status_code == 200 and model_body.get("status") == "not_ready",
        "model_not_cacheable": model.headers.get("Cache-Control") == "no-store",
        "classifier_no_mock": classifier_failure_code(settings, region_id="sz") == "MODEL_NOT_READY",
        "classifier_region_boundary": (
            classifier_failure_code(settings, region_id="beijing") == "REGION_NOT_SUPPORTED"
        ),
        "legacy_route_absent": boom.status_code == 404 and _error_code(boom_body) == "ROUTE_NOT_FOUND",
        "health_not_cacheable": all(
            response.headers.get("Cache-Control") == "no-store" for response in (live, ready)
        ),
        "features_snapshot": (
            features.status_code == 200
            and isinstance(features_body.get("features"), dict)
            and all(isinstance(value, bool) for value in features_body["features"].values())
        ),
        "error_request_id_header": (
            boom.headers.get("X-Request-ID") == boom_body.get("request_id") == "smoke-id"
        ),
        "cors_preflight_request_id": (
            preflight.status_code == 200
            and preflight.headers.get("X-Request-ID") == "preflight-smoke-id"
        ),
    }
    return _report_checks(checks)


if __name__ == "__main__":
    raise SystemExit(main())
