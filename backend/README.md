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

## Responsibilities

- Domain API and OpenAPI contract.
- PostgreSQL persistence through SQLAlchemy and Alembic.
- Keycloak identity verification.
- SpiceDB authorization checks and relationship writes.
- AI agent identity, tasking, and audit boundaries.
- Background work through Redis and Temporal.
