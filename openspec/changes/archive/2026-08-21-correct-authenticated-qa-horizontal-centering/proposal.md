# Proposal: Correct Authenticated Q&A Horizontal Centering

## Why

The authenticated Q&A hero remains visibly offset to the left. The full-width negative margin technique conflicts with its existing full-width flex parent.

## What Changes

- Remove only the incorrect workspace-entry viewport-relative horizontal margins.
- Use the existing full-width homepage wrapper and bounded inner content to produce true horizontal centering.

## Non-goals

- No API, IAM, RAG, placeholder, data, database, migration, configuration or interaction change.
- No persistence, mock/fallback, delete or write.

## References

- TECH: `docs/TECH-V1-UI-06.md`
- Development patch: `UI1.5`, after archived `UI1.4`
