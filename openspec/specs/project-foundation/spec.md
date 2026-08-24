# project-foundation Specification

## Purpose
为后续政策、问答、咨询和智能能力提供一个可以在新机器上重复启动、检查和继续扩展的最小工程底座，并让前后端、配置、权限、错误处理和运行状态在不同开发对话中保持一致。 This capability is the repeatable operational foundation for the demonstration project.
## Requirements
### Requirement: Versioned service health

The service SHALL expose public live and readiness checks under the `/api/v1` prefix. The live check MUST only indicate that the process and routing layer are running. The readiness check MUST report dependency state explicitly and MUST NOT claim full readiness when a configured database is unavailable.

#### Scenario: Live check without external dependencies

- **WHEN** a client sends `GET /api/v1/health/live`
- **THEN** the service returns HTTP 200 with a JSON status of `ok` and a service/version identifier

#### Scenario: Database is not configured for local development

- **WHEN** a client sends `GET /api/v1/health/ready` with no database URL in development mode
- **THEN** the service returns HTTP 200 with an explicit degraded/not-configured database check and does not label the database as ready

#### Scenario: Configured database cannot be reached

- **WHEN** a client sends `GET /api/v1/health/ready` and the configured database connectivity check fails
- **THEN** the service returns a non-ready status with HTTP 503 and a stable error/request identifier

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

### Requirement: Protected business API boundary

The service SHALL keep health checks public and SHALL require a valid bearer token for protected business endpoints when authentication is enabled. Missing, malformed, expired, or unverifiable tokens MUST produce explicit 401/503 errors and MUST NOT be replaced by mock business data.

#### Scenario: Missing token on protected endpoint

- **WHEN** authentication is enabled and a client calls `GET /api/v1/me` without a bearer token
- **THEN** the service returns HTTP 401 with error code `AUTH_REQUIRED`

#### Scenario: Invalid token on protected endpoint

- **WHEN** authentication is enabled and a client calls `GET /api/v1/me` with an invalid or expired bearer token
- **THEN** the service returns HTTP 401 with a stable authentication error and request ID

#### Scenario: Local development bypass is explicitly enabled

- **WHEN** authentication is disabled through the local development configuration
- **THEN** the protected endpoint returns a clearly marked development principal and the response indicates that the bypass is not suitable for the demonstration deployment

### Requirement: Reproducible project shell

The repository SHALL provide documented commands to install dependencies, start the frontend and backend separately, run checks, apply the approved foundation migration through an explicitly confirmed operator action, perform a non-destructive Stage 0 demo reset acknowledgement, and execute local smoke and aggregate Stage 0 acceptance checks. The frontend SHALL provide a working root route and a service-status route, and SHALL display a recoverable connection error when the API is unavailable. The aggregate local acceptance command MUST NOT perform migrations, resets, Supabase writes, or legacy-code imports.

#### Scenario: Fresh checkout starts without legacy assets

- **WHEN** a developer follows the README from a fresh checkout with the documented runtime versions
- **THEN** the frontend build, backend import, and backend smoke check complete without requiring files from the legacy `backend/` directory

#### Scenario: API is unavailable from the browser

- **WHEN** the frontend service-status page cannot reach its configured API base URL
- **THEN** it displays an error and retry action rather than a fabricated healthy result

#### Scenario: Developer runs local Stage 0 acceptance

- **WHEN** a developer runs the documented aggregate Stage 0 acceptance command in a local unconfigured environment
- **THEN** it runs only non-destructive checks and reports failure if any required test, lint, smoke, frontend, or strict-spec validation check fails

### Requirement: Environment-safe configuration

Runtime paths, database URLs, Supabase settings, CORS origins, model paths, feature flags, and external service credentials SHALL be supplied through environment configuration. Secrets MUST NOT be committed to source code or exposed in frontend build variables.

#### Scenario: Missing optional local dependency

- **WHEN** a developer starts the backend without configuring Supabase or model paths in development mode
- **THEN** the process starts with explicit degraded readiness information and logs the missing dependency without crashing during module import
