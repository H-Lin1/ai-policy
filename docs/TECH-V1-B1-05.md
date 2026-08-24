# TECH-V1-B1-05 | Policy Q&A Entry and RAG Contract Foundation

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-05` |
| Version | `V1.0` |
| Status | Accepted |
| Development step | `B1.5` |
| Product requirement | [`PRD-V1-B1-05`](./PRD-V1-B1-05.md) |
| Backend handoff | [`RAG-BACKEND-HANDOFF-V1`](./RAG-BACKEND-HANDOFF-V1.md) |
| Feishu copies | [PRD](https://a9ihi0un9c.feishu.cn/docx/RAcsdg7WroHGwTxUxlncCVF7npf) / [TECH](https://a9ihi0un9c.feishu.cn/docx/L8radzyovo1GjUxTAvSc4YFanlc) / [RAG handoff](https://a9ihi0un9c.feishu.cn/docx/UVyEdVZ55obG7QxOMsmcftArntZ) |
| OpenSpec change | `2026-08-21-establish-policy-qa-entry` |
| Database change | None planned |

## 1. Architecture and engine boundary

Create a `PolicyAnswerEngine` protocol under a new `policy_qa` module. Its sole input is a normalized `PolicyQuestion` containing text, canonical region and allowed role context; its output is a typed `PolicyAnswerResult`. The HTTP service owns IAM, request normalization, content length limits, error translation, logging discipline and response construction. Engine implementations do not receive the HTTP request, JWT, database session, secrets or raw identity record.

`PlaceholderPolicyAnswerEngine` is deliberately the only configured implementation in this change. It returns a static, non-authoritative Chinese message, empty sources and `answer_mode="placeholder"`. It is never selected as a silent fallback after a real RAG engine failure. The future RAG implementation is loaded only through an explicit, validated configuration boundary; unavailable or failed RAG returns an explicit 503 safe error.

## 2. HTTP contract

Add `POST /api/v1/policy-answers`. Request body: `{ "question": string }`, with NFKC and whitespace normalization performed server-side; maximum raw question length is 4,000 characters and the normalized result must be non-empty. The current identity must be active, Shenzhen-scoped, and have either `individual` or `enterprise` role. The API responds with:

```json
{
  "request_id": "request-id",
  "region_id": "sz",
  "answer_mode": "placeholder",
  "answer": "…",
  "sources": [],
  "notices": ["当前为演示回答，真实政策检索与生成能力尚未接入。"]
}
```

For future `rag` responses, sources are bounded and ordered, each containing only `source_type` (`policy_document` or `historical_qa`), stable `source_id`, `title`, `source_url`, optional `published_date`, and optional short `excerpt`. Raw scores, chunk identifiers, hidden prompts and corpus paths are forbidden. All success and error responses set `Cache-Control: no-store` and preserve the existing request ID envelope.

## 3. Frontend

Use a shared `PolicyQaWorkbench` component from the public home, authenticated home, and individual/enterprise workspace routes. It accepts a question, invokes the bearer-token API only when identity and role permit it, and renders five explicit states: sign-in required, empty, loading, placeholder result, and error. The status label makes placeholder mode obvious. The page contains no history, source import, model controls, “generated policy” claim or client-side answer fallback.

## 4. Data, security and operations

This change performs no database query or write inside the placeholder engine. Existing `app.policy_documents` and `app.historical_qa` tables remain read-only source-of-truth candidates for a later RAG implementation; browser roles retain no direct grants. The complete schema and future migration plan is in the handoff document.

Question text must not enter structured logs. The service logs only safe event names and request IDs. No cache, retries to a different engine, or cross-region retrieval is allowed. RAG-specific configuration values must never be added to browser-exposed runtime config.

## 5. Verification and rollback

Tests cover invalid/blank/too-long input, IAM role/scope rejection, placeholder contract, non-persistence, no-store/request ID, no input echo, engine failure translation, frontend render states and mobile styling. Acceptance includes backend tests, Ruff, local smoke, read-only runtime smoke, frontend test/build, an authenticated runtime request to the placeholder endpoint and strict OpenSpec validation. Rollback removes code and static documentation only; no migration or data operation is run.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-21 | V1.0 | Defined the stable policy Q&A API, explicit placeholder engine, shared UI workbench, RAG handoff boundary and no-persistence rollout. |
| 2026-08-21 | V1.0 | Accepted after full backend/frontend/static/runtime verification and authenticated placeholder endpoint validation; no migration, data/Auth write or deletion was performed. |
