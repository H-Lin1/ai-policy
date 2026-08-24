# Tasks: B1.2 Policy Library

## Planning gate

- [x] 1.1 Confirm PRD/TECH scope, source allowlist, read-only roles, and no-import-write boundary.
- [x] 1.2 Run strict validation before implementation.

## Migration and data

- [x] 2.1 Add the `app.policy_documents` migration source with constraints, indexes, and no Auth mutation.
- [x] 2.2 Add source adapter validation for the supplied CSV, `.gov.cn` hosts, dates, hashes, NULs, and statuses.
- [x] 2.3 Generate and review the deterministic 20-record local fixture without modifying the full CSV.

## Backend

- [x] 3.1 Add policy models, schemas, repository, and service using the existing API/pagination/UTC contracts.
- [x] 3.2 Add authenticated `GET /api/v1/policies` and `GET /api/v1/policies/{policy_id}` with `sz` scope and no-store responses.
- [x] 3.3 Add backend tests for list/detail, filtering, pagination, authorization, source validation, dedupe, and error sanitization.

## Frontend

- [x] 4.1 Replace the feature-guard placeholder with the read-only policy list/detail route and UI1.0 visual states.
- [x] 4.2 Add frontend rendering, responsive, loading, empty, denied, and error tests.

## Model and data import boundary

- [x] 5.1 Add only a non-mutating fixture/preflight path for the 20 accepted records.
- [x] 5.2 Keep migration application and Supabase import unexecuted pending separate explicit authorization.

## Verification and documentation

- [x] 6.1 Run backend tests, Ruff, frontend tests/build, local smoke, runtime smoke, and aggregate acceptance.
- [x] 6.2 Run OpenSpec strict validation before archive and record all evidence.
- [x] 6.3 Update `DEVELOPMENT_STATUS.md`, sync the PRD/TECH to Feishu, and archive only after acceptance.

## Acceptance evidence

- 2026-08-11: backend `200 passed`; Ruff passed; local smoke `14/14`; read-only runtime smoke database, target binding, IAM schema, Auth configuration, and JWKS all `ok`.
- 2026-08-11: frontend tests passed; production build passed with 91 modules; aggregate acceptance passed `6/6`; OpenSpec strict validation passed `9/9` before archive.
- 2026-08-11: isolated fixture browser smoke passed at desktop `1280` and mobile `390x844`; list rendered 10 of 20 records with pagination, detail rendered four metadata fields and 7,628 content characters, and both views had `documentWidth == innerWidth`.
- 2026-08-11: no migration, policy import, seed, reset, delete, Auth mutation, or legacy source-code read was performed. `0003_policy_library` and all database imports remain separately authorized deployment operations.
