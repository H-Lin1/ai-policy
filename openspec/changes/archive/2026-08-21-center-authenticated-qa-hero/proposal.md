# Proposal: Center Authenticated Q&A Hero

## Why

The authenticated homepage Q&A content is visually low in the available page area and repeats explanatory copy below the input that is no longer needed.

## What Changes

- Center the initial authenticated individual/enterprise Q&A hero between the shared header and footer.
- Remove the two redundant empty-state lines under the input.
- Preserve keyboard guidance inside the input, all real submission behavior and all post-submit states.

## Non-goals

- No API/IAM/RAG/placeholder/database/configuration change.
- No persistence, mock/fallback, migration, deletion or write.

## References

- TECH: `docs/TECH-V1-UI-05.md`
- Existing Q&A capability: `docs/TECH-V1-B1-05.md`
- Development patch: `UI1.4`, after archived `UI1.3`
