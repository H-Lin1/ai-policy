## 1. Product and specification

- [x] 1.1 Record B18-002 mismatch behavior, actions, permission boundary and acceptance in `PRD-V1-B1-08`.
- [x] 1.2 Strict-validate the OpenSpec change before implementation.

## 2. Frontend implementation

- [x] 2.1 Model matched, mismatched and direct-login post-auth decisions using backend roles.
- [x] 2.2 Render an accessible blocking mismatch dialog with actual-service and switch-account actions.
- [x] 2.3 Ensure switch-account signs out the authenticated session and preserves the selected entrance login context.
- [x] 2.4 Add responsive dialog styles and regression contracts.

## 3. Verification and evidence

- [x] 3.1 Run targeted/full frontend tests and production build.
- [x] 3.2 Verify mismatch decisions, dialog actions, matching behavior and mobile layout through render/behavior contracts without exposing credentials or mutating the user's browser session.
- [x] 3.3 Update B1.8 PRD and `DEVELOPMENT_STATUS.md` with evidence; archive only after acceptance.
