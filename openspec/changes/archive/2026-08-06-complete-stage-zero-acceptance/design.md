## Context

See `proposal.md` and the delta specs. Stage 0 already supplies a repeatable foundation migration, a reset placeholder, local and configured smoke scripts, frontend checks, and archived evidence through S0.5. The remaining problem is operational safety: `init_demo.py` currently starts Alembic on a bare invocation, reset lacks direct regression coverage, and final acceptance requires manually composing commands.

## Goals / Non-Goals

**Goals:**

- Make normal operator and CI-style validation non-mutating by construction.
- Preserve the previously approved foundation migration as a consciously requested local operator action, never as an acceptance side effect.
- Make the lack of Stage 0 demo data an explicit, tested reset contract rather than an invitation to add destructive cleanup.
- Make final local acceptance easy to repeat and safe to run without external credentials.

**Non-Goals:**

- No new public API, frontend feature, business schema, seed data, migration revision, data import, deletion, or Supabase write.
- No database migration execution in S0.6 verification, including against the configured Supabase project.
- No migration of verified classifier computation, model assets, legacy routes/payloads/state, search/RAG/FAISS/Embedding behavior, Mock data, startup code, or frontend.
- No CI provider integration, release packaging, scheduled job, or generic command runner.

## Decisions

### Default to preflight and require two independent migration acknowledgements

The initialization command parses `--apply-foundation-migration` and `--confirm`; all other invocations are preflight only. The apply flag identifies the exact authorized action, while confirmation prevents accidental execution through copy/paste or a broad script wrapper. It validates that a PostgreSQL URL is configured before constructing a fixed `subprocess.run` argument list for `alembic -c <backend/alembic.ini> upgrade 0001_foundation_schema`. The validated URL is bound explicitly into the child environment, and any ambient `ALEMBIC_CONFIG` override is removed, so the spawned process cannot silently select a different target or configuration from the one that passed preflight. It never renders the configured URL or Alembic output. Pinning the config and existing foundation revision prevents ambient overrides or future business revisions from being included in a historical convenience command. A single `--confirm` flag was rejected because it does not identify which potentially mutating operation is requested; leaving the current no-argument migration was rejected because it makes final validation unsafe.

### Treat reset as a permanent Stage 0 no-op, not a generic cleanup command

The reset command retains acknowledgement for operator clarity but has no database, filesystem, or network dependency. Tests assert both no-confirm failure and confirmed success, as well as the absence of any mutation helper invocation. A generic reset target, `--force`, or table list was rejected: there are no Stage 0 owned records and adding one would create a data-lifecycle contract before a business change approves it.

### Use a narrow Python acceptance orchestrator instead of shell composition

`acceptance.py` owns a fixed list of child commands with explicit working directories: root virtual-environment Python tests/Ruff, backend local smoke, frontend guard test/build, and strict OpenSpec validation. It prints only named pass/fail states, retains a non-zero aggregate status, and never receives arbitrary command arguments. It does not call initialization/reset/runtime smoke. A shell script was rejected because argument quoting and environment echoing are easier to get wrong; a broad task runner was rejected because no dependency is necessary.

### Keep configured runtime smoke opt-in and sanitize unexpected failures

Runtime smoke is intentionally outside local acceptance because it contacts configured Supabase/JWKS services. It rejects every command-line argument before loading settings, validates that the configured database target is PostgreSQL before it permits read-only connectivity and foundation-state queries (`app` schema, `alembic_version=0001_foundation_schema`, and zero `app` business tables), then maps expected or unexpected operational errors to stable public status strings. It avoids printing exception messages, URLs, headers, token material, or tracebacks. Treating unavailable external services as local acceptance failures was rejected: it would make a fresh checkout dependent on secrets and network availability.

### Separate application construction from the ambient ASGI instance

`app.factory.create_app` owns application construction without instantiating a global application, while `app.main` remains the Uvicorn entry point that exports `app = create_app()`. Hermetic smoke imports the side-effect-free factory and passes a fully explicit `Settings(_env_file=None, ...)` object, so malformed ambient runtime values cannot be read before the smoke exception boundary. Keeping smoke's import pointed at `app.main` was rejected because module import would construct an ambient-configured application before isolated settings existed.

### API/data/permission/model/failure decisions

No API contract changes; existing request ID, error envelope, readiness, and `no-store` behavior remain unchanged. No schema/data operation is authorized. The filesystem/DB action boundary stays CLI-only and requires operator flags. The classifier remains unloaded and not-ready; no Mock outcome is added. Any script failure returns a non-zero exit and safe named status rather than a fabricated success or detailed exception.

## Risks / Trade-offs

- [An explicit apply command can still be run against the wrong configured database] -> Require two flags, preflight by default, hide the URL, and document that operators must verify their environment before applying it.
- [An orchestrator can conceal child output that helps debugging] -> Keep aggregate output to safe named statuses; when a check fails, run that documented constituent command separately for diagnosis instead of echoing captured output that may contain configuration values.
- [Runtime smoke status strings may be less diagnostic than exceptions] -> Preserve distinct stable states and leave detailed diagnosis to protected local logs/operator tooling, not a portable smoke command.
- [Stage 0 reset can be mistaken for a future business reset] -> State in code/tests/docs that it is no-op only; a future reset requires a separately approved change.

## Migration Plan

1. Add script unit tests that mock subprocesses and prove bare initialization, reset, and acceptance avoid mutations.
2. Implement the guarded initialization command, no-op reset contract, acceptance orchestrator, and runtime-smoke safe failure mapping.
3. Update README and TECH evidence; run all local quality checks and separately opt-in read-only runtime smoke/bound process verification when configuration is available.
4. Update `DEVELOPMENT_STATUS.md`, sync the delta specs, archive only after strict validation and all evidence.

Rollback removes the new guards/orchestrator/tests/docs and restores the prior scripts. S0.6 itself does not run a migration or write external data, so it requires no database or Supabase rollback.
