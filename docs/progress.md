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

## Implementation Slices

| Slice | Status | Evidence | Notes |
| --- | --- | --- | --- |
| 000 - Fresh V2 repository | Complete | Commit `d723d61`; commit `0affab9` | Repo initialized, README charter pushed. |
| 001 - Executable SaaS foundation | Complete | Slice 001 foundation commit | Backend/frontend/infra starter code added and verified. |
| 002 - Identity, tenant, and authorization vertical | Partial | Backend tests 11/11 | Tenant graph, local identity bridge, authz boundary, organization APIs, team APIs, and committee APIs implemented; production Keycloak/SpiceDB adapters and migrations remain. |
| 003 - Database migration baseline | Complete | Alembic upgrade/downgrade; backend tests 11/11 | Baseline revision captures the current schema; production execution against `db.lindela.io` remains a deployment task. |

## Capability Coverage

Status values:

- `not-started` - no implementation yet.
- `foundation` - core model or boundary exists, but product workflow incomplete.
- `partial` - usable vertical exists, but not full scope.
- `complete` - implemented and verified against product requirements.

| Capability Area | Status | Notes |
| --- | --- | --- |
| Tenant organizations, clubs, schools, associations | foundation | Polymorphic membership supports associations, clubs, schools, teams, and people in the tenant graph. |
| Person identity and athlete profiles | foundation | `Person`, `AppUser`, and `AthleteProfile` models added. |
| Teams, rosters, staff, guardians | partial | Team APIs support team sports and individual sports with captains, vice captains, starters, bench, substitutes, reserves, individual athletes, staff/support roles, and team committees. |
| Events, schedules, attendance | foundation | `Event` and `AttendanceRecord` models added. |
| Performance metrics and assessments | not-started | To follow after core operating vertical. |
| AI-assisted ingestion and analysis | foundation | `Agent`, `AgentAssignment`, `AgentTask`, and SpiceDB `agent` schema added. |
| Training and coaching plans | not-started | Future slice. |
| Competition, fixtures, officials, tournaments | not-started | Future slice. |
| Communications and notifications | foundation | Service boundary exists; workflow pending. |
| Consent, safeguarding, compliance, incidents | not-started | Future slice. |
| Equipment, facilities, assets | not-started | Future slice. |
| Finance, sponsorship, fundraising, ticketing | not-started | Future slice. |
| Reports and intelligence | not-started | Future slice. |
| Integrations and webhooks | not-started | Future slice. |
| SaaS billing/subscriptions | not-started | Future slice. |
| Beautiful operational UI/UX | foundation | First command-center UI shell added. |

## Next Actions

1. Commit and push slice 003 database migration baseline.
2. Replace local/test identity bridge with Keycloak token validation and user
   provisioning rules.
3. Replace in-memory authorization with a live SpiceDB client adapter and
   relationship writer.
4. Continue the operating vertical into event scheduling, attendance, and
   athlete profile workflows.
5. Create deployment runbooks for creating/applying the `afrolete` database and
   role on `db.lindela.io`.
