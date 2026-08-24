# policy-library Specification Delta

## ADDED Requirements

### Requirement: Explicitly authorized sample provisioning

The system SHALL provide a fail-closed operator initializer that is inspect-only by default and SHALL require separate apply and confirmation flags before applying the exact `0003_policy_library` migration or importing the deterministic 20-record fixture. The import SHALL require verified Supabase target binding, the exact revision and schema, one active Shenzhen region, RLS with no browser policies or grants, and SHALL insert missing exact records without updating or deleting existing rows.

#### Scenario: Provisioning is inspected without write flags

- **WHEN** the initializer runs without both flags for a write operation
- **THEN** it reports a stable preflight state and performs no migration or data change

#### Scenario: Fixture is imported twice

- **WHEN** the authorized fixture import runs twice against the same valid database
- **THEN** the first run inserts only missing records and the second run inserts zero records while all row values and audit timestamps remain unchanged

#### Scenario: Existing policy identity conflicts

- **WHEN** an existing UUID or source/hash identity differs from the expected fixture record
- **THEN** the initializer aborts without updating, deleting, or partially inserting policy rows

#### Scenario: Unauthorized full dataset remains closed

- **WHEN** provisioning completes under this change
- **THEN** exactly the deterministic 20-record fixture is in scope and the complete CSV remains unimported
