# Design: B1.2 Policy Library

## Boundaries

The change owns a single immutable `app.policy_documents` read model, a source-validation/preflight adapter, two read APIs, and the feature-guarded frontend policy experience. FastAPI owns authentication, `sz` scope, validation, pagination, errors, and all database reads. The browser never writes `app.*`.

## Source Intake

The external CSV is parsed with a large-field-safe UTF-8 reader. NUL control characters are removed from field values for validation only; the source file is never rewritten. Accepted records require `crawl_status=success`, non-blank title/source/content, `region_code=sz`, and an HTTPS hostname equal to `gov.cn` or ending in `.gov.cn`. The adapter canonicalizes line endings in `content_text` and verifies a lowercase SHA-256 over its UTF-8 bytes. It rejects malformed dates, invalid hashes, duplicate `(source_url, content_sha256)`, and non-government hosts.

The fixture is generated from the first 20 accepted rows in source order, preserving source line numbers in a local manifest. It is used by tests and local rendering only; it is not a database seed.

## Database and Migration

Add `app.policy_documents` with a server-generated UUID, active-region FK, source metadata, cleaned full text, content hash, source-provenance fields, UTC audit timestamps, restrictive checks, a unique source/hash pair, and list/detail indexes. The migration is source-defined and structurally tested only. It is not run against the configured Supabase database in this change.

## API

`GET /api/v1/policies` uses `PaginationParams`, optional bounded `q`, current identity, `sz` scope, and `PageResponse[PolicyListItem]`. `GET /api/v1/policies/{id}` returns `PolicyDetail`. Both are no-store, authenticated, read-only, and document shared errors/OpenAPI metadata. A repository abstraction keeps test fixtures independent of external database state.

## Frontend

Keep `/policies` behind `FeatureGuard` and the existing Auth/IAM boundary. Render list items, pagination, detail text, official source links, loading, empty, disabled, signed-out, denied, not-found, and service-error states. Do not add edit, upload, fake search, or inactive controls. Use a route-level detail path under the existing shell and maintain the UI1.0 mobile no-overflow contract.

## Permissions

All active identities with `sz` region may read the B1.2 library. `individual`, `enterprise`, `government`, and `admin` have the same read-only behavior. No role receives write authority from this change. The decision is intentionally narrower than future policy editing and role-specific visibility requirements.

## Failure and Rollback

Source failures are rejected locally with stable reasons. API errors use the existing envelope and request ID. No error exposes credentials, SQL, DSN, paths, or stack traces. Rollback removes the module, route, fixture, migration source, tests, and documents; no downgrade or delete is automated.
