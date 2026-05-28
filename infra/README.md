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

Override `AFROLETE_DUE_WORKER_LIMIT` or
`AFROLETE_DUE_WORKER_WEBHOOK_MAX_ATTEMPTS` in the service environment if a
tenant needs a higher batch size or retry ceiling. Override
`AFROLETE_DUE_WORKER_PERFORMANCE_LIMIT` to tune automated performance
goal/achievement scans independently from webhook retries.
