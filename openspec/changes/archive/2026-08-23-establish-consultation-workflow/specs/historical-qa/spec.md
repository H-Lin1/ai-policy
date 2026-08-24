## MODIFIED Requirements

### Requirement: Immutable historical Q&A read model

The `0004_historical_qa` migration SHALL create only restrictive `app.historical_qa` records under active Shenzhen scope with immutable public-content identity, RLS, no browser policy/grant, and no `auth.users` mutation. A subsequent approved consultation migration MAY add a source-typed, de-identified public consultation projection while preserving the existing imported-source uniqueness and without updating existing imported historical-Q&A records.

#### Scenario: Exact imported source record is repeated

- **WHEN** an exact imported source URL and content hash are provisioned again
- **THEN** no second imported record is created and existing imported data is not updated

#### Scenario: Published consultation creates a public projection

- **WHEN** the selected consultation department's dedicated government account elects publication for an eligible replied consultation
- **THEN** exactly one immutable public-safe historical-Q&A projection is created for that consultation without a submitter or internal government identity field

### Requirement: Authenticated historical Q&A list and detail

The backend SHALL expose `GET /api/v1/qa` and `GET /api/v1/qa/{qa_id}` behind current identity. List SHALL use projected one-statement window-total pagination for non-empty pages; both endpoints SHALL scope to Shenzhen, include only imported public-safe records and published de-identified consultation projections, preserve shared errors/request ID behavior, and set `Cache-Control: no-store`.

#### Scenario: Authorized list and detail read

- **WHEN** an active Shenzhen identity requests a valid list or detail
- **THEN** it receives only approved public Q&A fields, exact pagination where applicable, and no-store headers

#### Scenario: Unauthorized, unavailable, or missing record

- **WHEN** the request lacks a valid identity/scope, the store is unavailable, or the identifier is unknown
- **THEN** existing 401/403/503/404 contracts apply without Q&A text leakage
