## Why

This change implements [`PRD-V1-B1-01`](../../../docs/PRD-V1-B1-01.md) and [`TECH-V1-B1-01`](../../../docs/TECH-V1-B1-01.md) for development-status step `B1.1`. Stage 0 verifies Supabase JWTs, but business roles are still represented by token claims and the frontend has no real signed-in role boundary. Policy, QA, classification, and consultation features must not be built on that incomplete authority model.

## What Changes

- Add the first IAM migration for `app.regions`, `app.roles`, `app.organizations`, `app.profiles`, and `app.user_roles`, with restrictive foreign keys, UTC timestamps, and browser-denying RLS posture.
- Resolve `/api/v1/me` from the verified JWT subject plus active application records, while retaining a safe development bypass only outside production.
- Add a server-enforced role workspace access contract and reusable identity/RBAC service behavior with stable 401/403/503 errors.
- Add a preflight-only, doubly confirmed initializer that verifies the API/database project binding and atomically inserts or verifies deterministic Shenzhen/demo mappings for existing Supabase Auth UUIDs; it never overwrites existing identity data, creates Auth users, or accepts credentials.
- Advance configured runtime smoke from the Stage 0 zero-table invariant to a read-only same-project/`0002_identity_access`/five-IAM-table/RLS/no-browser-access invariant.
- Add frontend Supabase session restore/sign-in/sign-out, identity loading, retry, sign-out, and four role-aware workspace routes with backend-confirmed authorization.
- Add migration, API, initializer, frontend guard, OpenAPI, and secret-safety tests and update the local run documentation.

## Capabilities

### New Capabilities

- `identity-access`: Database-owned identity, organization/region scope, four-role authorization, protected workspace entry, and safe initialization.

### Modified Capabilities

- `stage-zero-operations`: The configured runtime smoke evolves from its historical Stage 0 zero-table check to the current B1.1 IAM schema/revision check while retaining secret-safe, read-only behavior.

## Impact

- Affects `backend/migrations/`, `backend/app/modules/iam/`, the existing `/me` contract, `backend/scripts/`, frontend authentication/runtime state and role routes, tests, environment examples, README, and B1.1 documentation.
- Adds no `auth.users` table or account creation, no password/token persistence, no policy or AI data, no legacy-code import, and no Mock identity result.
- A real migration or IAM seed against configured Supabase is an external write and is outside automatic acceptance until the operator explicitly authorizes it.
