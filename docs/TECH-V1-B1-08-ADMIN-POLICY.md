# TECH-V1-B1-08-P | Admin policy authoring and batch Markdown publishing

| Item | Value |
|---|---|
| Step | B1.8 / B18-009 |
| Version / status | V1.1 / Accepted |
| PRD | [`PRD-V1-B1-08-ADMIN-POLICY`](./PRD-V1-B1-08-ADMIN-POLICY.md) |
| OpenSpec | `2026-09-05-establish-admin-policy-publishing` |
| Migration | `0007_admin_policy_publishing` |

## Architecture

Extend `policy_documents` with `source_type`, `publication_status`, optional raw Markdown metadata, and server-owned author/publish/withdraw audit fields. Add append-only `policy_document_events`. Existing imported policies migrate to `source_type=external_url` and `publication_status=published`; public queries add an explicit published filter.

Manual and Markdown input share one validated `PolicyDraftInput`. The browser reads selected `.md` files as UTF-8 and submits filename plus text; the backend remains authoritative for count, UTF-8 content length, YAML/front-matter parsing, allowed fields, normalization, hashes and duplicate checks. No total batch-size limit is enforced; count is capped at 20 and each encoded file at 2 MB.

To avoid a new YAML dependency, the accepted front matter is a flat `key: value` mapping with no aliases, nested collections or executable tags. Markdown headings are preserved as plain content text. The example template is served by the API.

## API

Admin-only endpoints under `/api/v1/admin/policies`: list/detail, manual create, Markdown parse batch, save selected drafts, publish selected items, publish one draft and withdraw one published policy. All use existing identity and `admin` authorization, common errors/request ID and no-store.

Batch parse is non-persistent. It returns one result per input in source order with `ready`, `warning` or `failed`, parsed editable fields and bounded errors/warnings. Save/publish receives selected validated items and processes each independently, returning per-item success/failure.

## Security and rollback

Requests forbid actor, region, status timestamps and hashes. Raw Markdown is bounded and never logged. URLs accept only HTTP(S). HTML inside Markdown is stored as text and never rendered as HTML. No physical delete endpoint exists. Rollback disables admin routes and uses a forward migration; published data is not automatically deleted.

Authorized local acceptance on 2026-09-06 applied `0007_admin_policy_publishing` to `aipolicy_local`, preserved 20 imported policy hashes, parsed the downloadable example, isolated one invalid item in a two-file batch, created/published a Markdown policy, created then published and withdrew a manual draft, rejected an exact duplicate, and confirmed non-admin 403 plus published-only ordinary reads. Chrome measurements at 1440px and 390px found no horizontal overflow on manual or batch pages.
