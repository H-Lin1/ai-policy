# TECH-V1-B1-02-P1 | Policy List Performance Patch

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-02-P1` |
| Version | `V1.1` |
| Status | Accepted and archived |
| Development step | `B1.2-P1` |
| Product baseline | [`PRD-V1-B1-02`](./PRD-V1-B1-02.md) V1.2 |
| OpenSpec change | `2026-08-11-optimize-policy-list-performance` (archived) |
| Feishu | [TECH-V1-B1-02-P1](https://a9ihi0un9c.feishu.cn/docx/VEgKdj6sRoFZh2xHK1vcGDEkn2b) |
| Prerequisite | `B1.2-D1` archived with 20 policy rows provisioned |
| Database write gate | Closed; this patch has no migration, data write, Auth mutation, or feature-flag change |

## 1. Problem and Goal

The authenticated policy list was observed at approximately 30-41 seconds on the current local-to-Supabase path. The API contract and returned data were correct, but this latency makes normal browsing unusable. This patch targets the database-backed `GET /api/v1/policies` path without changing pagination, authorization, response fields, error semantics, `Cache-Control: no-store`, or frontend behavior.

The goal is to remove avoidable database connection acquisition and round trips. It is not to hide latency with response caching, weaken identity checks, preload policy data into process memory, or change the database schema.

## 2. Read-Only Baseline

The configured database uses a Supabase pooler and SQLAlchemy `QueuePool` with pre-ping. Safe read-only measurements on 2026-08-11 showed:

| Measurement | Observed |
|---|---:|
| First session checkout and `SELECT 1` after pool disposal | 7,414 ms |
| Second concurrent session checkout and policy count while the first session remained open | 1,728 ms |
| One shared-session checkout | 1,748 ms |
| Projected policy page with window total on the same session | 222 ms |
| Existing authenticated list request | approximately 30-41 s |

The existing request creates separate IAM and policy sessions. IAM keeps its connection checked out until response completion, so the policy dependency may open a second physical connection. The list repository then executes a count query and a second ORM query that loads every column, including full `content_text`, even though the list schema does not expose the text.

## 3. Design

### 3.1 One request-scoped database session

Add one optional request database-session dependency in `app.core.database`. Both IAM and policy repository dependencies consume that same FastAPI dependency, allowing FastAPI dependency caching to provide one `Session` for the request. The session remains read-only by behavior and closes once after the response dependency scope ends.

Development bypass and fixture behavior remain explicit. An unavailable session still maps to the existing identity or policy store error; this change does not introduce a fallback principal or Mock result.

### 3.2 Projected single-query list

The normal non-empty page uses one SQL statement that selects only list fields and adds `count(*) over()` for the filtered total. It excludes `content_text`, hash, collection time, provenance, and audit fields from the list query. Ordering remains `published_date DESC NULLS LAST, title ASC`; filtering remains title-or-issuer case-insensitive matching.

If an offset is beyond the last row, the window query returns no total. Only that empty-page case performs a bounded fallback count so pagination metadata remains compatible. Detail continues to load one complete row.

### 3.3 No cache and no migration

The endpoint keeps `Cache-Control: no-store`; no process, Redis, browser, or CDN cache is added. The existing indexes are adequate for the current 20-row scope, and the dominant measured cost is connection/round-trip overhead, so this patch adds no Alembic revision and performs no Supabase write.

## 4. Verification and Performance Gate

Tests must prove both repositories receive the same request-scoped session, a non-empty list page executes exactly one projected SQL statement, list SQL does not select `content_text`, filtered and empty-page totals remain correct, and detail/API contracts are unchanged.

After local tests, Ruff, frontend tests/build, smoke, runtime smoke, aggregate acceptance, and strict OpenSpec validation pass, run a real authenticated API benchmark on the configured Supabase project. Prime the existing login flow with `/api/v1/me`, then measure at least three page-one list requests. Acceptance requires every measured warm list request at or below 5 seconds and a median at or below 2 seconds on the same network path. The first cold list request must be at or below 15 seconds or improve by at least 50% from the recorded 30-second lower baseline. Record durations only; never output credentials, JWTs, database URLs, keys, account IDs, or policy text.

## 5. Risk and Rollback

- A shared session increases transaction scope across IAM and policy reads. Both paths are read-only, and the session closes after the request; tests cover one close and no cross-request reuse.
- A window count may be more expensive for very large filtered datasets. It removes one network round trip and is appropriate for the current slice; later search work may replace offset pagination under its own OpenSpec.
- Network latency can vary. Structural query/session assertions are deterministic, while runtime thresholds are measured repeatedly and reported with their exact observation context.
- Rollback restores the two repository dependencies and two-query list implementation. No database rollback is necessary.

## 6. Implementation and Acceptance Result

The patch adds `request_db_session`, a FastAPI dependency that creates at most one SQLAlchemy `Session` for a configured request and closes it once at dependency teardown. IAM and policy repository dependencies now consume this shared session. Fixture mode remains database-free, and identity/policy storage failures retain their established fail-closed responses.

For a normal non-empty policy page, the repository now selects only `id`, title, document number, issuing organization, source URL, publication date, effective status, and `count(*) over()`. It does not select full text, content hash, collection time, provenance, or audit fields. A page beyond the result set falls back to one exact count only when the window query has no rows. Detail remains a complete-row read.

Focused tests prove session reuse, one-statement non-empty pages, excluded detail fields, filters, and empty/out-of-range totals. The final matrix passed on 2026-08-11: backend `213 passed`, Ruff, local smoke `14/14`, runtime `5/5`, all frontend tests, 91-module production build, aggregate acceptance `6/6`, pre-archive OpenSpec strict validation `10/10`, and post-archive strict validation `9/9`.

The real authenticated benchmark used the configured Supabase project without outputting account or connection values. A cold page-one list completed in `6,774 ms`; three warm page-one lists completed in `1,822 ms`, `852 ms`, and `1,594 ms` (median `1,594 ms`). Each response returned 10 items with total 20 and `Cache-Control: no-store`. This satisfies the cold threshold of 15 seconds and warm thresholds of 5 seconds maximum / 2 seconds median. No database mutation or cache was introduced.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-11 | V1.0 | Defined the no-migration shared-session and projected single-query policy-list performance patch from read-only baseline evidence. |
| 2026-08-11 | V1.1 | Implemented and accepted shared request session plus projected window-total list query; real cold/warm benchmark met all thresholds without external writes. |
