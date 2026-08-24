## MODIFIED Requirements

### Requirement: Shared Q&A entry workbench

The frontend SHALL provide a responsive policy-Q&A workbench as the primary visual entry on the public homepage and at individual/enterprise entry routes, using the established visual baseline and an independently authored treatment derived from the user-authorized old personal-service visual reference. It SHALL present sign-in-required, empty, loading, explicit placeholder, source-empty and error states without client-side answer fallback, history, import or model controls.

#### Scenario: Visitor sees the Q&A-first public entry

- **WHEN** a signed-out visitor opens the homepage
- **THEN** the Q&A greeting and chat-style entry are the primary visible content, personal and enterprise entrances remain available as secondary real route links, and submission does not transmit question text before login

#### Scenario: User starts a question from an eligible entry

- **WHEN** an eligible user submits a question from the homepage or individual/enterprise service entry by the form action or Enter key
- **THEN** the frontend calls the authenticated policy-answer API and displays the returned mode and notice without horizontal overflow

#### Scenario: Entry is viewed on a small screen

- **WHEN** the Q&A-first entry is rendered at `390x844` or narrower supported width
- **THEN** the greeting, textarea, submit action, login/service controls and explicit state content remain readable, keyboard-operable and free of horizontal overflow
