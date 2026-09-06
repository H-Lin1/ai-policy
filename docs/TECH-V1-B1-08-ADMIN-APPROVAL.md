# TECH-V1-B1-08-A | Registration application administration

| Item | Value |
|---|---|
| Document ID | `TECH-V1-B1-08-A` |
| Version / status | `V1.1` / Accepted |
| Development step | `B1.8` / `B18-007` |
| Product requirement | [`PRD-V1-B1-08-ADMIN-APPROVAL`](./PRD-V1-B1-08-ADMIN-APPROVAL.md) |
| OpenSpec change | `2026-09-05-establish-registration-and-admin-approval` |
| Database revision | Uses `0006_registration_applications`; no second application table |

## 1. Boundary

The approval workbench is an independent protected admin feature, with separate routes, API contracts, permissions and tests from public registration. It is delivered in the same B18-007 change for end-to-end verification.

## 2. Backend API

```text
GET  /api/v1/admin/registration-applications
GET  /api/v1/admin/registration-applications/{id}
POST /api/v1/admin/registration-applications/{id}/approve
POST /api/v1/admin/registration-applications/{id}/reject
```

Every endpoint resolves current identity then requires active `admin`. No client-supplied role, organization, department binding, reviewer, status or timestamp is trusted.

List supports type, status, keyword, page and page size. Safe summaries contain ID, type, status, display title, user-of-service name, department/enterprise name, timestamps and redacted contact summary. Detail returns validated form fields needed for a decision; passwords and hashes are never returned.

Approve accepts an optional note. Reject requires a non-blank reason. Both lock the row and require `pending`; otherwise return `REGISTRATION_ALREADY_PROCESSED` without an event or side effect.

## 3. Approval transactions

Enterprise approval locks and revalidates the application, username and credit code; creates an active enterprise organization, local user, profile and `enterprise` role; marks approved; and writes reviewer/event in one transaction. Organization code is server-generated from normalized credit code.

Government approval locks the application and selected consultation department, confirms no existing mapped government account or competing pending application, creates the local user/profile bound to the mapped government organization, assigns `government`, fills the existing dedicated `government_user_id`, marks approved and writes reviewer/event. The one-department/one-account rule remains enforced.

Rejection stores only a bounded user-facing reason, reviewer, timestamp and rejected event; it creates no active identity. Concurrent or repeated decisions are protected by row locks and stable conflict errors.

## 4. Frontend routes and state

```text
/admin/registration-applications
/admin/registration-applications/{id}
```

The list has pending count, type/status filters, keyword search, pagination and redacted summaries. Detail renders enterprise or government fields, status, audit timestamps and explicit Approve/Reject actions. Decisions use accessible confirmation dialogs; rejection requires a reason. Loading, empty, forbidden, conflict and error states are explicit; mutations refresh from the server. The layout remains operable at `390x844` without horizontal overflow.

## 5. Audit, privacy and verification

The append-only event table records submission and each administrative decision with server actor and timestamp. Logs contain event names, IDs and request IDs only. Responses use the common error envelope, request ID and no-store header; existing RLS/browser privilege restrictions remain unchanged.

Tests cover admin-only access, redaction, filters/pagination, mandatory rejection reason, transaction rollback, idempotency, concurrent approvals, enterprise organization creation, government department uniqueness, event ordering, API contracts, frontend accessibility/responsive states and registration-to-login acceptance.

Authorized local acceptance on 2026-09-05 created one direct admin identity, approved one enterprise and one government application, rejected a separate enterprise application with a user-visible reason, verified submitted/approved/rejected audit events, rejected non-admin review and repeated decisions, and confirmed the government department's one-account binding. Unapproved and rejected usernames could not log in. An initial government approval exposed an ORM flush-order issue; its transaction rolled back, the profile-before-department flush was added, and the pending application then approved successfully with no partial identity left behind.
