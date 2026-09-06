# TECH-V1-B1-08-R | Standalone account registration and approval applications

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-08-R` |
| Version / status | `V1.1` / Accepted |
| Development step | `B1.8` / `B18-007` |
| Product requirement | [`PRD-V1-B1-08-REGISTRATION`](./PRD-V1-B1-08-REGISTRATION.md) |
| OpenSpec change | `2026-09-05-establish-registration-and-admin-approval` |
| Database revision | `0006_registration_applications` (planned) |
| Authentication | standalone PostgreSQL local accounts only |

## 1. Scope and architecture

This change adds account registration to standalone PostgreSQL mode. It does not introduce a second identity provider, does not use Supabase Auth, and does not change the existing JWT format, `AuthSessionCoordinator`, `RoleGuard`, or `/me` authorization source of truth.

The public entry role is presentation state only. The server creates or activates roles through existing `app.profiles` and `app.user_roles`. Browser code never writes `app.*` tables directly.

Flows: individual self-registration creates an immediately usable individual account; enterprise registration creates a pending application; government registration creates a pending application tied to one existing Shenzhen department. Enterprise and government roles are created only after admin approval.

## 2. Database migration `0006_registration_applications`

Add `app.registration_applications` after `0005_consultation_workflow` with: `id`, `application_type` (`enterprise`/`government`), `status` (`pending`/`approved`/`rejected`/`cancelled`), `region_id`, nullable government `department_id`, `login_username`, `password_hash`, validated `form_data` JSONB, submitted/reviewed timestamps, nullable reviewer and reason, and audit timestamps. Alter `consultation_departments.government_user_id` to nullable so an approved directory department can exist before its one account is approved; approval fills it exactly once.

Add append-only `app.registration_application_events` with application ID, event type (`submitted`/`approved`/`rejected`/`cancelled`), server actor, bounded reason and timestamp.

Constraints and indexes: government applications require a department and enterprise applications must not have one; region is active Shenzhen; partial unique indexes allow at most one pending application username and one government application per department while pending or approved; RLS is enabled and browser roles receive no table privileges. Username and credit-code uniqueness is rechecked transactionally because username spans users and applications. No migration creates Auth users, demo data or modifies consultation rows.

The migration is PostgreSQL-only and a safe no-op during non-PostgreSQL source inspection, matching existing migration tests.

## 3. API contracts

All endpoints use `/api/v1`, the shared error envelope, request IDs and `Cache-Control: no-store`. Separate Pydantic models forbid arbitrary role, organization, department binding, reviewer, status and actor fields.

### Individual

`POST /api/v1/iam/registrations/individual` accepts username, password, confirmation, display name and terms acceptance. The service normalizes, validates a 12-character minimum password, hashes with the existing scrypt helper, and creates `app.users`, a Shenzhen active profile and `individual` role in one transaction. It returns success without a token.

### Enterprise application

`POST /api/v1/iam/registrations/enterprise` accepts enterprise name, unified social credit code, enterprise type, address, Shenzhen region, user-of-service name/title/contact, username, password confirmation and terms. It stores validated fields, hashes the password, creates a pending application and submitted event, and creates no organization, user, profile or role before approval.

### Government application

`POST /api/v1/iam/registrations/government` accepts a department ID from the server directory, user-of-service name/title/contact, optional employee identifier, usage scenario/reason, username, password confirmation and terms. The service locks and re-reads the active Shenzhen department and rejects any pending application or active mapped account for it. It stores the validated department ID and display snapshot; the client cannot supply organization or government-user IDs.

### Applicant status

`GET /api/v1/iam/registration-applications/{application_id}/status` requires the application ID plus a server-defined verification value derived from submitted contact information. Only the matching applicant receives type, status, timestamps and user-facing reason; invalid or foreign lookups return the same non-enumerating `REGISTRATION_NOT_FOUND` response.

## 4. Authentication, failure and privacy

Public registration is available only when local auth and database configuration are ready. Pending applicants receive no bearer token. Existing identity resolution remains authoritative; pending or inactive records cannot access protected workspaces.

Stable errors include `REGISTRATION_INVALID`, `REGISTRATION_DUPLICATE_ACCOUNT`, `REGISTRATION_DUPLICATE_CREDIT_CODE`, `REGISTRATION_DEPARTMENT_UNAVAILABLE`, `REGISTRATION_ALREADY_PROCESSED`, `REGISTRATION_NOT_FOUND` and `REGISTRATION_APPROVAL_REQUIRED`.

Passwords, hashes, raw form data, full contacts, reviewer details, database errors and tracebacks are excluded from responses and logs. Writes use one transaction with row locks and repeated uniqueness checks. Failed commits leave no partial records. Rollback is route disablement or a forward correction, never automatic deletion.

## 5. Verification

Cover validation, scrypt hashing, duplicate protection, role non-escalation, Shenzhen scope, one-department uniqueness, no token issuance, no-store/request ID, non-enumerating status, rollback, migration/RLS contracts and existing IAM/RoleGuard/consultation regressions.

On 2026-09-05, authorized migration `0006_registration_applications` was applied only to local standalone database `aipolicy_local`. One individual account completed public registration; enterprise and government accounts completed pending application and admin approval; all three plus a directly provisioned admin account logged in through local auth and passed matching `/me` and workspace authorization. Same-department duplicate submission, non-admin review and repeated approval were rejected. Credentials were not recorded in tracked files or acceptance output.
