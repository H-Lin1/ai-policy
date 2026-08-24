# TECH-V1-UI-05 | Center the Authenticated Q&A Hero

| Item | Value |
|---|---|
| Document ID | `TECH-V1-UI-05` |
| Version | `V1.0` |
| Status | Accepted |
| Scope | `UI1.4` authenticated Q&A composition patch after archived UI1.3 |
| OpenSpec | `2026-08-21-center-authenticated-qa-hero` |
| Database/API change | None |
| Feishu copy | [TECH-V1-UI-05](https://a9ihi0un9c.feishu.cn/docx/O87Qd5Jdlo2N3gxEOXNcRGNfndf) |

## Decision

For the authenticated individual/enterprise homepage in its initial empty-question state, center the Q&A hero as a coherent group within the available page area between the shared header and footer. Remove the two explanatory lines currently rendered below its input surface: “从这里开始咨询” and “可咨询政策条件、办理方向或企业发展支持等问题。”

The compact instruction inside the input surface (“按 Enter 发送，Shift + Enter 换行”) remains because it communicates the keyboard submission rule. Loading, explicit errors, signed-in state, placeholder results and source-empty results remain available after submission and must not be hidden.

## Implementation boundaries

This change modifies only JSX presentation and CSS. It does not change the policy-answer API, IAM, token handling, input limits, submit semantics, error state, response state, database, migration, configuration or telemetry. No question persistence, mock result, browser-side fallback, deletion or write is introduced.

The outer authenticated home container becomes a flex layout with a safe minimum height accounting for the global header and footer, while the workbench retains a bounded maximum content height and scrolls normally if a result exceeds the available vertical space. Narrow viewports revert to naturally flowing layout to avoid clipped content.

## Verification and rollback

Render checks assert removal of the two empty-state lines while preserving loading/error/result states and keyboard submission. Browser verification checks visual vertical centering at desktop width and no overflow at mobile width. Full backend/frontend regression, strict validation, documentation sync and archive remain required. Rollback restores only the two static lines and positioning styles; no server or data operation applies.

## Change Record

| Date | Version | Change |
|---|---|---|
| 2026-08-21 | V1.0 | Defined centered authenticated Q&A composition and removal of redundant post-input empty-state copy. |
| 2026-08-21 | V1.0 | Accepted after full frontend/backend regression and strict validation; no migration, data/Auth write or deletion was performed. |
