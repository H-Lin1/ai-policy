## Context

The current frontend uses `/admin` as the admin role workspace, while `/homepage` is a separate identity-aware landing route. Existing local PostgreSQL identity tables are relational and use restrictive foreign keys; consultation departments enforce one government account per department. Registration approval and policy management already expose admin-only backend APIs under `/api/v1/admin/...`.

## Decisions

### Admin homepage routing

`WorkspaceHomePage` becomes the single authenticated homepage. When identity includes `admin`, it renders the former admin workspace content directly. The `/admin` route and role path mapping are removed; admin login and root navigation land on `/homepage`. Admin navigation contains only 首页、政策中心、历史问答. Function cards on `/homepage` link to `/account-management`, `/registration-applications` and `/policy-management`.

### Account data and lifecycle

Migration `0008_admin_account_management` adds `account_management_events`. Existing `users`, `profiles`, `user_roles`, `organizations` and `consultation_departments` remain the source of truth. Disable sets users inactive, profiles disabled and role assignments inactive; enable revalidates scope and constraints. No physical delete endpoint exists.

### Server-owned account operations

Create operations use separate request models for individual, enterprise, government and admin. Enterprise may bind an existing active enterprise organization or create one; government must select an unoccupied active department; admin must bind the platform organization. Update does not accept login username or raw role/organization structures; role changes are explicit server-validated operations in the bounded update contract.

### API and privacy

Admin endpoints use existing identity resolution and require `admin`. Lists are paginated and filterable by role/status/keyword. Responses omit passwords, hashes, JWTs and full sensitive contacts. All mutations use the shared error envelope, request IDs and no-store. Audit summaries contain only safe field names and before/after labels.

### Migration and rollback

The migration is PostgreSQL-only, enables RLS on the audit table and revokes browser privileges in non-standalone mode. It creates no demo accounts and changes no existing data. Rollback is route disablement or forward correction; no approved account is automatically deleted.

## Migration Plan

1. Implement migration, account service/router, frontend admin homepage and account pages with tests.
2. Apply `0008` only to authorized local standalone PostgreSQL.
3. Verify admin homepage, removed `/admin`, role/status filters, create/update/disable/enable, organization/department constraints, audit and non-admin denial.
4. Update evidence and archive.

## Risks / Trade-offs

- Disable rather than delete preserves referential integrity and auditability but requires explicit re-enable semantics.
- Account role edits are powerful; bounded schemas and server-side constraints prevent arbitrary privilege injection.
- A single government account per department remains the confirmed operating rule.
