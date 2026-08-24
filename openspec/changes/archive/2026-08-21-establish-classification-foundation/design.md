# Design: Department Classification Foundation

## Asset and adapter boundary

The implementation begins with a source-independent asset probe. It validates the four explicitly configured assets (model, tokenizer directory, JSON label binding, and department embeddings), supported region registry, model architecture metadata, and label binding shape without importing legacy application modules. A concrete adapter is created only when the manifest is complete and compatible. Model loading is lazy, CPU-only, deterministic, inference-only, and fail-closed. No inference result is fabricated when the model is not ready.

## API and permission

`POST /api/v1/classifications` is an authenticated route. The current identity must be active, role-assigned, and in `sz`; an explicit request region, when present, must match the identity. The service translates classifier-domain errors to the existing error envelope and emits `Cache-Control: no-store`. Request text is never logged or persisted.

## Response and frontend

The API returns only canonical region, safe model version, and sorted department predictions. `/classify` renders a textarea and explicit state transitions. The page has no model controls, import, approval, chat history, or mock fallback.

## Failure and rollback

Manifest, tokenizer, label, shape, inference, and contract failures become stable safe codes. Unexpected exceptions are logged only as generic events and returned as `CLASSIFIER_INFERENCE_FAILED` or `MODEL_NOT_READY`. Rollback removes code/config/spec artifacts only; no database rollback is run.
