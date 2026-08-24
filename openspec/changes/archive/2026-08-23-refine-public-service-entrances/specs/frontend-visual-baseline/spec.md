## MODIFIED Requirements

### Requirement: Public entrance and real authentication continuity

The signed-out home SHALL omit the global header and SHALL present “政通惠” as its primary in-page title with “一站式政策服务平台” as its subtitle. It SHALL provide three equal-size personal, enterprise and government photographic entrance cards in one primary group and SHALL NOT show a separate small-text login entrance. Every card SHALL navigate directly to `/login` while preserving its role intent. After successful authentication, the frontend MAY navigate to the intended protected workspace only when the backend identity contains that role; otherwise it SHALL expose only the identity's actually authorized destinations. Entrances MUST NOT create a local identity, bypass a route guard, mount protected content, or display fabricated results.

#### Scenario: Signed-out visitor chooses a service entrance

- **WHEN** a signed-out visitor activates the personal, enterprise or government entrance
- **THEN** the browser opens `/login` directly without first rendering `/personal`, `/enterprise` or `/government`, and no protected workspace content is mounted before authorization

#### Scenario: Login succeeds for the intended service role

- **WHEN** authentication succeeds and the backend identity includes the entrance's intended role
- **THEN** the frontend navigates to that role's existing protected workspace, whose existing backend authorization still controls content access

#### Scenario: Login role does not match entrance intent

- **WHEN** authentication succeeds but the backend identity does not include the entrance's intended role
- **THEN** the frontend does not enter that role workspace and does not grant or fabricate the missing role

#### Scenario: Login service is unavailable

- **WHEN** required public authentication configuration is missing or sign-in fails
- **THEN** the login view preserves the explicit unavailable/error state and does not create a fake session or Mock success

#### Scenario: Local entrance assets are rendered

- **WHEN** the signed-out home is loaded without access to the legacy site
- **THEN** every entrance uses a repository-local image that decodes successfully with positive dimensions and the page does not depend on a runtime hotlink

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
