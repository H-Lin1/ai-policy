from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.modules.system.router as system_router_module
from app.core.config import Settings
from app.main import create_app
from app.modules.intelligence.adapters import (
    AdapterReadiness,
    ClassificationResult,
    ClassifierInput,
)
from app.modules.system.router import classifier_dependency


class ExplodingReadinessClassifier:
    @property
    def supported_regions(self) -> tuple[str, ...]:
        return ("sz",)

    def readiness(self) -> AdapterReadiness:
        raise RuntimeError("unsafe internal readiness detail")

    def classify(self, request: ClassifierInput) -> ClassificationResult:
        raise AssertionError("classification must not run during readiness")


class UnsafeReadinessClassifier(ExplodingReadinessClassifier):
    def readiness(self) -> AdapterReadiness:
        status = object.__new__(AdapterReadiness)
        object.__setattr__(status, "adapter", "department-classifier")
        object.__setattr__(status, "ready", False)
        object.__setattr__(status, "model_version", "/private/unsafe/model-version")
        object.__setattr__(status, "reason", "/private/unsafe/readiness")
        object.__setattr__(status, "supported_regions", ("sz",))
        return status


def test_protected_endpoint_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_legacy_classify_route_is_not_registered(client: TestClient) -> None:
    response = client.post(
        "/classify",
        json={"text": "需要政策咨询"},
        headers={"X-Request-ID": "legacy-route-check"},
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "legacy-route-check"
    assert response.json() == {
        "error": {
            "code": "ROUTE_NOT_FOUND",
            "message": "请求的接口不存在",
            "details": None,
        },
        "request_id": "legacy-route-check",
    }


def test_model_readiness_is_explicitly_not_ready(client: TestClient) -> None:
    response = client.get(
        "/api/v1/ai/readiness",
        headers={"X-Request-ID": "classifier-readiness-check"},
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"] == "classifier-readiness-check"
    assert response.json() == {
        "status": "not_ready",
        "adapter": "department-classifier",
        "model_version": None,
        "reason": "verified_model_not_configured",
    }


def test_model_readiness_invalid_assets_does_not_expose_paths() -> None:
    configured_path = "/private/classifier-assets/not-present"
    settings = Settings(
        _env_file=None,
        app_env="development",
        auth_required=True,
        database_url=None,
        supabase_url=None,
        classifier_model_path=f"{configured_path}/model.bin",
        classifier_tokenizer_path=f"{configured_path}/tokenizer.json",
        classifier_label_bindings_path=f"{configured_path}/labels.json",
    )

    with TestClient(create_app(settings)) as test_client:
        response = test_client.get("/api/v1/ai/readiness")

    assert response.status_code == 200
    assert response.json()["reason"] == "model_assets_invalid"
    assert configured_path not in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_model_readiness_fails_closed_on_adapter_exception(client: TestClient) -> None:
    client.app.dependency_overrides[classifier_dependency] = ExplodingReadinessClassifier
    try:
        response = client.get("/api/v1/ai/readiness")
    finally:
        client.app.dependency_overrides.pop(classifier_dependency, None)

    assert response.status_code == 200
    assert response.json() == {
        "status": "not_ready",
        "adapter": "department-classifier",
        "model_version": None,
        "reason": "readiness_check_failed",
    }
    assert "unsafe internal readiness detail" not in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_model_readiness_fails_closed_on_unsafe_status(client: TestClient) -> None:
    client.app.dependency_overrides[classifier_dependency] = UnsafeReadinessClassifier
    try:
        response = client.get("/api/v1/ai/readiness")
    finally:
        client.app.dependency_overrides.pop(classifier_dependency, None)

    assert response.status_code == 200
    assert response.json()["reason"] == "readiness_check_failed"
    assert "/private/unsafe/readiness" not in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_model_readiness_fails_closed_when_factory_raises(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_factory(settings: Settings) -> None:
        raise RuntimeError("unsafe factory detail")

    monkeypatch.setattr(system_router_module, "build_department_classifier", fail_factory)

    response = client.get("/api/v1/ai/readiness")

    assert response.status_code == 200
    assert response.json()["reason"] == "classifier_configuration_invalid"
    assert "unsafe factory detail" not in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_error_response_preserves_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers={"X-Request-ID": "contract-check"})

    assert response.status_code == 401
    assert response.headers["X-Request-ID"] == "contract-check"
    assert response.json()["request_id"] == "contract-check"
