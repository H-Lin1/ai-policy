from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from app.core.config import Settings

APPLY_FOUNDATION_MIGRATION = "--apply-foundation-migration"
CONFIRM = "--confirm"
FOUNDATION_REVISION = "0001_foundation_schema"
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def database_target_state(settings: Settings) -> str:
    """Return only a safe classification of the configured migration target."""

    database_url = settings.normalized_database_url
    if not database_url:
        return "not_configured"
    if database_url.lower().startswith("postgresql+psycopg://"):
        return "postgresql_configured"
    return "unsupported_database_target"


def migration_environment(database_url: str) -> dict[str, str]:
    """Bind the child process to the already-validated target and config file."""

    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    environment.pop("ALEMBIC_CONFIG", None)
    return environment


def main(argv: Sequence[str] | None = None, *, settings: Settings | None = None) -> int:
    """Preflight by default; apply only the explicit foundation migration on request."""

    arguments = _arguments(argv)
    if any(argument not in {APPLY_FOUNDATION_MIGRATION, CONFIRM} for argument in arguments):
        print("foundation_migration: invalid_arguments")
        return 2

    try:
        runtime_settings = settings or Settings()
        target_state = database_target_state(runtime_settings)
    except Exception:  # noqa: BLE001 - CLI output must not expose configuration errors.
        print("foundation_migration: configuration_invalid")
        return 2

    apply_requested = APPLY_FOUNDATION_MIGRATION in arguments
    confirmed = CONFIRM in arguments
    if not apply_requested and not confirmed:
        print(f"foundation_migration: not_requested ({target_state})")
        print("No migration or data change was performed.")
        return 0
    if not apply_requested:
        print("foundation_migration: apply_flag_required")
        return 2
    if not confirmed:
        print("foundation_migration: confirmation_required")
        return 2
    if target_state != "postgresql_configured":
        print(f"foundation_migration: {target_state}")
        return 2

    database_url = runtime_settings.normalized_database_url
    if not isinstance(database_url, str):
        print("foundation_migration: configuration_invalid")
        return 2
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "-c",
                str(BACKEND_ROOT / "alembic.ini"),
                "upgrade",
                FOUNDATION_REVISION,
            ],
            cwd=BACKEND_ROOT,
            check=False,
            capture_output=True,
            env=migration_environment(database_url),
            text=True,
            shell=False,
        )
    except Exception:  # noqa: BLE001 - do not expose subprocess or environment details.
        print("foundation_migration: execution_failed")
        return 1

    if result.returncode != 0:
        print("foundation_migration: failed")
        return result.returncode or 1

    print("foundation_migration: applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
