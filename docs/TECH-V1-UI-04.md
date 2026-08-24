# TECH-V1-UI-04 | Simplify Home by Authentication State

| Item | Value |
|---|---|
| Document ID | `TECH-V1-UI-04` |
| Version | `V1.0` |
| Status | Accepted |
| Scope | `UI1.3` homepage hierarchy patch after archived UI1.2 |
| OpenSpec | `2026-08-21-simplify-home-by-authentication-state` |
| Database/API change | None |
| Feishu copy | [TECH-V1-UI-04](https://a9ihi0un9c.feishu.cn/docx/XVBUdW4c7oWDCIx01XrcVPXynic) |

## Decision

The homepage has two intentionally distinct states:

- Signed out: show only the existing, real personal-service and enterprise-service entrances, plus the existing login link and any explicit login-configuration notice. Do not mount the Q&A workbench, textarea, question state or sign-in prompt.
- Signed in with `individual` or `enterprise`: make the existing policy Q&A hero the first homepage content immediately under the global header. Remove the redundant welcome/identity summary and the duplicate workspace-card overview; role navigation remains in the global header.

The removed block was a legacy reconstructed dashboard summary: it greeted the identity and repeated the region and role navigation. Since the header already exposes the active role and the Q&A hero is the accepted primary journey, it adds vertical distance without adding a necessary action.

## Permission and failure boundaries

This is presentation-only. It does not change Supabase session handling, `/me`, role guards, role navigation, `POST /api/v1/policy-answers`, request/response behavior, placeholder disclosure, error states, data, database schema or configuration.

Government or administrator identities, which remain ineligible for policy Q&A, retain a compact real workspace-access fallback on the homepage so no authorized role is hidden. Loading, configuration-missing and identity-error states remain explicit. No local identity, mock answer, client-side fallback, persistence, migration or write is introduced.

## Implementation

- Remove `PolicyQaWorkbench` from `PublicLanding`; retain its two existing service cards as the public primary surface.
- For an eligible signed-in homepage, render `PolicyQaWorkbench variant="workspace"` as the first and primary page content, without the duplicate hero or workspace-card section.
- Retain a compact, semantically labelled real workspace link fallback only for signed-in identities that have neither `individual` nor `enterprise` roles.
- Remove obsolete authenticated-home/dashboard styling only when no longer referenced; preserve responsive header, role routes and Q&A hero responsiveness.
- Extend render checks for signed-out no-Q&A, eligible signed-in Q&A-first, and ineligible-role fallback behavior.

## Verification and rollback

Run frontend render tests/build, backend tests, Ruff, local/runtime smoke, acceptance, browser checks and strict OpenSpec validation. Rollback restores only the removed presentation blocks and styles; no API, Auth, database or data operation is performed.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-21 | V1.0 | Defined signed-out service-only homepage and signed-in Q&A-first homepage without duplicate dashboard summary. |
| 2026-08-21 | V1.0 | Accepted after signed-out browser verification, full frontend/backend regression and strict validation; no migration, data/Auth write or deletion was performed. |
