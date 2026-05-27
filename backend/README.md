# AfroLete Backend

FastAPI backend for AfroLete V2.

## Development

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
```

## Responsibilities

- Domain API and OpenAPI contract.
- PostgreSQL persistence through SQLAlchemy and Alembic.
- Keycloak identity verification.
- SpiceDB authorization checks and relationship writes.
- AI agent identity, tasking, and audit boundaries.
- Background work through Redis and Temporal.

