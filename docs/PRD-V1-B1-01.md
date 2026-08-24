# PRD-V1-B1-01 | Identity, Organization, Region, and Access

## 0. Basic Information

| Field | Value |
|---|---|
| PRD ID / feature | `PRD-V1-B1-01` / Identity, organization, region, and access |
| Baseline step | First batch `B1.1` |
| Version / status | `V1.5` / Accepted and archived |
| Priority | P0 |
| Confirmation basis | AI Policy Service Platform V1.0 baseline `v1.1` and the instruction to continue the next development step |
| Confirmed date | 2026-08-06 |
| Prerequisite | Stage 0 archived; configured Supabase Auth/PostgreSQL is available for authorized runtime acceptance |
| OpenSpec change | `establish-identity-access` |

**Delivery:** A signed-in user can resolve a real application profile, Shenzhen scope, organization, and database-backed role, then enter only the matching personal, enterprise, government, or administrator workspace. The backend returns 403 for an authenticated but unprovisioned, disabled, roleless, or wrong-role identity.

## 1. Requirements and Scope

**Background:** Stage 0 verifies Supabase JWTs but still returns role claims directly from the token. The first business batch needs an application-owned identity and authorization source before policy, question-answering, classification, or consultation data can be scoped safely.

**Users and scenarios:** Personal, enterprise, government, and administrator demo users sign in through Supabase Auth, open the platform, and see only the workspace allowed by their active application profile and role assignment.

**Goals:**

- resolve the current identity from real `app.*` records after JWT verification;
- expose a stable `/api/v1/me` identity snapshot and role-specific workspace access check;
- provide frontend sign-in/session/error handling and four role-aware workspace entries;
- provide repeatable, explicitly confirmed initialization for Shenzhen dictionaries, demo organizations, and mappings to existing Supabase Auth user UUIDs;
- reject missing identity state and cross-role access explicitly without Mock fallback.

| Scope | Content |
|---|---|
| Included | `app.regions`, `app.roles`, `app.organizations`, `app.profiles`, `app.user_roles`; database-owned RBAC; `/me`; role workspace access API; sign-in/sign-out/session restore; four role routes; guarded initializer; tests and acceptance evidence |
| Excluded | Creating or deleting `auth.users`; storing passwords; profile editing; organization administration; multi-region operation; policy/QA/classification/consultation business data; audit table; model migration; old project code or Mock identities |

**Primary demo path:** Existing Supabase demo user signs in -> frontend sends bearer token to `/me` -> backend loads active profile/role/scope -> user enters the matching workspace -> direct access to another role workspace receives 403 and shows an access-denied state.

## 2. Data Flow and API Plan

**Main flow:** Credentials -> Supabase Auth session -> JWT to FastAPI -> JWKS identity verification -> `profiles/user_roles/roles/regions/organizations` lookup -> identity snapshot -> role workspace authorization -> role-specific page.

| Step | Role/page | Input and action | API | System handling | Result / failure |
|---|---|---|---|---|---|
| 1 | All roles / sign in | Email and password are submitted to Supabase Auth | Supabase Auth client | Supabase owns credentials and returns a session; the app does not store or log passwords/tokens | Session is established; unavailable or invalid auth remains an explicit sign-in error |
| 2 | Signed-in user / app shell | Load current identity | `GET /api/v1/me` | Verify JWT, parse UUID subject, load active profile, roles, Shenzhen region, and optional organization from PostgreSQL | Real identity snapshot; 401 for invalid/missing JWT; 403 for unprovisioned, disabled, or roleless identity; 503 for identity-store failure |
| 3 | Signed-in user / role workspace | Open a role-specific route | `GET /api/v1/iam/workspaces/{role}` | Reuse current database identity and require the requested stable role code | Matching role returns workspace/scope metadata; wrong role returns 403; invalid role returns 422 |
| 4 | Signed-in user / app shell | Sign out | Supabase Auth client | Clear Supabase session and local identity snapshot | Return to sign-in; no stale protected content remains visible |

**Key rules:**

- Stable role codes are `individual`, `enterprise`, `government`, and `admin`.
- Supabase JWT claims establish identity only. Business authorization comes from active database assignments, never from browser-provided role state or user-editable metadata.
- V1.0 accepts only active region code `sz`. Unknown or inactive scope fails closed.
- Personal users may have no organization. Enterprise, government, and administrator demo users require the corresponding enterprise, government, or platform organization.
- A frontend route guard improves navigation but never replaces backend role checks.
- Identity and workspace responses use `Cache-Control: no-store` and never include a token, password, connection string, or hidden configuration value.

**Data preparation:** One Alembic revision creates the five tables in dependency order and enables RLS without browser grants or policies. A separate initializer is preflight-only by default and, only after an apply flag plus confirmation, verifies that the Supabase API and database belong to the same project, then inserts missing deterministic Shenzhen, role, demo organization/profile, and role-assignment records for four existing Auth UUIDs. Exact existing seed records are a no-op; conflicting, disabled, non-demo, or drifted records fail closed and are never overwritten or reactivated. It does not create Auth accounts.

## 3. Development Plan and Progress

| Order | Layer | Milestone | Dependency | Status | Evidence |
|---|---|---|---|---|---|
| 1 | Data | Migration and guarded initialization | S0.6 archive | Completed | Exact `0002` head and runtime schema pass; initializer ran twice under separate authorization, final counts are `1/4/3/4/4`, and every row field/timestamp was unchanged on the second run |
| 2 | Backend | Database identity, `/me`, workspace RBAC, error behavior | Data contract | Local acceptance passed | 186 backend tests, Ruff, local smoke, API/OpenAPI matrix |
| 3 | Frontend | Supabase session, sign-in, identity state, four route guards | Backend contract | Completed | 31 guard/session/responsive scenarios, 89-module build, desktop/mobile real-session walk-through |
| 4 | Acceptance | Authorized migration/seed and four-role runtime path | Existing Auth UUIDs and operator approval | Completed | Four `/me`, four matching workspace, twelve cross-role 403, four sign-outs, runtime smoke and aggregate acceptance passed |

**Current blocker:** None. Implementation, separately authorized migration/seed, idempotency, four-account runtime acceptance, and final non-destructive verification are complete.

**OpenSpec status:** `2026-08-07-establish-identity-access` is archived. Main specifications are synchronized and post-archive strict validation passes `7/7`.

## 4. Acceptance and Change Record

| ID | Given | When | Then | Evidence | Result |
|---|---|---|---|---|---|
| AC-01 | Active personal profile with `individual` role | User signs in and opens personal workspace | `/me` returns real Shenzhen identity; personal workspace loads | Real personal login, `/me`, matching workspace, three denied cross-role routes, and sign-out | Passed runtime |
| AC-02 | Active enterprise, government, and admin profiles | Each user signs in and opens its matching workspace | Each receives its own real role and organization scope | Three real logins, three `/me`, three matching workspaces, nine denied cross-role routes, and three sign-outs | Passed runtime |
| AC-03 | Authenticated personal user | User requests government workspace API/route | Backend returns 403 and frontend renders no government content | Real personal cross-role denial plus the complete 12-denial browser/API matrix | Passed runtime |
| AC-04 | Valid JWT without profile, disabled profile, or no active role | User requests `/me` | Stable 403 error identifies the unusable identity state without leaking records | Service/API failure-state tests | Passed locally |
| AC-05 | Missing/invalid JWT or unavailable identity database | User requests protected identity API | Stable 401 or 503 envelope with request ID; no Mock result | API tests, local smoke, and bound Uvicorn `/me` 401 check | Passed locally |
| AC-06 | No apply authorization | Initializer or local acceptance is run | No migration, Auth-account creation, seed write, or secret output occurs | Initializer gate/preflight tests and aggregate acceptance | Passed locally |

**Acceptance environment:** Current worktree implementation is locally verified; configured database is at `0002_identity_access (head)`. The exact migration and IAM seed were separately authorized and completed on 2026-08-07. The seed ran twice; the second run preserved every row field and timestamp, with final table counts `1/4/3/4/4`. Runtime smoke verified the five IAM tables, RLS, and browser-denying posture. Real model and Mock are not involved. No Auth-account creation/update, reset, delete, downgrade, or unapproved data write was executed.

**Acceptance conclusion:** All B1.1 acceptance criteria passed. Main specifications are synchronized and the change is archived.

| Type | Content | Impact / decision | Status |
|---|---|---|---|
| Constraint | Demo Auth users must already exist in Supabase | Initializer accepts UUID mappings only; it never handles credentials | Confirmed |
| Constraint | Real database writes need explicit approval | Local implementation and non-mutating checks may proceed; runtime acceptance waits | Confirmed |

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-06 | V1.0 | Confirmed B1.1 product scope, real identity flow, four-role access behavior, and no-Auth-account-creation boundary from baseline v1.1. |
| 2026-08-06 | V1.1 | Added fail-closed project binding and non-overwriting, repeatable IAM initialization requirements. |
| 2026-08-06 | V1.2 | Recorded completed local implementation and acceptance evidence, plus the authorized migration/seed and real-account runtime blocker. |
| 2026-08-07 | V1.3 | Recorded the explicitly authorized `0002_identity_access` migration and passing post-migration runtime/schema evidence; seed remains separately gated. |
| 2026-08-07 | V1.4 | Recorded the separately authorized repeatable IAM seed, exact second-run invariance, and the remaining interactive real-account matrix. |
| 2026-08-07 | V1.5 | Completed real four-account acceptance, including 4 allowed and 12 denied workspace paths; corrected mobile sign-out visibility; synchronized main specs and archived B1.1. |
