# Tasks: Warm the Database Connection Before First User Query

## Planning

- [x] 1.1 Record B18-004 cold/warm measurements and the no-write boundary in PRD-V1-B1-08.
- [x] 1.2 Strict-validate the OpenSpec change before implementation.

## Backend

- [x] 2.1 Add a read-only startup `SELECT 1` warmup on the cached database engine.
- [x] 2.2 Keep fixture/test startup database-free and make warmup failures generic and non-blocking.
- [x] 2.3 Add lifecycle logging with duration only and focused warmup/lifespan tests.

## Verification

- [x] 3.1 Run backend tests and Ruff.
- [x] 3.2 Run a real configured cold/warm API benchmark after startup warmup without outputting credentials or mutating data.
- [x] 3.3 Re-run frontend tests/build and global OpenSpec strict validation to confirm no regression.

## Documentation and archive

- [x] 4.1 Record before/after evidence in B18-004 and archive only after the measured result is reviewed.
