# Design: B1.2 Policy Sample Provisioning

## Data and Migration

The initializer binds to the configured Supabase project through the existing target-binding check. The migration path invokes Alembic with the fixed project config and exact revision `0003_policy_library`; it does not accept a caller-supplied revision or URL. The import path reads only the checked-in 20-record JSONL fixture and requires the database already to be at `0003_policy_library`.

## Write Gate and Idempotency

The default command is preflight-only. Migration requires `--apply-policy-migration --confirm`; import requires `--apply-policy-fixture --confirm`. Import acquires one transaction-scoped PostgreSQL advisory lock, verifies the revision, region, table security, fixture count, deterministic UUIDs, and source/hash identities, then inserts only missing exact records. Any identity collision or field drift aborts the transaction. Existing records are never updated.

## API and Permissions

No API contract changes. FastAPI remains the only business read boundary. `app.policy_documents` keeps RLS enabled, has no policies, and grants no privileges to `anon` or `authenticated`. All four provisioned roles continue to receive the same authenticated Shenzhen-scoped read behavior through FastAPI.

## Model and Mock Boundary

No model, Mock, search, RAG, legacy code, or complete CSV path is used. The imported rows are exactly the previously accepted fixture records.

## Failure and Rollback

CLI output contains only stable states and counts, never configuration values or policy text. Target mismatch, revision mismatch, schema drift, fixture drift, or database errors fail closed. Rollback is not automated: no downgrade or policy deletion is executed by this change.

## Verification

Unit tests cover the dual flags, target/revision/schema gates, conflict rejection, transaction rollback, first insert, and second-run no-op. Authorized runtime evidence covers the exact migration, two imports, row/timestamp invariance, RLS/no-browser-grant state, database-backed API list/detail, runtime smoke, aggregate acceptance, and strict OpenSpec validation.
