## 1. Repository and runtime setup

- [x] 1.1 Create the root README, `.gitignore`, development status ledger, and environment templates without importing legacy files.
- [x] 1.2 Add the backend Python project metadata, dependency lock guidance, package markers, and the frontend Vite/TypeScript project metadata.
- [x] 1.3 Document the supported local runtime versions and the separate frontend/backend start commands.

## 2. Backend foundation

- [x] 2.1 Implement typed settings loading, environment validation, safe CORS configuration, and feature flags.
- [x] 2.2 Implement the FastAPI application factory, `/api/v1` router registration, lifespan logging, and module boundaries.
- [x] 2.3 Implement request ID middleware, structured request logging, and the standard application error envelope.
- [x] 2.4 Implement live, ready, aggregate health, and model-readiness endpoints with explicit degraded/503 behavior.
- [x] 2.5 Implement Supabase/PostgreSQL SQLAlchemy session setup and an Alembic environment with the foundation schema migration.
- [x] 2.6 Implement bearer-token verification boundary and the protected `/api/v1/me` endpoint; keep legacy `/classify` absent.
- [x] 2.7 Implement the `DepartmentClassifier` protocol, typed result models, and the explicit unavailable adapter.

## 3. Frontend foundation

- [x] 3.1 Add the React application shell, router, responsive layout, and placeholder workspace page.
- [x] 3.2 Add the single public API client, health page, loading/error/retry states, and configured API base URL.
- [x] 3.3 Confirm no legacy frontend imports, hard-coded business Mock data, or secret environment variables enter the build.

## 4. Scripts and verification

- [x] 4.1 Add migration, demo initialization/reset, and local smoke-test scripts with clear failure messages.
- [x] 4.2 Add backend tests for health, readiness degradation, request IDs, error shape, auth rejection, model-not-ready behavior, and legacy route absence.
- [x] 4.3 Install dependencies where available and run backend tests, frontend type/build checks, OpenSpec strict validation, and the smoke script.
- [x] 4.4 Record test evidence, runtime caveats, and the next baseline step in `DEVELOPMENT_STATUS.md`.

## 5. Documentation and handoff

- [x] 5.1 Create and review `docs/TECH-V1-S0-01.md` with scope, directory responsibilities, environment variables, startup flow, and acceptance scenarios.
- [x] 5.2 Ensure README, OpenSpec artifacts, API paths, migration instructions, and status ledger agree.
- [x] 5.3 Mark the change ready for acceptance; archive only after all evidence is recorded.
