## ADDED Requirements

### Requirement: Public and authenticated home routes remain distinct

The frontend SHALL reserve `/` for the signed-out public service-entry landing page and SHALL expose the authenticated policy-service home at `/homepage`. The authenticated home SHALL render only after the existing authentication state is ready; route selection MUST NOT grant roles, bypass a role guard, or mount protected content before authorization.

#### Scenario: Signed-out visitor opens the public root

- **WHEN** no session is available and the visitor opens `/`
- **THEN** the page shows the existing three service entrances and does not show the authenticated Q&A workbench

#### Scenario: Authenticated identity opens the public root

- **WHEN** the auth provider reports a ready identity and the browser is at `/`
- **THEN** the router replaces the location with `/homepage` and renders the existing authenticated home for that identity

#### Scenario: Signed-out visitor opens the authenticated home

- **WHEN** the auth provider reports signed out and the browser is at `/homepage`
- **THEN** the router replaces the location with `/` and does not render protected Q&A or role content

#### Scenario: Individual or enterprise login succeeds

- **WHEN** the backend identity contains the intended individual or enterprise role
- **THEN** login navigates to `/homepage`, where the existing role-aware Q&A authorization and UI apply

#### Scenario: Government or administrator role entry remains explicit

- **WHEN** a government or administrator role is selected and the backend authorizes it
- **THEN** login continues to navigate to its existing protected role route and does not grant access through `/homepage`

### Requirement: Active sign-out returns to the public landing page

The explicit sign-out control SHALL clear the existing auth session and replace the current browser location with `/`. It SHALL NOT leave the user on a protected route rendering only a signed-out or login-required state, and browser Back SHALL NOT restore the prior protected location from the logout action.

#### Scenario: User signs out from an authenticated page

- **WHEN** the user activates 退出登录 from `/homepage`, a policy page, a Q&A page, consultation page, or a role workspace
- **THEN** the existing session is cleared and the browser navigates to `/` with history replacement, showing the public service-entry landing page

#### Scenario: Remote sign-out is unavailable

- **WHEN** the remote auth gateway fails during explicit sign-out
- **THEN** local protected content is still cleared, the browser still navigates to `/`, and no private content or error details are exposed on the public page
