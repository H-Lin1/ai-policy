# Proposal: Warm the Database Connection Before First User Query

## Why

B18-004 profiling shows that the first authenticated policy request can spend several seconds establishing a Supabase database connection before the identity and projected list queries run. The current list SQL is already sub-second; moving the connection cost to API startup should improve the first user-visible query without changing data or permissions.

## What Changes

- Run one read-only `SELECT 1` against the configured SQLAlchemy engine during the FastAPI lifespan startup.
- Return the connection to the existing process pool for the first authenticated request.
- Emit only a safe lifecycle duration/status record; a failed warmup does not expose connection details or prevent the process from starting.
- Add focused tests and a cold/warm runtime benchmark after startup warmup.

## What Does Not Change

- No database schema, data, RLS, Auth, API response, cache, or query-shape changes.
- No fallback identity or Mock business data.
- Database-disabled fixture/test environments remain database-free.
