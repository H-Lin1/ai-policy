## 1. Database and data boundary

- [x] 1.1 Add only the `0002_identity_access` migration for the five IAM tables, restrictive ordered foreign keys, lowercase/non-blank checks, UTC timestamps, RLS plus explicit browser privilege revocation/no-policy posture, same-project Alembic target gate, and reversible downgrade; do not alter `auth.users` or add business tables.
- [x] 1.2 Add migration-structure tests that inspect PostgreSQL operations, dependency order, checks/defaults/nullability, downgrade order, browser access posture, and absence of destructive/Auth-account operations.

## 2. Backend identity and permissions

- [x] 2.1 Add IAM SQLAlchemy models, schemas, repository, and service with active-profile/region/organization/role resolution and stable failure codes.
- [x] 2.2 Replace token-claim-only `/me` output with the shared database identity resolver while preserving explicit non-production development bypass.
- [x] 2.3 Add `/api/v1/iam/workspaces/{role}` and reusable exact-role authorization with OpenAPI metadata, no-store, request IDs, and 401/403/422/503 behavior.
- [x] 2.4 Add secret-safe tests for four roles, JWT/database-role disagreement, unprovisioned/disabled/roleless identities, wrong-role access, and database failures.

## 3. Guarded initialization

- [x] 3.1 Add preflight-only `init_iam.py` with dual flags, same-project PostgreSQL binding, one locked transaction for revision/Auth/ownership revalidation plus insert-only/no-op seed behavior, and no overwrite/reactivation/Auth-user/password/Alembic/delete behavior.
- [x] 3.2 Add tests proving no database/write occurs before every gate, conflicting or drifted records fail without mutation, an exact second run is a zero-write no-op, rollback is atomic, and failures cannot expose project refs, UUIDs, URLs, tokens, keys, or tracebacks.
- [x] 3.3 Advance read-only runtime smoke to require same-project binding, revision `0002_identity_access`, the exact five IAM tables, RLS enabled, no browser policies, and no direct browser grants, with sanitized mismatch/error states.
- [x] 3.4 Load the four named UUID mappings through shared server-side Settings (`.env` plus process-environment precedence), preserve explicit test injection, and prove the CLI never requires shell export or exposes mapping values.

## 4. Frontend identity flow

- [x] 4.1 Add configured Supabase Auth client and provider for session restore, sign-in, sign-out, token refresh, `/me` loading, retry, and stale-state clearing.
- [x] 4.2 Add backend-authorized role guard and personal/enterprise/government/admin routes with loading, signed-out, missing-config, error, denied, and allowed states.
- [x] 4.3 Add frontend guard tests and update environment examples/API client without exposing secrets or direct `app.*` access.

## 5. Verification

- [x] 5.1 Run backend tests, Ruff, local smoke, frontend guard tests, frontend build, aggregate acceptance, and strict OpenSpec validation without migration/seed writes.
- [x] 5.2 Run separately invoked read-only runtime smoke and bound Uvicorn identity/OpenAPI/CORS/log checks with safe output only.
- [x] 5.3 After explicit operator authorization, apply the exact `0002_identity_access` migration, inspect schema/RLS/revision, and require a passing configured runtime smoke.
- [x] 5.4 After separate explicit operator authorization, apply the IAM seed twice and verify that the second execution preserves every seeded row field and timestamp; final table counts are `1/4/3/4/4`.
- [x] 5.5 Execute the real four-account JWT/API/browser role acceptance matrix.

2026-08-06 evidence: the read-only runtime command safely reported only
`identity_schema: revision_mismatch`; all other configured dependency checks and the bound
Uvicorn matrix passed. On 2026-08-07 the operator explicitly authorized only the exact migration;
the upgrade from `0001_foundation_schema` to `0002_identity_access` succeeded and configured
runtime smoke then passed database, target binding, identity schema, authentication, and JWKS.
The later read-only seed preflight verified four valid distinct mappings, all four existing Auth
users, target binding, current revision, and conflict-free deterministic ownership without acquiring
the initializer write lock or mutating data. Under a separate explicit authorization, the initializer
then completed twice. Final counts were `1/4/3/4/4`, and comparison of every row field including
timestamps proved that the second execution changed nothing. No Auth-account operation, downgrade,
reset, or delete ran. Post-seed runtime smoke, bound Uvicorn checks, aggregate acceptance `6/6`,
and strict validation `7/7` passed. The operator then authorized use of the four account credentials
from server `.env` for acceptance. Four real sign-ins and `/me` resolutions passed; each account
exposed exactly its assigned role entry, all four matching workspaces rendered, and all 12 cross-role
workspace attempts returned 403 without protected content. Each session signed out and credentials
were cleared from browser automation memory without being printed. The matrix also exposed a mobile
sign-out visibility defect; the responsive footer was corrected, guarded with a PostCSS test, and
verified at 390x844 with no horizontal overflow and a successful sign-out. Final frontend tests passed
31 scenarios, build transformed 89 modules, runtime smoke was fully `ok`, and aggregate acceptance
passed `6/6`.

## 6. Documentation and handoff

- [x] 6.1 Update PRD/TECH, README, environment examples, OpenAPI evidence, and `DEVELOPMENT_STATUS.md` after each verified milestone.
- [x] 6.2 Sync main OpenSpec specs, record authorized runtime evidence, run post-archive strict validation, and archive `establish-identity-access` only when all tasks and acceptance scenarios pass.
