## Why

The administrator experience currently duplicates the homepage and `/admin` workspace, exposes unnecessary classification/health entries, and lacks a controlled account-management surface. The admin workbench should live directly at `/homepage`, while account operations need server-enforced role, organization and department constraints.

## What Changes

- Render the existing administrator workbench directly at `/homepage` and remove the `/admin` frontend route.
- Reduce admin navigation to 首页、政策中心、历史问答; keep policy management, registration approvals and account management as homepage function entries.
- Add admin account list/detail/create/edit/disable/enable flows for individual, enterprise, government and admin accounts.
- Add account-management audit events and preserve historical records by using disable instead of physical deletion.
- Move registration approval frontend paths to `/registration-applications`; keep backend admin API boundaries.

## Non-Goals

- Do not physically delete users, profiles, organizations, consultations, policies or audit data.
- Do not add password reset, login-username changes, external identity providers, bulk account import, or non-admin write access.
- Do not change policy Markdown lifecycle, consultation workflow, real RAG, or ordinary role navigation beyond the admin-specific view.

## Capabilities

### New Capabilities

- `admin-home-account-management`: streamlined admin homepage and controlled account administration.

### Modified Capabilities

- `identity-access`: admin homepage routing, account management and admin-only mutations.

## Impact

- Adds admin account API/UI, audit table and migration `0008_admin_account_management`.
- Changes frontend route/navigation behavior for admin identities and removes `/admin`.
- Preserves existing account, role, organization, region, department, RLS and local JWT boundaries.
