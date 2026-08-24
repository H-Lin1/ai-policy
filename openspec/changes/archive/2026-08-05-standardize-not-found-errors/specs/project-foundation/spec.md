## MODIFIED Requirements

### Requirement: Consistent API envelope and request tracing

The service SHALL return application errors in one JSON shape containing a stable error code, a human-readable message, optional details, and the request ID. Every response SHALL include the request ID in the `X-Request-ID` header, preserving a valid caller-supplied ID or generating one when absent. This requirement SHALL include requests whose route is not registered.

#### Scenario: Invalid request

- **WHEN** an endpoint receives an invalid request body or query value
- **THEN** it returns HTTP 422 (or the endpoint-specific 4xx status) using the standard error shape and includes the request ID header

#### Scenario: Caller supplies a request ID

- **WHEN** a client sends a valid `X-Request-ID` header
- **THEN** the response contains the same ID in both the body metadata and the `X-Request-ID` response header

#### Scenario: Unregistered API route

- **WHEN** a client requests a route that is not registered, including legacy `POST /classify`
- **THEN** the service returns HTTP 404 with error code `ROUTE_NOT_FOUND`, the standard error shape, and the request ID in both the response body and `X-Request-ID` header
