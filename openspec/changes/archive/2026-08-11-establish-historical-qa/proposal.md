# Proposal: Establish Historical Government Q&A

## Why

The project has 1,650 adjudicated Shenzhen government Q&A records but no approved, privacy-screened, IAM-protected historical Q&A read path. B1.3 establishes that independent source-of-truth slice before later B1.5 retrieval work.

## What Changes

- Add privacy-first CSV adapter and deterministic 20-record fixture from user-provided adjudicated public-source data.
- Add `0004_historical_qa` schema source, guarded initializer, read-only list/detail API, and responsive guarded frontend path.
- Reuse existing IAM, request-scoped database session, pagination/errors/no-store, and visual baseline.

## Non-goals

- No full 1,650-row import, model/RAG, embedding, similarity search, chatbot, policy linkage assertion, user submission, legacy source code, or Auth mutation.
- No migration or external write runs without separate explicit authorization.

## References

- Development step: `B1.3`.
- PRD: `PRD-V1-B1-03`.
- TECH: `TECH-V1-B1-03`.
