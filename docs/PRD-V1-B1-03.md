# PRD-V1-B1-03 | 历史政务问答只读闭环

## 0. Basic Information

| Field | Value |
|---|---|
| PRD ID / feature | `PRD-V1-B1-03` / Historical government Q&A read-only slice |
| Baseline step | `B1.3` 历史问答 |
| Version / status | `V1.2` / Accepted |
| Priority | P0 |
| Confirmed date | 2026-08-11 |
| Prerequisite | `B1.1`, `UI1.0`, `B1.2`, and `B1.2-P1` archived |
| Source | Three Shenzhen government Q&A adjudicated CSVs; 1,650 rows, 1,589 unique question/answer pairs, all `www.sz.gov.cn` |
| Technical plan | [`TECH-V1-B1-03`](./TECH-V1-B1-03.md) |
| OpenSpec change | `2026-08-11-establish-historical-qa` |

**Delivery:** An authorized active Shenzhen identity can browse a small, deterministic and privacy-screened sample of historical government Q&A and open a complete question/answer record with public source and legal-basis provenance where present. The first slice is read-only; no conversational generation, similarity retrieval, RAG, classification, user-submitted question, or full dataset import is included.

## 1. Goals and Scope

- preserve a public source URL, topic, question text, government answer, published/replied dates, publisher, collection time, and optional legal-basis metadata;
- publish only source records that pass schema, text, official-host, duplicate, and sensitive-pattern validation;
- expose paginated list/detail APIs behind the existing IAM and Shenzhen scope;
- provide deterministic fixture and import boundaries suitable for later B1.5 retrieval work, without implementing retrieval now.

| Scope | Content |
|---|---|
| Included | `0004_historical_qa` migration source; deterministic 20-record privacy-screened fixture; local adapter; database list/detail API; guarded responsive frontend view; tests and explicit operational initializer |
| Excluded | Full 1,650-row import; nicknames, receipt/case IDs, user profile data, model prompts/outputs, model-generated answer, semantic search, embedding/RAG, policy linking claims, editing/approval/import UI, attachments, Auth writes, legacy source code |

## 2. User Experience and Authorization

- `/qa` presents total count, topic, publisher, reply date, and official source; it supports the existing one-based pagination and explicit loading/empty/error/denied states.
- `/qa/{id}` shows the complete source-preserved question/answer, dates, publisher, source, and optional legal-basis name/citation.
- The browser never reads or writes `app.*` tables directly. All four active B1.1 roles can read the Shenzhen sample; none can edit, delete, approve, or import it through the UI.
- API responses use the shared envelope/request ID behavior and `Cache-Control: no-store`.

## 3. Data and Privacy Contract

The source CSVs have Chinese column names. The adapter reads only public-safe fields: topic (`留言主题`), question (`留言内容`), question/reply times, publisher (`发布机构`), answer (`答复内容`), source URL (`来源链接`), collection time, and legal-basis/adjudication metadata. It never persists `数据ID`, `受理编号`, `昵称`, or free-text adjudication rationale.

The adapter requires non-empty topic/question/answer/source, HTTPS `gov.cn` host, parseable timezone-aware collection time, valid date/times, and a deterministic hash over normalized question/answer/source. It strips NULs and normalizes line endings. Duplicate normalized question/answer/source identities are rejected. Phone numbers, email addresses, Chinese resident-ID patterns, bank-card-like digit runs, and explicit contact-label patterns cause rejection. This is a conservative automated screen, not a claim that public text has no residual personal information.

## 4. Acceptance Criteria

| ID | Given | When | Then |
|---|---|---|---|
| AC-B13-01 | The three final adjudicated CSVs | Adapter audit and fixture selection run | Source counts and schema are recorded; exactly 20 valid, deduplicated, privacy-screened official-source records are selected deterministically |
| AC-B13-02 | An authorized active Shenzhen identity | Requests `/api/v1/qa` | Returns `{items, meta}` with exact pagination, source metadata, request ID behavior, and `no-store` |
| AC-B13-03 | A valid Q&A ID | Requests `/api/v1/qa/{id}` | Returns complete question/answer and optional legal-basis provenance without user identity fields |
| AC-B13-04 | Signed-out, wrong-scope, missing, or unavailable request | API processes it | Existing 401/403/404/503 contracts apply and no Q&A text leaks |
| AC-B13-05 | Authorized 20-record provisioning is repeated | Same fixture is imported again | Second run inserts zero and preserves all rows/timestamps exactly |
| AC-B13-06 | Full acceptance is run | Tests, Ruff, smoke, runtime, frontend build, and strict OpenSpec execute | All pass without full import, destructive operation, Auth write, feature-flag change, sensitive output, or legacy-source reuse |

## 5. Constraints and Rollback

- The user authorized the exact `0004_historical_qa` migration and the fixed 20-record fixture on 2026-08-12. The second import inserted zero and did not change the 20 existing rows.
- The full source data remains outside Supabase. A later bulk-import change must define privacy review, sample expansion, authorization, and separate evidence.
- Rollback removes B1.3 application/spec/fixture artifacts; no database downgrade or deletion runs automatically.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-11 | V1.0 | Defined the minimal historical government-Q&A slice, public-safe mapping, privacy screen, deterministic 20-record boundary, and non-goals. |
| 2026-08-11 | V1.1 | Completed local implementation and acceptance gates. The database remains unchanged until the user separately authorizes exact `0004` migration and the fixed 20-record import. |
| 2026-08-12 | V1.2 | Applied exactly the authorized migration and 20-record sample. The four active roles completed authenticated list/detail verification; the full 1,650-row source remains outside Supabase. |
