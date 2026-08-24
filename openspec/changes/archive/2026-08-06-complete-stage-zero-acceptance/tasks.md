## 1. Database and data boundary

- [x] 1.1 Confirm S0.6 adds no migration revision, seed/import, business table, Supabase write, reset/delete operation, and that no Alembic or destructive command is executed during implementation or acceptance.

## 2. Backend operational scripts

- [x] 2.1 Make `init_demo.py` preflight-only by default; require the named foundation-migration apply flag plus `--confirm`, lock it to `0001_foundation_schema`, reject missing/non-PostgreSQL configuration before subprocess creation, and never render configured values.
- [x] 2.2 Keep `reset_demo.py` acknowledgement-gated and implement its Stage 0 result as a deterministic no-op with no database, network, model, or filesystem mutation.
- [x] 2.3 Make local `smoke.py` hermetic against ambient external settings and make `runtime_smoke.py` perform read-only foundation-state checks while mapping expected and unexpected failures to stable secret-safe states without tracebacks.
- [x] 2.4 Add a fixed-command Stage 0 acceptance orchestrator for backend tests, Ruff, local smoke, frontend guard/build, and strict OpenSpec validation; exclude init, reset, migrations, external runtime smoke, and arbitrary shell input.

## 3. Frontend boundary

- [x] 3.1 Keep frontend routes and business content unchanged, and include the existing feature-guard test plus production build in the Stage 0 acceptance matrix.

## 4. Model and legacy-data boundary

- [x] 4.1 Confirm no legacy source, model asset, classifier computation, Mock result, search/RAG/FAISS/Embedding code, or business data is read, copied, imported, or reset in S0.6.

## 5. Verification

- [x] 5.1 Add focused tests proving initialization cannot spawn Alembic without both approvals, reset is mutation-free, runtime failures are sanitized, and aggregate acceptance uses only the fixed non-destructive matrix.
- [x] 5.2 Run initialization preflight, confirmed no-op reset, backend tests, Ruff, hermetic local smoke, frontend feature-guard test/build, and the aggregate Stage 0 acceptance command without running migrations or data writes.
- [x] 5.3 Run the separately invoked read-only configured runtime smoke and a bound Uvicorn live/readiness/CORS/OpenAPI/log check; record safe named evidence only.
- [x] 5.4 Run `openspec validate --all --strict --no-interactive` before implementation and retain the final pre-archive output as acceptance evidence.

## 6. Documentation and handoff

- [x] 6.1 Update `README.md` and finalize `docs/TECH-V1-S0-06.md` with the guarded commands, non-goals, failure behavior, and verification evidence.
- [x] 6.2 Update `DEVELOPMENT_STATUS.md` with S0.6 status, evidence, next step, and any blocker or residual risk.
- [x] 6.3 Sync the `project-foundation` and new `stage-zero-operations` main specs, archive `complete-stage-zero-acceptance`, and re-run strict validation after archive.
