# AfroLete Build Progress

This log tracks concrete movement toward the full AfroLete objective: implement
the complete product scope described in `docs/prd.md` and `docs/ext*.md` as an
ergonomic, functional, capable SaaS where AI agents are first-class ecosystem
members.

## Current Goal

Fully implement AfroLete as a production-grade sports operations and
athlete-development platform:

- FastAPI backend and TypeScript frontend.
- PJS shared infrastructure: `db.lindela.io`, Keycloak, SpiceDB, OpenBao,
  Redis, Temporal, MinIO.
- Complete coverage of core PRD and extension features over time.
- Beautiful, novel, operationally efficient UI/UX.
- AI agents as first-class actors with identity, permissions, tasks, and audit.
- Regular commits and pushes.

## Progress Log

### 2026-05-27

- Initialized fresh V2 repository from retained product docs.
- Added project charter in `README.md`.
- Added V2 directory scaffold for backend, frontend, infra, docs, scripts,
  tools, and tests.
- Started implementation slice 001: executable SaaS foundation.
- Implemented slice 001 foundation:
  - FastAPI backend with health/platform routes.
  - SQLAlchemy domain model foundation for identity, organizations, teams,
    athletes, guardians, events, attendance, AI agents, agent assignments, and
    agent tasks.
  - Backend test setup with passing platform route tests.
  - Next/TypeScript frontend shell with a polished SaaS command-center first
    screen.
  - Frontend dependency policy updated to exact Next.js `16.2.6` after the
    reported Next.js/React security release concerns; pnpm build-script policy
    explicitly denies `sharp` install scripts by default.
  - Initial PJS infra artifacts for Postgres, Keycloak, SpiceDB, OpenBao,
    MinIO, Temporal, and systemd.
  - Verification: `uv run ruff check .`, `uv run pytest`,
    `pnpm --filter @afrolete/frontend typecheck`.
- Implemented slice 002 tenant graph foundation:
  - Membership model changed from person-only to polymorphic membership.
  - Associations can have member associations, organizations, teams, and
    individuals.
  - Clubs and schools are organizations that can own teams and can themselves be
    members of associations or other organizations.
  - Association levels added: national, regional, local, and special.
  - Committees added for associations and organizations, with person committee
    memberships so one member can serve across multiple committees at different
    levels.
  - Teams broadened for both team sports and individual sports, with captains,
    vice captains, starters, bench, substitutes, reserves, individual athletes,
    support roles, and team committees.
  - Added local identity bridge and in-memory authorization service boundaries
    that can be replaced by Keycloak and SpiceDB adapters.
  - Added organization, membership, committee, team, roster, and team committee
    API routes.
  - Verification: `uv run ruff check .`, `uv run pytest`,
    `pnpm --filter @afrolete/frontend typecheck`.
- Implemented slice 003 database migration baseline:
  - Added Alembic migration template and initial schema revision for the
    current identity, organization, committee, team, roster, event, attendance,
    and AI-agent tables.
  - Normalized SQLAlchemy enum persistence to use public lowercase API values
    before the baseline migration.
  - Added local SQLite database artifacts to `.gitignore`.
  - Verification: `uv run alembic upgrade head`,
    `uv run alembic downgrade base`, `uv run ruff check .`, `uv run pytest`.
- Implemented slice 004 safeguarding, consent capture, and tenant branding:
  - Added organization contact, public name, subdomain, logo, and brand color
    fields for club/school/association managed sites.
  - Added guardian relationship details for parent, legal guardian, caregiver,
    emergency contact, pickup, medical visibility, and consent authority.
  - Added consent requests and activity consents for organization, team, and
    event scopes.
  - Consent can be captured by one-use web links, SMS, WhatsApp, Telegram,
    email, or manual administrative recording.
  - Added event participation clearance for minors, including guardian and
    consent-required states.
  - Switched the backend default local database to
    `postgresql+asyncpg:///afrolete`.
  - Verification: local PostgreSQL `alembic upgrade head`, PostgreSQL
    `alembic downgrade 537570abceee`, PostgreSQL `alembic upgrade head`,
    `uv run ruff check .`, `uv run pytest`.
- Implemented slice 005 event scheduling and consent-aware attendance:
  - Added event APIs for creating, listing, and reading organization/team
    events.
  - Added attendance APIs for seeding invitations from a team roster, recording
    RSVP/check-in status, and listing event attendance.
  - Attendance check-in now reuses safeguarding clearance so minors cannot be
    marked confirmed or present without a valid guardian consent.
  - SpiceDB event participant and guardian relations now support `person`
    subjects, not only application users.
  - Verification: `uv run ruff check .`, `uv run pytest`.
- Implemented slice 006 Keycloak bearer-token authentication:
  - Added `AFROLETE_AUTH_MODE=keycloak` so deployed APIs require bearer tokens
    instead of local identity headers.
  - Added Keycloak JWKS retrieval, signing-key selection by token `kid`, fixed
    algorithm allow-listing, issuer validation, audience validation, and
    required `exp`/`iat`/`sub` claims.
  - User provisioning now remains behind the existing identity bridge, fed by
    verified token claims instead of test headers.
  - Local development keeps `AFROLETE_AUTH_MODE=local` for trusted local tools
    and unit tests.
  - Verification: `uv run ruff check .`, `uv run pytest`.

## Implementation Slices

| Slice | Status | Evidence | Notes |
| --- | --- | --- | --- |
| 000 - Fresh V2 repository | Complete | Commit `d723d61`; commit `0affab9` | Repo initialized, README charter pushed. |
| 001 - Executable SaaS foundation | Complete | Slice 001 foundation commit | Backend/frontend/infra starter code added and verified. |
| 002 - Identity, tenant, and authorization vertical | Partial | Backend tests 22/22 | Tenant graph, authz boundary, Keycloak bearer-token validation, user provisioning, organization APIs, team APIs, and committee APIs implemented; production SpiceDB adapter remains. |
| 003 - Database migration baseline | Complete | Alembic upgrade/downgrade; backend tests 11/11 | Baseline revision captures the current schema; production execution against `db.lindela.io` remains a deployment task. |
| 004 - Safeguarding, consent, and tenant branding | Partial | Local PostgreSQL migration verified; backend tests 14/14 | Backend model/API support for guardians, consent requests, consent capture channels, minor event clearance, and branded organization sites. |
| 005 - Event scheduling and attendance | Partial | Backend tests 16/16 | Event APIs, roster invitation seeding, attendance recording/listing, and consent-aware check-in implemented; frontend event workflows remain. |
| 006 - Keycloak authentication | Partial | Backend tests 22/22 | Keycloak JWT validation and user provisioning are implemented behind runtime mode; frontend sign-in and live realm smoke test remain. |

## Capability Coverage

Status values:

- `not-started` - no implementation yet.
- `foundation` - core model or boundary exists, but product workflow incomplete.
- `partial` - usable vertical exists, but not full scope.
- `complete` - implemented and verified against product requirements.

| Capability Area | Status | Notes |
| --- | --- | --- |
| Tenant organizations, clubs, schools, associations | partial | Polymorphic membership supports associations, clubs, schools, teams, and people in the tenant graph; organization branding/contact/subdomain fields support owned public sites. |
| Person identity and athlete profiles | partial | `Person`, `AppUser`, and `AthleteProfile` models added; Keycloak token claims provision `AppUser` and `Person` identities. |
| Teams, rosters, staff, guardians | partial | Team APIs support team sports and individual sports with captains, vice captains, starters, bench, substitutes, reserves, individual athletes, staff/support roles, and team committees. |
| Events, schedules, attendance | partial | Event scheduling APIs, roster invitation seeding, attendance recording/listing, and consent-aware check-in are implemented. |
| Performance metrics and assessments | not-started | To follow after core operating vertical. |
| AI-assisted ingestion and analysis | foundation | `Agent`, `AgentAssignment`, `AgentTask`, and SpiceDB `agent` schema added. |
| Training and coaching plans | not-started | Future slice. |
| Competition, fixtures, officials, tournaments | not-started | Future slice. |
| Communications and notifications | foundation | Service boundary exists; workflow pending. |
| Consent, safeguarding, compliance, incidents | partial | Guardian relationships, consent requests, one-use web links, SMS/WhatsApp/Telegram/email/manual consent capture, and minor event clearance are implemented. |
| Equipment, facilities, assets | not-started | Future slice. |
| Finance, sponsorship, fundraising, ticketing | not-started | Future slice. |
| Reports and intelligence | not-started | Future slice. |
| Integrations and webhooks | foundation | Keycloak OIDC bearer-token validation is implemented; other integrations remain future slices. |
| SaaS billing/subscriptions | not-started | Future slice. |
| Beautiful operational UI/UX | foundation | First command-center UI shell added. |

## Next Actions

1. Commit and push slice 006 Keycloak bearer-token authentication.
2. Replace in-memory authorization with a live SpiceDB client adapter and
   relationship writer.
3. Add frontend flows for organization branding, event scheduling, roster
   attendance, guardian consent links, and event clearance review.
4. Add frontend Keycloak sign-in/session handling for `afrolete-web`.
5. Continue athlete profile workflows into performance metrics and assessments.
