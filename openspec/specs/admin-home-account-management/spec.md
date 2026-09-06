# admin-home-account-management Specification

## Purpose

Provide a concise administrator homepage and a controlled account-management capability for all four account roles without weakening role, organization, department, audit or data-retention boundaries.

## Requirements

### Requirement: Administrator homepage consolidation

The system SHALL render administrator workbench content directly at `/homepage` and SHALL not expose an `/admin` frontend route. Admin navigation SHALL contain only 首页、政策中心、历史问答; account management, registration approvals and policy management SHALL be reachable as homepage function entries rather than primary navigation items.

#### Scenario: Admin opens homepage

- **WHEN** an authenticated admin visits `/homepage`
- **THEN** the former admin workbench content is shown directly with overview and function entries, without a duplicate `/admin` workspace

#### Scenario: Admin navigation is concise

- **WHEN** an admin shell is rendered
- **THEN** it shows only 首页、政策中心、历史问答 and omits 智能分类、服务状态、平台管理、政策管理 and 注册申请 primary links

### Requirement: Admin account inventory

The system SHALL provide an admin-only account-management page listing individual, enterprise, government and admin accounts with role/status filters, keyword search and pagination. Responses SHALL omit passwords, hashes, JWTs and full sensitive contact values.

#### Scenario: Admin filters accounts

- **WHEN** an admin requests accounts by role, active status or keyword
- **THEN** only matching safe summaries and pagination metadata are returned

#### Scenario: Non-admin account inventory is denied

- **WHEN** an unauthenticated or non-admin identity requests account-management data
- **THEN** the established 401/403 contract is returned without account existence or content leakage

### Requirement: Controlled account administration

The system SHALL allow an admin to create and edit bounded account information for individual, enterprise, government and admin roles. Server-side rules SHALL require matching active organization/region/department scope, preserve the one-government-account-per-department rule, forbid login-username changes in this release, and append an audit event for each mutation.

#### Scenario: Admin creates an account

- **WHEN** an admin submits a valid role-specific account form
- **THEN** the server atomically creates the local user/profile/role and required organization or department binding, then records an audit event

#### Scenario: Invalid privileged binding is rejected

- **WHEN** an admin tries to assign a government role to an occupied department, an enterprise role without an enterprise organization, or an admin role outside the platform organization
- **THEN** the server returns a stable conflict/validation error and creates no partial identity or audit event

### Requirement: Disable instead of physical deletion

The system SHALL implement account deletion requests as disable operations and SHALL provide enable operations that revalidate scope and constraints. Disable SHALL preserve historical consultations, policies, applications and audit records.

#### Scenario: Admin disables and re-enables an account

- **WHEN** an admin confirms disable or enable for a target account
- **THEN** the account and role/profile status change transactionally, old access is rejected while disabled, and a corresponding audit event is appended

#### Scenario: Physical deletion is unavailable

- **WHEN** a caller attempts a user-delete operation
- **THEN** no delete route is registered and existing data remains intact
