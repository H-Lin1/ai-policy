## Purpose

Provide administrators a reviewed policy authoring and batch Markdown publishing workflow while protecting public policy quality, lifecycle history and role boundaries.

## ADDED Requirements

### Requirement: Manual policy authoring

The system SHALL allow only an active administrator to enter approved policy metadata and body, preview the result, and save it as draft or publish it. Server-owned identity, region, hashes and timestamps SHALL NOT be accepted from the client.

#### Scenario: Admin creates a manual draft

- **WHEN** an administrator submits valid policy fields and chooses save draft
- **THEN** one draft policy and audit event are created and the policy is absent from ordinary policy responses

### Requirement: Batch Markdown parsing

The system SHALL accept 1–20 UTF-8 Markdown files per batch, each no larger than 2 MB, and SHALL impose no aggregate batch-size limit. Each file SHALL use the documented flat front matter contract and SHALL be parsed independently into editable policy fields.

#### Scenario: Mixed batch results

- **WHEN** a batch contains valid and invalid Markdown files within count/per-file limits
- **THEN** each input returns an ordered ready/warning/failed result and one failed file does not prevent valid files from being edited or selected

#### Scenario: Per-file and count limits

- **WHEN** more than 20 files are submitted or one file exceeds 2 MB
- **THEN** the count violation rejects the batch or the oversize file fails explicitly without applying a total-byte limit across otherwise valid files

### Requirement: Example, preview and selected actions

The system SHALL provide a downloadable valid Markdown example, editable parsed fields, policy-detail preview and selected save-draft/publish actions. Publishing SHALL revalidate fields and duplicates server-side.

#### Scenario: Example imports successfully

- **WHEN** an administrator downloads and uploads the unchanged example
- **THEN** it parses as a ready item whose fields can be previewed and saved or published

### Requirement: Policy lifecycle and audit

The system SHALL expose draft, published and withdrawn states to administrators, only published policies to ordinary policy readers, and append a server-actor audit event for create, publish and withdraw. Withdraw SHALL require a reason and SHALL NOT delete the record.

#### Scenario: Published policy is withdrawn

- **WHEN** an administrator withdraws a published policy with a non-blank reason
- **THEN** it becomes withdrawn, remains in admin history with an audit event, and disappears from ordinary list/detail responses

### Requirement: Duplicate and permission protection

The system SHALL reject exact duplicate Markdown, content, document number or source URL persistence and SHALL reject every policy write from non-admin identities without revealing private drafts.

#### Scenario: Duplicate publish is rejected

- **WHEN** an administrator attempts to persist a policy conflicting with an existing protected identity
- **THEN** the item receives a stable duplicate error and no second policy or audit event is created

