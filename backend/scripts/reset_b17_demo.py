from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import bindparam, text

from app.core.config import Settings
from app.core.database import database_engine
from app.core.supabase_target import supabase_target_binding_state

APPLY = "--apply-b1-7-reset"
CONFIRM = "--confirm"
MARKER = "B17演示验收:"


@dataclass(frozen=True)
class ResetCounts:
    consultations: int
    events: int
    public_projections: int


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(sys.argv[1:] if argv is None else argv)


def _candidate_rows(connection):
    pattern = f"{MARKER}%"
    return connection.execute(
        text(
            "SELECT c.id::text AS consultation_id, c.status, c.historical_qa_id::text AS historical_qa_id, "
            "h.source_url, h.id::text AS projection_id "
            "FROM app.consultations AS c "
            "LEFT JOIN app.historical_qa AS h ON h.id = c.historical_qa_id "
            "WHERE c.question_text LIKE :pattern "
            "OR c.public_question_text LIKE :pattern "
            "OR c.public_answer_text LIKE :pattern "
            "FOR UPDATE OF c"
        ),
        {"pattern": pattern},
    ).mappings().all()


def _validate_candidates(rows) -> None:
    for row in rows:
        if row["status"] != "closed":
            raise RuntimeError("marked_consultation_not_closed")
        projection_id = row["projection_id"]
        if projection_id is not None and row["source_url"] != f"consultation://public/{row['consultation_id']}":
            raise RuntimeError("marked_projection_not_owned")


def reset(*, settings: Settings, apply: bool) -> tuple[bool, str, ResetCounts]:
    if supabase_target_binding_state(settings) != "ok":
        return False, "target_not_verified", ResetCounts(0, 0, 0)
    engine = database_engine(settings)
    if engine is None:
        return False, "database_not_configured", ResetCounts(0, 0, 0)
    try:
        with engine.begin() as connection:
            rows = _candidate_rows(connection)
            _validate_candidates(rows)
            if not apply:
                return True, "ready" if rows else "already_clean", ResetCounts(len(rows), 0, sum(row["projection_id"] is not None for row in rows))
            # Delete events in a separate statement so the exact count is retained.
            ids = [UUID(row["consultation_id"]) for row in rows]
            events_statement = text("DELETE FROM app.consultation_events WHERE consultation_id IN :ids").bindparams(bindparam("ids", expanding=True))
            consultations_statement = text("DELETE FROM app.consultations WHERE id IN :ids RETURNING id").bindparams(bindparam("ids", expanding=True))
            events = connection.execute(events_statement, {"ids": ids}).rowcount if ids else 0
            deleted_consultations = connection.execute(consultations_statement, {"ids": ids}).rowcount if ids else 0
            projection_ids = [UUID(row["projection_id"]) for row in rows if row["projection_id"] is not None]
            projections_statement = text("DELETE FROM app.historical_qa WHERE id IN :ids RETURNING id").bindparams(bindparam("ids", expanding=True))
            deleted_projections = connection.execute(projections_statement, {"ids": projection_ids}).rowcount if projection_ids else 0
            return True, "applied", ResetCounts(deleted_consultations, events, deleted_projections)
    except RuntimeError as exc:
        return False, str(exc), ResetCounts(0, 0, 0)
    except Exception:  # noqa: BLE001 - reset failures must not expose DSNs or private data.
        return False, "reset_failed", ResetCounts(0, 0, 0)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _arguments(argv)
    if any(argument not in {APPLY, CONFIRM} for argument in arguments) or (CONFIRM in arguments and APPLY not in arguments):
        print("b1_7_reset: invalid_arguments")
        return 2
    requested = APPLY in arguments and CONFIRM in arguments
    try:
        succeeded, state, counts = reset(settings=Settings(), apply=requested)
    except Exception:  # noqa: BLE001 - configuration errors are reported as a stable state.
        succeeded, state, counts = False, "configuration_invalid", ResetCounts(0, 0, 0)
    print(f"b1_7_reset: {state}")
    print(f"counts: consultations={counts.consultations}, events={counts.events}, public_projections={counts.public_projections}")
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
