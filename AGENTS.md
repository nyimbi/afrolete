# AfroLete Agent Instructions

This repository is the V2 rebuild. The old full-stack prototype has been
removed from this working tree; `docs/` is the retained product scope source.

## Architecture

- Backend: FastAPI Python service in `backend/`.
- Frontend: TypeScript UI in `frontend/`.
- Infrastructure: PJS deployment config in `infra/`.
- Authn: Keycloak shared `lindela` realm.
- Authz: SpiceDB relationship and permission model.
- Secrets: OpenBao; never commit real credentials.
- Database: PostgreSQL database/user `afrolete` on `db.lindela.io`.

## Working Rules

- Keep new implementation in the V2 directories; do not recreate the deleted
  root-level Next.js full-stack app.
- Prefer small, reversible commits with tests or verification evidence.
- Use Alembic for backend schema changes.
- Keep frontend business logic thin; backend owns persistence, authz, workers,
  and domain rules.
- Treat `docs/prd.md` and `docs/ext*.md` as product inputs, not generated code
  to rewrite casually.

