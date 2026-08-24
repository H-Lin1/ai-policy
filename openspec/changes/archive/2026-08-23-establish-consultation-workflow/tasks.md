## 1. Approval and contract completion

- [x] 1.1 Record a safe provisioning plan for 35 existing Supabase Auth identities, one dedicated active government identity for each B1.4 label-map department; non-sensitive 35/35 mapping verification completed. Supabase write remains explicitly gated.
- [x] 1.2 Complete the implemented directory/create/list/detail/reply contracts and registered safe errors; `openspec validate establish-consultation-workflow --strict` passes. User clarifications and multi-turn messages are outside B1.6.

## 2. Migration and controlled data

- [x] 2.1 Add the post-`0004` consultation migration and ORM model for B1.4-label-map `consultation_departments`, consultations, immutable event history, dedicated receiver-account binding, restrictive keys/checks/indexes/RLS/browser privilege revocation, and public-Q&A projection linkage. No consultation-message table is included in B1.6.
- [x] 2.2 Add migration source-contract tests proving schema order, RLS/revocation, absence of Auth mutation, and safe no-op behavior for non-PostgreSQL inspection.
- [x] 2.3 Add a double-confirmed, target-bound, initializer-locked B1.6 binding command. It validates all 35 B1.4 labels, one-account-per-department uniqueness, preflight, conflict refusal, idempotent second run and no Auth-user creation.
- [x] 2.4 Apply `0005_consultation_workflow` and the binding command to the configured, target-bound Supabase instance; recorded head revision and safe second-run evidence.

## 3. Backend workflow and authorization

- [x] 3.1 Implement consultation repository and service transactions for the selected directory department, dedicated-account scope and atomic `submitted → assigned`; immutable event history is written and replies close atomically.
- [x] 3.2 Implement versioned directory/create/list/detail/reply endpoints with no-store, request ID and safe error envelopes. Publish/close are intentionally atomic within reply; clarification and message endpoints are outside B1.6.
- [x] 3.3 Extend historical-Q&A projection only for explicitly published, department-supplied de-identified question/answer text; imported record behavior remains unchanged.
- [x] 3.4 Add backend unit/API tests for recommendation forwarding, user choice, automatic assignment, dedicated-account-only handling, 403/409/422 failures, private/public projection boundaries and RAG independence. Real-account acceptance covers the deployed path.

## 4. Frontend consultation workflow

- [x] 4.1 Add role-aware navigation and routes for `/consultations/new` and `/consultations`, including signed-out, empty, error and responsive states; API remains authoritative for denied states.
- [x] 4.2 Implement individual/enterprise consultation creation and “我的咨询” list/detail using only the real API. Clarification and message timeline are outside this approved scope.
- [x] 4.3 Implement submission-time classification recommendations with probabilities, full-directory final selection and explicit classification-unavailable recovery; recommendations never submit or route the consultation.
- [x] 4.4 Implement department-scoped government reply UI with optional de-identified publication and atomic close; no client-side state fabrication.
- [x] 4.5 Add the clearly labelled policy-Q&A “转为人工咨询” action with an editable local draft; it only navigates and cannot submit a consultation automatically.
- [x] 4.6 Add frontend render coverage for role navigation, recommendations/probabilities, final user choice, government public/private state and draft transfer; browser layout evidence confirms 1280px centering and no 390px horizontal overflow.

## 5. Verification, documentation and archive

- [x] 5.1 Run migration tests, 236 backend tests, Ruff, local smoke, controlled runtime checks, frontend tests/build and strict validation without emitting credentials or private test text.
- [x] 5.2 Record deployed acceptance: real classifier → submitter choice → automatic assignment → two dedicated department accounts; private close plus explicit public de-identified projection; unrelated-department denial and repeated-reply conflict; public history visibility and private-history absence.
- [x] 5.3 Update PRD, DEVELOPMENT_STATUS.md, OpenSpec tasks, API/seed documentation. Feishu synchronization is not required for code acceptance; archive remains a separate explicit project-state action.
