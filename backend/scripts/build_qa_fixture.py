from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import UUID, uuid5

from app.modules.historical_qa.source import read_csvs

FIXTURE_NAMESPACE = UUID("a1429f7d-7c96-48cd-a6e4-4b8d29d3a546")
DATASETS_ROOT = Path(__file__).resolve().parents[1] / "datasets"
SOURCE_PATHS = (
    DATASETS_ROOT / "2024-2025/sz_gov_qa_2024-2025_cleaned_model_validated_v2_name_adjudicated.csv",
    DATASETS_ROOT / "2025-2026/sz_gov_qa_2025-2026_cleaned_model_validated_v2_name_adjudicated.csv",
    DATASETS_ROOT / "2026至今/sz_gov_qa_2026至今_cleaned_model_validated_v2_name_adjudicated.csv",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic privacy-screened Q&A fixture")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records, rejected = read_csvs(SOURCE_PATHS)
    # Partition by source question year so the deterministic sample covers all
    # three user-provided periods even after privacy exclusions.
    periods = (
        [item for item in records if item.question_at and item.question_at.year <= 2024],
        [item for item in records if item.question_at and item.question_at.year == 2025],
        [item for item in records if item.question_at and item.question_at.year >= 2026],
    )
    selections = (*periods[0][:7], *periods[1][:7], *periods[2][:6])
    if len(selections) != 20 or len({item.content_sha256 for item in selections}) != 20:
        raise SystemExit("fixture selection is not exactly twenty unique records")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Pin LF so the deterministic fixture is byte-identical on Windows and Unix.
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for item in selections:
            payload = {
                "id": str(uuid5(FIXTURE_NAMESPACE, f"{item.source_url}:{item.content_sha256}")),
                "topic": item.topic, "question_text": item.question_text, "answer_text": item.answer_text,
                "source_url": item.source_url, "question_at": item.question_at.isoformat() if item.question_at else None,
                "replied_at": item.replied_at.isoformat() if item.replied_at else None,
                "publishing_organization": item.publishing_organization, "collected_at": item.collected_at.isoformat(),
                "contains_legal_basis": item.contains_legal_basis, "legal_basis_name": item.legal_basis_name,
                "legal_basis_citation": item.legal_basis_citation, "adjudication_result": item.adjudication_result,
                "content_sha256": item.content_sha256, "region_code": item.region_code,
            }
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"accepted={len(records)} rejected={sum(rejected.values())}", file=__import__("sys").stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
