from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.organization import Organization
from app.models.training import TrainingDrill
from app.schemas.developer import DeveloperApiKeyInspectionRead
from app.schemas.organization import OrganizationRead
from app.schemas.training import TrainingDrillCreate, TrainingDrillRead
from app.services.developer import (
    deliver_developer_webhook_event,
    ensure_developer_api_scope,
    inspect_developer_api_key,
)
from app.services.training import list_training_drills

router = APIRouter(prefix="/sdk", tags=["sdk"])


async def get_sdk_credential(
    request: Request,
    x_afrolete_api_key: str = Header(alias="X-Afrolete-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> DeveloperApiKeyInspectionRead:
    return await inspect_developer_api_key(db, x_afrolete_api_key, request.client.host if request.client else None)


def to_organization_read(organization: Organization) -> OrganizationRead:
    return OrganizationRead(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        organization_type=organization.organization_type,
        association_level=organization.association_level,
        country_code=organization.country_code,
        primary_sport=organization.primary_sport,
        mission=organization.mission,
        public_name=organization.public_name,
        contact_email=organization.contact_email,
        contact_phone=organization.contact_phone,
        website_url=organization.website_url,
        subdomain=organization.subdomain,
        logo_url=organization.logo_url,
        brand_primary_color=organization.brand_primary_color,
        brand_secondary_color=organization.brand_secondary_color,
        my_roles=[],
    )


def to_drill_read(drill: TrainingDrill) -> TrainingDrillRead:
    return TrainingDrillRead(
        id=drill.id,
        organization_id=drill.organization_id,
        sport=drill.sport,
        name=drill.name,
        focus_area=drill.focus_area,
        category=drill.category,
        min_age=drill.min_age,
        max_age=drill.max_age,
        equipment=drill.equipment,
        description=drill.description,
        coaching_points=drill.coaching_points,
        default_duration_minutes=drill.default_duration_minutes,
        default_intensity=drill.default_intensity,
        status=drill.status,
    )


@router.get("/me", response_model=DeveloperApiKeyInspectionRead)
async def sdk_me(
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
) -> DeveloperApiKeyInspectionRead:
    return credential


@router.get("/organization", response_model=OrganizationRead)
async def sdk_organization(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    ensure_developer_api_scope(credential, organization_id, {"read:organization"})
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return to_organization_read(organization)


@router.get("/training/drills", response_model=list[TrainingDrillRead])
async def sdk_list_training_drills(
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingDrillRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:organization", "read:training"})
    return [
        to_drill_read(drill)
        for drill in await list_training_drills(db, organization_id, sport=sport)
    ]


@router.post("/training/drills", response_model=TrainingDrillRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_training_drill(
    payload: TrainingDrillCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingDrillRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:training"})
    drill = TrainingDrill(**payload.model_dump())
    db.add(drill)
    await db.commit()
    await db.refresh(drill)
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "training.drill.created",
        str(drill.id),
        {
            "id": str(drill.id),
            "organization_id": str(drill.organization_id),
            "sport": drill.sport,
            "name": drill.name,
            "focus_area": drill.focus_area,
            "category": drill.category,
            "default_duration_minutes": drill.default_duration_minutes,
            "default_intensity": drill.default_intensity,
        },
    )
    return to_drill_read(drill)
