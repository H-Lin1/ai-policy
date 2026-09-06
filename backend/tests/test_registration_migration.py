from __future__ import annotations

import importlib


def test_registration_migration_follows_consultation() -> None:
    migration = importlib.import_module("migrations.versions.0006_registration_applications")
    assert migration.revision == "0006_registration_applications"
    assert migration.down_revision == "0005_consultation_workflow"


def test_registration_migration_has_restrictive_contract(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0006_registration_applications")
    commands: list[str] = []
    tables: list[str] = []
    indexes: list[str] = []

    class Bind:
        class dialect:
            name = "postgresql"

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    monkeypatch.setattr(migration.op, "alter_column", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "create_table", lambda name, *args, **kwargs: tables.append(name))
    monkeypatch.setattr(migration.op, "create_index", lambda name, *args, **kwargs: indexes.append(name))
    monkeypatch.setattr(migration.op, "execute", lambda statement: commands.append(str(statement)))
    migration.upgrade()

    assert tables == ["registration_applications", "registration_application_events"]
    assert "uq_registration_application_pending_username" in indexes
    assert "uq_registration_government_department_active" in indexes
    for table in tables:
        assert f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY" in commands
    assert all("auth.users" not in command for command in commands)


def test_registration_migration_is_non_postgresql_noop(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0006_registration_applications")

    class Bind:
        class dialect:
            name = "sqlite"

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    migration.upgrade()
    migration.downgrade()
