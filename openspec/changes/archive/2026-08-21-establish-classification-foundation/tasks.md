# Tasks: Department Classification Foundation

## Planning and asset audit

- [x] 1.1 Confirm B1.3/UI1.1 are archived and audit the new project classifier boundary plus configured asset state.
- [x] 1.2 Create PRD/TECH/proposal/design and strict-validate this change before implementation.
- [x] 1.3 Complete a source-independent read-only audit of the user-provided model/tokenizer/label assets and record compatibility findings.

## Adapter and API

- [x] 2.1 Add explicit classifier manifest settings and safe readiness states without exposing paths.
- [x] 2.2 Implement the verified pure computation adapter behind `ValidatedDepartmentClassifier`, with CPU deterministic inference and label binding validation.
- [x] 2.3 Add authenticated `POST /api/v1/classifications`, schemas, service translation, request ID/no-store behavior, and API tests.

## Frontend

- [x] 3.1 Add `/classify` API client and responsive workbench with loading, empty, success, not-ready, and error states.
- [x] 3.2 Add frontend render and build coverage; do not add model/admin/import controls.

## Verification and handoff

- [x] 4.1 Run backend tests, Ruff, local smoke, runtime smoke, frontend tests/build, and strict validation.
- [x] 4.2 If the configured model is ready, run authenticated repeated-inference verification; otherwise preserve explicit not-ready evidence.
- [x] 4.3 Update PRD/TECH/DEVELOPMENT_STATUS.md, sync Feishu, and archive only after all evidence is recorded.
