# Proposal: Establish Policy Q&A Entry and RAG Contract Foundation

## Why

Policy Q&A is the primary user journey for both individual and enterprise services, but the rebuilt platform currently has no stable entry or backend contract for a future RAG implementation.

## What Changes

- Add a shared homepage and individual/enterprise Q&A workbench in the observed legacy visual language.
- Add authenticated `POST /api/v1/policy-answers` and a typed, explicitly labelled placeholder engine.
- Add a complete backend RAG handoff document defining API, IAM, existing source tables, future data/index boundaries, validation and acceptance.

## Non-goals

- No real RAG, vector index, embedding, LLM provider, web crawling, persistence, migrations, ingestion, history, streaming, feedback, admin controls, Auth writes or silent fallback.
- No copying old application code. Public legacy pages are observed only for visual language.

## References

- PRD: `docs/PRD-V1-B1-05.md`
- TECH: `docs/TECH-V1-B1-05.md`
- Handoff: `docs/RAG-BACKEND-HANDOFF-V1.md`
- Development step: `B1.5`
