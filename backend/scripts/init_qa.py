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
from app.modules.historical_qa.models import HistoricalQa
from app.modules.historical_qa.source import SourceValidationError, normalize_source_row
from app.modules.iam.models import Region

APPLY_QA_MIGRATION = "--apply-qa-migration"
APPLY_QA_FIXTURE = "--apply-qa-fixture"
CONFIRM = "--confirm"
PREVIOUS_REVISION = "0003_policy_library"
QA_REVISION = "0004_historical_qa"
QA_IMPORT_LOCK_ID = 11_000_004
FIXTURE_SIZE = 20
FIXTURE_NAMESPACE = UUID("a1429f7d-7c96-48cd-a6e4-4b8d29d3a546")
BACKEND_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = BACKEND_ROOT / "app/modules/historical_qa/fixtures/historical_qa.jsonl"
QA_FIELDS = (
    "id", "region_id", "region_code", "topic", "question_text", "answer_text", "source_url",
    "question_at", "replied_at", "publishing_organization", "collected_at", "contains_legal_basis",
    "legal_basis_name", "legal_basis_citation", "adjudication_result", "content_sha256",
)


@dataclass(frozen=True)
class ImportResult:
    passed: bool
    state: str
    inserted: int = 0


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def database_target_state(settings: Settings) -> str:
    if not settings.normalized_database_url:
        return "not_configured"
    if not settings.normalized_database_url.lower().startswith("postgresql+psycopg://"):
        return "unsupported_database_target"
    state = supabase_target_binding_state(settings)
    return "postgresql_configured" if state == "ok" else state


def _current_revision(settings: Settings) -> tuple[str | None, str]:
    try:
        engine = database_engine(settings)
        if engine is None:
            return None, "not_configured"
        with engine.connect() as connection:
            revisions = tuple(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())
    except Exception:  # noqa: BLE001
        return None, "revision_check_failed"
    return (str(revisions[0]), "ok") if len(revisions) == 1 else (None, "revision_mismatch")


def apply_qa_migration(settings: Settings) -> tuple[bool, str]:
    if supabase_target_binding_state(settings) != "ok":
        return False, "target_not_verified"
    revision, state = _current_revision(settings)
    if state != "ok":
        return False, state
    if revision == QA_REVISION:
        return True, "already_applied"
    if revision != PREVIOUS_REVISION or not settings.normalized_database_url:
        return False, "revision_mismatch"
    environment = os.environ.copy()
    environment["DATABASE_URL"] = settings.normalized_database_url
    environment.pop("ALEMBIC_CONFIG", None)
    try:
        result = subprocess.run([sys.executable, "-m", "alembic", "-c", str(BACKEND_ROOT / "alembic.ini"), "upgrade", QA_REVISION], cwd=BACKEND_ROOT, check=False, capture_output=True, env=environment, text=True, shell=False)
    except Exception:  # noqa: BLE001
        return False, "execution_failed"
    return (True, "applied") if result.returncode == 0 else (False, "migration_failed")


def load_qa_fixture(path: Path = FIXTURE_PATH) -> tuple[tuple[dict[str, object], ...] | None, str]:
    records: list[dict[str, object]] = []
    identities: set[tuple[str, str]] = set()
    ids: set[UUID] = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            normalized = normalize_source_row({
                "留言主题": payload["topic"], "留言内容": payload["question_text"], "答复内容": payload["answer_text"],
                "来源链接": payload["source_url"], "留言时间": payload.get("question_at"), "答复时间": payload.get("replied_at"),
                "发布机构": payload["publishing_organization"], "抓取时间": payload["collected_at"],
                "是否含法律依据": "是" if payload["contains_legal_basis"] else "否", "法律依据名称": payload.get("legal_basis_name"),
                "法律依据完整引文": payload.get("legal_basis_citation"), "模型识别法律依据名称": payload.get("legal_basis_name"),
                "模型识别法律依据完整引文": payload.get("legal_basis_citation"), "分歧仲裁结果": payload["adjudication_result"],
            })
            record_id = UUID(str(payload["id"]))
            identity = (normalized.source_url, normalized.content_sha256)
            if record_id != uuid5(FIXTURE_NAMESPACE, f"{identity[0]}:{identity[1]}") or record_id in ids or identity in identities:
                return None, "fixture_identity_invalid"
            ids.add(record_id); identities.add(identity)
            records.append({
                "id": record_id, "region_code": normalized.region_code, "topic": normalized.topic,
                "question_text": normalized.question_text, "answer_text": normalized.answer_text, "source_url": normalized.source_url,
                "question_at": normalized.question_at, "replied_at": normalized.replied_at,
                "publishing_organization": normalized.publishing_organization, "collected_at": normalized.collected_at,
                "contains_legal_basis": normalized.contains_legal_basis, "legal_basis_name": normalized.legal_basis_name,
                "legal_basis_citation": normalized.legal_basis_citation, "adjudication_result": normalized.adjudication_result,
                "content_sha256": normalized.content_sha256,
            })
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, SourceValidationError):
        return None, "fixture_invalid"
    return (tuple(records), "ok") if len(records) == FIXTURE_SIZE else (None, "fixture_count_mismatch")


def _equal(actual: object, expected: object) -> bool:
    if isinstance(expected, UUID):
        try: return UUID(str(actual)) == expected
        except (ValueError, TypeError): return False
    return actual == expected


def _schema_state(connection) -> str:
    if not bool(connection.execute(text("SELECT to_regclass('app.historical_qa') IS NOT NULL")).scalar_one()): return "qa_table_missing"
    if not bool(connection.execute(text("SELECT c.relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='app' AND c.relname='historical_qa'")).scalar_one()): return "qa_rls_mismatch"
    if int(connection.execute(text("SELECT count(*) FROM pg_policies WHERE schemaname='app' AND tablename='historical_qa'")).scalar_one()): return "qa_browser_policy_mismatch"
    if int(connection.execute(text("SELECT count(*) FROM information_schema.table_privileges WHERE table_schema='app' AND table_name='historical_qa' AND grantee IN ('anon','authenticated')")).scalar_one()): return "qa_browser_grant_mismatch"
    return "ok"


def _import_plan(connection, fixture: Sequence[Mapping[str, object]]) -> tuple[str, tuple[dict[str, object], ...] | None]:
    if tuple(connection.execute(text("SELECT version_num FROM alembic_version FOR SHARE")).scalars()) != (QA_REVISION,): return "revision_mismatch", None
    state = _schema_state(connection)
    if state != "ok": return state, None
    regions = tuple(connection.execute(select(Region.__table__).where(Region.__table__.c.code == "sz", Region.__table__.c.is_active.is_(True)).with_for_update()).mappings().all())
    if len(regions) != 1: return "region_mismatch", None
    expected = tuple({**record, "region_id": UUID(str(regions[0]["id"]))} for record in fixture)
    ids, keys = tuple(record["id"] for record in expected), tuple((record["source_url"], record["content_sha256"]) for record in expected)
    existing = tuple(connection.execute(select(HistoricalQa.__table__).where(or_(HistoricalQa.__table__.c.id.in_(ids), tuple_(HistoricalQa.__table__.c.source_url, HistoricalQa.__table__.c.content_sha256).in_(keys))).with_for_update()).mappings().all())
    matched: set[int] = set()
    for row in existing:
        candidates = [index for index, record in enumerate(expected) if _equal(row.get("id"), record["id"]) or (row.get("source_url") == record["source_url"] and row.get("content_sha256") == record["content_sha256"])]
        if len(candidates) != 1 or candidates[0] in matched or any(not _equal(row.get(field), expected[candidates[0]][field]) for field in QA_FIELDS): return "fixture_conflict", None
        matched.add(candidates[0])
    return "ok", tuple(record for index, record in enumerate(expected) if index not in matched)


def apply_qa_fixture(settings: Settings, fixture: Sequence[Mapping[str, object]]) -> ImportResult:
    if supabase_target_binding_state(settings) != "ok": return ImportResult(False, "target_not_verified")
    try: engine = database_engine(settings)
    except Exception: return ImportResult(False, "configuration_invalid")  # noqa: BLE001
    if engine is None: return ImportResult(False, "not_configured")
    phase = "check"
    try:
        with engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": QA_IMPORT_LOCK_ID})
            state, missing = _import_plan(connection, fixture)
            if state != "ok" or missing is None: return ImportResult(False, state)
            phase = "write"
            if missing: connection.execute(insert(HistoricalQa.__table__), list(missing))
    except Exception: return ImportResult(False, "check_failed" if phase == "check" else "write_failed")  # noqa: BLE001
    return ImportResult(True, "ok", len(missing))


def main(argv: Sequence[str] | None = None, *, settings: Settings | None = None) -> int:
    arguments = _arguments(argv); allowed = {APPLY_QA_MIGRATION, APPLY_QA_FIXTURE, CONFIRM}
    if any(item not in allowed for item in arguments): print("qa_provision: invalid_arguments"); return 2
    operations = [item for item in (APPLY_QA_MIGRATION, APPLY_QA_FIXTURE) if item in arguments]
    try: runtime = settings or Settings(); target = database_target_state(runtime)
    except Exception: print("qa_provision: configuration_invalid"); return 2  # noqa: BLE001
    if not operations and CONFIRM not in arguments: print(f"qa_provision: not_requested ({target})"); print("No migration, Q&A import, update, or delete was performed."); return 0
    if len(operations) != 1: print("qa_provision: one_operation_required"); return 2
    if CONFIRM not in arguments: print("qa_provision: confirmation_required"); return 2
    if target != "postgresql_configured": print(f"qa_provision: {target}"); return 2
    if operations[0] == APPLY_QA_MIGRATION:
        passed, state = apply_qa_migration(runtime); print(f"qa_migration: {state}"); return 0 if passed else 1
    fixture, state = load_qa_fixture()
    if fixture is None: print(f"qa_fixture: {state}"); return 2
    result = apply_qa_fixture(runtime, fixture)
    print(f"qa_fixture: applied (inserted={result.inserted}, expected={FIXTURE_SIZE})" if result.passed else f"qa_fixture: {result.state}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
