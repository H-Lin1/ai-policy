from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import text

from app.core.config import Settings
from app.core.database import database_engine
from app.core.supabase_target import supabase_target_binding_state
from app.factory import create_app

EXPECTED_REVISION = "0005_consultation_workflow"
EXPECTED_TABLES = frozenset({
    "regions", "roles", "organizations", "profiles", "user_roles",
    "policy_documents", "historical_qa", "consultation_departments",
    "consultations", "consultation_events",
})
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _database_checks(settings: Settings) -> dict[str, bool]:
    checks = {"target_binding": supabase_target_binding_state(settings) == "ok"}
    if not checks["target_binding"]:
        return {**checks, "database": False, "revision": False, "tables": False, "rls": False, "browser_boundary": False, "department_bindings": False}
    engine = database_engine(settings)
    if engine is None:
        return {**checks, "database": False, "revision": False, "tables": False, "rls": False, "browser_boundary": False, "department_bindings": False}
    try:
        with engine.connect() as connection:
            checks["database"] = connection.execute(text("SELECT 1")).scalar_one() == 1
            checks["revision"] = tuple(connection.execute(text("SELECT version_num FROM alembic_version")).scalars()) == (EXPECTED_REVISION,)
            tables = frozenset(connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='app' AND table_type='BASE TABLE'")).scalars())
            checks["tables"] = tables == EXPECTED_TABLES
            rls = frozenset(connection.execute(text("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='app' AND c.relkind='r' AND c.relrowsecurity=true")).scalars())
            checks["rls"] = rls == EXPECTED_TABLES
            grants = tuple(connection.execute(text("SELECT 1 FROM information_schema.table_privileges WHERE table_schema='app' AND grantee IN ('anon','authenticated') LIMIT 1")).scalars())
            policies = tuple(connection.execute(text("SELECT 1 FROM pg_policies WHERE schemaname='app' LIMIT 1")).scalars())
            checks["browser_boundary"] = not grants and not policies
            checks["department_bindings"] = connection.execute(text("SELECT count(*) FROM app.consultation_departments WHERE is_active=true")).scalar_one() == 35
    except Exception:  # noqa: BLE001 - audit output must remain secret-safe.
        return {**checks, "database": False, "revision": False, "tables": False, "rls": False, "browser_boundary": False, "department_bindings": False}
    return checks


def _route_checks(settings: Settings) -> dict[str, bool]:
    try:
        paths = set(create_app(settings).openapi().get("paths", {}))
    except Exception:  # noqa: BLE001 - OpenAPI failures map to a stable audit state.
        return {"consultation_routes": False, "policy_answer_route": False, "qa_routes": False}
    return {
        "consultation_routes": all(path in paths for path in ("/api/v1/consultations", "/api/v1/consultations/departments", "/api/v1/consultations/{consultation_id}/reply")),
        "policy_answer_route": "/api/v1/policy-answers" in paths,
        "qa_routes": "/api/v1/qa" in paths and "/api/v1/qa/{qa_id}" in paths,
    }


def _local_gates() -> dict[str, bool]:
    frontend = PROJECT_ROOT / "frontend"
    backend = PROJECT_ROOT / "backend"
    commands = (("backend_tests", (sys.executable, "-m", "pytest"), backend), ("ruff", (sys.executable, "-m", "ruff", "check", "--no-cache", "."), backend), ("frontend_tests", ("npm", "test"), frontend), ("frontend_build", ("npm", "run", "build"), frontend))
    result: dict[str, bool] = {}
    for name, command, cwd in commands:
        try:
            result[name] = subprocess.run(command, cwd=cwd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        except Exception:  # noqa: BLE001 - local gate failures are reported by name.
            result[name] = False
    return result


def run(*, settings: Settings | None = None, include_local_gates: bool = True) -> dict[str, bool]:
    settings = settings or Settings()
    checks = {**_database_checks(settings), **_route_checks(settings)}
    if include_local_gates:
        checks.update(_local_gates())
    return checks


def main(argv: Sequence[str] = ()) -> int:
    if argv:
        print("b1_7_audit: arguments_not_supported")
        return 2
    try:
        checks = run()
    except Exception:  # noqa: BLE001 - aggregate audit failures must not expose internals.
        checks = {"audit": False}
    for name, passed in checks.items():
        print(f"{name}: {'ok' if passed else 'FAIL'}")
    return 0 if checks and all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
