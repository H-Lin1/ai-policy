# Tasks: B1.2 Policy Sample Provisioning

## Planning gate

- [x] 1.1 Record the exact user authorization, 20-record boundary, migration target, and non-destructive exclusions in TECH V1.2.
- [x] 1.2 Strict-validate the provisioning change before implementation (`10/10`).

## Migration and data

- [x] 2.1 Add a fixed-revision, doubly confirmed `0003_policy_library` initializer path.
- [x] 2.2 Add a locked insert-or-verify importer for exactly the deterministic 20-record fixture.
- [x] 2.3 Add runtime policy-schema and exact fixture verification without any delete/downgrade path.

## Backend

- [x] 3.1 Add tests for default no-op, dual gates, target/revision/schema rejection, conflicts, rollback, insert, and repeated no-op behavior.
- [x] 3.2 Preserve existing API, IAM, pagination, error, no-store, and database repository behavior.

## Frontend

- [x] 4.1 Run existing frontend tests/build; do not change UI or feature flags in this deployment patch.

## Model and data import boundary

- [x] 5.1 Execute only the authorized 20-record fixture import; keep the full CSV, rejected rows, model, Mock, and legacy paths out of scope.
- [x] 5.2 Repeat the import and prove zero inserted/updated rows plus complete row/timestamp invariance.

## Verification and documentation

- [x] 6.1 Execute the authorized exact migration and verify revision, table constraints, RLS, policies, and browser grants.
- [x] 6.2 Verify database-backed policy list/detail with a real provisioned identity.
- [x] 6.3 Run backend tests, Ruff, local smoke, runtime smoke, frontend tests/build, aggregate acceptance, and strict OpenSpec validation.
- [x] 6.4 Update TECH/PRD, `DEVELOPMENT_STATUS.md`, and Feishu; archive only after all evidence is recorded.

## Acceptance evidence

- Migration: exact `0003_policy_library` applied; schema, RLS, no-browser-policy, and no-browser-grant invariants passed.
- Import: first run inserted 20; second run inserted 0; all stored values and audit timestamps remained identical; advisory lock released.
- Real identity/API: authentication and `/api/v1/me` passed; policy list returned 10 items with total 20; detail returned full text, valid hash, and `.gov.cn` source; all responses were `no-store`.
- Final gates: backend `208 passed`; Ruff passed; local smoke `14/14`; runtime smoke `5/5`; frontend tests passed; build emitted 91 modules; aggregate acceptance `6/6`; pre-archive strict validation `10/10`.
- Exclusions: no full-CSV import, update, delete, downgrade, reset, Auth mutation, feature-flag change, sensitive output, or legacy source read.
