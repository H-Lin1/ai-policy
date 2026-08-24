from __future__ import annotations

from app.core.config import Settings
from app.core.database import check_database
from app.core.features import feature_snapshot, non_compliant_flags


def live_payload(settings: Settings) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


def readiness_payload(settings: Settings) -> tuple[bool, dict[str, object]]:
    db_ok, db_status = check_database(settings)
    auth_status = settings.auth_configuration_status
    unsafe_flags = non_compliant_flags(settings)
    checks: dict[str, object] = {
        "database": "ok" if db_ok else db_status,
        "authentication": auth_status,
    "features": feature_snapshot(settings),
    }
    if unsafe_flags:
        # Report the mismatch instead of silently serving the forced-safe value.
        checks["feature_configuration"] = "non_compliant"
        checks["non_compliant_features"] = unsafe_flags
    auth_ok = auth_status in {"configured", "development_bypass"}
    if unsafe_flags:
        return False, checks
    if db_ok and auth_ok:
        return True, checks
    if not settings.is_production and (
        db_status == "not_configured" or auth_status == "not_configured"
    ):
        checks["mode"] = "development_degraded"
        return True, checks
    return False, checks


def features_payload(settings: Settings) -> dict[str, object]:
    """Only booleans, the environment name, and whether auth is required.

    Nothing else, so this endpoint cannot become a configuration dump.
    """

    return {
        "environment": settings.app_env,
        "auth_required": settings.auth_required,
        "features": feature_snapshot(settings),
    }
