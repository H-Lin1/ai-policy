## 1. Migration and environment

- [x] 1.1 Add S0.2 environment fields for Supabase JWKS URL, issuer, and audience; remove the legacy secret from new templates.
- [x] 1.2 Run the existing foundation migration against the configured Supabase project and repeat it to verify idempotence.

## 2. Backend authentication and readiness

- [x] 2.1 Add current Supabase JWKS resolution and bounded key caching with an explicit unavailable-configuration error.
- [x] 2.2 Validate issuer, audience, signature, subject, and time claims; preserve explicit local bypass behavior.
- [x] 2.3 Include authentication configuration state in production readiness without fetching tokens during health checks.

## 3. Verification and handoff

- [x] 3.1 Add unit and API contract tests for valid/invalid JWKS tokens, missing configuration, and database readiness.
- [x] 3.2 Add a repeatable configured-runtime smoke script that never prints secret values.
- [x] 3.3 Run tests, Ruff, migration checks, runtime smoke, and strict OpenSpec validation; record evidence.
- [x] 3.4 Update `DEVELOPMENT_STATUS.md` and the S0.2 technical plan; archive only after all evidence is recorded.
