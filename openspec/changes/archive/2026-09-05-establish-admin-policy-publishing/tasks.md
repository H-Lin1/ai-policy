## 1. Migration and models

- [x] 1.1 Add `0007_admin_policy_publishing`, lifecycle/source fields and policy audit events while preserving 20 imported rows as published.
- [x] 1.2 Add admin policy schemas, deterministic Markdown parser/example and migration/parser tests.

## 2. Backend

- [x] 2.1 Add admin list/detail/manual create, batch parse, selected save/publish, single publish and withdraw services/APIs.
- [x] 2.2 Add published-only filtering to ordinary policy list/detail and authorization/duplicate/transaction tests.

## 3. Frontend

- [x] 3.1 Add admin policy navigation, list and manual/Markdown batch page with download example, edit, preview and per-item state.
- [x] 3.2 Add selected draft/publish actions, withdraw action and responsive/accessibility render tests.

## 4. Verification

- [x] 4.1 Run full backend/frontend/Ruff/build/OpenSpec gates.
- [x] 4.2 Apply `0007` to authorized local standalone database and run end-to-end manual/batch/partial-failure/draft/publish/withdraw/role tests.
- [x] 4.3 Update PRD/TECH/DEVELOPMENT_STATUS evidence and archive after all tasks pass.
