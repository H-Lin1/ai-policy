# Proposal: Optimize Policy List Performance

## Why

The accepted database-backed policy list returns correct data but was observed at approximately 30-41 seconds. Read-only profiling shows avoidable second-connection acquisition, two list SQL round trips, and full-text column loading on the list path.

## What Changes

- Share one request-scoped SQLAlchemy session between IAM and policy repository dependencies.
- Return normal non-empty policy pages with one projected SQL query and a window total.
- Keep an empty-page count fallback so the existing pagination contract remains exact.
- Add deterministic session/query-shape tests and a real authenticated runtime performance gate.
- Preserve API schemas, IAM enforcement, errors, `no-store`, frontend behavior, database schema, and all data.

## What Does Not Change

- No migration, policy write, full-CSV import, update, delete, downgrade, reset, Auth mutation, feature-flag change, cache, model/RAG work, or legacy source access.

## Impact

- Code: shared database dependency, IAM/policy repository wiring, policy list query, focused tests.
- Spec: `policy-library` performance behavior.
- TECH: `docs/TECH-V1-B1-02-P1.md`.
