# Tasks: Policy Q&A Entry and RAG Contract Foundation

## Planning and contract

- [x] 1.1 Confirm B1.4 is archived and inspect the current API, IAM, source-table and visual baseline boundaries.
- [x] 1.2 Create PRD/TECH/RAG handoff/proposal/design/spec and strict-validate before implementation.

## Backend placeholder contract

- [x] 2.1 Add typed policy-answer engine boundary, explicit placeholder implementation and safe readiness/error behavior without persistence.
- [x] 2.2 Add authenticated `POST /api/v1/policy-answers`, Shenzhen individual/enterprise role checks, request ID/no-store behavior and API tests.

## Frontend entry

- [x] 3.1 Add shared responsive policy-Q&A workbench to homepage and personal/enterprise entry routes with explicit sign-in/empty/loading/placeholder/error states.
- [x] 3.2 Add frontend API client, render coverage and build coverage; do not add history, model, import or fallback controls.

## Verification and handoff

- [x] 4.1 Run backend tests, Ruff, local smoke, runtime smoke, frontend tests/build and strict validation.
- [x] 4.2 Run authenticated placeholder API/runtime verification and verify no persistence occurs.
- [x] 4.3 Update PRD/TECH/DEVELOPMENT_STATUS.md, sync Feishu, and archive only after all evidence is recorded.
