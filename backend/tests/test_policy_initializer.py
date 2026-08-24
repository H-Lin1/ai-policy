from __future__ import annotations

import subprocess
from copy import deepcopy
from types import SimpleNamespace

from app.core.config import Settings
from scripts import init_policy

PROJECT_REF = "abcdefghijklmnopqrst"


def postgres_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url=(
            f"postgresql+psycopg://postgres@db.{PROJECT_REF}.supabase.co/postgres"
        ),
        supabase_url=f"https://{PROJECT_REF}.supabase.co",
    )


class FakeResult:
    def __init__(self, *, scalar=None, values=(), rows=()) -> None:
        self.scalar = scalar
        self.values = tuple(values)
        self.rows = tuple(rows)

    def scalar_one(self):
        return self.scalar

    def scalars(self):
        return iter(self.values)

    def mappings(self):
        return self

    def all(self):
        return list(self.rows)


class FakeConnection:
    def __init__(self) -> None:
        self.revision = init_policy.POLICY_REVISION
        self.region = {
            "id": "10000000-0000-4000-8000-000000000001",
            "code": "sz",
            "is_active": True,
        }
        self.policies: list[dict[str, object]] = []
        self.statements: list[str] = []
        self.fail_insert = False
        self.rls_enabled = True
        self.policy_count = 0
        self.browser_grants = 0

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.statements.append(sql)
        if "pg_advisory_xact_lock" in sql:
            assert parameters == {"lock_id": init_policy.POLICY_IMPORT_LOCK_ID}
            return FakeResult()
        if "alembic_version" in sql:
            return FakeResult(values=(self.revision,))
        if "to_regclass" in sql:
            return FakeResult(scalar=True)
        if "pg_class" in sql:
            return FakeResult(scalar=self.rls_enabled)
        if "pg_policies" in sql:
            return FakeResult(scalar=self.policy_count)
        if "table_privileges" in sql:
            return FakeResult(scalar=self.browser_grants)
        if "FROM app.regions" in sql:
            return FakeResult(rows=(deepcopy(self.region),))
        if "FROM app.policy_documents" in sql:
            return FakeResult(rows=deepcopy(self.policies))
        if "INSERT INTO app.policy_documents" in sql:
            if self.fail_insert:
                raise RuntimeError("private-write-detail")
            values = parameters if isinstance(parameters, list) else [parameters]
            self.policies.extend(deepcopy(values))
            return FakeResult()
        raise AssertionError(f"unexpected statement: {sql}")


class FakeTransaction:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.snapshot: list[dict[str, object]] | None = None

    def __enter__(self):
        self.snapshot = deepcopy(self.connection.policies)
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None and self.snapshot is not None:
            self.connection.policies = self.snapshot
        return False


class FakeEngine:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.begin_count = 0

    def begin(self):
        self.begin_count += 1
        return FakeTransaction(self.connection)


def fixture_records() -> tuple[dict[str, object], ...]:
    records, state = init_policy.load_policy_fixture()
    assert state == "ok" and records is not None
    return records


def test_policy_initializer_preflight_and_partial_flags_never_write(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        init_policy,
        "apply_policy_migration",
        lambda settings: (_ for _ in ()).throw(AssertionError("must not migrate")),
    )
    monkeypatch.setattr(
        init_policy,
        "apply_policy_fixture",
        lambda settings, fixture: (_ for _ in ()).throw(AssertionError("must not import")),
    )

    assert init_policy.main([], settings=postgres_settings()) == 0
    assert init_policy.main([init_policy.APPLY_POLICY_MIGRATION], settings=postgres_settings()) == 2
    assert init_policy.main([init_policy.CONFIRM], settings=postgres_settings()) == 2
    assert (
        init_policy.main(
            [
                init_policy.APPLY_POLICY_MIGRATION,
                init_policy.APPLY_POLICY_FIXTURE,
                init_policy.CONFIRM,
            ],
            settings=postgres_settings(),
        )
        == 2
    )
    output = capsys.readouterr().out
    assert "not_requested" in output
    assert "confirmation_required" in output
    assert "one_operation_required" in output
    assert PROJECT_REF not in output


def test_policy_initializer_rejects_unbound_target_before_write(monkeypatch, capsys) -> None:
    settings = Settings(
        _env_file=None,
        database_url=(
            "postgresql+psycopg://postgres@db.zyxwvutsrqponmlkjihg.supabase.co/postgres"
        ),
        supabase_url=f"https://{PROJECT_REF}.supabase.co",
    )
    monkeypatch.setattr(
        init_policy,
        "apply_policy_migration",
        lambda value: (_ for _ in ()).throw(AssertionError("must not migrate")),
    )
    assert (
        init_policy.main(
            [init_policy.APPLY_POLICY_MIGRATION, init_policy.CONFIRM],
            settings=settings,
        )
        == 2
    )
    output = capsys.readouterr().out
    assert "project_mismatch" in output
    assert PROJECT_REF not in output


def test_policy_migration_uses_exact_revision_and_sanitizes_child_output(monkeypatch) -> None:
    class RevisionConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            assert "alembic_version" in str(statement)
            return FakeResult(values=(init_policy.PREVIOUS_REVISION,))

    captured = None

    def fake_run(command, **kwargs):
        nonlocal captured
        captured = (tuple(command), kwargs)
        return subprocess.CompletedProcess(command, 0, "private-output", "private-error")

    monkeypatch.setattr(init_policy, "supabase_target_binding_state", lambda settings: "ok")
    monkeypatch.setattr(
        init_policy,
        "database_engine",
        lambda settings: SimpleNamespace(connect=lambda: RevisionConnection()),
    )
    monkeypatch.setattr(init_policy.subprocess, "run", fake_run)

    assert init_policy.apply_policy_migration(postgres_settings()) == (True, "applied")
    assert captured is not None
    command, kwargs = captured
    assert command[-2:] == ("upgrade", init_policy.POLICY_REVISION)
    assert kwargs["cwd"] == init_policy.BACKEND_ROOT
    assert kwargs["shell"] is False
    assert kwargs["capture_output"] is True


def test_policy_fixture_is_exact_deterministic_and_valid() -> None:
    records = fixture_records()
    assert len(records) == init_policy.FIXTURE_SIZE
    assert len({record["id"] for record in records}) == init_policy.FIXTURE_SIZE
    assert len(
        {(record["source_url"], record["content_sha256"]) for record in records}
    ) == init_policy.FIXTURE_SIZE
    assert all(record["region_code"] == "sz" for record in records)


def test_policy_fixture_import_inserts_once_then_is_exact_noop(monkeypatch) -> None:
    connection = FakeConnection()
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_policy, "supabase_target_binding_state", lambda settings: "ok")
    monkeypatch.setattr(init_policy, "database_engine", lambda settings: engine)
    fixture = fixture_records()

    first = init_policy.apply_policy_fixture(postgres_settings(), fixture)
    snapshot = deepcopy(connection.policies)
    second = init_policy.apply_policy_fixture(postgres_settings(), fixture)

    assert first == init_policy.ImportResult(True, "ok", init_policy.FIXTURE_SIZE)
    assert second == init_policy.ImportResult(True, "ok", 0)
    assert connection.policies == snapshot
    assert engine.begin_count == 2


def test_policy_fixture_import_rejects_conflict_without_mutation(monkeypatch) -> None:
    connection = FakeConnection()
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_policy, "supabase_target_binding_state", lambda settings: "ok")
    monkeypatch.setattr(init_policy, "database_engine", lambda settings: engine)
    fixture = fixture_records()
    assert init_policy.apply_policy_fixture(postgres_settings(), fixture).passed is True
    connection.policies[0]["title"] = "drifted"
    snapshot = deepcopy(connection.policies)

    result = init_policy.apply_policy_fixture(postgres_settings(), fixture)

    assert result == init_policy.ImportResult(False, "fixture_conflict", 0)
    assert connection.policies == snapshot


def test_policy_fixture_import_rolls_back_failed_insert_and_hides_error(monkeypatch) -> None:
    connection = FakeConnection()
    connection.fail_insert = True
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_policy, "supabase_target_binding_state", lambda settings: "ok")
    monkeypatch.setattr(init_policy, "database_engine", lambda settings: engine)

    result = init_policy.apply_policy_fixture(postgres_settings(), fixture_records())

    assert result == init_policy.ImportResult(False, "write_failed", 0)
    assert connection.policies == []


def test_policy_fixture_import_rejects_revision_and_security_drift(monkeypatch) -> None:
    monkeypatch.setattr(init_policy, "supabase_target_binding_state", lambda settings: "ok")
    fixture = fixture_records()

    revision_connection = FakeConnection()
    revision_connection.revision = init_policy.PREVIOUS_REVISION
    monkeypatch.setattr(
        init_policy,
        "database_engine",
        lambda settings: FakeEngine(revision_connection),
    )
    assert init_policy.apply_policy_fixture(postgres_settings(), fixture).state == "revision_mismatch"

    security_connection = FakeConnection()
    security_connection.browser_grants = 1
    monkeypatch.setattr(
        init_policy,
        "database_engine",
        lambda settings: FakeEngine(security_connection),
    )
    assert (
        init_policy.apply_policy_fixture(postgres_settings(), fixture).state
        == "policy_browser_grant_mismatch"
    )
