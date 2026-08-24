# stage-zero-operations Specification

## Purpose

Provides a repeatable and fail-closed operational finish for Stage 0, so its initialization, reset, smoke, and acceptance workflow does not accidentally mutate data or disclose runtime configuration.
## Requirements
### Requirement: Guarded Stage 0 initialization

The repository SHALL provide an initialization command whose default behavior is a non-mutating preflight. The command MUST NOT invoke a migration, write Supabase data, or expose a database URL, credential, JWT, token, or key unless an operator supplies both a named foundation-migration apply flag and an explicit confirmation flag. A requested migration without a configured PostgreSQL database target MUST fail before any migration subprocess starts, and the command MUST target only the approved `0001_foundation_schema` foundation revision rather than future revisions.

#### Scenario: Operator runs the default initialization command

- **WHEN** an operator runs the initialization command without an apply flag
- **THEN** it reports safe preflight state, performs no migration or data write, and does not print configuration secrets

#### Scenario: Operator omits migration confirmation

- **WHEN** an operator requests the foundation migration without the explicit confirmation flag
- **THEN** the command exits non-zero before starting Alembic or changing a database

#### Scenario: Migration target is not configured

- **WHEN** an operator supplies both migration flags but no database URL is configured
- **THEN** the command exits non-zero without spawning Alembic and without exposing a configuration value

#### Scenario: Migration target is not PostgreSQL

- **WHEN** an operator supplies both migration flags with a non-PostgreSQL database target
- **THEN** the command exits non-zero without spawning Alembic or creating a local database file

### Requirement: Non-destructive Stage 0 demo reset

The repository SHALL provide a demo-reset command that requires explicit acknowledgement and remains a no-op in Stage 0 because no business seed data or business tables are managed. The reset command MUST NOT issue database, Supabase, filesystem, or model-asset deletion/writing operations.

#### Scenario: Reset acknowledgement is absent

- **WHEN** an operator invokes the demo-reset command without its confirmation flag
- **THEN** the command exits non-zero before any mutation attempt

#### Scenario: Reset acknowledgement is present

- **WHEN** an operator invokes the demo-reset command with explicit acknowledgement
- **THEN** it reports that no Stage 0 business data exists to reset and exits successfully without mutation

### Requirement: Non-destructive Stage 0 acceptance

The repository SHALL provide one local acceptance command that runs the backend tests, Python lint, hermetic local smoke checks, all current frontend guard verifications (including the Stage 0 feature guard and B1.1 identity/role guard), the frontend production build, and strict OpenSpec validation. It MUST NOT invoke database migrations, IAM/demo seed writes, demo reset, destructive filesystem commands, Supabase writes, or legacy code. A failed constituent check MUST cause an unsuccessful aggregate result and MUST NOT be represented as a Mock success.

#### Scenario: Local acceptance runs in an unconfigured development environment

- **WHEN** a developer runs the aggregate acceptance command without external runtime configuration
- **THEN** it executes only the documented non-destructive local matrix, including all current frontend guards, and returns success only when every required check succeeds

#### Scenario: Local acceptance runs during B1.1 development

- **WHEN** a developer runs the aggregate acceptance command without authorizing external writes
- **THEN** it executes both frontend guard suites and the remaining fixed non-destructive matrix, and returns success only when every required check succeeds

#### Scenario: A constituent acceptance check fails

- **WHEN** any required local verification command returns a non-zero status
- **THEN** the aggregate acceptance command returns non-zero, continues the remaining independent checks, and identifies the failed check without printing child output or secrets

#### Scenario: Ambient runtime configuration is malformed

- **WHEN** local smoke or aggregate acceptance starts while unrelated runtime environment values are malformed
- **THEN** local smoke constructs its explicit isolated application without first creating an ambient-configured ASGI application, completes deterministically, and does not expose the malformed value or a traceback

### Requirement: Secret-safe configured runtime smoke

The configured runtime-smoke command SHALL remain a separately invoked read-only verification of the PostgreSQL database, Supabase API/database project binding, current approved schema/revision, authentication configuration, and JWKS availability. During B1.1 it MUST require Alembic revision `0002_identity_access`, exactly the five approved IAM tables (`regions`, `roles`, `organizations`, `profiles`, and `user_roles`) in the `app` schema, RLS enabled on each, no B1.1 browser policy, and no direct `anon` or `authenticated` table privilege. It MUST output stable status names only and MUST NOT expose project references, database connection strings, UUID mappings, JWTs, keys, exception text, or stack traces when configuration or an external dependency fails.

#### Scenario: Supabase targets do not prove the same project

- **WHEN** the public Supabase URL and database direct host or pooler username cannot be resolved to one matching project reference
- **THEN** runtime smoke fails closed with a stable target-binding state before representing the combined runtime as healthy

#### Scenario: Configured runtime dependency is unavailable

- **WHEN** the separately invoked runtime smoke check encounters a database, JWKS, or unexpected dependency error
- **THEN** it returns a non-zero result with a stable failure state and no secret or exception detail

#### Scenario: Foundation database state is inspected

- **WHEN** the configured PostgreSQL database is reachable during B1.1 runtime smoke
- **THEN** the check reports success only when the current revision is `0002_identity_access`, the `app` schema contains exactly the five approved IAM tables, RLS is enabled for every table, and browser policies/direct privileges are absent; all inspection queries are read-only

#### Scenario: Runtime smoke receives an unsupported argument

- **WHEN** an operator invokes configured runtime smoke with any command-line argument
- **THEN** it exits non-zero before reading runtime configuration or contacting an external dependency

