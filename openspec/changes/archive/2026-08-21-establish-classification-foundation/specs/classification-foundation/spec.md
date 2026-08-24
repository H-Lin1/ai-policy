## ADDED Requirements

### Requirement: Verified deterministic department classifier

The system SHALL load only explicitly configured and validated server-side classifier assets (model, tokenizer directory, JSON label binding, and department embeddings), support the canonical Shenzhen region `sz`, run CPU-safe inference without legacy route code or Mock fallback, and return deterministic sorted department predictions with safe model-version metadata. Missing, incompatible, malformed, or failed assets SHALL produce explicit not-ready or inference errors.

#### Scenario: Valid configured assets classify text

- **WHEN** an active Shenzhen identity submits non-empty text and the configured model, tokenizer, and label bindings pass validation
- **THEN** the service returns the canonical `sz` region, safe model version, and one or more label-bound predictions with finite confidence values in `[0,1]` in deterministic order

#### Scenario: Assets are unavailable or incompatible

- **WHEN** the manifest is missing, partial, unreadable, incompatible, or inference fails
- **THEN** readiness and classification fail explicitly without fabricated results, cross-region fallback, asset-path leakage, or database writes

### Requirement: Authenticated classification endpoint

The system SHALL expose `POST /api/v1/classifications` behind the current IAM and active Shenzhen scope. It SHALL preserve shared error envelopes/request IDs, set `Cache-Control: no-store`, reject empty text and explicit region mismatch, and return only approved result fields.

#### Scenario: Authorized classification request

- **WHEN** an active Shenzhen identity submits valid text to the endpoint
- **THEN** the endpoint returns the verified classifier result and no input text, raw logits, paths, credentials, or stack traces

#### Scenario: Unauthorized or out-of-scope request

- **WHEN** the request is signed out, unprovisioned, disabled, or outside Shenzhen
- **THEN** existing 401/403/503 contracts apply and no model inference is executed

### Requirement: Guarded classification workbench

The frontend SHALL provide an authenticated responsive `/classify` workbench with a text input, submit action, explicit loading/success/not-ready/error states, and department result cards. It SHALL provide no model configuration, import, approval, chat history, or Mock fallback controls.

#### Scenario: Classification workbench is used

- **WHEN** an authorized user enters text and submits it
- **THEN** the UI calls the real classification API and renders the returned departments or an explicit safe error state without horizontal overflow
