# AfroLete

AfroLete is an AI-assisted sports operations, athlete-development, and SaaS
management platform for clubs, schools, academies, associations, federations,
event operators, sponsors, families, and athletes.

This repository is the V2 rebuild. The retained `docs/` directory is the
product-scope source of truth. The implementation is intentionally split into a
FastAPI Python backend, a TypeScript/Next.js frontend, and PJS-oriented
infrastructure artifacts.

AfroLete is not a narrow team-management app. The intended product is a full
operating system for sport: identity, rosters, consent, safeguarding,
competitions, training, performance intelligence, communications, finance,
equipment, travel, reports, integrations, and first-class AI agents.

## Current State

The project has moved beyond scaffolding. It currently has a Docker-demoable
platform with a broad operations console, a FastAPI API surface, PostgreSQL
persistence, migrations, domain services, local/demo auth, Keycloak and SpiceDB
boundaries, a due-worker, public/family/player/sponsor pages, and many
implemented vertical slices.

The project is still not complete against the full `docs/prd.md` and
`docs/ext*.md` scope. Capability coverage is tracked in
[`docs/progress.md`](docs/progress.md). Treat that file as the current
implementation ledger, not as a replacement for the product requirements.

## Demo

Run the full local demo stack:

```bash
docker compose up --build
```

The Compose stack uses Postgres, runs migrations, seeds demo data, and starts
the unified due-worker. The backend and due-worker run as `linux/amd64` images
so the MediaPipe pose worker uses the available Linux wheel consistently on
Apple Silicon and x86_64 hosts.

Then open:

- Operations console: `http://localhost:3000`
- Backend health: `http://localhost:8000/api/v1/healthz`
- Emergency mobile console: `http://localhost:3000/emergency?slug=demo-city-fc`
- Family portal: `http://localhost:3000/family`
- Player portal: `http://localhost:3000/player`
- Sponsor portal: `http://localhost:3000/sponsors`
- Developer portal: `http://localhost:3000/developers`

The Docker demo starts:

- PostgreSQL 17
- FastAPI backend on port `8000`
- Next.js frontend on port `3000`
- Unified due-worker loop

The demo uses local trusted identity headers and memory authorization so it can
run without external PJS services. Production mode uses Keycloak, SpiceDB,
OpenBao, and the shared PJS infrastructure.

See [`docs/demo.md`](docs/demo.md) for demo user details, seed behavior, health
checks, reset notes, and walkthrough entry points.

## Vision

AfroLete exists to make high-quality sports operations and athlete development
available to organizations that would otherwise be forced to coordinate through
spreadsheets, chat groups, disconnected payment tools, and informal memory.

The platform should let each stakeholder work from a purpose-built surface:

- Administrators manage organizations, people, permissions, billing, compliance,
  communication, assets, reports, integrations, and audits.
- Coaches manage rosters, attendance, training plans, player feedback,
  assessments, workload, fixtures, and performance improvement.
- Athletes understand goals, progress, schedules, feedback, readiness, awards,
  and development paths.
- Parents and guardians handle consent, schedules, family logistics, safety
  information, communication, payments, and appeals.
- Associations and federations coordinate members, committees, competitions,
  officials, compliance, eligibility, reporting, and governance.
- Sponsors and alumni interact through visible, accountable commercial and
  community workflows.
- AI agents operate as governed, auditable members of the ecosystem rather than
  hidden helper functions.

## Product Principles

AfroLete is guided by these product standards:

1. **Operationally useful before ornamental**
   Interfaces must help real staff complete repeated work quickly and
   confidently.

2. **Beautiful but dense**
   The UI should feel modern and polished while still prioritizing information
   density, comparison, triage, and action.

3. **Backend-owned truth**
   The frontend presents and orchestrates workflows. Persistence, authorization,
   domain rules, workers, audits, and integration boundaries belong in the
   backend.

4. **Tenant boundaries everywhere**
   Organization boundaries are security boundaries, reporting boundaries, and
   billing boundaries.

5. **AI is governed**
   AI outputs need identity, provenance, policy checks, review paths, appeals,
   and audit records.

6. **Minors and safety are first-class**
   Guardian consent, safeguarding, incident management, emergency response, and
   medical clearance cannot be bolt-ons.

7. **Works in real deployment environments**
   The platform must tolerate intermittent connectivity, low-bandwidth
   contexts, local provider differences, and shared infrastructure constraints.

## Product Scope

The full product scope comes from:

- [`docs/prd.md`](docs/prd.md): core product requirements.
- [`docs/ext.md`](docs/ext.md): missing and underdeveloped feature analysis.
- [`docs/ext_1.md`](docs/ext_1.md) through [`docs/ext_12.md`](docs/ext_12.md):
  extended product, deployment, AI, UX, marketplace, localization, and ethics
  scope.
- [`docs/architecture/`](docs/architecture): architecture notes.
- [`docs/adr/`](docs/adr): architecture decision records.
- [`docs/progress.md`](docs/progress.md): implementation progress and coverage.

Major capability areas include:

- Multi-tenant organizations, clubs, schools, academies, associations,
  federations, committees, programs, seasons, teams, squads, and groups.
- Polymorphic membership: associations can contain other associations,
  organizations, teams, and individuals; clubs and schools can own many teams
  and also be members of associations or other organizations.
- Local, regional, national, and special-interest associations with committees,
  leaders, members, officials, and reporting obligations.
- Team sports and individual sports, including captains, vice captains,
  starters, bench players, substitutes, reserves, individual athletes, coaches,
  managers, medics, analysts, and team committees.
- Person identity, app users, athlete profiles, guardians, emergency contacts,
  medical visibility, membership history, and lifecycle tracking.
- Events, training sessions, matches, tournaments, leagues, fixtures,
  attendance, RSVPs, venue logistics, transport, weather, risk, and scheduling.
- Consent, safeguarding, minor participation clearance, family portals,
  incident management, background checks, compliance credentials, medical
  clearance, regulatory packages, and emergency action plans.
- Performance metric definitions, observations, assessments, ALS-style scores,
  goals, awards, trend analysis, benchmarks, forecasts, injury-risk signals,
  wearable data, stored video, MediaPipe/OpenCV pose extraction workers,
  provider-neutral pose landmark samples, tenant-managed movement reference
  profiles, pose/gait benchmarking, AI video coaching analysis, slow-motion
  review, human annotations, and athlete dashboards.
- Training drills, plans, sessions, readiness checks, feedback, workload
  management, schedule exports, and AI-assisted plan generation.
- Competition management, standings, officials, fixture generation, brackets,
  broadcasts, ticketing, conflict detection, and advancement flows.
- Communications: templates, scoped broadcasts, inboxes, preferences, quiet
  hours, urgent escalation, digests, provider callbacks, family onboarding, and
  multi-channel delivery.
- Equipment, facilities, maintenance, bookings, RFID/QR scanning, files, object
  storage, procurement, supplier orders, leases, utilization, and emergency
  response.
- Travel and logistics: manifests, offline links, consent reminders, trip fees,
  hosted payments, approvals, GPS tracking, geofences, expenses, payouts,
  carpooling, driver ratings, backup drivers, and route-risk guidance.
- Finance, sponsorship, fundraising, ticketing, invoices, payments, refunds,
  tax, accounting, payouts, sponsor portals, and public support showcases.
- Reports and intelligence: report definitions, generated reports, scheduled
  delivery, artifact storage, signed links, chart-ready summaries, deterministic
  AI insights, and export jobs.
- Integrations and developer platform: API keys, OAuth-style consent grants,
  SDK routes for roster, events, attendance, performance, training, and
  governed AI-agent tasks, marketplace listings, webhooks, replay, retry
  workers, database or Redis-backed quotas, and integration catalogs.
- SaaS billing and subscriptions: plans, tenant subscriptions, lifecycle
  actions, entitlements, enforcement, metering, recurring invoices, dunning,
  late fees, payment retries, checkout links, tax, provider webhooks, and
  billing summaries.
- Offline/PWA operation: installable frontend shell, service worker caching,
  encrypted travel-manifest cache, signed offline artifacts, offline mutation
  outbox, and replay controls.

## AI Agents

AI agents are first-class domain actors in AfroLete.

They are expected to have:

- Identity.
- Ownership and assignment.
- Explicit scopes.
- Permission checks.
- Task queues.
- SDK task queue access for trusted tenant integrations.
- Execution mode.
- Human review.
- Reviewer assignment, due dates, priority, and queue summaries.
- Review workload trends and manager-facing queue balancing.
- Cohort-level outcome comparisons for completion, failure, review, approval,
  and appeal rates.
- Policy enforcement.
- Audit trails.
- Run ledgers.
- Evidence artifacts.
- Appeals and governance reporting.

AI agents are not allowed to silently mutate important user-facing or
safety-critical state without policy, provenance, and review controls. The
platform supports deterministic/local execution for demo and test use, plus
provider/webhook boundaries for deployed execution.

The initial coaching workflow accepts athletics video evidence, creates
pending-review movement metrics, drafts a coach-verifiable assessment, and
returns concrete correction cues. Future computer-vision providers can replace
or enrich the deterministic extractor without changing the human-review
contract.

Video review now includes stored performance clips, slow-motion playback rates,
timestamped human annotations, provider-neutral pose/keypoint sample ingestion,
and a MediaPipe/OpenCV worker that decodes stored clips, samples frames,
extracts normalized body landmarks, and writes those landmarks through the same
pose-sample contract used by external providers. The worker also has an
endpoint-ingest mode that posts extracted keypoint batches to
`/api/v1/performance/videos/{video_asset_id}/pose-samples`, so containerized or
remote workers exercise the same API boundary as third-party pose providers.
Tenant-managed reference
profiles for world-class or optimal movement models then drive pose/gait
benchmark comparisons and optimal movement projections. The output remains
advisory and pending review until a coach accepts it.

## Architecture

AfroLete V2 is organized as a service split:

```text
backend/     FastAPI backend, domain services, migrations, workers, tests
frontend/    Next.js TypeScript UI, public routes, API client, PWA shell
infra/       PJS deployment config for Postgres, Keycloak, SpiceDB, OpenBao,
             Redis, Temporal, MinIO, systemd, and deploy runbooks
docs/        Product requirements, extensions, architecture notes, ADRs,
             demo notes, and progress log
scripts/     Project automation entrypoints
tools/       Development and migration utilities
tests/       Cross-service and end-to-end test surfaces
```

### Backend

The backend owns:

- HTTP API contracts and OpenAPI schema.
- Authentication and identity bridging.
- Authorization checks and relationship writes.
- PostgreSQL persistence through SQLAlchemy.
- Alembic migrations.
- Domain services and business rules.
- Background workers and scheduler-ready lanes.
- External provider boundaries.
- File and object access.
- Audit records, ledgers, and replay protection.

The backend must keep business rules out of route handlers where practical.
Routes should validate, authenticate, authorize, call services, and return typed
schemas.

### Frontend

The frontend owns:

- Operational workflows and UI composition.
- Public routes for consent, family, player, sponsor, developer, emergency, and
  branded organization surfaces.
- API calls through typed client boundaries.
- Local/demo identity headers in local mode.
- PWA shell behavior, connectivity indication, and offline replay UX.

The frontend must not connect directly to Postgres, Redis, SpiceDB, Temporal,
or MinIO. It must not duplicate backend source-of-truth business rules.

### Workers

The backend includes a unified due-worker that can run scheduler-ready lanes for
agent tasks, developer webhooks, billing, communications, travel reminders,
emergency escalation, performance achievements, forecast validation, review
escalation, injury-risk alerts, object-storage lifecycle cleanup, performance
video pose extraction, wearable pulls, and compliance reconciliation. The video
pose lane can run in direct in-process mode or endpoint-ingest mode, where the
worker decodes stored media and posts normalized keypoints back through the
existing pose-sample API.

Object storage can run in local mode for demos or S3-compatible mode for MinIO.
The same storage adapter supports retention policy enforcement: local mode
prunes stale artifacts from configured storage roots, while S3 mode writes a
bucket lifecycle configuration for the configured prefixes.

The local Docker demo runs this worker continuously. Production deployment can
run it through systemd, cron, Temporal activities, or container jobs depending
on the final PJS deployment path.

## Infrastructure Targets

Production targets the shared PJS environment:

| Capability | Target |
| --- | --- |
| Database | PostgreSQL database/user `afrolete` on `db.lindela.io:5432` |
| Authentication | Keycloak shared `lindela` realm |
| Authorization | SpiceDB relationship and permission service |
| Secrets | OpenBao rendered into runtime environment files |
| Cache and queues | Redis on shared PJS infrastructure |
| Durable workflows | Temporal namespace `afrolete` |
| Object storage | MinIO/S3-compatible storage with lifecycle retention policy |
| Deployment | Systemd-managed services and PJS deploy scripts |

Real secrets must never be committed. Runtime credentials should come from
OpenBao, local ignored `.env` files, or deployment-managed environment files.

## Authentication And Authorization

AfroLete separates identity from authorization:

```text
Keycloak sub -> app_users.keycloak_sub -> app_users.id -> SpiceDB user:<id>
```

- Keycloak verifies who the user is.
- AfroLete maps that identity to application users and person records.
- SpiceDB decides whether the user can perform an action on a resource.
- Local/demo mode uses trusted `X-Afrolete-*` headers and memory authorization.

Do not use Keycloak roles as the only authorization layer. Realm/client roles
may express broad capability, but resource-level permission belongs in SpiceDB.

## Data Standards

Important domain standards:

- Use UUIDs for durable domain identity.
- Keep person identity separate from tenant membership.
- Keep athlete profiles separate from roster entries.
- Treat organization boundaries as tenant boundaries.
- Persist audit timestamps on domain records.
- Use Alembic for schema changes.
- Keep SpiceDB relationships synchronized with source-of-truth domain writes.
- Record source, confidence, reviewer, and timestamps for AI-assisted data.
- Preserve raw observations separately from derived analytics where provenance
  matters.
- Add idempotency and replay protection around provider callbacks, workers, and
  offline replay paths.
- Prefer explicit state machines over ambiguous string notes for operational
  workflows.

## Development Setup

### Prerequisites

- Docker and Docker Compose for the full demo.
- Python with `uv` for backend development.
- Node.js and `pnpm` for frontend development.
- PostgreSQL for local non-Docker backend runs.

### Backend

```bash
cd backend
uv sync
createdb afrolete
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Default local database shape:

```text
postgresql:///afrolete
```

The app normalizes PostgreSQL URLs to the async driver it needs at runtime.
Tests override persistence for fast isolated runs.

### Frontend

```bash
cd frontend
pnpm install
pnpm run dev
```

Frontend package versions are pinned. The project currently uses:

- Next.js `16.2.6`
- React `19.2.6`
- TypeScript `5.9.3`

This pinning is intentional. Do not downgrade framework packages casually.

### Docker

```bash
docker compose up --build -d
docker compose ps
curl -s http://localhost:8000/api/v1/healthz
curl -s -I http://localhost:3000
```

Stop the stack:

```bash
docker compose down
```

Reset Docker database state:

```bash
docker compose down -v
docker compose up --build -d
```

## Verification Commands

Use the smallest verification set that proves the changed behavior, then widen
when the blast radius requires it.

Backend:

```bash
cd backend
uv run ruff check app tests
uv run pytest
uv run alembic heads
```

Frontend:

```bash
cd frontend
pnpm run typecheck
pnpm run build
```

Docker:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

For UI-heavy changes, use browser screenshots or Playwright checks before
claiming completion.

## Environment Modes

Local/demo defaults:

- `AFROLETE_AUTH_MODE=local`
- `AFROLETE_AUTHZ_MODE=memory`
- `AFROLETE_COMMUNICATION_DELIVERY_MODE=record_only`
- `AFROLETE_AGENT_EXECUTION_MODE=deterministic`
- `AFROLETE_PERFORMANCE_FORECAST_MODE=deterministic`

Production-like deployment should use:

- `AFROLETE_AUTH_MODE=keycloak`
- `AFROLETE_AUTHZ_MODE=spicedb`
- OpenBao-backed secrets.
- PostgreSQL on `db.lindela.io`.
- Shared Redis, Temporal, and MinIO services.

## UI And UX Standards

AfroLete is an operational SaaS. The UI should feel like a high-quality command
surface, not a marketing page.

Standards:

- First screen should be useful, not a landing-page hero.
- Prioritize dense but readable operational layouts.
- Use cards for repeated items, modals, and framed tools, not every section.
- Avoid nested decorative card stacks.
- Keep buttons clear and stable.
- Ensure text fits on mobile and desktop.
- Surface status, blockers, risks, counts, and next actions.
- Make family/player/sponsor/emergency surfaces simpler and more focused than
  the operator console.
- Make offline and provider-readiness state visible before operators rely on
  unavailable infrastructure.

## Offline And Low-Bandwidth Strategy

Offline support is required by the target deployment context.

Current implemented pieces include:

- Installable web manifest.
- Service worker app-shell caching.
- Connectivity status in the operations console.
- Offline mutation outbox for selected field-critical writes.
- Manual and automatic replay of queued operations.
- Encrypted travel-manifest offline cache.
- Signed offline travel-manifest artifacts.

Future offline work should move toward a general IndexedDB-backed data layer,
conflict resolution, sync receipts, device handoff, provider prefetch, and
browser QA across mobile field conditions.

## Commit And Progress Discipline

This repository uses small, verified slices.

- Update [`docs/progress.md`](docs/progress.md) when a meaningful capability is
  added or completed.
- Commit and push completed verified work regularly.
- Use the Lore commit protocol from `AGENTS.md`.
- Keep commits honest about `Tested:` and `Not-tested:` evidence.
- Do not rewrite product docs to hide incomplete scope.

## Security And Privacy Standards

- No real secrets in git.
- Validate bearer tokens in deployed mode.
- Fail closed on authorization errors.
- Use HMAC signatures and replay protection for inbound provider callbacks.
- Use signed short-lived links for sensitive artifacts.
- Treat medical, safeguarding, guardian, minor, and AI-governance data as
  sensitive.
- Keep audit logs and reviewer trails for safety-critical and AI-assisted
  decisions.
- Add provider-specific adapters behind provider-neutral service boundaries.

## Documentation Map

Use these files first:

- [`docs/prd.md`](docs/prd.md): full core product specification.
- [`docs/ext.md`](docs/ext.md): major missing/underdeveloped scope.
- [`docs/ext_3.md`](docs/ext_3.md): offline, low-bandwidth, PWA, and
  deployment resilience.
- [`docs/ext_4.md`](docs/ext_4.md): advanced AI, scouting, injury, video, and
  highlight intelligence.
- [`docs/ext_8.md`](docs/ext_8.md): competition and event enhancements.
- [`docs/ext_9.md`](docs/ext_9.md): localization, local payments, government,
  federation, and regional adaptation.
- [`docs/ext_10.md`](docs/ext_10.md): marketplace and platform scale.
- [`docs/ext_11.md`](docs/ext_11.md): onboarding, family UX, AR, and voice.
- [`docs/ext_12.md`](docs/ext_12.md): ethical AI, transparency, sovereignty,
  and governance.
- [`docs/progress.md`](docs/progress.md): current implementation ledger.
- [`docs/demo.md`](docs/demo.md): local demo runbook.
- [`docs/architecture/v2-platform.md`](docs/architecture/v2-platform.md):
  platform architecture notes.

## Working Agreement

The end state is a production-grade SaaS that is ergonomic, functional,
capable, and beautiful. The current implementation should keep moving toward
the complete documented scope rather than narrowing the ambition to what is
already easiest to test.

When in doubt:

1. Read the docs.
2. Inspect current code.
3. Implement a coherent vertical slice.
4. Verify the behavior.
5. Update progress.
6. Commit and push.
