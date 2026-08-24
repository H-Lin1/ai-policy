## 1. Product and specification

- [x] 1.1 Record the distinct public root, authenticated `/homepage`, login destination, and logout expectations in `PRD-V1-B1-08`.
- [x] 1.2 Strict-validate this OpenSpec change before implementation.

## 2. Frontend implementation

- [x] 2.1 Add the authenticated home path and route-mode handling while preserving the existing public landing and protected role routes.
- [x] 2.2 Update ready-identity navigation, login/mismatch destinations, and direct-login fallback to use `/homepage` where specified.
- [x] 2.3 Redirect explicit logout to `/` with history replacement after local session clearing.
- [x] 2.4 Add route, destination, logout, and responsive/render regression contracts.

## 3. Verification and evidence

- [x] 3.1 Run targeted and full frontend tests plus the production build.
- [x] 3.2 Verify `/`, `/homepage`, login destinations, mismatch action, and logout behavior through route/render contracts and local browser checks without using real credentials.
- [x] 3.3 Update B1.8 PRD and `DEVELOPMENT_STATUS.md` with evidence; archive only after acceptance.
