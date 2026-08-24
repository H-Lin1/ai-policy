## Purpose

Provide a repeatable, privacy-preserving integration audit and guarded demonstration reset for the first cross-module acceptance pass of the AI Policy Service Platform.

## ADDED Requirements

### Requirement: Read-only integration audit
The repository SHALL provide a repeatable audit that checks the configured PostgreSQL target binding, current Alembic revision, expected B1.1-B1.6 tables and RLS/browser privilege boundary, complete active consultation department bindings, registered protected routes, and existing frontend/backend regression gates. The audit SHALL emit only named pass/fail states and SHALL NOT output URLs, credentials, tokens, user IDs or private consultation text.

#### Scenario: Healthy integrated target
- **WHEN** the configured target is bound to one Supabase project, revision `0005_consultation_workflow` is current, expected tables and RLS are present, all 35 department bindings are active and local regression gates pass
- **THEN** the audit reports each named check as `ok` and exits successfully without changing external state

#### Scenario: Unsafe or incomplete target
- **WHEN** target binding, revision, table set, RLS, department binding count or a regression gate is invalid
- **THEN** the audit reports a stable failing state without exposing the underlying connection or data details and performs no write

### Requirement: Guarded B1.7 demonstration reset
The repository SHALL provide a reset command whose bare invocation and explicit preflight are read-only. Applying the reset SHALL require both a target-binding check and explicit `--apply-b1-7-reset --confirm` flags, run in one transaction, and delete only consultations whose question or public projection carries the exact B1.7 demonstration marker together with their immutable events and one-to-one public projections. It SHALL refuse to delete unmarked records, Auth identities, policy documents, imported historical Q&A, department bindings or unrelated user consultations.

#### Scenario: Preflight or empty reset
- **WHEN** the operator runs the command without both apply flags or no marked B1.7 records exist
- **THEN** it reports `not_requested` or `already_clean` and performs no database write

#### Scenario: Authorized marked reset
- **WHEN** the target is verified and the operator supplies both apply flags
- **THEN** only records matching the exact B1.7 marker and their dependent events/projections are deleted atomically, counts are reported without content, and unrelated records remain unchanged
