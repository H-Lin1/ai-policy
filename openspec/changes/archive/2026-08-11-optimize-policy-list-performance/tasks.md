# Tasks: Policy List Performance Patch

## Planning gate

- [x] 1.1 Record the read-only connection/query baseline and explicit no-write boundary in TECH.
- [x] 1.2 Strict-validate the active OpenSpec change before implementation (`10/10`).

## Backend

- [x] 2.1 Add one optional request-scoped session dependency and reuse it across IAM and policy repositories.
- [x] 2.2 Replace the normal list path with one projected window-total statement and an empty-page fallback count.
- [x] 2.3 Preserve fixture, IAM, API, error, pagination, ordering, filtering, detail, and no-store behavior.

## Verification

- [x] 3.1 Add focused tests for session reuse, one-statement projection, excluded detail columns, filters, and empty-page totals.
- [x] 3.2 Run backend tests, Ruff, local smoke, runtime smoke, frontend tests/build, aggregate acceptance, and strict OpenSpec validation.
- [x] 3.3 Run a secret-safe real authenticated cold/warm benchmark and satisfy the TECH thresholds.

## Documentation and archive

- [x] 4.1 Update TECH and `DEVELOPMENT_STATUS.md`, sync the technical plan/evidence to Feishu, and archive only after all acceptance evidence is recorded.

## Acceptance evidence

- Baseline: pooler double-session checkout showed 7,414 ms then 1,728 ms; one shared-session checkout plus projected window page measured 1,748 ms then 222 ms.
- Structural proof: one FastAPI request session is reused by IAM and policy dependencies; normal list page is one statement with `count(*) over()` and excludes `content_text`, hash, collection, and provenance fields; out-of-range pages retain an exact fallback count.
- Real authenticated benchmark: cold page-one list `6,774 ms`; warm page-one lists `1,822 / 852 / 1,594 ms`; median `1,594 ms`; every list retained 10 items, total 20, and `no-store`.
- Quality gates: backend `213 passed`; Ruff passed; local smoke `14/14`; runtime `5/5`; frontend tests passed; 91-module build passed; aggregate acceptance `6/6`; pre-archive strict `10/10`.
- Exclusions: no migration, policy/data write, full-CSV import, update, delete, downgrade, reset, Auth mutation, feature-flag change, cache, model/RAG, legacy source access, or sensitive output.
