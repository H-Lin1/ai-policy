## MODIFIED Requirements

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
