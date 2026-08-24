## 1. Planning and audit contract

- [x] 1.1 Add B1.7 integration-acceptance proposal, delta spec, design and DEVELOPMENT_STATUS pointer.
- [x] 1.2 Define stable audit checks and the exact reserved demonstration marker.

## 2. Safe operational implementation

- [x] 2.1 Implement read-only B1.7 integration audit using target/revision/schema/binding checks and named local gates.
- [x] 2.2 Implement guarded B1.7 reset preflight/apply script with target binding, dual flags, candidate locking, dependency-order deletion and rollback.
- [x] 2.3 Add unit/source-contract tests proving no broad deletion, no Auth/policy mutation, secret-safe output and safe no-op behavior.

## 3. Verification and evidence

- [x] 3.1 Run backend tests, Ruff, frontend tests/build and OpenSpec strict validation.
- [x] 3.2 Run B1.7 audit and reset preflight against the configured target; record only aggregate states/counts.
- [x] 3.3 Update DEVELOPMENT_STATUS.md with B1.7 evidence and archive after all tasks pass.
