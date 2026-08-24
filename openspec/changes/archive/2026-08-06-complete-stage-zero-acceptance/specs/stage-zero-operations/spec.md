## Purpose

Provides a repeatable and fail-closed operational finish for Stage 0, so its initialization, reset, smoke, and acceptance workflow does not accidentally mutate data or disclose runtime configuration.

## ADDED Requirements

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

The repository SHALL provide one local Stage 0 acceptance command that runs the backend tests, Python lint, hermetic local smoke checks, frontend feature-guard verification, frontend production build, and strict OpenSpec validation. It MUST NOT invoke database migrations, demo reset, destructive filesystem commands, Supabase writes, or legacy code. A failed constituent check MUST cause an unsuccessful aggregate result and MUST NOT be represented as a Mock success.

#### Scenario: Local acceptance runs in an unconfigured development environment

- **WHEN** a developer runs the Stage 0 acceptance command without external runtime configuration
- **THEN** it executes only the documented non-destructive local matrix and returns success only when every required check succeeds

#### Scenario: A constituent acceptance check fails

- **WHEN** any required local verification command returns a non-zero status
- **THEN** the aggregate acceptance command returns non-zero and identifies the failed check without printing secrets

#### Scenario: Ambient runtime configuration is malformed

- **WHEN** local smoke or aggregate acceptance starts while unrelated runtime environment values are malformed
- **THEN** local smoke constructs its explicit isolated application without first creating an ambient-configured ASGI application, completes deterministically, and does not expose the malformed value or a traceback

### Requirement: Secret-safe configured runtime smoke

The configured runtime-smoke command SHALL remain a separately invoked read-only verification of the PostgreSQL database, the Stage 0 foundation schema/revision and zero-business-table invariant, authentication configuration, and JWKS availability. It MUST output stable status names only and MUST NOT expose database connection strings, JWTs, keys, exception text, or stack traces when configuration or an external dependency fails.

#### Scenario: Configured runtime dependency is unavailable

- **WHEN** the separately invoked runtime smoke check encounters a database, JWKS, or unexpected dependency error
- **THEN** it returns a non-zero result with a stable failure state and no secret or exception detail

#### Scenario: Foundation database state is inspected

- **WHEN** the configured PostgreSQL database is reachable during runtime smoke
- **THEN** the check reports success only when the `app` schema exists, the approved `0001_foundation_schema` revision is present, and no Stage 0 business table exists; the queries do not write data

#### Scenario: Runtime smoke receives an unsupported argument

- **WHEN** an operator invokes configured runtime smoke with any command-line argument
- **THEN** it exits non-zero before reading runtime configuration or contacting an external dependency
