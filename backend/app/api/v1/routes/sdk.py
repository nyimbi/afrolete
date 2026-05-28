from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import Event
from app.models.organization import Organization
from app.models.team import Team
from app.models.training import TrainingDrill
from app.schemas.developer import DeveloperApiKeyInspectionRead
from app.schemas.event import EventCreate, EventRead
from app.schemas.organization import OrganizationRead
from app.schemas.team import TeamCreate, TeamRead
from app.schemas.training import TrainingDrillCreate, TrainingDrillRead
from app.services.authz.service import AuthorizationService, Relationship, get_authorization_service
from app.services.developer import (
    deliver_developer_webhook_event,
    ensure_developer_api_scope,
    inspect_developer_api_key,
)
from app.services.events import list_events
from app.services.teams import list_teams_for_organization
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


def to_event_read(event: Event) -> EventRead:
    return EventRead(
        id=event.id,
        organization_id=event.organization_id,
        team_id=event.team_id,
        event_type=event.event_type,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        timezone=event.timezone,
        venue_name=event.venue_name,
        notes=event.notes,
    )


def to_team_read(team: Team) -> TeamRead:
    return TeamRead(
        id=team.id,
        organization_id=team.organization_id,
        name=team.name,
        sport=team.sport,
        sport_format=team.sport_format,
        age_group=team.age_group,
        gender_category=team.gender_category,
        season_label=team.season_label,
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


@router.get("/events", response_model=list[EventRead])
async def sdk_list_events(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[EventRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:events", "write:events"})
    return [to_event_read(event) for event in await list_events(db, organization_id, team_id=team_id)]


@router.get("/teams", response_model=list[TeamRead])
async def sdk_list_teams(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TeamRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:organization", "read:teams"})
    return [to_team_read(team) for team in await list_teams_for_organization(db, organization_id)]


@router.post("/teams", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_team(
    payload: TeamCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:teams"})
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    team = Team(**payload.model_dump())
    db.add(team)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="organization",
            resource_id=str(payload.organization_id),
            relation="member_team",
            subject_type="team",
            subject_id=str(team.id),
        )
    )
    await db.commit()
    await db.refresh(team)
    return to_team_read(team)


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_event(
    payload: EventCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> EventRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:events"})
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found for organization")
    event = Event(**payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "events.created",
        str(event.id),
        {
            "id": str(event.id),
            "organization_id": str(event.organization_id),
            "team_id": str(event.team_id) if event.team_id else None,
            "event_type": event.event_type.value,
            "title": event.title,
            "starts_at": event.starts_at.isoformat(),
            "source": "developer_api",
        },
    )
    return to_event_read(event)


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
