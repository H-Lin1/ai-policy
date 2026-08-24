from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import bindparam, insert, or_, select, text

from app.core.config import Settings
from app.core.database import database_engine
from app.core.supabase_target import supabase_target_binding_state
from app.modules.iam.models import Organization, Profile, Region, Role, UserRole

APPLY_IAM_SEED = "--apply-iam-seed"
CONFIRM = "--confirm"
IAM_REVISION = "0002_identity_access"
IAM_SEED_LOCK_ID = 11_000_002

USER_ENV_KEYS = {
    "individual": "IAM_DEMO_INDIVIDUAL_USER_ID",
    "enterprise": "IAM_DEMO_ENTERPRISE_USER_ID",
    "government": "IAM_DEMO_GOVERNMENT_USER_ID",
    "admin": "IAM_DEMO_ADMIN_USER_ID",
}
USER_SETTING_FIELDS = {
    "individual": "iam_demo_individual_user_id",
    "enterprise": "iam_demo_enterprise_user_id",
    "government": "iam_demo_government_user_id",
    "admin": "iam_demo_admin_user_id",
}

REGION_ID = UUID("10000000-0000-4000-8000-000000000001")
ROLE_IDS = {
    "individual": UUID("20000000-0000-4000-8000-000000000001"),
    "enterprise": UUID("20000000-0000-4000-8000-000000000002"),
    "government": UUID("20000000-0000-4000-8000-000000000003"),
    "admin": UUID("20000000-0000-4000-8000-000000000004"),
}
ORGANIZATION_IDS = {
    "platform": UUID("30000000-0000-4000-8000-000000000001"),
    "government": UUID("30000000-0000-4000-8000-000000000002"),
    "enterprise": UUID("30000000-0000-4000-8000-000000000003"),
}


@dataclass(frozen=True)
class DemoUserIds:
    individual: UUID
    enterprise: UUID
    government: UUID
    admin: UUID

    def by_role(self) -> dict[str, UUID]:
        return {
            "individual": self.individual,
            "enterprise": self.enterprise,
            "government": self.government,
            "admin": self.admin,
        }


@dataclass(frozen=True)
class SeedPlan:
    regions: tuple[dict[str, object], ...]
    roles: tuple[dict[str, object], ...]
    organizations: tuple[dict[str, object], ...]
    profiles: tuple[dict[str, object], ...]
    user_roles: tuple[dict[str, object], ...]


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def database_target_state(settings: Settings) -> str:
    database_url = settings.normalized_database_url
    if not database_url:
        return "not_configured"
    if database_url.lower().startswith("postgresql+psycopg://"):
        binding_state = supabase_target_binding_state(settings)
        return "postgresql_configured" if binding_state == "ok" else binding_state
    return "unsupported_database_target"


def demo_user_ids(environment: Mapping[str, str]) -> tuple[DemoUserIds | None, str]:
    values: dict[str, UUID] = {}
    for role, key in USER_ENV_KEYS.items():
        raw_value = environment.get(key, "").strip()
        if not raw_value:
            return None, "user_mappings_missing"
        try:
            values[role] = UUID(raw_value)
        except (TypeError, ValueError):
            return None, "user_mappings_invalid"
    if len(set(values.values())) != len(values):
        return None, "user_mappings_duplicated"
    return DemoUserIds(**values), "ok"


def settings_user_environment(settings: Settings) -> dict[str, str]:
    return {
        USER_ENV_KEYS[role]: getattr(settings, setting_field) or ""
        for role, setting_field in USER_SETTING_FIELDS.items()
    }


def _expected_seed(user_ids: DemoUserIds) -> SeedPlan:
    roles = (
        {
            "id": ROLE_IDS["individual"],
            "code": "individual",
            "name": "个人",
            "description": "个人政策服务与咨询入口",
            "is_active": True,
        },
        {
            "id": ROLE_IDS["enterprise"],
            "code": "enterprise",
            "name": "企业",
            "description": "企业政策服务与业务入口",
            "is_active": True,
        },
        {
            "id": ROLE_IDS["government"],
            "code": "government",
            "name": "政府",
            "description": "政府政策与咨询办理入口",
            "is_active": True,
        },
        {
            "id": ROLE_IDS["admin"],
            "code": "admin",
            "name": "管理员",
            "description": "平台配置与管理入口",
            "is_active": True,
        },
    )
    organizations = (
        {
            "id": ORGANIZATION_IDS["platform"],
            "code": "sz-platform",
            "name": "深圳政策服务平台",
            "organization_type": "platform",
            "region_id": REGION_ID,
            "parent_id": None,
            "is_active": True,
            "is_demo": False,
        },
        {
            "id": ORGANIZATION_IDS["government"],
            "code": "sz-demo-government",
            "name": "深圳政策服务演示部门",
            "organization_type": "government",
            "region_id": REGION_ID,
            "parent_id": None,
            "is_active": True,
            "is_demo": True,
        },
        {
            "id": ORGANIZATION_IDS["enterprise"],
            "code": "sz-demo-enterprise",
            "name": "深圳演示企业",
            "organization_type": "enterprise",
            "region_id": REGION_ID,
            "parent_id": None,
            "is_active": True,
            "is_demo": True,
        },
    )
    user_mapping = user_ids.by_role()
    profiles = (
        {
            "user_id": user_mapping["individual"],
            "display_name": "个人演示用户",
            "region_id": REGION_ID,
            "organization_id": None,
            "status": "active",
            "is_demo": True,
        },
        {
            "user_id": user_mapping["enterprise"],
            "display_name": "企业演示用户",
            "region_id": REGION_ID,
            "organization_id": ORGANIZATION_IDS["enterprise"],
            "status": "active",
            "is_demo": True,
        },
        {
            "user_id": user_mapping["government"],
            "display_name": "政府演示用户",
            "region_id": REGION_ID,
            "organization_id": ORGANIZATION_IDS["government"],
            "status": "active",
            "is_demo": True,
        },
        {
            "user_id": user_mapping["admin"],
            "display_name": "管理员演示用户",
            "region_id": REGION_ID,
            "organization_id": ORGANIZATION_IDS["platform"],
            "status": "active",
            "is_demo": True,
        },
    )
    return SeedPlan(
        regions=(
            {
                "id": REGION_ID,
                "code": "sz",
                "name": "深圳市",
                "parent_id": None,
                "level": "city",
                "is_active": True,
            },
        ),
        roles=roles,
        organizations=organizations,
        profiles=profiles,
        user_roles=tuple(
            {
                "user_id": user_id,
                "role_id": ROLE_IDS[role],
                "is_active": True,
            }
            for role, user_id in user_mapping.items()
        ),
    )


def _values_equal(actual: object, expected: object) -> bool:
    if isinstance(expected, UUID):
        try:
            return UUID(str(actual)) == expected
        except (TypeError, ValueError):
            return False
    return actual == expected


def _plan_records(
    existing: Sequence[Mapping[str, object]],
    expected: Sequence[dict[str, object]],
    *,
    identity_fields: tuple[str, ...],
) -> tuple[dict[str, object], ...] | None:
    matched: set[int] = set()
    for row in existing:
        candidates = [
            index
            for index, record in enumerate(expected)
            if any(_values_equal(row.get(field), record[field]) for field in identity_fields)
        ]
        if len(candidates) != 1 or candidates[0] in matched:
            return None
        index = candidates[0]
        if any(not _values_equal(row.get(field), value) for field, value in expected[index].items()):
            return None
        matched.add(index)
    return tuple(record for index, record in enumerate(expected) if index not in matched)


def _locked_rows(connection, statement) -> tuple[Mapping[str, object], ...]:
    result = connection.execute(statement.with_for_update())
    return tuple(result.mappings().all())


def _seed_plan(connection, user_ids: DemoUserIds) -> tuple[str, SeedPlan | None]:
    expected = _expected_seed(user_ids)
    revisions = tuple(
        connection.execute(text("SELECT version_num FROM alembic_version FOR SHARE")).scalars()
    )
    if revisions != (IAM_REVISION,):
        return "revision_mismatch", None

    mapped_user_ids = tuple(user_ids.by_role().values())
    auth_query = text(
        "SELECT id FROM auth.users WHERE id IN :user_ids FOR KEY SHARE"
    ).bindparams(bindparam("user_ids", expanding=True))
    existing_users = {
        UUID(str(value))
        for value in connection.execute(auth_query, {"user_ids": mapped_user_ids}).scalars()
    }
    if existing_users != set(mapped_user_ids):
        return "auth_users_missing", None

    region_rows = _locked_rows(
        connection,
        select(Region.__table__).where(
            or_(
                Region.__table__.c.id.in_([record["id"] for record in expected.regions]),
                Region.__table__.c.code.in_([record["code"] for record in expected.regions]),
            )
        ),
    )
    role_rows = _locked_rows(
        connection,
        select(Role.__table__).where(
            or_(
                Role.__table__.c.id.in_([record["id"] for record in expected.roles]),
                Role.__table__.c.code.in_([record["code"] for record in expected.roles]),
            )
        ),
    )
    organization_rows = _locked_rows(
        connection,
        select(Organization.__table__).where(
            or_(
                Organization.__table__.c.id.in_(
                    [record["id"] for record in expected.organizations]
                ),
                Organization.__table__.c.code.in_(
                    [record["code"] for record in expected.organizations]
                ),
            )
        ),
    )
    profile_rows = _locked_rows(
        connection,
        select(Profile.__table__).where(
            or_(
                Profile.__table__.c.user_id.in_(mapped_user_ids),
                Profile.__table__.c.is_demo.is_(True),
            )
        ),
    )
    assignment_rows = _locked_rows(
        connection,
        select(UserRole.__table__).where(UserRole.__table__.c.user_id.in_(mapped_user_ids)),
    )

    missing_regions = _plan_records(region_rows, expected.regions, identity_fields=("id", "code"))
    missing_roles = _plan_records(role_rows, expected.roles, identity_fields=("id", "code"))
    missing_organizations = _plan_records(
        organization_rows,
        expected.organizations,
        identity_fields=("id", "code"),
    )
    missing_profiles = _plan_records(
        profile_rows,
        expected.profiles,
        identity_fields=("user_id", "display_name"),
    )
    missing_assignments = _plan_records(
        assignment_rows,
        expected.user_roles,
        identity_fields=("user_id",),
    )
    if any(
        records is None
        for records in (
            missing_regions,
            missing_roles,
            missing_organizations,
            missing_profiles,
            missing_assignments,
        )
    ):
        return "seed_conflict", None
    return (
        "ok",
        SeedPlan(
            regions=missing_regions,
            roles=missing_roles,
            organizations=missing_organizations,
            profiles=missing_profiles,
            user_roles=missing_assignments,
        ),
    )


def _insert_seed_plan(connection, plan: SeedPlan) -> None:
    for table, records in (
        (Region.__table__, plan.regions),
        (Role.__table__, plan.roles),
        (Organization.__table__, plan.organizations),
        (Profile.__table__, plan.profiles),
        (UserRole.__table__, plan.user_roles),
    ):
        if records:
            connection.execute(insert(table), list(records))


def apply_iam_seed(settings: Settings, user_ids: DemoUserIds) -> tuple[bool, str]:
    binding_state = supabase_target_binding_state(settings)
    if binding_state != "ok":
        return False, binding_state
    try:
        engine = database_engine(settings)
    except Exception:  # noqa: BLE001 - configuration values stay private.
        return False, "configuration_invalid"
    if engine is None:
        return False, "not_configured"
    phase = "check"
    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_id)"),
                {"lock_id": IAM_SEED_LOCK_ID},
            )
            state, plan = _seed_plan(connection, user_ids)
            if state != "ok" or plan is None:
                return False, state
            phase = "write"
            _insert_seed_plan(connection, plan)
    except Exception:  # noqa: BLE001 - database errors can expose target and record values.
        return False, "check_failed" if phase == "check" else "write_failed"
    return True, "ok"


def main(
    argv: Sequence[str] | None = None,
    *,
    settings: Settings | None = None,
    environment: Mapping[str, str] | None = None,
) -> int:
    arguments = _arguments(argv)
    if any(argument not in {APPLY_IAM_SEED, CONFIRM} for argument in arguments):
        print("iam_seed: invalid_arguments")
        return 2

    try:
        runtime_settings = settings or Settings()
        target_state = database_target_state(runtime_settings)
    except Exception:  # noqa: BLE001 - validation errors can echo environment input.
        print("iam_seed: configuration_invalid")
        return 2

    apply_requested = APPLY_IAM_SEED in arguments
    confirmed = CONFIRM in arguments
    if not apply_requested and not confirmed:
        print(f"iam_seed: not_requested ({target_state})")
        print("No IAM seed, Auth account, migration, or data change was performed.")
        return 0
    if not apply_requested:
        print("iam_seed: apply_flag_required")
        return 2
    if not confirmed:
        print("iam_seed: confirmation_required")
        return 2
    if target_state != "postgresql_configured":
        print(f"iam_seed: {target_state}")
        return 2

    mapping_environment = (
        environment if environment is not None else settings_user_environment(runtime_settings)
    )
    user_ids, state = demo_user_ids(mapping_environment)
    if user_ids is None:
        print(f"iam_seed: {state}")
        return 2

    try:
        passed, state = apply_iam_seed(runtime_settings, user_ids)
    except Exception:  # noqa: BLE001 - keep unexpected implementation details private.
        print("iam_seed: execution_failed")
        return 1
    print(f"iam_seed: {'applied' if passed else state}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
