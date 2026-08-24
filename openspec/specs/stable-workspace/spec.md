# stable-workspace Specification

## Purpose
TBD - created by archiving change 2026-08-18-remove-stable-workspace-feature-gate. Update Purpose after archive.
## Requirements
### Requirement: Stable read-only workspaces are not release-gated

The frontend SHALL render the accepted policy library and historical Q&A workspaces without depending on a `policy_workspace` feature flag or runtime feature snapshot. The workspaces SHALL preserve explicit signed-out, loading, empty, unavailable, and API error states.

#### Scenario: Policy workspace is available without feature snapshot

- **WHEN** an authenticated user opens `/policies` and the backend feature snapshot is absent or does not contain `policy_workspace`
- **THEN** the page requests the protected policy API and renders its normal list, loading, empty, or error state instead of a feature-disabled screen

### Requirement: Backend authorization remains authoritative

Removing the frontend gate SHALL NOT change backend identity, Shenzhen region scope, request ID, no-store, RLS, or browser-grant protections for policy and historical Q&A APIs.

#### Scenario: Unauthenticated request remains denied

- **WHEN** a signed-out client requests `/api/v1/policies` or `/api/v1/qa`
- **THEN** the API returns the existing authentication error contract

