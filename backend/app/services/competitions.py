from datetime import UTC, datetime, timedelta
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
    CompetitionFixtureGenerateCreate,
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


async def generate_competition_fixtures(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionFixtureGenerateCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    participants = await list_competition_participants(db, competition_id)
    ordered_teams = [team for _, team in participants]
    if len(ordered_teams) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least two teams are required to generate fixtures",
        )

    existing = (
        await db.scalars(
            select(CompetitionFixture).where(CompetitionFixture.competition_id == competition_id)
        )
    ).all()
    existing_keys = {
        (fixture.home_team_id, fixture.away_team_id, fixture.round_label, fixture.stage_label)
        for fixture in existing
    }
    pairings = round_robin_pairings([team.id for team in ordered_teams])
    if payload.double_round_robin:
        reverse_pairings = [
            [(away_id, home_id) for home_id, away_id in round_pairings]
            for round_pairings in pairings
        ]
        pairings = [*pairings, *reverse_pairings]

    created: list[CompetitionFixture] = []
    skipped = 0
    for round_index, round_pairings in enumerate(pairings, start=1):
        for slot_index, (home_team_id, away_team_id) in enumerate(round_pairings):
            round_label = f"Round {round_index}"
            key = (home_team_id, away_team_id, round_label, payload.stage_label)
            if key in existing_keys:
                skipped += 1
                continue
            fixture = CompetitionFixture(
                organization_id=competition.organization_id,
                competition_id=competition_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                round_label=round_label,
                stage_label=payload.stage_label,
                scheduled_at=payload.starts_at
                + timedelta(days=(round_index - 1) * payload.interval_days)
                + timedelta(minutes=slot_index * payload.match_spacing_minutes),
                venue_name=payload.venue_name,
                notes="Auto-generated by AfroLete fixture planner.",
            )
            db.add(fixture)
            created.append(fixture)
            existing_keys.add(key)
    await db.commit()
    for fixture in created:
        await db.refresh(fixture)
    return {
        "competition_id": competition_id,
        "created": len(created),
        "existing": skipped,
        "rounds": len(pairings),
        "fixtures": created,
    }


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


async def competition_bracket(db: AsyncSession, competition_id: UUID) -> dict[str, object]:
    competition = await get_competition(db, competition_id)
    participants = await list_competition_participants(db, competition_id)
    team_names = {team.id: team.name for _, team in participants}
    fixtures = (
        await db.scalars(
            select(CompetitionFixture)
            .where(CompetitionFixture.competition_id == competition_id)
            .order_by(CompetitionFixture.stage_label, CompetitionFixture.round_label, CompetitionFixture.scheduled_at)
        )
    ).all()
    rounds: dict[tuple[str, str], list[dict[str, object]]] = {}
    for index, fixture in enumerate(fixtures, start=1):
        round_label = fixture.round_label or "Round"
        stage_label = fixture.stage_label or "Competition"
        rounds.setdefault((stage_label, round_label), []).append(
            {
                "round_label": round_label,
                "stage_label": stage_label,
                "slot": index,
                "home_team_name": team_names.get(fixture.home_team_id),
                "away_team_name": team_names.get(fixture.away_team_id),
                "fixture_id": fixture.id,
                "status": fixture.status,
                "winner_team_name": fixture_winner_name(fixture, team_names),
            }
        )
    if not rounds:
        seeded = [team for _, team in participants]
        for slot, (home, away) in enumerate(seed_pairings(seeded), start=1):
            rounds.setdefault(("Projected", "Opening round"), []).append(
                {
                    "round_label": "Opening round",
                    "stage_label": "Projected",
                    "slot": slot,
                    "home_team_name": home.name if home else None,
                    "away_team_name": away.name if away else None,
                    "fixture_id": None,
                    "status": None,
                    "winner_team_name": None,
                }
            )
    return {
        "competition_id": competition_id,
        "format": competition.format,
        "rounds": [
            {"stage_label": stage, "round_label": round_label, "matches": matches}
            for (stage, round_label), matches in rounds.items()
        ],
    }


async def competition_conflicts(db: AsyncSession, competition_id: UUID) -> list[dict[str, object]]:
    await get_competition(db, competition_id)
    participants = await list_competition_participants(db, competition_id)
    team_names = {team.id: team.name for _, team in participants}
    fixtures = (
        await db.scalars(
            select(CompetitionFixture)
            .where(CompetitionFixture.competition_id == competition_id)
            .order_by(CompetitionFixture.scheduled_at)
        )
    ).all()
    assignments = (
        await db.scalars(
            select(FixtureOfficialAssignment).where(
                FixtureOfficialAssignment.fixture_id.in_([fixture.id for fixture in fixtures])
            )
        )
    ).all() if fixtures else []
    official_counts: dict[UUID, int] = {}
    for assignment in assignments:
        official_counts[assignment.fixture_id] = official_counts.get(assignment.fixture_id, 0) + 1

    conflicts: list[dict[str, object]] = []
    matchup_seen: set[tuple[UUID, UUID]] = set()
    for fixture in fixtures:
        matchup = tuple(sorted((fixture.home_team_id, fixture.away_team_id)))
        if matchup in matchup_seen:
            conflicts.append(
                conflict(
                    competition_id,
                    fixture.id,
                    "duplicate-matchup",
                    "watch",
                    "Duplicate matchup",
                    f"{team_names.get(fixture.home_team_id)} and {team_names.get(fixture.away_team_id)} appear more than once.",
                    "Confirm double-round-robin intent or remove the duplicate fixture.",
                )
            )
        matchup_seen.add(matchup)
        if official_counts.get(fixture.id, 0) == 0:
            conflicts.append(
                conflict(
                    competition_id,
                    fixture.id,
                    "missing-official",
                    "warning",
                    "Fixture has no official",
                    f"{team_names.get(fixture.home_team_id)} vs {team_names.get(fixture.away_team_id)} has no assigned official.",
                    "Assign a referee or match commissioner before publishing match day operations.",
                )
            )
    for index, fixture in enumerate(fixtures):
        for other in fixtures[index + 1 :]:
            minutes_apart = abs((other.scheduled_at - fixture.scheduled_at).total_seconds()) / 60
            shared_teams = {fixture.home_team_id, fixture.away_team_id} & {
                other.home_team_id,
                other.away_team_id,
            }
            if shared_teams and minutes_apart < 240:
                team_name = team_names.get(next(iter(shared_teams)), "Team")
                conflicts.append(
                    conflict(
                        competition_id,
                        other.id,
                        "team-rest-window",
                        "critical",
                        "Team rest conflict",
                        f"{team_name} has fixtures less than four hours apart.",
                        "Move one fixture or split the schedule across another match day.",
                    )
                )
            if (
                fixture.venue_name
                and other.venue_name
                and fixture.venue_name == other.venue_name
                and minutes_apart < 120
            ):
                conflicts.append(
                    conflict(
                        competition_id,
                        other.id,
                        "venue-overlap",
                        "critical",
                        "Venue overlap",
                        f"{fixture.venue_name} has fixtures scheduled within two hours.",
                        "Move one match, adjust kickoff spacing, or assign another venue.",
                    )
                )
    return conflicts


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


def round_robin_pairings(team_ids: list[UUID]) -> list[list[tuple[UUID, UUID]]]:
    teams: list[UUID | None] = list(team_ids)
    if len(teams) % 2:
        teams.append(None)
    rounds: list[list[tuple[UUID, UUID]]] = []
    for _ in range(len(teams) - 1):
        round_matches: list[tuple[UUID, UUID]] = []
        for index in range(len(teams) // 2):
            home = teams[index]
            away = teams[-index - 1]
            if home is not None and away is not None:
                round_matches.append((home, away))
        rounds.append(round_matches)
        teams = [teams[0], teams[-1], *teams[1:-1]]
    return rounds


def seed_pairings(teams: list[Team]) -> list[tuple[Team | None, Team | None]]:
    ordered = list(teams)
    pairs: list[tuple[Team | None, Team | None]] = []
    while ordered:
        home = ordered.pop(0)
        away = ordered.pop(-1) if ordered else None
        pairs.append((home, away))
    return pairs


def fixture_winner_name(fixture: CompetitionFixture, team_names: dict[UUID, str]) -> str | None:
    if fixture.home_score is None or fixture.away_score is None or fixture.home_score == fixture.away_score:
        return None
    winner_id = fixture.home_team_id if fixture.home_score > fixture.away_score else fixture.away_team_id
    return team_names.get(winner_id)


def conflict(
    competition_id: UUID,
    fixture_id: UUID | None,
    conflict_key: str,
    severity: str,
    title: str,
    description: str,
    recommendation: str,
) -> dict[str, object]:
    return {
        "competition_id": competition_id,
        "fixture_id": fixture_id,
        "conflict_key": conflict_key,
        "severity": severity,
        "title": title,
        "description": description,
        "recommendation": recommendation,
    }


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
