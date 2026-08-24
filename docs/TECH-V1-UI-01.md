# TECH-V1-UI-01 | Legacy-Aligned Frontend Visual Baseline

| Item | Value |
|---|---|
| Document ID | `TECH-V1-UI-01` |
| Version | `V1.2` |
| Status | Accepted and archived |
| Development step | `UI1.0`, between `B1.1` and `B1.2` |
| Product requirement | [`PRD-V1-UI-01`](./PRD-V1-UI-01.md) |
| OpenSpec change | `align-legacy-visual-baseline` |
| Prerequisite | B1.1 accepted and archived; no active OpenSpec change at UI1.0 start |
| Runtime write gate | No database, Auth, migration, seed, reset, or delete operation belongs to this change |

## 1. Engineering Goal

Replace the generic dark-green workbench presentation with a coherent visual system derived from the public “政通惠” site while leaving the rebuilt application architecture intact. The change is intentionally presentation-only: React Router paths, Supabase session coordination, `/me`, role filtering, backend workspace authorization, API errors, and database state do not change.

The implementation should feel related to the legacy public service without copying its frontend source or recreating unavailable business functions. It will use the public pages and two public entrance photographs as references, then implement repository-native React markup and CSS.

## 2. Reference Evidence and Design Translation

| Reference surface | Observed visual behavior | UI1.0 translation |
|---|---|---|
| Public homepage | Centered “政通惠” identity, location/account affordances, white canvas, two large photographic entrances with dark image overlays | Branded public home with local personal/enterprise photographs and existing protected-route links |
| Personal service | Pale blue-gray background, large greeting with blue-purple emphasis, generous centered composition | Shared pale canvas and expressive but compact heading treatment for home and role states; no inactive question box is added |
| Enterprise service | Compact white header, strong blue heading, blue primary actions, light decorative blocks, real Shenzhen photography | Top application header, restrained blue-purple action system, neutral/light supporting colors |
| Mobile views (`390x844`) | Stacked entrance cards, compact header, single-column content, large touch targets | One-column entry/workspace layouts, wrapping navigation/account region, visible sign-out, no horizontal scroll |

Reference URLs inspected on 2026-08-07:

- `https://aipolicy.bnu.edu.cn/`
- public SPA routes reached through the homepage for personal and enterprise service;
- `https://aipolicy.bnu.edu.cn/assets/index_people-BJSWcAI0.jpg`;
- `https://aipolicy.bnu.edu.cn/assets/index_business-C4gkoXkJ.jpg`.

The screenshots define product cues, not an exact DOM/CSS contract. No legacy source repository is read.

## 3. Scope and Ownership

UI1.0 owns presentational markup in `AppLayout`, `WorkspaceHomePage`, `LoginPage`, and `RoleWorkspacePage`, global CSS, page metadata, local entrance assets, and focused frontend rendering/responsive tests. Existing `RoleGuard` and `FeatureGuard` markup may consume the new global classes without changing their state logic.

The following remain unchanged:

- `router.tsx` and all public/role route paths;
- `AuthProvider`, session and role authorization coordinators, and Supabase client setup;
- API client contracts and backend endpoints;
- database schema, RLS, seeded identities, and feature flags;
- classifier/model adapters and all business-data boundaries.

## 4. Visual System

CSS custom properties will centralize the visual language:

| Token group | Direction |
|---|---|
| Canvas/surfaces | White and pale blue-gray (`#f4f7fc` family), with solid white interactive surfaces |
| Text | Near-black navy for primary text, neutral gray for supporting text |
| Accent | Restrained blue-purple (`#5267d9` family) for active navigation, focus, links, and primary actions |
| Supporting accents | Sparse cool blue and pale green blocks; no dominant one-hue gradient or decorative orb system |
| Typography | Local Chinese system stack headed by `Noto Sans SC`, `PingFang SC`, and `Microsoft YaHei`; serif fallback only for selected entrance headings |
| Geometry | Header and controls use predictable dimensions; content surfaces use radii no greater than `8px`, except the existing form/hero entrance treatment where the legacy reference requires a softer edge |
| Motion | Short opacity/transform feedback only, disabled under `prefers-reduced-motion` |

The page does not load remote fonts. Familiar actions remain text where the command is explicit; no icon dependency is added solely for decoration.

## 5. Component and Route Design

### 5.1 Application header

`AppLayout` changes from a fixed sidebar to a full-width header plus main content. It retains the existing navigation arrays and role filtering. The header contains:

- “政通惠” and the service subtitle;
- Shenzhen context;
- existing public and authorized role navigation;
- current identity label;
- the existing sign-out callback when a session exists.

At narrow widths the header becomes a stable multi-row layout. Navigation scroll/wrap behavior must not cover the identity row, and `.sign-out-button` remains rendered and visible.

### 5.2 Home

Signed-out and configuration/error/loading branches keep their current state semantics. The signed-out home adds a visual brand introduction and two image-backed service entrances linking to `/personal` and `/enterprise`; guards continue to own authentication. The ready home shows real identity/scope and maps the same filtered role entries without placeholder policy content.

### 5.3 Login and protected workspaces

`LoginPage` retains its local input, busy, disabled, error, and successful redirect logic. Only layout, labels around the form, and CSS classes change.

`RoleWorkspacePage` retains `RoleGuard` and the exact `WorkspaceResponse`/identity data. Role codes may select a presentational label or accent but may not select fabricated business content. Scope summaries remain real API data.

Health, feature, access, and not-found states continue using current components and text, with the new shared token and surface styles.

## 6. Assets and Provenance

The two public homepage photographs are stored in `frontend/src/assets/ui1/` using stable repository filenames and are fingerprinted by Vite for production. Runtime pages reference only these local assets. The implementation records the public source URLs above and does not hotlink, inspect source maps, or copy legacy component code.

Asset acceptance checks verify both files are non-empty images and that browser `naturalWidth` is positive. If either asset cannot be acquired, implementation pauses before replacing it with unrelated stock imagery.

The implemented Vite source path is `frontend/src/assets/ui1/` so production builds fingerprint the files. Verified assets are:

| File | Dimensions / bytes | SHA-256 |
|---|---|---|
| `individual-service.jpg` | `960x721` / `133890` | `32aa11edb98ac3fc0d03a4543d5b8b043d9579268fbf39b7bc2d2bc4144287d6` |
| `enterprise-service.jpg` | `1199x685` / `76322` | `8c88e302bcf75bb972d64f05b076c8a48b285e063c56e8ace8672291ca772865` |

## 7. API, Data, Permission, Model, Failure, and Migration Decisions

| Area | Decision |
|---|---|
| API | No endpoint, payload, request, route, cache, or error-envelope change |
| Data | No database or Supabase data read/write beyond existing runtime behavior; no new business data |
| Permission | Existing database role filtering and server workspace authorization remain authoritative; visual entrances never grant access |
| Model/Mock | No model invocation, classifier migration, Mock identity, fake policy, or fake answer |
| Failure | Existing loading, missing-config, auth error, identity error, denied, feature-disabled, and health states remain explicit and receive consistent presentation |
| Migration | No Alembic revision and no migration/seed/reset/delete command |
| Sensitive data | No `.env` field, credential, UUID, JWT, connection string, or key is added to markup, assets, tests, or output |
| Rollback | Revert the UI1.0 frontend files, tests, docs/spec, and local images; backend/database rollback is unnecessary |

## 8. Verification Plan

Before coding, strictly validate the PRD/TECH-backed OpenSpec change. After implementation, run:

1. focused frontend rendering and responsive CSS tests, then full `npm test`;
2. TypeScript/Vite production build;
3. full backend pytest, Ruff, and hermetic local smoke to prove no cross-layer regression;
4. read-only configured runtime smoke;
5. aggregate acceptance;
6. OpenSpec strict validation before and after archive;
7. browser QA at `1440x900` and `390x844` for `/`, `/login`, representative role/denied states, navigation/sign-out reachability, image load, horizontal overflow, clipping, and overlap.

No verification step may invoke Alembic, IAM seed, demo reset, delete, Auth Admin, or legacy source.

## 9. Implementation Order

1. Approve PRD/TECH, create OpenSpec proposal/spec/design/tasks, update the development pointer, and pass strict validation.
2. Localize the two approved public images and update metadata.
3. Implement the top header and shared visual tokens.
4. Restyle the public, login, role, health, guard, and error surfaces without changing behavior.
5. Add/update rendering and responsive tests.
6. Run the complete non-destructive verification and visual matrix.
7. Record evidence, synchronize the main capability spec through archive, revalidate, and move the pointer to `B1.2` pending.

## 10. Acceptance Evidence

| Check | Result |
|---|---|
| Pre-implementation OpenSpec | Full strict validation passed `8/8` before frontend files changed |
| Asset contract | Both JPEGs passed file/type, exact byte size, dimensions, SHA-256, production bundling, and browser `complete/naturalWidth` checks |
| Frontend tests | 34 scenarios passed: FeatureGuard 5, session coordinator 8, role guard 17, visual baseline 3, responsive auth 1 |
| Frontend build | TypeScript/Vite passed; 91 modules transformed; both local images emitted with content hashes |
| Backend regression | 186 pytest cases passed with one non-blocking upstream TestClient deprecation warning; Ruff passed; local smoke `14/14` |
| Configured runtime | Read-only database, project binding, exact IAM schema, Auth configuration, and JWKS checks all reported `ok` |
| Aggregate acceptance | `backend_tests`, `ruff`, `local_smoke`, `frontend_guards`, `frontend_build`, and `openspec_strict` all reported `ok` |
| Browser layout | Desktop `1440x900` public home/login and mobile `390x844` public/login/real-allowed/real-denied/sign-out paths passed; all measured mobile pages had no horizontal overflow |
| Real role behavior | Personal account exposed only `/personal`; allowed workspace returned 3 scope items; enterprise cross-role route showed “无权访问” with no `.scope-grid`; sign-out removed protected content |
| Destructive/write boundary | No Alembic, IAM seed, reset, delete, Auth Admin, database write, or legacy source operation ran |
| OpenSpec archive | New main `frontend-visual-baseline` spec contains 5 requirements; post-archive full strict validation passed `8/8` |

The only non-blocking verification warning is the existing Starlette TestClient/httpx deprecation notice. The virtual-environment invocation also reports a relative-path `sys.prefix` warning during runtime/aggregate checks; all named checks pass.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-07 | V1.0 | Defined the UI1.0 reference-derived visual system, presentation-only implementation boundary, local asset provenance, responsive acceptance, and non-destructive verification plan. |
| 2026-08-07 | V1.1 | Recorded the implemented top-header/home/login/workspace baseline, asset hashes, full automated/runtime acceptance, and real mobile role allow/deny/sign-out evidence. |
| 2026-08-07 | V1.2 | Recorded main-spec synchronization, OpenSpec archive, post-archive strict validation, and handoff to B1.2 pending. |
