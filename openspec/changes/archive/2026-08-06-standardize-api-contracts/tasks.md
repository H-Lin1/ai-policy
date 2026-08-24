## 1. Database and data boundary

- [x] 1.1 Confirm S0.3 requires no database migration or seed data, and record that the shared contract is persistence-neutral.

## 2. Backend contract implementation

- [x] 2.1 Add typed error, page pagination, generic paged response, and timezone-aware UTC datetime models with validation and JSON-safe serialization.
- [x] 2.2 Update application error and HTTP exception handlers to use the shared envelope, stable method/status codes, and JSON-safe validation details while preserving request IDs and headers.
- [x] 2.3 Add explicit operation IDs, tags, endpoint response schemas, and error response documentation to the current `/api/v1` routes and application OpenAPI metadata.

## 3. Frontend contract implementation

- [x] 3.1 Align the handwritten API client with shared error, request ID, pagination, and UTC string types; preserve structured error data in `ApiError` without adding business UI.

## 4. Verification

- [x] 4.1 Add backend contract tests for pagination defaults/bounds/empty pages, UTC normalization and naive rejection, validation/error serialization, method-not-allowed behavior, and unique OpenAPI operation IDs and schemas.
- [x] 4.2 Run backend tests and Ruff, frontend typecheck/build, OpenAPI inspection, and the existing runtime smoke without changing Supabase data.

## 5. Documentation and handoff

- [x] 5.1 Record implementation evidence in `TECH-V1-S0-03`, update `DEVELOPMENT_STATUS.md`, and sync the confirmed technical plan to the product PRD Feishu folder.
- [x] 5.2 Run full strict OpenSpec validation, archive `standardize-api-contracts`, sync its main spec, and move the development pointer to S0.4 pending.
