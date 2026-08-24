## Context

See `proposal.md` for motivation and `specs/api-contract-standards/spec.md` for observable behavior. S0.2 already provides `/api/v1`, request IDs, runtime error handlers, Supabase readiness, and typed success responses, but the conventions are distributed across route files and the OpenAPI document does not describe runtime errors. No business list or datetime endpoint exists yet, so S0.3 must establish reusable contracts without inventing a fake business API.

## Goals / Non-Goals

**Goals:**

- Give later modules one importable set of error, pagination, and UTC datetime types.
- Make the generated OpenAPI truthful for current routes and stable enough for a future generated client.
- Keep frontend error handling aligned with the backend envelope.
- Preserve existing successful response bodies and authentication behavior.

**Non-Goals:**

- No universal success wrapper, cursor pagination, business route, business table, Alembic migration, seed data, generated SDK, login UI, RBAC rule, logging redesign, model integration, or Mock response.
- No legacy Flask, search, RAG, FAISS, model, payload, or frontend code enters the new project.

## Decisions

### Use direct resource responses and a paged envelope only for lists

Single-resource and command endpoints keep typed response bodies such as the existing health and principal objects. Lists use `{items, meta}`. A universal `{data, error, meta}` wrapper was considered but rejected because HTTP already communicates success/failure and the extra nesting adds work without helping this demonstration project.

### Use one-based page pagination

The shared request accepts `page` (default 1) and `page_size` (default 20, maximum 100). Metadata includes total counts and navigation flags. Cursor pagination was considered but rejected for V1 because the planned policy, question, consultation, and administration lists are small and need visible page numbers and totals. A future high-volume endpoint can introduce a separate cursor contract without changing this one.

### Require timezone-aware datetimes and normalize to UTC

A shared Pydantic annotated datetime validates timezone presence and converts accepted offsets to UTC. Pydantic serializes UTC as RFC 3339 with `Z`. Naive values fail validation rather than being interpreted using the developer machine timezone. PostgreSQL `timestamptz` remains the persistence choice when business tables are introduced; S0.3 creates no column or migration. The frontend will convert UTC strings to `Asia/Shanghai` only when displaying them.

### Model errors once and reuse them in handlers and OpenAPI

Define typed error detail and envelope models plus small reusable OpenAPI response definitions. Runtime handlers build the same model and use JSON-safe encoding before returning `JSONResponse`. Route decorators list only errors relevant to that operation instead of claiming every status on every route. Standard HTTP exceptions receive stable codes such as `ROUTE_NOT_FOUND` and `METHOD_NOT_ALLOWED`; explicit `AppError` codes remain authoritative for domain and authentication failures.

### Publish stable operation metadata without generating a client yet

Current route decorators receive explicit operation IDs and use documented tag metadata. The frontend remains a small handwritten client but gains shared `ApiErrorEnvelope`, `PaginationMeta`, and `PagedResponse<T>` types and preserves error code, details, request ID, and HTTP status in `ApiError`. Generating a client now was considered but rejected because there are no business endpoints yet and it would add tooling before it provides value.

### Preserve permission, model, and Mock boundaries

This change does not alter which routes are public or protected. Authentication dependencies remain on their current routes, AI readiness remains explicit, and failures never produce Mock data. Error examples contain placeholders only and never contain tokens, connection strings, or user data.

## Risks / Trade-offs

- [Page totals require a count query on future lists] → Accept the cost for the small demonstration dataset; optimize only after a measured need.
- [Manually declared operation IDs can collide] → Add an OpenAPI contract test that asserts every operation ID is present and unique.
- [Shared types can be bypassed by a future module] → Make contract tests and OpenAPI review part of every later PRD/OpenSpec acceptance.
- [Validation details can contain non-JSON Python objects] → Encode error details through FastAPI's JSON-safe encoder and test a custom validator failure.
- [Frontend and backend types can drift before SDK generation] → Keep names and field shapes identical and verify the frontend production build in every change.

## Migration Plan

1. Add shared backend contracts and tests without changing successful responses.
2. Wire current error handlers and route OpenAPI metadata to the shared models.
3. Align the frontend API client types and error parsing.
4. Run backend, frontend, runtime, and strict OpenSpec checks.

No database or data migration is required. Rollback removes the shared contract module and restores the previous handler/router metadata; Supabase data and authentication configuration are unaffected.
