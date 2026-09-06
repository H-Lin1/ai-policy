## Context

The repository runs local accounts against standalone PostgreSQL. `app.users`, profiles, roles, organizations, regions and the consultation department directory exist after `0005_consultation_workflow`; local login issues JWTs and `/me` resolves authorization from the database. Registration and applications do not yet exist.

## Goals / Non-Goals

**Goals:** provide auditable registration without self-assigned privileged roles; keep enterprise/government onboarding pending until admin approval; preserve one government account per department; separate public forms from the admin workbench; provide safe errors and responsive states.

**Non-Goals:** no external verification, files, SSO, employee directory, multi-account department redesign, Supabase Auth writes, demo seed, existing data rewrite, RAG work or destructive rollback.

## Decisions

### Standalone-only identity path

Registration routes are enabled only for `AUTH_MODE=local` with a ready standalone PostgreSQL session. Existing Supabase-mode deployments remain login-only. Registration never calls a browser Auth SDK.

### One migration and two tables

Revision `0006_registration_applications` adds `registration_applications` and append-only `registration_application_events`, and makes `consultation_departments.government_user_id` nullable until approval fills the one-account binding. Enterprise and government fields use separate Pydantic schemas and bounded JSONB. Government department ID is a foreign key; partial unique indexes prevent two pending applications for one username or two pending/approved applications for one department. Historical applications remain queryable after approval, so username uniqueness is pending-only plus transactional checks against `app.users`.

### Server-owned role activation

Individual registration creates only `individual`. Enterprise approval creates an active enterprise organization and role. Government approval binds the selected existing department organization, creates `government`, and fills the existing dedicated `government_user_id` only when empty. Client role, organization, actor, status and timestamps are ignored.

### Transaction and idempotency

Writes use one transaction, row locks and repeated uniqueness checks. Approval requires `pending`; repeated decisions return a stable conflict and write no event. Constraints backstop service checks. Failed approval rolls back every object.

### Status privacy and admin separation

Applicants receive no token from submission. Status lookup requires application ID plus a server-defined verification value and returns non-enumerating not-found for foreign lookups. Admin routes are separate, require `admin`, redact sensitive fields and refresh from server after mutations.

### Error, logging and rollback

All responses use the shared error envelope, request ID and no-store. Passwords, hashes, raw form data and full contacts are excluded from logs/responses. Rollback is route disablement or forward correction, never automatic deletion.

## Risks / Trade-offs

- Without phone/email verification, this is registration rather than identity proof; UI states this explicitly.
- One department/one government account limits staffing but matches the confirmed rule; a queue redesign needs a separate change.
- Username uniqueness across users and applications requires transaction checks in addition to the users unique constraint.

## Migration Plan

1. Strict-validate this change and TECH documents.
2. Implement migration/model, schemas, services, routers and tests without applying migration.
3. Implement public registration/status and independent admin routes with render coverage.
4. With explicit target authorization, apply guarded `0006` to standalone PostgreSQL.
5. Verify register → submit → approve/reject → login, role boundaries, department uniqueness, audit and privacy; update `DEVELOPMENT_STATUS.md`.
6. Archive only after tasks/evidence pass.

## Open Questions

- Finalize the applicant status verification value (contact or one-time application secret) before exposing the endpoint; it must not be a password or public URL secret.
