"""Explicitly bind the classifier's 35 departments to their dedicated Auth accounts.

The supplied account document remains local-only.  This script reads account email
addresses solely to look up existing ``auth.users`` rows and never prints them.
It never creates Auth users or changes credentials.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import bindparam, insert, select, text

from app.core.config import Settings
from app.core.database import database_engine
from app.core.supabase_target import supabase_target_binding_state
from app.modules.iam.models import Organization, Profile, Role, UserRole
from scripts.init_iam import REGION_ID, ROLE_IDS

APPLY = "--apply-consultation-departments"
CONFIRM = "--confirm"
LOCK_ID = 11_000_005
REVISION = "0005_consultation_workflow"
NAMESPACE = UUID("7ea54099-ca2c-4928-bffb-d05ea073b60a")
DEFAULT_ACCOUNT_FILE = Path(__file__).resolve().parents[2] / "SUPABASE_SZ_GOV_TEST_ACCOUNTS.md"
DEFAULT_LABEL_FILE = Path(__file__).resolve().parents[1] / "models" / "sz" / "department_label_bindings.json"


def _parse_accounts(path: Path) -> tuple[dict[str, tuple[str, str]], str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        data = [line for line in lines if line.lstrip().startswith("|")][2:]
        result: dict[str, tuple[str, str]] = {}
        for line in data:
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) != 6 or not cells[1] or not cells[2] or not cells[3]:
                return {}, "account_file_invalid"
            department_id, department_name, email = cells[1:4]
            if department_id in result:
                return {}, "account_file_invalid"
            result[department_id] = (department_name, email)
        return result, "ok" if len(result) == 35 else "account_file_invalid"
    except Exception:  # noqa: BLE001 - account file contents are sensitive.
        return {}, "account_file_unavailable"


def _labels(path: Path) -> tuple[dict[str, str], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        labels = {item["department_id"]: item["department_name"] for item in payload["labels"]}
        return labels, "ok" if payload.get("region_id") == "sz" and len(labels) == 35 else "label_file_invalid"
    except Exception:  # noqa: BLE001 - label paths and parse details stay private.
        return {}, "label_file_unavailable"


def _code(department_id: str) -> str:
    return f"sz-{department_id}".lower()[:64]


def _org_id(department_id: str) -> UUID:
    return uuid5(NAMESPACE, f"organization:{department_id}")


def _matches_expected(
    rows: list[dict[str, object]], expected: list[dict[str, object]], *, key: str
) -> bool:
    if len(rows) != len(expected):
        return False
    expected_by_key = {str(item[key]): item for item in expected}
    if len(expected_by_key) != len(expected):
        return False
    for row in rows:
        candidate = expected_by_key.get(str(row.get(key)))
        if candidate is None:
            return False
        for field, value in candidate.items():
            actual = row.get(field)
            if isinstance(value, UUID):
                try:
                    if UUID(str(actual)) != value:
                        return False
                except (TypeError, ValueError):
                    return False
            elif actual != value:
                return False
    return True


def bind(settings: Settings, *, accounts_path: Path = DEFAULT_ACCOUNT_FILE, labels_path: Path = DEFAULT_LABEL_FILE) -> tuple[bool, str]:
    if supabase_target_binding_state(settings) != "ok":
        return False, "postgresql_not_configured"
    accounts, account_state = _parse_accounts(accounts_path)
    labels, label_state = _labels(labels_path)
    if account_state != "ok" or label_state != "ok" or set(accounts) != set(labels):
        return False, "department_mapping_invalid"
    if any(accounts[key][0] != labels[key] for key in labels):
        return False, "department_mapping_invalid"
    engine = database_engine(settings)
    if engine is None:
        return False, "postgresql_not_configured"
    try:
        with engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": LOCK_ID})
            revisions = tuple(connection.execute(text("SELECT version_num FROM alembic_version FOR SHARE")).scalars())
            if revisions != (REVISION,):
                return False, "revision_mismatch"
            emails = tuple(account[1] for account in accounts.values())
            rows = connection.execute(text("SELECT id, email FROM auth.users WHERE email IN :emails FOR KEY SHARE").bindparams(bindparam("emails", expanding=True)), {"emails": emails}).mappings().all()
            ids_by_email = {str(row["email"]).casefold(): UUID(str(row["id"])) for row in rows}
            if len(ids_by_email) != 35 or any(email.casefold() not in ids_by_email for _, email in accounts.values()):
                return False, "auth_users_missing"
            user_ids = tuple(ids_by_email[email.casefold()] for _, email in accounts.values())
            government_role = connection.execute(select(Role.id).where(Role.id == ROLE_IDS["government"], Role.code == "government", Role.is_active.is_(True))).scalar_one_or_none()
            if government_role is None:
                return False, "government_role_missing"
            organizations: list[dict[str, object]] = []
            profiles: list[dict[str, object]] = []
            assignments: list[dict[str, object]] = []
            bindings: list[dict[str, object]] = []
            for department_id, department_name in labels.items():
                _, email = accounts[department_id]
                user_id = ids_by_email[email.casefold()]
                org_id = _org_id(department_id)
                organizations.append({"id": org_id, "code": _code(department_id), "name": department_name, "organization_type": "government", "region_id": REGION_ID, "parent_id": None, "is_active": True, "is_demo": True})
                profiles.append({"user_id": user_id, "display_name": f"{department_name}办理账号", "region_id": REGION_ID, "organization_id": org_id, "status": "active", "is_demo": True})
                assignments.append({"user_id": user_id, "role_id": government_role, "is_active": True})
                bindings.append({"department_id": department_id, "department_name": department_name, "organization_id": org_id, "government_user_id": user_id, "is_active": True})
            organization_ids = [row["id"] for row in organizations]
            organization_codes = [row["code"] for row in organizations]
            existing_organizations = list(
                connection.execute(
                    select(Organization.__table__).where(
                        Organization.id.in_(organization_ids) | Organization.code.in_(organization_codes)
                    ).with_for_update()
                ).mappings().all()
            )
            existing_profiles = list(
                connection.execute(
                    select(Profile.__table__).where(Profile.user_id.in_(user_ids)).with_for_update()
                ).mappings().all()
            )
            existing_assignments = list(
                connection.execute(
                    select(UserRole.__table__).where(
                        UserRole.user_id.in_(user_ids), UserRole.role_id == government_role
                    ).with_for_update()
                ).mappings().all()
            )
            existing_bindings = list(
                connection.execute(
                    text(
                        "SELECT department_id, department_name, organization_id, government_user_id, is_active "
                        "FROM app.consultation_departments "
                        "WHERE department_id IN :department_ids OR organization_id IN :organization_ids "
                        "OR government_user_id IN :user_ids FOR UPDATE"
                    ).bindparams(
                        bindparam("department_ids", expanding=True),
                        bindparam("organization_ids", expanding=True),
                        bindparam("user_ids", expanding=True),
                    ),
                    {
                        "department_ids": list(labels),
                        "organization_ids": organization_ids,
                        "user_ids": list(user_ids),
                    },
                ).mappings().all()
            )
            all_empty = not any(
                (existing_organizations, existing_profiles, existing_assignments, existing_bindings)
            )
            all_exact = (
                _matches_expected(existing_organizations, organizations, key="id")
                and _matches_expected(existing_profiles, profiles, key="user_id")
                and _matches_expected(existing_assignments, assignments, key="user_id")
                and _matches_expected(existing_bindings, bindings, key="department_id")
            )
            if all_exact:
                return True, "already_applied"
            if not all_empty:
                return False, "binding_conflict"
            connection.execute(insert(Organization.__table__), organizations)
            connection.execute(insert(Profile.__table__), profiles)
            connection.execute(insert(UserRole.__table__), assignments)
            connection.execute(text("INSERT INTO app.consultation_departments (department_id, department_name, organization_id, government_user_id, is_active) VALUES (:department_id, :department_name, :organization_id, :government_user_id, :is_active)"), bindings)
    except Exception:  # noqa: BLE001 - database target and account identifiers stay private.
        return False, "binding_failed"
    return True, "ok"


def main(argv: Sequence[str] | None = None, *, settings: Settings | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if any(argument not in {APPLY, CONFIRM} for argument in arguments):
        print("consultation_departments: invalid_arguments")
        return 2
    if APPLY not in arguments or CONFIRM not in arguments:
        print("consultation_departments: not_requested")
        print("No Auth account, credential, or database change was performed.")
        return 0 if not arguments else 2
    try:
        succeeded, state = bind(settings or Settings())
    except Exception:  # noqa: BLE001 - configuration details stay private.
        succeeded, state = False, "execution_failed"
    result = "applied" if succeeded and state == "ok" else state
    print(f"consultation_departments: {result}")
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
