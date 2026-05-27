# AfroLete

AfroLete is being rebuilt as a V2 platform with:

- FastAPI Python backend in `backend/`
- TypeScript frontend in `frontend/`
- PJS shared infrastructure configuration in `infra/`
- Product and architecture source material in `docs/`

The surviving `docs/` directory is the product scope source of truth. New
implementation should proceed from the V2 architecture notes and avoid reviving
the deleted full-stack prototype structure.

## Repository Layout

```text
backend/   FastAPI service, SQLAlchemy/Alembic, workers, backend tests
frontend/  TypeScript frontend application
infra/     Keycloak, OpenBao, SpiceDB, Postgres, MinIO, Temporal, deploy config
docs/      Product requirements, architecture notes, ADRs, retained source docs
scripts/   Project automation entrypoints
tools/     Development utilities
tests/     Cross-service and end-to-end tests
```

## Infrastructure Direction

Production targets the PJS shared services:

- PostgreSQL database `afrolete` on `db.lindela.io`
- Keycloak realm `lindela` at `https://auth.lindela.io/realms/lindela`
- SpiceDB for authorization relationships
- OpenBao for secrets delivery
- Redis, Temporal, and MinIO on the shared PJS infrastructure

Do not commit secrets. Production credentials should be rendered from OpenBao or
provided through environment files outside git.

