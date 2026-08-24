# Proposal: Establish Department Classification Foundation

## Why

The project has a frozen `DepartmentClassifier` boundary but no verified real computation. B1.4 turns the user-provided classifier environment into a small, authenticated Shenzhen classification slice while preserving explicit readiness and legacy-code boundaries.

## What Changes

- Add a read-only model asset manifest and verified concrete classifier adapter.
- Add `POST /api/v1/classifications` with current IAM, Shenzhen scope, shared errors, request IDs, and no-store behavior.
- Add a guarded responsive `/classify` workbench and API client.
- Add deterministic asset/inference fixtures and acceptance evidence without database migration or persistence.

## Non-goals

- No database tables, migrations, AI run persistence, full dataset import, search, RAG, embedding, chatbot, policy linking, model training, Auth mutation, Mock fallback, or cross-region fallback.
- No reading or copying old Flask/frontend implementation. Only verified pure classification computation may be adapted behind the new contract.

## References

- PRD: `docs/PRD-V1-B1-04.md`
- TECH: `docs/TECH-V1-B1-04.md`
- Development step: `B1.4`
