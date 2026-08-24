# frontend-visual-baseline Specification

## Purpose
Define a stable “政通惠” visual identity for the rebuilt frontend across public, authenticated, protected, and failure states without changing accepted route, session, API, permission, or data behavior.
## Requirements
### Requirement: Reference-derived product identity

The frontend SHALL present “政通惠” and “一站式政策服务平台” as its primary product identity and SHALL use a coherent white/pale blue-gray canvas, neutral text, restrained blue-purple emphasis, Chinese system typography, and compact top navigation derived from the authorized public visual reference. The implementation MUST be independently authored in this repository and MUST NOT copy legacy JavaScript, CSS, component source, routes, payloads, state, or business behavior.

#### Scenario: Visitor recognizes the rebuilt product

- **WHEN** a visitor opens any current public or protected route
- **THEN** the visible shell uses the “政通惠” identity and shared reference-derived visual system rather than the previous generic dark sidebar workbench

#### Scenario: Visual reference is implemented within the new architecture

- **WHEN** UI1.0 assets and styles are inspected
- **THEN** they contain only repository-authored React/CSS plus documented authorized static photographs and do not contain copied legacy application source or unavailable legacy behavior

### Requirement: Public entrance and real authentication continuity

The signed-out home SHALL omit the global header and SHALL present “政通惠” as its primary in-page title with “一站式政策服务平台” as its subtitle. It SHALL provide three equal-size personal, enterprise and government photographic entrance cards in one primary group and SHALL NOT show a separate small-text login entrance. Every card SHALL navigate directly to `/login` while preserving its role intent. After successful authentication, the frontend SHALL navigate directly to the intended protected workspace only when the backend identity contains that role. When the identity does not contain the intended role, the frontend SHALL remain on the login path and display a blocking mismatch dialog naming only the selected and actual public service categories. The user SHALL explicitly choose either to enter an actually authorized service or to sign out and return to the selected service login form. Entrances and dialog actions MUST NOT create a local identity, grant a role, bypass a route guard, mount unauthorized content, or display fabricated results.

#### Scenario: Signed-out visitor chooses a service entrance

- **WHEN** a signed-out visitor activates the personal, enterprise or government entrance
- **THEN** the browser opens `/login` directly without first rendering `/personal`, `/enterprise` or `/government`, and no protected workspace content is mounted before authorization

#### Scenario: Login succeeds for the intended service role

- **WHEN** authentication succeeds and the backend identity includes the entrance's intended role
- **THEN** the frontend navigates to that role's existing protected workspace, whose existing backend authorization still controls content access

#### Scenario: Login role does not match entrance intent

- **WHEN** authentication succeeds but the backend identity does not include the entrance's intended role
- **THEN** the frontend stays on `/login`, does not enter any workspace automatically, and displays a modal dialog explaining the selected and actual service categories without exposing private identity details

#### Scenario: User accepts the account's actual service

- **WHEN** the mismatch dialog is open and the user chooses to enter the account's actual service
- **THEN** the frontend navigates to an existing workspace for a role returned by the backend and the existing workspace authorization remains in force

#### Scenario: User switches to an account for the selected service

- **WHEN** the mismatch dialog is open and the user chooses to switch accounts
- **THEN** the frontend signs out the current session and returns to the login form while retaining the originally selected public service context

#### Scenario: Login service is unavailable

- **WHEN** required public authentication configuration is missing or sign-in fails
- **THEN** the login view preserves the explicit unavailable/error state and does not create a fake session or Mock success

#### Scenario: Local entrance assets are rendered

- **WHEN** the signed-out home is loaded without access to the legacy site
- **THEN** every entrance uses a repository-local image that decodes successfully with positive dimensions and the page does not depend on a runtime hotlink

### Requirement: Protected workspace visual continuity without permission change

The authenticated header SHALL derive navigation from the backend identity roles. An identity containing individual SHALL see exactly the primary entries 首页、政策中心、历史问答、政民互动. An identity containing enterprise SHALL see exactly those four entries plus 我的企业. The enterprise entry SHALL navigate to an enterprise-guarded, read-only page showing only organization and current-account fields returned by /me. Individual, government, and administrator identities SHALL NOT see the enterprise entry or render enterprise information content. Existing government and administrator navigation capabilities SHALL remain available. Navigation simplification MUST NOT grant roles, bypass route guards, or change API/data permissions.

#### Scenario: Individual user sees focused navigation

- **WHEN** an authenticated identity contains individual and does not contain enterprise
- **THEN** the header shows 首页、政策中心、历史问答、政民互动 and does not show 智能分类、服务状态、个人服务、企业服务 or 我的企业

#### Scenario: Enterprise user sees focused navigation

- **WHEN** an authenticated identity contains enterprise
- **THEN** the header shows 首页、政策中心、历史问答、政民互动、我的企业 and does not show 智能分类、服务状态 or 企业服务

#### Scenario: Enterprise profile is read-only and authorized

- **WHEN** an enterprise identity opens /my-enterprise
- **THEN** the page renders only backend-returned organization name, code, type, region, display name and email fields, with missing values explicitly labeled, and contains no edit or direct database write control

#### Scenario: Non-enterprise identity is denied

- **WHEN** an individual, government, or administrator identity requests /my-enterprise
- **THEN** the existing enterprise role guard denies or withholds the page content and the header does not expose 我的企业

#### Scenario: Authenticated mobile navigation remains usable

- **WHEN** an individual or enterprise page is rendered at 390x844
- **THEN** all role-required navigation entries remain reachable in the existing horizontal navigation behavior without overlap or page overflow, and the enterprise information grid becomes one readable column

#### Scenario: Provisioned user enters an assigned role

- **WHEN** `/me` returns an active identity and the matching workspace endpoint authorizes the requested role
- **THEN** the header and page show only the existing real identity/scope and authorized role entries using the shared visual baseline

#### Scenario: Backend denies the requested role

- **WHEN** the workspace endpoint returns HTTP 403
- **THEN** the frontend shows the existing explicit access-denied state in the shared visual system and does not mount protected role content

### Requirement: Consistent explicit system states

Loading, signed-out, missing-configuration, authentication failure, identity failure, authorization checking, authorization failure, access denied, disabled-feature, health, and not-found views SHALL use the same typography, spacing, surface, action, and focus rules. Restyling MUST NOT merge distinct states, hide retry actions, or silently substitute a Mock result.

#### Scenario: A guarded dependency fails

- **WHEN** an existing auth, identity, permission, feature, or health dependency reports an error
- **THEN** its stable explicit message and retry action where currently provided remain visible and operable within the new presentation

### Requirement: Responsive and accessible essential controls

The frontend SHALL support desktop and mobile layouts down to `320px`, including the acceptance viewport `390x844`, without horizontal page overflow, incoherent overlap, clipped essential text, or layout shifts caused by dynamic identity/role content. The signed-out home SHALL render the three service cards at equal dimensions within the same viewport layout: three equal columns when desktop space permits and a single readable column on mobile. Navigation on non-landing routes, login, retry, role entrances, identity, and sign-out MUST remain visible and keyboard operable. Focus MUST be visibly indicated, media dimensions MUST be stable, and non-essential motion MUST respect `prefers-reduced-motion`.

#### Scenario: Visitor uses a desktop public home

- **WHEN** the signed-out home is rendered at a desktop viewport
- **THEN** its three service cards have equal dimensions, appear as one aligned group, and the page has no global header

#### Scenario: Visitor uses a mobile public home

- **WHEN** the signed-out home is rendered at `390x844`
- **THEN** the three equal-format service cards form one column with readable text and no horizontal overflow or overlap

#### Scenario: Authenticated user uses a mobile viewport

- **WHEN** an authenticated non-landing page is rendered at `390x844`
- **THEN** the product header, authorized navigation, current identity, and sign-out control remain reachable and no essential element is hidden behind another element or outside the horizontal viewport

#### Scenario: Dynamic content is longer than expected

- **WHEN** an identity, organization, route label, error, or control contains its longest supported text
- **THEN** it wraps or truncates deliberately within stable layout constraints and does not overlap adjacent content or resize fixed-format controls incoherently

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

