## ADDED Requirements

### Requirement: Efficient authenticated policy list read path

The database-backed policy list SHALL reuse one request-scoped database session for IAM and policy reads, and a normal non-empty page SHALL execute one projected policy statement that returns exact filtered total metadata without selecting full policy text or detail-only provenance. The optimization SHALL preserve identity enforcement, ordering, filtering, pagination, list/detail response schemas, errors, and `Cache-Control: no-store`, and SHALL require no cache or database mutation.

#### Scenario: Authorized non-empty page is loaded

- **WHEN** an active Shenzhen identity requests a non-empty policy list page
- **THEN** IAM and policy reads use the same request session and the policy repository returns the page and exact total from one projected statement without loading `content_text`

#### Scenario: Requested page is beyond the final record

- **WHEN** an authorized request has an offset beyond all matching policy rows
- **THEN** the API returns an empty page with the exact filtered total using a bounded fallback count and preserves the pagination contract

#### Scenario: Performance patch is accepted

- **WHEN** acceptance runs against the configured Supabase project after `/me` primes the login path
- **THEN** at least three warm page-one requests each complete within 5 seconds with median at most 2 seconds, and a cold request completes within 15 seconds or improves at least 50 percent from the recorded baseline, without exposing sensitive values or mutating external data
