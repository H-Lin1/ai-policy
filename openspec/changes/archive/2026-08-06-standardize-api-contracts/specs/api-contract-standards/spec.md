## Purpose

Defines one small, testable HTTP contract for every current and future V1 API so frontend code and backend modules agree on versioned paths, errors, pagination, and UTC datetimes before business features are added.

## ADDED Requirements

### Requirement: Versioned and discoverable API contract

The service SHALL expose all business and operational API routes under `/api/v1`. Its OpenAPI document SHALL publish stable operation identifiers, grouped tags, typed success models, and endpoint-specific error response models without registering legacy unversioned business routes.

#### Scenario: OpenAPI is inspected

- **WHEN** a developer opens `/openapi.json` or `/docs`
- **THEN** every registered service API path starts with `/api/v1`, each operation has a unique stable operation ID, and documented errors use the same envelope returned at runtime

#### Scenario: Legacy unversioned route is requested

- **WHEN** a caller requests an unregistered legacy business route such as `POST /classify`
- **THEN** the service returns HTTP 404 using the standard error envelope and does not expose that route in OpenAPI

### Requirement: Stable JSON error envelope

The service SHALL return expected application, validation, HTTP, and unhandled errors as JSON containing `error.code`, `error.message`, optional `error.details`, and `request_id`. Error details MUST be JSON serializable, and the body request ID MUST match the `X-Request-ID` response header.

#### Scenario: Request validation fails

- **WHEN** a request contains an invalid query, path, or body value
- **THEN** the service returns HTTP 422 with code `VALIDATION_ERROR`, serializable field details, and the same request ID in the body and response header

#### Scenario: HTTP method is not allowed

- **WHEN** a caller uses an unsupported method on a registered path
- **THEN** the service returns HTTP 405 with code `METHOD_NOT_ALLOWED` in the standard error envelope and preserves the protocol `Allow` header

#### Scenario: Unexpected server failure occurs

- **WHEN** an unexpected exception reaches the API boundary
- **THEN** the service returns HTTP 500 with code `INTERNAL_ERROR`, does not expose stack traces or secrets, and includes the request ID

### Requirement: Page-based list contract

List endpoints SHALL use one-based `page` and `page_size` query parameters, defaulting to page 1 and 20 items, with a maximum page size of 100. Paged responses SHALL contain `items` and `meta`; `meta` SHALL contain `page`, `page_size`, `total`, `total_pages`, `has_next`, and `has_previous`.

#### Scenario: Caller omits pagination values

- **WHEN** a caller requests a paged list without `page` or `page_size`
- **THEN** the endpoint uses `page=1` and `page_size=20` and returns matching pagination metadata

#### Scenario: Caller requests an invalid page

- **WHEN** `page` is below 1 or `page_size` is below 1 or above 100
- **THEN** the endpoint returns HTTP 422 using the standard validation error envelope

#### Scenario: List has no matching records

- **WHEN** a valid paged query has zero matching records
- **THEN** `items` is empty, `total=0`, `total_pages=0`, and both navigation flags are false

### Requirement: UTC datetime contract

API datetime fields governed by the shared datetime contract SHALL require timezone-aware input, normalize accepted offsets to UTC, and serialize responses as RFC 3339 strings ending in `Z`. Database timestamps remain UTC and timezone conversion for display belongs to the frontend.

#### Scenario: Aware datetime with a non-UTC offset is accepted

- **WHEN** a caller supplies a valid timezone-aware datetime such as `2026-08-06T08:00:00+08:00`
- **THEN** the validated API value represents the same instant in UTC and serializes as `2026-08-06T00:00:00Z`

#### Scenario: Naive datetime is rejected

- **WHEN** a caller supplies a datetime without timezone information to a field using the shared UTC contract
- **THEN** validation fails instead of guessing a local timezone
