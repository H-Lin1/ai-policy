# Proposal: Separate Public And Authenticated Home Routes

## Why

B1.8 follow-up review found that individual and enterprise sign-in currently lands on `/personal` or `/enterprise`, even though those role workspaces are no longer part of the focused navigation. The signed-out service-entry page and the authenticated policy-Q&A home therefore share an ambiguous route transition. Active sign-out also clears the session in place and leaves the user on a protected route that renders a login-required state.

## What Changes

- Keep `/` as the signed-out public landing page with the three service entrances.
- Add `/homepage` as the authenticated home route used by individual and enterprise users.
- Redirect an authenticated visitor who reaches `/` to `/homepage`; redirect a signed-out visitor who reaches `/homepage` to `/`.
- Make the authenticated navigation's 首页 link point to `/homepage`.
- Change individual and enterprise post-login destinations, including mismatch-dialog entry actions, to `/homepage`; preserve government and administrator role workspaces as protected routes.
- After an explicit logout, clear the session through the existing auth coordinator and replace the current history entry with `/`.

## What Does Not Change

- `/personal`, `/enterprise`, `/government`, and `/admin` remain available as existing protected role routes for compatibility and explicit role operations.
- Backend APIs, database schema/data, Supabase Auth configuration, role authorization, and policy-Q&A behavior do not change.
- Session expiry and direct unauthenticated access continue to use the existing route guards and explicit signed-out states.

## Impact

- Modify the frontend router shell, login destination decision, authenticated home rendering, route constants, and regression contracts.
- No database/Auth mutation is performed by the implementation or tests; browser verification uses fixture/auth mocks only.
