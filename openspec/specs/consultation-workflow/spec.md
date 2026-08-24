# consultation-workflow Specification

## Purpose
Provide a server-enforced Shenzhen consultation workflow so individual and enterprise users can submit trackable requests and authorized government users can process, publish and close them without exposing private submissions.

## Requirements

### Requirement: Distinct consultation entry and submission
The system SHALL provide active Shenzhen `individual` and `enterprise` identities one “政民互动” entry at `/consultations`. Its upper section SHALL submit a consultation and its lower “我的咨询” section SHALL display each full question and current status. Closed consultations SHALL display the department reply and reply time; long replies SHALL initially occupy two lines and offer an expand/collapse control. The requester view SHALL NOT disclose whether a reply was published to historical Q&A. Entering a non-blank bounded consultation body SHALL invoke the existing protected department-classification contract and display its top three returned department names and probabilities alongside the full active B1.4-department-map directory. A consultation submission SHALL require one non-blank bounded consultation body and one valid active directory department deliberately selected by the submitter; the recommendation SHALL NOT replace that choice. The policy-Q&A submit action SHALL NOT create, mutate or automatically forward a consultation.

#### Scenario: Eligible user submits a consultation
- **WHEN** an active Shenzhen individual or enterprise identity enters a valid body and selects one directory department after viewing classification recommendations
- **THEN** the system displays at most three classifier recommendations with probabilities, creates one consultation owned by that identity, records its submitted content and `submitted → assigned` status events, and returns the assigned consultation without exposing another user's information

#### Scenario: Invalid or unauthorized submission is rejected
- **WHEN** a caller is signed out, inactive, outside Shenzhen, lacks an individual or enterprise role, supplies invalid text, or selects an inactive/non-government/out-of-scope department
- **THEN** the system returns the established safe authorization or validation error and creates no consultation or status event

### Requirement: Server-enforced consultation lifecycle
The system SHALL enforce only the lifecycle `submitted → assigned → replied → published → closed`. A successful user submission SHALL automatically assign the consultation to the active dedicated government account mapped to the selected B1.4 directory department. Only that account SHALL submit a non-blank reply to move it to `replied`, choose publication to move it to `published`, and close it to move it to `closed`; a replied consultation that the account elects not to publish MAY move directly to `closed`. Every accepted transition SHALL create an immutable status-history event bearing the server-resolved actor and timestamp.

#### Scenario: Authorized government user completes a lifecycle
- **WHEN** an individual or enterprise user submits a consultation to a selected department and that department's dedicated government account replies, elects publication and then closes it in order
- **THEN** submission produces `submitted` and `assigned` events atomically, each subsequent request returns the resulting state, and the history contains exactly the ordered transitions with no client-supplied actor or timestamp

#### Scenario: Invalid transition or unauthorized department handling is rejected
- **WHEN** an actor attempts a transition out of order, a non-government actor attempts a government transition, a non-mapped government account attempts to mutate the consultation, or the selected directory department has no active dedicated government account
- **THEN** the system returns a stable conflict or authorization error, preserves the previously committed state, and creates no extra history event

### Requirement: Role-scoped consultation visibility
The system SHALL expose each submitted consultation and its immutable status history only to its submitting identity and the dedicated government account mapped to the selected department. B1.6 SHALL NOT provide user clarifications, multi-turn consultation messages or a message timeline. The requester can view the submitted question and, after department processing, the final department reply returned by the consultation record.

#### Scenario: Other caller requests private consultation data
- **WHEN** another individual, enterprise, unrelated government department or unauthenticated caller requests a consultation or write operation
- **THEN** the system applies the existing safe 401, 403 or non-enumerating 404 behavior and leaks no private consultation content or metadata

### Requirement: Public answer publication is explicit and privacy-safe
The system SHALL expose a consultation answer to the public historical-Q&A experience only after the dedicated government account explicitly elects publication for a `replied` consultation. The public projection SHALL include only the approved topic, public-safe question text, government reply, selected department display name and publication timestamp; it MUST NOT expose submitter identity, email, organization identity, internal assignee identity, internal status history or unpublished content. Closing a published consultation SHALL not remove the public projection.

#### Scenario: Published answer becomes visible publicly
- **WHEN** an authorized government user publishes a replied consultation with public-safe question and answer content
- **THEN** the historical-Q&A list and detail experience includes exactly one public, de-identified answer and the submitter's private consultation remains visible only to authorized participants

#### Scenario: Unpublished consultation remains private
- **WHEN** a consultation is submitted, assigned or replied but has not been published
- **THEN** it is absent from all public historical-Q&A responses and no public identifier or answer text is exposed

### Requirement: Consultation entry surfaces preserve clear user intent
The frontend SHALL render one “政民互动” navigation item for eligible individual and enterprise identities and “咨询办理” navigation for eligible government identities. The requester page SHALL place the consultation form above “我的咨询”, which renders the full question and current status for every record and the reply/reply time for closed records; it SHALL not render a requester-visible publication state or historical-Q&A link. Long replies SHALL initially show two lines and provide an expand/collapse control. The consultation form SHALL display B1.4 classification's top three department recommendations and probabilities with the full selectable department directory and require the user's final choice. A policy-Q&A result MAY offer “转为人工咨询” only as an explicit navigation action that pre-fills an editable draft; it SHALL not submit the draft or create a consultation until classification/directory selection and the separate form submission succeed.

#### Scenario: Policy-Q&A user elects human consultation
- **WHEN** an eligible user selects “转为人工咨询” from a policy-Q&A result
- **THEN** the browser opens the consultation form with an editable draft, presents classification recommendations after the draft is evaluated, and creates no consultation before the user separately chooses a department and submits the form

#### Scenario: Responsive consultation entry
- **WHEN** consultation navigation, create, list or government-processing views are rendered at desktop width or `390x844`
- **THEN** the relevant role-only controls remain visible, keyboard-operable and free of horizontal overflow
