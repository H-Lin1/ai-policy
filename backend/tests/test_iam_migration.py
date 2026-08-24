from __future__ import annotations

import importlib
from types import SimpleNamespace

import sqlalchemy as sa
from sqlalchemy.sql.elements import ClauseElement

from app.modules.iam.models import Organization, Profile, Region, Role, UserRole

migration = importlib.import_module("migrations.versions.0002_identity_access")

TABLE_ORDER = ("regions", "roles", "organizations", "profiles", "user_roles")
MODEL_TABLES = {
    "regions": Region.__table__,
    "roles": Role.__table__,
    "organizations": Organization.__table__,
    "profiles": Profile.__table__,
    "user_roles": UserRole.__table__,
}


class FakeOperations:
    def __init__(self) -> None:
        self.created: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.executed: list[str] = []
        self.dropped: list[tuple[str, str | None]] = []

    @staticmethod
    def get_bind():
        return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    def create_table(self, name: str, *items, **kwargs) -> None:
        self.created.append((name, items, kwargs))

    def execute(self, statement: str) -> None:
        self.executed.append(str(statement))

    def drop_table(self, name: str, *, schema: str | None = None) -> None:
        self.dropped.append((name, schema))


def _run_upgrade(monkeypatch) -> FakeOperations:
    operations = FakeOperations()
    monkeypatch.setattr(migration, "op", operations)
    migration.upgrade()
    return operations


def _created_items(operations: FakeOperations) -> dict[str, tuple[object, ...]]:
    return {name: items for name, items, _ in operations.created}


def _columns(items: tuple[object, ...]) -> dict[str, sa.Column]:
    return {item.name: item for item in items if isinstance(item, sa.Column)}


def _checks(items: tuple[object, ...]) -> dict[str, str]:
    return {
        item.name: str(item.sqltext)
        for item in items
        if isinstance(item, sa.CheckConstraint) and item.name is not None
    }


def _defaults(columns: dict[str, sa.Column]) -> dict[str, str]:
    return {
        name: str(column.server_default.arg)
        for name, column in columns.items()
        if column.server_default is not None
    }


def _foreign_keys(items: tuple[object, ...]) -> dict[tuple[str, ...], tuple[tuple[str, ...], str]]:
    return {
        tuple(item.column_keys): (
            tuple(element.target_fullname for element in item.elements),
            item.ondelete,
        )
        for item in items
        if isinstance(item, sa.ForeignKeyConstraint)
    }


def test_iam_migration_creates_only_approved_tables_in_dependency_order(monkeypatch) -> None:
    operations = _run_upgrade(monkeypatch)

    assert migration.revision == "0002_identity_access"
    assert migration.down_revision == "0001_foundation_schema"
    assert tuple(name for name, _, _ in operations.created) == TABLE_ORDER
    assert all(kwargs["schema"] == "app" for _, _, kwargs in operations.created)


def test_iam_migration_uses_only_restrictive_foreign_keys(monkeypatch) -> None:
    tables = _created_items(_run_upgrade(monkeypatch))

    expected = {
        "regions": {
            ("parent_id",): (("app.regions.id",), "RESTRICT"),
        },
        "roles": {},
        "organizations": {
            ("region_id",): (("app.regions.id",), "RESTRICT"),
            ("parent_id",): (("app.organizations.id",), "RESTRICT"),
        },
        "profiles": {
            ("user_id",): (("auth.users.id",), "RESTRICT"),
            ("region_id",): (("app.regions.id",), "RESTRICT"),
            ("organization_id",): (("app.organizations.id",), "RESTRICT"),
        },
        "user_roles": {
            ("user_id",): (("app.profiles.user_id",), "RESTRICT"),
            ("role_id",): (("app.roles.id",), "RESTRICT"),
        },
    }

    assert {table: _foreign_keys(items) for table, items in tables.items()} == expected


def test_iam_migration_enforces_checks_defaults_and_nullability(monkeypatch) -> None:
    tables = _created_items(_run_upgrade(monkeypatch))

    expected_checks = {
        "regions": {
            "ck_regions_code": "code = lower(btrim(code)) AND length(btrim(code)) > 0",
            "ck_regions_name": "length(btrim(name)) > 0",
            "ck_regions_level": (
                "level IN ('country', 'province', 'city', 'district', 'other')"
            ),
        },
        "roles": {
            "ck_roles_code": (
                "code IN ('individual', 'enterprise', 'government', 'admin')"
            ),
            "ck_roles_code_normalized": (
                "code = lower(btrim(code)) AND length(btrim(code)) > 0"
            ),
            "ck_roles_name": "length(btrim(name)) > 0",
            "ck_roles_description": "length(btrim(description)) > 0",
        },
        "organizations": {
            "ck_organizations_type": (
                "organization_type IN ('platform', 'government', 'enterprise')"
            ),
            "ck_organizations_code": (
                "code = lower(btrim(code)) AND length(btrim(code)) > 0"
            ),
            "ck_organizations_name": "length(btrim(name)) > 0",
        },
        "profiles": {
            "ck_profiles_status": "status IN ('active', 'disabled')",
            "ck_profiles_display_name": "length(btrim(display_name)) > 0",
        },
        "user_roles": {},
    }
    expected_defaults = {
        "regions": {"is_active": "true", "created_at": "now()", "updated_at": "now()"},
        "roles": {"is_active": "true", "created_at": "now()", "updated_at": "now()"},
        "organizations": {
            "is_active": "true",
            "is_demo": "false",
            "created_at": "now()",
            "updated_at": "now()",
        },
        "profiles": {
            "status": "'active'",
            "is_demo": "false",
            "created_at": "now()",
            "updated_at": "now()",
        },
        "user_roles": {"is_active": "true", "assigned_at": "now()"},
    }
    expected_nullable_columns = {
        "regions": {"parent_id"},
        "roles": set(),
        "organizations": {"parent_id"},
        "profiles": {"organization_id"},
        "user_roles": set(),
    }

    for table_name, items in tables.items():
        columns = _columns(items)
        assert _checks(items) == expected_checks[table_name]
        assert _defaults(columns) == expected_defaults[table_name]
        assert {name for name, column in columns.items() if column.nullable} == (
            expected_nullable_columns[table_name]
        )

    timestamp_columns = {
        "regions": ("created_at", "updated_at"),
        "roles": ("created_at", "updated_at"),
        "organizations": ("created_at", "updated_at"),
        "profiles": ("created_at", "updated_at"),
        "user_roles": ("assigned_at",),
    }
    for table_name, names in timestamp_columns.items():
        columns = _columns(tables[table_name])
        assert all(isinstance(columns[name].type, sa.DateTime) for name in names)
        assert all(columns[name].type.timezone is True for name in names)


def test_iam_migration_enables_rls_and_revokes_both_browser_roles(monkeypatch) -> None:
    operations = _run_upgrade(monkeypatch)
    expected_statements = []
    for table in TABLE_ORDER:
        expected_statements.extend(
            (
                f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY",
                f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM anon",
                f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM authenticated",
            )
        )

    assert operations.executed == expected_statements
    assert sum("ENABLE ROW LEVEL SECURITY" in item for item in operations.executed) == 5
    assert sum(item.startswith("REVOKE ALL PRIVILEGES") for item in operations.executed) == 10


def test_iam_migration_creates_no_policy_or_auth_mutation(monkeypatch) -> None:
    operations = _run_upgrade(monkeypatch)

    assert tuple(name for name, _, _ in operations.created) == TABLE_ORDER
    assert all(" POLICY " not in f" {statement.upper()} " for statement in operations.executed)
    assert all("auth." not in statement.lower() for statement in operations.executed)

    profile_fks = _foreign_keys(_created_items(operations)["profiles"])
    assert profile_fks[("user_id",)] == (("auth.users.id",), "RESTRICT")


def test_orm_metadata_matches_migration_contract_without_managed_auth_table(monkeypatch) -> None:
    migration_tables = _created_items(_run_upgrade(monkeypatch))

    for table_name, model_table in MODEL_TABLES.items():
        migration_columns = _columns(migration_tables[table_name])
        assert set(model_table.c.keys()) == set(migration_columns)
        assert {name: column.nullable for name, column in model_table.c.items()} == {
            name: column.nullable for name, column in migration_columns.items()
        }
        assert _defaults(dict(model_table.c.items())) == _defaults(migration_columns)
        assert {
            constraint.name: str(constraint.sqltext)
            for constraint in model_table.constraints
            if isinstance(constraint, sa.CheckConstraint) and constraint.name is not None
        } == _checks(migration_tables[table_name])

    organization_code_uniques = [
        constraint
        for constraint in Organization.__table__.constraints
        if isinstance(constraint, sa.UniqueConstraint)
        and tuple(constraint.columns.keys()) == ("code",)
    ]
    assert len(organization_code_uniques) == 1
    assert organization_code_uniques[0].name == "uq_organizations_code"
    assert Organization.__table__.c.code.unique in (None, False)
    assert not Organization.__table__.c.code.index

    assert not Profile.__table__.c.user_id.foreign_keys
    assert all(
        foreign_key.ondelete == "RESTRICT"
        for table in MODEL_TABLES.values()
        for foreign_key in table.foreign_keys
    )
    assert Profile.user_roles.property.passive_deletes is True
    assert Role.assignments.property.passive_deletes is True
    assert "delete" not in Profile.user_roles.property.cascade

    assert all(
        isinstance(column.server_default.arg, ClauseElement)
        for table in MODEL_TABLES.values()
        for column in table.c
        if column.server_default is not None
    )


def test_iam_migration_downgrade_reverses_dependencies_without_dropping_schema(
    monkeypatch,
) -> None:
    operations = FakeOperations()
    monkeypatch.setattr(migration, "op", operations)

    migration.downgrade()

    assert operations.dropped == [
        ("user_roles", "app"),
        ("profiles", "app"),
        ("organizations", "app"),
        ("roles", "app"),
        ("regions", "app"),
    ]
    assert operations.executed == []


def test_iam_migration_is_noop_for_non_postgresql(monkeypatch) -> None:
    operations = FakeOperations()
    operations.get_bind = lambda: SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    monkeypatch.setattr(migration, "op", operations)

    migration.upgrade()
    migration.downgrade()

    assert operations.created == []
    assert operations.executed == []
    assert operations.dropped == []
