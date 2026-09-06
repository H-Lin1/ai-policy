from __future__ import annotations

import importlib

from app.modules.policy.markdown import EXAMPLE_MARKDOWN, MAX_MARKDOWN_BYTES, parse_markdown
from app.modules.policy.schemas import MarkdownBatchRequest, MarkdownFileInput


def test_example_markdown_parses_ready() -> None:
    item = parse_markdown("policy-example.md", EXAMPLE_MARKDOWN)
    assert item.status == "ready"
    assert item.fields is not None
    assert item.fields.title == "深圳市科技创新专项资金管理办法"
    assert item.fields.source_type == "markdown"


def test_mixed_markdown_batch_is_isolated() -> None:
    ready = parse_markdown("ready.md", EXAMPLE_MARKDOWN)
    failed = parse_markdown("failed.md", "# no front matter")
    warning = parse_markdown("warning.md", EXAMPLE_MARKDOWN.replace("title:", "extra_field: ignored\ntitle:"))
    assert ready.status == "ready"
    assert failed.status == "failed" and failed.fields is None
    assert warning.status == "warning" and warning.fields is not None


def test_per_file_limit_has_no_aggregate_limit() -> None:
    # The request contract caps count, while no validator aggregates file bytes.
    files = [MarkdownFileInput(filename=f"policy-{index}.md", content=EXAMPLE_MARKDOWN) for index in range(20)]
    request = MarkdownBatchRequest(files=files)
    assert len(request.files) == 20
    oversized = "---\ntitle: x\n---\n" + ("政" * (MAX_MARKDOWN_BYTES // 3 + 1))
    assert parse_markdown("large.md", oversized).status == "failed"


def test_admin_policy_migration_contract(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0007_admin_policy_publishing")
    assert migration.down_revision == "0006_registration_applications"
    tables: list[str] = []
    commands: list[str] = []

    class Bind:
        class dialect:
            name = "postgresql"

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    for name in ("drop_constraint", "alter_column", "add_column", "create_foreign_key", "create_check_constraint", "create_unique_constraint", "create_index"):
        monkeypatch.setattr(migration.op, name, lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "create_table", lambda name, *args, **kwargs: tables.append(name))
    monkeypatch.setattr(migration.op, "execute", lambda statement: commands.append(str(statement)))
    migration.upgrade()
    assert tables == ["policy_document_events"]
    assert "ALTER TABLE app.policy_document_events ENABLE ROW LEVEL SECURITY" in commands
