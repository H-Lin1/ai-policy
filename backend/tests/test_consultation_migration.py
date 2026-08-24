from __future__ import annotations

import importlib


def test_consultation_migration_declares_post_historical_qa_contract() -> None:
    migration = importlib.import_module("migrations.versions.0005_consultation_workflow")
    assert migration.revision == "0005_consultation_workflow"
    assert migration.down_revision == "0004_historical_qa"


def test_consultation_migration_has_restrictive_database_boundary(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0005_consultation_workflow")
    commands: list[str] = []
    tables: list[str] = []

    class Bind:
        class dialect:
            name = "postgresql"

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    monkeypatch.setattr(migration.op, "create_table", lambda name, *args, **kwargs: tables.append(name))
    monkeypatch.setattr(migration.op, "create_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "execute", lambda statement: commands.append(str(statement)))
    migration.upgrade()

    assert tables == ["consultation_departments", "consultations", "consultation_events"]
    for table in tables:
        assert f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY" in commands
        assert f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM anon" in commands
        assert f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM authenticated" in commands
    assert all("auth.users" not in command for command in commands)


def test_consultation_migration_is_non_postgresql_noop(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0005_consultation_workflow")

    class Bind:
        class dialect:
            name = "sqlite"

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    migration.upgrade()
    migration.downgrade()
