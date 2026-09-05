"""Copy public policy and historical-Q&A content into a standalone database.

This deliberately excludes Supabase Auth users, credentials, sessions, and
consultation records.  Those require a separately approved identity/foreign-key
mapping plan rather than a blind database copy.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence

from sqlalchemy import create_engine, insert, select, text

from app.modules.historical_qa.models import HistoricalQa
from app.modules.policy.models import PolicyDocument

APPLY = "--apply"
CONFIRM = "--confirm"
SOURCE_ENV = "SUPABASE_SOURCE_DATABASE_URL"
TARGET_ENV = "STANDALONE_TARGET_DATABASE_URL"
TABLES = ("policy_documents", "historical_qa")


def _url(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _counts(connection, schema: str) -> dict[str, int]:
    return {
        table: int(connection.execute(text(f"SELECT count(*) FROM {schema}.{table}")).scalar_one())
        for table in TABLES
    }


def _records(connection, table) -> list[dict[str, object]]:
    return [dict(row) for row in connection.execute(select(table)).mappings().all()]


def _identity_key(record: dict[str, object]) -> tuple[str, str]:
    return str(record["source_url"]), str(record["content_sha256"])


def _insert_missing(target, model, source_records: list[dict[str, object]]) -> int:
    existing = {
        _identity_key(dict(row))
        for row in target.execute(select(model.__table__)).mappings().all()
    }
    missing = [record for record in source_records if _identity_key(record) not in existing]
    if missing:
        target.execute(insert(model.__table__), missing)
    return len(missing)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if set(arguments) - {APPLY, CONFIRM} or (APPLY in arguments and CONFIRM not in arguments):
        print("supabase_content_migration: confirmation_required")
        return 2
    source_url = _url(SOURCE_ENV)
    target_url = _url(TARGET_ENV)
    if not source_url or not target_url:
        print("supabase_content_migration: source_and_target_required")
        return 2
    try:
        source_engine = create_engine(source_url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
        target_engine = create_engine(target_url, pool_pre_ping=True)
        with source_engine.connect() as source, target_engine.begin() as target:
            source_counts = _counts(source, "app")
            target_counts = _counts(target, "app")
            print({"source_counts": source_counts, "target_counts": target_counts})
            if APPLY not in arguments:
                print("supabase_content_migration: dry_run")
                return 0
            policies = _records(source, PolicyDocument.__table__)
            historical_qa = _records(source, HistoricalQa.__table__)
            inserted = {
                "policy_documents": _insert_missing(target, PolicyDocument, policies),
                "historical_qa": _insert_missing(target, HistoricalQa, historical_qa),
            }
            print({"status": "applied", "inserted": inserted})
            return 0
    except Exception:
        print("supabase_content_migration: failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
