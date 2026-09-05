from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import insert, or_, select, text, tuple_

from app.core.config import Settings
from app.core.database import database_engine
from app.core.supabase_target import supabase_target_binding_state
from app.modules.iam.models import Region
from app.modules.policy.models import PolicyDocument
from app.modules.policy.source import SourceValidationError, normalize_source_row

APPLY_POLICY_MIGRATION = "--apply-policy-migration"
APPLY_POLICY_FIXTURE = "--apply-policy-fixture"
CONFIRM = "--confirm"
PREVIOUS_REVISION = "0002_identity_access"
POLICY_REVISION = "0003_policy_library"
CURRENT_REVISION = "0005_consultation_workflow"
POLICY_IMPORT_LOCK_ID = 11_000_003
FIXTURE_SIZE = 20
FIXTURE_NAMESPACE = UUID("c4ddc1a9-1f6a-4d0b-b0c1-0f8eaf6b1f20")
BACKEND_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = BACKEND_ROOT / "app/modules/policy/fixtures/policies.jsonl"

POLICY_FIELDS = (
    "id",
    "region_id",
    "region_code",
    "title",
    "document_no",
    "issuing_organization",
    "source_url",
    "document_url",
    "published_date",
    "collected_at",
    "content_text",
    "content_sha256",
    "effective_status",
    "requested_title",
    "reference_count",
    "source_years",
)


@dataclass(frozen=True)
class ImportResult:
    passed: bool
    state: str
    inserted: int = 0


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def database_target_state(settings: Settings) -> str:
    database_url = settings.normalized_database_url
    if not database_url:
        return "not_configured"
    if not database_url.lower().startswith("postgresql+psycopg://"):
        return "unsupported_database_target"
    if settings.database_mode == "standalone":
        return "postgresql_configured"
    binding_state = supabase_target_binding_state(settings)
    return "postgresql_configured" if binding_state == "ok" else binding_state


def migration_environment(database_url: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    environment.pop("ALEMBIC_CONFIG", None)
    return environment


def _current_revision(settings: Settings) -> tuple[str | None, str]:
    try:
        engine = database_engine(settings)
        if engine is None:
            return None, "not_configured"
        with engine.connect() as connection:
            revisions = tuple(
                connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
            )
    except Exception:  # noqa: BLE001 - database failures can expose connection details.
        return None, "revision_check_failed"
    if len(revisions) != 1:
        return None, "revision_mismatch"
    return str(revisions[0]), "ok"


def apply_policy_migration(settings: Settings) -> tuple[bool, str]:
    if settings.database_mode != "standalone" and supabase_target_binding_state(settings) != "ok":
        return False, "target_not_verified"
    revision, state = _current_revision(settings)
    if state != "ok":
        return False, state
    if revision == POLICY_REVISION:
        return True, "already_applied"
    if revision != PREVIOUS_REVISION:
        return False, "revision_mismatch"
    database_url = settings.normalized_database_url
    if not isinstance(database_url, str):
        return False, "configuration_invalid"
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "-c",
                str(BACKEND_ROOT / "alembic.ini"),
                "upgrade",
                POLICY_REVISION,
            ],
            cwd=BACKEND_ROOT,
            check=False,
            capture_output=True,
            env=migration_environment(database_url),
            text=True,
            shell=False,
        )
    except Exception:  # noqa: BLE001 - child output and environment stay private.
        return False, "execution_failed"
    return (True, "applied") if result.returncode == 0 else (False, "migration_failed")


def load_policy_fixture(path: Path = FIXTURE_PATH) -> tuple[tuple[dict[str, object], ...] | None, str]:
    records: list[dict[str, object]] = []
    ids: set[UUID] = set()
    identities: set[tuple[str, str]] = set()
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                normalized = normalize_source_row({**payload, "crawl_status": "success"})
                record_id = UUID(str(payload["id"]))
                expected_id = uuid5(
                    FIXTURE_NAMESPACE,
                    f"{normalized.source_url}:{normalized.content_sha256}",
                )
                identity = (normalized.source_url, normalized.content_sha256)
                if record_id != expected_id or record_id in ids or identity in identities:
                    return None, "fixture_identity_invalid"
                ids.add(record_id)
                identities.add(identity)
                records.append(
                    {
                        "id": record_id,
                        "region_code": normalized.region_code,
                        "title": normalized.title,
                        "document_no": normalized.document_no,
                        "issuing_organization": normalized.issuing_organization,
                        "source_url": normalized.source_url,
                        "document_url": normalized.document_url,
                        "published_date": normalized.published_date,
                        "collected_at": normalized.collected_at,
                        "content_text": normalized.content_text,
                        "content_sha256": normalized.content_sha256,
                        "effective_status": normalized.effective_status,
                        "requested_title": normalized.requested_title,
                        "reference_count": normalized.reference_count,
                        "source_years": normalized.source_years,
                    }
                )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, SourceValidationError):
        return None, "fixture_invalid"
    if len(records) != FIXTURE_SIZE:
        return None, "fixture_count_mismatch"
    return tuple(records), "ok"


def _values_equal(actual: object, expected: object) -> bool:
    if isinstance(expected, UUID):
        try:
            return UUID(str(actual)) == expected
        except (TypeError, ValueError):
            return False
    return actual == expected


def _schema_state(connection) -> str:
    table_exists = bool(
        connection.execute(
            text("SELECT to_regclass('app.policy_documents') IS NOT NULL")
        ).scalar_one()
    )
    if not table_exists:
        return "policy_table_missing"
    rls_enabled = bool(
        connection.execute(
            text(
                "SELECT c.relrowsecurity FROM pg_class AS c "
                "JOIN pg_namespace AS n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'app' AND c.relname = 'policy_documents'"
            )
        ).scalar_one()
    )
    if not rls_enabled:
        return "policy_rls_mismatch"
    policy_count = int(
        connection.execute(
            text(
                "SELECT count(*) FROM pg_policies "
                "WHERE schemaname = 'app' AND tablename = 'policy_documents'"
            )
        ).scalar_one()
    )
    if policy_count:
        return "policy_browser_policy_mismatch"
    browser_grants = int(
        connection.execute(
            text(
                "SELECT count(*) FROM information_schema.table_privileges "
                "WHERE table_schema = 'app' AND table_name = 'policy_documents' "
                "AND grantee IN ('anon', 'authenticated')"
            )
        ).scalar_one()
    )
    return "policy_browser_grant_mismatch" if browser_grants else "ok"


def _import_plan(
    connection,
    fixture: Sequence[Mapping[str, object]],
) -> tuple[str, tuple[dict[str, object], ...] | None]:
    revisions = tuple(
        connection.execute(text("SELECT version_num FROM alembic_version FOR SHARE")).scalars()
    )
    allowed_revisions = (
        (POLICY_REVISION, CURRENT_REVISION)
        if os.getenv("DATABASE_MODE", "supabase").strip().lower() == "standalone"
        else (POLICY_REVISION,)
    )
    if revisions not in ((revision,) for revision in allowed_revisions):
        return "revision_mismatch", None
    schema_state = _schema_state(connection)
    if schema_state != "ok":
        return schema_state, None
    regions = tuple(
        connection.execute(
            select(Region.__table__).where(
                Region.__table__.c.code == "sz",
                Region.__table__.c.is_active.is_(True),
            ).with_for_update()
        ).mappings().all()
    )
    if len(regions) != 1:
        return "region_mismatch", None
    region_id = UUID(str(regions[0]["id"]))
    expected = tuple({**record, "region_id": region_id} for record in fixture)
    expected_ids = tuple(record["id"] for record in expected)
    expected_keys = tuple(
        (record["source_url"], record["content_sha256"]) for record in expected
    )
    existing = tuple(
        connection.execute(
            select(PolicyDocument.__table__).where(
                or_(
                    PolicyDocument.__table__.c.id.in_(expected_ids),
                    tuple_(
                        PolicyDocument.__table__.c.source_url,
                        PolicyDocument.__table__.c.content_sha256,
                    ).in_(expected_keys),
                )
            ).with_for_update()
        ).mappings().all()
    )
    matched: set[int] = set()
    for row in existing:
        candidates = [
            index
            for index, record in enumerate(expected)
            if _values_equal(row.get("id"), record["id"])
            or (
                row.get("source_url") == record["source_url"]
                and row.get("content_sha256") == record["content_sha256"]
            )
        ]
        if len(candidates) != 1 or candidates[0] in matched:
            return "fixture_conflict", None
        index = candidates[0]
        if any(
            not _values_equal(row.get(field), expected[index][field])
            for field in POLICY_FIELDS
        ):
            return "fixture_conflict", None
        matched.add(index)
    return "ok", tuple(record for index, record in enumerate(expected) if index not in matched)


def apply_policy_fixture(
    settings: Settings,
    fixture: Sequence[Mapping[str, object]],
) -> ImportResult:
    if settings.database_mode != "standalone" and supabase_target_binding_state(settings) != "ok":
        return ImportResult(False, "target_not_verified")
    try:
        engine = database_engine(settings)
    except Exception:  # noqa: BLE001 - configuration values stay private.
        return ImportResult(False, "configuration_invalid")
    if engine is None:
        return ImportResult(False, "not_configured")
    phase = "check"
    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_id)"),
                {"lock_id": POLICY_IMPORT_LOCK_ID},
            )
            state, missing = _import_plan(connection, fixture)
            if state != "ok" or missing is None:
                return ImportResult(False, state)
            phase = "write"
            if missing:
                connection.execute(insert(PolicyDocument.__table__), list(missing))
    except Exception:  # noqa: BLE001 - database errors can expose data or target details.
        return ImportResult(False, "check_failed" if phase == "check" else "write_failed")
    return ImportResult(True, "ok", inserted=len(missing))


def main(argv: Sequence[str] | None = None, *, settings: Settings | None = None) -> int:
    arguments = _arguments(argv)
    allowed = {APPLY_POLICY_MIGRATION, APPLY_POLICY_FIXTURE, CONFIRM}
    if any(argument not in allowed for argument in arguments):
        print("policy_provision: invalid_arguments")
        return 2
    operations = [
        flag for flag in (APPLY_POLICY_MIGRATION, APPLY_POLICY_FIXTURE) if flag in arguments
    ]
    try:
        runtime_settings = settings or Settings()
        target_state = database_target_state(runtime_settings)
    except Exception:  # noqa: BLE001 - validation errors can echo configuration values.
        print("policy_provision: configuration_invalid")
        return 2
    if not operations and CONFIRM not in arguments:
        print(f"policy_provision: not_requested ({target_state})")
        print("No migration, policy import, update, or delete was performed.")
        return 0
    if len(operations) != 1:
        print("policy_provision: one_operation_required")
        return 2
    if CONFIRM not in arguments:
        print("policy_provision: confirmation_required")
        return 2
    if target_state != "postgresql_configured":
        print(f"policy_provision: {target_state}")
        return 2
    if operations[0] == APPLY_POLICY_MIGRATION:
        passed, state = apply_policy_migration(runtime_settings)
        print(f"policy_migration: {state}")
        return 0 if passed else 1
    fixture, state = load_policy_fixture()
    if fixture is None:
        print(f"policy_fixture: {state}")
        return 2
    result = apply_policy_fixture(runtime_settings, fixture)
    if result.passed:
        print(f"policy_fixture: applied (inserted={result.inserted}, expected={FIXTURE_SIZE})")
        return 0
    print(f"policy_fixture: {result.state}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
