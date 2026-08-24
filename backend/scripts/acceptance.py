from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


@dataclass(frozen=True)
class AcceptanceCheck:
    name: str
    command: tuple[str, ...]
    cwd: Path


def _python_executable() -> str:
    project_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    return str(project_python if project_python.is_file() else Path(sys.executable))


def acceptance_checks() -> tuple[AcceptanceCheck, ...]:
    """Return the fixed local matrix; no migration, reset, or external smoke belongs here."""

    python = _python_executable()
    return (
        AcceptanceCheck("backend_tests", (python, "-m", "pytest"), BACKEND_ROOT),
        AcceptanceCheck("ruff", (python, "-m", "ruff", "check", "--no-cache", "."), BACKEND_ROOT),
        AcceptanceCheck("local_smoke", (python, "scripts/smoke.py"), BACKEND_ROOT),
        AcceptanceCheck("frontend_guards", ("npm", "test"), FRONTEND_ROOT),
        AcceptanceCheck("frontend_build", ("npm", "run", "build"), FRONTEND_ROOT),
        AcceptanceCheck(
            "openspec_strict",
            ("openspec", "validate", "--all", "--strict", "--no-interactive"),
            PROJECT_ROOT,
        ),
    )


def _run_check(check: AcceptanceCheck) -> bool:
    try:
        result = subprocess.run(
            check.command,
            cwd=check.cwd,
            check=False,
            capture_output=True,
            text=True,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    except Exception:  # noqa: BLE001 - an aggregate check must not expose child errors.
        return False
    return result.returncode == 0


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the non-destructive Stage 0 local acceptance matrix."""

    if _arguments(argv):
        print("stage_zero_acceptance: arguments_not_supported")
        return 2

    passed = True
    for check in acceptance_checks():
        check_passed = _run_check(check)
        print(f"{check.name}: {'ok' if check_passed else 'FAIL'}")
        passed = passed and check_passed
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
