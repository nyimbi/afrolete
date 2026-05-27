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
- Implemented slice 014 equipment, facilities, and asset operations:
  - Added facility profiles for fields, courts, stadiums, gyms, pools,
    clubhouses, storage, capacity, surface, amenities, insurance, maintenance
    budgets, conditions, and inspection dates.
  - Added equipment inventory with category/subcategory, brand/model, QR/RFID
    tag codes, serial numbers, total and available quantity, condition,
    storage location, reorder thresholds, value, depreciation, warranty, audit,
    and photo metadata.
  - Added equipment checkout and return workflows that decrement and restore
    availability, capture borrower/team/event context, due dates, conditions,
    damage reports, and late fees.
  - Added facility bookings with overlap rejection, requester details, event and
    team linkage, attendee counts, rate/deposit, insurance certificates,
    requirements, and access codes.
  - Added maintenance work orders with facility/equipment linkage, assignment,
    priority, due dates, vendor, estimated/actual cost, safety flag, compliance
    reference, and completion tracking.
  - Added an asset summary endpoint for facilities, inventory counts, stock
    alerts, open/overdue checkouts, open/safety work orders, upcoming bookings,
    booked hours, and projected revenue.
  - Added the Assets console lane for facility creation, booking, inventory
    creation, checkout/return, maintenance work orders, and readiness checks.
  - Verification: `uv run ruff check .`, `uv run pytest`, PostgreSQL
    `alembic upgrade head`, PostgreSQL `alembic downgrade 001fdd0cead7`,
    PostgreSQL `alembic upgrade head`, `pnpm --filter @afrolete/frontend
    typecheck`, `pnpm --filter @afrolete/frontend build`, production
    Playwright screenshot at
    `/private/tmp/afrolete-assets-console-viewport.png`.
- Implemented slice 015 commercial operations fast surface:
  - Added sponsors with industry, contacts, websites, brand assets, and notes.
  - Added sponsorship agreements with event linkage, tiers, value, currency,
    dates, deliverables, activation notes, ROI notes, and lifecycle status.
  - Added fundraising campaigns and donations with goals, raised totals,
    donor records, external references, messages, and automatic campaign
    completion when the goal is met.
  - Added ticket products, paid ticket orders, issued QR-token tickets, and
    ticket check-in with gate and timestamp.
  - Added finance invoices and payments with partial/paid status tracking.
  - Added a commercial summary endpoint for sponsorship value, fundraising
    goals/raised totals, ticket revenue, invoice outstanding, sponsors,
    campaigns, tickets sold, and tickets checked in.
  - Added the Commerce console lane for sponsorship activation, fundraising
    donation capture, ticket sale/check-in, invoice/payment capture, and
    commercial summary review.
  - Verification: `uv run ruff check .`, PostgreSQL `alembic upgrade head`,
    `pnpm --filter @afrolete/frontend typecheck`. Full test/build/screenshot
    verification deferred by user instruction during low-battery fast delivery.
- Implemented slice 016 reporting and intelligence fast surface:
  - Added report definitions across performance, administrative, operational,
    financial, compliance, and intelligence categories.
  - Added generated report runs with team, athlete, event, and competition
    scope, period parameters, online/PDF/Excel/CSV/API output targets, summary,
    findings, recommendations, shared tokens, and expiry metadata.
  - Added scheduled report delivery with daily/weekly/monthly/quarterly/on
    trigger frequency, delivery channels, recipients, next-run, and last-run
    tracking.
  - Added intelligence insights with AI-agent linkage, athlete/team/event scope,
    severity, confidence, evidence, recommendations, model name, review status,
    and human reviewer tracking.
  - Added predictive risk scores with model name, score, risk band, drivers,
    recommendations, and validity date.
  - Added report export jobs for PDF/Excel/CSV/API destinations and webhook
    delivery status.
  - Added a reporting summary endpoint and Reports console lane for generating
    reports, scheduling delivery, exporting artifacts, creating insights,
    recording risk scores, and actioning insights.
  - Verification: `uv run ruff check .`, PostgreSQL `alembic upgrade head`,
    `pnpm --filter @afrolete/frontend typecheck`. Full test/build/screenshot
    verification deferred by user instruction during low-battery fast delivery.
- Implemented slice 017 SaaS billing and subscription fast surface:
  - Added SaaS billing plans with code, tier name, pricing, billing cycle,
    included athletes, teams, AI-agent tasks, storage, per-athlete pricing,
    per-agent-task pricing, feature text, and status.
  - Added tenant subscriptions with organization linkage, plan, billing cycle,
    active/trial/past-due/cancelled states, period dates, trial and next billing
    dates, purchased seats, negotiated pricing, discount codes, external
    customer/subscription IDs, and cancellation flags.
  - Added usage meters and usage records for athletes, teams, agent tasks,
    reports, storage, and messages with included quantities, overage pricing,
    aggregation, sources, and external references.
  - Added SaaS invoices and payments with line-item summaries, subtotal, tax,
    discount, total, amount paid, status, due dates, external IDs, provider, and
    collection metadata.
  - Added billing entitlements for feature limits, usage, reset dates, and
    status.
  - Added a billing summary endpoint for active subscriptions, plans, usage
    meters, usage records, open invoices, monthly recurring revenue,
    outstanding invoice value, and entitlements.
  - Added the Billing console lane for plan/subscription creation, usage
    metering, invoice/payment capture, and entitlement assignment.
  - Verification: `uv run ruff check .`, PostgreSQL `alembic upgrade head`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`. Full
    test/build/screenshot verification deferred by user instruction during
    low-battery fast delivery.
- Implemented slice 018 frontend Keycloak session handling:
  - Added frontend runtime configuration for `NEXT_PUBLIC_AFROLETE_AUTH_MODE`,
    Keycloak issuer, web client ID, and OIDC scopes.
  - Added a no-new-dependency browser OIDC authorization-code + PKCE flow for
    the `afrolete-web` public client, including state verification, token
    exchange, stored session expiry, claim extraction, and logout URL support.
  - API calls now automatically attach a stored Keycloak bearer token while
    preserving local-mode AfroLete identity headers for development.
  - The operations console now exposes Keycloak sign-in/sign-out controls,
    displays the active browser session, derives operator identity from token
    claims, and waits for a session before synchronizing protected data in
    Keycloak mode.
  - Verification: `pnpm --filter @afrolete/frontend typecheck`,
    `git diff --check`. Live Keycloak realm/browser redirect, full build, and
    screenshot verification deferred by user instruction during low-battery
    fast delivery.
- Implemented slice 019 communication delivery adapter fast surface:
  - Added backend configuration for record-only vs webhook communication
    delivery, channel-specific webhook URLs, a shared delivery webhook key, and
    delivery timeout controls.
  - Added a dispatch service and API endpoint that sends email, SMS, WhatsApp,
    Telegram, and push payloads to configured HTTP adapters while preserving
    queued status when no transport is configured.
  - In-app messages are marked delivered immediately, suppressed recipients
    remain suppressed, and failed webhook responses are captured on recipient
    failure reasons.
  - Added a provider callback endpoint for delivery/read/failure events guarded
    by `AFROLETE_COMMUNICATION_WEBHOOK_KEY` outside local mode.
  - Added a console dispatch action that refreshes recipient delivery state and
    surfaces sent, failed, and queued counts.
  - Verification: `uv run ruff check .`,
    `uv run pytest tests/unit/test_communications.py -q` (4/4),
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`. Full
    suite/build/screenshot verification deferred by user instruction during
    low-battery fast delivery.
- Implemented slice 020 agent task execution fast surface:
  - Added backend configuration for deterministic local agent execution,
    optional provider-neutral webhook execution, webhook keys, default model
    policy, and execution timeouts.
  - Added an agent task execution endpoint that moves queued tasks through a
    real run boundary, generates deterministic review-ready output by default,
    or posts provider-neutral payloads to an external agent worker when
    configured.
  - Webhook execution captures output references, review notes, returned
    statuses, HTTP failures, and transport errors on the task record.
  - The console Run control now invokes the execution endpoint and displays
    output references and review notes instead of only manually setting a task
    to running.
  - Verification: `uv run ruff check .`,
    `uv run pytest tests/unit/test_agents.py -q` (2/2),
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`. Full
    suite/build/screenshot and live provider execution deferred by user
    instruction during low-battery fast delivery.
- Implemented slice 021 communication inbox, digests, and AI drafting:
  - Added a person-scoped communications inbox API for athletes, guardians,
    parents, and members, with self-access for the recipient and manager access
    for organization operators.
  - Added digest generation that collects unread inbox items, chooses an
    in-app/email/SMS channel from notification preferences, creates a digest
    message, and records a recipient delivery state.
  - Added deterministic AI-assisted message drafting for selected organization,
    team, event, or person scopes, including tone, audience, guardian context,
    model attribution, and mandatory human review.
  - Extended the operations console with Draft, Digest, inbox review, digest
    summary, and read-action controls so communication work is not API-only.
  - Verification: `uv run ruff check .`,
    `uv run pytest tests/unit/test_communications.py -q` (5/5),
    `uv run pytest` (44/44), `pnpm --filter @afrolete/frontend typecheck`,
    `pnpm --filter @afrolete/frontend build`, `git diff --check`.
- Implemented slice 022 asset procurement, scan, supplier, lease, and
  utilization intelligence:
  - Added RFID/barcode-style equipment scan lookup by tag code or serial number
    with organization scoping and manager authorization.
  - Added equipment photo metadata updates for audit/photo capture workflows.
  - Added procurement recommendations from reorder points, minimum stock,
    available quantity, unit value, and supplier hints.
  - Added supplier scorecards from maintenance vendor work orders, completion
    rates, safety work, estimated cost, and actual cost variance.
  - Added lease quote estimates for equipment planning using replacement value,
    depreciation, quantity, and term.
  - Added asset utilization recommendations for low stock, unused stock,
    overdue checkouts, and open safety work orders.
  - Extended the operations console with Scan, Photo, Lease, procurement,
    supplier, and utilization controls.
  - Verification: `uv run ruff check .`,
    `uv run pytest tests/unit/test_assets.py -q` (4/4),
    `uv run pytest` (45/45), `pnpm --filter @afrolete/frontend typecheck`,
    `pnpm --filter @afrolete/frontend build`, `git diff --check`.

## Implementation Slices

| Slice | Status | Evidence | Notes |
| --- | --- | --- | --- |
| 000 - Fresh V2 repository | Complete | Commit `d723d61`; commit `0affab9` | Repo initialized, README charter pushed. |
| 001 - Executable SaaS foundation | Complete | Slice 001 foundation commit | Backend/frontend/infra starter code added and verified. |
| 002 - Identity, tenant, and authorization vertical | Partial | Backend tests 22/22 plus SpiceDB adapter tests; frontend typecheck | Tenant graph, authz boundary, Keycloak bearer-token validation, frontend PKCE session handling, user provisioning, SpiceDB adapter, organization APIs, team APIs, and committee APIs implemented; live service smoke tests remain. |
| 003 - Database migration baseline | Complete | Alembic upgrade/downgrade; backend tests 11/11 | Baseline revision captures the current schema; production execution against `db.lindela.io` remains a deployment task. |
| 004 - Safeguarding, consent, and tenant branding | Partial | Local PostgreSQL migration verified; backend tests 14/14 | Backend model/API support for guardians, consent requests, consent capture channels, minor event clearance, and branded organization sites. |
| 005 - Event scheduling and attendance | Partial | Backend tests 16/16 | Event APIs, roster invitation seeding, attendance recording/listing, and consent-aware check-in implemented; frontend event workflows remain. |
| 006 - Keycloak authentication | Partial | Backend tests 22/22; frontend typecheck | Keycloak JWT validation, frontend PKCE sign-in/session handling, bearer API calls, logout wiring, and user provisioning are implemented behind runtime mode; live realm smoke test remains. |
| 007 - SpiceDB authorization adapter | Partial | Adapter tests 4/4 | Official Python gRPC client wired behind runtime mode; live schema/write/check smoke test remains. |
| 008 - Operational SaaS console | Partial | Frontend typecheck/build; desktop/mobile screenshots | Console now drives tenant, team, roster, event, attendance, guardian consent, and clearance workflows, with local-mode identity and production Keycloak session controls; full live deployed UX smoke remains. |
| 009 - AI agent operations | Partial | Backend tests 29/29; frontend build | Agents can be created, permissioned, assigned to scopes, queued for work, and reviewed from the console; real model execution and AI governance dashboards remain. |
| 010 - Athlete performance metrics and assessments | Partial | Backend tests 31/31; PostgreSQL migration upgrade/downgrade; frontend build | Metric definitions, observations, ALS-style assessments, summaries, and console recording flows are implemented; automated video/audio/wearable ingestion remains. |
| 011 - Training and coaching plans | Partial | Backend tests 34/34; PostgreSQL migration upgrade/downgrade; frontend build; Playwright screenshot | Drill library, scoped plans, weekly plan blocks, session load planning, and console workflows are implemented; automatic AI plan generation, readiness check-ins, and post-session feedback loops remain. |
| 012 - Competition management foundation | Partial | Backend tests 36/36; PostgreSQL migration upgrade/downgrade; frontend build; Playwright screenshot | Competition records, team registration, fixtures, official assignments, match events, result confirmation, computed standings, and console workflows are implemented; automated fixture generation, bracket visualization, conflict optimization, ticketing, and broadcast operations remain. |
| 013 - Communications and notifications | Partial | Backend tests 39/39; PostgreSQL migration upgrade/downgrade; frontend build; Playwright screenshot | Templates, scoped broadcasts, recipient expansion, delivery/read audit records, preferences, quiet hours, emergency override, guardian copy for minors, and console workflows are implemented; later slices add delivery adapters, inbox, digests, and drafting. |
| 014 - Equipment, facilities, and asset operations | Partial | Backend tests 42/42; PostgreSQL migration upgrade/downgrade; frontend build; Playwright screenshot | Facility profiles, equipment inventory, checkout/return, maintenance work orders, facility bookings, overlap rejection, asset summary metrics, and console workflows are implemented; procurement, supplier scoring, RFID scanning, photo uploads, lease billing, and AI optimization remain. |
| 015 - Commercial operations fast surface | Partial | Backend ruff; PostgreSQL migration upgrade; frontend typecheck | Sponsors, sponsorship agreements, fundraising campaigns, donations, ticket products/orders/QR tickets/check-in, invoices, payments, commercial summary, and console workflows are implemented; payment gateway settlement, refunds, tax, accounting exports, sponsorship dashboards, and full verification remain. |
| 016 - Reporting and intelligence fast surface | Partial | Backend ruff; PostgreSQL migration upgrade; frontend typecheck | Report definitions, generated reports, scheduled delivery, intelligence insights, predictive risk scores, export jobs, reporting summary, and console workflows are implemented; real AI model execution, rendered PDF/Excel generation, charts, benchmark models, and full verification remain. |
| 017 - SaaS billing and subscription fast surface | Partial | Backend ruff; PostgreSQL migration upgrade; frontend typecheck | Billing plans, tenant subscriptions, usage meters/records, SaaS invoices/payments, entitlements, billing summary, and console workflows are implemented; Stripe/processor webhooks, dunning automation, tax localization, plan-change proration, and full verification remain. |
| 018 - Frontend Keycloak session handling | Partial | Frontend typecheck; diff check | Browser OIDC authorization-code + PKCE login, bearer-token API attachment, session display, logout URL wiring, and local-mode fallback are implemented; live Keycloak redirect and deployed smoke test remain. |
| 019 - Communication delivery adapters | Partial | Backend ruff; communications tests 4/4; frontend typecheck | Configurable HTTP webhook dispatch, channel-specific adapter URLs, secured provider delivery callbacks, in-app delivery handling, failure capture, and console dispatch are implemented; real provider credentials and background delivery hardening remain. |
| 020 - Agent task execution fast surface | Partial | Backend ruff; agent tests 2/2; frontend typecheck | Agent tasks can now execute through a deterministic local executor or provider-neutral webhook boundary, produce output refs/review notes, and update console task state; live provider workers, model credential vaulting, run history tables, and governance telemetry remain. |
| 021 - Communication inbox, digests, and AI drafting | Partial | Backend tests 44/44; frontend typecheck/build | Person inbox, manager/self access, digest generation, notification-preference channel selection, deterministic AI-assisted drafts, console draft/digest/inbox controls, and read actions are implemented; provider-specific credentials, background digest scheduler, and full parent portal remain. |
| 022 - Asset procurement and utilization intelligence | Partial | Backend tests 45/45; frontend typecheck/build | Scan lookup, photo metadata updates, procurement recommendations, supplier scorecards, lease quotes, utilization recommendations, and console controls are implemented; supplier ordering workflows, file uploads, RFID hardware integration, and accounting lease billing remain. |

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
| AI-assisted ingestion and analysis | partial | Agent identity, assignment, task queue, deterministic/webhook task execution, task review, and console workflows are implemented; live provider workers, model credential vaulting, run history tables, and model governance remain. |
| Training and coaching plans | partial | Drill library, scoped plans, weekly plan blocks, session load formula, and console workflows are implemented; automatic AI generation/readiness/feedback loops remain. |
| Competition, fixtures, officials, tournaments | partial | Competition records, participant registration, fixtures/results, officials, match events, standings, and console workflows are implemented; automated fixture generation, bracket visualization, advanced conflict resolution, ticketing, and broadcast operations remain. |
| Communications and notifications | partial | Templates, scoped broadcasts, recipient expansion, configurable email/SMS/WhatsApp/Telegram/push webhook dispatch, delivery/read callback capture, person inbox, digest generation, AI-assisted drafts, notification preferences, quiet-hours controls, emergency override, guardian copy for minors, and console workflows are implemented; provider credentials, background digest scheduler, and full parent portal remain. |
| Consent, safeguarding, compliance, incidents | partial | Guardian relationships, consent requests, one-use web links, SMS/WhatsApp/Telegram/email/manual consent capture, and minor event clearance are implemented. |
| Equipment, facilities, assets | partial | Facility profiles, equipment inventory, checkout/return, maintenance work orders, booking overlap checks, asset readiness metrics, scan lookup, photo metadata, procurement recommendations, supplier scorecards, lease quotes, utilization recommendations, and console workflows are implemented; supplier ordering workflows, real file uploads, RFID hardware integration, and accounting lease billing remain. |
| Finance, sponsorship, fundraising, ticketing | partial | Sponsors, sponsorship agreements, fundraising campaigns, donations, ticket products/orders/QR tickets/check-in, invoices, payments, commercial summary, and console workflows are implemented; payment gateway settlement, refunds, tax, accounting exports, sponsorship dashboards, and full verification remain. |
| Reports and intelligence | partial | Report definitions, generated reports, scheduled delivery, intelligence insights, predictive risk scores, export jobs, reporting summary, and console workflows are implemented; real AI model execution, rendered PDF/Excel generation, charts, benchmark models, and full verification remain. |
| Integrations and webhooks | foundation | Keycloak OIDC bearer-token validation, frontend PKCE session handling, and SpiceDB gRPC authorization adapter are implemented; live service smoke tests and other integrations remain future slices. |
| SaaS billing/subscriptions | partial | Billing plans, tenant subscriptions, usage meters/records, SaaS invoices/payments, entitlements, billing summary, and console workflows are implemented; Stripe/processor webhooks, dunning automation, tax localization, plan-change proration, and full verification remain. |
| Beautiful operational UI/UX | partial | First screen is now an operational console with responsive tenant, roster, event, assets, commerce, reports, billing, competition, communications, attendance, performance, training, agent, and safeguarding workflows. |

## Next Actions

1. Run a live Keycloak realm redirect/token/API smoke test for `afrolete-web`
   against the deployed backend auth mode.
2. Run a live SpiceDB schema/write/check smoke test with the OpenBao-managed
   SpiceDB key.
3. Add provider-specific communication credentials, background digest scheduler,
   and full parent portal/inbox experience.
4. Add supplier ordering workflows, real file uploads, RFID hardware
   integration, and accounting lease billing for assets and facilities.
5. Add payment gateway settlement, refunds, tax handling, accounting exports,
   sponsorship dashboards, and commercial reporting verification.
6. Add rendered PDF/Excel report generation, chart visualizations, benchmark
   models, live AI-generated insights, and report verification coverage.
7. Add Stripe/payment-processor webhooks, dunning automation, tax localization,
   plan-change proration, and full billing verification coverage.
8. Add automated fixture generation, bracket visualization, and scheduling
   conflict checks for leagues and tournaments.
9. Add automated training-plan generation from performance trends, readiness,
   upcoming competitions, and availability constraints.
10. Add automated ingestion pipelines for video, audio narration, text
   evaluation, wearable feeds, and agent-extracted metric review.
11. Add live AI provider workers, credential vaulting, run history tables, and
   AI governance telemetry.
