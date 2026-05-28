from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import MemberSubjectType
from app.models.event import Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.team import AthleteProfile, Team, TeamRosterEntry
from app.models.training import TrainingDrill
from app.schemas.developer import (
    DeveloperApiKeyInspectionRead,
    DeveloperPersonCreate,
    DeveloperPersonRead,
)
from app.schemas.event import EventCreate, EventRead
from app.schemas.organization import OrganizationRead
from app.schemas.team import TeamCreate, TeamMemberAdd, TeamRead, TeamRosterEntryRead
from app.schemas.training import TrainingDrillCreate, TrainingDrillRead
from app.services.authz.service import (
    AuthorizationService,
    Relationship,
    get_authorization_service,
)
from app.services.developer import (
    deliver_developer_webhook_event,
    ensure_developer_api_scope,
    inspect_developer_api_key,
)
from app.services.events import list_events
from app.services.organizations import organization_member_relation
from app.services.teams import list_teams_for_organization, team_member_relation
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


def to_developer_person_read(
    person: Person,
    organization_id: UUID,
    membership: Membership | None,
) -> DeveloperPersonRead:
    return DeveloperPersonRead(
        id=person.id,
        organization_id=organization_id,
        membership_id=membership.id if membership is not None else None,
        display_name=person.display_name,
        given_name=person.given_name,
        family_name=person.family_name,
        date_of_birth=person.date_of_birth,
        primary_email=person.primary_email,
        primary_phone=person.primary_phone,
        country_code=person.country_code,
        notes=person.notes,
        membership_role=membership.role if membership is not None else None,
        membership_title=membership.title if membership is not None else None,
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


@router.post("/people", response_model=DeveloperPersonRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_person(
    payload: DeveloperPersonCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperPersonRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:people", "write:roster"})
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    person = None
    if payload.primary_email is not None:
        person = await db.scalar(select(Person).where(Person.primary_email == payload.primary_email))
    if person is None:
        person = Person(
            display_name=payload.display_name,
            given_name=payload.given_name,
            family_name=payload.family_name,
            date_of_birth=payload.date_of_birth,
            primary_email=payload.primary_email,
            primary_phone=payload.primary_phone,
            country_code=payload.country_code,
            notes=payload.notes,
        )
        db.add(person)
        await db.flush()
    else:
        person.display_name = person.display_name or payload.display_name
        person.given_name = person.given_name or payload.given_name
        person.family_name = person.family_name or payload.family_name
        person.date_of_birth = person.date_of_birth or payload.date_of_birth
        person.primary_phone = person.primary_phone or payload.primary_phone
        person.country_code = person.country_code or payload.country_code
        person.notes = person.notes or payload.notes

    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person.id,
            Membership.role == payload.membership_role,
        )
    )
    if membership is None:
        membership = Membership(
            organization_id=payload.organization_id,
            subject_type=MemberSubjectType.PERSON,
            subject_id=person.id,
            role=payload.membership_role,
            title=payload.membership_title,
        )
        db.add(membership)
        await authz.touch(
            Relationship(
                resource_type="organization",
                resource_id=str(payload.organization_id),
                relation=organization_member_relation(
                    MemberSubjectType.PERSON,
                    payload.membership_role,
                ),
                subject_type="person",
                subject_id=str(person.id),
            )
        )
    await db.commit()
    await db.refresh(person)
    if membership is not None:
        await db.refresh(membership)
    return to_developer_person_read(person, payload.organization_id, membership)


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


@router.post(
    "/teams/{team_id}/members",
    response_model=TeamRosterEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_add_team_member(
    team_id: UUID,
    payload: TeamMemberAdd,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamRosterEntryRead:
    team = await db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    ensure_developer_api_scope(credential, team.organization_id, {"write:roster", "write:teams"})
    person = await db.get(Person, payload.person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    athlete_profile = await db.scalar(
        select(AthleteProfile).where(
            AthleteProfile.organization_id == team.organization_id,
            AthleteProfile.person_id == payload.person_id,
        )
    )
    if athlete_profile is None:
        athlete_profile = AthleteProfile(
            organization_id=team.organization_id,
            person_id=payload.person_id,
        )
        db.add(athlete_profile)
        await db.flush()
    roster_entry = await db.scalar(
        select(TeamRosterEntry).where(
            TeamRosterEntry.team_id == team_id,
            TeamRosterEntry.athlete_profile_id == athlete_profile.id,
        )
    )
    if roster_entry is None:
        roster_entry = TeamRosterEntry(
            team_id=team_id,
            athlete_profile_id=athlete_profile.id,
            role=payload.role,
            status=payload.status,
            primary_position=payload.primary_position,
            jersey_number=payload.jersey_number,
            is_captain=payload.is_captain,
        )
        db.add(roster_entry)
        await authz.touch(
            Relationship(
                resource_type="team",
                resource_id=str(team_id),
                relation=team_member_relation(payload.role),
                subject_type="person",
                subject_id=str(payload.person_id),
            )
        )
        await db.commit()
        await db.refresh(roster_entry)
    return TeamRosterEntryRead(
        id=roster_entry.id,
        team_id=roster_entry.team_id,
        athlete_profile_id=roster_entry.athlete_profile_id,
        role=roster_entry.role,
        primary_position=roster_entry.primary_position,
        jersey_number=roster_entry.jersey_number,
        is_captain=roster_entry.is_captain,
        status=roster_entry.status,
    )


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
