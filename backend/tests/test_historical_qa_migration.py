from __future__ import annotations

import importlib


def test_historical_qa_migration_is_after_policy_and_restricts_browser_access(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0004_historical_qa")
    assert migration.down_revision == "0003_policy_library"
    operations = []

    class Bind:
        dialect = type("Dialect", (), {"name": "postgresql"})()

    class Op:
        def get_bind(self): return Bind()
        def create_table(self, name, *columns, **kwargs): operations.append(("table", name, columns, kwargs))
        def create_index(self, *args, **kwargs): operations.append(("index", args, kwargs))
        def execute(self, statement): operations.append(("sql", str(statement)))

    monkeypatch.setattr(migration, "op", Op())
    migration.upgrade()
    table = next(item for item in operations if item[0] == "table")
    names = {column.name for column in table[2] if hasattr(column, "name")}
    assert {"topic", "question_text", "answer_text", "source_url", "content_sha256"} <= names
    sql = [item[1] for item in operations if item[0] == "sql"]
    assert any("ENABLE ROW LEVEL SECURITY" in item for item in sql)
    assert any("FROM anon" in item for item in sql)
    assert any("FROM authenticated" in item for item in sql)
