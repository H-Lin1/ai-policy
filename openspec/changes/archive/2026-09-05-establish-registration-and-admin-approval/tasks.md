## 1. Migration and data contracts

- [x] 1.1 Add migration `0006_registration_applications` with application/event tables, standalone guards, checks, indexes, FKs, RLS and no browser privileges.
- [x] 1.2 Add ORM models, bounded form schemas and repositories for registration, application status and admin review.
- [x] 1.3 Add migration/source-contract tests for revision order, one-department uniqueness, RLS/revocation, no Auth writes and safe non-PostgreSQL inspection.

## 2. Backend registration and approval

- [x] 2.1 Implement individual registration with scrypt hashing, Shenzhen profile, `individual` role, duplicate protection and no token.
- [x] 2.2 Implement enterprise application/status with pending-only semantics and duplicate credit-code protection.
- [x] 2.3 Implement government application/status with directory lock/re-read and one-department guard.
- [x] 2.4 Implement admin list/detail/approve/reject APIs with authorization, redaction, filters, mandatory rejection reason, transactions, locks, idempotency and audit events.
- [x] 2.5 Add backend tests for validation, privacy, authorization, rollback, concurrent decisions, activation and IAM/consultation regressions.

## 3. Frontend registration and admin workbench

- [x] 3.1 Add role-aware login links and `/register` routes for all three forms with explicit states.
- [x] 3.2 Add `/registration-status` with non-enumerating verification and status presentation.
- [x] 3.3 Add independent admin list/detail routes, filters, redaction, approve/reject dialogs, responsive/accessibility states.
- [x] 3.4 Add frontend render tests for forms, government directory selection, admin-only UI and mobile layout.
- [x] 3.5 Center all registration cards, replace successful individual registration with immediate/three-second login navigation, add the secondary public administrator entry, and record desktop/mobile browser measurements.

## 4. Verification and documentation

- [x] 4.1 Run backend tests, Ruff, frontend tests/build, local smoke and strict OpenSpec validation without database/Auth writes.
- [x] 4.2 After explicit authorization, run guarded migration and standalone runtime acceptance for individual register/login, enterprise/government submit, admin approve/reject, approved login, department conflict, audit and privacy.
- [x] 4.3 Update TECH/PRD, `DEVELOPMENT_STATUS.md`, API docs and evidence; archive only after completion.
