## Purpose

Provides a real Supabase runtime boundary for the demonstration platform, including repeatable empty-schema migration and verification of tokens signed by the project's current asymmetric JWT keys.

## ADDED Requirements

### Requirement: Supabase database runtime

The service SHALL read its PostgreSQL connection from a server-side `DATABASE_URL`, use that connection for readiness checks and migrations, and report database state without exposing credentials. The foundation migration SHALL be safe to run repeatedly and SHALL not create business tables.

#### Scenario: Configured Supabase database is reachable

- **WHEN** `DATABASE_URL` points to the configured Supabase PostgreSQL instance and a client requests `GET /api/v1/health/ready`
- **THEN** the service returns HTTP 200 with `status=ready` and a database check of `ok`

#### Scenario: Production database is missing or unavailable

- **WHEN** `APP_ENV=production` and the configured database cannot be connected
- **THEN** readiness returns HTTP 503 with a stable error envelope and does not claim the service is ready

#### Scenario: Foundation migration is repeated

- **WHEN** an operator runs `alembic upgrade head` more than once against the configured project
- **THEN** each run succeeds, the `app` schema remains present, and no business table is created by this change

### Requirement: Current Supabase JWT verification

When authentication is required, the service SHALL verify Supabase access tokens using the project's published JWKS/current signing keys and SHALL validate the token issuer, audience, subject, and time claims. It MUST NOT silently treat an unavailable or unverifiable token as a development principal or Mock result.

#### Scenario: Valid current Supabase token

- **WHEN** a caller sends a non-expired token signed by a key published by the configured Supabase JWKS endpoint with the expected issuer, audience, and subject
- **THEN** `GET /api/v1/me` returns the subject, email, and normalized roles

#### Scenario: JWKS or authentication configuration is missing

- **WHEN** authentication is required but `SUPABASE_URL`/JWKS configuration is absent or cannot be initialized
- **THEN** a protected endpoint returns HTTP 503 with error code `AUTH_NOT_CONFIGURED`

#### Scenario: Token is invalid, expired, or signed by an unknown key

- **WHEN** a caller sends a token that fails signature, issuer, audience, subject, or time validation
- **THEN** the protected endpoint returns HTTP 401 with error code `AUTH_INVALID` and no principal data

#### Scenario: Explicit local bypass

- **WHEN** `AUTH_REQUIRED=false` is set in development configuration
- **THEN** the protected endpoint returns a principal explicitly marked as a development bypass, without contacting Supabase
