# AfroLete

AfroLete is an AI-assisted sports operations and athlete-development platform
for clubs, schools, academies, associations, federations, event operators, and
community sport programs.

The project is being rebuilt as a clean V2 platform. The old implementation has
been removed from this working tree. The retained `docs/` directory is the
product scope source of truth, and the V2 architecture is intentionally centered
on a FastAPI backend, a TypeScript frontend, and PJS shared infrastructure.

## Vision

AfroLete exists to give every sports organization the kind of operational
discipline, performance intelligence, athlete safeguarding, and development
feedback usually reserved for elite professional environments.

The long-term product vision is a unified operating system for sport:

- Clubs and schools can manage athletes, teams, staff, facilities, events,
  equipment, finances, communication, compliance, and reporting from one place.
- Coaches can turn attendance, assessments, match events, video, audio, and
  written observations into usable development plans.
- Athletes and parents can see progress, goals, schedules, feedback, safety
  obligations, and opportunities without depending on fragmented chat groups or
  spreadsheets.
- Associations and federations can coordinate competitions, eligibility,
  registrations, officials, compliance, and aggregate reporting across member
  organizations.
- Sponsors, alumni, medical staff, scouts, administrators, and event teams can
  interact through controlled workflows instead of informal side channels.

## Product Goals

AfroLete is designed around these goals:

1. **Unify athlete identity and lifecycle data**
   Maintain a durable person and athlete profile across organizations, teams,
   seasons, guardians, medical details, history, eligibility, and consent.

2. **Make sports operations reliable**
   Replace ad hoc spreadsheets and chat threads with structured workflows for
   rosters, attendance, events, training sessions, fixtures, facilities,
   equipment, communication, payments, and documents.

3. **Create actionable performance intelligence**
   Capture physical, technical, tactical, cognitive, and wellness data; convert
   it into dashboards, reports, plans, alerts, and trend analysis.

4. **Support coaches without burying them in admin**
   Provide session planning, drill libraries, load management, assessments,
   feedback loops, and AI-assisted training recommendations.

5. **Protect minors and vulnerable participants**
   Build consent, safeguarding, guardian access, incident reporting, emergency
   plans, eligibility, health/safety checks, and auditability into the system
   rather than treating them as optional add-ons.

6. **Operate across many sport contexts**
   Support clubs, schools, academies, teams, leagues, tournaments, associations,
   multi-sport events, and community programs without hard-coding a single sport
   or country model.

7. **Provide an extensible integration platform**
   Allow controlled integrations with devices, video platforms, communication
   tools, school systems, finance systems, analytics tools, and future mobile
   apps.

## Product Scope

The retained product documents describe a broad eventual platform. Important
capability areas include:

- Multi-tenant organizations, clubs, schools, associations, teams, programs,
  groups, seasons, and inter-organization relationships.
- Player and person identity, athlete profiles, guardians, emergency contacts,
  medical visibility, membership, and lifecycle tracking.
- Staff, coach, official, volunteer, scout, sponsor, parent, player, and admin
  personas with role-appropriate access.
- Events, training sessions, matches, tournaments, leagues, fixtures, attendance,
  RSVPs, venue logistics, transport, and scheduling constraints.
- Performance metrics, assessments, athlete goals, training plans, drills,
  dashboards, percentile rankings, and progress reports.
- AI-assisted video analysis, audio narration processing, text evaluation
  ingestion, confidence scoring, provenance, and human review.
- Communications, announcements, direct messaging, templates, notification
  preferences, parent portals, and minor-protection communication policies.
- Consent workflows, safeguarding, incident management, background checks,
  eligibility, transfer certificates, compliance documents, weather alerts, and
  emergency action plans.
- Equipment, facilities, assets, inventory, maintenance, loans, QR/barcode
  tracking, and lifecycle audit trails.
- Financial and administrative tools including subscriptions, membership fees,
  fundraising, sponsorship activation, ticketing, revenue reporting, and exports.
- Engagement features such as community feeds, alumni networks, fan engagement,
  awards, ceremonies, donations, and sponsor portals.
- Reporting and intelligence: operational reports, performance reports,
  administrative reports, scheduled reports, exports, and AI-generated insights.

Not all of this is the first release. The first production vertical should prove
the core identity, organization, team, athlete, attendance, and authorization
model before expanding into the full roadmap.

## V2 Architecture

AfroLete V2 is a service split:

- `backend/` - FastAPI Python backend for API contracts, domain logic,
  persistence, authentication, authorization, jobs, imports, and integrations.
- `frontend/` - TypeScript frontend for UI and user workflows. It is a client,
  not the owner of business logic.
- `infra/` - deployment and integration configuration for the PJS shared
  infrastructure.
- `docs/` - product requirements, expansion notes, architecture notes, and ADRs.
- `scripts/` - project automation entrypoints.
- `tools/` - development and migration utilities.
- `tests/` - cross-service and end-to-end tests.

The backend owns:

- OpenAPI schema and API versioning.
- PostgreSQL persistence and Alembic migrations.
- Keycloak token validation and identity bridging.
- SpiceDB permission checks and relationship writes.
- Background jobs and workflow orchestration.
- File/object access through MinIO or S3-compatible storage.
- External integration boundaries.

The frontend owns:

- Product UI and workflows.
- Client-side routing and state.
- Calling FastAPI through typed API clients.
- Displaying authorization-aware experiences based on backend-provided context.

The frontend must not connect directly to Postgres, Redis, SpiceDB, Temporal, or
MinIO. It must not become a second backend.

## Infrastructure Targets

Production targets the PJS shared services:

| Capability | Target |
| --- | --- |
| Database | PostgreSQL database `afrolete` on `db.lindela.io:5432` |
| Authentication | Keycloak realm `lindela` at `https://auth.lindela.io/realms/lindela` |
| Authorization | SpiceDB relationship and permission service |
| Secrets | OpenBao rendered into runtime environment files |
| Cache / queues | Redis on the shared PJS infrastructure |
| Workflows | Temporal namespace `afrolete` |
| Object storage | MinIO/S3-compatible storage |
| Deployment | Systemd-managed services and PJS deploy scripts |

Real secrets must never be committed. Runtime credentials should come from
OpenBao, a local `.env` excluded from git, or deployment-managed environment
files.

## Authentication And Authorization

AfroLete uses a split identity model:

- **Keycloak answers identity**: who the user is, how they authenticated, and
  which identity claims and realm/client roles they have.
- **AfroLete bridges identity**: maps Keycloak `sub` to an internal application
  user/person record.
- **SpiceDB answers authorization**: whether the internal user can perform an
  action on a specific organization, team, athlete, event, report, form, or
  other resource.

The canonical bridge is:

```text
Keycloak sub -> app_users.keycloak_sub -> app_users.id -> SpiceDB user:<id>
```

Do not use Keycloak roles as the only authorization system. Realm/client roles
can express broad capabilities, but resource-level access belongs in SpiceDB.

## Data And Domain Standards

AfroLete should model the domain explicitly. Important standards:

- Use stable internal UUIDs for domain records.
- Keep person identity separate from organization-specific memberships and
  athlete/team participation.
- Treat organization boundaries as first-class tenancy boundaries.
- Use audit timestamps on persistent domain records.
- Use Alembic for database schema evolution.
- Keep authorization relationships synchronized with source-of-truth domain
  writes. Add an outbox before high-volume or multi-step relationship syncing.
- Store derived analytics separately from raw observations where provenance
  matters.
- Record source, confidence, reviewer, and timestamp for AI-assisted ingested
  performance data.
- Design for multiple sports, languages, countries, and organization types from
  the beginning, but do not overbuild generic abstractions before the first
  vertical is working.

## Engineering Standards

### Backend

- Python 3.12+.
- FastAPI for HTTP APIs.
- Pydantic v2 for schemas and settings.
- SQLAlchemy 2.x for persistence.
- Alembic for migrations.
- PostgreSQL as the primary database.
- Redis for cache/queue support where appropriate.
- Temporal for durable workflows when a process spans time, retries, or external
  systems.
- OpenAPI is a public contract and should be kept coherent.
- Business rules belong in services/domain modules, not route handlers.
- Route handlers should authenticate, authorize, validate, call application
  services, and return structured responses.

### Frontend

- TypeScript-first.
- The frontend is a UI client for the FastAPI backend.
- Prefer generated or typed API clients from OpenAPI.
- Keep state local and explicit; avoid hidden business rules in UI components.
- Build dense, operational, accessible interfaces for repeated use.
- Match UI to the sports operations domain: clear tables, schedules, profiles,
  forms, dashboards, filters, alerts, and review flows.
- Do not introduce frontend-only data stores that conflict with backend source
  of truth.

### Infrastructure

- No committed secrets.
- Runtime config belongs in OpenBao-backed env files or local ignored `.env`
  files.
- Every deployable service should have health checks.
- Services should fail clearly on missing required config.
- Logs should be structured enough for debugging production incidents.
- Background workers must be idempotent where retries are possible.
- Database and SpiceDB changes should be deployable, reversible where practical,
  and documented.

### Testing

Testing should scale with risk:

- Unit tests for pure domain and validation logic.
- API tests for route contracts, auth decisions, and error behavior.
- Migration tests or smoke checks for schema changes.
- Integration tests for Keycloak/SpiceDB/Postgres flows where feasible.
- End-to-end tests for core user journeys once the frontend exists.
- Regression tests before refactoring behavior that is already in use.

## Delivery Method

The first implementation milestone should be a narrow but production-shaped
vertical:

1. Repository tooling and local development commands.
2. FastAPI app boot, settings, logging, health checks.
3. PostgreSQL connection and Alembic baseline.
4. Keycloak JWT validation.
5. `app_users` identity bridge.
6. Organization, membership, and role model.
7. SpiceDB schema and permission checks.
8. Teams, athletes, guardians, and staff.
9. Events and attendance.
10. Dashboard summary APIs.
11. Minimal frontend workflows for the above.

After this vertical is stable, expand into assessments, performance metrics,
reports, communications, consent, equipment, competitions, and AI ingestion.

## Repository Layout

```text
backend/
  app/
    api/          HTTP route modules and API versioning
    core/         settings, logging, security configuration
    db/           database engine/session and Alembic integration
    models/       SQLAlchemy persistence models
    schemas/      Pydantic request/response schemas
    services/     domain services and external integrations
    workers/      background worker entrypoints
  alembic/        database migrations
  tests/          backend unit and integration tests

frontend/
  app/            frontend route tree
  public/         static assets
  src/            components, features, client libraries, styles, types

infra/
  keycloak/       realm/client setup notes
  openbao/        policy and agent templates
  spicedb/        authorization schemas and relationship tooling
  postgres/       database setup and migration helpers
  minio/          object storage setup
  temporal/       namespace and worker deployment setup
  systemd/        service units and environment templates
  deploy/         deployment scripts and runbooks

docs/
  prd.md          core product requirements
  ext*.md         expansion and capability notes
  architecture/   architecture notes
  adr/            architecture decision records

scripts/          project automation
tools/            developer and migration tools
tests/e2e/        cross-service end-to-end tests
```

## Documentation Standards

- Use `docs/adr/` for durable technical decisions.
- Keep `docs/architecture/` for system boundaries, integration patterns, and
  deployment assumptions.
- Treat product docs as planning source material. Do not silently rewrite them
  to match implementation shortcuts.
- When scope is deferred, record it as deferred rather than deleting it from the
  product vision.

## Current Status

This repository is at the beginning of the V2 rebuild:

- Git is initialized on `main`.
- The old code has been removed.
- The product documents have been retained.
- The V2 directory skeleton exists.
- Implementation code has not yet been built in the fresh tree.

## Immediate Next Steps

1. Add backend project files: `pyproject.toml`, FastAPI app entrypoint, settings,
   health route, Alembic config, and test setup.
2. Add frontend project files: package manager config, TypeScript config, Next
   app shell, and API client boundary.
3. Add infra setup docs for creating `afrolete` database/user on `db.lindela.io`.
4. Add Keycloak client and SpiceDB schema starter files.
5. Commit each verified slice as it lands.

