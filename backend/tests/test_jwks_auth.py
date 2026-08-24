from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.modules.iam.repository import IdentityRecord, RoleRecord
from app.modules.iam.service import identity_repository_dependency

TEST_USER_ID = "00000000-0000-4000-8000-000000000123"


class _FakeSigningKey:
    def __init__(self, key: object) -> None:
        self.key = key


class _FakeJwksClient:
    def __init__(self, key: object) -> None:
        self.key = key

    def get_signing_key(self, key_id: str) -> _FakeSigningKey:
        return _FakeSigningKey(self.key)


class _FakeIdentityRepository:
    def load(self, user_id):
        return IdentityRecord(
            user_id=user_id,
            display_name="数据库个人用户",
            profile_status="active",
            region_code="sz",
            region_name="深圳市",
            region_active=True,
            organization_code=None,
            organization_name=None,
            organization_type=None,
            organization_active=False,
            organization_region_id=None,
            profile_region_id=None,
            roles=(RoleRecord("individual", "个人", True, True),),
        )


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="development",
        app_version="test",
        auth_required=True,
        database_url=None,
        supabase_url="https://example.supabase.co",
        cors_origins="http://localhost:5173",
    )


def _token(private_key: ec.EllipticCurvePrivateKey, *, expires_at: datetime) -> str:
    issued_at = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": TEST_USER_ID,
            "email": "demo@example.com",
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
            "app_metadata": {"roles": ["admin", "reviewer"]},
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "test-key"},
    )


def test_current_supabase_jwks_token_is_accepted(monkeypatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(
        "app.core.auth._get_jwks_client",
        lambda _: _FakeJwksClient(private_key.public_key()),
    )
    token = _token(private_key, expires_at=datetime.now(UTC) + timedelta(minutes=5))

    app = create_app(_settings())
    app.dependency_overrides[identity_repository_dependency] = _FakeIdentityRepository
    with TestClient(app) as client:
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
        admin_workspace = client.get(
            "/api/v1/iam/workspaces/admin",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "subject": TEST_USER_ID,
        "email": "demo@example.com",
        "display_name": "数据库个人用户",
        "roles": ["individual"],
        "role_summaries": [{"code": "individual", "name": "个人"}],
        "region": {"code": "sz", "name": "深圳市"},
        "organization": None,
        "development_bypass": False,
    }
    assert response.headers["Cache-Control"] == "no-store"
    assert admin_workspace.status_code == 403
    assert admin_workspace.headers["Cache-Control"] == "no-store"
    assert admin_workspace.json()["error"]["code"] == "ROLE_FORBIDDEN"


def test_expired_supabase_token_is_rejected(monkeypatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(
        "app.core.auth._get_jwks_client",
        lambda _: _FakeJwksClient(private_key.public_key()),
    )
    token = _token(private_key, expires_at=datetime.now(UTC) - timedelta(minutes=1))

    with TestClient(create_app(_settings())) as client:
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_jwks_configuration_is_required_for_token_verification() -> None:
    settings = Settings(
        _env_file=None,
        app_env="development",
        app_version="test",
        auth_required=True,
        database_url=None,
        supabase_url=None,
        supabase_jwks_url=None,
        supabase_jwt_issuer=None,
    )
    with TestClient(create_app(settings)) as client:
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer eyJ.invalid.token"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_NOT_CONFIGURED"


def test_ready_check_reports_auth_configuration_separately(client: TestClient) -> None:
    body = client.get("/api/v1/health/ready").json()

    assert body["checks"]["authentication"] == "not_configured"


def test_unsupported_algorithm_is_rejected_without_fetching_jwks(monkeypatch) -> None:
    called = False

    def unexpected_client(_: str):
        nonlocal called
        called = True
        raise AssertionError("JWKS must not be fetched for a disallowed algorithm")

    monkeypatch.setattr("app.core.auth._get_jwks_client", unexpected_client)
    token = jwt.encode(
        {
            "sub": "user-123",
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        },
        "legacy-secret-with-at-least-32-bytes",
        algorithm="HS256",
        headers={"kid": "legacy-key"},
    )

    with TestClient(create_app(_settings())) as client:
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID"
    assert called is False


def test_missing_key_id_is_rejected_without_fetching_jwks(monkeypatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(
        "app.core.auth._get_jwks_client",
        lambda _: (_ for _ in ()).throw(AssertionError("JWKS must not be fetched")),
    )
    issued_at = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "user-123",
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "iat": int(issued_at.timestamp()),
            "exp": int((issued_at + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="ES256",
    )

    with TestClient(create_app(_settings())) as client:
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID"


def test_production_cannot_enable_development_auth_bypass() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        app_version="test",
        auth_required=False,
        database_url=None,
        supabase_url=None,
    )

    with TestClient(create_app(settings)) as client:
        me_response = client.get("/api/v1/me")
        ready_response = client.get("/api/v1/health/ready")

    assert me_response.status_code == 503
    assert me_response.json()["error"]["code"] == "AUTH_NOT_CONFIGURED"
    assert ready_response.status_code == 503
    assert ready_response.json()["error"]["details"]["authentication"] == (
        "invalid_production_bypass"
    )


def test_wrong_issuer_and_empty_subject_are_rejected(monkeypatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(
        "app.core.auth._get_jwks_client",
        lambda _: _FakeJwksClient(private_key.public_key()),
    )
    issued_at = datetime.now(UTC)
    base_payload = {
        "sub": "user-123",
        "aud": "authenticated",
        "iss": "https://wrong-project.supabase.co/auth/v1",
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=5)).timestamp()),
    }
    wrong_issuer_token = jwt.encode(
        base_payload,
        private_key,
        algorithm="ES256",
        headers={"kid": "test-key"},
    )
    empty_subject_token = jwt.encode(
        {
            **base_payload,
            "sub": "   ",
            "iss": "https://example.supabase.co/auth/v1",
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "test-key"},
    )

    with TestClient(create_app(_settings())) as client:
        wrong_issuer = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {wrong_issuer_token}"},
        )
        empty_subject = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {empty_subject_token}"},
        )

    assert wrong_issuer.status_code == 401
    assert wrong_issuer.json()["error"]["code"] == "AUTH_INVALID"
    assert empty_subject.status_code == 401
    assert empty_subject.json()["error"]["code"] == "AUTH_INVALID"


def test_jwks_dependency_failure_is_distinct_from_unknown_key(monkeypatch) -> None:
    class _BrokenJwksClient:
        def __init__(self, error: Exception) -> None:
            self.error = error

        def get_signing_key(self, key_id: str) -> _FakeSigningKey:
            raise self.error

    private_key = ec.generate_private_key(ec.SECP256R1())
    token = _token(private_key, expires_at=datetime.now(UTC) + timedelta(minutes=5))

    monkeypatch.setattr(
        "app.core.auth._get_jwks_client",
        lambda _: _BrokenJwksClient(jwt.PyJWKClientConnectionError("timeout")),
    )
    with TestClient(create_app(_settings())) as client:
        unavailable = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    monkeypatch.setattr(
        "app.core.auth._get_jwks_client",
        lambda _: _BrokenJwksClient(
            jwt.PyJWKClientError('Unable to find a signing key that matches: "test-key"')
        ),
    )
    with TestClient(create_app(_settings())) as client:
        unknown_key = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "AUTH_NOT_CONFIGURED"
    assert unknown_key.status_code == 401
    assert unknown_key.json()["error"]["code"] == "AUTH_INVALID"


def test_malformed_jwks_is_reported_as_dependency_failure(monkeypatch) -> None:
    class _MalformedJwksClient:
        def get_signing_key(self, key_id: str) -> _FakeSigningKey:
            raise ValueError("malformed JSON")

    private_key = ec.generate_private_key(ec.SECP256R1())
    token = _token(private_key, expires_at=datetime.now(UTC) + timedelta(minutes=5))
    monkeypatch.setattr("app.core.auth._get_jwks_client", lambda _: _MalformedJwksClient())

    with TestClient(create_app(_settings())) as client:
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_NOT_CONFIGURED"


def test_valid_token_without_identity_store_fails_closed(monkeypatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(
        "app.core.auth._get_jwks_client",
        lambda _: _FakeJwksClient(private_key.public_key()),
    )
    token = _token(private_key, expires_at=datetime.now(UTC) + timedelta(minutes=5))

    with TestClient(create_app(_settings())) as client:
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "IDENTITY_STORE_UNAVAILABLE"
    assert "admin" not in response.text


def test_malformed_supabase_url_is_not_reported_as_configured() -> None:
    settings = Settings(
        _env_file=None,
        app_env="development",
        auth_required=True,
        database_url=None,
        supabase_url="not-a-url",
    )

    assert settings.auth_configuration_status == "not_configured"
