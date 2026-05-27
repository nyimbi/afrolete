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
- Implemented slice 007 SpiceDB authorization adapter:
  - Added `AFROLETE_AUTHZ_MODE=spicedb` so deployed APIs use the shared PJS
    SpiceDB service instead of the in-memory local authorization set.
  - Relationship writes now map AfroLete relationships to SpiceDB `TOUCH`
    updates for idempotent role and membership synchronization.
  - Permission checks now map resource, permission, and internal app user
    subject IDs to SpiceDB `CheckPermission` calls.
  - SpiceDB check failures fail closed; write failures surface instead of
    silently dropping authorization relationships.
  - Verification: `uv run ruff check .`, focused SpiceDB unit tests.
- Implemented slice 008 operational SaaS console:
  - Replaced the static first screen with a real Next.js operations console for
    local-mode organization creation, team creation, athlete intake, roster
    assignment, event scheduling, roster-based attendance seeding, attendance
    recording, guardian linking, consent request creation, and event clearance
    checks.
  - Added a frontend API client that sends local identity headers in development
    and surfaces backend validation errors in the activity feed.
  - Added a public one-use guardian consent page at `/consent/[token]` that
    captures grant/deny responses through the backend token endpoint.
  - Fixed default backend CORS to allow the actual Next development origin at
    `http://127.0.0.1:3000`.
  - Verification: `pnpm --filter @afrolete/frontend typecheck`,
    `pnpm --filter @afrolete/frontend build`, production Playwright screenshots
    at desktop and mobile sizes.
- Implemented slice 009 first-class AI agent operations:
  - Added agent APIs for organization-scoped agent creation, assignment to
    organization/team/event/athlete-profile scopes, task queueing, task listing,
    and human review/status updates.
  - Agent creation now writes the agent owner relationship; assignment writes
    `assigned_agent` relationships to SpiceDB-compatible resources.
  - Added cross-organization scope validation so agents cannot be assigned to
    resources outside their tenant.
  - Added the agent identity and task inbox lane to the operational console,
    including agent creation, assignment buttons, task queueing, and review
    status transitions.
  - Verification: `uv run ruff check .`, `uv run pytest`,
    `uv run alembic upgrade head`, `pnpm --filter @afrolete/frontend
    typecheck`, `pnpm --filter @afrolete/frontend build`.
- Implemented slice 010 athlete performance metrics and assessments:
  - Added performance metric definitions with sport, category, units, value
    ranges, weights, and directionality.
  - Added athlete performance observations with event context, source,
    confidence, verification status, raw value, notes, and recorder provenance.
  - Added athlete assessments with physical, technical, tactical, mental, and
    computed AfroLete Score components using the PRD weighting model.
  - Added summary APIs for latest score, rating, observation count, and
    assessment count.
  - Added the performance lane to the console for metric creation, observation
    recording, assessment recording, and score review.
  - Verification: `uv run ruff check .`, `uv run pytest`, PostgreSQL
    `alembic upgrade head`, PostgreSQL `alembic downgrade 6138f95a6b16`,
    PostgreSQL `alembic upgrade head`, `pnpm --filter @afrolete/frontend
    typecheck`, `pnpm --filter @afrolete/frontend build`.
- Implemented slice 011 training and coaching plans:
  - Added a training drill library with sport, focus area, category, equipment,
    age suitability, duration, intensity, description, and coaching points.
  - Added training plans that can be scoped to an organization, team, and/or
    athlete profile, with AI-generated provenance, source summary, load
    guidance, recovery protocol, and progress checkpoints.
  - Added weekly training plan items/blocks linked to drills and carrying
    sequence, day label, focus area, duration, intensity, and coaching notes.
  - Added session planning with team/event/plan scope validation and target
    training load computed as `duration_minutes * rpe_target`.
  - Added the Training console lane for drill creation, plan creation, weekly
    block creation, and load-aware session planning.
  - Verification: `uv run ruff check .`, `uv run pytest`, PostgreSQL
    `alembic upgrade head`, PostgreSQL `alembic downgrade dea9ca28416e`,
    PostgreSQL `alembic upgrade head`, `pnpm --filter @afrolete/frontend
    typecheck`, `pnpm --filter @afrolete/frontend build`, production
    Playwright screenshot at `/private/tmp/afrolete-training-console.png`.
- Implemented slice 012 competition management foundation:
  - Added competition records for leagues, tournaments, cups, and friendly
    series with sport, format, season dates, points rules, tiebreakers, status,
    and rules summary.
  - Added registered competition participants with team, seed, group, and
    tenant-scoped validation.
  - Added fixtures with home/away teams, schedule, stage/round, venue, linked
    event support, result confirmation, and final score recording.
  - Added official assignments with role, status, certification level, and
    conflict notes, restricted to organization members.
  - Added match event logging for goals, cards, substitutions, injuries, and
    notes.
  - Added computed standings with played/win/draw/loss, goals for/against,
    goal difference, and points using the competition scoring rules.
  - Added the Competition console lane for competition creation, team
    registration, fixture creation, result confirmation, official assignment,
    match event logging, readiness checks, and standings review.
  - Verification: `uv run ruff check .`, `uv run pytest`, PostgreSQL
    `alembic upgrade head`, PostgreSQL `alembic downgrade b23079d70437`,
    PostgreSQL `alembic upgrade head`, `pnpm --filter @afrolete/frontend
    typecheck`, `pnpm --filter @afrolete/frontend build`, production
    Playwright screenshot at `/private/tmp/afrolete-competition-console.png`.
- Implemented slice 013 communications and notifications:
  - Added reusable communication templates with message type, channel, subject,
    body, variables, locale, and active state.
  - Added scoped communication messages for organization, team, event, and
    person targets, with tenant-safe recipient expansion and urgent/quiet-hours
    controls.
  - Added recipient delivery records with channel destination, queued,
    suppressed, delivered, read, and failed states plus delivery/read
    timestamps.
  - Added notification preferences for frequency, preferred channel, language,
    quiet hours, and emergency override.
  - Added minor-safe guardian copying so direct person messages to minors can
    include guardians with consent authority.
  - Added the Communications console lane for template creation, scoped
    broadcasts, recipient review, read-receipt updates, and preference
    management.
  - Verification: `uv run ruff check .`, `uv run pytest`, PostgreSQL
    `alembic upgrade head`, PostgreSQL `alembic downgrade 5ae823a88e0f`,
    PostgreSQL `alembic upgrade head`, `pnpm --filter @afrolete/frontend
    typecheck`, `pnpm --filter @afrolete/frontend build`, production
    Playwright screenshot at
    `/private/tmp/afrolete-communications-console-v2.png`.

## Implementation Slices

| Slice | Status | Evidence | Notes |
| --- | --- | --- | --- |
| 000 - Fresh V2 repository | Complete | Commit `d723d61`; commit `0affab9` | Repo initialized, README charter pushed. |
| 001 - Executable SaaS foundation | Complete | Slice 001 foundation commit | Backend/frontend/infra starter code added and verified. |
| 002 - Identity, tenant, and authorization vertical | Partial | Backend tests 22/22 plus SpiceDB adapter tests | Tenant graph, authz boundary, Keycloak bearer-token validation, user provisioning, SpiceDB adapter, organization APIs, team APIs, and committee APIs implemented; live service smoke tests and frontend auth flows remain. |
| 003 - Database migration baseline | Complete | Alembic upgrade/downgrade; backend tests 11/11 | Baseline revision captures the current schema; production execution against `db.lindela.io` remains a deployment task. |
| 004 - Safeguarding, consent, and tenant branding | Partial | Local PostgreSQL migration verified; backend tests 14/14 | Backend model/API support for guardians, consent requests, consent capture channels, minor event clearance, and branded organization sites. |
| 005 - Event scheduling and attendance | Partial | Backend tests 16/16 | Event APIs, roster invitation seeding, attendance recording/listing, and consent-aware check-in implemented; frontend event workflows remain. |
| 006 - Keycloak authentication | Partial | Backend tests 22/22 | Keycloak JWT validation and user provisioning are implemented behind runtime mode; frontend sign-in and live realm smoke test remain. |
| 007 - SpiceDB authorization adapter | Partial | Adapter tests 4/4 | Official Python gRPC client wired behind runtime mode; live schema/write/check smoke test remains. |
| 008 - Operational SaaS console | Partial | Frontend typecheck/build; desktop/mobile screenshots | Console now drives tenant, team, roster, event, attendance, guardian consent, and clearance workflows in local mode; production Keycloak session UX remains. |
| 009 - AI agent operations | Partial | Backend tests 29/29; frontend build | Agents can be created, permissioned, assigned to scopes, queued for work, and reviewed from the console; real model execution and AI governance dashboards remain. |
| 010 - Athlete performance metrics and assessments | Partial | Backend tests 31/31; PostgreSQL migration upgrade/downgrade; frontend build | Metric definitions, observations, ALS-style assessments, summaries, and console recording flows are implemented; automated video/audio/wearable ingestion remains. |
| 011 - Training and coaching plans | Partial | Backend tests 34/34; PostgreSQL migration upgrade/downgrade; frontend build; Playwright screenshot | Drill library, scoped plans, weekly plan blocks, session load planning, and console workflows are implemented; automatic AI plan generation, readiness check-ins, and post-session feedback loops remain. |
| 012 - Competition management foundation | Partial | Backend tests 36/36; PostgreSQL migration upgrade/downgrade; frontend build; Playwright screenshot | Competition records, team registration, fixtures, official assignments, match events, result confirmation, computed standings, and console workflows are implemented; automated fixture generation, bracket visualization, conflict optimization, ticketing, and broadcast operations remain. |
| 013 - Communications and notifications | Partial | Backend tests 39/39; PostgreSQL migration upgrade/downgrade; frontend build; Playwright screenshot | Templates, scoped broadcasts, recipient expansion, delivery/read audit records, preferences, quiet hours, emergency override, guardian copy for minors, and console workflows are implemented; live transport adapters, digest jobs, and parent inbox remain. |

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
| Performance metrics and assessments | partial | Metric definitions, observations with provenance/confidence, ALS-style assessments, summaries, and console workflows are implemented. |
| AI-assisted ingestion and analysis | partial | Agent identity, assignment, task queue, task review, and console workflows are implemented; real AI execution pipelines and model governance remain. |
| Training and coaching plans | partial | Drill library, scoped plans, weekly plan blocks, session load formula, and console workflows are implemented; automatic AI generation/readiness/feedback loops remain. |
| Competition, fixtures, officials, tournaments | partial | Competition records, participant registration, fixtures/results, officials, match events, standings, and console workflows are implemented; automated fixture generation, bracket visualization, advanced conflict resolution, ticketing, and broadcast operations remain. |
| Communications and notifications | partial | Templates, scoped broadcasts, recipient expansion, delivery/read audit records, notification preferences, quiet-hours controls, emergency override, guardian copy for minors, and console workflows are implemented; live email/SMS/WhatsApp/push adapters remain. |
| Consent, safeguarding, compliance, incidents | partial | Guardian relationships, consent requests, one-use web links, SMS/WhatsApp/Telegram/email/manual consent capture, and minor event clearance are implemented. |
| Equipment, facilities, assets | not-started | Future slice. |
| Finance, sponsorship, fundraising, ticketing | not-started | Future slice. |
| Reports and intelligence | not-started | Future slice. |
| Integrations and webhooks | foundation | Keycloak OIDC bearer-token validation and SpiceDB gRPC authorization adapter are implemented; other integrations remain future slices. |
| SaaS billing/subscriptions | not-started | Future slice. |
| Beautiful operational UI/UX | partial | First screen is now an operational console with responsive tenant, roster, event, competition, communications, attendance, performance, training, agent, and safeguarding workflows. |

## Next Actions

1. Add frontend Keycloak sign-in/session handling for `afrolete-web`.
2. Run a live SpiceDB schema/write/check smoke test with the OpenBao-managed
   SpiceDB key.
3. Add live communication transport adapters for email, SMS, WhatsApp, push,
   delivery webhooks, digest jobs, parent inbox, and AI-assisted message
   drafting.
4. Add automated fixture generation, bracket visualization, and scheduling
   conflict checks for leagues and tournaments.
5. Add automated training-plan generation from performance trends, readiness,
   upcoming competitions, and availability constraints.
6. Add automated ingestion pipelines for video, audio narration, text
   evaluation, wearable feeds, and agent-extracted metric review.
6. Add real AI execution workers, model/provider configuration, and AI
   governance telemetry.
