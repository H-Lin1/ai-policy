# TECH-V1-B1-04 | Department Classification Foundation

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-04` |
| Version | `V1.1` |
| Status | Accepted |
| Development step | `B1.4` |
| Product requirement | [`PRD-V1-B1-04`](./PRD-V1-B1-04.md) |
| OpenSpec change | `2026-08-21-establish-classification-foundation` |
| Database change | None planned |
| Feishu | [TECH-V1-B1-04](https://a9ihi0un9c.feishu.cn/docx/EqxuddpTKoX4UFxiNAcc5Nirnpg) |

## 1. Asset boundary and provenance

The only implementation inputs are server-side model assets explicitly configured through the new B1.4 manifest. The current audit found candidate Shenzhen assets under the user workspace (`model weights`, Chinese BERT tokenizer files, and a label encoder), but the new project currently loads no classifier paths and the existing adapter reports `verified_model_not_configured`. Before wiring inference, a small read-only asset probe must establish file type, label mapping shape, model architecture compatibility, tokenizer compatibility, and deterministic version metadata. It must not read or copy legacy application code.

2026-08-21 asset audit: the user supplied the Shenzhen model, BERT tokenizer directory, label encoder, and department embeddings inside this repository. The tokenizer reports a 21,128-token BERT-compatible vocabulary; the model head and embeddings both resolve to 35 classes. The legacy label encoder was inspected once under a narrow trusted conversion procedure and will be replaced at runtime by an auditable JSON binding. The manifest therefore has four explicit non-sensitive paths: model, tokenizer directory, label binding, and department embeddings. It must validate the required tokenizer files and all four assets without deriving sibling paths implicitly.

The adapter may reuse only the verified pure classification computation as an adapter implementation. Legacy Flask routes, payloads, global state, startup code, frontend code, search/RAG/FAISS/embedding code, and unverified model wrappers remain outside the repository boundary.

## 2. Model adapter

`ValidatedDepartmentClassifier` remains the application-neutral contract. B1.4 adds a concrete, settings-aware implementation only after manifest validation succeeds. Model and tokenizer objects are loaded lazily or during an explicit readiness probe, never from module import. The implementation must use CPU-safe deterministic inference, `eval()`/inference-only execution, bounded input length, and stable prediction ordering. Any import, deserialization, shape, tokenizer, label, or inference error maps to a registered safe readiness or classifier error and never exposes the underlying exception.

The label binding file is the authority for `department_id` and display name. Model class indices are translated through that binding; unknown/out-of-range indices fail closed. The adapter returns only canonical `sz` results, and its `model_version` is a safe manifest token derived from explicit configuration rather than a path or file contents dumped into a response.

## 3. HTTP contract

Add `POST /api/v1/classifications` with a Pydantic request containing `text` and optional explicit `region_id` only for internal/testing use; normal browser calls derive the region from the authenticated identity and reject a mismatch. The endpoint depends on `get_current_identity`, checks active Shenzhen scope, invokes the classifier, translates domain failures through the shared error envelope, preserves request IDs, and sets `Cache-Control: no-store`. It never writes `app.*` tables.

Response fields are `region_id`, `model_version`, and `predictions[]` with `department_id`, `department_name`, and `confidence`. The response omits input text, asset paths, raw logits, labels file contents, and exception details.

## 4. Frontend

Add `/classify` as an authenticated, responsive workbench in the existing visual baseline. It contains a textarea, submit action, result cards, and explicit loading/empty/error/not-ready states. The page uses the shared Supabase bearer session and API client. It does not offer model configuration, import, approval, chat history, or fallback data.

## 5. Failure, security, and operations

`MODEL_NOT_READY`, `MODEL_ASSETS_INVALID`, `CLASSIFIER_CONTRACT_INVALID`, `CLASSIFIER_INFERENCE_FAILED`, and `IDENTITY_SCOPE_INACTIVE` remain stable safe codes. Readiness is fail-closed. Request text is not logged. No cache is allowed because results may depend on model configuration and identity scope. The model endpoint must not be added to smoke as a successful mock; local smoke expects explicit not-ready behavior when assets are absent.

## 6. Verification and rollback

Tests cover manifest absence/partial/incompatibility, tokenizer directory requirements, label mapping, deterministic repeated CPU inference, invalid input/result, scope/auth errors, safe errors, no-store, and absence of database writes. Acceptance evidence on 2026-08-21: backend `238` tests pass; Ruff passes; local smoke `14/14` passes; read-only runtime smoke `5/5` passes; frontend `7` render suites and production build pass; active-change strict validation passes. A real Shenzhen account completed two authenticated API calls with matching result payloads, `no-store`, and request-ID propagation. No migration, database write, Auth write, deletion, Mock fallback, or legacy route/frontend reuse occurred.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-21 | V1.0 | Defined B1.4 asset audit, verified adapter boundary, classification API, frontend workbench, failure model, and acceptance gates. |
| 2026-08-21 | V1.1 | Recorded four-asset manifest, audited JSON label binding, verified CPU inference, authenticated runtime result, and complete acceptance evidence. |
