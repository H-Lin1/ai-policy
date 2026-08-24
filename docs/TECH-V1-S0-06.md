# TECH-V1-S0-06 | Initialization, Demo Reset, Smoke, and Stage 0 Acceptance

| Item | Value |
|---|---|
| Document ID | `TECH-V1-S0-06` |
| Version | `V1.1` |
| Status | Archived |
| Development step | `S0.6` |
| OpenSpec change | [`2026-08-06-complete-stage-zero-acceptance`](../openspec/changes/archive/2026-08-06-complete-stage-zero-acceptance/) |
| Prerequisites | `S0.1` through `S0.5` are archived |
| Goal | Close Stage 0 with repeatable, safe operator preflight, non-destructive demo-reset behavior, and one evidence-producing acceptance entry point. |

## 1. Scope

Stage 0 already has the application skeleton, real Supabase/JWKS runtime boundary, API contracts, observability, feature guards, and a fail-closed classifier adapter. S0.6 does not add a business capability. It makes the final operational workflow explicit and safe:

1. initialization defaults to an inspect-only preflight and does not mutate a database;
2. a migration can only be requested through explicit operator acknowledgement, and is never invoked by automated Stage 0 acceptance;
3. demo reset remains a no-op because Stage 0 owns no business seed data or business tables;
4. a hermetic local smoke check and a separately opted-in configured-runtime smoke check remain distinct;
5. a Stage 0 acceptance script runs the local verification matrix without printing secrets, launching destructive actions, or reading legacy sources;
6. README, OpenSpec, and the status ledger describe the same workflow and final evidence.

## 2. Boundaries and Non-Goals

S0.6 MUST NOT create, alter, seed, truncate, delete, or drop database objects or Supabase data during normal checks. It MUST NOT run `alembic upgrade`, `alembic downgrade`, SQL reset commands, or a data import unless an operator explicitly invokes the separately guarded initialization command after reviewing its target. The acceptance script never calls that command.

There are no business tables, policy records, demo users, model assets, or classifier results to reset in Stage 0. Therefore `reset_demo.py` remains an acknowledged no-op and must not grow `DELETE`, `TRUNCATE`, `DROP`, filesystem deletion, or Supabase write behavior. The first business reset, if any, requires its own approved PRD/TECH/OpenSpec change.

Do not read, import, copy, or reuse old project source, routes, payloads, frontend, data, models, search/RAG/FAISS/Embedding logic, or startup code. The future verified classifier computation remains outside this change. No new API, frontend business page, migration, dependency, or Mock data is introduced.

## 3. Operational Design

### 3.1 Initialization command

`backend/scripts/init_demo.py` becomes a command with an inspect-only default. It reports only safe state such as whether `DATABASE_URL` is configured; it never echoes its value. It exits successfully for a missing local database configuration while explaining that no operation was performed.

The command accepts a deliberately named `--apply-foundation-migration` flag only together with `--confirm`. Before invoking Alembic it requires a configured PostgreSQL target and prints an operator warning without a connection string. The subprocess receives a fixed argument vector and config path for only the existing foundation revision (`python -m alembic -c backend/alembic.ini upgrade 0001_foundation_schema`), captures its output, and returns a safe named result. The already-validated URL is explicitly bound into the child environment and any ambient `ALEMBIC_CONFIG` override is removed, so child execution cannot silently diverge from preflight. Pinning the config and revision prevents an ambient override or future business migration from being run by a historical foundation command.

### 3.2 Demo reset command

`backend/scripts/reset_demo.py` stays a deterministic no-op. Without `--confirm` it errors before doing anything. With it, it emits a truthful statement that Stage 0 has no managed business data and returns success. It deliberately has no database import, no `subprocess` call, and no destructive SQL/filesystem operation.

### 3.3 Verification entry point

Add `backend/scripts/acceptance.py` as an orchestrator for non-destructive checks. It runs the project-local backend test suite, Ruff, hermetic `smoke.py`, frontend feature-guard test, frontend production build, and strict OpenSpec validation from fixed working directories. It does not call `init_demo.py`, `reset_demo.py`, Alembic, or `runtime_smoke.py`.

Configured Supabase/JWKS verification remains a separate explicit command (`runtime_smoke.py`) because it connects to external services. It performs only read-only PostgreSQL checks for connectivity, the `app` schema, `0001_foundation_schema`, and zero Stage 0 business tables, plus authentication/JWKS checks. It keeps output to named status values and catches unexpected exceptions so it cannot emit tracebacks that may contain configured values. It is permitted only as a read-only verification, never as part of a reset or migration flow. The prior S0.2 migration evidence remains authoritative; S0.6 does not run a migration to create or repair that state.

Hermetic smoke imports the side-effect-free application factory from `app.factory` and passes a complete `Settings(_env_file=None, ...)` object. `app.main` remains the Uvicorn ASGI entry point but no longer owns factory implementation. This prevents its module-level `app` construction from reading malformed ambient settings before smoke isolation and failure sanitization take effect. Configured runtime smoke rejects every command-line argument before settings or external dependencies are accessed.

### 3.4 Evidence and failure behavior

The acceptance script reports only check names and pass/fail outcome. It forwards no environment values and avoids command shell interpolation. A failed child check causes a non-zero aggregate exit, while remaining non-dependent checks may still run to show the complete local quality picture. No real service failure is relabeled as a pass or replaced with Mock data.

## 4. Data, API, Permission, and Model Decisions

| Area | Decision |
|---|---|
| API | No endpoint or API response changes. Existing `/api/v1` contracts remain authoritative. |
| Data | No schema/data change in S0.6. The existing foundation migration is not executed by this change's tests or acceptance script. |
| Permissions | Migration remains an explicit local operator action; no web endpoint can trigger it. Demo reset has no privileged effect. |
| Models/Mock | No model load, import, prediction, or Mock result. The classifier remains fail-closed/not-ready until a later approved change. |
| Failure | Missing configuration and failed checks have explicit exit codes/messages without paths, connection strings, JWTs, tokens, or stack traces. |

## 5. Acceptance Matrix

| Check | Expected evidence |
|---|---|
| Bare initialization | Does not invoke Alembic or mutate data; emits only safe preflight state. |
| Guarded migration request | Requires both named apply flag and `--confirm`; absence of a PostgreSQL configuration fails before spawning Alembic; the only permitted revision is `0001_foundation_schema`. |
| Demo reset | Requires acknowledgement and remains an explicit no-op, with no database/filesystem mutation. |
| Local smoke | Existing 12 assertions pass using isolated settings and no external configuration. |
| Runtime smoke | When explicitly run against configured services, reports read-only database/foundation/auth/JWKS status names and no sensitive values; it does not execute a migration. |
| Aggregate acceptance | Runs backend tests, Ruff, local smoke, frontend guard/build, and strict OpenSpec validation; does not run migrations or resets. |
| Documentation | README, this TECH, OpenSpec, and `DEVELOPMENT_STATUS.md` agree on commands, non-goals, safety gates, evidence, and next step. |

## 6. Risks and Rollback

- A convenience command can be mistaken for permission to alter a shared database. The default is therefore preflight-only and the mutating path needs two explicit flags. Operators must still verify the target before using it.
- An aggregate script can accidentally become a broad automation surface. It uses fixed commands and has no arbitrary command, shell, migration, or reset option.
- Runtime smoke needs network and configured services. It stays separate from the hermetic acceptance path and reports external failures honestly.
- Rollback removes only the command guards, acceptance script, tests, and documentation. No migration or data rollback is required because S0.6 does not execute a migration or write data.

## 7. Implementation Order

1. Create and strictly validate the S0.6 OpenSpec artifacts.
2. Add guarded initialization/reset behavior and focused no-mutation tests.
3. Add the non-destructive acceptance orchestrator and hardened runtime-smoke failure reporting.
4. Run the required test, lint, frontend build, local/runtime smoke, bound-runtime, and strict validation matrix without performing migrations or reset writes.
5. Record evidence, sync specs, archive the change, and move the status pointer to the first B1 step.

## 8. Implementation and Verification Evidence

Acceptance date: 2026-08-06.

| Check | Result |
|---|---|
| Planning gate | TECH, proposal, two delta specs, design, and tasks completed before code; active-change and full strict validation passed 6/6. |
| Script safety tests | 19 focused test functions / 20 executed cases cover migration gates, fixed revision/config/cwd/argv, validated child target binding despite hostile ambient variables, hidden child output, reset subprocess/filesystem guards, pre-import hermetic smoke, PostgreSQL-only runtime checks, read-only foundation queries, JWKS/schema exception sanitization, argument rejection, and the exact fixed acceptance matrix. |
| Backend regression | 114 tests passed; the only warning is the existing Starlette/httpx deprecation notice. |
| Python quality | Full Ruff check passed with no findings. |
| Initialization/reset | Bare initialization reported `not_requested`; confirmed reset reported `no_stage_zero_business_data`; neither spawned Alembic nor changed database/filesystem state. |
| Local smoke | All 12 live/ready/auth/model/legacy/CORS/request-ID/feature checks passed with isolated settings. |
| Aggregate acceptance | `backend_tests`, `ruff`, `local_smoke`, `frontend_feature_guard`, `frontend_build`, and `openspec_strict` all reported `ok`; migration, reset, and external runtime smoke are absent from its fixed matrix. |
| Frontend | Feature guard loading/error/disabled/missing/enabled states passed; production build transformed 37 modules successfully. |
| Configured runtime | Read-only runtime smoke reported database, foundation schema/revision/zero-business-table invariant, authentication configuration, and JWKS all `ok`. |
| Bound process | Uvicorn on `127.0.0.1:8016` returned live/ready 200 with `no-store`, propagated live/ready/CORS request IDs, returned OpenAPI 200, emitted JSON lifecycle/request logs, and shut down with exit 0 after the application-factory extraction. |
| Static/data boundary | No new migration revision or business table; no legacy/model/data import; build scan found no connection-string, private-key, JWT-shaped, or Legacy JWT-secret marker; no Alembic apply/downgrade, delete/reset write, or Supabase write was executed. |
| Pre-archive OpenSpec | `openspec validate --all --strict --no-interactive`: 7 passed, 0 failed. |
| Post-archive OpenSpec | `openspec validate --all --strict --no-interactive`: 6 passed, 0 failed. |

## 9. Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-06 | V1.0 | Proposed the S0.6 safe initialization, non-destructive reset, smoke, and Stage 0 acceptance workflow. |
| 2026-08-06 | V1.1 | Implemented the guarded scripts, read-only foundation runtime check, aggregate acceptance command, documentation corrections, and complete acceptance matrix. |
| 2026-08-06 | V1.2 | Bound the validated migration target/config into Alembic, separated the side-effect-free application factory from the ASGI instance, and expanded hostile-environment and no-mutation regression coverage. |
| 2026-08-06 | V1.3 | Archived the accepted OpenSpec change and recorded the post-archive strict validation result. |
