## Why

`TECH-V1-S0-05` / `S0.5` must turn the existing placeholder classifier into a boundary that a later verified computation can safely implement. The current Protocol is intentionally small, but it does not yet make supported regions, input normalization, asset validation, or stable adapter failures explicit; leaving those decisions implicit would make a future model migration likely to reintroduce legacy route behavior or cross-region fallback.

## What Changes

- Strengthen the `DepartmentClassifier` contract around normalized text, canonical region identifiers, typed predictions, confidence bounds, and model metadata.
- Add an explicit supported-region configuration and return `REGION_NOT_SUPPORTED` without selecting another region's model.
- Add a side-effect-free model-asset validation boundary used by readiness; missing or invalid assets remain `MODEL_NOT_READY` and never produce a fabricated or Mock result.
- Keep inference behind the adapter only. The new service owns future HTTP validation, authorization, ID mapping, and run recording; this change does not add a classify route.
- Add focused adapter, configuration, readiness, and error-contract tests plus smoke assertions for the not-ready and unsupported-region paths.
- Do not execute database migrations, write Supabase data, or import any legacy route, payload, global state, model asset, search/RAG/FAISS/Embedding code, or frontend code.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `department-classifier-adapter`: make region support, normalization, asset validation, and stable failure behavior executable while preserving the isolated adapter boundary.

## Impact

- Affects `backend/app/modules/intelligence/adapters.py`, classifier-related settings and system readiness schemas/routes, and their tests and smoke checks.
- Adds no runtime dependency and no database/schema change; model files are only inspected for configured-path validation and are not loaded or migrated in S0.5.
- Updates `docs/TECH-V1-S0-05.md`, `DEVELOPMENT_STATUS.md`, and the active OpenSpec artifacts; the main capability spec is synchronized only after implementation and strict validation.
