## Context

See `proposal.md` for the motivation. S0.1 already has SQLAlchemy, Alembic, a database readiness check, and an HS256-only authentication placeholder. The configured Supabase project now reports an ECC (P-256) current JWT signing key and a legacy HS256 key only for compatibility with older tokens.

## Goals / Non-Goals

**Goals:**

- Prove a real Supabase PostgreSQL connection from the local backend.
- Keep the empty foundation migration idempotent and isolated from business data.
- Verify current Supabase asymmetric tokens through a cached JWKS client.
- Make missing configuration, network failures, and invalid tokens explicit and testable.

**Non-Goals:**

- Creating business tables, seed data, user-facing login screens, or role-management APIs.
- Rotating, creating, or revoking Supabase signing keys.
- Supporting the deprecated Legacy HS256 secret as a silent fallback.
- Importing any legacy Flask, Excel, FAISS, embedding, or model assets.

## Decisions

- **JWKS source:** derive `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json` from `SUPABASE_URL`, with an optional `SUPABASE_JWKS_URL` override for tests or proxies. Deriving the URL keeps the local environment small while allowing deployment-specific routing.
- **JWT claims:** derive the issuer as `<SUPABASE_URL>/auth/v1`, default the audience to `authenticated`, and allow explicit environment overrides. Restrict accepted algorithms to asymmetric `ES256` and `RS256`; do not accept an algorithm from the token header without this allow-list.
- **Key caching:** use PyJWT's `PyJWKClient`, cached by JWKS URL, so normal requests do not fetch keys repeatedly. A key-fetch or signature failure becomes `AUTH_NOT_CONFIGURED` for missing/unreachable configuration or `AUTH_INVALID` for a supplied bad token.
- **Database connection:** preserve the existing `postgresql://` normalization to the installed `psycopg` driver. The Supabase Session pooler URI is the default local choice because it works on IPv4 networks; Direct can be selected later when the deployment network supports it.
- **Migration bookkeeping:** keep Alembic's version table as migration metadata and leave business schema creation to later changes. This change executes only the existing `0001_foundation_schema` migration.
- **Compatibility:** retain the old `SUPABASE_JWT_SECRET` setting only as an ignored/deprecated configuration name during transition; it is not used for verification and is removed from new environment templates.

## Risks / Trade-offs

- [JWKS endpoint unavailable] → Keep public health checks available, return `AUTH_NOT_CONFIGURED` only when a protected endpoint needs verification, and expose no token or key material.
- [Signing-key rotation] → Cache keys with the library's bounded lifespan and retry unknown key IDs through the JWKS client; operators can override the endpoint without code changes.
- [Pooler feature differences] → Use a Session pooler for the long-lived API and Alembic; do not use Transaction pooler as the default for migration or session-dependent work.
- [Audience/issuer variation] → Make both values explicit settings with secure Supabase defaults and test the configured values, rather than disabling claim validation.

## Migration Plan

1. Add JWKS settings, verifier, and readiness configuration checks.
2. Install the PyJWT crypto extra needed for ECC verification.
3. Run `alembic upgrade head` against the configured Supabase project and repeat it to prove idempotence.
4. Run backend tests, runtime smoke checks, and strict OpenSpec validation.
5. Roll back application code by reverting the verifier/configuration change; the foundation schema can be downgraded only on a disposable demo project because downgrade removes the `app` schema.
