from __future__ import annotations

from typing import Self

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import warm_database_connection
from app.main import create_app


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, statement: object) -> None:
        self.statements.append(str(statement))


class FakeEngine:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def connect(self) -> FakeConnection:
        return self.connection


class FailingEngine:
    def connect(self) -> FakeConnection:
        raise RuntimeError("private connection detail")


def test_warm_database_connection_executes_read_only_probe(monkeypatch) -> None:
    connection = FakeConnection()
    monkeypatch.setattr(
        "app.core.database.database_engine",
        lambda _settings: FakeEngine(connection),
    )

    status, duration_ms = warm_database_connection(Settings(_env_file=None))

    assert status == "ok"
    assert duration_ms >= 0
    assert connection.statements == ["SELECT 1"]


def test_warm_database_connection_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.core.database.database_engine",
        lambda _settings: FailingEngine(),
    )

    status, duration_ms = warm_database_connection(Settings(_env_file=None))

    assert status == "unavailable"
    assert duration_ms >= 0


def test_application_lifespan_warms_configured_database(monkeypatch) -> None:
    calls: list[Settings] = []

    def warm(settings: Settings):
        calls.append(settings)
        return "ok", 12.5

    monkeypatch.setattr("app.factory.warm_database_connection", warm)
    settings = Settings(
        _env_file=None,
        app_env="development",
        auth_required=True,
        database_url="postgresql+psycopg://placeholder.invalid/postgres",
    )

    with TestClient(create_app(settings)) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert calls == [settings]
