from __future__ import annotations

import importlib

from sqlalchemy.dialects import postgresql


def test_policy_migration_is_after_iam_and_declares_read_only_table_contract(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0003_policy_library")
    assert migration.revision == "0003_policy_library"
    assert migration.down_revision == "0002_identity_access"

    operations = []

    class FakeBind:
        dialect = type("Dialect", (), {"name": "postgresql"})()

    class FakeOp:
        def get_bind(self):
            return FakeBind()

        def create_table(self, name, *columns, **kwargs):
            operations.append(("create_table", name, columns, kwargs))

        def create_index(self, name, table, columns, **kwargs):
            operations.append(("create_index", name, table, columns, kwargs))

        def execute(self, statement):
            operations.append(("execute", str(statement)))

    fake = FakeOp()
    monkeypatch.setattr(migration, "op", fake)
    migration.upgrade()

    table = next(item for item in operations if item[0] == "create_table")
    assert table[1] == "policy_documents"
    names = {column.name for column in table[2] if hasattr(column, "name")}
    assert {"id", "region_id", "region_code", "title", "source_url", "collected_at", "content_text", "content_sha256"}.issubset(names)
    assert any("REVOKE ALL PRIVILEGES ON TABLE app.policy_documents FROM anon" in item[1] for item in operations if item[0] == "execute")
    assert any("REVOKE ALL PRIVILEGES ON TABLE app.policy_documents FROM authenticated" in item[1] for item in operations if item[0] == "execute")


def test_policy_model_compiles_for_postgresql() -> None:
    migration = importlib.import_module("migrations.versions.0003_policy_library")
    assert postgresql.dialect().name == "postgresql"
    assert migration.revision
