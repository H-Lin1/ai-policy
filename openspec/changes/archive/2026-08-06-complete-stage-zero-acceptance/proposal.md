## Why

Implementation plan: [`TECH-V1-S0-06`](../../../docs/TECH-V1-S0-06.md); development-status step: `S0.6` (see [`DEVELOPMENT_STATUS.md`](../../../DEVELOPMENT_STATUS.md)).

The Stage 0 components have been implemented and individually validated, but its operational entry points still leave a safety and repeatability gap: a bare initialization command runs Alembic immediately, while reset is only an informal no-op and there is no single non-destructive final acceptance command. S0.6 closes Stage 0 by making these operator boundaries executable and producing repeatable evidence without silently writing to Supabase or importing legacy material.

## What Changes

- Change initialization to an inspect-only default; allow the existing approved foundation migration only after explicit named apply and confirmation flags, with no connection-string output.
- Keep demo reset an explicit, acknowledged no-op because Stage 0 owns no business seed data or business tables; prohibit reset code from issuing database, filesystem, or Supabase writes.
- Add a deterministic local Stage 0 acceptance entry point that runs tests, Ruff, hermetic local smoke, frontend guard/build checks, and strict OpenSpec validation without invoking migrations, reset, or external runtime smoke.
- Harden configured runtime-smoke failure output so external dependency failures are explicit but cannot disclose exception text or configuration values.
- Recheck the already-approved foundation schema, Alembic revision, and zero-business-table invariant through read-only PostgreSQL queries; do not run a migration to establish that evidence.
- Add focused tests and documentation for the safety gates, acceptance workflow, and final Stage 0 evidence.
- Do not add an API, business table, migration revision, seed data, delete/reset operation, model integration, Mock response, or legacy-code import/reuse.

## Capabilities

### New Capabilities

- `stage-zero-operations`: Defines safe initialization gating, no-op Stage 0 demo reset, non-destructive acceptance orchestration, and secret-safe smoke reporting.

### Modified Capabilities

- `project-foundation`: The documented initialization, reset, smoke, and final acceptance workflow gains executable safety guarantees.

## Impact

- Affects `backend/scripts/`, script-focused tests, root documentation, `TECH-V1-S0-06`, and `DEVELOPMENT_STATUS.md`.
- Does not alter public API behavior, authentication, frontend routes, persistence schema, or approved classifier boundaries.
- No new dependencies, no Supabase data writes, and no migration execution are part of implementation or acceptance. Legacy Flask/routes/payloads, model assets, search/RAG/FAISS/Embedding code, Mock data, startup code, and frontend are outside the change boundary.
