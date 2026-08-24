## MODIFIED Requirements

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
