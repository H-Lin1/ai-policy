# registration-approval Specification

## Purpose

Provide an independent admin-only registration application workbench with transactional approval, rejection, redaction and auditability.

## Requirements

### Requirement: Admin-only application review

The system SHALL expose paginated, filterable application list/detail endpoints and routes under `/admin/registration-applications`. Only an active identity with `admin` role SHALL access them; all other callers receive the established authorization error.

#### Scenario: Admin lists applications

- **WHEN** an authorized admin requests type/status/keyword/page filters
- **THEN** safe summaries and pagination are returned without passwords, hashes, full contacts or unrelated data

#### Scenario: Non-admin is denied

- **WHEN** an unauthenticated, individual, enterprise or government caller requests a review route
- **THEN** the existing 401/403 contract is returned without application existence or content

### Requirement: Transactional approval

The system SHALL allow approval only for `pending`. Enterprise approval SHALL atomically create an active organization, local user, profile and `enterprise` role before marking approved. Government approval SHALL atomically create local user/profile, bind the selected department organization, assign `government`, fill the one-account department mapping and mark approved.

#### Scenario: Enterprise approval activates identity

- **WHEN** an admin approves a valid pending enterprise application
- **THEN** one active enterprise organization/user/profile/role and approved event are created, and the applicant can pass enterprise authorization

#### Scenario: Government approval activates department account

- **WHEN** an admin approves a valid pending application for an unoccupied department
- **THEN** one government user/profile/role, selected department mapping and approved event are created, and the applicant can pass government authorization

#### Scenario: Approval failure rolls back

- **WHEN** uniqueness, department, database or identity validation fails during approval
- **THEN** no partial objects or event remain and the application remains safely reviewable

### Requirement: Rejection and idempotency

The system SHALL require a non-blank rejection reason and SHALL reject a second decision for a processed application without another event or side effect.

#### Scenario: Admin rejects with reason

- **WHEN** an admin rejects a pending application with a non-blank reason
- **THEN** it becomes rejected, stores reason/reviewer timestamp and one rejected event, and activates no identity

#### Scenario: Repeated decision is a conflict

- **WHEN** an admin approves or rejects an application whose status is not pending
- **THEN** `REGISTRATION_ALREADY_PROCESSED` is returned, existing state is preserved, and no extra side effect occurs

### Requirement: Approval UI is separate and operable

The frontend SHALL keep approval pages separate from public registration pages, show explicit loading/empty/forbidden/conflict/error states, require confirmation for decisions, require a rejection reason, refresh from the server after success and remain keyboard-operable without horizontal overflow at desktop and `390x844` widths.

#### Scenario: Admin completes a decision

- **WHEN** an admin opens detail and confirms approve or reject
- **THEN** duplicate actions are disabled while pending, the server result is shown, and status/list counts refresh from the API
