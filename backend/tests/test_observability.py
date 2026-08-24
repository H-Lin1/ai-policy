from __future__ import annotations

import json
import logging
import sys

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.context import NO_REQUEST, get_request_id
from app.core.features import (
    MOCKS,
    feature_enabled,
    feature_snapshot,
    non_compliant_flags,
)
from app.core.logging import (
    UVICORN_LOGGERS,
    JsonFormatter,
    RequestContextFilter,
    TextFormatter,
    configure_logging,
)
from app.main import create_app

CONTEXT_LOGGER = "ai_policy.tests.context"


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "_env_file": None,
        "app_env": "development",
        "app_version": "test",
        "auth_required": True,
        "database_url": None,
        "supabase_url": None,
        "supabase_jwks_url": None,
        "supabase_jwt_issuer": None,
        "cors_origins": "http://localhost:5173",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def _observability_client(settings: Settings | None = None) -> TestClient:
    app = create_app(settings or _settings())

    @app.get("/api/v1/_observability-log", operation_id="observabilityLogProbe")
    def emit_log() -> dict[str, str]:
        # A logger other than the access-log middleware must still correlate.
        logging.getLogger(CONTEXT_LOGGER).info("probe_record", extra={"probe": "value"})
        return {"context_request_id": get_request_id()}

    @app.get("/api/v1/_observability-boom", operation_id="observabilityBoomProbe")
    def boom() -> dict[str, str]:
        raise RuntimeError("probe failure")

    return TestClient(app, raise_server_exceptions=False)


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="ai_policy.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="probe_record",
        args=None,
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    RequestContextFilter().filter(record)
    return record


def _emitted_records(output: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        records.append(json.loads(line))
    return records


def test_context_request_id_reaches_other_loggers(capsys: pytest.CaptureFixture[str]) -> None:
    # Assert on real emitted output: configure_logging replaces root handlers,
    # so caplog's handler is not part of the configured pipeline.
    with _observability_client() as client:
        response = client.get(
            "/api/v1/_observability-log", headers={"X-Request-ID": "correlation-check"}
        )

    assert response.status_code == 200
    assert response.json()["context_request_id"] == "correlation-check"
    records = _emitted_records(capsys.readouterr().out)
    probe_records = [record for record in records if record["logger"] == CONTEXT_LOGGER]
    access_records = [record for record in records if record["logger"] == "ai_policy.http"]
    assert probe_records and access_records
    for record in probe_records + access_records:
        assert record["request_id"] == "correlation-check"


def test_records_outside_a_request_use_the_placeholder(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with _observability_client():
        pass

    startup = [
        record
        for record in _emitted_records(capsys.readouterr().out)
        if record["logger"] == "ai_policy.app"
    ]
    assert startup
    assert all(record["request_id"] == NO_REQUEST for record in startup)


def test_uvicorn_loggers_use_the_structured_root_pipeline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO", "json")
    logging.getLogger("uvicorn.error").info(
        "server_probe",
        extra={"authorization": "Bearer acceptance-probe-value"},
    )

    records = _emitted_records(capsys.readouterr().out)
    server_records = [record for record in records if record["logger"] == "uvicorn.error"]
    assert len(server_records) == 1
    assert server_records[0]["authorization"] == "***"
    assert "acceptance-probe-value" not in json.dumps(server_records[0])
    for logger_name in UVICORN_LOGGERS:
        server_logger = logging.getLogger(logger_name)
        assert server_logger.handlers == []
        assert server_logger.propagate is True
        assert server_logger.level == logging.NOTSET
        assert server_logger.disabled is (logger_name == "uvicorn.access")


def test_request_id_context_is_cleared_between_requests() -> None:
    with _observability_client() as client:
        first = client.get("/api/v1/_observability-log", headers={"X-Request-ID": "first-request"})
        second = client.get("/api/v1/_observability-log", headers={"X-Request-ID": "second-request"})

    assert first.json()["context_request_id"] == "first-request"
    assert second.json()["context_request_id"] == "second-request"
    assert get_request_id() == NO_REQUEST


def test_unhandled_error_sends_request_id_header_matching_body() -> None:
    with _observability_client() as client:
        response = client.get(
            "/api/v1/_observability-boom", headers={"X-Request-ID": "boom-check"}
        )

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["details"] is None
    assert body["request_id"] == "boom-check"
    assert response.headers["X-Request-ID"] == "boom-check"
    assert "Traceback" not in response.text


def test_client_error_sends_request_id_header_matching_body() -> None:
    with _observability_client() as client:
        not_found = client.post("/classify", json={"text": "x"}, headers={"X-Request-ID": "nf"})
        unauthorized = client.get("/api/v1/me", headers={"X-Request-ID": "unauth"})

    assert not_found.status_code == 404
    assert not_found.headers["X-Request-ID"] == not_found.json()["request_id"] == "nf"
    assert unauthorized.status_code == 401
    assert unauthorized.headers["X-Request-ID"] == unauthorized.json()["request_id"] == "unauth"


def test_method_not_allowed_keeps_allow_header_and_request_id() -> None:
    with _observability_client() as client:
        response = client.post("/api/v1/health/live", headers={"X-Request-ID": "method-check"})

    assert response.status_code == 405
    assert "Allow" in response.headers
    assert response.headers["X-Request-ID"] == response.json()["request_id"] == "method-check"


def test_cors_preflight_has_a_request_id() -> None:
    with _observability_client() as client:
        preflight = client.options(
            "/api/v1/health/live",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "X-Request-ID": "preflight-check",
            },
        )
        cors_response = client.get(
            "/api/v1/health/live",
            headers={"Origin": "http://localhost:5173"},
        )

    assert preflight.status_code == 200
    assert preflight.headers["X-Request-ID"] == "preflight-check"
    assert cors_response.headers["X-Request-ID"]
    assert cors_response.headers["Access-Control-Expose-Headers"] == "X-Request-ID"


def test_json_log_records_are_parseable_and_carry_request_id() -> None:
    formatted = JsonFormatter().format(_record(method="GET", path="/api/v1/health/live"))
    payload = json.loads(formatted)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "ai_policy.tests"
    assert payload["message"] == "probe_record"
    assert payload["request_id"] == NO_REQUEST
    assert payload["timestamp"].endswith("Z")
    assert payload["path"] == "/api/v1/health/live"


def test_log_formatters_redact_sensitive_fields() -> None:
    sensitive = {
        "authorization": "Bearer header-token",
        "access_token": "raw-token",
        "password": "raw-password",
        "supabase_secret": "raw-secret",
        "api_key": "raw-api-key",
        "cookie": "session=raw-cookie",
        "database_url": "postgresql://user:raw-password@host/db",
        "jwt": "raw-jwt",
    }
    json_payload = json.loads(JsonFormatter().format(_record(**sensitive)))
    text_output = TextFormatter().format(_record(**sensitive))

    for key, raw_value in sensitive.items():
        assert json_payload[key] == "***"
        assert raw_value not in json.dumps(json_payload)
        assert raw_value not in text_output
    assert "path=" not in text_output


def test_log_formatters_redact_sensitive_messages_exceptions_and_nested_values() -> None:
    raw_value = "acceptance-probe-secret"
    try:
        raise RuntimeError(
            f"password={raw_value}; Authorization: Bearer {raw_value}; "
            f"database_url=postgresql://user:{raw_value}@db.invalid/app"
        )
    except RuntimeError:
        record = logging.LogRecord(
            name="ai_policy.tests",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg=f"token={raw_value}",
            args=None,
            exc_info=sys.exc_info(),
        )
    record.payload = {"nested": {"password": raw_value}}
    RequestContextFilter().filter(record)

    json_output = JsonFormatter().format(record)
    text_output = TextFormatter().format(record)
    payload = json.loads(json_output)

    assert raw_value not in json_output
    assert raw_value not in text_output
    assert payload["payload"]["nested"]["password"] == "***"
    assert "***" in payload["message"]
    assert "***" in payload["exception"]


def test_unserializable_log_values_are_bounded_and_never_raise() -> None:
    payload = json.loads(JsonFormatter().format(_record(payload=object(), note="x" * 900)))

    assert isinstance(payload["payload"], str)
    assert len(payload["payload"]) <= 501
    assert len(payload["note"]) == 501


def test_health_routes_are_not_cacheable() -> None:
    with _observability_client() as client:
        for path in ("/api/v1/health/live", "/api/v1/health/ready", "/api/v1/health"):
            assert client.get(path).headers["Cache-Control"] == "no-store"


def test_not_ready_response_is_not_cacheable() -> None:
    with _observability_client(_settings(app_env="production")) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"


def test_liveness_does_not_touch_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_: object, **__: object) -> None:
        raise AssertionError("liveness must not check dependencies")

    monkeypatch.setattr("app.modules.system.service.check_database", fail_if_called)
    with _observability_client() as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_reports_effective_feature_snapshot() -> None:
    with _observability_client() as client:
        response = client.get("/api/v1/health/ready")

    checks = response.json()["checks"]
    assert checks["features"] == {MOCKS: False}
    assert "feature_configuration" not in checks


def test_production_mock_flag_is_reported_as_non_compliant() -> None:
    settings = _settings(app_env="production", enable_mocks=True, database_url=None)
    with _observability_client(settings) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    details = response.json()["error"]["details"]
    assert details["feature_configuration"] == "non_compliant"
    assert details["non_compliant_features"] == [MOCKS]
    # The unsafe flag is forced off as well as reported.
    assert details["features"][MOCKS] is False


def test_unknown_and_production_forced_flags_resolve_to_disabled() -> None:
    development = _settings(enable_mocks=True)
    production = _settings(app_env="production", enable_mocks=True)

    assert feature_enabled(MOCKS, development) is True
    assert feature_enabled(MOCKS, production) is False
    assert feature_enabled("nonexistent_flag", development) is False
    assert feature_snapshot(production) == {MOCKS: False}
    assert non_compliant_flags(development) == []
    assert non_compliant_flags(production) == [MOCKS]


def test_features_endpoint_exposes_only_booleans_and_environment() -> None:
    settings = _settings(
        database_url="postgresql://user:secret-password@db.example.com/postgres",
        supabase_url="https://project.supabase.co",
    )
    with _observability_client(settings) as client:
        response = client.get("/api/v1/system/features")

    assert response.status_code == 200
    assert response.json() == {
        "environment": "development",
        "auth_required": True,
        "features": {MOCKS: False},
    }
    assert "secret-password" not in response.text
    assert "supabase.co" not in response.text
