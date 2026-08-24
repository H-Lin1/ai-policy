## 1. Migration and data boundary

- [x] 1.1 Confirm UI1.0 adds no database/storage schema, migration, seed, reset, delete, Auth-account mutation, or business-data write.
- [x] 1.2 Localize only the two authorized public entrance photographs, record their source/dimensions, and verify valid non-empty image files without reading legacy source.

## 2. Backend, API, and permissions

- [x] 2.1 Confirm backend routes, API payloads, error envelopes, session handling, role codes, `/me` filtering, workspace authorization, and feature flags remain unchanged.

## 3. Frontend visual baseline

- [x] 3.1 Replace the dark sidebar with the responsive “政通惠” top header while preserving existing public navigation, database-role-filtered entries, identity state, and sign-out.
- [x] 3.2 Add shared visual tokens and restyle public home, login, authenticated home, role summaries, health, loading, failure, denied, disabled-feature, and not-found surfaces without Mock business content.
- [x] 3.3 Add local personal/enterprise image entrances on the signed-out home using the existing protected route targets and stable responsive media dimensions.
- [x] 3.4 Add/update focused shell, home, asset, focus, and mobile account/sign-out regression tests.

## 4. Model and legacy boundary

- [x] 4.1 Add no model/classifier work, Mock result, remote font, or legacy JavaScript/CSS/component/route/payload reuse; independently implement only the observed visual language and authorized static assets.

## 5. Verification

- [x] 5.1 Run full frontend tests and production build.
- [x] 5.2 Run full backend pytest, Ruff, hermetic local smoke, aggregate acceptance, and separately invoked read-only runtime smoke with safe output only.
- [x] 5.3 Verify desktop and `390x844` browser states for `/`, `/login`, representative allowed/denied workspaces, image decoding, navigation/sign-out reachability, horizontal overflow, clipping, and overlap.
- [x] 5.4 Run full OpenSpec strict validation before implementation, before archive, and after archive.

Planning evidence (2026-08-07): the pre-implementation strict validation passed `8/8`.

Frontend evidence (2026-08-07): all 34 frontend scenarios passed, including the 3 new visual-baseline cases, and the TypeScript/Vite production build completed with 91 modules and both local JPEGs fingerprinted into `dist`.

Final pre-archive evidence (2026-08-07): backend pytest passed 186 cases, Ruff passed, local smoke passed `14/14`, read-only configured runtime smoke reported all five checks `ok`, aggregate acceptance passed all 6 constituents, and strict validation passed `8/8`. Browser QA passed desktop public/login plus mobile public/login, real personal allow, real enterprise cross-role deny, and sign-out; no measured page overflowed horizontally and no denied protected scope mounted. No migration, seed, reset, delete, Auth-account mutation, or legacy source read ran.

## 6. Documentation and handoff

- [x] 6.1 Update `PRD-V1-UI-01`, `TECH-V1-UI-01`, frontend documentation, and `DEVELOPMENT_STATUS.md` with final implementation and verification evidence.
- [x] 6.2 Synchronize the new main capability spec through archive, archive `align-legacy-visual-baseline`, re-run strict validation, and advance the development pointer to `B1.2` pending.

Archive evidence (2026-08-07): OpenSpec created the `frontend-visual-baseline` main specification with 5 requirements and archived this change as `2026-08-07-align-legacy-visual-baseline`. Post-archive full strict validation passed all 8 main specifications. The development pointer was advanced only after that result.
