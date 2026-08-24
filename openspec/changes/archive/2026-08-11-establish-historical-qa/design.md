# Design: Historical Government Q&A

## Data and privacy

Source headers are mapped explicitly, never inferred from legacy application code. Records are accepted only after public-host, mandatory-field, parsing, normalized identity, and conservative sensitive-pattern checks. Potentially identifying source columns are neither read into persistence models nor sent to APIs. Failing rows are rejected with stable local reasons.

## Database and operations

The `0004` migration is source-only until separately authorized. It creates one restrictive table after existing IAM/policy revisions. The initializer has separate named double gates for migration and import. It locks imports, verifies exact revision/security/region/fixture identities, inserts only missing exact rows, and fails closed on conflict. It never updates/deletes/downgrades.

## Read path

The API uses the current identity and one request session across IAM and Q&A. Normal pages use a projected window-total query; empty out-of-range pages use an exact count fallback. Detail loads the permitted complete Q&A record. No caching or mock fallback is introduced.

## Failure and rollback

All query, source, configuration, and privacy failures map to stable error states without source text, DB details, credentials, or stack traces. Rollback is code/spec/fixture removal only; no runtime rollback executes automatically.
