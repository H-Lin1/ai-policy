from fastapi.testclient import TestClient


def test_live_check_is_public_and_has_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "smoke-001"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"] == "smoke-001"


def test_ready_check_reports_local_database_degradation(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "not_configured"


def test_production_ready_check_fails_without_database() -> None:
    from app.core.config import Settings
    from app.main import create_app

    settings = Settings(app_env="production", database_url=None, auth_required=True)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "SERVICE_NOT_READY"
    assert body["request_id"]


def test_aggregate_health_is_browser_friendly(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
