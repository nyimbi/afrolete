# Docker Demo

AfroLete can run as a local demo stack with PostgreSQL, FastAPI, Next.js, and
the unified due-worker.

## Start

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Mobile emergency console: http://localhost:3000/emergency?slug=demo-city-fc
- Public branded site: http://localhost:3000/site/demo-city-fc
- Sponsor portal: http://localhost:3000/sponsors
- Backend health: http://localhost:8000/api/v1/healthz
- OpenAPI: http://localhost:8000/api/v1/openapi.json

The backend runs Alembic migrations and seeds a local demo tenant on startup
when `AFROLETE_SEED_DEMO=1`.

## Sponsor Payment Walkthrough

1. Open http://localhost:3000/sponsors.
2. Keep the default sponsor identity (`sponsor@example.com`) and choose
   **Open portal**.
3. Select the seeded sponsor invoice and choose **Pay balance**.
4. Confirm payment on the hosted AfroLete payment page.

The local demo uses a provider-neutral `manual_gateway` settlement path so the
invoice balance, sponsor portal, and finance ledger update without external
payment credentials.

If the frontend URL shows a different application, another local process is
already listening on port 3000. Stop that process and recreate the frontend
container:

```bash
docker compose up -d --force-recreate frontend
```

## Demo Identity

The frontend defaults to local identity headers:

- Subject: `kc-owner-1`
- Email: `owner@example.com`
- Name: `Owner Example`

The sponsor portal defaults to the seeded sponsor contact:

- Subject: `kc-sponsor-1`
- Email: `sponsor@example.com`
- Name: `Sponsor Example`

The demo seed creates the matching user, person, owner membership, Demo City FC
tenant, team, minor athlete, guardian, travel consent request, travel plan,
performance observations, public sponsor, sponsorship agreement, sponsor
invoice, inbox item, notification preference, and AI agent task.

## Worker

The `due-worker` container runs the unified worker once per minute with local
record-only delivery. It exercises scheduler-ready behavior such as
scheduled SaaS dunning, automated SaaS late fees, SaaS payment retries, recurring SaaS invoices, communication digests, travel consent reminders,
performance forecast drift alerts, performance review escalations, injury-risk
scans, achievement scans, emergency escalation timers, developer webhook
retries, agent tasks, and wearable retry scans when matching data exists.

## Reset

```bash
docker compose down -v
docker compose up --build
```

This drops the local PostgreSQL volume and recreates the seeded demo tenant.
