from __future__ import annotations

import sys
from collections.abc import Sequence

import jwt
from sqlalchemy import text

from app.core.auth import JWT_ALGORITHMS, _get_jwks_client
from app.core.config import Settings
from app.core.database import check_database, database_engine
from app.core.supabase_target import supabase_target_binding_state

CURRENT_REVISION = "0005_consultation_workflow"
EXPECTED_IAM_TABLES = frozenset(
    {
        "regions",
        "roles",
        "organizations",
        "profiles",
        "user_roles",
        "policy_documents",
        "historical_qa",
        "consultation_departments",
        "consultations",
        "consultation_events",
    }
)


def _is_postgresql_target(settings: Settings) -> bool:
    try:
        database_url = settings.normalized_database_url
    except Exception:  # noqa: BLE001 - runtime configuration stays private.
        return False
    return isinstance(database_url, str) and database_url.lower().startswith(
        "postgresql+psycopg://"
    )


def target_binding_smoke(settings: Settings) -> tuple[bool, str]:
    state = supabase_target_binding_state(settings)
    return state == "ok", state


def database_smoke(settings: Settings, *, target_bound: bool = True) -> tuple[bool, str]:
    """Run a PostgreSQL-only read check and map every failure to a safe state."""

    try:
        database_url = settings.normalized_database_url
    except Exception:  # noqa: BLE001 - do not surface configuration values.
        return False, "configuration_invalid"
    if not database_url:
        return False, "not_configured"
    if not _is_postgresql_target(settings):
        return False, "unsupported_database_target"
    if not target_bound:
        return False, "target_not_verified"
    try:
        connected, state = check_database(settings)
    except Exception:  # noqa: BLE001 - SQL/driver errors can contain DSNs.
        return False, "check_failed"
    if connected and state == "ok":
        return True, "ok"
    if state in {"not_configured", "unavailable"}:
        return False, state
    return False, "check_failed"


def authentication_smoke(settings: Settings) -> tuple[bool, str]:
    try:
        state = settings.auth_configuration_status
    except Exception:  # noqa: BLE001 - keep environment parsing errors private.
        return False, "configuration_invalid"
    if state == "configured":
        return True, state
    if state in {"not_configured", "development_bypass", "invalid_production_bypass"}:
        return False, state
    return False, "configuration_invalid"


def identity_schema_smoke(
    settings: Settings,
    *,
    database_ready: bool,
    target_bound: bool = True,
) -> tuple[bool, str]:
    """Inspect the approved B1.1 database state without mutating it."""

    if not target_bound:
        return False, "target_not_verified"
    if not database_ready:
        return False, "database_not_ready"
    if not _is_postgresql_target(settings):
        return False, "unsupported_database_target"
    try:
        engine = database_engine(settings)
        if engine is None:
            return False, "not_configured"
        with engine.connect() as connection:
            schema_exists = bool(
                connection.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT 1 FROM information_schema.schemata "
                        "WHERE schema_name = 'app'"
                        ")"
                    )
                ).scalar_one()
            )
            revisions = tuple(
                connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
            )
            table_names = frozenset(
                connection.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'app' AND table_type = 'BASE TABLE'"
                    )
                ).scalars()
            )
            rls_tables = frozenset(
                connection.execute(
                    text(
                        "SELECT c.relname FROM pg_class AS c "
                        "JOIN pg_namespace AS n ON n.oid = c.relnamespace "
                        "WHERE n.nspname = 'app' AND c.relkind = 'r' "
                        "AND c.relrowsecurity = true"
                    )
                ).scalars()
            )
            policy_tables = frozenset(
                connection.execute(
                    text(
                        "SELECT tablename FROM pg_policies "
                        "WHERE schemaname = 'app'"
                    )
                ).scalars()
            )
            browser_grants = frozenset(
                connection.execute(
                    text(
                        "SELECT table_name || ':' || grantee "
                        "FROM information_schema.table_privileges "
                        "WHERE table_schema = 'app' "
                        "AND grantee IN ('anon', 'authenticated')"
                    )
                ).scalars()
            )
    except Exception:  # noqa: BLE001 - SQL errors can include connection details.
        return False, "check_failed"
    if not schema_exists:
        return False, "schema_missing"
    if revisions != (CURRENT_REVISION,):
        return False, "revision_mismatch"
    if table_names != EXPECTED_IAM_TABLES:
        return False, "table_set_mismatch"
    if rls_tables != EXPECTED_IAM_TABLES:
        return False, "rls_mismatch"
    if policy_tables:
        return False, "browser_policy_mismatch"
    if browser_grants:
        return False, "browser_grant_mismatch"
    return True, "ok"


def jwks_smoke(
    settings: Settings,
    *,
    authentication_configured: bool,
    target_bound: bool = True,
) -> tuple[bool, str]:
    if not target_bound:
        return False, "target_not_verified"
    if not authentication_configured:
        return False, "not_configured"
    try:
        jwks_url = settings.resolved_supabase_jwks_url
    except Exception:  # noqa: BLE001 - never expose a configured URL.
        return False, "configuration_invalid"
    if not jwks_url:
        return False, "not_configured"
    try:
        signing_keys = _get_jwks_client(jwks_url).get_signing_keys()
        supported_keys = [
            key for key in signing_keys if getattr(key, "algorithm_name", None) in JWT_ALGORITHMS
        ]
    except jwt.PyJWKClientConnectionError:
        return False, "unavailable"
    except (jwt.PyJWKClientError, jwt.PyJWKSetError, TypeError, ValueError):
        return False, "invalid"
    except Exception:  # noqa: BLE001 - third-party failures can include response content.
        return False, "check_failed"
    return (True, "ok") if supported_keys else (False, "no_supported_signing_key")


def _report_checks(checks: dict[str, tuple[bool, str]]) -> int:
    for name, (passed, state) in checks.items():
        print(f"{name}: {'ok' if passed else 'FAIL'} ({state})")
    return 0 if all(passed for passed, _ in checks.values()) else 1


def main(argv: Sequence[str] = ()) -> int:
    if tuple(argv):
        print("runtime_smoke: arguments_not_supported")
        return 2

    try:
        settings = Settings()
    except Exception:  # noqa: BLE001 - Pydantic errors can echo raw environment input.
        return _report_checks(
            {
                "database": (False, "configuration_invalid"),
                "target_binding": (False, "configuration_invalid"),
                "identity_schema": (False, "configuration_invalid"),
                "authentication_configuration": (False, "configuration_invalid"),
                "jwks": (False, "configuration_invalid"),
            }
        )

    target_binding = target_binding_smoke(settings)
    database = database_smoke(settings, target_bound=target_binding[0])
    authentication = authentication_smoke(settings)
    identity_schema = identity_schema_smoke(
        settings,
        database_ready=database[0],
        target_bound=target_binding[0],
    )
    jwks = jwks_smoke(
        settings,
        authentication_configured=authentication[0],
        target_bound=target_binding[0],
    )
    return _report_checks(
        {
            "database": database,
            "target_binding": target_binding,
            "identity_schema": identity_schema,
            "authentication_configuration": authentication,
            "jwks": jwks,
        }
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
