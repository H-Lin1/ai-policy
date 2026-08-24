## 1. Database and data boundary

- [x] 1.1 Confirm S0.4 requires no migration, seed data, or Supabase data change, and record that observability and flags are persistence-neutral.

## 2. Backend request context and logging

- [x] 2.1 Add a request-ID context variable with safe set/reset, and set it in the request-context middleware so it is cleared when the request finishes.
- [x] 2.2 Add structured JSON logging with a fixed base field set, a `LOG_FORMAT` text option, nested/message/exception redaction of credential-bearing values, and bounded rendering of unserializable values.
- [x] 2.3 Emit correlated application access records with method, path, status code, and duration; route Uvicorn lifecycle logs through the formatter and disable its uncorrelated duplicate access log.

## 3. Backend response and health semantics

- [x] 3.1 Set `X-Request-ID` in every error handler, wrap CORS with request context so preflight responses carry the header, and expose it to browser clients.
- [x] 3.2 Keep liveness free of database, JWKS, and model access, and send `Cache-Control: no-store` on live, ready, and aggregate health responses.
- [x] 3.3 Add the effective feature-flag snapshot to readiness and report an explicitly non-compliant state when production enables the Mock flag.

## 4. Backend feature flags

- [x] 4.1 Add a central flag registry with `ENABLE_MOCKS` and `ENABLE_POLICY_WORKSPACE`, unknown names resolving to disabled, and the Mock flag forced off in production.
- [x] 4.2 Add `GET /api/v1/system/features` returning environment, authentication requirement, and the boolean snapshot with a stable operation ID and no configuration values.
- [x] 4.3 Add the new flag variables to the environment templates without introducing secrets.

## 5. Frontend runtime configuration and guards

- [x] 5.1 Add a features request to the API client and a runtime configuration provider exposing loading, error, and resolved snapshot states.
- [x] 5.2 Add a feature-flag route guard that renders protected content only when the flag is enabled, with explicit loading, not-open, and retryable error states.
- [x] 5.3 Add the guarded `/policies` route and navigation entry containing only the guard and its not-open state, with no business data or placeholder results.
- [x] 5.4 Add a dependency-free SSR acceptance script covering loading, error, disabled, missing-flag, and enabled guard states.

## 6. Verification

- [x] 6.1 Add backend tests for request-ID correlation across loggers, CORS preflight tracing, header/body agreement on 4xx and unhandled 500, structured/nested/message/exception redaction, Uvicorn logging, health cache directives, liveness isolation, readiness flags, and the feature endpoint payload.
- [x] 6.2 Extend the local smoke script to cover the features endpoint, health cache directives, and CORS preflight request IDs without printing secrets.
- [x] 6.3 Run backend tests, Ruff, frontend guard SSR tests, frontend typecheck/build, runtime smoke, an ASGI-stack check, and a bound Uvicorn check without changing Supabase data.

## 7. Documentation and handoff

- [x] 7.1 Record implementation evidence in `TECH-V1-S0-04` and update `README.md` where runtime behavior changed.
- [x] 7.2 Update `DEVELOPMENT_STATUS.md` with S0.4 status, evidence, and next step.
- [x] 7.3 Run full strict OpenSpec validation, archive `establish-runtime-observability`, sync main specs, and move the development pointer to S0.5 pending.
