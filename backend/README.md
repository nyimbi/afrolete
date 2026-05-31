# AfroLete Backend

FastAPI backend for AfroLete V2.

## Development

```bash
cd backend
uv sync
createdb afrolete
uv run uvicorn app.main:app --reload
uv run pytest
```

The default local database URL is `postgresql:///afrolete`, matching the
production PostgreSQL target shape while staying easy to type locally. The app
normalizes plain PostgreSQL URLs to the async driver required by FastAPI at
runtime. Unit tests override persistence to an in-memory SQLite database for
fast isolated test runs.

Local development uses `AFROLETE_AUTH_MODE=local`, which accepts explicit
`X-Afrolete-*` identity headers from tests and trusted local tools. Set
`AFROLETE_AUTH_MODE=keycloak` in deployed environments so the API requires a
Bearer token signed by the configured Keycloak realm and audience.

Local development uses `AFROLETE_AUTHZ_MODE=memory` for fast isolated tests.
Set `AFROLETE_AUTHZ_MODE=spicedb` and `AFROLETE_SPICEDB_KEY` in deployed
environments so permission checks and relationship writes go through SpiceDB.

## Workers

Developer webhook retries can run without an operator click:

```bash
cd backend
uv run python -m app.workers.developer_webhooks --limit 100 --max-attempts 5
```

The worker processes queued/failed deliveries whose `next_attempt_at` is due,
honors per-delivery attempt limits, and emits a JSON summary suitable for cron,
Temporal activities, or container job logs.

Queued AI agent tasks can also be executed from a worker:

```bash
cd backend
uv run python -m app.workers.agents --limit 25
```

The agent worker uses the same deterministic/webhook execution mode as the API,
appends the same hash-chained run ledger records, and returns a JSON summary for
schedulers and job logs.

A unified due-worker command runs all currently scheduler-ready lanes:

```bash
cd backend
uv run python -m app.workers.due --limit 25
```

Use `--lane agent-tasks`, `--lane billing-dunning`, `--lane billing-late-fees`, `--lane billing-payment-retries`, `--lane billing-recurring-invoices`, `--lane commercial-grant-alerts`, `--lane communication-digests`,
`--lane communication-escalations`,
`--lane event-travel-consent-reminders`, `--lane emergency-escalations`, `--lane developer-webhooks`,
`--lane insurance-renewal-reminders`,
`--lane member-dues-charges`,
`--lane member-dues-reminders`,
`--lane performance-achievements`, `--lane performance-forecast-validations`,
`--lane performance-review-escalations`, `--lane performance-injury-risk-alerts`,
`--lane performance-video-pose`, or `--lane wearable-pull-retries` to run a
single lane. The billing dunning lane sends repeat-suppressed overdue invoice
notices, records invoice dunning state, and marks subscriptions past due. The
recurring billing lane creates open SaaS invoices for subscriptions whose
`next_billing_on` date is due, advances their service period, and suppresses
duplicate period invoices. The late-fee lane applies configured fixed and/or
percentage fees to overdue open SaaS invoices, records repeat-suppression state,
appends invoice audit notes, and marks active/trial subscriptions past due. The
payment retry lane prepares or dispatches provider retry attempts for overdue
open invoices, records retry attempt state, applies webhook-reported
collections, and marks subscriptions past due while respecting retry windows and
max-attempt limits. The communication digest lane creates daily/weekly digests
for people with matching notification preferences and unread inbox items. The
commercial grant alert lane executes due saved searches, persists run evidence,
updates last-run match counts, and leaves outbound funder/channel delivery to
the later provider integration layer. The insurance renewal lane sends
repeat-suppressed reminders to organization managers for active or expiring
policies inside each policy renewal-notice window; tune with
`--insurance-renewal-reminder-horizon-days`,
`--insurance-renewal-reminder-repeat-after-days`, and
`--dry-run-insurance-renewal-reminders`. The member dues charge lane generates
recurring club-owned receivable charges for due subscription cycles, advances
the subscription period, increments the member balance, and keeps those
receivables separate from AfroLete hosting invoices. Member dues payments
allocate oldest-due first against those charge rows, tracking per-period paid
amount, open balance, paid-at timestamp, last payment id, and receivables aging
summaries for collections decisions. Managers can pause, reactivate, or cancel
member dues accounts, and retired dues plans stop producing future recurring
club receivable charges. Approved waivers reduce open member-dues balances
without recording fake cash and retain waiver reason, timestamp, and approving
person on the charge. Member dues statements assemble charges, successful
payments, and waivers into shareable running-balance account evidence, and can
be exported as text or CSV artifacts with checksum and download filename
metadata or sent through the communications system to members and guardians;
tune with
`--member-dues-charge-on` and `--dry-run-member-dues-charges`. The member dues
reminder lane sends repeat-suppressed reminders for due or overdue
club-managed subscription balances, marks accounts past due after the plan
grace period, and keeps those receivables separate from AfroLete hosting
invoices; tune with
`--member-dues-reminder-due-within-days`,
`--member-dues-reminder-repeat-after-days`, and
`--dry-run-member-dues-reminders`. The
communication escalation lane scans unresolved urgent messages and creates
quiet-hours-override escalation messages with repeat suppression. The travel consent lane sends scheduled
guardian reminders for due travel consent requests and suppresses repeats with
`--event-travel-consent-reminder-repeat-after-hours`. The emergency escalation
lane advances active emergency activations after
`--emergency-escalation-unresolved-after-minutes` and suppresses repeats with
`--emergency-escalation-repeat-after-minutes`. The performance
achievement lane evaluates active athlete goals and recent observations so
goal-achieved and personal-best awards are created without a coach click.
Forecast validation can also send scheduled manager alerts for watch/high drift
when run with
`--auto-alert-performance-forecast-drift`; use
`--performance-forecast-drift-channel`,
`--performance-forecast-drift-repeat-after-hours`, and
`--dry-run-performance-forecast-drift-alerts` to tune rollout behavior.

The video pose worker decodes stored performance video files with OpenCV, runs
the configured MediaPipe pose model, normalizes pose landmarks to the
provider-neutral keypoint schema, and can post the resulting batch through the
same `/api/v1/performance/videos/{video_asset_id}/pose-samples` endpoint used
by external providers:

```bash
cd backend
uv run python -m app.workers.video_pose \
  --limit 10 \
  --max-frames 45 \
  --sample-every-seconds 0.2 \
  --api-base-url http://127.0.0.1:8000 \
  --local-auth-sub kc-owner-1 \
  --local-auth-email owner@example.com
```

Omit `--api-base-url` to store extracted samples in-process through the same
domain service. Add `--video-asset-id <uuid>` to process one stored clip for a
manual retry or a controlled demo. Use bearer-token headers in Keycloak
deployments and local `X-Afrolete-*` headers only for trusted local/demo runs.

Training plan generation defaults to deterministic local planning. To hand
planning off to a live model worker, set:

```bash
AFROLETE_TRAINING_PLAN_GENERATION_MODE=webhook
AFROLETE_TRAINING_PLAN_GENERATION_MODEL=afrolete-training-planner-v1
AFROLETE_TRAINING_PLAN_GENERATION_WEBHOOK_URL=https://models.example/training-plan
AFROLETE_TRAINING_PLAN_GENERATION_WEBHOOK_KEY_SECRET_PATH=secret/data/afrolete/training
AFROLETE_TRAINING_PLAN_GENERATION_WEBHOOK_KEY_SECRET_FIELD=webhook_key
```

The backend signs the canonical JSON payload with
`X-Afrolete-Training-Signature` and falls back to deterministic planning with
provider metadata in the response if the provider is unavailable.

Reporting insight generation also defaults to deterministic local review. To
send reporting/risk context to a live model worker, set:

```bash
AFROLETE_REPORTING_INSIGHT_GENERATION_MODE=webhook
AFROLETE_REPORTING_INSIGHT_GENERATION_MODEL=afrolete-reporting-insight-v1
AFROLETE_REPORTING_INSIGHT_GENERATION_WEBHOOK_URL=https://models.example/reporting-insight
AFROLETE_REPORTING_INSIGHT_GENERATION_WEBHOOK_KEY_SECRET_PATH=secret/data/afrolete/reporting
AFROLETE_REPORTING_INSIGHT_GENERATION_WEBHOOK_KEY_SECRET_FIELD=webhook_key
```

The backend signs the canonical JSON payload with
`X-Afrolete-Reporting-Signature` and records provider references in the
generated insight evidence while retaining deterministic fallback behavior.

## Responsibilities

- Domain API and OpenAPI contract.
- PostgreSQL persistence through SQLAlchemy and Alembic.
- Keycloak identity verification.
- SpiceDB authorization checks and relationship writes.
- AI agent identity, tasking, and audit boundaries.
- Background work through Redis and Temporal.
