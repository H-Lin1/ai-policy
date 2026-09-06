# policy-library Specification

## Purpose
Defines the first read-only policy library slice backed by verified government-source crawl records and the existing FastAPI/IAM/API contracts.
## Requirements
### Requirement: Validated government-source intake

The policy intake adapter SHALL accept only records with `crawl_status=success`, non-blank `title`, `source_url`, and `content_text`, `region_code=sz`, and an HTTPS hostname equal to `gov.cn` or ending with `.gov.cn`. It SHALL remove NUL control characters for validation, normalize line endings, verify or derive a lowercase SHA-256 over the stored UTF-8 content, and reject duplicate `(source_url, content_sha256)` candidates.

#### Scenario: Successful government record is accepted

- **WHEN** an input row has successful crawl status, Shenzhen scope, a valid `.gov.cn` source, a title, and non-empty content
- **THEN** the adapter returns a deterministic normalized record with source metadata and content hash

#### Scenario: Failed or non-government record is rejected

- **WHEN** an input row is `needs_review`, has empty content, or its source hostname is outside the government allowlist
- **THEN** the adapter rejects it with a stable validation reason and does not create a policy record

### Requirement: Immutable policy read model

The backend SHALL represent one successfully crawled policy version as one immutable policy record with a server-generated UUID, active Shenzhen region, source metadata, cleaned full text, content hash, collection time, and optional source-preserved document number, publication date, effective status, and provenance fields. The migration SHALL define restrictive foreign keys, non-blank checks, and uniqueness on `(source_url, content_sha256)` without modifying `auth.users`.

#### Scenario: Exact version is repeated

- **WHEN** the same source URL and content hash are processed again
- **THEN** the normalized identity is recognized as an exact duplicate and no second version is created

#### Scenario: Source content changes

- **WHEN** the same source URL is processed with a different content hash
- **THEN** the input is treated as a new version candidate and the previous record is not overwritten

### Requirement: Authenticated policy list and detail APIs

The backend SHALL expose `GET /api/v1/policies` and `GET /api/v1/policies/{policy_id}` behind the existing current-identity dependency. The list SHALL use one-based `page`/`page_size` and return `{items, meta}`; both endpoints SHALL restrict results to active Shenzhen scope, set `Cache-Control: no-store`, and use the shared error envelope and request ID behavior.

#### Scenario: Authorized list request

- **WHEN** an active identity with `sz` scope requests the policy list
- **THEN** the API returns typed list items and complete pagination metadata without fabricated records

#### Scenario: Unauthorized or missing detail

- **WHEN** a signed-out, wrong-scope, or unknown-record request is received
- **THEN** the API returns the existing 401, 403, or 404 error contract and no policy text is returned

### Requirement: Read-only responsive policy experience

The frontend SHALL keep `/policies` behind the existing feature and authentication guards and SHALL render list, pagination, detail, loading, empty, disabled, signed-out, denied, not-found, and service-error states using the UI1.0 visual baseline. It SHALL provide no edit, upload, approval, fake search, or inactive business controls.

#### Scenario: Enabled policy browsing

- **WHEN** an authorized user opens `/policies` and selects a record
- **THEN** the UI renders the real title/metadata/full text and an official source link without horizontal overflow at desktop and mobile widths

#### Scenario: Feature disabled or service unavailable

- **WHEN** the feature is disabled or the API fails
- **THEN** the UI renders an explicit guarded/error state and does not mount placeholder policy content

### Requirement: Non-mutating acceptance boundary

The change SHALL provide deterministic fixture validation and migration-structure tests, but SHALL NOT apply a migration, import the full CSV, seed Supabase, reset/delete data, mutate Auth, or emit sensitive configuration during normal acceptance.

#### Scenario: Acceptance is run without write authorization

- **WHEN** the local acceptance matrix executes
- **THEN** source validation, backend/frontend tests, build, smoke, runtime read-only checks, and strict OpenSpec validation pass without external data mutation

### Requirement: Explicitly authorized sample provisioning

The system SHALL provide a fail-closed operator initializer that is inspect-only by default and SHALL require separate apply and confirmation flags before applying the exact `0003_policy_library` migration or importing the deterministic 20-record fixture. The import SHALL require verified Supabase target binding, the exact revision and schema, one active Shenzhen region, RLS with no browser policies or grants, and SHALL insert missing exact records without updating or deleting existing rows.

#### Scenario: Provisioning is inspected without write flags

- **WHEN** the initializer runs without both flags for a write operation
- **THEN** it reports a stable preflight state and performs no migration or data change

#### Scenario: Fixture is imported twice

- **WHEN** the authorized fixture import runs twice against the same valid database
- **THEN** the first run inserts only missing records and the second run inserts zero records while all row values and audit timestamps remain unchanged

#### Scenario: Existing policy identity conflicts

- **WHEN** an existing UUID or source/hash identity differs from the expected fixture record
- **THEN** the initializer aborts without updating, deleting, or partially inserting policy rows

#### Scenario: Unauthorized full dataset remains closed

- **WHEN** provisioning completes under this change
- **THEN** exactly the deterministic 20-record fixture is in scope and the complete CSV remains unimported

### Requirement: Efficient authenticated policy list read path

The database-backed policy list SHALL reuse one request-scoped database session for IAM and policy reads, and a normal non-empty page SHALL execute one projected policy statement that returns exact filtered total metadata without selecting full policy text or detail-only provenance. The optimization SHALL preserve identity enforcement, ordering, filtering, pagination, list/detail response schemas, errors, and `Cache-Control: no-store`, and SHALL require no cache or database mutation.

#### Scenario: Authorized non-empty page is loaded

- **WHEN** an active Shenzhen identity requests a non-empty policy list page
- **THEN** IAM and policy reads use the same request session and the policy repository returns the page and exact total from one projected statement without loading `content_text`

#### Scenario: Requested page is beyond the final record

- **WHEN** an authorized request has an offset beyond all matching policy rows
- **THEN** the API returns an empty page with the exact filtered total using a bounded fallback count and preserves the pagination contract

#### Scenario: Performance patch is accepted

- **WHEN** acceptance runs against the configured Supabase project after `/me` primes the login path
- **THEN** at least three warm page-one requests each complete within 5 seconds with median at most 2 seconds, and a cold request completes within 15 seconds or improves at least 50 percent from the recorded baseline, without exposing sensitive values or mutating external data

### Requirement: Published-only policy visibility

The backend SHALL expose authenticated policy list and detail responses only for records whose publication status is `published` and whose region is active Shenzhen. Draft and withdrawn records SHALL remain available only through authorized administrator policy APIs.

#### Scenario: Ordinary reader sees published policies

- **WHEN** an active Shenzhen user requests the policy list or a published policy detail
- **THEN** the response contains only published records and preserves existing pagination, identity and no-store contracts

#### Scenario: Ordinary reader cannot see draft or withdrawn policy

- **WHEN** an active Shenzhen user requests a draft, withdrawn or unknown policy identifier
- **THEN** the API returns the established not-found behavior without policy content

### Requirement: Published-only policy visibility

The backend SHALL expose authenticated policy list and detail responses only for records whose publication status is `published` and whose region is active Shenzhen. Draft and withdrawn records SHALL remain available only through authorized administrator policy APIs.

#### Scenario: Ordinary reader sees published policies

- **WHEN** an active Shenzhen user requests the policy list or a published policy detail
- **THEN** the response contains only published records and preserves existing pagination, identity and no-store contracts

#### Scenario: Ordinary reader cannot see draft or withdrawn policy

- **WHEN** an active Shenzhen user requests a draft, withdrawn or unknown policy identifier
- **THEN** the API returns the established not-found behavior without policy content
