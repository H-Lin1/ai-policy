# runtime-observability Specification

## Purpose
Makes the running service observable and controllable before business features exist, by defining how logs are structured and correlated to requests, what liveness and readiness actually promise, and how backend-owned feature flags gate both API exposure and frontend routes.
## Requirements
### Requirement: Correlated structured logging

The service SHALL emit single-line JSON log records containing at least a timestamp, level, logger name, message, and request ID. Every record produced while serving a request SHALL carry that request's ID regardless of which logger emitted it, and records produced outside a request SHALL use an explicit placeholder. Sensitive values such as authorization headers, bearer tokens, passwords, secrets, API keys, cookies, and database connection strings MUST be redacted rather than logged.

#### Scenario: Application logger emits a record during a request

- **WHEN** a logger other than the access-log middleware emits a record while a request is being served
- **THEN** the record carries the same request ID as that request's access log record

#### Scenario: Log record contains a sensitive field

- **WHEN** a log record includes a field whose name identifies a credential, token, secret, cookie, or database URL
- **THEN** the emitted record replaces that value with a redaction placeholder and never contains the original value

#### Scenario: Sensitive value reaches a message or exception

- **WHEN** a common credential representation reaches a nested value, log message, object representation, or formatted exception trace
- **THEN** both JSON and text output replace the sensitive value before emitting the record

#### Scenario: Service runs under Uvicorn

- **WHEN** the API is started by Uvicorn
- **THEN** lifecycle records use the configured structured formatter and per-request access is emitted only by the correlated application access logger

#### Scenario: Record is emitted outside any request

- **WHEN** a startup, shutdown, or background record is emitted with no active request
- **THEN** the record is still valid JSON and uses an explicit non-request request-ID placeholder

### Requirement: Request ID on every response

Every HTTP response SHALL include the `X-Request-ID` header, and any response using the standard error envelope SHALL report the same identifier in the header and in the body. This SHALL include unhandled server failures whose response is produced outside the request-context middleware.

#### Scenario: Unhandled exception reaches the API boundary

- **WHEN** an endpoint raises an unexpected exception
- **THEN** the service returns HTTP 500 with the standard error envelope, and the `X-Request-ID` header matches the body request ID

#### Scenario: Caller supplies a request ID on a failing request

- **WHEN** a client sends a valid `X-Request-ID` header and the request fails
- **THEN** the error body and the `X-Request-ID` response header both contain the supplied identifier

#### Scenario: Browser sends a CORS preflight request

- **WHEN** an allowed browser origin sends a CORS preflight request before the API route executes
- **THEN** the preflight response still contains `X-Request-ID`, and browser-visible API responses expose that header

### Requirement: Distinct liveness and readiness semantics

The liveness check SHALL report only process and routing availability and MUST NOT access the database, the authentication key endpoint, or any model. The readiness check SHALL report dependency state and the effective feature-flag snapshot. Health responses MUST NOT be cached by intermediaries.

#### Scenario: Liveness check is called

- **WHEN** a client sends `GET /api/v1/health/live`
- **THEN** the service returns HTTP 200 without performing a database, authentication-key, or model check, and the response carries a no-store cache directive

#### Scenario: Readiness check is called

- **WHEN** a client sends `GET /api/v1/health/ready`
- **THEN** the response reports dependency checks and the effective feature-flag snapshot, and carries a no-store cache directive

#### Scenario: Production enables the demonstration Mock flag

- **WHEN** the service runs in production configuration with the Mock data flag enabled
- **THEN** the readiness check reports an explicitly non-compliant flag configuration instead of reporting a compliant ready state

### Requirement: Backend-owned feature flags

Feature availability SHALL be resolved from one central flag registry sourced from environment configuration, and SHALL be readable through a public system endpoint that returns the environment name, whether authentication is required, and the flag snapshot. Unknown flag names SHALL resolve to disabled. The endpoint MUST NOT expose configuration values such as URLs, credentials, or connection strings.

#### Scenario: Client reads the feature snapshot

- **WHEN** a client sends `GET /api/v1/system/features`
- **THEN** the service returns the environment name, whether authentication is required, and a boolean flag snapshot containing no URLs, credentials, or connection strings

#### Scenario: Unknown flag is queried

- **WHEN** code resolves a flag name that is not registered
- **THEN** the resolution returns disabled instead of raising an error or defaulting to enabled

#### Scenario: Production requests the Mock data flag

- **WHEN** the Mock data flag is resolved while the service runs in production configuration
- **THEN** the flag resolves to disabled regardless of the configured value

### Requirement: Feature-flag route guard

The frontend SHALL read the backend feature snapshot at startup and SHALL gate flag-controlled routes on it. A guarded route MUST NOT render protected content while the snapshot is loading, when the flag is disabled, or when the snapshot cannot be retrieved, and MUST NOT substitute placeholder business data for a real result.

#### Scenario: Flag-controlled route is opened while the flag is disabled

- **WHEN** a user opens a guarded route and the backend snapshot reports that flag as disabled
- **THEN** the application shows an explicit not-open state and renders no protected content or placeholder business data

#### Scenario: Snapshot cannot be retrieved

- **WHEN** the frontend cannot reach the feature snapshot endpoint
- **THEN** the guarded route shows a connection error with a retry action and does not assume the feature is open

#### Scenario: Snapshot is still loading

- **WHEN** a guarded route is rendered before the snapshot resolves
- **THEN** the application shows a loading state instead of protected content

### Requirement: Startup database connection warmup is read-only and fail-safe

When a database URL is configured, the service SHALL execute one read-only `SELECT 1` probe during application startup using the same cached SQLAlchemy engine and SHALL return that connection to the existing pool before serving requests. The probe SHALL report only a safe status and duration. A failed probe SHALL NOT expose connection details or prevent the process from starting; existing readiness and request-level dependency errors SHALL remain authoritative. Database-disabled fixture and test environments SHALL skip the probe.

#### Scenario: Configured database is warmed before requests

- **WHEN** the application starts with a configured database and the read-only probe succeeds
- **THEN** one pooled connection is returned to the existing engine pool before the lifespan serves requests, and a structured lifecycle record contains only the success status and duration

#### Scenario: Database warmup fails safely

- **WHEN** the configured database cannot be reached during startup
- **THEN** the process continues starting, emits a generic warmup-failed lifecycle record without connection details, and readiness/request paths retain their existing dependency failure behavior

#### Scenario: Database is not configured

- **WHEN** the application starts in a fixture or test environment without a database URL
- **THEN** no connection or SQL probe is attempted and existing database-free behavior remains unchanged

