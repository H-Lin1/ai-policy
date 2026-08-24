# Design: Remove Stable Workspace Feature Gate

## Runtime and frontend

Policy and historical Q&A pages render directly under the existing application shell. Each page already checks the authenticated session before requesting its protected API and maps loading, empty, denied, and API failure states explicitly. The root runtime configuration provider and `FeatureGuard` become unused and are removed.

## Backend contract

`Settings.enable_policy_workspace` and the `POLICY_WORKSPACE` registry entry are removed. `/api/v1/system/features` continues to return a boolean snapshot for the remaining `mocks` flag, preserving the shared response envelope and readiness checks. No business route becomes public: `/policies`, `/qa`, and their detail endpoints continue to depend on current identity and Shenzhen scope.

## Failure and rollback

The change removes only a frontend release gate. Backend 401/403/404/503 behavior, request IDs, no-store headers, IAM, RLS, and production mock fail-closed behavior remain unchanged. Rollback is source/spec restoration and does not require a database action.
