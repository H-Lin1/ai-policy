# Proposal: Provision the B1.2 Policy Library Sample

## Why

B1.2 code and migration source are accepted, but the configured Supabase database remains at `0002_identity_access` and contains no policy records. The user explicitly authorized completing the database provisioning on 2026-08-11.

## What Changes

- Add a doubly confirmed initializer for the exact `0003_policy_library` migration.
- Add a separately confirmed, insert-or-verify import for the deterministic 20-record fixture.
- Extend runtime smoke to verify the exact policy schema after provisioning.
- Execute the migration once and the fixture import twice, proving the second import changes nothing.
- Record database, API, test, documentation, and Feishu evidence before archive.

## Non-Goals

- No import of the complete 1,578-row CSV or any rejected/review record.
- No update, overwrite, delete, downgrade, reset, Auth mutation, or feature-flag change.
- No policy editing API/UI, classifier, search, Embedding, RAG, Q&A, or legacy code access.

## Related Documents

- PRD: `docs/PRD-V1-B1-02.md`
- TECH: `docs/TECH-V1-B1-02.md` V1.2
- Development step: `B1.2-D1`
