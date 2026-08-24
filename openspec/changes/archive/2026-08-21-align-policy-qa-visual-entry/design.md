# Design: Align Policy Q&A Entry with Authorized Legacy Visual Reference

## Presentation

The shared workbench receives an explicit visual entry variant, rather than duplicating question state or implementing a new page. Public and eligible role views use the variant as their first content; its visual surface is a pale-blue hero with non-interactive decoration, greeting copy, clear regional/service context, adaptive chat input and round send action. Existing service links remain as a secondary section on the public homepage.

## Interaction and accessibility

Only an eligible user with a valid access token can submit. Enter submits a non-empty question; Shift+Enter retains a newline. The form submit path continues to work for keyboard and assistive-technology users. The icon-only send control has a textual accessible name, disabled state and visible focus. Existing live result/status regions and the explicit placeholder label remain unchanged.

## API, data, permissions and failure

There is no API, database, model or configuration change. Existing `POST /api/v1/policy-answers`, IAM, server-side normalization, no-store headers and error envelope remain authoritative. Signed-out, ineligible, blank, loading, error and placeholder conditions retain their current safe behavior; no state may be hidden through decorative presentation or replaced with a client-side answer.

## Rollback

Remove only the visual variant and associated styles/tests. Do not modify accepted B1.5 API code, run a migration, change data, or perform an Auth/database operation.
