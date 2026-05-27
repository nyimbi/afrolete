from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import (
    Competition,
    CompetitionFixture,
    CompetitionParticipant,
    FixtureMatchEvent,
    FixtureOfficialAssignment,
)
from app.models.enums import FixtureStatus, MemberSubjectType
from app.models.event import Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.team import AthleteProfile, Team
from app.schemas.competition import (
    CompetitionCreate,
    CompetitionFixtureCreate,
    CompetitionParticipantCreate,
    FixtureMatchEventCreate,
    FixtureOfficialAssignmentCreate,
    FixtureResultUpdate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_competition(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_competition(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CompetitionCreate,
    authz: AuthorizationService,
) -> Competition:
    await get_organization(db, payload.organization_id)
    await ensure_manage_competition(authz, identity, payload.organization_id)

    competition = Competition(**payload.model_dump())
    db.add(competition)
    await db.commit()
    await db.refresh(competition)
    return competition


async def list_competitions(db: AsyncSession, organization_id: UUID) -> list[Competition]:
    return list(
        (
            await db.scalars(
                select(Competition)
                .where(Competition.organization_id == organization_id)
                .order_by(Competition.starts_on.desc().nullslast(), Competition.name)
            )
        ).all()
    )


async def add_competition_participant(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionParticipantCreate,
    authz: AuthorizationService,
) -> CompetitionParticipant:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    await get_team_for_organization(db, payload.team_id, competition.organization_id)

    existing = await db.scalar(
        select(CompetitionParticipant).where(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.team_id == payload.team_id,
        )
    )
    if existing is not None:
        return existing

    participant = CompetitionParticipant(competition_id=competition_id, **payload.model_dump())
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    return participant


async def list_competition_participants(
    db: AsyncSession,
    competition_id: UUID,
) -> list[tuple[CompetitionParticipant, Team]]:
    await get_competition(db, competition_id)
    return list(
        (
            await db.execute(
                select(CompetitionParticipant, Team)
                .join(Team, Team.id == CompetitionParticipant.team_id)
                .where(CompetitionParticipant.competition_id == competition_id)
                .order_by(CompetitionParticipant.group_label, CompetitionParticipant.seed, Team.name)
            )
        ).all()
    )


async def create_competition_fixture(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionFixtureCreate,
    authz: AuthorizationService,
) -> CompetitionFixture:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    await ensure_participant_team(db, competition_id, payload.home_team_id, competition.organization_id)
    await ensure_participant_team(db, competition_id, payload.away_team_id, competition.organization_id)
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != competition.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    fixture = CompetitionFixture(
        organization_id=competition.organization_id,
        competition_id=competition_id,
        **payload.model_dump(),
    )
    db.add(fixture)
    await db.commit()
    await db.refresh(fixture)
    return fixture


async def list_competition_fixtures(
    db: AsyncSession,
    competition_id: UUID,
) -> list[tuple[CompetitionFixture, Team, Team]]:
    await get_competition(db, competition_id)
    home = Team.__table__.alias("home_team")
    away = Team.__table__.alias("away_team")
    return list(
        (
            await db.execute(
                select(CompetitionFixture, home.c.name, away.c.name)
                .join(home, home.c.id == CompetitionFixture.home_team_id)
                .join(away, away.c.id == CompetitionFixture.away_team_id)
                .where(CompetitionFixture.competition_id == competition_id)
                .order_by(CompetitionFixture.scheduled_at, CompetitionFixture.round_label)
            )
        ).all()
    )


async def update_fixture_result(
    db: AsyncSession,
    identity: CurrentIdentity,
    fixture_id: UUID,
    payload: FixtureResultUpdate,
    authz: AuthorizationService,
) -> CompetitionFixture:
    fixture = await get_fixture(db, fixture_id)
    await ensure_manage_competition(authz, identity, fixture.organization_id)

    fixture.home_score = payload.home_score
    fixture.away_score = payload.away_score
    fixture.notes = payload.notes if payload.notes is not None else fixture.notes
    if payload.confirmed:
        fixture.status = FixtureStatus.FINAL
        fixture.result_confirmed_at = datetime.now(UTC)
    else:
        fixture.status = FixtureStatus.SCHEDULED
        fixture.result_confirmed_at = None

    await db.commit()
    await db.refresh(fixture)
    return fixture


async def assign_fixture_official(
    db: AsyncSession,
    identity: CurrentIdentity,
    fixture_id: UUID,
    payload: FixtureOfficialAssignmentCreate,
    authz: AuthorizationService,
) -> FixtureOfficialAssignment:
    fixture = await get_fixture(db, fixture_id)
    await ensure_manage_competition(authz, identity, fixture.organization_id)
    await ensure_person_member(db, payload.person_id, fixture.organization_id)

    existing = await db.scalar(
        select(FixtureOfficialAssignment).where(
            FixtureOfficialAssignment.fixture_id == fixture_id,
            FixtureOfficialAssignment.person_id == payload.person_id,
            FixtureOfficialAssignment.role == payload.role,
        )
    )
    if existing is not None:
        existing.status = payload.status
        existing.certification_level = payload.certification_level
        existing.conflict_notes = payload.conflict_notes
        await db.commit()
        await db.refresh(existing)
        return existing

    assignment = FixtureOfficialAssignment(fixture_id=fixture_id, **payload.model_dump())
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def record_fixture_match_event(
    db: AsyncSession,
    identity: CurrentIdentity,
    fixture_id: UUID,
    payload: FixtureMatchEventCreate,
    authz: AuthorizationService,
) -> FixtureMatchEvent:
    fixture = await get_fixture(db, fixture_id)
    await ensure_manage_competition(authz, identity, fixture.organization_id)
    if payload.team_id not in {fixture.home_team_id, fixture.away_team_id}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not in fixture")
    if payload.athlete_profile_id is not None:
        athlete_profile = await db.get(AthleteProfile, payload.athlete_profile_id)
        if athlete_profile is None or athlete_profile.organization_id != fixture.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")

    match_event = FixtureMatchEvent(fixture_id=fixture_id, **payload.model_dump())
    db.add(match_event)
    await db.commit()
    await db.refresh(match_event)
    return match_event


async def list_fixture_match_events(
    db: AsyncSession,
    fixture_id: UUID,
) -> list[FixtureMatchEvent]:
    await get_fixture(db, fixture_id)
    return list(
        (
            await db.scalars(
                select(FixtureMatchEvent)
                .where(FixtureMatchEvent.fixture_id == fixture_id)
                .order_by(FixtureMatchEvent.minute, FixtureMatchEvent.created_at)
            )
        ).all()
    )


async def competition_standings(db: AsyncSession, competition_id: UUID) -> list[dict[str, object]]:
    competition = await get_competition(db, competition_id)
    participants = await list_competition_participants(db, competition_id)
    standings: dict[UUID, dict[str, object]] = {
        team.id: {
            "competition_id": competition_id,
            "team_id": team.id,
            "team_name": team.name,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
        }
        for _, team in participants
    }
    fixtures = (
        await db.scalars(
            select(CompetitionFixture)
            .where(CompetitionFixture.competition_id == competition_id)
            .where(CompetitionFixture.status == FixtureStatus.FINAL)
            .where(CompetitionFixture.home_score.is_not(None))
            .where(CompetitionFixture.away_score.is_not(None))
        )
    ).all()
    for fixture in fixtures:
        if fixture.home_team_id not in standings or fixture.away_team_id not in standings:
            continue
        apply_result(
            standings[fixture.home_team_id],
            int(fixture.home_score or 0),
            int(fixture.away_score or 0),
            competition.points_for_win,
            competition.points_for_draw,
            competition.points_for_loss,
        )
        apply_result(
            standings[fixture.away_team_id],
            int(fixture.away_score or 0),
            int(fixture.home_score or 0),
            competition.points_for_win,
            competition.points_for_draw,
            competition.points_for_loss,
        )

    rows = list(standings.values())
    rows.sort(
        key=lambda row: (
            -int(row["points"]),
            -int(row["goal_difference"]),
            -int(row["goals_for"]),
            str(row["team_name"]),
        )
    )
    return rows


def apply_result(
    row: dict[str, object],
    goals_for: int,
    goals_against: int,
    points_for_win: int,
    points_for_draw: int,
    points_for_loss: int,
) -> None:
    row["played"] = int(row["played"]) + 1
    row["goals_for"] = int(row["goals_for"]) + goals_for
    row["goals_against"] = int(row["goals_against"]) + goals_against
    row["goal_difference"] = int(row["goals_for"]) - int(row["goals_against"])
    if goals_for > goals_against:
        row["wins"] = int(row["wins"]) + 1
        row["points"] = int(row["points"]) + points_for_win
    elif goals_for == goals_against:
        row["draws"] = int(row["draws"]) + 1
        row["points"] = int(row["points"]) + points_for_draw
    else:
        row["losses"] = int(row["losses"]) + 1
        row["points"] = int(row["points"]) + points_for_loss


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_competition(db: AsyncSession, competition_id: UUID) -> Competition:
    competition = await db.get(Competition, competition_id)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")
    return competition


async def get_fixture(db: AsyncSession, fixture_id: UUID) -> CompetitionFixture:
    fixture = await db.get(CompetitionFixture, fixture_id)
    if fixture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fixture not found")
    return fixture


async def get_team_for_organization(db: AsyncSession, team_id: UUID, organization_id: UUID) -> Team:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


async def ensure_participant_team(
    db: AsyncSession,
    competition_id: UUID,
    team_id: UUID,
    organization_id: UUID,
) -> None:
    await get_team_for_organization(db, team_id, organization_id)
    participant = await db.scalar(
        select(CompetitionParticipant).where(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.team_id == team_id,
        )
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Team is not registered in this competition",
        )


async def ensure_person_member(db: AsyncSession, person_id: UUID, organization_id: UUID) -> Person:
    person = await db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person_id,
            Membership.status == "active",
        )
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official not found")
    return person
