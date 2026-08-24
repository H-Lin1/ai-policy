## Why

实施方案：[`TECH-V1-S0-03`](../../docs/TECH-V1-S0-03.md)；飞书版本：[TECH-V1-S0-03](https://a9ihi0un9c.feishu.cn/docx/B2KaddUh6oQME9x4O2cc7GXznue)。

The existing S0.2 service already uses `/api/v1` and a stable runtime error body, but its OpenAPI document does not describe those error responses and the project has no shared pagination or UTC datetime contract. S0.3 and `TECH-V1-S0-03` freeze these conventions before policy, question, consultation, and AI business endpoints are added, so later modules do not invent incompatible shapes.

## What Changes

- Add reusable backend API models for the standard error envelope, page-based pagination metadata, generic paged responses, and timezone-aware UTC datetimes.
- Publish stable operation IDs, tag descriptions, documented error responses, and examples in OpenAPI while keeping all business APIs under `/api/v1`.
- Align the frontend API client with the backend error and pagination contracts so request ID, error code, details, and paging metadata are preserved.
- Add contract tests for pagination limits, UTC normalization, runtime error serialization, OpenAPI paths, operation IDs, and response schemas.
- Keep the implementation intentionally small: no business endpoint, database table, migration, generated client, authentication flow, role policy, logging redesign, or UI page is added in S0.3.
- Do not import or reuse legacy Flask routes, payloads, frontend code, search/RAG logic, model assets, or Mock data.

## Capabilities

### New Capabilities

- `api-contract-standards`: Defines versioned routing, OpenAPI documentation, page-based pagination, UTC datetime serialization, and stable error envelopes shared by future modules.

### Modified Capabilities

None.

## Impact

- Affects the FastAPI application metadata, shared API models, router defaults, error handlers, frontend API types, tests, technical documentation, and development status.
- Does not change the Supabase schema, authentication keys, deployed data, existing successful response bodies, or legacy-code boundary.
