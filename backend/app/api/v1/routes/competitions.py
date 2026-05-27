from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.competition import (
    CompetitionCreate,
    CompetitionFixtureCreate,
    CompetitionFixtureRead,
    CompetitionParticipantCreate,
    CompetitionParticipantRead,
    CompetitionRead,
    CompetitionStandingRead,
    FixtureMatchEventCreate,
    FixtureMatchEventRead,
    FixtureOfficialAssignmentCreate,
    FixtureOfficialAssignmentRead,
    FixtureResultUpdate,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.competitions import (
    add_competition_participant,
    assign_fixture_official,
    competition_standings,
    create_competition,
    create_competition_fixture,
    list_competition_fixtures,
    list_competition_participants,
    list_competitions,
    list_fixture_match_events,
    record_fixture_match_event,
    update_fixture_result,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])


def to_competition_read(competition) -> CompetitionRead:
    return CompetitionRead(
        id=competition.id,
        organization_id=competition.organization_id,
        name=competition.name,
        sport=competition.sport,
        competition_type=competition.competition_type,
        format=competition.format,
        season_label=competition.season_label,
        starts_on=competition.starts_on,
        ends_on=competition.ends_on,
        status=competition.status,
        points_for_win=competition.points_for_win,
        points_for_draw=competition.points_for_draw,
        points_for_loss=competition.points_for_loss,
        tiebreakers=competition.tiebreakers,
        rules_summary=competition.rules_summary,
    )


def to_participant_read(participant, team) -> CompetitionParticipantRead:
    return CompetitionParticipantRead(
        id=participant.id,
        competition_id=participant.competition_id,
        team_id=participant.team_id,
        team_name=team.name,
        seed=participant.seed,
        group_label=participant.group_label,
        status=participant.status,
    )


def to_fixture_read(row) -> CompetitionFixtureRead:
    fixture, home_team_name, away_team_name = row
    return CompetitionFixtureRead(
        id=fixture.id,
        organization_id=fixture.organization_id,
        competition_id=fixture.competition_id,
        event_id=fixture.event_id,
        home_team_id=fixture.home_team_id,
        away_team_id=fixture.away_team_id,
        home_team_name=home_team_name,
        away_team_name=away_team_name,
        round_label=fixture.round_label,
        stage_label=fixture.stage_label,
        scheduled_at=fixture.scheduled_at,
        venue_name=fixture.venue_name,
        status=fixture.status,
        home_score=fixture.home_score,
        away_score=fixture.away_score,
        result_confirmed_at=fixture.result_confirmed_at,
        notes=fixture.notes,
    )


def to_official_assignment_read(assignment) -> FixtureOfficialAssignmentRead:
    return FixtureOfficialAssignmentRead(
        id=assignment.id,
        fixture_id=assignment.fixture_id,
        person_id=assignment.person_id,
        role=assignment.role,
        status=assignment.status,
        certification_level=assignment.certification_level,
        conflict_notes=assignment.conflict_notes,
    )


def to_match_event_read(match_event) -> FixtureMatchEventRead:
    return FixtureMatchEventRead(
        id=match_event.id,
        fixture_id=match_event.fixture_id,
        team_id=match_event.team_id,
        athlete_profile_id=match_event.athlete_profile_id,
        minute=match_event.minute,
        event_type=match_event.event_type,
        description=match_event.description,
    )


@router.post("", response_model=CompetitionRead, status_code=status.HTTP_201_CREATED)
async def create_competition_route(
    payload: CompetitionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CompetitionRead:
    return to_competition_read(await create_competition(db, identity, payload, authz))


@router.get("", response_model=list[CompetitionRead])
async def list_competitions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[CompetitionRead]:
    return [
        to_competition_read(competition)
        for competition in await list_competitions(db, organization_id)
    ]


@router.post(
    "/{competition_id}/participants",
    response_model=CompetitionParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_competition_participant_route(
    competition_id: UUID,
    payload: CompetitionParticipantCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CompetitionParticipantRead:
    participant = await add_competition_participant(db, identity, competition_id, payload, authz)
    participants = await list_competition_participants(db, competition_id)
    team = next(team for item, team in participants if item.id == participant.id)
    return to_participant_read(participant, team)


@router.get("/{competition_id}/participants", response_model=list[CompetitionParticipantRead])
async def list_competition_participants_route(
    competition_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CompetitionParticipantRead]:
    return [
        to_participant_read(participant, team)
        for participant, team in await list_competition_participants(db, competition_id)
    ]


@router.post(
    "/{competition_id}/fixtures",
    response_model=CompetitionFixtureRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_competition_fixture_route(
    competition_id: UUID,
    payload: CompetitionFixtureCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CompetitionFixtureRead:
    fixture = await create_competition_fixture(db, identity, competition_id, payload, authz)
    rows = await list_competition_fixtures(db, competition_id)
    return to_fixture_read(next(row for row in rows if row[0].id == fixture.id))


@router.get("/{competition_id}/fixtures", response_model=list[CompetitionFixtureRead])
async def list_competition_fixtures_route(
    competition_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CompetitionFixtureRead]:
    return [to_fixture_read(row) for row in await list_competition_fixtures(db, competition_id)]


@router.patch("/fixtures/{fixture_id}/result", response_model=CompetitionFixtureRead)
async def update_fixture_result_route(
    fixture_id: UUID,
    payload: FixtureResultUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CompetitionFixtureRead:
    fixture = await update_fixture_result(db, identity, fixture_id, payload, authz)
    rows = await list_competition_fixtures(db, fixture.competition_id)
    return to_fixture_read(next(row for row in rows if row[0].id == fixture.id))


@router.post(
    "/fixtures/{fixture_id}/officials",
    response_model=FixtureOfficialAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def assign_fixture_official_route(
    fixture_id: UUID,
    payload: FixtureOfficialAssignmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FixtureOfficialAssignmentRead:
    return to_official_assignment_read(
        await assign_fixture_official(db, identity, fixture_id, payload, authz)
    )


@router.post(
    "/fixtures/{fixture_id}/events",
    response_model=FixtureMatchEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_fixture_match_event_route(
    fixture_id: UUID,
    payload: FixtureMatchEventCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FixtureMatchEventRead:
    return to_match_event_read(
        await record_fixture_match_event(db, identity, fixture_id, payload, authz)
    )


@router.get("/fixtures/{fixture_id}/events", response_model=list[FixtureMatchEventRead])
async def list_fixture_match_events_route(
    fixture_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FixtureMatchEventRead]:
    return [
        to_match_event_read(match_event)
        for match_event in await list_fixture_match_events(db, fixture_id)
    ]


@router.get("/{competition_id}/standings", response_model=list[CompetitionStandingRead])
async def competition_standings_route(
    competition_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CompetitionStandingRead]:
    return [CompetitionStandingRead(**row) for row in await competition_standings(db, competition_id)]
