## Context

See `proposal.md` and the `department-classifier-adapter` delta spec. The new project currently has a small Protocol and an always-unavailable implementation, while `Settings` only records model-path strings. S0.5 must make the boundary executable without loading or copying any legacy computation.

## Goals / Non-Goals

**Goals:**

- Make normalization, region selection, result validation, readiness reasons, and domain failures deterministic and independently testable.
- Build the default adapter from the current runtime settings through an explicit dependency seam, with fail-closed behavior for every incomplete asset configuration.
- Keep the existing public readiness endpoint and shared error/request-ID contracts stable while making its cache and secret-safety behavior explicit.

**Non-Goals:**

- No verified inference implementation, model loading, label import, or migration of old computation in S0.5.
- No classify HTTP route, business authorization policy, `ai_runs` table, database migration, seed/reset write, or Supabase data access.
- No Mock classification response and no changes to authentication, frontend behavior, or the legacy project.

## Decisions

### Domain errors stay below HTTP

Define a small classifier-domain error carrying a stable `code`, human-safe message, and optional safe details. The adapter raises this error for input, region, readiness, and result-contract failures; it does not import FastAPI, Flask, or the shared HTTP `AppError`. A future application service will map the domain code to `AppError` and the existing API envelope. This keeps the adapter reusable in a worker or CLI and avoids making HTTP status codes part of inference logic. The current S0.5 tests assert domain codes directly; the existing `/api/v1/ai/readiness` endpoint remains a read-only status translation.

### Normalize at the adapter boundary and validate typed values

`ClassifierInput.normalized()` applies Unicode NFKC normalization, trims and collapses whitespace, and canonicalizes a region to lower-case ASCII. Empty text/region and malformed identifiers produce stable domain codes. Frozen dataclasses enforce result invariants: department IDs are non-empty and unique, confidence is finite and within 0..1, predictions are non-empty and sorted deterministically, the result region is canonical, and model version is a bounded ASCII metadata token. Validation is performed before a result leaves the adapter so a future implementation cannot leak an invalid contract.

### Use an explicit region registry, not fallback heuristics

Add a comma-separated `CLASSIFIER_SUPPORTED_REGIONS` setting (default `sz` for the Shenzhen-only demonstration). The factory parses, canonicalizes, de-duplicates, and exposes an immutable tuple. `UnavailableDepartmentClassifier` checks region support before the readiness gate: a well-formed unknown region deterministically returns `REGION_NOT_SUPPORTED`, while a supported region with no verified implementation returns `MODEL_NOT_READY`. No region is inferred from text, hostname, locale, or another region's assets.

### Validate an asset manifest without loading model code

Represent the three expected runtime assets (model, tokenizer metadata, label bindings) as an immutable manifest. Readiness checks only whether all configured values are present, regular files, and readable; no file contents or model libraries are loaded in S0.5. Empty configuration yields `verified_model_not_configured`; partial or invalid paths yield `model_assets_invalid`; all paths valid but no approved implementation wired yields `verified_adapter_not_implemented`. The default adapter remains not ready for all three cases and never returns a fabricated result. Reasons are stable identifiers only and never include paths or exception text.

### Build per-settings adapters through dependency injection

Replace the mutable module singleton with `build_department_classifier(settings)` and a compatibility `get_department_classifier(settings=None)` factory. The system router injects the app's `Settings` and constructs the adapter through that seam, so tests can provide supported regions and asset manifests without global state. Construction is cheap and side-effect-free; no background model load or database access occurs.

### Keep readiness safe and observable

`GET /api/v1/ai/readiness` continues to return the existing `status`, `adapter`, `model_version`, and safe `reason` fields. It rebuilds/validates injected readiness values before serialization, adds `Cache-Control: no-store`, and translates an unexpected readiness exception or malformed status to a stable not-ready response rather than exposing a traceback. It does not expose supported paths, credentials, or model internals. The legacy `POST /classify` route remains unregistered.

### Verification and data boundary

Unit tests cover normalization, input/result invariants, supported and unsupported regions, all asset states, factory injection, and readiness combinations. API tests cover the readiness header/body and secret/path absence; smoke checks cover not-ready and legacy-route behavior. The change is persistence-neutral: no Alembic command, SQL write, Supabase call, or business table is introduced.

## Risks / Trade-offs

- **[Risk]** File-existence checks cannot prove that weights and labels are semantically compatible → **Mitigation:** keep readiness false until a separately reviewed implementation validates and loads them; use the explicit `verified_adapter_not_implemented` reason.
- **[Risk]** A strict ASCII region format could reject a future external identifier → **Mitigation:** map external names to stable ASCII IDs in the application service; expand the contract in a later OpenSpec change rather than guessing here.
- **[Risk]** Per-request construction repeats inexpensive path checks → **Mitigation:** keep the manifest check bounded and side-effect-free; introduce lifecycle caching only with a measured requirement.
- **[Risk]** Removing `AppError` from the adapter changes callers that imported the placeholder directly → **Mitigation:** provide a compatibility factory and document service-level translation; no public classify route exists yet.

## Migration Plan

1. Add the settings parser, domain contract/value validation, asset manifest validator, and explicit adapter factory.
2. Update the system readiness dependency and safe response headers without changing the endpoint path or success fields.
3. Extend focused tests and the existing smoke script; run the full required verification matrix.
4. On rollback, remove the new factory/validation and restore the prior unavailable adapter and readiness dependency. No database or external data rollback is required.

No database migration or Supabase data change is permitted in this change.
