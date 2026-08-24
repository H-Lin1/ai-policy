# Design: Center Authenticated Q&A Hero

## Layout

The eligible authenticated home wrapper owns vertical centering via flex layout. The workspace variant of `PolicyQaWorkbench` keeps the title and input as one bounded unit. Static empty-state explanatory content is omitted only for this workspace entry variant; standard workbench behavior and dynamic result/error state components are unchanged.

On narrow screens and when dynamic content grows, normal document flow wins over fixed centering so all controls and results remain reachable without overlap or clipping.

## Safety

No change is made to `submit`, API calls, role eligibility, request normalization, input limit, disabled state, live regions, placeholder disclosure or error/result rendering. There is no backend/data/configuration operation.

## Rollback

Rollback restores presentation-only JSX/CSS. Do not modify API, Auth, database or data.
