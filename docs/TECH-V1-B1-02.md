# TECH-V1-B1-02 | Policy Library Read-Only Slice

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-02` |
| Version | `V1.3` |
| Status | Accepted and deployed |
| Development step | `B1.2` |
| Product requirement | [`PRD-V1-B1-02`](./PRD-V1-B1-02.md) |
| OpenSpec change | `2026-08-11-establish-policy-library` (archived); `2026-08-11-provision-policy-library-sample` (archived) |
| Feishu | [TECH-V1-B1-02](https://a9ihi0un9c.feishu.cn/docx/Ux4EdPaQboXkeRxYSYqciLIInbh) |
| Prerequisite | `B1.1` and `UI1.0` archived; shared API, feature, IAM, and visual contracts available |
| Database write gate | On 2026-08-11 the user authorized the exact `0003_policy_library` upgrade and deterministic 20-record fixture import; full CSV import remains unauthorized |

## 1. Engineering Goal

Add the first real policy browsing vertical slice while keeping the data boundary small and auditable. The backend owns policy validation, region scope, authorization, pagination, and database reads. The frontend consumes only the versioned API and preserves the existing visual baseline.

## 2. Source and Fixture Boundary

The supplied [`backend/datasets/sz_policy_documents.csv`](../backend/datasets/sz_policy_documents.csv) is treated as an external crawl artifact. It contains 1,578 rows: 726 `success`, 845 `needs_review`, 5 `not_found`, and 2 `no_effective_version`. All successful rows have non-empty content and `.gov.cn` source hosts; four have a mismatched supplied hash and are rejected for review, leaving 722 strict accepted records. B1.2 accepts only `success` rows with non-empty `title`, `source_url`, and `content_text`, and requires `region_code=sz`.

The local fixture contains 20 deterministically selected accepted rows. The original CSV is never modified. The adapter removes NUL control characters from an input field before validation, normalizes line endings only for the stored text, and verifies/derives the content hash from the resulting UTF-8 text. A source URL is canonicalized only for validation; the official URL shown to users remains the source value.

Host validation is scheme- and hostname-based: `https` is required, the hostname must equal `gov.cn` or end with `.gov.cn`, and redirects/document URLs outside the allowlist fail closed. URL strings containing `gov` are not sufficient. The adapter rejects credentials in URLs and private/loopback targets where the crawler boundary can inspect resolved URLs.

## 3. Data Model

One row represents one successfully crawled policy version. The application generates the primary UUID. The immutable identity of an imported version is `(source_url, content_sha256)`; the same source URL with changed content is a new version candidate, while an exact repeat is a no-op.

| Field | Type | Rule |
|---|---|---|
| `id` | UUID | Server-generated primary key |
| `region_id` | UUID FK | References active `app.regions`; B1.2 accepts only code `sz` |
| `title` | text | Non-blank |
| `document_no` | text nullable | Source-preserved |
| `issuing_organization` | text nullable | Source-preserved |
| `source_url` | text | HTTPS `.gov.cn` host |
| `document_url` | text nullable | HTTPS `.gov.cn` host when present |
| `published_date` | date nullable | Source date; no timezone needed for date-only values |
| `collected_at` | timestamptz | Required, UTC in persistence |
| `content_text` | text | Non-blank cleaned full text |
| `content_sha256` | char(64) | Lowercase SHA-256 of `content_text` UTF-8 bytes |
| `effective_status` | text nullable | Source-preserved (`valid`, `invalid`, `unknown`) |
| `requested_title` | text nullable | Crawl provenance only |
| `reference_count` | integer nullable | Non-negative crawl provenance |
| `source_years` | text nullable | Crawl provenance |
| `created_at` / `updated_at` | timestamptz | UTC audit timestamps |

The migration adds one `app.policy_documents` table with restrictive foreign keys, uniqueness on `(source_url, content_sha256)`, non-blank checks, and indexes for `region_id`, `published_date`, and lower-cased title. It does not add browser RLS policies or direct browser grants; FastAPI remains the trusted read boundary, consistent with B1.1.

## 4. Backend Contract

`GET /api/v1/policies` requires the existing current-identity dependency and returns `PageResponse[PolicyListItem]`. It accepts `page`, `page_size`, and an optional bounded `q` title/issuer filter. It returns only active `sz` records and uses `Cache-Control: no-store` because policy visibility is scoped business data.

`GET /api/v1/policies/{policy_id}` requires the same identity and returns `PolicyDetail` with the list fields plus full text, hash, collection date, effective status, and provenance. Unknown IDs return the standard 404 envelope. Both operations declare stable operation IDs, typed success models, and the shared error responses.

No write route is introduced in B1.2. The import adapter is a local, non-mutating validation/preflight command for the 20-record fixture. A future full import must have its own task evidence and explicit authorization.

## 5. Frontend Contract

`PolicyWorkspacePage` remains behind `policy_workspace` and the existing authentication/identity guard. When enabled, it calls the list API, renders a compact list with pagination, and links to a detail route. The detail view can be implemented as a nested route or selected state, but it must preserve the current top navigation and responsive no-overflow baseline. Loading, disabled, empty, 401/403/404, and API failure states are explicit and contain no fake policy content.

## 6. Failure, Security, and Rollback

- Invalid source hosts, failed crawl statuses, blank titles/text, malformed dates, invalid hashes, and duplicate `(source_url, content_sha256)` candidates fail closed with stable local validation reasons.
- API failures expose error codes and request IDs only; no SQL, file system path, database URL, JWT, or key is returned.
- The browser never writes `app.*` tables or uploads source files directly.
- No model, classifier, old code, Embedding, vector store, or RAG path is involved.
- Rollback is code/spec/fixture removal. Applying a downgrade or deleting policy data is outside automatic acceptance.

## 7. Verification Plan

Run source-validation tests for the supplied CSV, migration structure tests without applying the migration, repository/API tests for pagination and IAM denial, frontend render tests for list/detail states, Ruff, frontend build, local smoke, read-only runtime smoke, and OpenSpec strict validation. The final evidence must state that no external migration, import, seed, reset, delete, or Auth mutation ran.

## 8. Acceptance Result

The initial non-mutating B1.2 matrix passed on 2026-08-11: backend `200 passed`, Ruff passed, local smoke `14/14`, runtime checks for database connectivity, target binding, IAM schema, Auth configuration, and JWKS all returned `ok`, frontend tests passed, the production build emitted 91 modules, aggregate acceptance passed `6/6`, and OpenSpec strict validation passed `9/9` before archive.

An isolated browser run used `AUTH_REQUIRED=false`, `ENABLE_POLICY_WORKSPACE=true`, no database URL, and the 20-record fixture. At desktop width `1280`, the first list page rendered 10 records and two-page pagination; the selected detail rendered four metadata fields and 7,628 content characters. The same list and detail passed at `390x844`, with `documentWidth == innerWidth` in both desktop and mobile views. This development bypass was confined to the isolated smoke process and did not change checked-in configuration.

At that initial checkpoint, migration source `0003_policy_library.py` was structurally tested but not applied. The separately authorized deployment and its evidence are recorded below.

## 9. Authorized Deployment Patch

The 2026-08-11 authorization opens only two fixed write operations against the already bound Supabase project: upgrade the configured database from `0002_identity_access` to `0003_policy_library`, then insert the 20 records in `app/modules/policy/fixtures/policies.jsonl`. It does not authorize importing the complete 1,578-row CSV, changing Auth users, enabling the frontend feature flag, updating existing policy rows, or deleting data.

`scripts/init_policy.py` is inspect-only by default. Migration execution requires both `--apply-policy-migration` and `--confirm`; fixture import requires both `--apply-policy-fixture` and `--confirm`. Both paths require the existing Supabase/database target binding to be `ok`. Migration targets the exact revision `0003_policy_library`; import requires that exact revision, one active `sz` region, an exact 20-record fixture, and the expected table/RLS/no-browser-grant invariants.

The import runs in one transaction under a fixed PostgreSQL advisory lock. Deterministic fixture UUIDs and `(source_url, content_sha256)` are both identities. Existing rows must match every source-preserved field and region binding exactly; otherwise the operation fails closed without inserts. Missing records are inserted only, never updated. A second run must insert zero rows and preserve every row value and audit timestamp.

Post-write acceptance reads the revision, policy count, exact fixture projection, RLS state, browser grants, and API list/detail behavior. Normal aggregate acceptance remains non-mutating and never invokes the deployment initializer.

## 10. Deployment Acceptance Result

The authorized deployment completed on 2026-08-11. The database advanced exactly from `0002_identity_access` to `0003_policy_library`; the first fixture import inserted 20 rows, and the second import inserted zero. A full before/after projection of all database columns, including `created_at` and `updated_at`, proved that the repeated import preserved all 20 rows unchanged. The advisory lock had no remaining holder after the transaction.

A real provisioned identity authenticated through Supabase and successfully called `/api/v1/me`, `/api/v1/policies?page=1&page_size=10`, and one policy detail endpoint. The list returned 10 items with total 20; detail returned non-empty full text, a 64-character content hash, and an official `.gov.cn` source. All three responses used `Cache-Control: no-store`. One cold database-backed list request took approximately 30-41 seconds in this local network path; this is recorded as an operational latency risk, not a contract failure, because the response completed correctly and no latency SLO is defined in B1.2.

Final post-write verification passed: backend `208 passed`, Ruff, local smoke `14/14`, all five runtime checks, all frontend tests, 91-module production build, aggregate acceptance `6/6`, pre-archive OpenSpec strict validation `10/10`, and post-archive strict validation `9/9`. No full-CSV import, update, delete, downgrade, reset, Auth mutation, feature-flag change, sensitive-output operation, or legacy source read occurred.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-11 | V1.0 | Defined the read-only policy model, government-source validation, 20-record fixture boundary, API/frontend contracts, and non-mutating import preflight. |
| 2026-08-11 | V1.1 | Recorded implementation and full non-destructive acceptance, including responsive browser evidence and the still-closed migration/import write gates. |
| 2026-08-11 | V1.2 | Opened the separately authorized, exact `0003` plus 20-record insert-or-verify deployment patch while keeping full CSV import and all destructive operations closed. |
| 2026-08-11 | V1.3 | Recorded successful migration, 20-row import, zero-change second import, authenticated database API acceptance, final quality gates, and the observed local-network latency risk. |
