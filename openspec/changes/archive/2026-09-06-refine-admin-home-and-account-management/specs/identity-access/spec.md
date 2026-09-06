## ADDED Requirements

### Requirement: Role-aware authenticated routing

The frontend SHALL route authenticated administrators to `/homepage`, where the admin workbench is rendered directly. The legacy `/admin` frontend route SHALL not exist; ordinary individual, enterprise and government role routes retain their existing authorization behavior.

#### Scenario: Admin login destination

- **WHEN** an admin completes local login or opens the authenticated root
- **THEN** navigation lands on `/homepage` and renders the admin workbench

#### Scenario: Legacy admin path is unavailable

- **WHEN** any caller opens `/admin`
- **THEN** the frontend renders its normal not-found behavior and does not expose the admin workbench through that path
