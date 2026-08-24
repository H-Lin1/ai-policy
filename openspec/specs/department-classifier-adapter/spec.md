# department-classifier-adapter Specification

## Purpose
为唯一允许迁移的旧分类计算逻辑提供稳定、可测试、与 HTTP 路由隔离的模型适配器边界，避免旧 Flask 实现重新成为新业务接口。
## Requirements
### Requirement: Isolated classifier adapter contract

The system SHALL define a `DepartmentClassifier` adapter boundary that accepts text normalized at the boundary and an explicit canonical region identifier and returns a typed classification result. Text normalization SHALL apply Unicode compatibility normalization and collapse surrounding/internal whitespace. Region identifiers SHALL be trimmed, lower-cased, and validated as stable ASCII identifiers before lookup. The configured supported-region set SHALL be explicit; an unsupported region MUST return `REGION_NOT_SUPPORTED` and MUST NOT select another region's adapter or model. A successful result SHALL be rebuilt and validated at the adapter boundary before return, and contain the requested canonical region, one or more unique non-empty stable department IDs, finite confidence values in the inclusive range 0..1, a deterministic prediction order, and non-empty model-version metadata. The adapter SHALL not expose Flask request/response objects, legacy payload names, global mutable route state, or implicit cross-region fallback.

#### Scenario: Adapter is invoked with a supported region

- **WHEN** the application service submits non-empty text and an explicit supported region to a verified classifier implementation
- **THEN** the adapter receives the canonical text and region and returns a typed classification result containing that region, one or more stable department IDs, bounded confidence values, deterministic ordering, and model version metadata

#### Scenario: Adapter normalizes its boundary input

- **WHEN** a caller submits compatibility-equivalent Unicode text, surrounding or repeated whitespace, and a mixed-case region identifier
- **THEN** the adapter uses the normalized text and lower-case canonical region for validation and inference without changing the caller's unrelated payload fields

#### Scenario: Adapter receives an unsupported region

- **WHEN** the application service submits a syntactically valid region that is not in the configured supported set
- **THEN** the adapter returns a stable `REGION_NOT_SUPPORTED` failure and does not silently use another region's model

#### Scenario: Adapter rejects an invalid result contract

- **WHEN** an implementation attempts to construct a result with no predictions, duplicate or blank department IDs, a non-finite or out-of-range confidence, a blank model version, or a region different from the request
- **THEN** the boundary rejects the result with a stable classifier contract error before it can be returned to the application service

### Requirement: Explicit model readiness failure

The adapter SHALL expose readiness information containing a stable adapter identifier, a strict boolean readiness state, and a safe reason code when it is not ready. Adapter identifiers, model-version metadata, and reason codes SHALL be bounded ASCII metadata tokens; reason codes SHALL come from the registered safe set and MUST NOT contain paths, credentials, or exception text. Readiness validation MAY inspect configured model, tokenizer, and label-binding paths for presence and regular-file readability, but SHALL NOT load unverified model code or expose asset paths, credentials, or exception text. When the approved legacy classification computation or its verified model assets are not configured, are incomplete, fail validation, or are not yet wired to the adapter, the adapter MUST report not ready and classification requests MUST fail with `MODEL_NOT_READY` (or an equivalent stable classifier error). It MUST NOT return a fixed answer, fixed confidence, or mock classification.

#### Scenario: Model assets are absent

- **WHEN** a classification request is made before a verified model adapter is configured
- **THEN** the service returns a non-success response with `MODEL_NOT_READY`, a request ID, and no fabricated department result

#### Scenario: Model assets fail validation

- **WHEN** model weights, tokenizer metadata, or label bindings are missing, partial, or not readable during readiness validation
- **THEN** readiness is false and classification requests fail explicitly without falling back to Beijing, Shenzhen, or another unrelated model, and the response does not contain asset paths

#### Scenario: Assets exist but the computation is not verified

- **WHEN** all configured asset paths pass the side-effect-free file checks but no approved classifier implementation has been wired
- **THEN** readiness remains false with a stable not-ready reason and classification still fails with `MODEL_NOT_READY`

#### Scenario: Readiness endpoint exposes only safe state

- **WHEN** a client requests `GET /api/v1/ai/readiness`
- **THEN** the endpoint returns the adapter's status and safe reason with `Cache-Control: no-store`, and never returns model paths, tokens, connection strings, or stack traces

### Requirement: New API owns business orchestration

The new service layer SHALL own authentication, authorization, region and department ID mapping, AI run recording, and translation of classifier-domain failures into the shared HTTP error envelope. The adapter SHALL only perform normalization required by its contract, readiness checks, and classification inference; it SHALL not recreate the legacy `/classify` route or write application data.

#### Scenario: Legacy route is requested

- **WHEN** a client requests the legacy `POST /classify` endpoint on the new service
- **THEN** the endpoint is not registered and the service returns the standard 404 response

#### Scenario: Adapter failure is translated by the service boundary

- **WHEN** a future application service receives `REGION_NOT_SUPPORTED` or `MODEL_NOT_READY` from the adapter
- **THEN** the service maps the stable domain code to the shared API error envelope while keeping HTTP concerns out of the adapter

