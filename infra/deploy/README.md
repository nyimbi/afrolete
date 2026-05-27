# Deployment Notes

AfroLete should deploy as separate backend and frontend services.

The backend service reads `/run/pjs/afrolete-backend.env`, rendered by OpenBao
agent. The frontend should receive only public runtime configuration such as API
base URL and Keycloak public client metadata.

