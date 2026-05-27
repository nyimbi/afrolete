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
- Implemented slice 023 commercial finance controls:
  - Added provider-neutral tax quote estimates for invoice, ticketing, donation,
    and checkout review, including jurisdiction, tax rate, reverse-charge
    support, tax amount, and total.
  - Added payment settlement summaries across ticket revenue, invoice payments,
    and donations with provider name, fee rate, fixed fee, gross amount, fees,
    net payout, payout reference, and line count.
  - Added ticket refunds that mutate ticket status, decrement sold inventory,
    and adjust order status for partial/full refunds.
  - Added invoice refunds/credit notes that reduce amount paid and recalculate
    invoice status.
  - Added accounting export rows for invoice payments and donations with debit,
    credit, account codes, external references, basis, and target system.
  - Added sponsorship dashboard metrics for agreement count, active/contracted
    value, deliverables, activations, ROI score, and renewal recommendations.
  - Extended the operations console with Tax, Settle, Export, Refund ticket,
    Refund invoice, and sponsorship ROI cards.
  - Verification: `uv run ruff check .`,
    `uv run pytest tests/unit/test_commercial.py -q` (1/1),
    `uv run pytest` (46/46), `pnpm --filter @afrolete/frontend typecheck`,
    `pnpm --filter @afrolete/frontend build`, `git diff --check`.
- Implemented slice 024 reporting output intelligence:
  - Added report artifact rendering endpoints with selected output format,
    content type, artifact reference, checksum, body preview, and PDF/Excel
    page/sheet metadata.
  - Added report verification scoring for readiness, narrative completeness,
    share expiry, period validity, and rendered artifact presence.
  - Added chart-ready reporting summaries for throughput, insight severity,
    and predictive risk bands.
  - Added benchmark model summaries from predictive risk scores, including
    sample size, average score, high-risk counts, banding, and recommended
    follow-up.
  - Added deterministic AI-generated reporting review insights from the latest
    report/export/open-insight/risk signals.
  - Extended the operations console with Render, Verify, AI Review, chart cards,
    artifact cards, verification cards, and benchmark cards.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, and real binary PDF/Excel file generation.
- Implemented slice 025 SaaS billing operations:
  - Added localized SaaS tax quote estimates with jurisdiction rates,
    reverse-charge support, totals, and filing hints.
  - Added subscription plan-change proration quotes with remaining-period
    credits, new charges, net amount, and recommendations.
  - Added dunning notice preparation for overdue SaaS invoices with severity,
    channel, amount due, message, and next action.
  - Added provider-neutral payment webhook intake for succeeded invoice payment
    events, including invoice status mutation and payment records.
  - Extended the operations console with Tax, Prorate, Dunning, and Webhook
    controls plus result cards for tax, proration, dunning, and webhook intake.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, real Stripe/webhook signature validation,
    external dunning delivery, and jurisdiction-specific filing integrations.
- Implemented slice 026 competition automation:
  - Added deterministic round-robin fixture generation from registered
    competition participants, with configurable start time, interval, match
    spacing, venue, stage label, and double round-robin support.
  - Added bracket projections from existing fixtures or seeded participants,
    including round/stage grouping, slots, fixture links, status, and winner
    names where results exist.
  - Added schedule conflict detection for duplicate matchups, missing
    officials, team rest-window conflicts, and venue overlaps with severity and
    recommended actions.
  - Extended the operations console with Auto fixtures and Conflicts controls,
    generated-fixture summary cards, bracket cards, and conflict cards.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, and complex tournament bracket advancement.
- Implemented slice 027 AI training plan generation:
  - Added an AI-assisted training plan generation endpoint that creates a plan
    and session blocks from organization/team/athlete scope, readiness score,
    period, weekly session target, drill library, recent assessments,
    observations, and upcoming competition fixtures.
  - Added deterministic focus inference from readiness and lowest assessment
    dimension, load guidance, recovery protocol, competition tapering, and
    readiness-aware intensity progression.
  - Added generated plan response metadata with rationale, load balance,
    readiness score, next competition date, plan, and generated items.
  - Extended the operations console with AI Plan controls, readiness/session
    inputs, and generated-plan rationale cards.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, live model generation, availability
    calendars, and post-session feedback loops.
- Implemented slice 028 performance ingestion and review:
  - Added provider-neutral performance evidence ingestion for video analysis,
    audio narration, text/manual evidence, wearable feeds, official stats, and
    agent-extracted observations.
  - Added deterministic metric value extraction, source-specific confidence,
    extractor naming, evidence references, pending-review observations, and
    ingestion summaries without adding new storage tables.
  - Added human review workflow for ingested observations, including value
    correction, verification status promotion/rejection, and review notes.
  - Extended the operations console with evidence reference/text fields,
    Ingest and Review controls, ingestion summary cards, and selectable
    observation review cards.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, real video/audio/wearable provider parsing,
    and model-backed extraction accuracy.
- Implemented slice 029 AI agent governance telemetry:
  - Added derived agent run records that join tasks to agent identity, kind,
    model policy, status, input/output refs, review requirement, and governance
    notes.
  - Added agent governance summary metrics for queued, running, waiting for
    review, completed, failed, cancelled, and human-review-required tasks.
  - Added credential-boundary status from runtime settings, including execution
    mode, default model, webhook URL/key readiness, local/OpenBao boundary, and
    production hardening recommendations.
  - Extended the operations console with a Telemetry control, governance metric
    cards, credential-boundary cards, and recent run ledger cards.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, live model providers, OpenBao secret fetch,
    persisted run-history tables, and replay/audit immutability.
- Implemented slice 030 binary report artifacts:
  - Added authenticated report artifact download responses for PDF, Excel
    workbook, CSV, JSON/API, and HTML output formats.
  - Added dependency-free PDF byte generation, valid minimal XLSX workbook
    generation, CSV generation, HTML rendering, content type selection,
    checksums, and stable filenames.
  - Updated render metadata to checksum and size the actual generated artifact
    bytes rather than only the preview text.
  - Extended the operations console with a Download control that fetches the
    selected report artifact, applies local/Keycloak auth headers, saves the
    returned file, and refreshes reporting state.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, MinIO/object storage persistence, and
    visual report layout QA.
- Implemented slice 031 report artifact storage boundary:
  - Added configurable local report artifact storage settings for artifact
    directory and URL prefix.
  - Persisted rendered/downloaded report artifact bytes under the ignored
    local artifact directory using organization, report, checksum, and stable
    filename pathing.
  - Returned stored artifact URLs through report metadata and download response
    headers so the API shape can map to MinIO/S3-compatible storage later.
  - Added artifact storage environment examples for local development and
    deployment configuration.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend production
    build, Playwright screenshots, MinIO client persistence, object lifecycle
    rules, and signed object URLs.
- Implemented slice 055 background communication digest scheduler:
  - Added a manager-triggered digest scheduler API that scans daily/weekly
    notification preferences for an organization, rejects immediate-mode runs,
    skips people without unread non-digest inbox items, and reuses the existing
    per-person digest creation path.
  - Extended the operations console with a Run digests control and batch run
    summary showing checked, created, and skipped counts.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and real cron/background worker execution.
- Implemented slice 056 family inbox portal:
  - Added an authenticated my-inbox API so guardians, parents, athletes, and
    members can load their own messages without supplying a person id.
  - Added a self-service inbox read endpoint that lets recipients mark their
    own messages read while preserving manager override for operators.
  - Added a `/family` portal page with organization/account controls, unread
    metrics, message list, message detail, and read acknowledgement.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and live Keycloak guardian-account mapping.
- Implemented slice 057 family athlete consent dashboard:
  - Added an authenticated family summary API that lists athletes linked to the
    current guardian account inside an organization.
  - Included relationship role, consent signing flags, pending consent-request
    counts, and latest consent status/scope/signing time for each child.
  - Extended the `/family` portal with child cards and consent counters
    alongside the inbox workflow.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and live Keycloak guardian-account mapping.
- Implemented slice 058 guardian account email binding:
  - Updated the identity bridge so a first login with an email already recorded
    on a guardian/member `Person` binds the `AppUser` to that existing person
    instead of creating a duplicate.
  - Existing app users with missing or broken person links are repaired against
    the same email-based person lookup before falling back to new person
    creation.
  - User email/display name are refreshed from the verified principal during
    login.
  - Verification: `uv run ruff check .`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite and live Keycloak
    guardian-account login.
- Implemented slice 059 family schedule and clearance view:
  - Added a guardian-scoped family events API that derives upcoming child
    activities from attendance invitations and team roster membership.
  - Reused the existing safeguarding clearance logic so family users see the
    same consent-required, denied, expired, no-guardian, and cleared states
    that operators enforce at check-in.
  - Extended `/family` with upcoming event cards showing child, event type,
    date, attendance status, and clearance status alongside inbox and consent
    summaries.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and live guardian account smoke.
- Implemented slice 060 family event RSVP:
  - Added a guardian-owned RSVP API for linked child events, allowing confirmed
    or declined responses only.
  - Confirmation reuses safeguarding clearance and blocks when consent is
    missing, denied, expired, or otherwise not cleared; declined responses can
    still be recorded.
  - Extended `/family` event cards with Confirm and Decline controls that
    update the schedule state in place.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and live guardian account smoke.
- Implemented slice 061 family portal consent responses:
  - Added guardian-owned pending consent request listing for `/family`, scoped
    to the authenticated guardian and linked athletes with consent authority.
  - Added direct family portal consent responses for grant/deny decisions,
    including expiry handling, request fulfillment, and consent upsert through
    the existing safeguarding consent path.
  - Extended `/family` with pending consent cards and Grant/Deny controls that
    update child consent summaries in place.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and live guardian account smoke.
- Implemented slice 062 branded public organization sites:
  - Added a public organization site API addressable by slug or subdomain,
    returning brand fields, contact details, teams, and upcoming events without
    requiring an authenticated session.
  - Added a branded `/site/[slug]` frontend page that applies tenant colors,
    logo/public name, mission, contact links, team cards, and schedule cards.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and live subdomain routing.
- Implemented slice 063 public registration inquiry funnel:
  - Added persisted registration inquiries for public organization sites,
    including athlete, guardian, contact, team, age-group, sport-interest,
    source URL, and review status fields.
  - Added public inquiry submission by organization slug/subdomain and an
    authenticated operator inquiry list for organization managers.
  - Extended `/site/[slug]` with a branded registration inquiry form tied to
    the site's team list.
  - Added Alembic migration `f2d4c6a8b901_add_registration_inquiries.py`.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, migration
    upgrade/downgrade execution, frontend production build, and browser QA.
- Implemented slice 064 registration inquiry conversion:
  - Added an operator conversion API for public registration inquiries that
    creates athlete person/profile records, athlete organization membership,
    optional team roster entry, and optional guardian relationship from the
    inquiry contact details.
  - Converted inquiries are marked `converted` and protected from repeat
    conversion.
  - Extended the operations console tenant panel with recent inquiry cards and
    Convert actions that add the converted athlete into the local roster state.
  - Verification: `uv run ruff check .`,
    `pnpm --filter @afrolete/frontend typecheck`, `git diff --check`.
  - Not tested in this fast slice: full backend test suite, frontend
    production build, browser QA, and bulk inquiry deduplication.

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
| 023 - Commercial finance controls | Partial | Backend tests 46/46; frontend typecheck/build | Tax quote estimates, settlement summaries, ticket refunds, invoice refunds, accounting export rows, sponsorship dashboard metrics, and console controls are implemented; live payment provider webhooks, tax authority filing, accounting API sync, and sponsor-facing dashboards remain. |
| 024 - Reporting output intelligence | Partial | Backend ruff; frontend typecheck; diff check | Report artifact rendering metadata, verification scoring, chart-ready summaries, benchmark models, deterministic AI review insights, and console controls are implemented; real binary PDF/Excel generation, report file storage, visual chart rendering, and full verification remain. |
| 025 - SaaS billing operations | Partial | Backend ruff; frontend typecheck; diff check | SaaS tax quotes, plan-change proration quotes, dunning notice preparation, signed payment webhook intake, invoice status mutation, and console controls are implemented; external dunning delivery, tax filing integrations, and full verification remain. |
| 026 - Competition automation | Partial | Backend ruff; frontend typecheck; diff check | Round-robin fixture generation, bracket projections, conflict detection, and console controls are implemented; advanced tournament advancement, bracket visualization polish, optimization algorithms, and full verification remain. |
| 027 - AI training plan generation | Partial | Backend ruff; frontend typecheck; diff check | AI-assisted plan generation from readiness, assessments, observations, drills, and upcoming competition fixtures is implemented with generated blocks and console controls; live model generation, availability calendars, post-session feedback, and full verification remain. |
| 028 - Performance ingestion and review | Partial | Backend ruff; frontend typecheck; diff check | Provider-neutral evidence ingestion, deterministic value extraction, pending-review observations, human review/correction, and console controls are implemented; real provider parsers, model-backed extraction, and full verification remain. |
| 029 - AI agent governance telemetry | Partial | Backend ruff; frontend typecheck; diff check | Derived run records, governance summary metrics, credential-boundary status, and console telemetry cards are implemented; live model providers, OpenBao secret fetch, persisted run history, audit immutability, and full verification remain. |
| 030 - Binary report artifacts | Partial | Backend ruff; frontend typecheck; diff check | Authenticated PDF/XLSX/CSV/API/HTML artifact download, byte-level checksums, filenames, render metadata, and console download controls are implemented; object storage persistence, visual report QA, and full verification remain. |
| 031 - Report artifact storage boundary | Partial | Backend ruff; frontend typecheck; diff check | Local persisted report artifacts, configurable artifact directory/prefix, stored artifact URLs, and download headers are implemented; MinIO persistence, signed URLs, lifecycle policy, and full verification remain. |
| 032 - Signed report artifact access | Partial | Backend ruff; frontend typecheck; diff check | Short-lived HMAC signed artifact links, unauthenticated signed local artifact serving, checksum headers, signing TTL configuration, and console link minting are implemented; MinIO persistence, lifecycle policy, visual report QA, and full verification remain. |
| 033 - Reporting chart visualization | Partial | Frontend typecheck; diff check | Reporting throughput, insight severity, and predictive risk chart payloads now render as compact bars and donut cards in the console; deeper dashboard interactions, visual QA, and full verification remain. |
| 034 - Billing webhook signature boundary | Partial | Backend ruff; frontend typecheck; diff check | SaaS payment webhook intake now supports timestamped HMAC signature enforcement, configurable tolerance, signature result reporting, and console visibility; external dunning delivery, tax filing integrations, plan-change application, and full verification remain. |
| 035 - Billing dunning delivery | Partial | Backend ruff; frontend typecheck; diff check | Overdue invoice dunning notices can now be delivered through a configurable provider-neutral webhook, record-only mode stays usable locally, delivery keys and timeouts are configurable, and the console shows delivery outcomes; tax filing integrations, plan-change application, and full verification remain. |
| 036 - Billing plan-change application | Partial | Backend ruff; frontend typecheck; diff check | Proration quotes can now be applied to tenant subscriptions, updating negotiated price, optional plan identity, billing cycle, subscription status, and plan-change notes from the console; tax filing integrations and full verification remain. |
| 037 - Billing tax filing delivery | Partial | Backend ruff; frontend typecheck; diff check | Invoice tax totals can now be packaged by jurisdiction and period, prepared in record-only mode, or delivered through a configurable tax filing webhook with separate keys/timeouts and console result visibility; full billing verification remains. |
| 038 - Tournament round advancement | Partial | Backend ruff; frontend typecheck; diff check | Confirmed non-draw winners from a source stage/round can now be advanced into the next knockout round with duplicate protection, bye reporting, generated fixture visibility, and console controls; bracket visualization polish, scheduling optimization, broadcast operations, and full verification remain. |
| 039 - Bracket visualization lanes | Partial | Frontend typecheck; diff check | Competition brackets now render as structured responsive lanes with match slots, projected/byed teams, fixture status, and winner visibility instead of compressed text; scheduling optimization, broadcast operations, and full verification remain. |
| 040 - Competition schedule optimization | Partial | Backend ruff; frontend typecheck; diff check | Pending fixtures can now be rescheduled by a deterministic optimizer that preserves confirmed finals, enforces team rest windows, avoids venue overlaps, updates fixture notes, and exposes moved/protected counts in the console; ticketing, broadcast operations, and full verification remain. |
| 041 - Competition broadcast operations | Partial | Backend ruff; frontend typecheck; diff check | Competition updates can now be broadcast to rostered participants and guardians through the existing communications delivery pipeline, with generated status/fixture summaries, channel selection, dispatch counts, and console visibility; ticketing and full verification remain. |
| 042 - Competition ticketing integration | Partial | Backend ruff; frontend typecheck; diff check | League and tournament fixtures can now open ticket sales through the existing commercial ticket product system, auto-create linked match events when needed, show ticket capacity/sales in the competition console, and feed the commerce summary/check-in/refund workflows; full competition verification remains. |
| 043 - Training readiness and feedback loops | Partial | Backend ruff; frontend typecheck; diff check | Training sessions now collect readiness, soreness, sleep, mood, actual RPE, duration, completion, athlete feedback, coach notes, load deltas, and recommendations from the console; live model generation, availability calendars, and full verification remain. |
| 044 - Training availability suggestions | Partial | Backend ruff; frontend typecheck; diff check | Coaches can now request ranked training slots that account for existing events, training sessions, competition fixtures, and facility bookings, then apply the best slot to the session planner; live calendar sync and full verification remain. |
| 045 - Supplier ordering workflow | Partial | Backend ruff; frontend typecheck; diff check | Procurement recommendations can now become supplier orders, open orders are visible in the asset console, and receiving an order updates equipment total/available quantities; real supplier API submission, invoice sync, and full verification remain. |
| 046 - Equipment file uploads | Partial | Backend ruff; frontend typecheck; diff check | Equipment records now accept real local file uploads through a base64 API, persist bytes with checksum-based storage names, keep upload metadata, can mark uploaded images as the equipment photo, and expose files in the asset console; MinIO persistence, lifecycle policy, and full verification remain. |
| 047 - RFID scan intake | Partial | Backend ruff; frontend typecheck; diff check | RFID reader events can now be recorded as durable equipment scan events, preserve unmatched codes for reconciliation, update matched item audit dates and reader locations, expose scan history filters through the API, and show latest scans in the asset console; live reader gateway provisioning and full verification remain. |
| 048 - Supplier API submission | Partial | Backend ruff; frontend typecheck; diff check | Supplier orders can now be submitted through a provider-neutral webhook or prepared in record-only mode, update order submission status and notes, expose delivery outcomes in the API, and provide Submit controls in the asset console; supplier-specific adapters, invoice sync, and full verification remain. |
| 049 - Equipment lease invoicing | Partial | Backend ruff; frontend typecheck; diff check | Equipment lease estimates can now be converted into draft commercial invoices with person/team billing targets, invoice numbers, due dates, memo context, and console visibility; accounting API sync, lease payment schedules, and full verification remain. |
| 050 - RFID reader gateway provisioning | Partial | Backend ruff; frontend typecheck; diff check | RFID readers can now be provisioned with hashed reader keys, listed by organization, accept hardware-style gateway scan posts with a reader key, update reader heartbeat/last-scan metadata, and appear in the asset console; live device fleet rollout and full verification remain. |
| 051 - Equipment lease payment schedules | Partial | Backend ruff; frontend typecheck; diff check | Equipment leases can now create persisted finance invoices, lease schedules, and monthly installment rows with due dates, person/team targets, console Schedule controls, and lease schedule visibility; installment payment reconciliation and full verification remain. |
| 052 - Equipment lease payment reconciliation | Partial | Backend ruff; frontend typecheck; diff check | Lease schedules can now record commercial payments against their backing invoice, mark due installments paid in sequence, update invoice paid/partial state, expose remaining balances, and provide console Reconcile/Pay controls; partial-installment allocation and full verification remain. |
| 053 - Supplier invoice sync | Partial | Backend ruff; frontend typecheck; diff check | Received, submitted, and ordered supplier orders can now be packaged for supplier invoice/accounting sync through record-only mode or a provider-neutral webhook, update order sync status and notes, and expose Sync controls/results in the asset console; supplier-specific adapters and full verification remain. |
| 054 - Partial lease installment allocation | Partial | Backend ruff; frontend typecheck; diff check | Lease installment rows now persist amount paid, reject overpayment beyond invoice balance, allocate payments across installments including partial fills, update partial/paid installment status, and show paid/partial counts in the console; full verification remains. |
| 055 - Background communication digest scheduler | Partial | Backend ruff; frontend typecheck; diff check | Daily/weekly notification preferences can now be processed in batch through a manager-triggered API and console control, skipping empty inboxes and reusing per-person digest creation; real cron/background worker execution and full verification remain. |
| 056 - Family inbox portal | Partial | Backend ruff; frontend typecheck; diff check | Authenticated users can now load their own communication inbox, mark messages read, and use a dedicated `/family` portal surface with inbox metrics and message detail; live Keycloak guardian mapping and full verification remain. |
| 057 - Family athlete consent dashboard | Partial | Backend ruff; frontend typecheck; diff check | Guardian accounts can now retrieve linked athlete summaries with relationship, consent authority, pending consent counts, and latest consent state, with child cards exposed in `/family`; live Keycloak guardian mapping and full verification remain. |
| 058 - Guardian account email binding | Partial | Backend ruff; diff check | First login now binds an `AppUser` to an existing `Person` with the same verified email, so guardian/member accounts can access their linked family data without duplicate person records; live Keycloak smoke and full verification remain. |
| 059 - Family schedule and clearance view | Partial | Backend ruff; frontend typecheck; diff check | Guardian accounts can now see upcoming linked-athlete events with attendance and safeguarding clearance state in `/family`; live guardian account smoke and full verification remain. |
| 060 - Family event RSVP | Partial | Backend ruff; frontend typecheck; diff check | Guardians can confirm or decline linked child events from `/family`, with confirmations gated by the same safeguarding clearance logic as operator check-in; live guardian account smoke and full verification remain. |
| 061 - Family portal consent responses | Partial | Backend ruff; frontend typecheck; diff check | Guardians can now list pending consent requests and grant or deny them from `/family`, fulfilling requests and updating consent records through existing safeguarding flows; live guardian smoke and full verification remain. |
| 062 - Branded public organization sites | Partial | Backend ruff; frontend typecheck; diff check | Organization slugs/subdomains now expose public branded site profiles and `/site/[slug]` renders tenant colors, logo/name, mission, contact links, teams, and upcoming events; live subdomain routing and full verification remain. |
| 063 - Public registration inquiry funnel | Partial | Backend ruff; frontend typecheck; diff check | Public organization sites now collect persisted player/parent registration inquiries and operators can list them through an authenticated organization API; full verification remains. |
| 064 - Registration inquiry conversion | Partial | Backend ruff; frontend typecheck; diff check | Operators can convert public inquiries into athlete person/profile records, athlete membership, team roster entries, and guardian relationships from the console; full verification remains. |
| 065 - Registration inquiry review workflow | Partial | Backend ruff; frontend typecheck; diff check | Operators can now triage public inquiries through review, contacted, waitlisted, and rejected states, capture review notes, set follow-up times, preserve reviewer metadata, and still convert accepted inquiries into roster records; full verification remains. |
| 066 - Registration inquiry follow-up messaging | Partial | Backend ruff; frontend typecheck; diff check | Operators can now queue an email follow-up directly from a public registration inquiry, automatically create or reuse the contact person, mark the inquiry contacted, append review context, and surface the message in the existing communications console; full verification remains. |
| 067 - Persisted AI agent run ledger | Partial | Backend ruff; frontend typecheck; diff check | Agent queueing, execution, and manual review updates now append durable run records with execution mode, model policy, timing, operator, governance notes, idempotency keys, and hash chaining, and the console shows the latest ledger hashes; full migration/live-provider verification remains. |
| 068 - AI agent ledger verification | Partial | Backend ruff; frontend typecheck; diff check | The agent ledger now has a verification API that recomputes record hashes, checks hash-chain continuity by ledger sequence, reports broken record IDs, and surfaces ledger validity plus latest hash in the console; full migration/live-provider verification remains. |
| 069 - MinIO-compatible object storage adapter | Partial | Backend ruff; frontend typecheck; diff check | Report artifacts and equipment uploads now use a shared storage adapter that supports local files by default and S3-compatible MinIO writes/reads through SigV4-signed backend requests, with environment examples and MinIO deployment notes; live MinIO smoke and lifecycle policy remain. |
| 070 - Authenticated equipment file downloads | Partial | Backend ruff; frontend typecheck; diff check | Equipment file records now have an authenticated download endpoint that reads through the same local/MinIO storage adapter, verifies checksums before returning bytes, and adds console download controls; live MinIO download smoke and browser QA remain. |
| 071 - Safeguarding incident reporting | Partial | Backend ruff; frontend typecheck; diff check | Operators can now log injury, medical, safeguarding, misconduct, facility, transport, weather, and other incidents with severity, event/team/athlete context, immediate action, medical follow-up and regulatory-report flags, then triage, investigate, and resolve them from the console; full compliance workflows and external reporting remain. |
| 072 - Background checks and compliance credentials | Partial | Backend ruff; frontend typecheck; diff check | Operators can now request background checks for athlete-facing people, track provider/reference/status/risk/expiry, record safeguarding, first-aid, coaching, officiating, driver, medical, and other credentials with renewal dates, then update compliance state from the console; real provider adapters, automated expiry jobs, and evidence upload review remain. |
| 073 - Compliance dashboard and expiry reconciliation | Partial | Backend ruff; frontend typecheck; diff check | Managers now get a derived safeguarding compliance summary with overall compliance percentage, check/credential/incident counters, blocker queues, renewal queues, investigation queues, and a reconciliation action that marks expired checks/credentials and near-due renewals; scheduled workers, access-control automation, and provider-sourced risk scoring remain. |
| 074 - Incident regulatory report packages | Partial | Backend ruff; frontend typecheck; diff check | Reportable safeguarding incidents can now generate auditable regulatory packages with agency, jurisdiction, due date, narrative, checklist payload, submission payload, external reference, and draft/ready/submitted/accepted/rejected workflow controls in the console; electronic government portal submission and document exports remain. |
| 075 - Incident insurance claim tracking | Partial | Backend ruff; frontend typecheck; diff check | Injury, liability, equipment, property, travel, and other incident claims can now be drafted from safeguarding incidents with insurer, policy, claim number, coverage verification, claimed/approved/paid/reserve amounts, documentation checklist, submission payload, communication log, tracking URL, and ready/submitted/approved/paid/denied workflow controls; direct insurer APIs and automatic status polling remain. |
| 076 - Return-to-play medical clearance | Partial | Backend ruff; frontend typecheck; diff check | Injury and medical incidents can now spawn medical clearance reviews with athlete binding, provider, assessed/valid dates, return-to-play stage, restrictions, documentation pointer, and pending/restricted/cleared/not-cleared/expired workflow controls in the console; medical portal integrations and attendance gating by active clearance remain. |
| 077 - Attendance medical clearance gate | Partial | Backend ruff; frontend typecheck; diff check | Event check-in now blocks confirmed/present attendance when an athlete has an open injury or medical incident without an active cleared or restricted return-to-play clearance, surfaces medical clearance status/reason in attendance rows, and returns structured conflict details for operators; deeper attendance policy configuration and browser QA remain. |
| 078 - Emergency action plan management | Partial | Backend ruff; frontend typecheck; diff check | Facilities can now maintain emergency action plans with emergency contacts, evacuation routes, medical/weather/communication protocols, equipment locations, assembly points, special-needs plans, review dates, plan status controls, live activation records, assigned responders, guidance steps, communication logs, outcomes, and response-time tracking; mobile emergency UI, automated alerts, and map/media integrations remain. |
| 079 - Emergency activation alert dispatch | Partial | Backend ruff; frontend typecheck; diff check | Emergency activations can now create urgent quiet-hours-override alert messages through the existing communications recipient expansion, including guardian copies for minors, message IDs, recipient counts, and console dispatch controls; live provider delivery, escalation trees, and mobile map/media UI remain. |
| 080 - Emergency escalation matrix | Partial | Backend ruff; frontend typecheck; diff check | Emergency action plans now capture incident command roles, tiered escalation matrices, and external agency contacts, activations carry an escalation level, alert bodies include escalation context, and the console can escalate active responses; live mobile command UI and automated escalation timers remain. |
| 081 - Emergency post-incident reporting | Partial | Backend ruff; frontend typecheck; diff check | Emergency activations can now generate or reuse linked safeguarding incident reports with mapped incident type, severity, activation narrative, immediate action, medical follow-up, regulatory-report flags, and console linkage; richer after-action review packages and browser QA remain. |
| 082 - Event weather safety decisions | Partial | Backend ruff; frontend typecheck; diff check | Events can now store provider-neutral weather assessments with temperature/heat index/WBGT, humidity, AQI, lightning distance, wind, precipitation, deterministic alert classification, proceed/monitor/modify/delay/evacuate decisions, recommended actions, and console weather checks; live multi-source provider ingestion and automated participant broadcasts remain. |
| 083 - Event weather alert dispatch | Partial | Backend ruff; frontend typecheck; diff check | Weather assessments can now generate urgent event-scoped communication alerts through the existing broadcast recipient expansion, including guardian copies, quiet-hours override, message IDs, recipient counts, and console dispatch controls; live weather-triggered automation and provider delivery remain. |
| 084 - Event travel planning and risk | Partial | Backend ruff; frontend typecheck; diff check | Events can now carry travel plans with destination, transport mode, departure/return times, route, driver/vehicle checks, staff/passenger manifests, lodging/meals/equipment, emergency contacts, medical access, consent due dates, costs, deterministic travel risk classification, status workflow, and console controls; live GPS tracking, carpool matching, receipts, and payment collection remain. |
| 085 - Event travel consent generation | Partial | Backend ruff; frontend typecheck; diff check | Event travel plans can now generate event-scoped guardian consent requests for event participants using the existing one-time token consent workflow, with minor/unknown-age filtering, primary signing guardian selection, duplicate pending request detection, destination/token return, and console controls; multi-level school/association approval, payment collection, and automated reminder delivery remain. |
| 086 - Event travel consent reminders | Partial | Backend ruff; frontend typecheck; diff check | Event travel plans can now send guardian reminders for pending event-scoped travel consent requests through the existing communications pipeline, with selectable email/SMS/WhatsApp/Telegram/push/in-app channels, pending request counts, recipient counts, message linkage, and console controls; scheduled reminder automation, provider delivery credentials, and per-request reminder history remain. |
| 087 - Event travel safety manifest | Partial | Backend ruff; frontend typecheck; diff check | Event travel plans can now produce a staff safety manifest with event participants, guardian names, guardian contact destinations, medical clearance status/reason, emergency contacts, medical access plan, participant counts, and console controls; exportable PDFs, offline mobile access, and fine-grained medical data permissions remain. |
| 088 - Event travel fee invoicing | Partial | Backend ruff; frontend typecheck; diff check | Event travel plans can now generate deterministic per-participant trip fee invoices through the existing finance invoice system, bill guardians for minors, skip minors without signing guardians, reuse existing invoice numbers to prevent duplicate charges, total generated fees, and expose console controls; online payment checkout, payment links, waivers/scholarships, and automated payment reminders remain. |
| 089 - Event travel approval workflow | Partial | Backend ruff; frontend typecheck; migration upgrade; diff check | Event travel plans can now maintain approval requirements with approval level, assigned approver, pending/approved/rejected/cancelled status, decision actor/time, unique per-plan levels, and console controls to require, list, approve, or reject approvals; automatic routing to school/association approvers, notification tasks, and readiness gating remain. |
| 090 - Event travel inspection checklists | Partial | Backend ruff; frontend typecheck; migration upgrade; diff check | Event travel plans can now seed, list, and update digital checklist items for pre-trip inspections and other travel phases, with default safety items, per-item pending/completed/blocked/not-applicable status, operator completion actor/time, evidence URL, notes, uniqueness per checklist item, and console controls; photo upload attachment, checklist templates by trip type, and departure gating remain. |
| 091 - Event travel live tracking updates | Partial | Backend ruff; frontend typecheck; migration upgrade; diff check | Event travel plans can now record provider-neutral GPS/location updates with phase, source, timestamp, recorder, latitude/longitude, speed, heading, notes, and linked guardian/team notifications for departure, delay, arrival, and return phases through the existing communications pipeline; hardware GPS ingestion, geofencing, and streaming transport remain. |
| 092 - Event travel expense and reimbursement tracking | Partial | Fast backend/frontend checks; migration authored | Event travel plans can now capture travel expenses with category, vendor, amount, currency, incurred time, paid-by person, receipt URL, notes, reimbursement status, approving actor, reimbursement time, and console controls to submit, list, approve, reimburse, or reject trip costs; live receipt uploads, accounting sync, and richer reimbursement policy remain. |
| 093 - Offline travel manifest export | Partial | Fast backend/frontend checks | Travel manifests can now be exported as CSV or text payloads with deterministic filenames, participant IDs, guardian names/contacts, medical clearance state, medical reasons, emergency contacts, and console export controls; direct file download packaging, PDF layout, and signed offline links remain. |
| 094 - Travel carpool coordination | Partial | Fast backend/frontend checks; migration authored | Event travel plans can now track carpool ride requests and offers with rider/driver person links, pickup/dropoff locations, optional pickup/dropoff coordinates, seat counts, pickup windows, open/matched/confirmed/cancelled status, match scores, matched time, notes, APIs, and console controls to create, load, match, confirm, or cancel rides; live map routing remains. |
| 095 - Travel departure readiness gate | Partial | Fast backend/frontend checks | Event travel plans can now run a departure readiness gate that combines deterministic travel risk, approvals, rejected approvals, checklist pending/blocked counts, seeded checklist presence, pending guardian travel consents, and console blocker/warning display with recommended ready/draft status; automatic status enforcement, scheduled rechecks, and browser workflow QA remain. |
| 096 - Travel route optimization | Partial | Fast backend/frontend checks | Event travel plans can now generate deterministic route optimizations with balanced/fastest/safest/carpool-dense strategies, ordered origin/carpool/destination stops, pickup windows, seat context, traffic/weather delay modifiers, latest weather-assessment reroute guidance, recommended strategy overrides, recommended departure time, route risk warnings, and console optimization controls; live map provider routing, live traffic/geocoding APIs, and weather provider rerouting remain. |
| 097 - Travel fee checkout links | Partial | Fast backend/frontend checks | Existing travel fee invoices can now be converted into provider-neutral checkout/session payloads with invoice IDs, payer IDs, open amounts, provider labels, deterministic payment URLs, processor-style session IDs, session URLs/status, client references, return URLs, optional expiry, aggregate open amount, and console payment-session controls; reminder automation and live payment provider handoff remain. |
| 098 - Travel receipt uploads | Partial | Fast backend/frontend checks | Travel expenses can now accept real receipt uploads from the console, decode base64 payloads, persist files through the local/MinIO-compatible object storage adapter, checksum stored content, update expense receipt URLs, and return upload metadata; authenticated receipt download/review queues and accounting attachment sync remain. |
| 099 - Travel geofence breach checks | Partial | Fast backend/frontend checks | Event travel plans can now evaluate the latest recorded vehicle location against a configurable circular safety zone, compute distance from center, flag breaches, send urgent event-scoped guardian/team alerts through the communications pipeline, and expose console geofence controls; persistent geofence zones, hardware GPS ingestion, and streaming automation remain. |
| 100 - Travel approval routing | Partial | Fast backend/frontend checks | Event travel plans can now automatically recommend and seed operations, school, association, medical, and finance approval records from trip risk, consent requirements, medical context, destination level, weather risk, and cost signals, then show created/existing approval routes in the console; notification tasks, delegated approver assignment, and policy-admin configuration remain. |
| 101 - Travel checklist evidence uploads | Partial | Fast backend/frontend checks | Travel checklist items can now accept real photo/PDF evidence uploads from the console, decode base64 payloads, persist files through the local/MinIO-compatible object storage adapter, checksum stored content, update checklist evidence URLs, and mark uploaded items completed; authenticated evidence download/review queues and checklist templates by trip type remain. |
| 102 - Travel consent reminder automation | Partial | Fast backend/frontend checks | Events can now run an automated travel consent reminder pass that scans consent-required travel plans due within a configurable horizon, counts pending event consent requests, deduplicates guardian recipients, sends one scheduled-style event reminder through the communications pipeline, and surfaces due plan/reminder results in the console; background cron workers, per-request reminder history, and provider delivery credentials remain. |
| 103 - Travel carpool auto-matching | Partial | Fast backend/frontend checks | Travel carpool requests and offers can now be automatically matched from existing ride records using seat capacity, pickup/dropoff token overlap, optional coordinate distance scoring, and departure-window compatibility, update request/offer statuses with deterministic match scores, and expose auto-match controls/results in the console; live geocoder/provider enrichment remains. |
| 104 - Signed offline travel manifest links | Partial | Fast backend/frontend checks | Travel manifests can now be persisted as CSV/text files through the local/MinIO-compatible object storage adapter, minted into short-lived HMAC signed offline links, served without an authenticated session until expiry, and opened from the operations console; PDF layouts and live MinIO smoke remain. |
| 105 - Travel manifest PDF layout | Partial | Fast backend/frontend checks | Signed offline travel manifests can now be rendered as dependency-free PDF artifacts with destination, participant counts, emergency contacts, medical access plan, guardian contacts, medical clearance state, multi-page pagination, HMAC signed delivery, and console PDF-link controls; richer visual branding and live MinIO smoke remain. |
| 106 - Hardware GPS travel ingest | Partial | Fast backend checks | Hardware GPS devices and provider gateways can now post travel-plan location updates through a dedicated ingest endpoint with optional HMAC timestamp signatures, device/provider metadata, accuracy, battery state, external event IDs, automatic travel status transitions, and normal tracking history reads; live provider smoke remains. |
| 107 - Persistent travel geofence zones | Partial | Fast backend/frontend checks; migration authored | Travel plans can now store reusable named geofence zones with center coordinates, radius, optional provider-linked polygon vertices, active state, alert channel, breach alert policy, notes, list/create APIs, saved-zone breach checks, and console save/list/check controls; map drawing and scheduled streaming checks remain. |
| 108 - Travel geofence zone administration | Partial | Fast backend/frontend checks | Saved travel geofence zones can now be renamed, moved, resized, re-channeled, annotated, linked to provider zone IDs/revisions, assigned polygon boundaries, deactivated, reactivated, duplicate-label guarded, and updated from the console geofence form; map drawing and scheduled streaming checks remain. |
| 109 - Travel GPS device provisioning | Partial | Fast backend/frontend checks; migration authored | Travel plans can now provision hardware GPS devices with provider IDs, labels, status, vehicle assignment, installation time, notes, list/create/update APIs, console device controls, active/disabled/maintenance state management, and ingest-time last-seen/battery/accuracy health updates; per-device secret rotation and live provider smoke remain. |
| 110 - Travel device secret rotation | Partial | Fast backend/frontend checks; migration authored | Provisioned travel GPS devices can now rotate one-time ingest secrets, store per-device callback keys, surface secret configuration/rotation time, validate location-ingest HMAC signatures with the device secret before falling back to the global transition key, and expose console rotation controls; external vault write/fetch, replay nonces, and live provider smoke remain. |
| 111 - Travel device replay protection | Partial | Fast backend/frontend checks; migration authored | Travel device ingest now persists provider external event IDs per trip/provider/device, rejects duplicate external event IDs before creating location updates, links accepted provider events to the resulting GPS update, and returns replay-protection metadata in ingest responses; live provider smoke remain. |
| 112 - Travel replay nonce expiry policy | Partial | Fast backend/frontend checks | Travel device replay records now follow a configurable retention window, prune expired provider event IDs before duplicate checks, and return retention/prune metadata in ingest responses so replay protection is durable but bounded; live provider smoke remain. |
| 113 - Travel driver ratings | Partial | Fast backend/frontend checks; migration authored | Travel plans can now collect post-trip driver ratings with driver/person references, vehicle labels, category scores, reviewer identity, incident flags, use-again recommendations, aggregate summaries, marketplace matching inputs, API routes, and console create/list controls; provider-sourced safety scores remain. |
| 114 - Travel backup driver network | Partial | Fast backend/frontend checks; migration authored | Travel plans can now maintain backup driver rosters with driver/person references, phone, vehicle, capacity, license and screening status, availability, response time, priority ordering, notes, APIs, status updates, marketplace ranking inputs, and console controls; live credential-provider checks remain. |
| 115 - Travel backup driver dispatch | Partial | Fast backend/frontend checks; migration authored | Travel plans can now automatically select an eligible backup driver from the roster using availability, capacity, priority, response time, optional verification filters, and marketplace-compatible scoring signals, mark the driver dispatched, record dispatch reason/time/actor, notify person-linked drivers through communications, return dispatch rationale, and expose console dispatch controls; live credential-provider checks remain. |
| 116 - Travel GPS fleet inventory | Partial | Fast backend/frontend checks | Organizations can now view travel GPS devices across all travel plans with fleet totals, active/maintenance/disabled/lost counts, stale-device detection, low-battery detection, per-device trip destination, vehicle assignment, last-seen health, secret configuration, API access, and console inventory controls; live device fleet rollout and streaming telemetry remain. |
| 117 - Travel reimbursement payout execution | Partial | Fast backend/frontend checks; migration authored | Approved travel expenses can now execute provider-neutral reimbursement payouts with generated or external payout references, provider/status/timestamp/processor audit fields, adapter mode, payout destination, idempotency key, provider status code/response metadata, automatic reimbursed-state transition, API response metadata, and console payout controls; live provider HTTP submission and accounting sync remain. |
| 118 - Travel provider idempotency windows | Partial | Fast backend/frontend checks | Travel device ingest can now configure per-provider replay retention windows through `AFROLETE_TRAVEL_DEVICE_PROVIDER_IDEMPOTENCY_DAYS`, prune expired replay IDs only for the active provider before duplicate checks, and return whether the provider-specific or default idempotency window was used; live provider smoke and streaming transport remain. |
| 119 - Travel route map rendering | Partial | Fast backend/frontend checks | Travel plans can now expose a provider-neutral route map payload from recorded GPS path points and active geofence zones, calculate map bounds, identify origin/latest-position/geofence markers, and render a console map summary with marker and latest-position context; live map SDK tiles, provider routing, and dense-route browser QA remain. |
| 120 - Geocoded carpool scoring | Partial | Fast backend/frontend checks; migration authored | Carpool ride requests and offers can now store optional pickup/dropoff latitude/longitude values, auto-match with distance-bucket scoring when coordinates are present, return pickup/dropoff match distances, retain text-token fallback for ungeocoded rides, and expose coordinate capture/results in the console; live geocoder lookup, map-assisted pickup selection, and browser QA remain. |
| 121 - Mobile travel manifest offline cache | Partial | Fast frontend typecheck; diff check | The operations console can now cache a fetched travel manifest into browser storage, restore it later without a network call, show cache timestamp/version metadata, and expose Cache/Offline controls for field/mobile use; service-worker prefetch and browser QA remain. |
| 122 - Travel payment processor sessions | Partial | Fast backend/frontend checks | Travel fee checkout generation now emits provider-ready processor session metadata for each invoice, including stable session IDs, hosted-session URLs, client references, open/paid session state, success/cancel return URLs, and console session visibility; live processor API creation remains. |
| 123 - Provider-backed geofence polygons | Partial | Fast backend/frontend checks; migration authored | Travel geofence zones can now store provider names, provider zone IDs, provider revisions, and polygon coordinate vertices, evaluate latest vehicle positions with point-in-polygon containment before falling back to radius checks, return boundary type/vertex counts, and expose polygon/provider controls in the console; map drawing UX, scheduled streaming checks, and live map provider sync remain. |
| 124 - Weather-aware travel rerouting | Partial | Fast backend/frontend checks | Route optimization now consumes the latest event weather assessment and route weather risk, upgrades fastest/high-risk trips to safer strategies, estimates deterministic traffic and weather delay buffers, flags reroute-required decisions, returns reroute reasons/actions plus latest weather decision metadata, and surfaces the guidance in the console; live traffic APIs, live weather provider feeds, and map-provider reroute geometry remain. |
| 125 - Verified driver marketplace matching | Partial | Fast backend/frontend checks | Travel plans can now rank available backup drivers as marketplace candidates using license/background verification, capacity, response time, availability, and post-trip rating/incident history, return recommended driver IDs, score rationales, verified counts, and expose marketplace controls/results in the console; live credential-provider verification, external driver marketplace inventory, and provider-sourced safety scores remain. |
| 126 - Travel payout adapter audit | Partial | Fast backend/frontend checks; migration authored | Travel reimbursement payouts now persist bank/mobile-money adapter mode, payout destination, idempotency key, provider status code, provider response payload, and console-visible adapter audit details while retaining deterministic local execution; live provider HTTP submission, callback reconciliation, and accounting sync remain. |
| 127 - Travel telemetry streaming transport | Partial | Fast backend/frontend checks | Travel location tracking now exposes authenticated NDJSON telemetry streams with no-cache stream headers, replayable GPS update rows, stream discovery metadata, latest update context, replay window metadata, and console stream controls; long-lived push workers, provider smoke tests, and browser streaming QA remain. |
| 128 - Encrypted travel manifest offline cache | Partial | Fast frontend typecheck; diff check | Offline travel manifests are now stored as versioned Web Crypto AES-GCM envelopes bound to the operator identity and travel plan, include SHA-256 payload checksums, carry seven-day expiry metadata, reject expired restores, and keep legacy-cache restore compatibility; service-worker prefetch, background refresh, browser crypto QA, and multi-device key recovery remain. |
| 129 - Travel device secret vault reference custody | Partial | Fast backend/frontend checks; migration authored | Travel GPS device secret rotation can now stamp each rotated secret with a configurable custody mode, OpenBao-style vault provider, and deterministic vault reference path, expose that metadata through device, fleet, and rotation responses, and render the custody reference in the operations console; live OpenBao write/fetch, removing database fallback storage, and provider smoke tests remain. |
| 130 - Hosted travel fee payment page | Partial | Fast backend/frontend checks | Travel fee checkout sessions now resolve to a public hosted payment-page payload, render a dedicated `/pay/sessions/{sessionId}` portal with invoice status, due dates, method selection, outstanding totals, and confirmation controls, and accept provider-neutral settlement events that record finance payments and mark invoices partial/paid; live processor redirects, PCI payment fields, and browser payment QA remain. |
| 131 - Signed travel fee payment webhooks | Partial | Fast backend/frontend checks | Travel fee payment providers can now post settlement callbacks to a dedicated webhook endpoint with timestamped HMAC signature enforcement, configurable signing key/tolerance, duplicate external-reference protection through the settlement path, and signature-required/validated response metadata; provider smoke tests and browser payment QA remain. |
| 132 - Travel fee provider payload normalization | Partial | Fast backend/frontend checks | The signed travel fee webhook endpoint now accepts raw provider callback bodies and normalizes provider-neutral, Stripe Checkout, M-Pesa STK callback, and PayPal capture payloads into the settlement path, extracting invoice/session metadata, amount/currency, external payment references, method names, and payment status; live provider sandbox smoke tests, reconciliation dashboards, and browser payment QA remain. |
| 133 - Travel fee payment reconciliation | Partial | Fast backend/frontend checks | Travel plans now expose a fee reconciliation API and console control that summarize generated travel invoices, checkout session IDs, paid/partial/unpaid counts, total due/paid/open amounts, per-invoice payment counts, latest provider references, and payment rows from the finance ledger; live provider sandbox smoke tests and browser payment QA remain. |
| 134 - Travel fee reconciliation exceptions | Partial | Fast backend/frontend checks | Travel fee reconciliation now derives operator exceptions for overpaid invoices, paid invoices without payment rows, overdue open balances, payment currency mismatches, missing provider references, and invoice/payment ledger total drift, returning exception severity/action guidance and surfacing exception counts in the console; live provider sandbox smoke tests and browser payment QA remain. |
| 135 - Travel fee exception resolution actions | Partial | Fast backend/frontend checks | Operators can now resolve actionable travel fee reconciliation exceptions by applying open-balance waivers, attaching missing provider references, rebuilding missing payment rows from invoice paid totals, and refund-adjusting overpayments, with each action returning a refreshed reconciliation and console feedback; currency conversion review, live provider sandbox smoke tests, and browser payment QA remain. |
| 136 - Travel fee ledger drift repair | Partial | Fast backend/frontend checks | Travel fee reconciliation now detects per-invoice paid-total drift against finance payment rows and gives operators a sync action that resets the invoice paid total to the payment ledger, refreshes invoice status, and clears the aggregate ledger mismatch when all affected invoices are repaired; live provider sandbox smoke tests and browser payment QA remain. |
| 137 - Travel fee currency mismatch repair | Partial | Fast backend/frontend checks | Operators can now resolve travel fee payment currency mismatches by rebooking the affected payment into the invoice currency, preserving prior amount/currency in notes, recomputing the invoice paid total from payment rows, refreshing invoice status, and returning an updated reconciliation to the console; live provider sandbox smoke tests and browser payment QA remain. |
| 138 - Travel payout callback reconciliation | Partial | Fast backend/frontend checks | Travel reimbursement payouts now accept provider-neutral callback reconciliation by payout reference or idempotency key, optionally enforce timestamped HMAC signatures, normalize provider statuses into paid/queued/failed/cancelled/returned outcomes, update reimbursement state, preserve callback payload audit metadata, and expose console callback controls; live payout provider smoke tests and browser QA remain. |
| 139 - Weather-triggered alert automation | Partial | Fast backend/frontend checks | Event weather assessments can now be processed by an automation run that filters by alert severity, skips already-alerted assessment/channel pairs, dispatches urgent event-scoped weather alerts with guardian copies through the existing communications pipeline, supports dry-run mode for scheduled workers, and exposes automation results in the console; live weather provider ingestion, real worker/cron scheduling, and browser QA remain. |
| 140 - Urgent communication escalation workflow | Partial | Fast backend/frontend checks | Urgent messages can now be escalated to unresolved queued/failed/suppressed recipients through an alternate channel, generating a new quiet-hours-override message with escalation level context, target/skipped counts, recipient expansion, and console controls/results; provider credentials, scheduled escalation timers, and browser QA remain. |
| 141 - AI model transparency reporting | Partial | Fast backend/frontend checks | Agent governance now exposes a model transparency report derived from the hash-chained run ledger, summarizing model policies, assigned agent counts, run counts, execution modes, failed/review runs, latest evidence, risk bands, credential boundary, ledger validity, recommendations, and console-visible model cards; live model-provider telemetry, formal model registry records, and browser QA remain. |
| 142 - Signed agent worker execution | Partial | Fast backend checks | Live agent webhook execution now serializes deterministic JSON payloads with task idempotency keys and sends timestamped HMAC signatures using the configured agent webhook key, giving external workers a stable replay-protection boundary before returning model output; live worker verification, inbound result callbacks, and OpenBao secret fetch remain. |
| 143 - Signed agent worker callbacks | Partial | Fast backend/frontend checks | External AI workers can now post signed result callbacks with task IDs, statuses, output references, review notes, idempotency keys, and raw provider payload metadata; callbacks update governed agent tasks, append hash-chained worker callback ledger records, ignore duplicate idempotency keys, and expose a console callback simulation control; live worker verification and OpenBao secret fetch remain. |
| 144 - AI model registry records | Partial | Fast backend/frontend checks; migration authored | Organizations can now register AI model policies with provider, family/version, use case, risk tier, review status, documentation, evaluation, limitation, bias, data-residency, owner, and approval metadata; model transparency includes registry status/risk/doc fields and the console can register current agent policies; live model-provider telemetry, approval workflow automation, and browser QA remain. |
| 145 - AI model registry approval controls | Partial | Fast frontend typecheck; diff check | Operators can now approve, block, or retire registered AI model policies from the console, updating governance review status and refreshing the transparency report; multi-person approval routing, policy expiry reminders, and browser QA remain. |
| 146 - AI bias audit records | Partial | Fast backend/frontend checks; migration authored | Registered model policies can now produce persisted fairness/bias audit records with audit dimension, population slice, sample size, disparity proxy score, pass/watch/fail/insufficient-data status, severity, findings, recommendations, mitigation status, reviewer provenance, API access, and console audit controls; cohort-level outcome comparisons, automated mitigation, appeal workflows, and browser QA remain. |

## Capability Coverage

Status values:

- `not-started` - no implementation yet.
- `foundation` - core model or boundary exists, but product workflow incomplete.
- `partial` - usable vertical exists, but not full scope.
- `complete` - implemented and verified against product requirements.

| Capability Area | Status | Notes |
| --- | --- | --- |
| Tenant organizations, clubs, schools, associations | partial | Polymorphic membership supports associations, clubs, schools, teams, and people in the tenant graph; organization branding/contact/subdomain fields now feed public branded site profiles and `/site/[slug]` pages with registration inquiry capture. |
| Person identity and athlete profiles | partial | `Person`, `AppUser`, and `AthleteProfile` models added; Keycloak token claims provision `AppUser` identities and bind them to existing `Person` records by verified email before creating new people. |
| Teams, rosters, staff, guardians | partial | Team APIs support team sports and individual sports with captains, vice captains, starters, bench, substitutes, reserves, individual athletes, staff/support roles, and team committees; public site inquiries can now be reviewed, followed up, converted into athlete profiles, roster entries, and guardian links. |
| Events, schedules, attendance | partial | Event scheduling APIs, roster invitation seeding, attendance recording/listing, consent-aware check-in, event weather safety assessments, weather alert dispatch, travel planning/risk workflows, event travel consent generation, guardian travel consent reminders, travel safety manifests, trip fee invoice generation, travel approval workflows, travel inspection checklists, travel tracking updates, and travel expense/reimbursement tracking are implemented. |
| Performance metrics and assessments | partial | Metric definitions, observations with provenance/confidence, ALS-style assessments, summaries, provider-neutral evidence ingestion, pending-review observations, human review/correction, and console workflows are implemented. |
| AI-assisted ingestion and analysis | partial | Agent identity, assignment, task queue, deterministic/webhook task execution with signed worker payloads and signed inbound callbacks, task review, provider-neutral performance evidence ingestion, persisted hash-chained run records, ledger verification, governance summary metrics, credential-boundary status, model transparency reports, formal model registry records, registry approval controls, bias audit records, and console workflows are implemented; live provider workers, OpenBao secret fetch, model-backed extraction, cohort-level outcome comparisons, multi-person approval routing, and deeper model governance remain. |
| Training and coaching plans | partial | Drill library, scoped plans, weekly plan blocks, session load formula, AI-assisted plan generation from readiness/performance/competition context, readiness check-ins, post-session feedback, load-delta recommendations, schedule availability suggestions, and console workflows are implemented; live model generation, external calendar sync, and full verification remain. |
| Competition, fixtures, officials, tournaments | partial | Competition records, participant registration, fixtures/results, officials, match events, standings, round-robin fixture generation, bracket projections, source-round winner advancement, visual bracket lanes, schedule optimization, competition broadcasts, fixture ticketing, conflict detection, and console workflows are implemented; full verification remains. |
| Communications and notifications | partial | Templates, scoped broadcasts, recipient expansion, emergency activation alerts, weather assessment alerts, weather-triggered alert automation, urgent message escalation, travel consent reminders, travel departure/delay/arrival/return notifications, public inquiry follow-up messages, configurable email/SMS/WhatsApp/Telegram/push webhook dispatch, delivery/read callback capture, person inbox, self-service family inbox portal, family athlete consent dashboard, family schedule/clearance view, family event RSVP, family portal consent responses, digest generation, batch digest scheduler trigger, AI-assisted drafts, notification preferences, quiet-hours controls, emergency override, guardian copy for minors, and console workflows are implemented; provider credentials, scheduled consent reminders, real worker/cron execution, scheduled escalation timers, and deeper parent dashboards remain. |
| Consent, safeguarding, compliance, incidents | partial | Guardian relationships, consent requests, one-use web links, SMS/WhatsApp/Telegram/email/manual consent capture, family portal consent responses, minor event clearance, event travel consent request generation and reminders, travel safety manifests with guardian and medical clearance context, background-check tracking, compliance credential renewal tracking, derived compliance dashboards, expiry reconciliation, blocker/renewal/investigation queues, operator incident reporting/triage, emergency activation incident generation, regulatory report packages, incident insurance claim tracking, return-to-play medical clearance, and medical-clearance-aware attendance gating are implemented; real screening-provider integrations, deeper investigation workflows, electronic government portal submission, insurer API submission/status polling, medical portal integrations, richer attendance policy configuration, document exports, scheduled expiry jobs, access-control automation, and provider-sourced risk scoring remain. |
| Equipment, facilities, assets | partial | Facility profiles, emergency action plans and activations, incident command roles, escalation matrices, external agency contacts, emergency alert dispatch from activations, emergency activation incident linkage, equipment inventory, checkout/return, maintenance work orders, booking overlap checks, asset readiness metrics, scan lookup, RFID scan intake/history, RFID reader provisioning and keyed gateway intake, photo metadata, equipment file upload/download through local or MinIO-compatible object storage, procurement recommendations, supplier scorecards, supplier orders/receiving/submission/invoice sync, lease quotes, lease invoice creation, lease payment schedules/installments, lease payment reconciliation with partial installment allocation, utilization recommendations, and console workflows are implemented; mobile emergency UI, automated escalation timers, automated provider delivery, live MinIO smoke, lifecycle policy, live device fleet rollout, supplier-specific adapters, accounting API sync, and full verification remain. |
| Travel and logistics | partial | Event travel plans now cover trip itinerary, transport mode, route, driver/vehicle checks, digital inspection checklists with evidence uploads, manifests, CSV/text offline manifest exports, signed offline manifest links with PDF artifact rendering, mobile manifest offline cache controls with encrypted expiring storage, lodging, meals, equipment, emergency contacts, medical access, consent timing, guardian travel consent request generation, operator-triggered guardian reminders, automated travel consent reminder runs, safety manifests, cost estimates, trip fee invoice generation, hosted travel fee payment pages with provider-neutral settlement intake, signed travel fee payment webhooks with Stripe/M-Pesa/PayPal normalization, travel fee payment reconciliation with derived exceptions, resolution actions, ledger drift repair, and currency mismatch repair, travel fee checkout links with processor-session metadata, approval workflow records, automated approval routing, provider-neutral GPS/location tracking updates, provider-neutral route map payload/rendering, authenticated NDJSON telemetry streaming, hardware GPS/provider ingest with replay protection, nonce expiry policy, provider-specific idempotency windows, travel GPS device provisioning/health tracking, fleet-level GPS inventory, per-device ingest secret rotation with vault-reference custody metadata, departure/delay/arrival/return notifications, ad hoc and persistent geofence breach checks with saved-zone administration, provider-backed geofence polygon storage/checking, trip expense/reimbursement records with receipt uploads, bank/mobile-money payout adapter audit, and payout callback reconciliation, carpool requests/offers, automatic carpool matching with optional coordinate scoring, post-trip driver ratings and summaries, backup driver rosters with automated dispatch, verified driver marketplace matching, departure readiness gating, deterministic route optimization, traffic/weather-aware reroute guidance, risk scoring, and status controls; live map provider routing, live geocoder enrichment, live traffic APIs, live weather-provider reroute geometry, live payment processor redirects, richer branded PDF layouts, live OpenBao secret write/fetch, external driver marketplace inventory, service-worker prefetch, long-lived push workers, and browser streaming/crypto QA remain. |
| Finance, sponsorship, fundraising, ticketing | partial | Sponsors, sponsorship agreements, fundraising campaigns, donations, ticket products/orders/QR tickets/check-in, invoices, trip fee invoices, travel fee checkout links, travel expense reimbursement records with receipt evidence and payout execution, payments, settlement summaries, refunds, tax quotes, accounting exports, sponsorship dashboards, commercial summary, and console workflows are implemented; live payment provider webhooks, hosted checkout sessions, live payout adapters, tax authority filing, accounting API sync, and sponsor-facing dashboards remain. |
| Reports and intelligence | partial | Report definitions, generated reports, scheduled delivery, intelligence insights, predictive risk scores, export jobs, reporting summary, artifact rendering metadata, authenticated PDF/XLSX/CSV/API/HTML artifact download, local or MinIO-compatible artifact persistence, stored artifact URLs, short-lived signed artifact links, verification scoring, chart-ready summaries, visual chart cards, benchmark models, deterministic AI review insights, and console workflows are implemented; real AI model execution, live MinIO smoke/lifecycle policy, visual report QA, deeper chart interactions, and full verification remain. |
| Integrations and webhooks | foundation | Keycloak OIDC bearer-token validation, frontend PKCE session handling, and SpiceDB gRPC authorization adapter are implemented; live service smoke tests and other integrations remain future slices. |
| SaaS billing/subscriptions | partial | Billing plans, tenant subscriptions, usage meters/records, SaaS invoices/payments, entitlements, billing summary, tax quotes, tax filing packages/delivery, proration quotes, plan-change application, dunning notice preparation and webhook delivery, signed payment webhook intake, and console workflows are implemented; full billing verification remains. |
| Beautiful operational UI/UX | partial | First screen is now an operational console with responsive tenant, roster, event, assets, commerce, reports, billing, competition, communications, attendance, performance, training, agent, and safeguarding workflows; branded public organization pages and family portal surfaces are also implemented. |

## Next Actions

1. Run a live Keycloak realm redirect/token/API smoke test for `afrolete-web`
   against the deployed backend auth mode.
2. Run a live SpiceDB schema/write/check smoke test with the OpenBao-managed
   SpiceDB key.
3. Add provider-specific communication credentials, real communication worker
   scheduling, live guardian account mapping, and deeper parent dashboards.
4. Add MinIO-backed equipment storage, live RFID device fleet rollout,
   supplier-specific adapters, accounting API sync, and full verification for
   assets and facilities.
5. Add live payment provider webhooks, tax authority filing, accounting API
   sync, and sponsor-facing dashboard portals.
6. Add MinIO object persistence, lifecycle policy, visual report layout QA,
   deeper chart interactions, live AI-generated insights, and report
   verification coverage.
7. Add full billing verification coverage with provider replay tests,
   tax-filing delivery tests, proration application tests, and browser QA.
8. Add full competition verification for leagues, tournaments, ticketing, broadcasts, and advancement flows.
9. Add live-model training-plan generation, external calendar sync, and full
   training verification.
10. Add real provider parsers for video, audio narration, text evaluation, and
   wearable feeds, plus model-backed extraction accuracy evaluation.
11. Add live AI provider workers, OpenBao secret fetch, persisted run history
   tables, replay protection, audit immutability, and deeper AI governance
   policy controls.
