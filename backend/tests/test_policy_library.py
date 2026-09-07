from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app
from app.modules.iam.service import IdentityContext, get_current_identity
from app.modules.policy.repository import FixturePolicyRepository
from app.modules.policy.service import policy_repository_dependency
from app.modules.policy.source import SourceValidationError, normalize_source_row, read_csv

FIXTURE_PATH = Path(__file__).parents[1] / "app/modules/policy/fixtures/policies.jsonl"
SOURCE_PATH = Path(__file__).parents[1] / "datasets/sz_policy_documents.csv"
USER_ID = "00000000-0000-4000-8000-000000000111"


def identity(*, region_code: str | None = "sz") -> IdentityContext:
    return IdentityContext(
        subject=USER_ID,
        email="user@example.com",
        display_name="policy reader",
        roles=(),
        region_code=region_code,
        region_name="深圳市" if region_code else None,
        organization_code=None,
        organization_name=None,
        organization_type=None,
    )


def app_with_fixture(*, region_code: str | None = "sz"):
    app = create_app(Settings(_env_file=None, database_url=None, supabase_url=None))
    repository = FixturePolicyRepository.from_jsonl(FIXTURE_PATH)
    app.dependency_overrides[get_current_identity] = lambda: identity(region_code=region_code)
    app.dependency_overrides[policy_repository_dependency] = lambda: repository
    return app


def source_row(**overrides: object) -> dict[str, object]:
    content = str(overrides.pop("content_text", "第一条\r\n政策正文\x00"))
    normalized = "第一条\n政策正文"
    return {
        "crawl_status": "success",
        "title": "深圳政策",
        "document_no": "深规〔2026〕1号",
        "issuing_organization": "深圳市某局",
        "source_url": "https://www.sz.gov.cn/policy/1",
        "document_url": "",
        "published_date": "2026-08-01",
        "collected_at": "2026-08-01T12:00:00+08:00",
        "content_text": content,
        "content_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
        "region_code": "sz",
        **overrides,
    }


def test_source_adapter_normalizes_content_and_verifies_hash() -> None:
    result = normalize_source_row(source_row())

    assert result.content_text == "第一条\n政策正文"
    assert result.content_sha256 == hashlib.sha256(result.content_text.encode()).hexdigest()
    assert result.collected_at == datetime(2026, 8, 1, 4, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"crawl_status": "needs_review"}, "CRAWL_STATUS_NOT_SUCCESS"),
        ({"source_url": "http://www.sz.gov.cn/policy/1"}, "SOURCE_HOST_NOT_ALLOWED"),
        ({"source_url": "https://gov-example.com/policy/1"}, "SOURCE_HOST_NOT_ALLOWED"),
        ({"region_code": "gd"}, "REGION_NOT_SUPPORTED"),
        ({"content_sha256": "0" * 64}, "CONTENT_HASH_MISMATCH"),
    ],
)
def test_source_adapter_rejects_invalid_records(override, reason) -> None:
    with pytest.raises(SourceValidationError, match=reason):
        normalize_source_row(source_row(**override))


def test_supplied_csv_validation_is_deterministic_and_read_only() -> None:
    records, rejected = read_csv(SOURCE_PATH, limit=20)

    assert len(records) == 20
    assert all(record.source_url.startswith("https://") for record in records)
    assert all(record.region_code == "sz" for record in records)
    assert rejected == {
        "CONTENT_HASH_MISMATCH": 4,
        "CRAWL_STATUS_NOT_SUCCESS": 852,
        "DUPLICATE_SOURCE_VERSION": 28,
        "SOURCE_HOST_NOT_ALLOWED": 66,
    }


def test_fixture_matches_deterministic_source_sample() -> None:
    expected, _ = read_csv(SOURCE_PATH, limit=20)
    fixture = FixturePolicyRepository.from_jsonl(FIXTURE_PATH)
    actual = fixture.list(offset=0, limit=20, query=None).items

    assert len(actual) == len(expected) == 20
    assert {item.content_sha256 for item in actual} == {item.content_sha256 for item in expected}


def test_policy_list_and_detail_use_fixture_and_no_store() -> None:
    with TestClient(app_with_fixture()) as client:
        response = client.get("/api/v1/policies?page=1&page_size=5", headers={"X-Request-ID": "policy-list"})

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json()["meta"] == {
            "page": 1,
            "page_size": 5,
            "total": 20,
            "total_pages": 4,
            "has_next": True,
            "has_previous": False,
        }
        assert len(response.json()["items"]) == 5
        policy_id = response.json()["items"][0]["id"]
        detail = client.get(f"/api/v1/policies/{policy_id}", headers={"X-Request-ID": "policy-detail"})

    assert detail.status_code == 200
    assert detail.headers["Cache-Control"] == "no-store"
    assert detail.json()["id"] == policy_id
    assert detail.json()["content_text"]
    assert len(detail.json()["content_sha256"]) == 64


def test_policy_filter_and_not_found_are_explicit() -> None:
    with TestClient(app_with_fixture()) as client:
        filtered = client.get("/api/v1/policies?q=住房公积金")
        missing = client.get(f"/api/v1/policies/{UUID('00000000-0000-4000-8000-000000000999')}")

    assert filtered.status_code == 200
    assert filtered.json()["meta"]["total"] > 0
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "POLICY_NOT_FOUND"
    assert missing.json()["request_id"] == missing.headers["X-Request-ID"]


def test_policy_scope_and_store_fail_closed() -> None:
    with TestClient(app_with_fixture(region_code="gd")) as client:
        denied = client.get("/api/v1/policies")

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "IDENTITY_SCOPE_INACTIVE"

    app = create_app(Settings(_env_file=None, database_url=None, policy_fixture_path=None))
    app.dependency_overrides[get_current_identity] = lambda: identity()
    with TestClient(app) as client:
        unavailable = client.get("/api/v1/policies")

    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "POLICY_STORE_UNAVAILABLE"


def test_policy_openapi_contract_is_versioned_and_typed() -> None:
    with TestClient(app_with_fixture()) as client:
        schema = client.get("/openapi.json").json()

    listing = schema["paths"]["/api/v1/policies"]["get"]
    detail = schema["paths"]["/api/v1/policies/{policy_id}"]["get"]
    assert listing["operationId"] == "policyList"
    assert detail["operationId"] == "policyDetail"
    assert {"401", "403", "422", "503"}.issubset(listing["responses"])
    assert {"401", "403", "404", "422", "503"}.issubset(detail["responses"])
