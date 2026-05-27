from fastapi import APIRouter

from app.api.v1.routes import agents
from app.api.v1.routes import events
from app.api.v1.routes import organizations
from app.api.v1.routes import platform
from app.api.v1.routes import performance
from app.api.v1.routes import safeguarding
from app.api.v1.routes import teams

api_router = APIRouter()
api_router.include_router(platform.router, tags=["platform"])
api_router.include_router(agents.router)
api_router.include_router(events.router)
api_router.include_router(organizations.router)
api_router.include_router(performance.router)
api_router.include_router(safeguarding.router)
api_router.include_router(teams.router)
