## Purpose

Provide standalone PostgreSQL account registration while keeping privileged enterprise and government access behind administrator approval.

## ADDED Requirements

### Requirement: Individual self-registration

The system SHALL expose a public standalone-local individual registration endpoint and form. A valid submission SHALL atomically create one local user, active Shenzhen profile and active `individual` role. It SHALL not issue a token or accept privileged role, organization or department fields.

#### Scenario: Individual registration succeeds

- **WHEN** a user submits a unique username, a compliant password and confirmation, display name and accepted terms
- **THEN** the server creates user/profile/individual role in one transaction, returns success without a token, and the user can log in through the existing local login flow

#### Scenario: Individual registration cannot escalate

- **WHEN** a client adds enterprise, government, admin, organization, department or status fields
- **THEN** the server rejects or ignores those fields, creates at most an individual role, and no privileged organization/role

### Requirement: Enterprise registration application

The system SHALL expose a public enterprise application form and endpoint for approved enterprise主体 and user-of-service fields. A valid submission SHALL create one `pending` application and `submitted` event, but no active enterprise organization, profile or role.

#### Scenario: Enterprise application is pending

- **WHEN** valid enterprise identity, address, user-of-service and login fields are submitted
- **THEN** the system stores a validated pending application, returns a status reference, and protected enterprise routes remain unavailable

#### Scenario: Duplicate enterprise application is rejected

- **WHEN** username or unified social credit code conflicts with an existing account or active/pending application
- **THEN** a stable duplicate error is returned, no second application is created, and unrelated account details are not revealed

### Requirement: Government department application

The system SHALL expose a government application form whose department selector comes from the active Shenzhen directory. The server SHALL re-read and lock the selected row and allow at most one pending or active government application per department.

#### Scenario: Government application uses an available department

- **WHEN** an available directory department and valid user-of-service, reason and login fields are submitted
- **THEN** one pending application with validated department ID/snapshot is created, no government role is created, and approval-required status is returned

#### Scenario: Government department is occupied

- **WHEN** the selected department has a pending application or active mapped government account
- **THEN** `REGISTRATION_DEPARTMENT_UNAVAILABLE` is returned, no application is created, and the other applicant/account is not disclosed

### Requirement: Applicant status privacy

The system SHALL allow an applicant to query only its own enterprise/government application using application ID and a server-defined verification value. Invalid or foreign lookups SHALL return the same non-enumerating not-found response and never reveal password, hash, reviewer or other private fields.

#### Scenario: Applicant reads own status

- **WHEN** a valid applicant supplies the matching verification value
- **THEN** type, status, submitted/reviewed timestamps and user-facing reason are returned

#### Scenario: Foreign status lookup is hidden

- **WHEN** an unknown ID or non-matching verification value is supplied
- **THEN** `REGISTRATION_NOT_FOUND` is returned with no existence signal or private fields

### Requirement: Registration entry and completion experience

The frontend SHALL horizontally center the individual, enterprise and government registration heading and form card without horizontal overflow at desktop and `390x844` widths. After successful individual registration, the form SHALL be removed and replaced by a completion card with an immediate personal-login action and an automatic redirect to the same login destination after three seconds. The signed-out public home SHALL provide a visually secondary administrator-login link below the three primary service entries.

#### Scenario: Registration forms remain centered

- **WHEN** any of the three registration forms is rendered at desktop or mobile width
- **THEN** the form card shares the viewport horizontal center line, retains equal left/right space and introduces no horizontal overflow

#### Scenario: Individual registration completes

- **WHEN** individual registration succeeds
- **THEN** the registration form is no longer rendered, a success card offers immediate login, and the browser automatically navigates to `/login?role=individual` after three seconds

#### Scenario: Administrator uses the secondary entry

- **WHEN** a signed-out user selects the gray administrator-login link below the primary service cards
- **THEN** the browser opens the administrator-specific login presentation without adding a fourth primary service card
