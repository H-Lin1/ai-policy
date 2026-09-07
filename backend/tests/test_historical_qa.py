from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app
from app.modules.historical_qa.repository import FixtureHistoricalQaRepository
from app.modules.historical_qa.service import historical_qa_repository_dependency
from app.modules.historical_qa.source import SourceValidationError, normalize_source_row, read_csvs
from app.modules.iam.service import IdentityContext, get_current_identity

FIXTURE_PATH = Path(__file__).parents[1] / "app/modules/historical_qa/fixtures/historical_qa.jsonl"
DATASETS_ROOT = Path(__file__).parents[1] / "datasets"
SOURCE_PATHS = (
    DATASETS_ROOT / "2024-2025/sz_gov_qa_2024-2025_cleaned_model_validated_v2_name_adjudicated.csv",
    DATASETS_ROOT / "2025-2026/sz_gov_qa_2025-2026_cleaned_model_validated_v2_name_adjudicated.csv",
    DATASETS_ROOT / "2026至今/sz_gov_qa_2026至今_cleaned_model_validated_v2_name_adjudicated.csv",
)


def identity(*, region_code: str | None = "sz") -> IdentityContext:
    return IdentityContext("00000000-0000-4000-8000-000000000113", "user@example.com", "QA reader", (), region_code, "深圳市" if region_code else None, None, None, None)


def source_row(**overrides: object) -> dict[str, object]:
    return {
        "留言主题": "政务咨询", "留言内容": "请问业务如何办理？", "答复内容": "您好，请按办事指南提交申请。",
        "来源链接": "https://www.sz.gov.cn/hdjlpt/detail?pid=1", "留言时间": "2026-08-01 09:00:00",
        "答复时间": "2026-08-02 10:00:00", "发布机构": "深圳市人民政府办公厅", "抓取时间": "2026-08-03 11:00:00",
        "是否含法律依据": "否", "法律依据名称": "", "法律依据完整引文": "", "模型识别法律依据名称": "",
        "模型识别法律依据完整引文": "", "分歧仲裁结果": "规则对", **overrides,
    }


def app_with_fixture(*, region_code: str | None = "sz"):
    app = create_app(Settings(_env_file=None, database_url=None, supabase_url=None))
    repository = FixtureHistoricalQaRepository.from_jsonl(FIXTURE_PATH)
    app.dependency_overrides[get_current_identity] = lambda: identity(region_code=region_code)
    app.dependency_overrides[historical_qa_repository_dependency] = lambda: repository
    return app


def test_source_adapter_normalizes_and_excludes_sensitive_records() -> None:
    record = normalize_source_row(source_row(留言内容="第一行\r\n第二行\x00"))
    assert record.question_text == "第一行\n第二行"
    assert len(record.content_sha256) == 64
    with pytest.raises(SourceValidationError, match="SENSITIVE_PHONE"):
        normalize_source_row(source_row(答复内容="请拨打0755-12345678咨询"))
    with pytest.raises(SourceValidationError, match="SENSITIVE_EMAIL"):
        normalize_source_row(source_row(答复内容="请发邮件至name@example.com"))
    with pytest.raises(SourceValidationError, match="SOURCE_HOST_NOT_ALLOWED"):
        normalize_source_row(source_row(来源链接="https://example.com/qa/1"))


def test_source_csvs_and_fixture_are_privacy_screened_and_deterministic() -> None:
    records, rejected = read_csvs(SOURCE_PATHS)
    fixture = FixtureHistoricalQaRepository.from_jsonl(FIXTURE_PATH)
    actual = fixture.list(offset=0, limit=20, query=None).items
    assert len(records) == 1308
    assert rejected["SENSITIVE_PHONE"] > 0
    assert len(actual) == 20
    assert {item.id for item in actual}
    assert {item.id for item in actual} == {item.id for item in FixtureHistoricalQaRepository.from_jsonl(FIXTURE_PATH).list(offset=0, limit=20, query=None).items}


def test_historical_qa_list_detail_scope_and_no_store() -> None:
    with TestClient(app_with_fixture()) as client:
        response = client.get("/api/v1/qa?page=1&page_size=5", headers={"X-Request-ID": "qa-list"})
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json()["meta"]["total"] == 20
        record_id = response.json()["items"][0]["id"]
        detail = client.get(f"/api/v1/qa/{record_id}")
        missing = client.get(f"/api/v1/qa/{UUID('00000000-0000-4000-8000-000000000999')}")
    assert detail.status_code == 200
    assert detail.json()["question_text"] and detail.json()["answer_text"]
    assert "数据ID" not in detail.text and "受理编号" not in detail.text
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "HISTORICAL_QA_NOT_FOUND"
    with TestClient(app_with_fixture(region_code="gd")) as client:
        assert client.get("/api/v1/qa").status_code == 403


def test_historical_qa_openapi_contract() -> None:
    with TestClient(app_with_fixture()) as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert paths["/api/v1/qa"]["get"]["operationId"] == "historicalQaList"
    assert paths["/api/v1/qa/{qa_id}"]["get"]["operationId"] == "historicalQaDetail"
