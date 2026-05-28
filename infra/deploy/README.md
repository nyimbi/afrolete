# Deployment Notes

AfroLete should deploy as separate backend, frontend, and due-worker services.

The backend service reads `/run/pjs/afrolete-backend.env`, rendered by OpenBao
agent. The frontend should receive only public runtime configuration such as API
base URL and Keycloak public client metadata.

The due-worker service also reads `/run/pjs/afrolete-backend.env` and should be
enabled through `afrolete-due-worker.timer`. It runs the unified worker command
for queued agent tasks and due developer webhook retries, producing JSON logs
for the system journal.
