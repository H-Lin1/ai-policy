from __future__ import annotations

from dataclasses import replace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from app.core.auth import Principal
from app.core.config import Settings
from app.core.errors import AppError
from app.factory import create_app
from app.modules.iam.repository import IdentityRecord, IdentityRepository, RoleRecord
from app.modules.iam.service import IdentityContext, get_current_identity, resolve_identity

USER_ID = UUID("00000000-0000-4000-8000-000000000111")
REGION_ID = UUID("10000000-0000-4000-8000-000000000001")


class FakeRepository:
    def __init__(self, record: IdentityRecord | None = None, error: Exception | None = None) -> None:
        self.record = record
        self.error = error

    def load(self, user_id: UUID) -> IdentityRecord | None:
        if self.error is not None:
            raise self.error
        assert user_id == USER_ID
        return self.record


def identity_record(
    role: str = "individual",
    *,
    organization_type: str | None = None,
    organization_active: bool = True,
) -> IdentityRecord:
    organization_code = f"sz-{role}" if organization_type else None
    return IdentityRecord(
        user_id=USER_ID,
        display_name=f"{role} user",
        profile_status="active",
        region_code="sz",
        region_name="深圳市",
        region_active=True,
        organization_code=organization_code,
        organization_name=f"{role} organization" if organization_code else None,
        organization_type=organization_type,
        organization_active=organization_active if organization_code else False,
        organization_region_id=REGION_ID if organization_code else None,
        profile_region_id=REGION_ID,
        roles=(RoleRecord(role, role.title(), True, True),),
    )


def principal(*, subject: str = str(USER_ID), bypass: bool = False) -> Principal:
    return Principal(subject=subject, email="user@example.com", development_bypass=bypass)


@pytest.mark.parametrize(
    ("role", "organization_type"),
    [
        ("individual", None),
        ("enterprise", "enterprise"),
        ("government", "government"),
        ("admin", "platform"),
    ],
)
def test_resolve_identity_accepts_each_database_role(role, organization_type) -> None:
    identity = resolve_identity(
        principal(),
        FakeRepository(identity_record(role, organization_type=organization_type)),
    )

    assert identity.subject == str(USER_ID)
    assert identity.role_codes == (role,)
    assert identity.region_code == "sz"
    assert identity.organization_type == organization_type


@pytest.mark.parametrize(
    ("record", "code"),
    [
        (None, "PROFILE_NOT_PROVISIONED"),
        (replace(identity_record(), profile_status="disabled"), "ACCOUNT_DISABLED"),
        (replace(identity_record(), region_code="beijing"), "IDENTITY_SCOPE_INACTIVE"),
        (replace(identity_record(), region_active=False), "IDENTITY_SCOPE_INACTIVE"),
        (replace(identity_record(), roles=()), "ROLE_NOT_ASSIGNED"),
        (
            replace(identity_record(), roles=(RoleRecord("individual", "个人", False, True),)),
            "ROLE_NOT_ASSIGNED",
        ),
        (
            identity_record("government", organization_type="enterprise"),
            "IDENTITY_SCOPE_INACTIVE",
        ),
        (
            identity_record("government", organization_type=None),
            "IDENTITY_SCOPE_INACTIVE",
        ),
        (
            identity_record("government", organization_type="government", organization_active=False),
            "IDENTITY_SCOPE_INACTIVE",
        ),
    ],
)
def test_resolve_identity_fails_closed_for_invalid_application_state(record, code) -> None:
    with pytest.raises(AppError) as exc_info:
        resolve_identity(principal(), FakeRepository(record))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == code


def test_resolve_identity_rejects_non_uuid_subject() -> None:
    with pytest.raises(AppError) as exc_info:
        resolve_identity(principal(subject="not-a-uuid"), FakeRepository(identity_record()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "AUTH_INVALID"


def test_resolve_identity_sanitizes_unavailable_store() -> None:
    marker = "database-secret-marker"
    for repository in (None, FakeRepository(error=RuntimeError(marker))):
        with pytest.raises(AppError) as exc_info:
            resolve_identity(principal(), repository)
        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "IDENTITY_STORE_UNAVAILABLE"
        assert marker not in exc_info.value.message


def test_development_bypass_does_not_require_database() -> None:
    identity = resolve_identity(principal(subject="local-dev", bypass=True), None)

    assert identity.development_bypass is True
    assert identity.role_codes == ("developer",)
    assert identity.region_code is None


def test_identity_repository_query_is_schema_qualified_and_stably_ordered() -> None:
    statements = []

    class EmptySession:
        def execute(self, statement):
            statements.append(statement)
            return type("EmptyResult", (), {"all": lambda self: []})()

    assert IdentityRepository(EmptySession()).load(USER_ID) is None  # type: ignore[arg-type]
    assert len(statements) == 1
    sql = str(statements[0].compile(dialect=postgresql.dialect()))
    assert "FROM app.profiles" in sql
    assert "LEFT OUTER JOIN app.user_roles" in sql
    assert "LEFT OUTER JOIN app.roles" in sql
    assert "ORDER BY app.roles.code ASC" in sql


def api_identity(role: str = "individual", organization_type: str | None = None) -> IdentityContext:
    record = identity_record(role, organization_type=organization_type)
    return resolve_identity(principal(), FakeRepository(record))


def test_me_and_role_workspace_use_database_identity_and_no_store() -> None:
    app = create_app(
        Settings(_env_file=None, auth_required=True, database_url=None, supabase_url=None)
    )
    app.dependency_overrides[get_current_identity] = lambda: api_identity()

    with TestClient(app) as client:
        me = client.get("/api/v1/me", headers={"X-Request-ID": "iam-me"})
        allowed = client.get(
            "/api/v1/iam/workspaces/individual",
            headers={"X-Request-ID": "iam-allowed"},
        )
        denied = client.get(
            "/api/v1/iam/workspaces/admin",
            headers={"X-Request-ID": "iam-denied"},
        )
        invalid = client.get("/api/v1/iam/workspaces/reviewer")

    assert me.status_code == 200
    assert me.headers["Cache-Control"] == "no-store"
    assert me.headers["X-Request-ID"] == "iam-me"
    assert me.json()["roles"] == ["individual"]
    assert me.json()["region"] == {"code": "sz", "name": "深圳市"}
    assert allowed.status_code == 200
    assert allowed.headers["Cache-Control"] == "no-store"
    assert allowed.json()["role"] == "individual"
    assert denied.status_code == 403
    assert denied.headers["Cache-Control"] == "no-store"
    assert denied.json()["error"]["code"] == "ROLE_FORBIDDEN"
    assert denied.json()["request_id"] == denied.headers["X-Request-ID"] == "iam-denied"
    assert invalid.status_code == 422
    assert invalid.headers["Cache-Control"] == "no-store"
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    ("role", "organization_type"),
    [
        ("individual", None),
        ("enterprise", "enterprise"),
        ("government", "government"),
        ("admin", "platform"),
    ],
)
def test_each_database_role_can_enter_its_matching_http_workspace(
    role, organization_type
) -> None:
    app = create_app(
        Settings(_env_file=None, auth_required=True, database_url=None, supabase_url=None)
    )
    app.dependency_overrides[get_current_identity] = lambda: api_identity(
        role,
        organization_type,
    )

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/iam/workspaces/{role}",
            headers={"X-Request-ID": f"iam-{role}"},
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"] == f"iam-{role}"
    assert response.json()["role"] == role
    expected_organization = f"sz-{role}" if organization_type else None
    assert (response.json()["organization"] or {}).get("code") == expected_organization


def test_identity_openapi_documents_contract_and_errors() -> None:
    app = create_app(Settings(_env_file=None, database_url=None, supabase_url=None))
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    me = schema["paths"]["/api/v1/me"]["get"]
    workspace = schema["paths"]["/api/v1/iam/workspaces/{role}"]["get"]
    assert me["operationId"] == "currentPrincipal"
    assert {"401", "403", "503"}.issubset(me["responses"])
    assert workspace["operationId"] == "iamWorkspaceAccess"
    assert {"401", "403", "422", "503"}.issubset(workspace["responses"])
