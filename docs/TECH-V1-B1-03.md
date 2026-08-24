# TECH-V1-B1-03 | Historical Government Q&A Read-Only Slice

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-03` |
| Version | `V1.2` |
| Status | Accepted; archived after OpenSpec validation |
| Development step | `B1.3` |
| Product requirement | [`PRD-V1-B1-03`](./PRD-V1-B1-03.md) |
| OpenSpec change | `2026-08-11-establish-historical-qa` (archived) |
| Database write gate | User authorized and completed: exact `0004` migration and fixed 20-record fixture only |

## 1. Source Audit and Fixed Boundary

The only B1.3 source is the three `*_cleaned_model_validated_v2_name_adjudicated.csv` files under the user-provided data directory. They contain 846, 558, and 246 rows respectively (1,650 total). All 1,650 source URLs resolve to `www.sz.gov.cn`; source `数据ID` values are unique. There are 1,589 unique normalized topic/question/answer pairs and 61 duplicate pairs. Legal-basis metadata reports 1,002 `是` and 648 `否`; adjudication has 1,076 `大模型清洗对`, 348 `规则对`, and 226 `无法确认`.

The adapter must not use or persist `数据ID`, `受理编号`, `昵称`, answer-unit blank field, or adjudication rationale. The deterministic fixture selects 20 valid records after global de-duplication and privacy screening, balanced across the three source periods when possible. The full 1,650 rows remain out of scope.

## 2. Model and Migration

`0004_historical_qa` follows `0003_policy_library` and creates only `app.historical_qa`. A row has server-generated UUID, active `sz` region, normalized topic/question/answer, source URL, optional question/reply dates, publisher, collection time, optional legal-basis fields and adjudication outcome, immutable SHA-256, and UTC audit timestamps. Identity uniqueness is `(source_url, content_sha256)`. It has non-blank/hash/region checks, restrictive FK, RLS enabled, no browser policies, and revoked `anon`/`authenticated` privileges. It does not modify `auth.users`.

## 3. Adapter and Privacy Controls

The adapter normalizes NULs/line endings and computes the content hash from `topic + "\\n" + question + "\\n" + answer + "\\n" + source_url`. It accepts only HTTPS hosts equal to `gov.cn` or ending in `.gov.cn`; it validates dates and UTC collection time. It rejects duplicate identity, missing mandatory text, unsupported region, malformed metadata, and sensitive patterns for telephone, email, PRC ID, long card-like digit sequences, and labeled contact values. It excludes entire records rather than redacting source text in-place, preserving a clear audit boundary.

## 4. API and Frontend

`GET /api/v1/qa` and `/api/v1/qa/{qa_id}` use the existing current-identity path and request-scoped session. List uses the B1.2-P1 projected one-statement window-total pattern; detail returns complete permitted text. Both scope to `sz`, return `no-store`, and retain shared errors/request IDs. The frontend adds guarded `/qa` and `/qa/:qaId` routes, compact old-site-baseline cards, pagination, source links, and explicit failure states. It contains no chatbot form or retrieval interface.

## 5. Provisioning and Verification

`scripts/init_qa.py` is inspect-only by default. A migration requires `--apply-qa-migration --confirm`; fixture import requires `--apply-qa-fixture --confirm`, verified target binding, exact revision/schema/security state, active region, advisory lock, deterministic UUIDs, and insert-or-verify behavior. No update/delete/downgrade path exists. On 2026-08-12, the user authorized and the provisioner applied exactly `0004_historical_qa`, then inserted exactly 20 records; an immediate second run inserted 0 records. The database check confirmed revision `0004_historical_qa`, 20 unique identities, unchanged audit timestamps, RLS enabled, zero browser policies, and zero `anon`/`authenticated` grants. All four existing roles completed real authenticated list/detail checks.

Before any external write, test adapter privacy rejection, fixture determinism, migration structure, repository/API/frontend behavior, initializer gates, conflicts, rollback, and second-run invariance. Complete acceptance requires backend tests, Ruff, local/runtime smoke, frontend tests/build, authenticated API verification, aggregate acceptance, strict validation, TECH/status update, Feishu sync, and archive. The full CSV is never imported by this change.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-11 | V1.0 | Defined B1.3 source audit, privacy-first mapping, minimal schema/API/UI, deterministic 20-record provisioner, and explicit migration gate. |
| 2026-08-11 | V1.1 | Implemented `0004` source, 20-record privacy-screened fixture, guarded initializer, authenticated list/detail API and responsive UI. Local gates passed: 222 backend tests, Ruff, local smoke, dependency runtime smoke, frontend render tests/build, aggregate acceptance, and OpenSpec strict 10/10. No database migration or import was executed. |
| 2026-08-12 | V1.2 | User-authorized provisioning completed: `0004_historical_qa` applied, fixture first run inserted 20 and second run inserted 0. Database security/identity checks and real authenticated API list/detail checks passed for individual, enterprise, government, and admin roles. No full import, update, delete, Auth write, or feature-flag change occurred. |
