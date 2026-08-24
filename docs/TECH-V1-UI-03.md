# TECH-V1-UI-03 | Align Policy Q&A Entry with Authorized Legacy Visual Reference

| Item | Value |
|---|---|
| Document ID | `TECH-V1-UI-03` |
| Version | `V1.0` |
| Status | Accepted |
| Scope | `UI1.2` visual alignment patch after archived B1.5 |
| Related product capability | `B1.5` policy Q&A entry |
| OpenSpec | `2026-08-21-align-policy-qa-visual-entry` |
| Database/API change | None |
| Feishu copy | [TECH-V1-UI-03](https://a9ihi0un9c.feishu.cn/docx/GjTZd8yRToeLhox47yKclDx0ndf) |

## Decision

Rework the public homepage and the individual/enterprise Q&A entry presentation so that the question is the dominant first action, matching the authorized old personal-service visual reference: pale-blue canvas, restrained floating geometric decoration, large greeting headline with blue gradient emphasis, centered chat-style input surface, focused shadow, compact Enter/Shift+Enter guidance, and round send action.

The old project was inspected only after explicit user authorization for visual comparison. This implementation is independently authored in the rebuilt React/TypeScript application. It does not copy legacy source, routes, state, data, API behavior, Tailwind classes, JavaScript or CSS; it does not reuse any old mock behavior or build output.

## Architecture and behavior boundaries

`PolicyQaWorkbench` remains the only Q&A interaction component and continues to call only the accepted authenticated `POST /api/v1/policy-answers` contract. The existing sign-in, empty, loading, placeholder-result, source-empty and error states remain explicit. Signed-out submission still does not send question text and instead presents the existing login action. Eligible users retain bearer-token API calls. No browser-side fallback, history, local storage, session storage, mock answer, new route, API/schema/configuration change, database access or migration is introduced.

The public homepage keeps its actual individual and enterprise entrances, but moves them below the Q&A hero so they support rather than obscure the primary journey. Individual and enterprise workspaces render the Q&A hero before identity-scope detail. Government and administrator workspaces do not gain Q&A access.

## Implementation

- Add presentation variants to the independently authored workbench: public hero and eligible workspace hero.
- Use semantic, accessible HTML: labelled textarea, submit form, live state regions and an icon-only send button with an accessible name.
- Support Enter to submit and Shift+Enter for a line break for eligible users; retain form submission and disabled state behavior.
- Replace the generic rectangular input treatment for these entry variants with an adaptive-height chat surface and round send control; no effect on returned answer content or status semantics.
- Add responsive CSS for `390x844` and `320px` widths, reduced-motion behavior, keyboard focus, wrapping and no horizontal overflow.
- Update render checks to assert the visual hierarchy and the retained explicit/status-safe behavior.

## Verification and rollback

Run frontend render tests and production build; backend tests, Ruff, local smoke, runtime smoke, acceptance and strict OpenSpec validation remain required for this visual patch. Browser verification checks the public, individual and enterprise entry flows at desktop and mobile width. Rollback is a source/style revert only; no migration, delete, Auth action, data write or API rollback occurs.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-21 | V1.0 | Defined independent visual alignment of the policy Q&A entry with the user-authorized old personal-service reference. |
| 2026-08-21 | V1.0 | Accepted after browser verification, backend/frontend verification and strict validation; no migration, data/Auth write or deletion was performed. |
