## Context

See `proposal.md` for the motivation. FastAPI's built-in missing-route behavior bypasses the existing handler for `fastapi.HTTPException`, so `POST /classify` currently has a request header but returns the framework's default `detail` body.

## Goals / Non-Goals

**Goals:**

- Make the existing error envelope and request-ID guarantees apply to unregistered routes.
- Preserve the intentional absence of all legacy routes.
- Keep the correction isolated and covered by a regression test.

**Non-Goals:**

- Adding a replacement classification endpoint.
- Changing business authorization, data, models, Mock behavior, or frontend handling.

## Decisions

- Register a handler for Starlette's HTTP exception type, which is what the router uses for an unmatched path. The handler will translate only 404s to `ROUTE_NOT_FOUND` and use the existing error-envelope function; it will retain the existing FastAPI handler for explicitly raised endpoint errors.
- Use a stable public message rather than exposing framework-specific wording. This keeps frontend handling and future API documentation independent of FastAPI defaults.
- Add an end-to-end `TestClient` assertion against legacy `/classify`, because it verifies the practical boundary rather than only a handler in isolation.

## Risks / Trade-offs

- [Exception-class overlap] → Register the Starlette handler separately and retain the FastAPI handler so explicitly raised `HTTPException` responses keep their existing error-code behavior.
- [Overbroad rewriting of 4xx responses] → Translate only status 404 in the Starlette handler; pass other routing-generated status codes through the existing error-envelope semantics.

## Migration Plan

1. Add the route-not-found handler and registration.
2. Add the regression test.
3. Run backend tests, lint, smoke checks, and strict OpenSpec validation.
4. Roll back by removing the handler registration if an unexpected framework interaction is found; no data migration or deployment sequencing is required.
