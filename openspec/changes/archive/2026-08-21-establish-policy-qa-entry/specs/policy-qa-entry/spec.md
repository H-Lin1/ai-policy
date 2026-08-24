## ADDED Requirements

### Requirement: Explicit policy Q&A engine contract

The system SHALL expose a typed policy-answer engine boundary for canonical Shenzhen questions. Until a real RAG implementation is explicitly configured and verified, it SHALL return only an explicitly labelled `placeholder` answer with no fabricated sources, no database persistence and no silent fallback from a failed real engine.

#### Scenario: Placeholder answer is returned

- **WHEN** an eligible Shenzhen user submits a valid question while the placeholder engine is configured
- **THEN** the system returns `answer_mode` `placeholder`, a clear non-authoritative notice, an empty source list and no claim that policy retrieval or generation occurred

#### Scenario: Future RAG engine is unavailable

- **WHEN** a future configured RAG engine is missing, incompatible or fails
- **THEN** the system returns an explicit safe not-ready or failure response without falling back to placeholder content or leaking implementation details

### Requirement: Protected policy-answer endpoint

The system SHALL provide `POST /api/v1/policy-answers` only to active Shenzhen identities with an `individual` or `enterprise` role. It SHALL derive region from identity, reject empty or overlong questions, preserve the shared request-ID error envelope and set `Cache-Control: no-store` on every outcome.

#### Scenario: Eligible role submits a question

- **WHEN** an active Shenzhen individual or enterprise identity submits a non-empty bounded question
- **THEN** the system invokes the configured answer engine and returns only approved answer, mode, notices and source fields

#### Scenario: Ineligible identity or invalid question

- **WHEN** the caller is signed out, disabled, outside Shenzhen, lacks an eligible role, or submits an invalid question
- **THEN** existing 401/403/422/503 contracts apply and the engine is not invoked when authorization or validation fails

### Requirement: Shared Q&A entry workbench

The frontend SHALL provide a responsive policy-Q&A workbench on the homepage and at individual/enterprise entry routes, using the established visual baseline. It SHALL present sign-in-required, empty, loading, explicit placeholder, source-empty and error states without client-side answer fallback, history, import or model controls.

#### Scenario: User starts a question from an eligible entry

- **WHEN** an eligible user submits a question from the homepage or individual/enterprise service entry
- **THEN** the frontend calls the authenticated policy-answer API and displays the returned mode and notice without horizontal overflow
