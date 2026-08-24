# Design: Startup Database Connection Warmup

## Decisions

1. Reuse `database_engine(settings)` so the probe primes the same cached SQLAlchemy engine and pool used by request-scoped sessions.
2. Execute exactly `SELECT 1` under a context-managed connection, then return it to the pool. The probe never begins a transaction or touches application tables.
3. Run the probe in the existing FastAPI lifespan before serving requests. A successful probe moves connection setup out of the first user request; an unavailable database is logged as a safe warning and keeps the existing readiness/error behavior.
4. Record only `database_connection_warmed` or `database_connection_warmup_failed` and `duration_ms`; do not log URLs, exception text, credentials, or database contents.
5. Keep `pool_pre_ping` and all existing session/query behavior unchanged. This change isolates the connection-startup effect before considering pool lifecycle or frontend prefetch changes.

## Risks And Mitigations

- Startup can take as long as the external connection attempt: the probe is bounded by the driver's existing connection behavior and does not block test/fixture apps without a database URL.
- A connection may be closed after a long idle period: `pool_pre_ping` remains enabled, and later idle-connection policy is outside this first optimization.
- A failed probe must not turn a transient dependency outage into an opaque process crash: warmup catches failures, emits a generic warning, and leaves `/health/ready` as the dependency authority.

## Rollback

Remove the lifespan call and helper/tests. No database rollback is required because the probe is read-only.
