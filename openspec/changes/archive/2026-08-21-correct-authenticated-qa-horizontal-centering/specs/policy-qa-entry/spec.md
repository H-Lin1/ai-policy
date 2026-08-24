## MODIFIED Requirements

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
