# TECH-V1-UI-02 | Remove Stable Workspace Feature Gate

| Item | Value |
|---|---|
| Document ID | `TECH-V1-UI-02` |
| Version | `V1.0` |
| Status | Implementation complete |
| Scope | UI/runtime patch before B1.4 |
| Related steps | B1.2, B1.3 |
| OpenSpec | `2026-08-18-remove-stable-workspace-feature-gate` |

## Decision

Remove the `policy_workspace` feature flag and the frontend `FeatureGuard` runtime gate. The accepted, read-only policy library and historical Q&A pages render directly and continue to handle authentication, loading, unavailable-store, empty, and API error states in their own page components.

## Boundaries

This patch does not change database schema, API authorization, IAM, region scope, RLS, policy/Q&A data, or production mock protection. FastAPI remains the only business authorization boundary. The `mocks` feature flag remains available for experimental data and is still forced off in production. No legacy code is read or reused.

## Implementation

- Remove `enable_policy_workspace` from runtime settings and the `POLICY_WORKSPACE` registry entry.
- Remove `FeatureGuard` and `RuntimeConfigProvider` from the frontend bootstrap and policy page.
- Keep `/system/features` for the remaining `mocks` flag and its existing observability contract.
- Remove the policy feature-guard render test and add direct page rendering coverage for the un-gated policy view.

## Risk and rollback

The lost capability is operational feature-gate rollout for stable read-only workspaces. Security remains in backend IAM and database controls. Rollback is a code/spec revert only; no database operation is required.

## Acceptance

The policy page renders with the flag absent/disabled, signed-out and API failure states remain explicit, historical Q&A remains accessible, all backend/frontend tests and builds pass, Ruff passes, and OpenSpec strict validation passes.

## Verification

Backend tests, Ruff, local smoke, dependency runtime smoke, frontend tests/build, and OpenSpec strict validation passed. The policy page direct-render test confirms it shows its own loading state without `FeatureGuard`; backend feature output now contains only the remaining `mocks` flag. No migration or database write was executed.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-18 | V1.0 | Removed the stable workspace feature gate and runtime configuration bootstrap; preserved backend IAM and mock-data controls. |
