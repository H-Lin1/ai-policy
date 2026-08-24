## Why

实施方案：[`TECH-V1-S0-04`](../../docs/TECH-V1-S0-04.md)；开发进度步骤：`S0.4`（见 [`DEVELOPMENT_STATUS.md`](../../DEVELOPMENT_STATUS.md)）。

S0.3 froze the HTTP contract, but the runtime is still not observable or controllable. Logs are unstructured single-line text, and only the access-log middleware carries a request ID, so records emitted by other loggers show `request_id=-` and cannot be correlated with the request that produced them. An unhandled exception returns the request ID in the JSON body but not in the `X-Request-ID` response header, because that response is produced by the outermost server error middleware and never passes back through the request context middleware. Both defects were reproduced locally before this change.

The service also has no way to declare which capabilities are open. `ENABLE_MOCKS` exists in configuration but is not reachable through any API, so the frontend cannot know what is available and would have to hardcode assumptions or render empty business shells. S0.4 establishes logging, request tracing, liveness/readiness semantics, backend-owned feature flags, and frontend route guards before the first business slice depends on them.

## What Changes

- Store the request ID in a context variable so every log record from any logger carries the ID of the request being served, and clear it when the request finishes.
- Emit structured single-line JSON logs with a fixed field set; redact sensitive structured fields, nested values, messages, and exception traces; route Uvicorn lifecycle logs through the same formatter; and keep a `text` format option for local reading.
- Return `X-Request-ID` from every error handler so the header and the error body always agree, including on unhandled 500 responses, and place request context outside CORS so preflight responses carry the same header.
- Keep `live` free of dependency access, report the effective feature-flag snapshot in `ready`, mark a production Mock flag as an explicitly non-compliant configuration, and send `Cache-Control: no-store` on health responses.
- Add a central feature-flag registry and a read-only `GET /api/v1/system/features` endpoint returning environment, whether authentication is required, and the flag snapshot; unknown flag names resolve to disabled.
- Add a frontend runtime configuration context and a feature-flag route guard, plus one guarded `/policies` route that shows an explicit not-open state in Stage 0.
- Non-goals: no business table, migration, seed data, model integration, login UI, RBAC rule, pagination or datetime contract change, error-code change, real policy page, or Mock business response.
- Do not import or reuse legacy Flask routes, payloads, global state, search/RAG/FAISS/Embedding code, model assets, mock data, or frontend code.

## Capabilities

### New Capabilities

- `runtime-observability`: Defines structured logging, request-ID propagation, liveness/readiness semantics, backend-owned feature flags, and the frontend guard behavior that depends on them.

### Modified Capabilities

- `project-foundation`: Request tracing now applies to log records and to unhandled-error response headers, not only to the error body.

## Impact

- Affects backend logging, request context, middleware ordering, error handlers, feature flags, the system module, frontend runtime configuration and routing, reproducible guard tests, `TECH-V1-S0-04`, and `DEVELOPMENT_STATUS.md`.
- Does not change the Supabase schema, run any migration, alter authentication verification, change existing successful response fields, or change the shared error/pagination/UTC contracts.
- Does not expose secrets: the flag snapshot contains booleans, the environment name, and whether authentication is required, never URLs, tokens, or connection strings.
