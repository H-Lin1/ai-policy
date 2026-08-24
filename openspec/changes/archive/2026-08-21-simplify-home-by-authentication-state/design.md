# Design: Simplify Home by Authentication State

## State routing

`WorkspaceHomePage` continues to choose based on the existing auth-provider state. `signed_out` and `configuration_missing` render `PublicLanding`, which does not import or mount the Q&A workbench. A ready identity with `individual` or `enterprise` renders the existing workspace Q&A variant directly. A ready identity without either role renders existing authorized workspace links as a compact fallback.

## Safety and permissions

Only the existing workbench may call the policy-answer endpoint. It remains unavailable to signed-out and non-eligible users. The global header still derives role links from the real `/me` identity. No change to route protection, token handling, response behavior, error handling, persistence or server code occurs.

## Presentation

The public cards become the first primary visual content below the shared header. The eligible Q&A hero becomes the first primary visual content below that same header. The removed summary is not replaced by a visual-only duplicate of the current identity, region or role. Existing responsive styles continue to prevent overflow at supported narrow widths.

## Rollback

Restore the deleted homepage presentation components and associated styles only. Do not modify data or run migration/rollback commands.
