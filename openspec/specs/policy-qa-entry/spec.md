# policy-qa-entry Specification

## Purpose
TBD - created by archiving change 2026-08-21-establish-policy-qa-entry. Update Purpose after archive.
## Requirements
### Requirement: Explicit human-consultation conversion

The policy-Q&A result interface SHALL offer eligible individual and enterprise users an optional, clearly labelled “转为人工咨询” navigation action. It SHALL transfer only the current question as an editable browser-local draft to the consultation form and SHALL not submit the question to any consultation API, create a consultation, or imply government acceptance until the user completes the distinct consultation form.

#### Scenario: User converts a question to a draft

- **WHEN** an eligible user chooses “转为人工咨询” after viewing a policy-Q&A result
- **THEN** the consultation form receives an editable question draft and no consultation record or lifecycle event exists before the user separately evaluates recommendations, selects a department and submits the form

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

The frontend SHALL provide a responsive policy-Q&A workbench as the primary visual entry only for authenticated individual/enterprise homepage and service-entry views, using the established visual baseline and independently authored visual treatment. In the eligible authenticated homepage initial state, the Q&A heading and input SHALL be centered both vertically within the available page area and horizontally within the homepage content area. The signed-out homepage SHALL instead show its real personal and enterprise service entrances without mounting a Q&A textarea, chat result or question-submission affordance. The workbench SHALL present loading, explicit placeholder, source-empty and error states without client-side answer fallback, history, import or model controls.

#### Scenario: Visitor sees the Q&A-first public entry

- **WHEN** a signed-out visitor opens the homepage
- **THEN** personal and enterprise entrances and the existing login action are visible, while no policy-Q&A textarea, question state or API submission action is mounted

#### Scenario: User starts a question from an eligible entry

- **WHEN** an eligible authenticated individual or enterprise user submits a question from the homepage or individual/enterprise service entry by the form action or Enter key
- **THEN** the frontend calls the authenticated policy-answer API and displays the returned mode and notice without horizontal overflow

#### Scenario: Initial authenticated Q&A composition

- **WHEN** an eligible authenticated user opens the homepage before submitting a question
- **THEN** the Q&A heading and input are centered in both axes of the available content area, the redundant post-input empty-state explanation is absent, and the input’s keyboard submission guidance remains available

#### Scenario: Ineligible authenticated role visits home

- **WHEN** an authenticated identity without an individual or enterprise role opens the homepage
- **THEN** the page provides its existing real authorized workspace access without mounting policy-Q&A controls

#### Scenario: Entry is viewed on a small screen

- **WHEN** the signed-out service entrances or authenticated Q&A-first entry is rendered at `390x844` or narrower supported width
- **THEN** essential service, login, Q&A and explicit state controls remain readable, keyboard-operable and free of horizontal overflow
