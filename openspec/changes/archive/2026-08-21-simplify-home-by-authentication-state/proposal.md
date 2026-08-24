# Proposal: Simplify Home by Authentication State

## Why

The current public homepage exposes a chat surface before sign-in, contrary to the desired product flow. The signed-in homepage also repeats identity, region and role information in a large dashboard summary before the actual Q&A entry.

## What Changes

- Make the signed-out homepage service-entry-only: personal and enterprise cards plus existing login/explicit configuration state.
- Make the eligible signed-in homepage immediately Q&A-first.
- Remove the redundant authenticated welcome/dashboard overview and retain compact access for non-Q&A roles.

## Non-goals

- No change to API, IAM, database, migration, data, RAG, placeholder behavior, global navigation or role guards.
- No identity fabrication, mock response, browser-side fallback, persistence or writes.

## References

- TECH: `docs/TECH-V1-UI-04.md`
- Existing Q&A capability: `docs/TECH-V1-B1-05.md`
- Development patch: `UI1.3`, after archived `UI1.2`
