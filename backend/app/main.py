from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.authz.bootstrap import bootstrap_local_authorization
from app.services.authz.service import get_configured_authorization_service


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AfroLete API",
        version="0.1.0",
        description="Sports operations and athlete-development SaaS API.",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)

    @app.on_event("startup")
    async def startup_local_authorization() -> None:
        if settings.authz_mode != "memory" or not settings.seed_demo:
            return
        async with SessionLocal() as db:
            await bootstrap_local_authorization(db, get_configured_authorization_service())

    return app


app = create_app()
