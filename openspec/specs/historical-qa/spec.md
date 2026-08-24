# historical-qa Specification

## Purpose
TBD - created by archiving change 2026-08-11-establish-historical-qa. Update Purpose after archive.
## Requirements
### Requirement: Privacy-screened Shenzhen historical Q&A intake

The system SHALL map only approved public-safe fields from the user-provided adjudicated Shenzhen government Q&A CSVs, reject non-government HTTPS sources, missing mandatory text, duplicate normalized source/content identities, malformed dates, and records matching registered sensitive patterns. It SHALL not persist or expose source receipt IDs, nicknames, or adjudication rationale.

#### Scenario: Valid public Q&A record is accepted

- **WHEN** an adjudicated source record has valid public-safe text, HTTPS `.gov.cn` source, valid metadata, unique identity, and no registered sensitive pattern
- **THEN** the adapter returns a deterministic normalized record without user identity fields

#### Scenario: Potentially sensitive or invalid source record is rejected

- **WHEN** a record contains a registered sensitive pattern, an invalid source, missing mandatory text, malformed date, or duplicate identity
- **THEN** it is rejected with a stable local reason and no historical Q&A row is created

### Requirement: Immutable historical Q&A read model

The `0004_historical_qa` migration SHALL create only restrictive `app.historical_qa` records under active Shenzhen scope with immutable `(source_url, content_sha256)` uniqueness, RLS, no browser policy/grant, and no `auth.users` mutation. A subsequent approved consultation workflow MAY add a one-to-one source-typed, de-identified public consultation projection while preserving imported-source uniqueness and without updating existing imported records.

#### Scenario: Exact source record is repeated

- **WHEN** an exact source URL and content hash are provisioned again
- **THEN** no second record is created and existing data is not updated

#### Scenario: Published consultation creates a public projection

- **WHEN** the selected consultation department's dedicated government account elects publication for an eligible replied consultation
- **THEN** exactly one immutable public-safe historical-Q&A projection is created for that consultation without submitter or internal government identity fields

### Requirement: Authenticated historical Q&A list and detail

The backend SHALL expose `GET /api/v1/qa` and `GET /api/v1/qa/{qa_id}` behind current identity. List SHALL use projected one-statement window-total pagination for non-empty pages; both endpoints SHALL scope to Shenzhen, include imported public-safe records and published de-identified consultation projections, preserve shared errors/request ID behavior, and set `Cache-Control: no-store`.

#### Scenario: Authorized list and detail read

- **WHEN** an active Shenzhen identity requests a valid list or detail
- **THEN** it receives only approved Q&A fields, exact pagination where applicable, and no-store headers

#### Scenario: Unauthorized, unavailable, or missing record

- **WHEN** the request lacks a valid identity/scope, the store is unavailable, or the identifier is unknown
- **THEN** existing 401/403/503/404 contracts apply without Q&A text leakage

### Requirement: Guarded historical Q&A experience

The frontend SHALL add guarded `/qa` and `/qa/{qa_id}` views in the visual baseline with real list/detail, pagination, source link, and explicit loading/empty/error states. It SHALL provide no chatbot, semantic search, edit, import, or approval control.

#### Scenario: Enabled Q&A browsing

- **WHEN** an authorized user opens the Q&A route and selects a record
- **THEN** the UI renders permitted real source content without horizontal overflow at desktop and mobile widths
