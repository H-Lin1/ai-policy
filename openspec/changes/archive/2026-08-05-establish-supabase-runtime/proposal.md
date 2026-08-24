## Why

S0.1 created a safe database and authentication boundary, but it was intentionally verified only without a real cloud dependency. The configured Supabase project now allows us to prove the connection, apply the empty foundation migration, and align JWT verification with the project's current ECC signing keys.

This change implements development-status step `S0.2` and technical plan `TECH-V1-S0-02`.

## What Changes

- Connect SQLAlchemy and Alembic to the configured Supabase PostgreSQL URI through environment configuration.
- Execute and verify the idempotent foundation migration, which creates only the `app` schema and migration bookkeeping.
- Add Supabase JWKS configuration and a cached public-key resolver for current asymmetric JWTs.
- Validate issuer, audience, expiration, subject, and roles without falling back to the deprecated Legacy HS256 secret.
- Report explicit authentication configuration or verification errors while keeping health endpoints public.
- Add tests and a repeatable evidence script for database readiness and JWT verification boundaries.

## Capabilities

### New Capabilities

- `supabase-runtime`: Defines the real database readiness, migration, and current Supabase JWT verification behavior for S0.2.

### Modified Capabilities

- None.

## Impact

- Affects backend settings, database readiness, authentication utilities, tests, migration scripts, and stage 0 documentation.
- Adds no business tables, business routes, legacy imports, model weights, or Mock data.
- Requires `DATABASE_URL` and `SUPABASE_URL`; JWT verification additionally requires the Supabase JWKS endpoint to be reachable. Secrets remain server-side and are never exposed to the frontend.
