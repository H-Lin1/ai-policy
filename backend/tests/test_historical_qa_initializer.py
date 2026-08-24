from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from app.core.config import Settings
from scripts import init_qa


def postgres_settings() -> Settings:
    return Settings(_env_file=None, database_url="postgresql+psycopg://postgres@db.abcdefghijklmnopqrst.supabase.co/postgres", supabase_url="https://abcdefghijklmnopqrst.supabase.co")


class Result:
    def __init__(self, *, scalar=None, values=(), rows=()): self.scalar, self.values, self.rows = scalar, tuple(values), tuple(rows)
    def scalar_one(self): return self.scalar
    def scalars(self): return iter(self.values)
    def mappings(self): return self
    def all(self): return list(self.rows)


class Connection:
    def __init__(self):
        self.revision = init_qa.QA_REVISION; self.rows: list[dict[str, object]] = []; self.fail_insert = False
        self.region = {"id": "10000000-0000-4000-8000-000000000001", "code": "sz", "is_active": True}
        self.rls_enabled = True; self.policy_count = 0; self.browser_grants = 0
    def execute(self, statement, parameters=None):
        sql = str(statement)
        if "pg_advisory_xact_lock" in sql: assert parameters == {"lock_id": init_qa.QA_IMPORT_LOCK_ID}; return Result()
        if "alembic_version" in sql: return Result(values=(self.revision,))
        if "to_regclass" in sql: return Result(scalar=True)
        if "pg_class" in sql: return Result(scalar=self.rls_enabled)
        if "pg_policies" in sql: return Result(scalar=self.policy_count)
        if "table_privileges" in sql: return Result(scalar=self.browser_grants)
        if "FROM app.regions" in sql: return Result(rows=(deepcopy(self.region),))
        if "FROM app.historical_qa" in sql: return Result(rows=deepcopy(self.rows))
        if "INSERT INTO app.historical_qa" in sql:
            if self.fail_insert: raise RuntimeError("private-write-detail")
            self.rows.extend(deepcopy(parameters if isinstance(parameters, list) else [parameters])); return Result()
        raise AssertionError(f"unexpected statement: {sql}")


class Transaction:
    def __init__(self, connection): self.connection = connection; self.snapshot = None
    def __enter__(self): self.snapshot = deepcopy(self.connection.rows); return self.connection
    def __exit__(self, exc_type, exc, traceback):
        if exc_type and self.snapshot is not None: self.connection.rows = self.snapshot
        return False


class Engine:
    def __init__(self, connection): self.connection = connection
    def begin(self): return Transaction(self.connection)


def fixture_records():
    fixture, state = init_qa.load_qa_fixture()
    assert state == "ok" and fixture is not None
    return fixture


def test_qa_initializer_preflight_is_non_mutating(monkeypatch, capsys):
    monkeypatch.setattr(init_qa, "apply_qa_migration", lambda _: (_ for _ in ()).throw(AssertionError("must not migrate")))
    assert init_qa.main([], settings=postgres_settings()) == 0
    assert init_qa.main([init_qa.APPLY_QA_MIGRATION], settings=postgres_settings()) == 2
    assert init_qa.main([init_qa.CONFIRM], settings=postgres_settings()) == 2
    assert "not_requested" in capsys.readouterr().out


def test_qa_fixture_is_exact_and_import_is_idempotent(monkeypatch):
    connection = Connection(); monkeypatch.setattr(init_qa, "supabase_target_binding_state", lambda _: "ok"); monkeypatch.setattr(init_qa, "database_engine", lambda _: Engine(connection))
    fixture = fixture_records()
    first = init_qa.apply_qa_fixture(postgres_settings(), fixture); snapshot = deepcopy(connection.rows); second = init_qa.apply_qa_fixture(postgres_settings(), fixture)
    assert first == init_qa.ImportResult(True, "ok", 20)
    assert second == init_qa.ImportResult(True, "ok", 0)
    assert connection.rows == snapshot


def test_qa_fixture_conflict_and_failed_insert_do_not_mutate(monkeypatch):
    connection = Connection(); monkeypatch.setattr(init_qa, "supabase_target_binding_state", lambda _: "ok"); monkeypatch.setattr(init_qa, "database_engine", lambda _: Engine(connection))
    fixture = fixture_records(); assert init_qa.apply_qa_fixture(postgres_settings(), fixture).passed
    connection.rows[0]["topic"] = "drifted"; snapshot = deepcopy(connection.rows)
    assert init_qa.apply_qa_fixture(postgres_settings(), fixture).state == "fixture_conflict"
    assert connection.rows == snapshot
    failing = Connection(); failing.fail_insert = True; monkeypatch.setattr(init_qa, "database_engine", lambda _: Engine(failing))
    assert init_qa.apply_qa_fixture(postgres_settings(), fixture).state == "write_failed"
    assert failing.rows == []


def test_qa_migration_uses_exact_revision(monkeypatch):
    class RevisionConnection:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, statement): assert "alembic_version" in str(statement); return Result(values=(init_qa.PREVIOUS_REVISION,))
    captured = {}
    monkeypatch.setattr(init_qa, "supabase_target_binding_state", lambda _: "ok")
    monkeypatch.setattr(init_qa, "database_engine", lambda _: SimpleNamespace(connect=lambda: RevisionConnection()))
    monkeypatch.setattr(init_qa.subprocess, "run", lambda command, **kwargs: captured.update(command=command, kwargs=kwargs) or SimpleNamespace(returncode=0))
    assert init_qa.apply_qa_migration(postgres_settings()) == (True, "applied")
    assert tuple(captured["command"][-2:]) == ("upgrade", init_qa.QA_REVISION)
    assert captured["kwargs"]["shell"] is False
