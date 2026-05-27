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

## Implementation Slices

| Slice | Status | Evidence | Notes |
| --- | --- | --- | --- |
| 000 - Fresh V2 repository | Complete | Commit `d723d61`; commit `0affab9` | Repo initialized, README charter pushed. |
| 001 - Executable SaaS foundation | Complete | Slice 001 foundation commit | Backend/frontend/infra starter code added and verified. |

## Capability Coverage

Status values:

- `not-started` - no implementation yet.
- `foundation` - core model or boundary exists, but product workflow incomplete.
- `partial` - usable vertical exists, but not full scope.
- `complete` - implemented and verified against product requirements.

| Capability Area | Status | Notes |
| --- | --- | --- |
| Tenant organizations, clubs, schools, associations | foundation | `Organization`, `Membership`, and SpiceDB organization schema added. |
| Person identity and athlete profiles | foundation | `Person`, `AppUser`, and `AthleteProfile` models added. |
| Teams, rosters, staff, guardians | foundation | `Team`, `TeamRosterEntry`, and `GuardianRelationship` models added. |
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

1. Commit and push slice 001.
2. Start slice 002: identity, tenant, and authorization vertical.
3. Add Alembic baseline migration.
4. Implement organization creation and membership APIs.
5. Wire SpiceDB relationship writes behind service boundaries.
