# Proposal: Align Policy Q&A Entry with Authorized Legacy Visual Reference

## Why

The accepted B1.5 Q&A capability is correctly wired but its public visual hierarchy differs from the previous personal-service experience, where policy questions were the immediate primary action.

## What Changes

- Make the policy Q&A entry the visual hero on the homepage and individual/enterprise entry views.
- Independently implement the authorized visual characteristics of the old personal entry: pale-blue canvas, quiet geometry, greeting treatment, centered chat input and round send action.
- Preserve actual service entrances, current API/IAM/error states and explicit placeholder disclosure.

## Non-goals

- No legacy source copying or reuse; old code is inspected only for user-authorized visual comparison.
- No RAG change, response/route/API/schema/configuration change, persistence, history, data import, database/Auth write, migration, model or mock behavior.
- No government/admin Q&A access or relaxation of existing authorization.

## References

- TECH: `docs/TECH-V1-UI-03.md`
- Existing Q&A capability: `docs/TECH-V1-B1-05.md`
- Development patch: `UI1.2`, after archived `B1.5`
