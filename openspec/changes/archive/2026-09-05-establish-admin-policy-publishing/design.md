## Context

Twenty existing policy rows are read-only public records. Admin registration and approval are complete, local standalone authentication is active, and no policy write API or lifecycle exists.

## Decisions

### Data lifecycle

Revision `0007` adds lifecycle/source/audit columns to `policy_documents` and a `policy_document_events` table. Existing rows default to published external URL sources. Admin-created rows can have no external URL; the existing non-empty source URL check is replaced by a source-type consistency check.

### Manual and batch inputs

Manual creation and Markdown parse output share the same field schema. Batch request count is 1–20, each UTF-8 Markdown string is at most 2 MB, and there is deliberately no aggregate byte limit. Parsing one invalid file returns a failed item while other items continue.

### Markdown parsing

Only flat YAML front matter is accepted. Allowed keys are fixed. Values are scalar text; optional quoting is stripped. Dates, enum status and HTTP(S) URLs are validated server-side. The Markdown body is retained as text, normalized and hashed; raw HTML is never executed.

### Persistence and visibility

Parse is non-persistent. Saving drafts/publishing selected items processes each item in an independent transaction/result boundary. Public repositories explicitly filter `publication_status=published`. Withdraw is a state transition with required reason and audit event, never deletion.

### Duplicate behavior

Exact content hash, raw Markdown hash, document number and source URL conflicts block persistence. Same title/organization with different content produces a warning before confirmation. Idempotency uses server checks and database indexes.

### Permissions and failures

All admin APIs resolve current identity and require `admin`. Stable errors do not leak content or database details. Raw Markdown/body text is excluded from logs. Responses use no-store and request IDs.

## Migration Plan

1. Strict validate artifacts.
2. Implement source migration/models/API/frontend/tests without database writes.
3. With the user's existing local-write authorization, apply `0007` only to `aipolicy_local` and verify 20 existing rows remain published.
4. Run manual, batch partial-failure, draft, publish, duplicate, withdraw and authorization acceptance; update evidence and archive.

## Risks / Trade-offs

- Flat front matter is intentionally less expressive but deterministic and dependency-free.
- No aggregate batch limit allows twenty 2 MB files; request count/per-file limits bound worst-case processing.
- Plain Markdown storage preserves source but does not provide rich HTML rendering in this phase.

