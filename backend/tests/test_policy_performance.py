from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.database import request_db_session
from app.modules.iam.repository import IdentityRepository
from app.modules.iam.service import identity_repository_dependency
from app.modules.policy.repository import PolicyRepository
from app.modules.policy.service import policy_repository_dependency


class MappingResult:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows

    def mappings(self):
        return self

    def all(self) -> list[dict[str, object]]:
        return self._rows


class ScalarResult:
    def __init__(self, value: int) -> None:
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class RecordingSession:
    def __init__(self, rows: list[dict[str, object]], *, fallback_total: int = 0) -> None:
        self.rows = rows
        self.fallback_total = fallback_total
        self.statements: list[str] = []

    def execute(self, statement):
        sql = str(statement)
        self.statements.append(sql)
        if len(self.statements) == 1:
            return MappingResult(self.rows)
        return ScalarResult(self.fallback_total)


def policy_row(*, total: int = 20) -> dict[str, object]:
    return {
        "id": UUID("f7425d1e-4777-59dd-86c4-b269d84384b5"),
        "title": "深圳政策",
        "document_no": None,
        "issuing_organization": "深圳市人民政府",
        "source_url": "https://www.sz.gov.cn/policy/1",
        "published_date": date(2026, 8, 1),
        "effective_status": "valid",
        "_total": total,
    }


def test_iam_and_policy_repositories_share_one_request_session() -> None:
    app = FastAPI()
    shared_session = object()
    provider_calls = 0

    def settings_override() -> Settings:
        return Settings(
            _env_file=None,
            auth_required=True,
            database_url="postgresql+psycopg://placeholder.invalid/postgres",
            policy_fixture_path=None,
        )

    def session_override():
        nonlocal provider_calls
        provider_calls += 1
        yield shared_session

    @app.get("/probe")
    def probe(
        identity_repository=Depends(identity_repository_dependency),
        policy_repository=Depends(policy_repository_dependency),
    ) -> dict[str, bool]:
        assert isinstance(identity_repository, IdentityRepository)
        assert isinstance(policy_repository, PolicyRepository)
        return {
            "same_session": identity_repository._session is policy_repository._session,
        }

    app.dependency_overrides[get_settings] = settings_override
    app.dependency_overrides[request_db_session] = session_override

    with TestClient(app) as client:
        response = client.get("/probe")

    assert response.status_code == 200
    assert response.json() == {"same_session": True}
    assert provider_calls == 1


def test_non_empty_policy_page_uses_one_projected_statement() -> None:
    session = RecordingSession([policy_row()])

    result = PolicyRepository(session).list(offset=0, limit=10, query=None)  # type: ignore[arg-type]

    assert result.total == 20
    assert len(result.items) == 1
    assert len(session.statements) == 1
    sql = session.statements[0].lower()
    assert "count(*) over" in sql
    assert "content_text" not in sql
    assert "content_sha256" not in sql
    assert "collected_at" not in sql


def test_filtered_page_keeps_filter_in_projected_statement() -> None:
    session = RecordingSession([policy_row(total=1)])

    result = PolicyRepository(session).list(  # type: ignore[arg-type]
        offset=0,
        limit=10,
        query="住房公积金",
    )

    assert result.total == 1
    assert len(session.statements) == 1
    sql = session.statements[0].lower()
    assert "lower(app.policy_documents.title) like lower" in sql
    assert "lower(app.policy_documents.issuing_organization) like lower" in sql


def test_out_of_range_page_uses_one_bounded_count_fallback() -> None:
    session = RecordingSession([], fallback_total=20)

    result = PolicyRepository(session).list(offset=20, limit=10, query=None)  # type: ignore[arg-type]

    assert result.items == []
    assert result.total == 20
    assert len(session.statements) == 2
    assert "count(*)" in session.statements[1].lower()


def test_empty_first_page_does_not_need_count_fallback() -> None:
    session = RecordingSession([])

    result = PolicyRepository(session).list(offset=0, limit=10, query="missing")  # type: ignore[arg-type]

    assert result.items == []
    assert result.total == 0
    assert len(session.statements) == 1
