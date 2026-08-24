## Context

The Stage 0 authentication boundary verifies Supabase JWTs and exposes `/me`, but the response currently trusts role claims from the token. B1.1 is the prerequisite for every business module: it must establish one database-owned identity source, a Shenzhen scope, organization membership, and server-side role checks without importing the legacy Flask project or creating Supabase Auth accounts.

## Goals / Non-Goals

**Goals:**

- create and validate the five first-batch IAM tables and their dependency order;
- resolve current identity and role access through FastAPI and PostgreSQL;
- provide a safe, repeatable mapping initializer for existing Auth UUIDs;
- make the frontend session and role states explicit and fail closed;
- preserve shared API/error/request-ID/no-store contracts.

**Non-Goals:**

- no Auth user creation, password handling, direct Supabase browser table access, profile/organization CRUD, multi-region support, business records, model/index work, audit trail, or legacy source/model reuse;
- no real migration, seed, deletion, or reset execution during local acceptance without explicit authorization.

## Decisions

### Make application records the authority for roles and scope

`get_current_principal` verifies JWT cryptography and identity claims. A new IAM service then loads the subject's active profile, region, organization, and role joins. Token `roles` metadata remains observable only as untrusted input and is never used to authorize. This prevents a stale or user-editable claim from granting a business workspace.

### Use one reversible migration with ordered table creation

Revision `0002_identity_access` creates regions and roles first, organizations and profiles second, and user-role assignments last; downgrade reverses that order. UUIDs and stable codes are used throughout, database checks reject lowercase/blank violations, and all deletion foreign keys are restrictive. `auth.users` is referenced but never created or altered. PostgreSQL RLS is enabled, direct browser-role privileges are revoked, and no browser policy is created; the trusted FastAPI connection remains responsible for application authorization. Alembic imports the same target-binding validator as runtime smoke and the initializer and rejects both online and offline migration commands before configuration is bound when the standard Supabase API/database references cannot be matched.

### Keep one identity context and reusable role dependency

The IAM service returns an immutable context containing user ID, profile, region, organization, and role summaries. `/me` and `/iam/workspaces/{role}` share this resolver. `require_role` performs an exact active-role check and returns a stable 403. Development bypass short-circuits only in non-production and is visibly marked.

### Gate initialization with target, revision, UUID, and two operator approvals

`init_iam.py` defaults to preflight. The apply path requires `--apply-iam-seed` plus `--confirm`, a PostgreSQL URL whose direct host or pooler username proves the same Supabase project as the public API URL, current `0002_identity_access`, and four distinct UUID environment values. These four fields are declared on the shared `Settings` model so normal process-environment precedence and the configured root/backend `.env` sources work identically; the initializer converts only those named settings into its mapping validator, while explicit test injection remains available. One transaction acquires a fixed advisory lock, revalidates revision/Auth users and all deterministic records on that same connection, and inserts only missing rows. Exact existing rows are no-ops; ID/code collisions, non-demo or disabled profiles, extra/inactive roles, and previous UUID mappings fail closed. No existing row or `updated_at` value is rewritten. It does not call Alembic, Supabase Auth Admin, or any destructive operation.

### Use a side-effect-free frontend Auth provider

`@supabase/supabase-js` owns browser Auth sessions. A provider restores the session, calls `/me`, and clears identity on sign-out or token change. A role guard waits for both identity and backend workspace authorization before mounting children. Missing public configuration and network errors are visible states, not local bypasses or Mock responses. The API client keeps the access token in memory and sends it only as a bearer header.

### Preserve Stage 0 boundaries and avoid legacy reuse

The new IAM router is included under `/api/v1/iam`; no historical `/classify` route or payload is reintroduced. Existing health, classifier readiness, error envelope, request ID, CORS, and feature-guard behavior remain unchanged. No old source, model asset, data file, or startup code is read or copied.

### Advance the configured runtime invariant with the migration

The separate read-only runtime smoke changes its expected head from `0001_foundation_schema` to `0002_identity_access`. It verifies the public API/database project binding, then queries PostgreSQL catalogs for exactly the five approved `app` tables, `relrowsecurity=true` on each, an empty B1.1 browser-policy set, and no direct browser-role table privileges. The historical Stage 0 zero-table state remains recorded in its archived evidence; keeping that live invariant after a business migration would make a healthy B1.1 database appear broken.

## API / Data / Permission / Model / Failure Decisions

| Area | Decision |
|---|---|
| API | `GET /api/v1/me` becomes database-backed; `GET /api/v1/iam/workspaces/{role}` is the minimal testable role boundary. Both are no-store and OpenAPI-described. |
| Data | Five IAM tables only; no business data or Auth table migration. Seed records are explicitly `seeded_demo`; no Mock identity. |
| Permission | JWT proves subject; active DB role and scope authorize. Wrong role, absent profile, disabled scope, and roleless identity fail closed. |
| Model/Mock | No model or classifier computation is loaded; no Mock result or fallback is introduced. |
| Failure | Stable 401/403/422/503 codes, request IDs, no internal exception/SQL/secret output. |
| Migration | Source-only during normal implementation; runtime apply requires separate user authorization. Read-only runtime smoke expects `0002` and the exact five-table/RLS invariant after application. |
| Rollback | Code rollback is reversible; DB downgrade is documented but never automated or run against configured data without explicit approval. |

## Implementation Shape

```text
backend/app/modules/iam/
  models.py       SQLAlchemy table mapping
  schemas.py      identity/workspace response models
  repository.py   session-bound reads and deterministic seed helpers
  service.py      identity resolution and role checks
  router.py       /me integration and /iam/workspaces/{role}
backend/scripts/init_iam.py
backend/migrations/versions/0002_identity_access.py
frontend/src/app/auth/
  client.ts       configured Supabase client
  AuthProvider.tsx session + identity state
  RoleGuard.tsx   backend-authorized route guard
```

Existing `app.modules.system` owns health/features/model readiness; it will import the IAM resolver only for `/me` contract integration, keeping business logic in `iam`.

## Verification and Rollback Plan

1. Strict-validate this change before code.
2. Test migration source with a PostgreSQL dialect/offline operation capture; do not connect to configured Supabase.
3. Unit/API-test every identity failure state, role matrix, no-store/request ID, and secret-safe initializer gate.
4. Run frontend auth/role guard rendering cases, backend tests, Ruff, local smoke, frontend build, aggregate acceptance, read-only runtime smoke, and bound Uvicorn.
5. Request separate authorization for migration/seed, then inspect revision/schema/RLS and run an idempotent four-user matrix.
6. If rollback is approved, disable role routes, verify data/export, and run the exact reverse migration; never use a generic reset/delete command.

## Risks / Trade-offs

- Requiring existing Auth UUIDs leaves account creation to Supabase operators, but avoids password/secret handling and accidental account creation.
- A single migration is easy to review and reverse, but a future large IAM change must use a new revision rather than editing `0002`.
- No browser RLS policies means direct frontend table access remains unavailable by construction; all business reads intentionally pass through FastAPI.
- Development bypass supports local shell checks but is explicitly marked and forbidden in production.
