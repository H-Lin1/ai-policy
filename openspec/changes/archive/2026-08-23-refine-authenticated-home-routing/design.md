# Design: Separate Public And Authenticated Home Routes

## Decisions

1. Define `/` as the public landing contract and `/homepage` as the authenticated home contract. This avoids making one URL change its semantic meaning when authentication changes.
2. Reuse the existing `WorkspaceHomePage` component with an explicit mode. Public mode renders the three local service entries only when signed out; authenticated mode renders the existing individual/enterprise policy-Q&A workbench or the existing non-Q&A role links after identity loading and session checks complete.
3. When a ready identity reaches `/`, public mode issues a React Router replace redirect to `/homepage`. When a signed-out identity reaches `/homepage`, authenticated mode issues a replace redirect to `/`. No protected content is mounted before the relevant auth state is ready.
4. Add an `authenticatedHomePath` constant and a role-aware post-login destination helper. Individual and enterprise roles use `/homepage`; government and administrator role-entry intents retain `/government` and `/admin`. A direct login without an entrance intent uses `/homepage` as the authenticated landing destination.
5. The header's 首页 link uses `/homepage` for every ready identity. Signed-out navigation, when visible on non-landing public routes, continues to use `/`.
6. The sign-out button starts the existing coordinator sign-out (which clears the in-memory session before awaiting the remote gateway) and immediately navigates with `{ replace: true }` to `/`. This keeps logout responsive and prevents browser Back from restoring the previous protected location. The mismatch dialog's switch-account action remains on `/login` and is unchanged.

## Security And Data Boundaries

- Route selection is presentation-only; it never grants a role or bypasses `RoleGuard`.
- `/homepage` renders the Q&A workbench only after the existing `AuthProvider` reports a ready identity. Backend policy-answer authorization remains unchanged.
- No credentials, tokens, identity details, database rows, migrations, or external resources are added or modified.

## Risks And Mitigations

- A user may have bookmarked `/personal` or `/enterprise`: those routes remain intact and still enforce server authorization, while only the default post-login destination changes.
- Auth restoration may briefly be loading: the authenticated route shows the existing explicit identity-loading state and redirects only after a signed-out result is known.
- Remote sign-out may fail: the coordinator already clears local state first; navigation still returns the user to the public landing page and the next auth event can reconcile the remote session.

## Rollback

Restore the prior `/` authenticated rendering, role-specific post-login destinations, and in-place sign-out callback. No data or backend rollback is required.
