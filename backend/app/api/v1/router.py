from fastapi import APIRouter

from app.api.v1.routes import organizations
from app.api.v1.routes import platform
from app.api.v1.routes import teams

api_router = APIRouter()
api_router.include_router(platform.router, tags=["platform"])
api_router.include_router(organizations.router)
api_router.include_router(teams.router)
