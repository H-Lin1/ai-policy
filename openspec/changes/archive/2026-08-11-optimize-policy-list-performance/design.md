# Design: Policy List Performance Patch

## Decisions

### Reuse one dependency-scoped session

FastAPI caches dependencies per request. IAM and policy repositories will both depend on one optional session provider from `app.core.database`, so an authenticated policy request checks out one pooled connection instead of holding an IAM connection while acquiring another policy connection. The provider yields one session and owns its single close.

Separate per-module sessions were rejected because profiling shows connection acquisition dominates the current Supabase pooler path. A global session was rejected because SQLAlchemy sessions are not safe to share across requests.

### Project only list fields and combine total with the page

The list repository selects the seven list fields plus `count(*) over()` and maps rows into a list-specific record. This avoids loading full policy text and reduces a normal page from two statements to one. An empty page cannot obtain a window total, so it performs one fallback count; this preserves current metadata for out-of-range pages.

Caching was rejected because scoped policy data is explicitly `no-store`, because invalidation would add unnecessary state, and because the measured waste is below the response layer. A migration was rejected because the current 20-row scope is not index-bound and no data/schema write is needed.

## Invariants

- IAM validation completes before policy data is returned.
- A session is never shared across requests and closes exactly once.
- Normal pages execute one projected statement and exclude `content_text`.
- Filter, ordering, total, list response, detail response, errors, and `no-store` remain unchanged.
- Fixture mode remains database-free and deterministic.

## Performance Acceptance

Read-only structural tests prove connection and SQL reductions. Real acceptance authenticates without logging sensitive values, primes `/me`, measures at least three page-one list calls, and requires a maximum of 5 seconds plus median of 2 seconds for warm calls. A cold list must be at most 15 seconds or at least 50% faster than the recorded 30-second lower baseline.
