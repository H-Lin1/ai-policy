# TECH-V1-B1-08-M | Admin homepage consolidation and account management

| Item | Value |
|---|---|
| Step | B1.8 / B18-010、B18-011 |
| Version / status | V1.0 / Accepted |
| PRD | [`PRD-V1-B1-08-ADMIN-HOMEPAGE-AND-ACCOUNTS`](./PRD-V1-B1-08-ADMIN-HOMEPAGE-AND-ACCOUNTS.md) |
| OpenSpec | `2026-09-06-refine-admin-home-and-account-management` |
| Migration | `0008_admin_account_management` |

## Architecture and routing

`/homepage` is the only authenticated homepage. It selects an admin workbench when the database identity includes `admin`; `/admin` is not registered. Admin navigation contains only 首页、政策中心、历史问答. Account management, registration approvals and policy management are homepage cards routed to `/account-management`, `/registration-applications` and `/policy-management`; backend APIs retain `/api/v1/admin/...` authorization boundaries.

## Account data and API

The existing users/profiles/user_roles/organizations/consultation_departments tables remain authoritative. Migration `0008` adds optional contact phone/job title to local users and an RLS-protected append-only account-management audit table. Admin APIs provide counts, filtered/paginated list, detail, role-specific create, bounded update and disable/enable.

Create/update operations validate Shenzhen region, enterprise/platform organization type and one-government-account-per-department. Login username is immutable. Disable deactivates user/profile/roles without deleting rows; enable restores only the latest intended role after revalidating organization/department scope. The current admin cannot disable itself or remove its own admin role.

## Verification

Authorized local acceptance applied `0008` to `aipolicy_local`; created individual, enterprise and admin accounts; edited, disabled and re-enabled an individual; verified disabled login failure and restored login; rejected current-admin self-disable, occupied government department and non-admin access; and confirmed audit events. Browser checks at 1440px and 390px verified `/homepage`, exactly three navigation items, three management cards, `/admin` 404 and zero horizontal overflow on account inventory.
