## Context

See `proposal.md` for motivation and `specs/` for observable behavior. S0.1–S0.3 already provide `/api/v1`, request-ID generation in one middleware, typed health responses, shared error/pagination/UTC contracts, and a `Settings` object holding `enable_mocks`. What is missing is correlation (only the access-log middleware knows the request ID), machine-readable log output, a guarantee that the request ID reaches the header on the unhandled-error path, and any way for the frontend to learn which capabilities are open.

Two defects were reproduced locally before designing this change: an unhandled exception returns a 500 whose body contains the request ID but whose response headers do not, and records from `ai_policy.errors` print `request_id=-`. Both follow from the same root cause — request identity lives on `request.state` and in one middleware frame, so anything outside that frame cannot see it.

## Goals / Non-Goals

**Goals:**

- Make one request traceable across every log record it produces and every response header it returns.
- Emit logs a machine can parse, with credential-bearing fields redacted by construction rather than by reviewer discipline.
- State precisely what `live` and `ready` promise, and stop intermediaries from caching either.
- Put feature availability in one backend registry and let the frontend read it instead of guessing.
- Give the frontend a guard whose closed state is explicit, never an empty business shell.

**Non-Goals:**

- No log shipping, metrics backend, tracing exporter, sampling policy, or log rotation.
- No business table, migration, seed data, model integration, login UI, RBAC rule, or real policy page.
- No change to error codes, the pagination contract, the UTC contract, authentication verification, or existing successful response fields.
- No Mock business response, and no legacy Flask/search/RAG/model/frontend code entering the project.

## Decisions

### Carry the request ID in a context variable, not only on the request object

A `contextvars.ContextVar` holds the current request ID. The request-context middleware sets it, and resets it in a `finally` block using the token returned by `set`, so concurrent requests cannot read each other's ID and a finished request cannot leak its ID into a later one. A logging filter reads the context variable and attaches it to every record, so `ai_policy.errors`, SQLAlchemy, and future business loggers all correlate without passing the request around.

Threading the ID through function arguments was considered and rejected: it would touch every future service signature to serve a cross-cutting concern. `request.state` alone is insufficient because the failing case is precisely the frame that has no request object.

### Set the request ID header inside the error handlers

The unhandled-error response is produced by Starlette's outermost `ServerErrorMiddleware`, which sits above the request-context middleware, so the header assignment on the way out never runs for that response. Each error handler therefore sets `X-Request-ID` on the `JSONResponse` it builds, reading the ID from the request object with the context variable as a fallback. The existing middleware assignment stays for success responses, so the header is set exactly once on each path.

### Put request context outside CORS

Starlette applies the last user middleware added as the outer layer. `RequestContextMiddleware` is therefore registered after `CORSMiddleware`, so CORS preflight responses cannot short-circuit before request-ID generation. CORS also exposes `X-Request-ID` on browser-visible responses. This ordering is independent of the outer `ServerErrorMiddleware`, so explicit 500 response headers remain necessary.

### Emit JSON by default and keep a text format for humans

A `LOG_FORMAT` setting selects `json` (default) or `text`. Both run through the same redaction, so the human-readable option cannot become the leaky one. A fixed base field set (`timestamp`, `level`, `logger`, `message`, `request_id`) plus request fields on access records keeps records greppable without a schema registry. Uvicorn lifecycle loggers propagate through the same formatter. Its duplicate access logger is disabled because the application already emits a correlated access record and Uvicorn emits its copy only after request context has been cleared. Adopting `structlog` or `python-json-logger` was considered and rejected: a formatter subclass adds no dependency, and the project has no aggregation backend whose format it must match yet.

### Redact by key name, and treat unserializable values as opaque

Redaction matches on a case-insensitive substring set (`authorization`, `token`, `password`, `secret`, `api_key`, `apikey`, `cookie`, `database_url`, `dsn`, `credential`, `jwt`) over extra-field keys, replacing the value with `***`. Nested mappings and collections are traversed with recursion protection. Messages, string values, object representations, and formatted exception traces additionally remove key/value credentials, Bearer values, JWT-shaped values, and database connection URLs. Values are bounded before output, so a logging call cannot emit an unbounded blob. Structured fields remain the preferred logging API, while free-text scanning provides defense in depth for third-party exceptions.

### Register flags in one table, and let production override the Mock flag

`features.py` holds a registry mapping each flag name to the settings attribute that backs it. `feature_enabled` resolves through the registry and returns `False` for unregistered names, so a typo fails closed. The Mock flag additionally resolves to `False` whenever the environment is production: a demonstration deployment must not serve Mock data even if the variable is set wrong, and readiness surfaces that mismatch as a non-compliant configuration rather than silently ignoring it. Reporting the mismatch and forcing the safe value are both needed — forcing alone would hide a misconfiguration, reporting alone would serve Mock data in production.

`ENABLE_POLICY_WORKSPACE` is added now, defaulting to `false`, so B1.x has a flag to flip rather than a guard to invent.

### Expose the snapshot as a system endpoint with a deliberately narrow payload

`GET /api/v1/system/features` returns the environment name, whether authentication is required, and a boolean map. It stays public because the frontend needs it before any login exists, and because it reveals no more than the existing health endpoints. Nothing else is included — no URLs, no credential state, no dependency detail — so the endpoint cannot become an accidental configuration dump. Embedding flags in the frontend build was rejected: it would require a rebuild to flip a flag and would let backend and frontend disagree about what is open.

### Guard routes on the snapshot, with three explicit closed states

A React context loads the snapshot once at startup and exposes loading, error, and resolved states. The guard renders protected children only in the resolved-and-enabled case; loading shows a loading state, error shows the failure with a retry, and disabled shows an explicit not-open message. Defaulting to open while loading was rejected as it would flash unavailable content; defaulting to a generic 404 was rejected because "not built yet" and "does not exist" are different facts and the demonstration should say which one applies. A snapshot failure must not affect public pages, so the provider does not block the whole application shell.

Stage 0 wires one guarded route, `/policies`, controlled by `policy_workspace`. It contains only the guard and the not-open state; the real page belongs to the B1.x vertical slice with its own migration, API, permissions, and acceptance.

### Send no-store on health responses

`live`, `ready`, and `health` set `Cache-Control: no-store`. A cached readiness result is worse than no result: it can report a dependency healthy after it has failed. The three health handlers set the header explicitly rather than a blanket middleware rule, so future cacheable business responses are unaffected. The 503 not-ready path raises through `AppError`, which now carries response headers so the directive survives that path too.

## Risks / Trade-offs

- [Free-text patterns cannot identify every possible credential encoding] → Keep credentials in structured fields, redact common message/exception forms as defense in depth, assert on emitted output, and never log request bodies or headers wholesale.
- [Context variable leaks an ID across requests if the reset is skipped] → Reset with the `set` token in a `finally` block and cover sequential requests in tests.
- [Setting the header in both middleware and handlers could conflict] → Success responses are set by the middleware and error responses by the handlers; tests assert the header matches the body ID on 4xx and 5xx.
- [A public feature endpoint reveals roadmap state] → Accept it for this demonstration; the payload is booleans and an environment name, no more revealing than the existing health checks.
- [The extra startup request adds a failure mode to the frontend] → The provider surfaces failure with a retry and does not gate public routes on it.
- [JSON logs are harder to read locally] → `LOG_FORMAT=text` keeps the readable format, with identical redaction.

## Migration Plan

1. Add the request-ID context variable, structured logging with redaction, and the middleware set/reset.
2. Put request context outside CORS, expose `X-Request-ID`, set the header in error handlers, and add health cache directives.
3. Add the flag registry, production Mock override, readiness snapshot, and the features endpoint.
4. Add the frontend runtime configuration provider, the guard, and the guarded `/policies` route.
5. Run backend tests, Ruff, a reproducible frontend guard test, frontend build, runtime smoke, a bound Uvicorn check, and strict OpenSpec validation.

No database or data migration is required, and no Supabase data is touched. Rollback removes the context, logging, flag, endpoint, and guard changes and restores the previous formatter and handlers; the API error envelope, pagination, UTC contract, and authentication behavior are unaffected either way.
