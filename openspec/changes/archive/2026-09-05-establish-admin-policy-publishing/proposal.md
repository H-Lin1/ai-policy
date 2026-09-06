## Why

The policy library is read-only and can only be provisioned through an operator script. B1.8 needs an administrator workflow for reviewed manual policy entry and stable batch Markdown import without exposing write access to ordinary roles.

## What Changes

- Add admin-only manual policy authoring and batch Markdown parsing for at most 20 files, each at most 2 MB, with no total batch-size limit.
- Add a downloadable Markdown example, per-file isolated validation, editable preview, selected draft saving and selected publishing.
- Add draft/published/withdrawn lifecycle, duplicate checks, audit events and public published-only filtering.
- Add standalone migration `0007_admin_policy_publishing`, APIs, admin pages and end-to-end evidence.

## Non-Goals

- No PDF/DOCX/OCR/ZIP/folder upload, AI metadata generation, automatic web verification, policy version graph, scheduled publishing or physical deletion.
- No non-admin write access, browser direct database writes, mock fallback or change to real RAG.

## Capabilities

### New Capabilities

- `admin-policy-publishing`: administrator manual authoring, batch Markdown parsing, draft/publish/withdraw lifecycle and audit.

### Modified Capabilities

- `policy-library`: ordinary policy list/detail includes only published records after admin lifecycle is introduced.

## Impact

- Adds migration/model/service/router code and frontend admin policy pages.
- Existing 20 imported records become published external-source policies without content mutation.
- Applies only to standalone PostgreSQL and preserves current IAM, RLS and API error boundaries.

