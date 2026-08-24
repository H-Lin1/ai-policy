## 1. Database and data boundary

- [x] 1.1 Confirm S0.5 is persistence-neutral: no Alembic migration, business table, seed/reset write, or Supabase data change.

## 2. Backend adapter boundary

- [x] 2.1 Add the explicit supported-region setting (`CLASSIFIER_SUPPORTED_REGIONS`) and deterministic parsing/canonicalization in `Settings`, plus safe environment-template documentation.
- [x] 2.2 Replace HTTP-coupled adapter failures with classifier-domain errors and implement normalized input validation and typed prediction/result invariants.
- [x] 2.3 Add the immutable asset manifest and side-effect-free path validation with stable not-ready reasons; keep the default implementation fail-closed and Mock-free.
- [x] 2.4 Replace the mutable classifier singleton with a settings-aware factory/dependency seam and make supported-region rejection precede the model-readiness gate.
- [x] 2.5 Update `/api/v1/ai/readiness` to use the injected factory, emit `Cache-Control: no-store`, and fail closed with safe status/reason fields on unexpected readiness errors.

## 3. Frontend boundary

- [x] 3.1 Verify that S0.5 changes no frontend routes, business data, or public client secrets and that the existing runtime guard/build contract remains unchanged.

## 4. Model and legacy-data boundary

- [x] 4.1 Confirm no legacy source, model weights, tokenizer, labels, Mock data, or inference dependency is imported or copied; leave verified computation migration for a later approved change.

## 5. Verification

- [x] 5.1 Add unit and API regression tests for normalization, input/result invariants, supported and unsupported regions, asset states, factory injection, readiness headers, safe reasons, and legacy route absence.
- [x] 5.2 Extend the local smoke script with classifier readiness and unsupported-region boundary assertions without printing paths or secrets.
- [x] 5.3 Run backend tests, Ruff, frontend guard test/build, runtime smoke, and a bound Uvicorn readiness check; confirm no migration or Supabase write was executed.
- [x] 5.4 Run `openspec validate --all --strict --no-interactive` and retain the output as acceptance evidence.

## 6. Documentation and handoff

- [x] 6.1 Write and review `docs/TECH-V1-S0-05.md` with the final contract, failure reasons, configuration, security/data boundary, and verification evidence.
- [x] 6.2 Update `DEVELOPMENT_STATUS.md` with S0.5 status, evidence, next step, and any residual risk/blocker.
- [x] 6.3 Sync the modified main capability spec, archive `establish-department-classifier-adapter`, and re-run strict validation after archive.
