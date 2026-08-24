from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app
from app.modules.iam.repository import RoleRecord
from app.modules.iam.service import IdentityContext, get_current_identity
from app.modules.policy_qa.adapters import (
    PolicyAnswerEngine,
    PolicyAnswerError,
    PolicyAnswerResult,
    PolicyQuestion,
)
from app.modules.policy_qa.router import policy_answer_engine_dependency


class RecordingEngine:
    def __init__(self) -> None:
        self.calls: list[PolicyQuestion] = []

    def answer(self, question: PolicyQuestion) -> PolicyAnswerResult:
        self.calls.append(question)
        return PolicyAnswerResult("sz", "placeholder", "演示回答", (), ("这是演示。",))


class FailingEngine:
    def answer(self, question: PolicyQuestion) -> PolicyAnswerResult:
        raise PolicyAnswerError("RAG_GENERATION_FAILED", "internal provider secret")


def identity(
    *, roles: tuple[str, ...] = ("individual",), region_code: str | None = "sz"
) -> IdentityContext:
    return IdentityContext(
        "00000000-0000-4000-8000-000000000115",
        "user@example.com",
        "问答用户",
        tuple(RoleRecord(role, role, True, True) for role in roles),
        region_code,
        "深圳市" if region_code else None,
        None,
        None,
        None,
    )


def app_with(
    engine: PolicyAnswerEngine,
    *,
    roles: tuple[str, ...] = ("individual",),
    region_code: str | None = "sz",
):
    app = create_app(Settings(_env_file=None, database_url=None, supabase_url=None))
    app.dependency_overrides[get_current_identity] = lambda: identity(
        roles=roles, region_code=region_code
    )
    app.dependency_overrides[policy_answer_engine_dependency] = lambda: engine
    return app


def test_policy_answer_returns_placeholder_contract_and_no_store() -> None:
    engine = RecordingEngine()
    with TestClient(app_with(engine)) as client:
        response = client.post(
            "/api/v1/policy-answers",
            json={"question": "  企业\n政策咨询  "},
            headers={"X-Request-ID": "policy-qa-answer"},
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "request_id": "policy-qa-answer",
        "region_id": "sz",
        "answer_mode": "placeholder",
        "answer": "演示回答",
        "sources": [],
        "notices": ["这是演示。"],
    }
    assert engine.calls == [PolicyQuestion("企业 政策咨询", "sz", ("individual",))]


def test_policy_answer_rejects_scope_and_role_before_engine() -> None:
    engine = RecordingEngine()
    with TestClient(app_with(engine, roles=(), region_code="sz")) as client:
        role_denied = client.post("/api/v1/policy-answers", json={"question": "政策咨询"})
    with TestClient(app_with(engine, region_code="beijing")) as client:
        region_denied = client.post("/api/v1/policy-answers", json={"question": "政策咨询"})

    assert role_denied.status_code == 403
    assert role_denied.json()["error"]["code"] == "ROLE_FORBIDDEN"
    assert region_denied.status_code == 403
    assert region_denied.json()["error"]["code"] == "IDENTITY_SCOPE_INACTIVE"
    assert engine.calls == []


def test_policy_answer_invalid_or_engine_failure_is_safe() -> None:
    with TestClient(app_with(RecordingEngine())) as client:
        invalid = client.post("/api/v1/policy-answers", json={"question": " \n "})
    sensitive_question = "不可回显问题"
    with TestClient(app_with(FailingEngine())) as client:
        failure = client.post("/api/v1/policy-answers", json={"question": sensitive_question})

    assert invalid.status_code == 422
    assert invalid.headers["Cache-Control"] == "no-store"
    assert failure.status_code == 503
    assert failure.headers["Cache-Control"] == "no-store"
    assert failure.json()["error"]["code"] == "POLICY_ANSWER_UNAVAILABLE"
    assert sensitive_question not in failure.text
    assert "provider secret" not in failure.text


def test_policy_answer_validation_error_is_not_cacheable() -> None:
    with TestClient(app_with(RecordingEngine())) as client:
        response = client.post("/api/v1/policy-answers", json={"question": ""})

    assert response.status_code == 422
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
