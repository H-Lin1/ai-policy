from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from uuid import UUID

import pytest

from app.core.config import Settings
from scripts import init_iam

PROJECT_REF = "abcdefghijklmnopqrst"
VALID_ENVIRONMENT = {
    "IAM_DEMO_INDIVIDUAL_USER_ID": "00000000-0000-4000-8000-000000000001",
    "IAM_DEMO_ENTERPRISE_USER_ID": "00000000-0000-4000-8000-000000000002",
    "IAM_DEMO_GOVERNMENT_USER_ID": "00000000-0000-4000-8000-000000000003",
    "IAM_DEMO_ADMIN_USER_ID": "00000000-0000-4000-8000-000000000004",
}


def postgres_settings(*, project_ref: str = PROJECT_REF) -> Settings:
    return Settings(
        _env_file=None,
        database_url=(
            f"postgresql+psycopg://postgres@db.{project_ref}.supabase.co/postgres"
        ),
        supabase_url=f"https://{PROJECT_REF}.supabase.co",
    )


def demo_users() -> init_iam.DemoUserIds:
    users, state = init_iam.demo_user_ids(VALID_ENVIRONMENT)
    assert state == "ok" and users is not None
    return users


class FakeResult:
    def __init__(self, *, values=(), rows=()) -> None:
        self.values = tuple(values)
        self.rows = tuple(rows)

    def scalars(self):
        return iter(self.values)

    def mappings(self):
        return self

    def all(self):
        return list(self.rows)


class FakeConnection:
    def __init__(self, users: init_iam.DemoUserIds) -> None:
        self.revision = init_iam.IAM_REVISION
        self.auth_users = set(users.by_role().values())
        self.rows: dict[str, list[dict[str, object]]] = {
            "regions": [],
            "roles": [],
            "organizations": [],
            "profiles": [],
            "user_roles": [],
        }
        self.statements: list[str] = []
        self.insert_calls: list[tuple[str, int]] = []
        self.fail_on_insert: str | None = None
        self.fail_on_check = False

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.statements.append(sql)
        if self.fail_on_check and not sql.startswith("INSERT"):
            raise RuntimeError("private-check-detail")
        if "pg_advisory_xact_lock" in sql:
            assert parameters == {"lock_id": init_iam.IAM_SEED_LOCK_ID}
            return FakeResult()
        if "alembic_version" in sql:
            return FakeResult(values=(self.revision,))
        if "FROM auth.users" in sql:
            return FakeResult(values=self.auth_users)
        for table_name in self.rows:
            if f"FROM app.{table_name}" in sql:
                return FakeResult(rows=deepcopy(self.rows[table_name]))
            if f"INSERT INTO app.{table_name}" in sql:
                if self.fail_on_insert == table_name:
                    raise RuntimeError("private-write-detail")
                values = parameters if isinstance(parameters, list) else [parameters]
                self.rows[table_name].extend(deepcopy(values))
                self.insert_calls.append((table_name, len(values)))
                return FakeResult()
        raise AssertionError(f"unexpected statement shape: {type(statement).__name__}")


class FakeTransaction:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.snapshot: dict[str, list[dict[str, object]]] | None = None

    def __enter__(self):
        self.snapshot = deepcopy(self.connection.rows)
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None and self.snapshot is not None:
            self.connection.rows = self.snapshot
        return False


class FakeEngine:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.begin_count = 0

    def begin(self):
        self.begin_count += 1
        return FakeTransaction(self.connection)


def test_iam_init_preflight_and_partial_flags_never_call_apply(monkeypatch, capsys) -> None:
    called = False

    def unexpected_apply(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("IAM seed must not run before both approvals")

    monkeypatch.setattr(init_iam, "apply_iam_seed", unexpected_apply)

    assert init_iam.main([], settings=postgres_settings(), environment={}) == 0
    assert init_iam.main([init_iam.APPLY_IAM_SEED], settings=postgres_settings()) == 2
    assert init_iam.main([init_iam.CONFIRM], settings=postgres_settings()) == 2
    assert called is False
    output = capsys.readouterr().out
    assert "not_requested" in output
    assert PROJECT_REF not in output
    assert "postgresql+psycopg" not in output


@pytest.mark.parametrize(
    ("settings", "state"),
    [
        (Settings(_env_file=None, database_url="sqlite:///iam.db"), "unsupported_database_target"),
        (postgres_settings(project_ref="zyxwvutsrqponmlkjihg"), "project_mismatch"),
        (
            Settings(
                _env_file=None,
                database_url="postgresql+psycopg://postgres@example.invalid/postgres",
                supabase_url=f"https://{PROJECT_REF}.supabase.co",
            ),
            "project_unresolved",
        ),
    ],
)
def test_iam_init_rejects_unsafe_or_unbound_target_before_mapping_or_apply(
    monkeypatch, capsys, settings, state
) -> None:
    called = False

    def unexpected_apply(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("unsafe database target must not reach apply")

    monkeypatch.setattr(init_iam, "apply_iam_seed", unexpected_apply)
    assert (
        init_iam.main(
            [init_iam.APPLY_IAM_SEED, init_iam.CONFIRM],
            settings=settings,
            environment=VALID_ENVIRONMENT,
        )
        == 2
    )
    assert called is False
    output = capsys.readouterr().out
    assert state in output
    assert PROJECT_REF not in output


@pytest.mark.parametrize(
    ("environment", "state"),
    [
        ({}, "user_mappings_missing"),
        ({**VALID_ENVIRONMENT, "IAM_DEMO_ADMIN_USER_ID": "not-a-uuid"}, "user_mappings_invalid"),
        (
            {
                **VALID_ENVIRONMENT,
                "IAM_DEMO_ADMIN_USER_ID": VALID_ENVIRONMENT["IAM_DEMO_INDIVIDUAL_USER_ID"],
            },
            "user_mappings_duplicated",
        ),
    ],
)
def test_iam_init_rejects_invalid_user_mappings_before_apply(
    monkeypatch, capsys, environment, state
) -> None:
    monkeypatch.setattr(
        init_iam,
        "apply_iam_seed",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("invalid mapping must not reach apply")
        ),
    )
    assert (
        init_iam.main(
            [init_iam.APPLY_IAM_SEED, init_iam.CONFIRM],
            settings=postgres_settings(),
            environment=environment,
        )
        == 2
    )
    assert state in capsys.readouterr().out


def test_iam_init_passes_validated_mapping_without_printing_values(monkeypatch, capsys) -> None:
    captured = None

    def fake_apply(settings, user_ids):
        nonlocal captured
        captured = user_ids
        return True, "ok"

    monkeypatch.setattr(init_iam, "apply_iam_seed", fake_apply)
    assert (
        init_iam.main(
            [init_iam.APPLY_IAM_SEED, init_iam.CONFIRM],
            settings=postgres_settings(),
            environment=VALID_ENVIRONMENT,
        )
        == 0
    )
    assert captured is not None
    assert len(set(captured.by_role().values())) == 4
    output = capsys.readouterr().out
    assert "iam_seed: applied" in output
    assert PROJECT_REF not in output
    assert all(value not in output for value in VALID_ENVIRONMENT.values())


def test_iam_init_loads_mapping_from_shared_settings_env_file(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            (
                f"SUPABASE_URL=https://{PROJECT_REF}.supabase.co",
                (
                    "DATABASE_URL="
                    f"postgresql+psycopg://postgres@db.{PROJECT_REF}.supabase.co/postgres"
                ),
                *(f"{key}={value}" for key, value in VALID_ENVIRONMENT.items()),
            )
        ),
        encoding="utf-8",
    )
    settings = Settings(_env_file=env_file)
    captured = None

    def fake_apply(runtime_settings, user_ids):
        nonlocal captured
        captured = user_ids
        assert runtime_settings is settings
        return True, "ok"

    monkeypatch.setattr(init_iam, "apply_iam_seed", fake_apply)

    assert init_iam.main([init_iam.APPLY_IAM_SEED, init_iam.CONFIRM], settings=settings) == 0
    assert captured is not None
    assert len(set(captured.by_role().values())) == 4
    output = capsys.readouterr().out
    assert "iam_seed: applied" in output
    assert PROJECT_REF not in output
    assert all(value not in output for value in VALID_ENVIRONMENT.values())


def test_process_environment_overrides_iam_mapping_env_file(
    monkeypatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"IAM_DEMO_ADMIN_USER_ID={VALID_ENVIRONMENT['IAM_DEMO_INDIVIDUAL_USER_ID']}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("IAM_DEMO_ADMIN_USER_ID", VALID_ENVIRONMENT["IAM_DEMO_ADMIN_USER_ID"])

    settings = Settings(_env_file=env_file)

    assert settings.iam_demo_admin_user_id == VALID_ENVIRONMENT["IAM_DEMO_ADMIN_USER_ID"]


def test_iam_init_sanitizes_unexpected_apply_failure(monkeypatch, capsys) -> None:
    marker = "iam-secret-marker"
    monkeypatch.setattr(
        init_iam,
        "apply_iam_seed",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(marker)),
    )
    assert (
        init_iam.main(
            [init_iam.APPLY_IAM_SEED, init_iam.CONFIRM],
            settings=postgres_settings(),
            environment=VALID_ENVIRONMENT,
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "execution_failed" in output
    assert marker not in output
    assert "Traceback" not in output


def test_seed_runs_checks_and_inserts_on_one_locked_transaction_then_becomes_noop(
    monkeypatch,
) -> None:
    users = demo_users()
    connection = FakeConnection(users)
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_iam, "database_engine", lambda settings: engine)

    assert init_iam.apply_iam_seed(postgres_settings(), users) == (True, "ok")
    assert connection.insert_calls == [
        ("regions", 1),
        ("roles", 4),
        ("organizations", 3),
        ("profiles", 4),
        ("user_roles", 4),
    ]
    first_rows = deepcopy(connection.rows)
    first_insert_calls = list(connection.insert_calls)

    assert init_iam.apply_iam_seed(postgres_settings(), users) == (True, "ok")
    assert connection.rows == first_rows
    assert connection.insert_calls == first_insert_calls
    assert engine.begin_count == 2
    assert sum("pg_advisory_xact_lock" in sql for sql in connection.statements) == 2


@pytest.mark.parametrize(
    "conflicting_rows",
    [
        {
            "roles": [
                {
                    **init_iam._expected_seed(demo_users()).roles[0],
                    "id": UUID("99999999-0000-4000-8000-000000000001"),
                }
            ]
        },
        {
            "profiles": [
                {
                    **init_iam._expected_seed(demo_users()).profiles[0],
                    "is_demo": False,
                }
            ]
        },
        {
            "profiles": [
                {
                    **init_iam._expected_seed(demo_users()).profiles[0],
                    "status": "disabled",
                }
            ]
        },
        {
            "profiles": [
                {
                    **init_iam._expected_seed(demo_users()).profiles[0],
                    "user_id": UUID("99999999-0000-4000-8000-000000000001"),
                }
            ]
        },
        {
            "user_roles": [
                {
                    **init_iam._expected_seed(demo_users()).user_roles[0],
                    "role_id": init_iam.ROLE_IDS["admin"],
                }
            ]
        },
        {
            "user_roles": [
                {
                    **init_iam._expected_seed(demo_users()).user_roles[0],
                    "is_active": False,
                }
            ]
        },
    ],
)
def test_seed_rejects_id_collision_non_demo_disabled_drift_and_role_conflict(
    monkeypatch, conflicting_rows
) -> None:
    users = demo_users()
    connection = FakeConnection(users)
    connection.rows.update(deepcopy(conflicting_rows))
    before = deepcopy(connection.rows)
    monkeypatch.setattr(
        init_iam,
        "database_engine",
        lambda settings: FakeEngine(connection),
    )

    assert init_iam.apply_iam_seed(postgres_settings(), users) == (False, "seed_conflict")
    assert connection.rows == before
    assert connection.insert_calls == []


def test_seed_rejects_revision_and_missing_auth_users_without_writes(monkeypatch) -> None:
    users = demo_users()
    connection = FakeConnection(users)
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_iam, "database_engine", lambda settings: engine)

    connection.revision = "0001_foundation_schema"
    assert init_iam.apply_iam_seed(postgres_settings(), users) == (
        False,
        "revision_mismatch",
    )
    connection.revision = init_iam.IAM_REVISION
    connection.auth_users.pop()
    assert init_iam.apply_iam_seed(postgres_settings(), users) == (
        False,
        "auth_users_missing",
    )
    assert connection.insert_calls == []


def test_seed_rolls_back_every_insert_when_a_later_write_fails(monkeypatch) -> None:
    users = demo_users()
    connection = FakeConnection(users)
    connection.fail_on_insert = "profiles"
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_iam, "database_engine", lambda settings: engine)

    assert init_iam.apply_iam_seed(postgres_settings(), users) == (False, "write_failed")
    assert all(not rows for rows in connection.rows.values())


def test_seed_sanitizes_check_failure_and_never_opens_separate_connection(monkeypatch) -> None:
    users = demo_users()
    connection = FakeConnection(users)
    connection.fail_on_check = True
    engine = FakeEngine(connection)
    monkeypatch.setattr(init_iam, "database_engine", lambda settings: engine)

    assert init_iam.apply_iam_seed(postgres_settings(), users) == (False, "check_failed")
    assert engine.begin_count == 1
    assert not hasattr(engine, "connect")


def test_initializer_has_no_update_delete_subprocess_or_auth_admin_surface() -> None:
    namespace = vars(init_iam)
    assert "subprocess" not in namespace
    assert "supabase" not in namespace
    source_names = {
        *init_iam._insert_seed_plan.__code__.co_names,
        *init_iam.apply_iam_seed.__code__.co_names,
    }
    assert not {"update", "remove", "unlink", "rmtree", "drop", "delete"} & source_names
    assert init_iam.IAM_REVISION == "0002_identity_access"
    assert isinstance(init_iam.REGION_ID, UUID)
