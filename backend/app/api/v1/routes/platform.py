from fastapi import APIRouter

from app.schemas.platform import Capability, HealthResponse, PlatformSummary

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok", service="afrolete-api", version="0.1.0")


@router.get("/platform", response_model=PlatformSummary)
async def platform_summary() -> PlatformSummary:
    return PlatformSummary(
        product="AfroLete",
        architecture="FastAPI backend, TypeScript frontend, Keycloak, SpiceDB, Postgres",
        capabilities=[
            Capability(
                key="tenant-operations",
                name="Tenant Operations",
                status="foundation",
                description="Organizations, memberships, teams, athletes, guardians, events.",
            ),
            Capability(
                key="ai-agents",
                name="AI Agents",
                status="foundation",
                description="Agents are modeled as governed actors with assignments and tasks.",
            ),
            Capability(
                key="authz",
                name="Resource Authorization",
                status="foundation",
                description="SpiceDB is the intended authorization system for resources.",
            ),
        ],
    )
