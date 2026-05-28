# Deployment Notes

AfroLete should deploy as separate backend, frontend, and due-worker services.

The backend service reads `/run/pjs/afrolete-backend.env`, rendered by OpenBao
agent. The frontend should receive only public runtime configuration such as API
base URL and Keycloak public client metadata.

The due-worker service also reads `/run/pjs/afrolete-backend.env` and should be
enabled through `afrolete-due-worker.timer`. It runs the unified worker command
for queued agent tasks, daily/weekly communication digest runs, compliance
expiry reconciliation, due travel consent reminders, due developer webhook
retries, performance achievement scans, forecast validation with drift
auto-alerting, assessment review escalations, injury-risk alert scans, and
wearable pull retries, producing JSON logs for the system journal.

Install flow:

```bash
sudo install -m 0644 infra/systemd/afrolete-due-worker.service /etc/systemd/system/
sudo install -m 0644 infra/systemd/afrolete-due-worker.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now afrolete-due-worker.timer
sudo systemctl status afrolete-due-worker.timer
```

After rollout, run a dry smoke with the same environment file before enabling
external delivery channels:

```bash
cd /opt/afrolete/backend
set -a
. /run/pjs/afrolete-backend.env
set +a
./.venv/bin/python -m app.workers.due \
  --limit 5 \
  --auto-alert-performance-forecast-drift \
  --dry-run-event-travel-consent-reminders \
  --dry-run-performance-forecast-drift-alerts \
  --dry-run-performance-injury-risk-alerts \
  --dry-run-performance-review-escalations \
  --pretty
```
