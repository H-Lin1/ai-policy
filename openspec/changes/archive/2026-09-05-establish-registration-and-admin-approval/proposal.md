## Why

The three public service entrances currently support login only. The standalone PostgreSQL deployment needs safe account opening: individuals can self-register, while enterprise and government access must be reviewed before privileged identity activation.

## What Changes

- Add standalone-local individual self-registration with a server-created Shenzhen profile and `individual` role.
- Add enterprise applications; approval creates the organization, account, profile and `enterprise` role transactionally.
- Add government applications that choose one existing Shenzhen department; enforce at most one pending or active government account per department and approve transactionally.
- Add an independent admin-only application review API/UI with list/detail, approve/reject, audit, redaction, idempotency and concurrency protection.
- Add migration `0006_registration_applications`, contracts, frontend routes and regression evidence.

## Non-Goals

- Do not use Supabase Auth or another identity provider; standalone PostgreSQL local accounts are the only registration path.
- Do not add SMS/email verification, document upload, government SSO, employee invitations, multi-account department queues or self-service role changes.
- Do not create enterprise/government roles before approval, expose passwords/hashes, bypass IAM/RoleGuard/RLS, modify consultations, implement RAG, perform production rollout or destructive cleanup.

## Capabilities

### New Capabilities

- `account-registration`: individual self-registration and enterprise/government application submission/status.
- `registration-approval`: admin-only review, approval/rejection transactions and audit behavior.

## Impact

- Adds a post-`0005` standalone PostgreSQL migration and IAM ORM/repository/service/router code.
- Adds public registration/status routes and protected admin application routes.
- Adds frontend registration forms, status view and independent admin approval pages.
- Preserves local JWT, identity resolution, role guards, RLS and consultation department one-account mapping.
