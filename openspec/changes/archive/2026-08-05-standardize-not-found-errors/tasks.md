## 1. Backend contract

- [x] 1.1 Register a route-not-found exception handler that uses the existing error-envelope helper and request ID.
- [x] 1.2 Keep explicitly raised endpoint HTTP errors on their current error-code path.

## 2. Verification and handoff

- [x] 2.1 Add a regression test for the absent legacy `/classify` route, including body and `X-Request-ID` assertions.
- [x] 2.2 Run backend tests, Ruff, smoke checks, and strict OpenSpec validation; record evidence.
- [x] 2.3 Update `DEVELOPMENT_STATUS.md` with the corrective-change evidence and final stage-0 handoff state.
