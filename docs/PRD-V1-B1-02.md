# PRD-V1-B1-02 | 政策库只读闭环

## 0. Basic Information

| Field | Value |
|---|---|
| PRD ID / feature | `PRD-V1-B1-02` / Policy library read-only slice |
| Baseline step | `B1.2` 政策库 |
| Version / status | `V1.2` / Accepted and provisioned |
| Priority | P0 |
| Confirmed date | 2026-08-11 |
| Prerequisite | `UI1.0` and `B1.1` archived; existing Supabase/JWT and IAM scope available |
| Source sample | `/Users/hlin/Documents/ai policy/backend/datasets/sz_policy_documents.csv`; 1,578 rows, 726 successful government-source records, 722 passing strict hash validation |
| Technical plan | [`TECH-V1-B1-02`](./TECH-V1-B1-02.md) |
| OpenSpec change | `2026-08-11-establish-policy-library`; `2026-08-11-provision-policy-library-sample` |
| Feishu | [PRD-V1-B1-02](https://a9ihi0un9c.feishu.cn/docx/K1szdybv8oCKC0x2CfMciBfrneb) |

**Delivery:** A provisioned Shenzhen user can browse 20 verified policy records and open the full cleaned text sourced from government websites. The first slice is read-only and the same reproducible 20-record fixture has been imported into Supabase under separate authorization; the full CSV remains outside the application database.

## 1. Background and User Need

The current `/policies` route only verifies the `policy_workspace` feature flag and does not render business data. The supplied crawl output contains policy titles, source metadata, cleaned text, hashes, and crawl status from public government domains. B1.2 turns the successful subset into the first real policy browsing path without mixing in classification, search/RAG, historical Q&A, or consultation behavior.

Users need to scan policy titles and issuing organizations, understand publication dates, open an individual policy, and verify the official source. The system must not show failed or unreviewed crawl rows as published policy content.

## 2. Goals, Scope, and Non-Goals

**Goals:**

- store one successful crawled policy version as one immutable read model;
- expose a paginated `/api/v1/policies` list and `/api/v1/policies/{id}` detail contract;
- preserve the official source page, optional document URL, publication date, collection time, content hash, and cleaned full text;
- restrict records to the existing active Shenzhen region and authorized identities;
- render a usable policy list/detail flow in the existing visual baseline;
- provide a deterministic 20-record local fixture and a non-mutating CSV preflight/validation path.

| Scope | Content |
|---|---|
| Included | Policy table migration and authorized execution; gov.cn host validation; deterministic 20-record insert-or-verify import; list/detail API; IAM-protected read access; feature-guarded frontend list/detail views; fixture and regression tests |
| Excluded | Full 1,578-row database import; policy updates/deletes; policy editing or review workflow; attachments upload/storage; category/tag administration; status/version adjudication beyond source fields; full-text search ranking; OCR; Embedding/RAG; policy recommendation; old project code or data |

## 3. User Experience Requirements

### 3.1 Policy list

- An authorized user opening `/policies` sees a page title, total count, policy cards or rows, and pagination controls.
- Each list item shows title, issuing organization when present, publication date when present, and an official-source action.
- Empty, loading, feature-disabled, signed-out, denied, and service-error states use the existing shared visual system and never show fake policy data.
- The list uses the established `page`/`page_size` and `{items, meta}` API contract.

### 3.2 Policy detail

- Opening a policy shows title, document number when present, issuing organization, publication date, collection date, official source link, and cleaned full text.
- A missing or inaccessible record renders a standard 404/error state without exposing SQL, file paths, or internal exceptions.
- Full text preserves paragraphs, headings, numbered provisions, and meaningful whitespace; it is not silently truncated.

### 3.3 Authorization and source trust

- The backend requires a valid application identity with active `sz` scope; the browser never queries `app.*` directly.
- B1.2 is read-only for all four existing roles. No role can edit, delete, approve, or import through the UI.
- Only records whose source URL hostname is `gov.cn` or ends with `.gov.cn` and whose crawl status is `success` are eligible for the fixture/import adapter.
- Failed, missing, or `needs_review` crawl rows remain outside the published read model.

## 4. Data Contract

The supplied CSV is an intake source, not the database schema. The adapter reads these source columns: `title`, `document_no`, `issuing_organization`, `source_url`, `document_url`, `published_date`, `collected_at`, `content_text`, `content_sha256`, `region_code`, `crawl_status`, `effective_status`, `requested_title`, `reference_count`, and `source_years`. Four successful rows have a source hash that does not match the normalized content and remain rejected for review; they are not silently rewritten.

The policy read model requires: title, source URL, collection time, cleaned full text, content hash, and active Shenzhen scope. Document number, issuing organization, document URL, publication date, effective status, and source provenance remain nullable or source-preserved when missing. The server generates its own UUID; no database UUID is supplied by the crawl file.

Dates without a time use `YYYY-MM-DD`. API datetimes are timezone-aware and serialize as UTC RFC 3339 values ending in `Z`.

## 5. Acceptance Criteria

| ID | Given | When | Then |
|---|---|---|---|
| AC-B12-01 | The supplied crawl CSV is read | The adapter validates a deterministic sample | Exactly 20 successful records with non-empty text and `.gov.cn` source hosts are accepted; failed/review rows are rejected with stable reasons |
| AC-B12-02 | An authorized active Shenzhen identity exists | User requests `/api/v1/policies` | API returns `{items, meta}` with the shared pagination contract and no-store headers |
| AC-B12-03 | A valid policy ID is requested | User requests `/api/v1/policies/{id}` | API returns metadata, official source, hash, and complete cleaned text |
| AC-B12-04 | A signed-out, wrong-scope, or unavailable identity requests policy data | Request is processed | Backend returns the existing 401/403/503 error envelope; no policy content is mounted |
| AC-B12-05 | The frontend policy route is enabled | User opens `/policies` and a detail link | List, empty, error, pagination, and detail states render without horizontal overflow or fabricated controls |
| AC-B12-06 | The authorized 20-record import has completed once | The same fixture import is repeated | It inserts zero rows and preserves every stored field and audit timestamp |
| AC-B12-07 | Repository acceptance is run | Tests, Ruff, frontend build, smoke, runtime smoke, and OpenSpec strict validation execute | All checks pass; no unapproved full import, update, delete, downgrade, Auth mutation, or sensitive output occurs |

## 6. Constraints and Rollback

- Public `.gov.cn` pages and the supplied crawl output are data references only; no legacy project source, routes, payloads, or crawler code is imported.
- The fixture is the deterministic import set for the 20 provisioned sample records and is not a claim that the full CSV has been imported into Supabase.
- The separate authorization covered only migration `0003_policy_library` and the exact 20-record fixture. It did not authorize the full CSV, updates, deletes, downgrade, Auth writes, or feature-flag changes.
- Rollback removes the B1.2 application files, fixture, migration source, and OpenSpec change; no runtime database rollback is executed automatically.

## 7. Acceptance Evidence

B1.2 passed the initial non-destructive acceptance matrix on 2026-08-11: 200 backend tests, Ruff, local smoke `14/14`, read-only runtime smoke, frontend tests, a 91-module production build, aggregate acceptance `6/6`, and OpenSpec strict validation `9/9`. Browser smoke used an isolated fixture backend and verified the policy list, pagination, detail metadata, official links, and complete policy text at desktop `1280` and mobile `390x844`; both viewports had `documentWidth == innerWidth`.

The separately authorized deployment then applied exactly `0003_policy_library`, inserted the 20 deterministic fixture records, and repeated the import with zero inserts and complete row/timestamp invariance. A real provisioned identity received a 10-of-20 policy page and a complete policy detail from the database-backed API with `no-store`. Final verification passed 208 backend tests, Ruff, local and runtime smoke, all frontend tests, the 91-module build, aggregate acceptance `6/6`, and pre-archive strict validation `10/10`. The original 1,578-row CSV was not modified or imported; no update, delete, downgrade, reset, Auth mutation, or feature-flag change occurred.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-11 | V1.0 | Defined the minimal read-only policy library slice around 20 verified `.gov.cn` records from the supplied crawl output, with no database import authorization. |
| 2026-08-11 | V1.1 | Accepted the implemented list/detail slice after full local, runtime, browser, and OpenSpec verification; recorded that migration and database import remain unexecuted. |
| 2026-08-11 | V1.2 | Recorded the separately authorized `0003` migration, exact 20-record import, zero-change repeated import, and authenticated database-backed acceptance. |
