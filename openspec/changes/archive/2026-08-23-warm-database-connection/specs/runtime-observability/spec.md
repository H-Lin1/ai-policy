## ADDED Requirements

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
