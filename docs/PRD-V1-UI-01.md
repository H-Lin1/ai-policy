# PRD-V1-UI-01 | Legacy-Aligned Frontend Visual Baseline

## 0. Basic Information

| Field | Value |
|---|---|
| PRD ID / feature | `PRD-V1-UI-01` / Legacy-aligned frontend visual baseline |
| Baseline step | Visual patch `UI1.0`, inserted between `B1.1` and `B1.2` |
| Version / status | `V1.2` / Accepted and archived |
| Priority | P0 before `B1.2` |
| Confirmation basis | User instruction to preserve the visual style of `https://aipolicy.bnu.edu.cn/` after the rebuild |
| Confirmed date | 2026-08-07 |
| Prerequisite | `B1.1` archived; current authentication, role guards, routes, and configured runtime accepted |
| Technical plan | [`TECH-V1-UI-01`](./TECH-V1-UI-01.md) |
| OpenSpec change | `align-legacy-visual-baseline` |
| Feishu document | [PRD-V1-UI-01](https://a9ihi0un9c.feishu.cn/docx/MBDudlnbDoLyF8xgBfWcHSUGnMh) |

**Delivery:** The rebuilt application presents a recognizable “政通惠” visual identity across public, login, protected, loading, failure, and access-denied views while preserving every accepted B1.1 authentication and authorization behavior.

## 1. Background and User Need

The rebuilt frontend is functionally correct but currently uses a dark green left sidebar, an “AI” badge, and a generic workbench composition. The legacy public site uses a materially different visual language: a white and pale blue-gray canvas, compact top navigation, a prominent “政通惠” wordmark, restrained blue-purple accents, generous whitespace, and photographic personal/enterprise entrances.

Users should recognize the rebuilt service as the same product even though its implementation, authentication flow, and business architecture have been replaced. Visual continuity must not reintroduce legacy routes, frontend source, Mock business results, or outdated authorization behavior.

The reference was inspected through the public site at desktop and `390x844` mobile sizes on 2026-08-07. The observed pages were the public entrance, personal service view, enterprise service view, and enterprise login modal. These references define direction and hierarchy, not pixel-perfect cloning.

## 2. Goals, Scope, and Non-Goals

**Goals:**

- restore the “政通惠 / 一站式政策服务平台” product identity;
- replace the dark sidebar shell with a compact, responsive top navigation consistent with the public reference;
- apply a shared neutral and pale blue-gray visual system with blue-purple emphasis to all current routes and states;
- use locally stored copies of the two public entrance photographs for a reliable personal/enterprise entry experience;
- keep login, role filtering, server-side workspace authorization, feature guards, retry behavior, and sign-out unchanged;
- keep navigation and sign-out reachable without horizontal overflow or hidden controls at `390x844` and desktop widths.

| Scope | Content |
|---|---|
| Included | Global design tokens; top application header; public/signed-out home; login page; ready home; four role workspace summaries; health, feature, loading, failure, denied, and not-found presentation; local visual assets; responsive and rendering regression tests |
| Excluded | API or route changes; Supabase session changes; RBAC changes; database migration/seed/reset/delete; policy data or search; question-answering UI without a real service; Mock results; model/classifier work; legacy source-code migration |

## 3. Experience Requirements

### 3.1 Product shell

- The visible product name is “政通惠”, supported by “一站式政策服务平台”.
- The shell uses a white compact top header with product identity, Shenzhen context, current navigation, identity state, and sign-out when authenticated.
- Public and role navigation remains derived from the existing route map and database roles. Government and administrator workspaces remain reachable for authorized users.
- The shell must not obscure route content, force a persistent desktop sidebar, or hide the only sign-out action on mobile.

### 3.2 Public entrance and login

- A signed-out visitor sees a branded introduction and two photographic personal/enterprise service entrances inspired by the legacy homepage.
- Entry links use the existing `/personal` and `/enterprise` protected routes. They do not bypass the role guard or fabricate an identity.
- `/login` keeps the existing Supabase email/password submission and all missing-configuration, busy, and error behavior, but adopts the new centered, light visual treatment.

### 3.3 Authenticated workspaces and system states

- An authenticated home shows the real display name, real organization/region scope, and only role entries returned by `/me`.
- Each protected role page continues to mount only after backend authorization and displays only the existing real identity/workspace summary.
- Loading, signed-out, unavailable, denied, disabled-feature, health, and 404 states use the same typography, spacing, color, focus, and surface rules.
- UI1.0 must not add inactive search boxes, fake policy cards, sample answers, or decorative controls that imply unavailable behavior.

### 3.4 Responsive and accessibility baseline

- At `390x844`, all essential navigation, identity, login, role entry, retry, and sign-out controls remain visible and operable.
- At desktop sizes, content remains centered and legible with stable maximum widths; there is no incoherent overlap or excessive empty sidebar region.
- The page has no horizontal overflow at supported widths down to `320px`.
- Keyboard focus is visible; landmarks and existing accessible names remain intact; text and controls maintain readable contrast.
- Motion is restrained and respects `prefers-reduced-motion`.

## 4. Acceptance Criteria

| ID | Given | When | Then |
|---|---|---|---|
| AC-UI-01 | Signed-out visitor | Opens `/` at desktop or mobile width | “政通惠” identity, subtitle, and personal/enterprise photographic entrances render without overflow; links target existing protected routes |
| AC-UI-02 | Signed-out or configuration-missing visitor | Opens `/login` | The real Supabase form or explicit unavailable state is presented in the new visual system; no fake session is created |
| AC-UI-03 | Provisioned user | Session resolves through `/me` | Header and home expose only role routes allowed by the existing database identity, with identity and sign-out visible |
| AC-UI-04 | Authenticated user | Opens an assigned or unassigned role route | Existing backend authorization still decides allowed versus denied content, and both outcomes use the shared visual baseline |
| AC-UI-05 | Any current route/state | Rendered at `1440x900` and `390x844` | There is no horizontal overflow, clipped essential text, overlapping controls, hidden sign-out, or failed local entrance image |
| AC-UI-06 | Repository acceptance is run | Tests, Ruff, frontend build, local/runtime smoke, and OpenSpec strict validation execute | All checks pass without migration, seed, reset, delete, Auth-account mutation, or sensitive output |

## 5. Constraints and Rollback

- The public legacy site is a visual reference and asset source only. UI1.0 independently implements React structure and CSS in this repository and does not read or copy legacy frontend source.
- Public reference photographs are stored locally with their source URLs documented in the technical plan. No remote runtime hotlink is required.
- No new browser secret or environment field is introduced.
- Rollback consists only of reverting UI1.0 frontend/docs/spec files and local image assets. No database or API rollback is involved.

## 6. Acceptance Evidence

| Check | Result |
|---|---|
| Planning gate | PRD, TECH, proposal, new capability spec, design, and tasks existed before frontend implementation; pre-implementation strict validation passed `8/8` |
| Frontend automated acceptance | 34 scenarios passed, including 3 new visual-shell/local-asset cases; TypeScript/Vite production build passed with 91 modules |
| Backend regression | 186 tests passed; Ruff passed; hermetic local smoke passed `14/14` |
| Runtime and aggregate | Read-only runtime smoke passed database, target binding, IAM schema, Auth configuration, and JWKS; aggregate acceptance passed all 6 constituents |
| Desktop browser | `1440x900` public home and login rendered the new top header, pale canvas, photographic entrances, and login surface without overlap or horizontal overflow |
| Mobile browser | `390x844` public home/login, real personal role home/workspace, cross-role enterprise denial, and sign-out passed; account/sign-out stayed visible and `documentWidth == innerWidth` |
| Permission preservation | Real personal identity exposed only `/personal`; assigned workspace rendered 3 real scope fields; denied enterprise route rendered no protected scope |
| Data safety | No migration, seed, reset, delete, Auth-account mutation, legacy-source read, or new sensitive configuration was performed |
| OpenSpec archive | `frontend-visual-baseline` main spec created with 5 requirements; post-archive strict validation passed `8/8` |

**Acceptance conclusion:** UI1.0 meets all product acceptance criteria and is ready for OpenSpec archive. Credentials used for the authorized real-session browser check remained in memory only and were cleared after sign-out.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-07 | V1.0 | Approved the legacy-aligned visual baseline patch before B1.2, with explicit B1.1 behavior preservation and no database or legacy-source migration. |
| 2026-08-07 | V1.1 | Recorded completed frontend implementation, automated/runtime/browser acceptance, preserved real role authorization, and readiness for archive. |
| 2026-08-07 | V1.2 | Synchronized the main visual-baseline specification, archived OpenSpec, passed post-archive strict validation, and advanced the pointer to B1.2 pending. |
