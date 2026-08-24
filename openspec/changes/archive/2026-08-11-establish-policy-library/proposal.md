# Proposal: Establish the B1.2 Policy Library

## Why

The rebuilt `/policies` route currently verifies only the `policy_workspace` feature flag and renders no business data. The supplied crawl output provides a traceable set of successful policy records from government domains, including official source URLs, metadata, cleaned full text, collection times, and content hashes.

## What Changes

- Add the B1.2 policy read model and migration source without applying it to Supabase.
- Validate the supplied crawl contract and create a deterministic 20-record local fixture.
- Expose authenticated, Shenzhen-scoped paginated policy list and detail APIs.
- Replace the feature-guard placeholder with a read-only policy list/detail experience using the accepted UI1.0 baseline.
- Add non-mutating data validation, API, frontend, and migration-structure tests.

## Non-Goals

- No full 1,578-row import or external database write.
- No policy edit/review/approval/import UI.
- No attachment upload/storage, OCR, classification, tags, search ranking, Embedding, RAG, Q&A, consultation, or recommendation.
- No legacy source, crawler implementation, routes, payloads, Mock data, or model code is read or reused.

## Related Documents

- PRD: `docs/PRD-V1-B1-02.md`
- TECH: `docs/TECH-V1-B1-02.md`
- Development step: `B1.2`
