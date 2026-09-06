## 1. Migration and models

- [x] 1.1 Add `0008_admin_account_management` audit table, indexes, RLS and browser privilege boundary.
- [x] 1.2 Add account-management ORM models, bounded schemas and repository/service tests.

## 2. Backend

- [x] 2.1 Move admin homepage behavior to `/homepage`, remove `/admin` route mapping and simplify admin navigation.
- [x] 2.2 Implement admin account list/detail/create/update/disable/enable APIs with role/organization/department constraints and audit events.
- [x] 2.3 Move registration approval frontend paths and preserve policy-management special entry/API boundaries.

## 3. Frontend

- [x] 3.1 Add admin homepage overview and function entries for accounts, registration approvals and policy management.
- [x] 3.2 Add account list/detail/forms, filters, edit and disable/enable confirmation states.
- [x] 3.3 Add responsive/accessibility render tests and remove admin classification/health/navigation entries.

## 4. Verification

- [x] 4.1 Run backend tests, Ruff, frontend tests/build and strict OpenSpec validation.
- [x] 4.2 Apply `0008` to authorized standalone PostgreSQL and run end-to-end admin account lifecycle and permission acceptance.
- [x] 4.3 Update PRD/TECH/DEVELOPMENT_STATUS evidence and archive after all tasks pass.
