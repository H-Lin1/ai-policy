# TECH-V1-UI-06 | Correct Authenticated Q&A Horizontal Centering

| Item | Value |
|---|---|
| Document ID | `TECH-V1-UI-06` |
| Version | `V1.0` |
| Status | Accepted |
| Scope | `UI1.5` authenticated Q&A horizontal-centering correction after archived UI1.4 |
| OpenSpec | `2026-08-21-correct-authenticated-qa-horizontal-centering` |
| Database/API change | None |
| Feishu copy | [TECH-V1-UI-06](https://a9ihi0un9c.feishu.cn/docx/MRDsdr4WLohFV2xMPYmc2xjpnVy) |

## Decision

Correct the authenticated Q&A hero so its heading and input surface are horizontally centered in the full homepage content area, in addition to the accepted desktop vertical centering. The reported leftward layout came from using viewport-based negative horizontal margins on a workbench that is already inside a full-width homepage flex container. In this nesting context, those margins shift and oversize the visual surface rather than centering it.

Remove the workspace-entry negative margins. The `qa-home` wrapper already spans the page width; the workbench will occupy its available width normally, while its heading and form retain explicit bounded widths with `margin-inline: auto`.

## Boundaries

This is CSS-only presentation correction. It does not change the Q&A component state, API, IAM, session/token handling, keyboard submission, placeholder disclosure, error/result states, data, database, migration, configuration or telemetry. No write, deletion, mock response or fallback is introduced.

## Verification and rollback

At desktop width, verify the heading and input centers align to the viewport/content midpoint and the decorative surface does not overflow horizontally. At mobile width, verify normal responsive flow and no horizontal scroll. Run frontend tests/build, full backend regression, strict validation, Feishu sync and archive. Rollback restores only the removed CSS margins.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-21 | V1.0 | Defined correction of negative-margin-induced horizontal displacement on the authenticated Q&A homepage. |
| 2026-08-21 | V1.0 | Accepted after workspace entry now fills its existing full-width parent without viewport-relative offset; frontend tests/build, backend regression, Ruff, smoke/runtime/acceptance and strict validation passed. No migration, data/Auth write or deletion was performed. |
