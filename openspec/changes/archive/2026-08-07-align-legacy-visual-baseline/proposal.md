## Why

`PRD-V1-UI-01` / `TECH-V1-UI-01` / step `UI1.0` must restore product continuity before `B1.2`. The rebuilt frontend has accepted B1.1 authentication and role authorization, but its generic dark-green sidebar and “AI” workbench identity are materially different from the public “政通惠” service. Continuing business development on that divergent shell would spread visual rework across every later slice.

## What Changes

- Replace the fixed dark sidebar with a compact white top header carrying the “政通惠” identity, Shenzhen context, existing public navigation, database-role-filtered navigation, current identity, and visible sign-out.
- Establish shared white/pale blue-gray surfaces, near-black text, restrained blue-purple actions, Chinese system typography, spacing, focus, and responsive tokens.
- Recompose the signed-out home around two locally stored personal/enterprise entrance photographs from the authorized public reference site while keeping links on the existing protected routes.
- Restyle login, authenticated home, role workspace summaries, health, loading, error, denied, disabled-feature, and not-found states without changing their logic or data.
- Add focused rendering, asset, and responsive regression checks plus desktop/mobile browser acceptance.
- Independently implement the observed visual language. Do not copy legacy JavaScript, CSS, components, routes, payloads, application state, or business behavior.

## Capabilities

### New Capabilities

- `frontend-visual-baseline`: define the cross-route product identity, visual continuity, local reference assets, responsive behavior, and state presentation required before B1.2.

### Modified Capabilities

- None. Existing `identity-access`, `runtime-observability`, and route/API requirements remain behaviorally unchanged.

## Impact

- Affects frontend presentational markup, global styles, page metadata, local static images, frontend rendering/responsive tests, and frontend documentation.
- Updates `docs/PRD-V1-UI-01.md`, `docs/TECH-V1-UI-01.md`, `DEVELOPMENT_STATUS.md`, and the OpenSpec governance wording that distinguishes authorized static visual assets from prohibited legacy frontend source reuse.
- Adds no backend route, API contract, database table, migration, seed, reset, Auth-account operation, model/Mock result, or new secret configuration.
- Runtime rollback is frontend-only and does not require database or API rollback.
