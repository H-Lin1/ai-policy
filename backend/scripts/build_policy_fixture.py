from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.modules.policy.source import read_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic local policy fixture")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    records, rejected = read_csv(args.source, limit=args.limit)
    if len(records) != args.limit:
        raise SystemExit(f"accepted {len(records)} records, expected {args.limit}: {rejected}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    import uuid

    namespace = uuid.UUID("c4ddc1a9-1f6a-4d0b-b0c1-0f8eaf6b1f20")
    with args.output.open("w", encoding="utf-8") as handle:
        for record in records:
            payload = {
                "id": str(uuid.uuid5(namespace, f"{record.source_url}:{record.content_sha256}")),
                "title": record.title,
                "document_no": record.document_no,
                "issuing_organization": record.issuing_organization,
                "source_url": record.source_url,
                "document_url": record.document_url,
                "published_date": record.published_date.isoformat() if record.published_date else None,
                "collected_at": record.collected_at.isoformat(),
                "content_text": record.content_text,
                "content_sha256": record.content_sha256,
                "region_code": record.region_code,
                "requested_title": record.requested_title,
                "effective_status": record.effective_status,
                "reference_count": record.reference_count,
                "source_years": record.source_years,
            }
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"accepted={len(records)} rejected={sum(rejected.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
