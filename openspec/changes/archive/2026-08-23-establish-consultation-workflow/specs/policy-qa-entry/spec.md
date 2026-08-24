## ADDED Requirements

### Requirement: Explicit human-consultation conversion

The policy-Q&A result interface SHALL offer eligible individual and enterprise users an optional, clearly labelled “转为人工咨询” navigation action. It SHALL transfer only the current question as an editable browser-local draft to the consultation form and SHALL not submit the question to any consultation API, create a consultation, or imply government acceptance until the user completes the distinct consultation form.

#### Scenario: User converts a question to a draft

- **WHEN** an eligible user chooses “转为人工咨询” after viewing a policy-Q&A result
- **THEN** the consultation form receives an editable question draft and no consultation record, message or lifecycle event exists before the user separately evaluates recommendations, selects a department and submits the form
