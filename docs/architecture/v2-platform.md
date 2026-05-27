# AfroLete V2 Platform Architecture

## Decision

AfroLete V2 is a clean service split:

- FastAPI Python backend for domain logic, persistence, authn/authz, jobs, and OpenAPI.
- TypeScript frontend for UI only.
- PJS shared infrastructure for Postgres, Keycloak, SpiceDB, Redis, Temporal, MinIO, and OpenBao.

The existing Next.js full-stack prototype is preserved in git as
`pre-v2-prototype` and remains a salvage source for product ideas, UI patterns,
domain vocabulary, and validation intent.

## Infrastructure Assumptions

- PostgreSQL database: `afrolete` on `db.lindela.io:5432`.
- PostgreSQL role: `afrolete`, eventually replaced or supplemented by OpenBao-issued credentials.
- Keycloak issuer: `https://auth.lindela.io/realms/lindela`.
- SpiceDB endpoint: `62.84.181.55:50051`.
- MinIO S3 endpoint: `http://62.84.181.55:9002`.
- Temporal endpoint: `62.84.181.55:7233`, namespace `afrolete`.
- Redis endpoint: `62.84.181.55:6379`, with an AfroLete-specific DB index or key prefix.
- Secrets should be delivered through OpenBao, not checked into source files.

## Auth Boundary

Keycloak answers who the user is. SpiceDB answers whether that user can perform
an action on a resource. AfroLete bridges the two with `app_users`:

```text
Keycloak sub -> app_users.keycloak_sub -> app_users.id -> SpiceDB user:<id>
```

The frontend never calls SpiceDB and never connects directly to infrastructure
services. It obtains OIDC tokens and sends bearer tokens to FastAPI.

## Persistence Boundary

Postgres stores source-of-truth domain state. SpiceDB stores derived
authorization relationships. Relationship writes should happen in the same
service operation as domain writes, with an outbox added before high-volume or
multi-step workflows.

## Initial Vertical

Build the first production slice in this order:

1. Health, config, and deployment boot.
2. Keycloak token validation.
3. `app_users` identity bridge.
4. Organization and membership model.
5. SpiceDB schema and permission checks.
6. Teams, players, guardians, and staff.
7. Events and attendance.
8. Dashboard summary APIs.

## Current Non-Goals

- No direct Drizzle migration into production.
- No BetterAuth in V2.
- No frontend API routes for business logic.
- No browser direct access to Postgres, Redis, SpiceDB, Temporal, or MinIO.

