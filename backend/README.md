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

Use `--lane agent-tasks`, `--lane developer-webhooks`,
`--lane performance-achievements`, `--lane performance-forecast-validations`,
`--lane performance-review-escalations`,
`--lane performance-injury-risk-alerts`, or `--lane wearable-pull-retries` to
run a single lane. The performance achievement lane evaluates active athlete
goals and recent observations so goal-achieved and personal-best awards are
created without a coach click. Forecast validation can also send scheduled
manager alerts for watch/high drift when run with
`--auto-alert-performance-forecast-drift`; use
`--performance-forecast-drift-channel`,
`--performance-forecast-drift-repeat-after-hours`, and
`--dry-run-performance-forecast-drift-alerts` to tune rollout behavior.

## Responsibilities

- Domain API and OpenAPI contract.
- PostgreSQL persistence through SQLAlchemy and Alembic.
- Keycloak identity verification.
- SpiceDB authorization checks and relationship writes.
- AI agent identity, tasking, and audit boundaries.
- Background work through Redis and Temporal.
