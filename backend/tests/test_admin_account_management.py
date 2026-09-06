from __future__ import annotations

import importlib

import pytest

from app.core.errors import AppError
from app.modules.iam.account_service import admin_id
from app.modules.iam.service import IdentityContext


def identity(role: str) -> IdentityContext:
    return IdentityContext(
        subject="00000000-0000-4000-8000-000000000111",
        email=None,
        display_name="tester",
        roles=(type("Role", (), {"code": role, "name": role})(),),
        region_code="sz",
        region_name="深圳市",
        organization_code=None,
        organization_name=None,
        organization_type=None,
    )


def test_account_management_requires_admin() -> None:
    with pytest.raises(AppError) as error:
        admin_id(identity("individual"))
    assert error.value.code == "ROLE_FORBIDDEN"
    assert str(admin_id(identity("admin"))) == "00000000-0000-4000-8000-000000000111"


def test_account_management_migration_contract(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0008_admin_account_management")
    assert migration.down_revision == "0007_admin_policy_publishing"
    tables: list[str] = []
    commands: list[str] = []

    class Bind:
        class dialect:
            name = "postgresql"

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    monkeypatch.setattr(migration.op, "add_column", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "create_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "create_table", lambda name, *args, **kwargs: tables.append(name))
    monkeypatch.setattr(migration.op, "execute", lambda statement: commands.append(str(statement)))
    migration.upgrade()
    assert tables == ["account_management_events"]
    assert "ALTER TABLE app.account_management_events ENABLE ROW LEVEL SECURITY" in commands


def test_account_management_migration_is_non_postgresql_noop(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.0008_admin_account_management")

    class Bind:
        class dialect:
            name = "sqlite"

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    migration.upgrade()
    migration.downgrade()
