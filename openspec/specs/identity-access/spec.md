# identity-access Specification

## Purpose
Provide a database-backed identity and authorization boundary for the first business vertical slice. Supabase Auth proves the caller's identity; FastAPI owns application profile, role, organization, and Shenzhen region scope.
## Requirements
### Requirement: Restrictive IAM schema boundary

Revision `0002_identity_access` SHALL create only the five approved IAM tables with deterministic dependency order, lowercase non-blank codes, non-blank human-readable values, UTC timestamps, and restrictive foreign keys. It MUST enable RLS on every table, revoke direct `anon` and `authenticated` privileges, create no browser policy, and leave `auth.users` unmodified. The Alembic environment MUST reject an upgrade when the standard Supabase API host and database direct host or pooler username do not resolve to the same project.

#### Scenario: Migration target binding is absent or mismatched

- **WHEN** an operator invokes Alembic with unresolved or different Supabase API/database project references
- **THEN** the migration environment exits before opening a migration transaction and reports only a stable configuration error without printing either target

#### Scenario: IAM migration source is inspected

- **WHEN** the B1.1 migration is validated without connecting to configured Supabase
- **THEN** table order, checks, restrictive foreign keys, reverse downgrade order, RLS, browser privilege revocation, and absence of Auth-table mutation are all verifiable

### Requirement: Database-backed current identity

The service SHALL resolve `GET /api/v1/me` from the verified bearer-token subject and active records in `app.profiles`, `app.user_roles`, `app.roles`, `app.regions`, and `app.organizations`. JWT role claims, browser state, and Mock records MUST NOT grant business access. The response MUST use the shared error envelope, request ID behavior, and `Cache-Control: no-store`.

#### Scenario: Provisioned user reads current identity

- **WHEN** a caller presents a valid Supabase JWT whose subject has an active profile, active `sz` region, active organization when applicable, and at least one active role
- **THEN** `GET /api/v1/me` returns the database-owned user, display name, region, organization scope, and role summaries with HTTP 200 and no-store caching

#### Scenario: Token claims disagree with database roles

- **WHEN** a valid JWT claims an administrator role but the active database assignment is only `individual`
- **THEN** `/api/v1/me` reports only the database role and an administrator workspace request returns HTTP 403 `ROLE_FORBIDDEN`

#### Scenario: Identity is not provisioned

- **WHEN** a valid JWT subject has no active application profile, no active role, or a disabled profile/region/organization
- **THEN** the protected identity endpoint returns HTTP 403 with a stable code (`PROFILE_NOT_PROVISIONED`, `ROLE_NOT_ASSIGNED`, or the applicable inactive-scope code), a request ID, and no record details or traceback

#### Scenario: Identity store is unavailable

- **WHEN** JWT verification succeeds but the identity database is unconfigured, unreachable, or raises an unexpected query error
- **THEN** the endpoint returns HTTP 503 with a stable identity-store code and no SQL, URL, UUID list, or exception text

#### Scenario: Development bypass remains explicit

- **WHEN** authentication bypass is explicitly enabled in a non-production environment and a caller requests `/me`
- **THEN** the service returns a clearly marked local development principal without querying the identity database; production bypass remains rejected with HTTP 503

### Requirement: Server-enforced role workspace access

The service SHALL provide `GET /api/v1/iam/workspaces/{role}` for exactly `individual`, `enterprise`, `government`, and `admin`. It MUST resolve the current database identity for every request and MUST enforce the requested role server-side, independent of frontend route state or JWT role claims.

#### Scenario: User enters the assigned workspace

- **WHEN** a provisioned user requests the workspace matching one of its active database roles
- **THEN** the service returns HTTP 200 with stable workspace and region/organization scope metadata, a request ID, and no-store caching

#### Scenario: User requests another role workspace

- **WHEN** a provisioned user requests a workspace for a role not assigned in `app.user_roles`
- **THEN** the service returns HTTP 403 `ROLE_FORBIDDEN` using the shared error envelope and does not return protected workspace content

#### Scenario: Workspace role is unsupported

- **WHEN** a caller requests a workspace with a role code outside the four registered codes
- **THEN** the service returns a validation error before any business data is read and does not silently map the request to another role

### Requirement: Guarded IAM seed initialization

The repository SHALL provide an IAM initialization command whose default behavior is a non-mutating preflight. A write path MUST require both `--apply-iam-seed` and `--confirm`, a configured PostgreSQL target whose database host or pooler username resolves to the same project as the Supabase API URL, the approved IAM migration revision, and four distinct valid existing Supabase Auth user UUID mappings. The mappings MUST be loaded through the same server-side Settings source as the remaining runtime configuration, including configured `.env` files and process-environment precedence; they MUST NOT require an additional shell export or enter frontend configuration. All preconditions and writes MUST run on one transaction-scoped, initializer-locked connection. The command MUST insert missing deterministic records, treat exact existing initializer records as a no-op, and fail before mutation on any ID/code collision, non-demo or disabled profile, role conflict, or prior-mapping drift. It MUST NOT overwrite or reactivate records, create Auth users, accept passwords, run Alembic, delete data, or print UUIDs, credentials, URLs, JWTs, keys, or exception text.

#### Scenario: Operator runs IAM initialization without apply approval

- **WHEN** the command is invoked without the named apply flag and confirmation
- **THEN** it reports safe preflight state, performs no database/Auth/filesystem write, and exits successfully or with a safe configuration status without printing configuration values

#### Scenario: Operator omits one approval

- **WHEN** the apply flag or confirmation flag is missing
- **THEN** the command exits non-zero before opening a database or spawning an external process

#### Scenario: Seed target or UUID mapping is unsafe

- **WHEN** both flags are present but the target is non-PostgreSQL, the API/database project binding is absent or mismatched, the migration revision is not current, a UUID is missing/invalid/duplicated, or required configuration is absent
- **THEN** the command exits non-zero before a write transaction and reports only a stable failure state

#### Scenario: UUID mappings are configured in the server environment file

- **WHEN** all four mappings exist only in the configured server-side `.env` source and are not separately exported into the invoking shell
- **THEN** the confirmed initializer resolves them through Settings, applies the same UUID/distinctness gates, and never copies or reports them through frontend configuration or command output

#### Scenario: Existing data conflicts with deterministic seed ownership

- **WHEN** a fixed ID/code is paired with different values, a supplied UUID already owns a non-demo or disabled profile, a conflicting role exists, or a prior demo mapping uses another UUID
- **THEN** the locked transaction performs no insert/update/reactivation and reports a stable conflict state without exposing record values

#### Scenario: Authorized seed is repeated

- **WHEN** an operator explicitly authorizes the seed against the approved PostgreSQL revision with valid existing Auth UUID mappings
- **THEN** one locked transaction inserts only missing deterministic roles, `sz`, organizations, profiles, and role assignments; an identical second execution changes no row or timestamp and exposes no values

### Requirement: Frontend session and role guard

The frontend SHALL use the configured Supabase Auth client for session restore, sign-in, and sign-out, and SHALL call the backend identity/workspace APIs with the current access token. It MUST distinguish loading, signed-out, missing configuration, identity failure, denied, and allowed states; protected role content MUST render only after backend authorization succeeds.

#### Scenario: Signed-out visitor opens a protected role route

- **WHEN** no Supabase session exists and the visitor opens `/personal`, `/enterprise`, `/government`, or `/admin`
- **THEN** the frontend shows the sign-in state and does not render protected workspace content or fabricated identity data

#### Scenario: Session identity request fails

- **WHEN** a session exists but `/me` or the matching workspace endpoint fails
- **THEN** the frontend shows a recoverable identity/error state with retry and clears stale protected content

#### Scenario: Backend denies a role route

- **WHEN** the session is valid but the backend returns HTTP 403 for the requested role workspace
- **THEN** the frontend shows an explicit access-denied state and does not mount that role's content

#### Scenario: Backend authorizes a role route

- **WHEN** `/me` and the matching workspace endpoint both succeed for an assigned role
- **THEN** the frontend renders the role workspace with the database identity and scope summary, without exposing tokens or direct `app.*` database access

### Requirement: Role-aware authenticated routing

The frontend SHALL route authenticated administrators to `/homepage`, where the admin workbench is rendered directly. The legacy `/admin` frontend route SHALL not exist; ordinary individual, enterprise and government role routes retain their existing authorization behavior.

#### Scenario: Admin login destination

- **WHEN** an admin completes local login or opens the authenticated root
- **THEN** navigation lands on `/homepage` and renders the admin workbench

#### Scenario: Legacy admin path is unavailable

- **WHEN** any caller opens `/admin`
- **THEN** the frontend renders its normal not-found behavior and does not expose the admin workbench through that path
