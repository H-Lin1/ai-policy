## MODIFIED Requirements

### Requirement: Authenticated policy list and detail

The backend SHALL expose `GET /api/v1/policies` and `GET /api/v1/policies/{policy_id}` behind current identity. List SHALL use projected one-statement window-total pagination for non-empty pages; both endpoints SHALL scope to Shenzhen and published policy records only, preserve shared errors/request ID behavior, and set `Cache-Control: no-store`.

#### Scenario: Authorized list and detail read

- **WHEN** an active Shenzhen identity requests a valid list or published detail
- **THEN** it receives only published policy fields, exact pagination where applicable, and no-store headers

#### Scenario: Unauthorized, unavailable, draft, withdrawn, or missing record

- **WHEN** the request lacks a valid identity/scope, the store is unavailable, or the identifier is draft, withdrawn or unknown
- **THEN** existing 401/403/503/404 contracts apply without policy text leakage

