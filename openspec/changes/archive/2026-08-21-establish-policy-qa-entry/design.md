# Design: Policy Q&A Entry and RAG Contract Foundation

## Engine and API

The `policy_qa` module exposes a settings-independent engine protocol and typed result. Its current implementation is a static placeholder chosen explicitly at factory construction. The FastAPI service applies existing IAM, requires an active Shenzhen individual or enterprise identity, normalizes and bounds the question, and maps failures to the shared error envelope with `no-store`.

The `POST /api/v1/policy-answers` response is stable across placeholder and future RAG modes. Placeholder results declare their mode, use empty sources, and include a visible notice; they cannot be a fallback after a future engine fails. There are no database calls or writes in this change.

## UI and visual baseline

The shared workbench is used by the public homepage, authenticated home and individual/enterprise workspaces. It follows the existing “政通惠” shell and observed legacy entry language but is independently implemented. Signed-out submission does not transmit the question; it directs the user to login. Eligible users receive explicit empty/loading/result/error states.

## RAG handoff

The handoff specifies existing read-only `policy_documents` and `historical_qa` source tables, recommended future index tables, offline ingestion boundary, citation validation, provider isolation, privacy requirements, safe errors and test gates. Future persistence or infrastructure is excluded from this change and must start through its own approved plan and OpenSpec.

## Rollback

Rollback removes the new route, UI and placeholder implementation only. It does not run any database downgrade, delete data or modify existing source tables.
