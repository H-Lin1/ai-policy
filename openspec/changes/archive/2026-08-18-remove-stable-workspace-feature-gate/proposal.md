# Proposal: Remove Stable Workspace Feature Gate

## Why

The accepted policy library is still hidden by the `policy_workspace` frontend release gate. This gate adds a runtime dependency and blocks a stable read-only workspace that already has IAM, API, and database protections.

## What Changes

- Remove the policy workspace feature flag from runtime configuration and feature registry.
- Remove the frontend `FeatureGuard` and runtime configuration bootstrap.
- Let the policy and historical Q&A pages expose their own explicit auth/loading/error states.
- Preserve backend authorization, region scope, RLS, no-store contracts, and the experimental mocks gate.

## Non-goals

- No database migration or data changes.
- No API authorization change, Auth write, feature flag for mocks change, or legacy code reuse.
- No implementation of B1.4 classification or later retrieval capabilities.
