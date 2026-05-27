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

The default local database URL is `postgresql+asyncpg:///afrolete`, matching the
production PostgreSQL target shape. Unit tests override persistence to an
in-memory SQLite database for fast isolated test runs.

## Responsibilities

- Domain API and OpenAPI contract.
- PostgreSQL persistence through SQLAlchemy and Alembic.
- Keycloak identity verification.
- SpiceDB authorization checks and relationship writes.
- AI agent identity, tasking, and audit boundaries.
- Background work through Redis and Temporal.
