from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="development",
        app_version="test",
        auth_required=True,
        database_url=None,
        supabase_url=None,
        supabase_jwks_url=None,
        supabase_jwt_issuer=None,
        cors_origins="http://localhost:5173",
    )


@pytest.fixture()
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
