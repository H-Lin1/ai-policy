## Context

See `proposal.md` and the archived B1.6 consultation workflow. The repository already has target-binding checks, a PostgreSQL-only runtime smoke, protected B1.6 tables and deterministic frontend/backend test commands. B1.7 is an operational acceptance step, not a new user-facing workflow.

## Goals / Non-Goals

**Goals:**

- Make integrated acceptance checks repeatable and secret-safe.
- Make demonstration cleanup explicit, narrowly scoped and recoverable before commit.
- Preserve ordinary user consultations and imported public policy/Q&A data.

**Non-Goals:**

- No new API route, business table, Auth provisioning, migration, RAG implementation or frontend feature.
- No broad reset, truncation, cascade deletion or deletion based on requester identity/time alone.

## Decisions

The audit will compose existing read-only runtime checks and local test/build commands, returning stable check names rather than raw exceptions. It will fail closed when the target is not verified.

The reset marker will be a fixed, exact prefix `B17演示验收:` in consultation question/public projection text. The command will first lock and count candidate consultations, verify that every candidate is closed and that all referenced historical projections are one-to-one consultation projections, then delete events, consultations and projections in dependency order inside one transaction. No candidate means a successful no-op.

The implementation will use a separate script rather than an HTTP endpoint so browser clients cannot trigger destructive operations. Tests will use fakes/source inspection to prove flags, target checks, SQL scope and rollback behavior without touching the configured database.

## Risks / Trade-offs

- [A marker is accidentally reused in real content] -> Use an exact reserved prefix, require closed status, and report candidates before apply.
- [A reset is run against the wrong Supabase project] -> Reuse the existing project-ref binding and refuse any non-`ok` state.
- [A partial delete leaves inconsistent data] -> Use one transaction and delete restrictive foreign-key dependents before parents.

## Migration Plan

No migration is required. Run the audit first, run reset preflight, review counts, then apply only with both explicit flags. Rollback is transaction rollback on any error; no automatic retry or fallback is performed.
