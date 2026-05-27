from fastapi import APIRouter

from app.api.v1.routes import agents
from app.api.v1.routes import assets
from app.api.v1.routes import billing
from app.api.v1.routes import commercial
from app.api.v1.routes import communications
from app.api.v1.routes import competitions
from app.api.v1.routes import events
from app.api.v1.routes import organizations
from app.api.v1.routes import platform
from app.api.v1.routes import performance
from app.api.v1.routes import reporting
from app.api.v1.routes import safeguarding
from app.api.v1.routes import teams
from app.api.v1.routes import training

api_router = APIRouter()
api_router.include_router(platform.router, tags=["platform"])
api_router.include_router(agents.router)
api_router.include_router(assets.router)
api_router.include_router(billing.router)
api_router.include_router(commercial.router)
api_router.include_router(communications.router)
api_router.include_router(competitions.router)
api_router.include_router(events.router)
api_router.include_router(organizations.router)
api_router.include_router(performance.router)
api_router.include_router(reporting.router)
api_router.include_router(safeguarding.router)
api_router.include_router(teams.router)
api_router.include_router(training.router)
