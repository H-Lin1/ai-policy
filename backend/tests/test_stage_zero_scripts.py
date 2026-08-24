from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import acceptance, init_demo, reset_demo, runtime_smoke, smoke

PROJECT_REF = "abcdefghijklmnopqrst"


def _postgres_settings() -> SimpleNamespace:
    return SimpleNamespace(
        normalized_database_url=(
            f"postgresql+psycopg://postgres@db.{PROJECT_REF}.supabase.co/postgres"
        ),
        supabase_url=f"https://{PROJECT_REF}.supabase.co",
        auth_configuration_status="configured",
        resolved_supabase_jwks_url=(
            f"https://{PROJECT_REF}.supabase.co/auth/v1/.well-known/jwks.json"
        ),
        resolved_supabase_jwt_issuer=f"https://{PROJECT_REF}.supabase.co/auth/v1",
    )


def _sqlite_settings() -> SimpleNamespace:
    return SimpleNamespace(
        normalized_database_url="sqlite:///stage-zero-test.db",
        supabase_url=None,
        auth_configuration_status="not_configured",
        resolved_supabase_jwks_url=None,
        resolved_supabase_jwt_issuer=None,
    )


def test_init_preflight_does_not_spawn_alembic(monkeypatch, capsys) -> None:
    called = False

    def unexpected_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("migration must not run during preflight")

    monkeypatch.setattr(init_demo.subprocess, "run", unexpected_run)

    assert init_demo.main([], settings=_postgres_settings()) == 0
    assert called is False
    output = capsys.readouterr().out
    assert "not_requested" in output
    assert "postgresql+psycopg" not in output


@pytest.mark.parametrize(
    "arguments",
    [[init_demo.APPLY_FOUNDATION_MIGRATION], [init_demo.CONFIRM]],
)
def test_init_requires_both_explicit_flags(monkeypatch, arguments) -> None:
    called = False

    def unexpected_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("migration must not run without both flags")

    monkeypatch.setattr(init_demo.subprocess, "run", unexpected_run)

    assert init_demo.main(arguments, settings=_postgres_settings()) == 2
    assert called is False


def test_init_rejects_missing_or_non_postgresql_target(monkeypatch) -> None:
    called = False

    def unexpected_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("migration must not run for an unsafe target")

    monkeypatch.setattr(init_demo.subprocess, "run", unexpected_run)

    assert (
        init_demo.main(
            [init_demo.APPLY_FOUNDATION_MIGRATION, init_demo.CONFIRM],
            settings=SimpleNamespace(normalized_database_url=None),
        )
        == 2
    )
    assert (
        init_demo.main(
            [init_demo.APPLY_FOUNDATION_MIGRATION, init_demo.CONFIRM],
            settings=_sqlite_settings(),
        )
        == 2
    )
    assert called is False


def test_init_uses_fixed_foundation_revision_and_hides_child_output(monkeypatch, capsys) -> None:
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_run(*args, **kwargs):
        calls.append((tuple(args[0]), kwargs))
        return subprocess.CompletedProcess(
            args[0],
            7,
            stdout="database-secret-marker",
            stderr="dsn-secret-marker",
        )

    monkeypatch.setattr(init_demo.subprocess, "run", fake_run)

    assert (
        init_demo.main(
            [init_demo.APPLY_FOUNDATION_MIGRATION, init_demo.CONFIRM],
            settings=_postgres_settings(),
        )
        == 7
    )
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == (
        init_demo.sys.executable,
        "-m",
        "alembic",
        "-c",
        str(init_demo.BACKEND_ROOT / "alembic.ini"),
        "upgrade",
        init_demo.FOUNDATION_REVISION,
    )
    assert kwargs["cwd"] == init_demo.BACKEND_ROOT
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["env"]["DATABASE_URL"] == _postgres_settings().normalized_database_url
    assert kwargs["shell"] is False
    output = capsys.readouterr()
    assert "database-secret-marker" not in output.out
    assert "dsn-secret-marker" not in output.err


def test_init_binds_validated_target_despite_hostile_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///hostile.db")
    monkeypatch.setenv("ALEMBIC_CONFIG", "/tmp/hostile.ini")
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

    monkeypatch.setattr(init_demo.subprocess, "run", fake_run)

    assert (
        init_demo.main(
            [init_demo.APPLY_FOUNDATION_MIGRATION, init_demo.CONFIRM],
            settings=_postgres_settings(),
        )
        == 0
    )
    assert captured["env"]["DATABASE_URL"] == _postgres_settings().normalized_database_url
    assert "ALEMBIC_CONFIG" not in captured["env"]
    assert captured["cwd"] == init_demo.BACKEND_ROOT


def test_init_hides_subprocess_exception(monkeypatch, capsys) -> None:
    marker = "subprocess-secret-marker"

    def fail_run(*args, **kwargs):
        raise RuntimeError(marker)

    monkeypatch.setattr(init_demo.subprocess, "run", fail_run)

    assert (
        init_demo.main(
            [init_demo.APPLY_FOUNDATION_MIGRATION, init_demo.CONFIRM],
            settings=_postgres_settings(),
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "execution_failed" in output
    assert marker not in output


def test_reset_requires_acknowledgement_and_confirmed_call_is_noop(
    monkeypatch, capsys, tmp_path
) -> None:
    def unexpected_subprocess(*args, **kwargs):
        raise AssertionError("reset must not spawn a child process")

    monkeypatch.setattr(subprocess, "run", unexpected_subprocess)
    monkeypatch.chdir(tmp_path)
    before = tuple(tmp_path.iterdir())

    assert reset_demo.main([]) == 2
    assert reset_demo.main([reset_demo.CONFIRM]) == 0
    assert tuple(tmp_path.iterdir()) == before
    assert not {"subprocess", "database_engine", "create_engine"} & vars(reset_demo).keys()
    output = capsys.readouterr().out
    assert "no_stage_zero_business_data" in output
    assert "No reset" in output


def test_smoke_settings_ignore_ambient_runtime_configuration(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///ambient.db")
    monkeypatch.setenv("SUPABASE_URL", "https://ambient.invalid")
    monkeypatch.setenv("CLASSIFIER_SUPPORTED_REGIONS", "beijing")
    monkeypatch.setenv("ENABLE_MOCKS", "true")

    settings = smoke.smoke_settings()

    assert settings.normalized_database_url is None
    assert settings.resolved_supabase_jwks_url is None
    assert settings.classifier_supported_region_ids == ("sz",)
    assert settings.enable_mocks is False


def test_smoke_command_is_hermetic_before_application_import() -> None:
    marker = "ambient-secret-marker"
    environment = os.environ.copy()
    environment.update(
        {
            "PORT": marker,
            "LOG_FORMAT": marker,
            "ENABLE_MOCKS": marker,
        }
    )

    result = subprocess.run(
        [sys.executable, str(Path(smoke.__file__).resolve())],
        cwd=Path(smoke.__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        shell=False,
    )

    assert result.returncode == 0
    assert marker not in result.stdout
    assert marker not in result.stderr
    assert "Traceback" not in result.stderr


def test_runtime_smoke_sanitizes_unexpected_database_failure(monkeypatch, capsys) -> None:
    marker = "runtime-secret-marker"

    def fail_database(settings):
        raise RuntimeError(marker)

    monkeypatch.setattr(runtime_smoke, "Settings", lambda: _postgres_settings())
    monkeypatch.setattr(runtime_smoke, "check_database", fail_database)
    monkeypatch.setattr(
        runtime_smoke,
        "_get_jwks_client",
        lambda _: SimpleNamespace(
            get_signing_keys=lambda: [SimpleNamespace(algorithm_name="ES256")]
        ),
    )

    assert runtime_smoke.main() == 1
    output = capsys.readouterr().out
    assert "check_failed" in output
    assert marker not in output
    assert "Traceback" not in output


def test_runtime_smoke_rejects_sqlite_before_connecting(monkeypatch, capsys) -> None:
    database_called = False
    engine_called = False

    def unexpected_database(settings):
        nonlocal database_called
        database_called = True
        raise AssertionError("SQLite must not be opened by Supabase runtime smoke")

    def unexpected_engine(settings):
        nonlocal engine_called
        engine_called = True
        raise AssertionError("SQLite must not create an engine")

    monkeypatch.setattr(runtime_smoke, "Settings", lambda: _sqlite_settings())
    monkeypatch.setattr(runtime_smoke, "check_database", unexpected_database)
    monkeypatch.setattr(runtime_smoke, "database_engine", unexpected_engine)

    assert runtime_smoke.main() == 1
    assert database_called is False
    assert engine_called is False
    assert not Path("stage-zero-test.db").exists()
    output = capsys.readouterr().out
    assert "unsupported_database_target" in output


def test_runtime_smoke_rejects_project_mismatch_before_database_or_jwks(
    monkeypatch, capsys
) -> None:
    other_ref = "zyxwvutsrqponmlkjihg"
    settings = SimpleNamespace(
        normalized_database_url=(
            f"postgresql+psycopg://postgres@db.{other_ref}.supabase.co/postgres"
        ),
        supabase_url=f"https://{PROJECT_REF}.supabase.co",
        auth_configuration_status="configured",
        resolved_supabase_jwks_url=(
            f"https://{PROJECT_REF}.supabase.co/auth/v1/.well-known/jwks.json"
        ),
        resolved_supabase_jwt_issuer=f"https://{PROJECT_REF}.supabase.co/auth/v1",
    )

    monkeypatch.setattr(runtime_smoke, "Settings", lambda: settings)
    monkeypatch.setattr(
        runtime_smoke,
        "check_database",
        lambda value: (_ for _ in ()).throw(AssertionError("must not connect")),
    )
    monkeypatch.setattr(
        runtime_smoke,
        "database_engine",
        lambda value: (_ for _ in ()).throw(AssertionError("must not inspect")),
    )
    monkeypatch.setattr(
        runtime_smoke,
        "_get_jwks_client",
        lambda value: (_ for _ in ()).throw(AssertionError("must not fetch")),
    )

    assert runtime_smoke.main() == 1
    output = capsys.readouterr().out
    assert "project_mismatch" in output
    assert "target_not_verified" in output
    assert PROJECT_REF not in output
    assert other_ref not in output


def test_runtime_smoke_hides_configuration_exception(monkeypatch, capsys) -> None:
    marker = "configuration-secret-marker"
    monkeypatch.setattr(
        runtime_smoke,
        "Settings",
        lambda: (_ for _ in ()).throw(RuntimeError(marker)),
    )

    assert runtime_smoke.main() == 1
    output = capsys.readouterr().out
    assert "configuration_invalid" in output
    assert marker not in output
    assert "Traceback" not in output


def test_runtime_smoke_rejects_arguments_before_loading_settings(monkeypatch, capsys) -> None:
    called = False

    def unexpected_settings():
        nonlocal called
        called = True
        raise AssertionError("arguments must be rejected before configuration access")

    monkeypatch.setattr(runtime_smoke, "Settings", unexpected_settings)

    assert runtime_smoke.main(["--help"]) == 2
    assert called is False
    assert "arguments_not_supported" in capsys.readouterr().out


def test_runtime_smoke_sanitizes_identity_schema_and_jwks_exceptions(
    monkeypatch, capsys
) -> None:
    marker = "dependency-secret-marker"

    monkeypatch.setattr(runtime_smoke, "Settings", lambda: _postgres_settings())
    monkeypatch.setattr(runtime_smoke, "check_database", lambda settings: (True, "ok"))
    monkeypatch.setattr(
        runtime_smoke,
        "database_engine",
        lambda settings: (_ for _ in ()).throw(RuntimeError(marker)),
    )
    monkeypatch.setattr(
        runtime_smoke,
        "_get_jwks_client",
        lambda url: (_ for _ in ()).throw(RuntimeError(marker)),
    )

    assert runtime_smoke.main() == 1
    output = capsys.readouterr().out
    assert output.count("check_failed") == 2
    assert marker not in output
    assert "Traceback" not in output


def test_identity_runtime_smoke_uses_read_only_queries(monkeypatch) -> None:
    statements: list[str] = []

    class FakeResult:
        def __init__(self, *, scalar=None, values=()) -> None:
            self.scalar = scalar
            self.values = values

        def scalar_one(self):
            return self.scalar

        def scalars(self):
            return iter(self.values)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            sql = str(statement)
            statements.append(sql)
            if "information_schema.schemata" in sql:
                return FakeResult(scalar=True)
            if "alembic_version" in sql:
                return FakeResult(values=(runtime_smoke.CURRENT_REVISION,))
            if "information_schema.tables" in sql or "pg_class" in sql:
                return FakeResult(values=runtime_smoke.EXPECTED_IAM_TABLES)
            if "pg_policies" in sql or "table_privileges" in sql:
                return FakeResult(values=())
            raise AssertionError("unexpected runtime query")

    fake_engine = SimpleNamespace(connect=lambda: FakeConnection())
    monkeypatch.setattr(runtime_smoke, "database_engine", lambda settings: fake_engine)

    assert runtime_smoke.identity_schema_smoke(_postgres_settings(), database_ready=True) == (
        True,
        "ok",
    )
    assert len(statements) == 6
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)


@pytest.mark.parametrize(
    ("tables", "rls_tables", "state"),
    [
        (frozenset({"regions"}), runtime_smoke.EXPECTED_IAM_TABLES, "table_set_mismatch"),
        (runtime_smoke.EXPECTED_IAM_TABLES, frozenset({"regions"}), "rls_mismatch"),
    ],
)
def test_identity_runtime_smoke_rejects_table_or_rls_mismatch(
    monkeypatch, tables, rls_tables, state
) -> None:
    class FakeResult:
        def __init__(self, *, scalar=None, values=()) -> None:
            self.scalar = scalar
            self.values = values

        def scalar_one(self):
            return self.scalar

        def scalars(self):
            return iter(self.values)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            sql = str(statement)
            if "information_schema.schemata" in sql:
                return FakeResult(scalar=True)
            if "alembic_version" in sql:
                return FakeResult(values=(runtime_smoke.CURRENT_REVISION,))
            if "information_schema.tables" in sql:
                return FakeResult(values=tables)
            if "pg_class" in sql:
                return FakeResult(values=rls_tables)
            if "pg_policies" in sql or "table_privileges" in sql:
                return FakeResult(values=())
            raise AssertionError("unexpected runtime query")

    monkeypatch.setattr(
        runtime_smoke,
        "database_engine",
        lambda settings: SimpleNamespace(connect=lambda: FakeConnection()),
    )

    assert runtime_smoke.identity_schema_smoke(_postgres_settings(), database_ready=True) == (
        False,
        state,
    )


@pytest.mark.parametrize(
    ("policy_tables", "browser_grants", "state"),
    [
        (frozenset({"profiles"}), frozenset(), "browser_policy_mismatch"),
        (frozenset(), frozenset({"profiles:authenticated"}), "browser_grant_mismatch"),
    ],
)
def test_identity_runtime_smoke_rejects_browser_policy_or_grant(
    monkeypatch, policy_tables, browser_grants, state
) -> None:
    class FakeResult:
        def __init__(self, *, scalar=None, values=()) -> None:
            self.scalar = scalar
            self.values = values

        def scalar_one(self):
            return self.scalar

        def scalars(self):
            return iter(self.values)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            sql = str(statement)
            if "information_schema.schemata" in sql:
                return FakeResult(scalar=True)
            if "alembic_version" in sql:
                return FakeResult(values=(runtime_smoke.CURRENT_REVISION,))
            if "information_schema.tables" in sql or "pg_class" in sql:
                return FakeResult(values=runtime_smoke.EXPECTED_IAM_TABLES)
            if "pg_policies" in sql:
                return FakeResult(values=policy_tables)
            if "table_privileges" in sql:
                return FakeResult(values=browser_grants)
            raise AssertionError("unexpected runtime query")

    monkeypatch.setattr(
        runtime_smoke,
        "database_engine",
        lambda settings: SimpleNamespace(connect=lambda: FakeConnection()),
    )
    assert runtime_smoke.identity_schema_smoke(_postgres_settings(), database_ready=True) == (
        False,
        state,
    )


def test_acceptance_uses_fixed_non_destructive_commands(monkeypatch, capsys) -> None:
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_run(*args, **kwargs):
        calls.append((tuple(args[0]), kwargs))
        return subprocess.CompletedProcess(args[0], 0, stdout="hidden", stderr="hidden")

    monkeypatch.setattr(acceptance.subprocess, "run", fake_run)

    assert acceptance.main([]) == 0
    assert len(calls) == 6
    python = acceptance._python_executable()
    assert [(command, kwargs["cwd"]) for command, kwargs in calls] == [
        ((python, "-m", "pytest"), acceptance.BACKEND_ROOT),
        ((python, "-m", "ruff", "check", "--no-cache", "."), acceptance.BACKEND_ROOT),
        ((python, "scripts/smoke.py"), acceptance.BACKEND_ROOT),
        (("npm", "test"), acceptance.FRONTEND_ROOT),
        (("npm", "run", "build"), acceptance.FRONTEND_ROOT),
        (
            ("openspec", "validate", "--all", "--strict", "--no-interactive"),
            acceptance.PROJECT_ROOT,
        ),
    ]
    flattened = [part for command, _ in calls for part in command]
    assert "alembic" not in flattened
    assert "init_demo.py" not in flattened
    assert "reset_demo.py" not in flattened
    assert "runtime_smoke.py" not in flattened
    assert all(kwargs["shell"] is False for _, kwargs in calls)
    assert all(kwargs["capture_output"] is True for _, kwargs in calls)
    output = capsys.readouterr().out
    assert "backend_tests: ok" in output
    assert "frontend_build: ok" in output
    assert "hidden" not in output


def test_acceptance_reports_failure_without_child_output(monkeypatch, capsys) -> None:
    marker = "child-secret-marker"
    calls: list[tuple[str, ...]] = []

    def fake_run(command, **kwargs):
        calls.append(tuple(command))
        return subprocess.CompletedProcess(
            command,
            1 if command[1:3] == ("-m", "pytest") else 0,
            stdout=marker,
            stderr=marker,
        )

    monkeypatch.setattr(acceptance.subprocess, "run", fake_run)

    assert acceptance.main([]) == 1
    assert len(calls) == 6
    output = capsys.readouterr().out
    assert "backend_tests: FAIL" in output
    assert "openspec_strict: ok" in output
    assert marker not in output


def test_acceptance_rejects_arbitrary_arguments_without_echoing_them(capsys) -> None:
    marker = "argument-secret-marker"

    assert acceptance.main([marker]) == 2
    output = capsys.readouterr().out
    assert "arguments_not_supported" in output
    assert marker not in output


def test_acceptance_paths_are_project_relative() -> None:
    checks = acceptance.acceptance_checks()

    assert checks[0].cwd == Path(acceptance.BACKEND_ROOT)
    assert checks[-1].cwd == Path(acceptance.PROJECT_ROOT)
