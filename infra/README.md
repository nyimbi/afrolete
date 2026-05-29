# AfroLete Infrastructure

Deployment artifacts for the PJS shared-services environment.

## Target Services

| Service | Target | Purpose |
| --- | --- | --- |
| PostgreSQL | `db.lindela.io:5432` | Primary domain database `afrolete`. |
| Keycloak | `https://auth.lindela.io/realms/lindela` | Human and service identity. |
| SpiceDB | `62.84.181.55:50051` | Resource-level authorization. |
| OpenBao | `https://vault.lindela.io` | Secret delivery to services. |
| Redis | shared PJS Redis | Cache and lightweight queue coordination. |
| Temporal | `62.84.181.55:7233` | Durable workflows, namespace `afrolete`. |
| MinIO | shared PJS MinIO | Object storage for media, imports, reports. |

## Setup Order

1. For local development, create `postgresql:///afrolete` with `createdb
   afrolete`; for PJS deployment, create the PostgreSQL role/database with
   `infra/postgres/create-afrolete.sql`.
2. Apply SpiceDB schema in `infra/spicedb/afrolete.zed`.
3. Create Keycloak clients described in `infra/keycloak/README.md`.
4. Create OpenBao policy/agent files from `infra/openbao/`.
5. Create Temporal namespace and MinIO bucket.
6. Deploy backend, frontend, and due-worker systemd units.

## Background Workers

`infra/systemd/afrolete-due-worker.service` runs the unified Python due-worker
command against the same OpenBao-rendered `/run/pjs/afrolete-backend.env` file
as the FastAPI backend. `infra/systemd/afrolete-due-worker.timer` starts it once
per minute by default.

Install both unit files on the target host, then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now afrolete-due-worker.timer
sudo systemctl list-timers afrolete-due-worker.timer
```

The service runs all scheduler-ready lanes and turns on forecast-drift
auto-alerting by default for in-app manager alerts. Override these variables in
a systemd drop-in when a tenant needs different throughput or alert policy:

| Variable | Default | Purpose |
| --- | --- | --- |
| `AFROLETE_DUE_WORKER_LIMIT` | `25` | Default batch size for lanes without a narrower limit. |
| `AFROLETE_DUE_WORKER_BILLING_RECURRING_INVOICE_LIMIT` | `100` | Subscriptions scanned for due recurring SaaS invoices. |
| `AFROLETE_DUE_WORKER_BILLING_RECURRING_INVOICE_DUE_IN_DAYS` | `14` | Payment due-date offset for generated recurring SaaS invoices. |
| `AFROLETE_DUE_WORKER_BILLING_RECURRING_INVOICE_PREFIX` | `SAAS` | Invoice-number prefix for scheduler-generated SaaS invoices. |
| `AFROLETE_DUE_WORKER_COMMUNICATION_DIGEST_LIMIT` | `100` | Daily/weekly notification preferences processed per digest run. |
| `AFROLETE_DUE_WORKER_COMMUNICATION_ESCALATION_LIMIT` | `100` | Urgent communication messages scanned for scheduled escalation. |
| `AFROLETE_DUE_WORKER_COMMUNICATION_ESCALATION_UNRESOLVED_AFTER_MINUTES` | `15` | Time an urgent message may remain queued, failed, or suppressed before escalation. |
| `AFROLETE_DUE_WORKER_COMMUNICATION_ESCALATION_REPEAT_AFTER_MINUTES` | `60` | Suppression window for repeated escalation of the same urgent message. |
| `AFROLETE_DUE_WORKER_COMMUNICATION_ESCALATION_LEVEL` | `2` | Default escalation level stamped onto scheduled escalation messages. |
| `AFROLETE_DUE_WORKER_COMMUNICATION_ESCALATION_CHANNEL` | `sms` | Default alternate escalation channel. |
| `AFROLETE_DUE_WORKER_COMPLIANCE_RECONCILIATION_LIMIT` | `100` | Organizations scanned for expired checks and credential renewals per run. |
| `AFROLETE_DUE_WORKER_EVENT_TRAVEL_CONSENT_REMINDER_LIMIT` | `50` | Travel events checked for due guardian consent reminders. |
| `AFROLETE_DUE_WORKER_EVENT_TRAVEL_CONSENT_REMINDER_DUE_WITHIN_HOURS` | `48` | Reminder horizon for travel plans with approaching consent deadlines. |
| `AFROLETE_DUE_WORKER_EVENT_TRAVEL_CONSENT_REMINDER_REPEAT_AFTER_HOURS` | `24` | Suppression window for repeated scheduled travel consent reminders. |
| `AFROLETE_DUE_WORKER_EVENT_TRAVEL_CONSENT_REMINDER_CHANNEL` | `email` | Default scheduled travel consent reminder channel. |
| `AFROLETE_DUE_WORKER_EMERGENCY_ESCALATION_LIMIT` | `50` | Active emergency activations scanned for timer escalation. |
| `AFROLETE_DUE_WORKER_EMERGENCY_ESCALATION_UNRESOLVED_AFTER_MINUTES` | `15` | Time an emergency activation may remain active before timer escalation. |
| `AFROLETE_DUE_WORKER_EMERGENCY_ESCALATION_REPEAT_AFTER_MINUTES` | `15` | Suppression window for repeated escalation of the same emergency activation. |
| `AFROLETE_DUE_WORKER_WEBHOOK_MAX_ATTEMPTS` | `5` | Developer webhook retry ceiling. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_LIMIT` | `25` | Shared performance-lane fallback limit. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_FORECAST_VALIDATION_LIMIT` | `25` | Forecast validation organizations per run. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_FORECAST_DRIFT_REPEAT_AFTER_HOURS` | `24` | Suppression window for repeated drift alerts. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_FORECAST_DRIFT_CHANNEL` | `in_app` | Drift alert channel. Use a drop-in ExecStart override for multiple channels. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_REVIEW_LIMIT` | `25` | Assessment review escalation scan limit. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_REVIEW_HORIZON_HOURS` | `24` | Due-soon review escalation horizon. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_REVIEW_REPEAT_AFTER_HOURS` | `24` | Review escalation repeat suppression window. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_INJURY_RISK_LIMIT` | `25` | Injury-risk profiles scanned per run. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_INJURY_RISK_THRESHOLD` | `65` | Minimum risk score for urgent alerts. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_INJURY_RISK_REPEAT_AFTER_HOURS` | `24` | Injury-risk alert repeat suppression window. |
| `AFROLETE_DUE_WORKER_PERFORMANCE_INJURY_RISK_CHANNEL` | `in_app` | Injury-risk alert channel. Use a drop-in ExecStart override for multiple channels. |
| `AFROLETE_DUE_WORKER_WEARABLE_PULL_LIMIT` | `25` | Wearable retry candidates per run. |
| `AFROLETE_DUE_WORKER_WEARABLE_PULL_MAX_PAGES` | `3` | Max provider pages retried per wearable connection. |
| `AFROLETE_DUE_WORKER_WEARABLE_PULL_DEFAULT_RETRY_AFTER_SECONDS` | `300` | Backoff when a provider omits `Retry-After`. |

For a deployment smoke without sending messages, run the command manually with
`--dry-run-communication-escalations`,
`--dry-run-billing-recurring-invoices`,
`--dry-run-emergency-escalations`,
`--dry-run-performance-forecast-drift-alerts`,
`--dry-run-performance-injury-risk-alerts`, and
`--dry-run-performance-review-escalations`, then inspect the JSON summary and
`journalctl -u afrolete-due-worker.service`.
