# Tasks: Historical Government Q&A

## Planning and data boundary

- [x] 1.1 Audit the three adjudicated source CSVs and record counts, duplicates, host scope, privacy exclusions, 20-record boundary, and external-write gate in PRD/TECH.
- [x] 1.2 Strict-validate B1.3 OpenSpec before implementation.

## Migration and data

- [x] 2.1 Add source-only `0004_historical_qa` migration with restrictive schema/RLS/no browser grants.
- [x] 2.2 Add privacy-screened adapter, deterministic fixture, and guarded insert-or-verify initializer.
- [x] 2.3 Add migration/adapter/initializer tests, including gates, conflicts, rollback, and second-run invariance.

## Backend and frontend

- [x] 3.1 Add Q&A models, repository, IAM-protected list/detail API, projected list query, and API tests.
- [x] 3.2 Add guarded responsive Q&A list/detail frontend and render tests.

## Provisioning and acceptance

- [x] 4.1 Obtain separate explicit authorization before applying `0004` or importing the 20-record fixture; otherwise preserve source-only status.
- [x] 4.2 After authorization, execute exact migration/import, repeat import, and verify authenticated database API.
- [x] 4.3 Run backend tests, Ruff, local smoke, runtime smoke, frontend tests/build, aggregate acceptance, and strict OpenSpec validation.
- [x] 4.4 Update PRD/TECH/status, sync Feishu, archive only after all evidence is recorded.
