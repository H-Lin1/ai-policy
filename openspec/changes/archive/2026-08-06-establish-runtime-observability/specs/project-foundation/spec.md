## MODIFIED Requirements

### Requirement: Consistent API envelope and request tracing

The service SHALL return application errors in one JSON shape containing a stable error code, a human-readable message, optional details, and the request ID. Every response SHALL include the request ID in the `X-Request-ID` header, preserving a valid caller-supplied ID or generating one when absent. This requirement SHALL include requests whose route is not registered and responses produced by the unhandled-error boundary. Log records emitted while serving a request SHALL carry that request's ID.

#### Scenario: Invalid request

- **WHEN** an endpoint receives an invalid request body or query value
- **THEN** it returns HTTP 422 (or the endpoint-specific 4xx status) using the standard error shape and includes the request ID header

#### Scenario: Caller supplies a request ID

- **WHEN** a client sends a valid `X-Request-ID` header
- **THEN** the response contains the same ID in both the body metadata and the `X-Request-ID` response header

#### Scenario: Unregistered API route

- **WHEN** a client requests a route that is not registered, including legacy `POST /classify`
- **THEN** the service returns HTTP 404 with error code `ROUTE_NOT_FOUND`, the standard error shape, and the request ID in both the response body and `X-Request-ID` header

#### Scenario: Unhandled failure at the error boundary

- **WHEN** an unexpected exception is converted into an HTTP 500 response outside the request-context middleware
- **THEN** the response still contains the `X-Request-ID` header matching the request ID in the error body

#### Scenario: CORS preflight short-circuits routing

- **WHEN** an allowed browser origin sends a CORS preflight request that is answered before endpoint routing
- **THEN** the response still contains `X-Request-ID`, and browser-visible API responses expose that header
