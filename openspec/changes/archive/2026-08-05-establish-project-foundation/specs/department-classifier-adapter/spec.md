## Purpose

为唯一允许迁移的旧分类计算逻辑提供稳定、可测试、与 HTTP 路由隔离的模型适配器边界，避免旧 Flask 实现重新成为新业务接口。

## ADDED Requirements

### Requirement: Isolated classifier adapter contract

The system SHALL define a `DepartmentClassifier` adapter contract that accepts normalized text and an explicit region identifier and returns stable department identifiers, confidence values, and model metadata. The adapter SHALL not expose Flask request/response objects, legacy payload names, global mutable route state, or implicit cross-region fallback.

#### Scenario: Adapter is invoked with a supported region

- **WHEN** the application service submits non-empty text and an explicit supported region to the classifier adapter
- **THEN** the adapter returns a typed classification result containing the region, one or more stable department IDs, confidence values, and model version metadata

#### Scenario: Adapter receives an unsupported region

- **WHEN** the application service submits a region that is not configured
- **THEN** the adapter returns a stable `REGION_NOT_SUPPORTED` failure and does not silently use another region's model

### Requirement: Explicit model readiness failure

The adapter SHALL expose readiness information. When the approved legacy classification computation or its verified model assets are not configured or fail validation, the adapter MUST return `MODEL_NOT_READY` (or an equivalent stable error) and MUST NOT return a fixed answer, fixed confidence, or mock classification.

#### Scenario: Model assets are absent

- **WHEN** a classification request is made before a verified model adapter is configured
- **THEN** the service returns a non-success response with `MODEL_NOT_READY`, a request ID, and no fabricated department result

#### Scenario: Model assets fail validation

- **WHEN** model weights, tokenizer metadata, or label bindings fail startup validation
- **THEN** readiness is false and classification requests fail explicitly without falling back to Beijing, Shenzhen, or another unrelated model

### Requirement: New API owns business orchestration

The new service layer SHALL own authentication, authorization, region and department ID mapping, AI run recording, and error translation. The adapter SHALL only perform classification inference and shall not recreate the legacy `/classify` route.

#### Scenario: Legacy route is requested

- **WHEN** a client requests the legacy `POST /classify` endpoint on the new service
- **THEN** the endpoint is not registered and the service returns the standard 404 response

