## MODIFIED Requirements

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
