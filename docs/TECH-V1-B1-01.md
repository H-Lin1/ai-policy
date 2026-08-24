# TECH-V1-B1-01 | Identity and Access Foundation

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-01` |
| Version | `V1.6` |
| Status | Accepted and archived |
| Development step | `B1.1` |
| Product requirement | [`PRD-V1-B1-01`](./PRD-V1-B1-01.md) |
| OpenSpec change | `2026-08-07-establish-identity-access` (archived) |
| Prerequisite | S0.1-S0.6 archived; Supabase Auth/JWKS/PostgreSQL runtime boundary verified |
| Runtime write gate | Exact migration and IAM seed completed under separate explicit authorizations on 2026-08-07; no further database write is authorized |

## 1. Engineering Goal

Replace token-claim-only business roles with a real application identity boundary. JWT verification continues to prove the Supabase subject; FastAPI then resolves the subject against five `app.*` tables and owns role, organization, and Shenzhen scope decisions. Deliver the first complete protected frontend flow without importing legacy code, generating Auth users, or returning Mock identity data.

Success requires:

1. deterministic PostgreSQL schema and reversible migration source;
2. fail-closed database identity resolution and reusable RBAC dependencies;
3. `/api/v1/me` plus a role-specific workspace access contract;
4. Supabase frontend session handling and four role-aware routes with loading, signed-out, error, denied, and allowed states;
5. a doubly confirmed initializer that maps existing Auth UUIDs to seeded demo business records;
6. tests, build, runtime smoke, strict OpenSpec validation, and an authorized real migration/seed matrix before archive.

## 2. Scope and Non-Goals

This change owns the `iam` module, `0002_identity_access` migration, frontend authentication/authorization state, and IAM initialization. It may modify `/me` because B1.1 explicitly replaces its Stage 0 token snapshot with the database-backed identity contract.

It does not create, update, or delete `auth.users`; store passwords or tokens; add profile/admin CRUD; add another region; add policy, QA, model, search, RAG, consultation, notification, attachment, audit, enterprise-profile, matching, or cooperation records; migrate classifier computation; read legacy code; or execute a real migration/seed without approval.

## 3. Data Design

One revision, `0002_identity_access`, creates tables in this dependency order and drops them in reverse:

| Table | Key fields and constraints | Purpose |
|---|---|---|
| `app.regions` | UUID PK; unique normalized `code`; `name`; nullable self `parent_id`; `level`; active flag; UTC timestamps | Extensible region dictionary; B1.1 seeds only `sz` |
| `app.roles` | UUID PK; unique `code`; name/description; active flag; UTC timestamps | Four stable business roles |
| `app.organizations` | UUID PK; unique `code`; region FK; nullable self parent; type `platform/government/enterprise`; active/demo flags; UTC timestamps | Platform, government, and demo enterprise scope |
| `app.profiles` | `user_id` UUID PK/FK to `auth.users.id`; region FK; optional organization FK; display name; active/demo flags; UTC timestamps | Application-owned identity state without duplicating credentials/email |
| `app.user_roles` | composite PK `user_id + role_id`; FKs to profile and role; assigned UTC timestamp | Active role assignments; authority for FastAPI RBAC |

All identifiers use UUID. Codes use lowercase stable identifiers with database checks. Required human-readable values reject blank or whitespace-only strings. Foreign keys use restrictive deletion, including profile-to-role assignments, preventing identity scope from being silently orphaned. API timestamps are UTC-aware.

RLS is enabled on all five tables, direct `anon`/`authenticated` privileges are explicitly revoked, and B1.1 creates no browser policy. The frontend never queries `app.*` directly. The trusted FastAPI database connection owns business reads; backend authorization remains mandatory even if a future database policy is added.

## 4. Backend Design

### 4.1 Module boundary

`app.modules.iam` follows router/service/repository/schema/model layering. Repository code is the only IAM layer issuing SQLAlchemy queries. Service code validates the Supabase UUID subject, active profile, active Shenzhen region, organization compatibility, and non-empty active role set. Router code maps those results to versioned API responses.

### 4.2 Authentication and authority

`get_current_principal` continues to verify the JWT signature, issuer, audience, lifetime, and subject. JWT/app-metadata roles are not authorization authority after B1.1. A new `get_current_identity` dependency resolves database state and returns an immutable identity context with user ID, profile name, region, optional organization, and stable role codes.

Failure mapping:

| Condition | HTTP / code |
|---|---|
| Missing or invalid bearer token | Existing 401 `AUTH_REQUIRED` / `AUTH_INVALID` |
| Non-UUID authenticated subject | 401 `AUTH_INVALID` |
| No application profile | 403 `PROFILE_NOT_PROVISIONED` |
| Disabled profile/region/organization | 403 `ACCOUNT_DISABLED` / `IDENTITY_SCOPE_INACTIVE` |
| No active role | 403 `ROLE_NOT_ASSIGNED` |
| Requested role not assigned | 403 `ROLE_FORBIDDEN` |
| Database/configuration/query failure | 503 `IDENTITY_STORE_UNAVAILABLE` or existing `DATABASE_NOT_CONFIGURED` |

No error includes a SQL statement, DSN, JWT, user list, or internal exception text.

### 4.3 HTTP contracts

`GET /api/v1/me` returns a no-store `MeResponse`: UUID user identifier, verified email when present, display name, active Shenzhen region, optional organization summary, role summaries, and the existing development-bypass marker. Development bypass remains available only outside production and returns an unmistakable local identity without querying PostgreSQL.

`GET /api/v1/iam/workspaces/{role}` accepts only the four stable role codes, loads the same current identity, enforces the requested role server-side, and returns no-store workspace/scope metadata. It performs no write. This endpoint makes 403 behavior testable before later business modules add their own role dependencies.

Both endpoints preserve the shared error envelope, request ID, OpenAPI metadata, and CORS behavior.

## 5. Initialization and Migration Safety

The migration source was locally inspected/tested and was applied to configured Supabase only after the operator explicitly authorized the exact `0002_identity_access` revision on 2026-08-07. It revised only `0001_foundation_schema` and did not alter `auth.users`. The Alembic environment shares the same fail-closed project-binding check as runtime smoke and IAM initialization, so any future migration command still rejects unresolved or mismatched standard Supabase API/database targets before opening its migration transaction.

`scripts/init_iam.py` is preflight-only by default. The write path requires both `--apply-iam-seed` and `--confirm`, a PostgreSQL target already migrated to `0002_identity_access`, and four valid distinct UUIDs supplied through dedicated server-side settings. The four fields use the same `Settings` source and precedence as the rest of the runtime configuration, so values in the configured root/backend `.env` work without an unsafe shell `source` step; process environment values still take precedence, and explicit mapping injection remains test-only. Before opening a write transaction, it must fail closed unless the Supabase API URL and the direct database host or pooler username resolve to the same project reference; unsupported/custom target forms require an explicit, independently verifiable binding rather than an operator guess.

One transaction acquires a transaction-scoped advisory lock, rechecks the revision and existing Auth UUIDs on the same connection, validates all deterministic ID/code pairs and current mappings, and then inserts only missing records. An existing exact initializer-owned record is a no-op. Any ID/code collision, non-demo profile, disabled record, conflicting role, changed UUID mapping, or other value drift fails before mutation. The initializer never overwrites or reactivates existing records, and an identical second run performs no row or timestamp update. It does not create Auth users, accept passwords, call Supabase Auth Admin APIs, print UUIDs/configuration, or run Alembic.

Fixed seeded records use deterministic IDs/codes. Demo profiles and demo organizations carry `is_demo=true`; real platform/role/region dictionaries are not misrepresented as collected business data. Reset/delete behavior remains outside B1.1.

## 6. Frontend Design

Use the maintained `@supabase/supabase-js` client for Auth session handling. Browser configuration is limited to the public Supabase URL and anon/publishable key plus the existing API base URL. Missing auth configuration yields an explicit unavailable state; no fake session is created.

An `AuthProvider` owns session restore, sign-in, sign-out, `/me` loading, retry, and stale-state clearing. The API client receives the access token only in an `Authorization` header and never persists another copy. `RoleGuard` handles stable states: loading, signed out, identity unavailable, denied, and allowed. Protected content mounts only in the allowed state.

Routes are `/personal`, `/enterprise`, `/government`, and `/admin`. Navigation is derived from database roles returned by `/me`; direct URL entry still calls the backend workspace endpoint and renders a dedicated 403 state when denied. The B1.1 pages show the current identity and scope, not placeholder policy/QA/consultation results.

## 7. Tests and Acceptance

Before archive, run:

- migration-structure tests for table/order/FK/RLS/downgrade behavior without applying configured Supabase;
- repository/service/API tests for four roles, 401, all 403 identity states, wrong-role access, development bypass, 503 sanitization, request IDs, `no-store`, and OpenAPI;
- initializer tests for bare/partial flags, project mismatch/unresolved targets, invalid or duplicate UUIDs, missing revision/Auth users, deterministic ID/code collisions, non-demo/disabled/conflicting/drifted mappings, one-transaction revalidation, exact no-op second execution, rollback, and secret-safe failures;
- frontend auth/role guard tests for config missing, loading, signed out, identity failure, denied, and each allowed role;
- full backend tests, Ruff, local smoke, frontend build, aggregate acceptance, read-only runtime smoke, bound Uvicorn check, and OpenSpec strict validation;
- only after explicit authorization: real migration upgrade, revision/schema/RLS inspection, idempotent IAM seed, four-account runtime matrix, and rollback strategy verification without destructive execution.

No test may use or print a real password, JWT, UUID mapping, database URL, or key.

The configured runtime smoke advances with this migration: it first requires a verified Supabase API/database project binding, current revision `0002_identity_access`, exactly the five approved `app` tables, RLS enabled for all five, no B1.1 browser policies, and no direct `anon`/`authenticated` table privilege. The 2026-08-06 pre-migration run truthfully reported `identity_schema: revision_mismatch`. After the explicitly authorized upgrade on 2026-08-07, database connectivity, target binding, identity schema, authentication configuration, and JWKS all passed.

## 8. Rollback and Risks

Code rollback restores the Stage 0 `/me` contract and removes IAM frontend routes. Database downgrade is source-defined in reverse dependency order, but running it against configured data is destructive and is never part of automatic acceptance. If a deployed rollback is needed, first disable IAM entry points, export/verify data, obtain explicit approval, and then run the exact revision downgrade.

Primary risks are trusting token roles, cross-role content flashing, orphaned organization scope, accidental Auth-account creation, and running migration/seed against the wrong project. Database-backed authority, server checks, mount-after-allow guards, restrictive FKs, no Auth Admin integration, same-project/revision gates, dual flags, deterministic IDs, insert-or-verify semantics, and hidden configuration mitigate them.

The production dependency audit currently reports two moderate React Router 6.30.4 advisories with no v6 fix available. The exposed conditions are constrained in B1.1: every `Link`/role destination is a compile-time mapping rather than untrusted input, and this Vite application does not use SSR hydration or `deserializeErrors`. A major upgrade to React Router 7.18+ requires its own compatibility plan and is not silently applied inside the IAM change; the audit remains a recorded residual risk rather than an untested major-version mutation.

## 9. Implementation Order

1. Confirm PRD/TECH and strictly validate the full OpenSpec change.
2. Add migration source, models, initializer gates, and non-mutating tests.
3. Add identity repository/service/dependencies and API contracts.
4. Add Supabase Auth provider, role guards, four workspaces, and frontend tests.
5. Run the non-mutating verification matrix and update evidence.
6. Complete the real four-account runtime matrix, then sync specs, archive, and advance to B1.2.

## 10. Local and Runtime Acceptance Evidence

The original local evidence was collected on 2026-08-06 without migration, seed, reset, delete,
Auth Admin, or other Supabase writes. The table also records the separately authorized migration
and seed operations plus their post-write read-only verification on 2026-08-07.

| Check | Result |
|---|---|
| OpenSpec before implementation, before archive, and after archive | Strict validation passed `7/7`; main `identity-access` and updated `stage-zero-operations` specs are synchronized |
| Backend tests | `186 passed`; one upstream Starlette/httpx deprecation warning |
| Ruff | All checks passed |
| Hermetic local smoke | `14/14` named checks passed |
| IAM initializer preflight | `not_requested (postgresql_configured)`; explicitly reported no data change |
| Frontend tests | 31 scenarios passed: FeatureGuard 5, Auth/session 8, role guards/routes 17, responsive sign-out 1 |
| Frontend production build | TypeScript and Vite passed; 89 modules transformed |
| Aggregate acceptance | All 6 constituents passed: backend, Ruff, smoke, frontend tests/build, OpenSpec strict |
| Authorized migration | Explicitly authorized exact upgrade `0001_foundation_schema -> 0002_identity_access` completed successfully; no seed, downgrade, reset, delete, or Auth operation ran |
| Post-migration configured runtime smoke | Database, same-project binding, exact five-table/RLS/no-policy/no-browser-grant identity schema, auth configuration, and JWKS all passed |
| Earlier read-only IAM seed preflight | Shared Settings loaded four valid distinct mappings from the configured root `.env` without shell export; all four Auth users existed and deterministic ownership had no conflict; no advisory write lock or data mutation occurred during preflight |
| Authorized IAM seed | Under separate explicit authorization, the locked initializer completed twice. Final counts were regions/roles/organizations/profiles/user_roles=`1/4/3/4/4`; comparison of every row field, including timestamps, proved the second run changed nothing |
| Post-seed configured runtime smoke | Database, same-project binding, exact identity schema, authentication configuration, and JWKS all passed |
| Real four-account matrix | Four real sign-ins and `/me` resolutions passed; each account exposed only its assigned navigation, its matching workspace returned protected content, and all 12 cross-role workspace attempts returned 403 without mounting protected content; every session signed out successfully |
| Mobile sign-out correction | Real-account acceptance exposed the only sign-out control being hidden below 720px. The mobile footer now remains visible; a PostCSS regression test and 390x844 browser check verified the account row, sign-out, no horizontal overflow, and successful return to the login page |
| Bound Uvicorn | live/ready 200, unauthenticated `/me` 401, OpenAPI 200, allowed-origin CORS preflight 200, `no-store`, JSON request logs, and graceful shutdown passed |
| Browser walk-through | 1280x720 and 390x844 signed-out/signed-in paths had no horizontal overflow, clipped text, or overlap; real session restore, navigation, allowed/denied role states, and sign-out rendered correctly after the mobile correction |
| Production dependency audit | Two moderate React Router 6 advisories remain; no v6 fix is available and the constrained residual risk is recorded in section 8 |

The local implementation, exact migration, configured runtime schema, IAM seed, real-database
idempotency, and four-account JWT/API/browser role matrix are verified. B1.1 is accepted and
archived. The configured database remains at `0002_identity_access (head)` with the
expected IAM records. Credentials and tokens were never printed or persisted by the acceptance
workflow, and the browser was left signed out.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-06 | V1.0 | Confirmed the B1.1 database-owned identity, four-role RBAC, frontend session, guarded initialization, migration, failure, and rollback design. |
| 2026-08-06 | V1.1 | Hardened target binding, conflict-safe insert-or-verify seed semantics, single-transaction locking/revalidation, restrictive constraints, and RLS privilege/policy acceptance before runtime writes. |
| 2026-08-06 | V1.2 | Recorded the completed non-mutating implementation matrix and the observed pre-migration `revision_mismatch` blocker. |
| 2026-08-07 | V1.3 | Recorded the explicitly authorized exact migration, passing five-table/RLS/browser-denial runtime invariant, and separately gated seed blocker. |
| 2026-08-07 | V1.4 | Unified IAM UUID loading with server Settings so configured `.env` and process-environment precedence work without shell export; added CLI/config regression coverage. |
| 2026-08-07 | V1.5 | Recorded the separately authorized IAM seed, exact second-run row/timestamp invariance, expected five-table counts, and the remaining interactive four-account acceptance blocker. |
| 2026-08-07 | V1.6 | Completed the real four-account allow/deny matrix, corrected mobile sign-out visibility with regression coverage, synchronized main specs, and archived B1.1 with post-archive strict validation. |
