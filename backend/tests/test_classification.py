from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app
from app.modules.iam.service import IdentityContext, get_current_identity
from app.modules.intelligence.adapters import (
    AdapterReadiness,
    ClassificationResult,
    ClassifierInput,
    DepartmentPrediction,
)
from app.modules.system.router import classifier_dependency


class ReadyClassifier:
    supported_regions = ("sz",)

    def readiness(self) -> AdapterReadiness:
        return AdapterReadiness(
            adapter="test-classifier",
            ready=True,
            model_version="test-v1",
            supported_regions=("sz",),
        )

    def classify(self, request: ClassifierInput) -> ClassificationResult:
        return ClassificationResult(
            region_id="sz",
            model_version="test-v1",
            predictions=(DepartmentPrediction("sz-department-01", 0.8),),
        )

    def department_name(self, department_id: str) -> str:
        assert department_id == "sz-department-01"
        return "测试部门"


class NotReadyClassifier(ReadyClassifier):
    def readiness(self) -> AdapterReadiness:
        return AdapterReadiness(
            adapter="test-classifier",
            ready=False,
            reason="model_assets_invalid",
            supported_regions=("sz",),
        )

    def classify(self, request: ClassifierInput) -> ClassificationResult:
        from app.modules.intelligence.adapters import ClassifierError

        raise ClassifierError("MODEL_NOT_READY", "部门分类模型尚未完成验证和配置")


def identity(*, region_code: str | None = "sz") -> IdentityContext:
    return IdentityContext(
        "00000000-0000-4000-8000-000000000114",
        "user@example.com",
        "分类用户",
        (),
        region_code,
        "深圳市" if region_code else None,
        None,
        None,
        None,
    )


def client_with(classifier: object, *, region_code: str | None = "sz") -> TestClient:
    app = create_app(Settings(_env_file=None, database_url=None, supabase_url=None))
    app.dependency_overrides[get_current_identity] = lambda: identity(region_code=region_code)
    app.dependency_overrides[classifier_dependency] = lambda: classifier
    return TestClient(app)


def test_classification_returns_safe_result_and_no_store() -> None:
    with client_with(ReadyClassifier()) as client:
        response = client.post(
            "/api/v1/classifications",
            json={"text": "科技资金申报"},
            headers={"X-Request-ID": "classification-ok"},
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"] == "classification-ok"
    assert response.json() == {
        "region_id": "sz",
        "model_version": "test-v1",
        "predictions": [
            {"department_id": "sz-department-01", "department_name": "测试部门", "confidence": 0.8}
        ],
    }


def test_classification_rejects_region_mismatch_before_inference() -> None:
    with client_with(ReadyClassifier()) as client:
        response = client.post(
            "/api/v1/classifications", json={"text": "科技资金申报", "region_id": "beijing"}
        )

    assert response.status_code == 403
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["error"]["code"] == "REGION_SCOPE_MISMATCH"


def test_classification_scope_and_not_ready_are_explicit() -> None:
    with client_with(ReadyClassifier(), region_code="beijing") as client:
        denied = client.post("/api/v1/classifications", json={"text": "科技资金申报"})
    with client_with(NotReadyClassifier()) as client:
        unavailable = client.post("/api/v1/classifications", json={"text": "科技资金申报"})

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "IDENTITY_SCOPE_INACTIVE"
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "MODEL_NOT_READY"
    assert unavailable.headers["Cache-Control"] == "no-store"


def test_classification_input_is_not_echoed_in_error() -> None:
    sensitive_text = "不可回显的测试输入"
    with client_with(NotReadyClassifier()) as client:
        response = client.post("/api/v1/classifications", json={"text": sensitive_text})

    assert sensitive_text not in response.text
