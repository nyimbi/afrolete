from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.team import (
    TeamCommitteeCreate,
    TeamCommitteeMemberAdd,
    TeamCommitteeMembershipRead,
    TeamCommitteeRead,
    TeamCreate,
    TeamMemberAdd,
    TeamRead,
    TeamRosterEntryRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.teams import (
    add_team_committee_member,
    add_team_member,
    create_team,
    create_team_committee,
    list_teams_for_organization,
)

router = APIRouter(prefix="/teams", tags=["teams"])


def to_team_read(team) -> TeamRead:
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


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team_route(
    payload: TeamCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamRead:
    return to_team_read(await create_team(db, identity, payload, authz))


@router.get("/by-organization/{organization_id}", response_model=list[TeamRead])
async def list_organization_teams_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[TeamRead]:
    return [to_team_read(team) for team in await list_teams_for_organization(db, organization_id)]


@router.post("/{team_id}/members", response_model=TeamRosterEntryRead, status_code=201)
async def add_team_member_route(
    team_id: UUID,
    payload: TeamMemberAdd,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamRosterEntryRead:
    roster_entry = await add_team_member(db, identity, team_id, payload, authz)
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


def to_team_committee_read(committee) -> TeamCommitteeRead:
    return TeamCommitteeRead(
        id=committee.id,
        team_id=committee.team_id,
        name=committee.name,
        mandate=committee.mandate,
        status=committee.status,
    )


@router.post("/{team_id}/committees", response_model=TeamCommitteeRead, status_code=201)
async def create_team_committee_route(
    team_id: UUID,
    payload: TeamCommitteeCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamCommitteeRead:
    return to_team_committee_read(
        await create_team_committee(db, identity, team_id, payload, authz)
    )


@router.post(
    "/committees/{team_committee_id}/members",
    response_model=TeamCommitteeMembershipRead,
    status_code=201,
)
async def add_team_committee_member_route(
    team_committee_id: UUID,
    payload: TeamCommitteeMemberAdd,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamCommitteeMembershipRead:
    membership = await add_team_committee_member(db, identity, team_committee_id, payload, authz)
    return TeamCommitteeMembershipRead(
        id=membership.id,
        team_committee_id=membership.team_committee_id,
        person_id=membership.person_id,
        role=membership.role,
        title=membership.title,
        status=membership.status,
    )
