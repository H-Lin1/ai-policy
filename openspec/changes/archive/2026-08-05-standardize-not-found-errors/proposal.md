## Why

The stage 0 API contract promises one error envelope and request tracing, but an unregistered route currently returns FastAPI's default `{"detail":"Not Found"}` response. This small corrective change makes routing failures consistent with every other public API failure before later modules build on the contract.

This change belongs to `TECH-V1-S0-01` and closes a stage 0 acceptance gap without advancing the `S0.2` feature scope.

## What Changes

- Convert unregistered API routes to the existing `error.code` / `error.message` / `details` / `request_id` envelope.
- Preserve or generate `X-Request-ID` for those responses.
- Add a focused contract test for the intentionally absent legacy `POST /classify` route.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project-foundation`: the consistent API envelope and request-tracing requirement now explicitly covers unregistered routes.

## Impact

- Affects FastAPI exception registration, one backend contract test, and the `project-foundation` specification.
- Does not add a legacy route, business API, database table, dependency, model, or Mock behavior.
