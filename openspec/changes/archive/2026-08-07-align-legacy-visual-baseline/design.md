## Context

B1.1 delivered a functional React/Vite shell with Supabase sessions, database identity, four server-authorized workspaces, and explicit failure states. Its visual shell is a generic 248px dark-green sidebar that does not resemble the public “政通惠” service. UI1.0 is a bounded presentation patch inserted before policy-library development so later pages inherit one stable design language.

The public site was inspected at desktop and `390x844` through its rendered pages. It uses a prominent “政通惠” identity, a compact white header, pale blue-gray content canvases, blue-purple accents, wide whitespace, and photographic individual/enterprise entrances. UI1.0 translates those cues into the rebuilt architecture; it does not reproduce the legacy DOM or unavailable interactions.

## Goals and Non-Goals

**Goals:**

- make every current route visibly part of the “政通惠” product;
- establish reusable CSS tokens and layout rules before B1.2;
- preserve current route, session, role filtering, backend authorization, and explicit-state contracts;
- keep essential actions usable at desktop and `390x844` mobile sizes;
- localize the two authorized public entrance photographs with documented provenance.

**Non-goals:** policy data, search/RAG, question answering, consultation, new routes, new API calls, role changes, database operations, remote fonts, legacy source migration, pixel-perfect cloning, or fabricated demo content.

## Decisions

### Use one top-header shell for all existing routes

`AppLayout` will retain its navigation arrays, role filtering, identity label, and sign-out callback, but render a semantic top header instead of a sidebar. A single shell avoids route-layout divergence and ensures health, feature, auth, and protected states share the new visual baseline.

Desktop navigation remains compact and wraps only when needed. Mobile uses explicit stable rows for brand/location, navigation, and account/sign-out. The account area is never hidden merely to save space.

### Keep business flow and state ownership unchanged

`WorkspaceHomePage`, `LoginPage`, and `RoleWorkspacePage` may add presentational wrappers and labels only. `AuthProvider`, `RoleGuard`, `FeatureGuard`, API clients, router paths, and role mappings retain ownership of behavior. The personal and enterprise public entrances link to `/personal` and `/enterprise`; the existing guard still decides whether sign-in or protected content appears.

No inactive assistant input, fake policy result, illustrative organization, or simulated workspace operation will be added. Existing error and retry states remain explicit and do not silently fall back.

### Build a reference-derived token system, not a copied stylesheet

Global CSS variables will define neutral ink, muted text, white surfaces, pale blue-gray canvas, blue-purple primary actions, sparse supporting blue/green tints, borders, shadows, spacing, and focus rings. The font stack uses locally available Chinese system fonts. Content widths and media aspect ratios are stable; typography does not scale with viewport width.

The implementation uses repository-authored selectors and components based on visual observation. Legacy JavaScript, CSS, source maps, component code, and runtime behavior are out of scope.

### Localize authorized public photographs

The two homepage JPEGs will be stored under a semantic repository path and imported or served locally. Their original public URLs and dimensions are recorded in `TECH-V1-UI-01`. Cards use a fixed aspect ratio, `object-fit: cover`, and tuned `object-position` so different source ratios do not shift layout. Browser acceptance requires both images to decode with positive natural dimensions.

### Add structural and responsive regression coverage

A focused frontend test will render or inspect the real visual shell/home components and assert the brand, public route targets, role-filtered navigation, identity, and sign-out behavior. The existing mobile auth-control CSS test will follow the new account container rather than the removed sidebar, while continuing to reject hidden sign-out controls. Asset presence/type and required responsive/focus rules will be checked without snapshotting implementation-specific pixels.

Browser QA at desktop and `390x844` verifies image loading, visible controls, no horizontal overflow, and no overlap/clipping. Existing session/guard tests continue to prove protected content behavior.

## API / Data / Permission / Model / Failure Decisions

| Area | Decision |
|---|---|
| API | No route, endpoint, payload, request header, caching, or error-envelope change |
| Data | No schema, record, storage bucket, seed, or business-data change; two static public visual assets are repository files, not application data |
| Permission | `/me` roles and backend workspace authorization remain authoritative; visual links cannot grant access |
| Model/Mock | No classifier/model call and no Mock identity, policy, answer, or fallback |
| Failure | Existing loading, missing-config, auth/identity failure, denied, disabled-feature, and health failure states remain distinct and are only restyled |
| Migration | No Alembic revision and no migration, initializer, reset, delete, or Auth Admin command |
| Sensitive output | Tests and pages do not read or render `.env`, UUID mappings, credentials, database URLs, JWTs, or keys |
| Rollback | Revert UI1.0 presentation files, tests, metadata, and static assets; no backend/database action is needed |

## Risks / Trade-offs

- **Reference drift:** hashed legacy image URLs could change. Local copies with source documentation remove the runtime dependency.
- **Behavior regression from shell refactor:** navigation or sign-out could become unreachable. Structural tests plus desktop/mobile browser acceptance cover these paths.
- **Static entrances mistaken for authorization:** links may look public while routes are protected. Existing guards remain unchanged and tests verify no protected content mounts early.
- **Government/admin discoverability:** a two-card public entrance emphasizes individual/enterprise. Authenticated navigation and ready-home entries still expose every role returned by `/me`.
- **Font mismatch:** the legacy display font is not bundled. A deterministic Chinese system stack preserves readability without unlicensed remote font loading.
- **Overfitting screenshots:** pixel snapshots are brittle. Requirements target hierarchy, tokens, reachability, overflow, and asset decoding rather than exact coordinates.

## Implementation and Verification

1. Strictly validate PRD/TECH/OpenSpec and the UI1.0 development pointer before implementation.
2. Localize and verify the two approved images.
3. Update metadata, `AppLayout`, home/login/workspace presentation, and the shared stylesheet.
4. Update/add frontend structural, asset, and responsive tests.
5. Run frontend tests/build, backend pytest/Ruff/local smoke, read-only runtime smoke, aggregate acceptance, and strict validation.
6. Complete desktop/mobile browser QA, record evidence, archive with main-spec synchronization, and re-run strict validation.

No step runs database migration, seed, reset, delete, or legacy source code.
