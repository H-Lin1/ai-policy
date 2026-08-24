## Context

See `proposal.md` for motivation and `specs/` for the required user-visible behavior. The current application has database-backed Shenzhen profiles, roles and organizations, a public historical-Q&A read model, a protected policy-Q&A endpoint, and no consultation model or routes. The IAM seed currently provides one government organization, while B1.4's classifier labels are not organization-routing records; a consultation department directory therefore cannot be inferred safely from either source.

## Goals / Non-Goals

**Goals:**

- Add one transactional, auditable consultation aggregate with a server-owned lifecycle and narrowly scoped data access.
- Keep policy Q&A and a formal government consultation as distinct deliberate actions, while allowing a user to carry an editable Q&A draft into the consultation form.
- Make publication a one-way, de-identified projection into public historical Q&A without broadening the existing browser database boundary.
- Preserve a route and response shape that does not depend on the real RAG engine.

**Non-Goals:**

- Do not choose a real RAG provider, create an index, change `POST /api/v1/policy-answers`, or implement an AI fallback.
- Do not infer governmental routing from a model score, expose a private consultation in `/qa`, add attachments/notifications, or import legacy consultation data or source code.
- Do not run a migration, seed, database write, Auth write, or create an external account during planning.

## Decisions

### Separate presentation and API paths

Individual/enterprise navigation will lead to `/consultations/new` for creation and `/consultations` for owned work. Government navigation will lead to the same list URL but render a department-scoped processing workbench. A result from `/policy-answers` can transfer only its visible question to a browser-local editable draft.

This avoids making an ambiguous chat “send” action a legally meaningful work-order submission. It also preserves B1.5's existing API and lets B1.6 run while RAG remains an external handoff. A single unlabelled chat input was rejected because it cannot prove user intent or distinguish request handling from informational Q&A.

### Consultation aggregate and automatic assignment

The approved implementation introduces `app.consultation_departments`, `app.consultations`, and `app.consultation_events` in a new revision after `0004_historical_qa`. `consultation_departments` pins every B1.4 label-map `department_id` and display name to one active Shenzhen government organization and one dedicated government profile/account. The consultation owns its submitter, selected directory department, resolved receiver account, current status, public-safe question copy and lifecycle timestamps. The event table records only immutable lifecycle events; B1.6 does not include user clarifications, multi-turn messages or a message timeline.

Submitting a consultation locks/validates the selected directory row, resolves its one dedicated account and writes `submitted` followed by `assigned` plus the initial content in one transaction. The reply operation updates the consultation and lifecycle events in the same transaction. The service accepts only `submitted → assigned → replied → published → closed`, with the narrow approved non-public branch `replied → closed`; client actor IDs, state names and timestamps are ignored rather than trusted.

An append-only event approach was considered, but a current-state aggregate plus immutable history gives simple list filters and a directly verifiable state-machine guard for this small demonstration scope. Manual government claim was rejected because the user has confirmed immediate assignment to the final selected department.

### Classifier map is the department directory

The B1.4 label map is authoritative for the 35 selectable department IDs and display names. The submission page invokes existing `POST /api/v1/classifications` when text is ready, uses its top three ordered predictions and probabilities as recommendation UI, and separately loads the full B1.4-derived directory. The recommendation is not persisted as a routing decision and cannot select a department without the user's final choice.

For every label-map department, the controlled initializer must create or verify exactly one active government organization and exactly one dedicated active government application profile/role mapping. The server validates that the selected stable map ID has a matching active mapping at submission and accepts government reply/publication only when current identity equals the mapped dedicated account. Existing one-account IAM seed is insufficient; the 35 new account mappings require a separate, user-authorized Supabase Auth provisioning plan and must never be fabricated in browser/client code.

### Permissions and public projection

The service resolves identity through existing IAM on every operation. Individuals/enterprises can create and read only records whose requester ID is their subject. They cannot append clarifications or messages in B1.6. Government users must have an active government organization matching the consultation's receiving department; no admin bypass is introduced by this change.

Publishing is an optional choice made by the mapped department account after it has replied. If elected, a transaction first checks `replied`, then creates an immutable, one-to-one public historical-Q&A projection with a consultation reference and only approved public fields. The read repository will union/represent the existing imported records and the projection while keeping current pagination, Shenzhen scoping and no-store headers. Source metadata for the projection will identify the platform consultation publication rather than inventing an external government URL. A department may instead leave the response private and close from `replied`; closing does not delete or alter an already public projection.

Copying the full consultation or submitter organization to `historical_qa` was rejected because the public list's trust and privacy guarantees require a deliberately limited projection.

### API, failure and operational contract

All endpoints remain under `/api/v1`, use the common error envelope/request ID and set `Cache-Control: no-store`. Exact endpoint field shapes, error-code registration and OpenAPI examples will be written before implementation. The intended operations are directory/list/detail, create, reply, publish and close; no generic arbitrary PATCH endpoint will permit user-chosen state.

Expected failures include identity/scope denial, missing/invalid department, missing object, malformed text and state conflicts. They must not return another submitter's title, existence, government account name, database errors or traceback. Question and reply bodies must not be logged. No mock consultation or silent fallback is permitted.

### Migration, seed and rollback

The source migration will be inspected and unit-tested without a configured database. Applying the revision and seeding demo data require a named, double-confirmed command, target-binding checks, approved revision, an initializer lock, deterministic IDs and a second-run zero-change assertion, following the B1.1/B1.3 controlled-seed pattern. The seed cannot create Auth users or overwrite an existing non-demo row.

Because a published consultation may become a public answer, rollback means disabling routes and deploying a forward corrective migration when necessary; automatic downgrade or deletion of production consultations is prohibited.

## Risks / Trade-offs

- [35 department account mappings require new Auth identities] → Build a separately approved account-provisioning and B1.6 mapping initializer before database seed; do not substitute a single shared government identity or fabricate accounts.
- [Public disclosure includes sensitive text] → Require an explicit publication action and define the approved public field set before implementation; retain only the private consultation fields needed for the single-round workflow.
- [Concurrent government handling] → Use transaction-level current-state guard plus immutable transition-history invariants and test stale/repeated reply, publication and close attempts.
- [Historical-Q&A contract regression] → Keep imported records immutable, add source typing/projection tests, and run its existing list/detail regression suite.
- [RAG handoff is delayed] → Maintain fully independent B1.6 entry and no RAG call in the consultation path.

## Migration Plan

1. Obtain PRD V1.0 approval for the 35 department account mappings and account-provisioning authorization; classification recommendations, user choice, automatic assignment and department-controlled publication are confirmed.
2. Complete and strict-validate the OpenSpec; only then implement migration source, repository/service/router, frontend and tests.
3. After separate database-write authorization, run the guarded migration and deterministic seed against the bound target; repeat it to prove no mutation.
4. Execute automated authorization/state-machine tests and a real cross-role desktop/mobile demonstration: classify → user selects → submit/assign → reply → department elects public/private → public view when elected → close.
5. Archive only after all evidence is recorded. If a production issue requires reversal, disable the affected route and use a separately approved forward correction; do not delete consultations automatically.

## Open Questions

- The dedicated-account seed will require 35 existing Supabase Auth user identities. Confirm whether the operator will provision these through a documented approved batch before the B1.6 initializer binds them, or whether an approved alternative government identity provider/management flow should be designed. A single shared government account is explicitly not an alternative.
