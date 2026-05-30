import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.commercial import TicketProduct
from app.models.competition import (
    AthleteTransferRecord,
    Competition,
    CompetitionEligibilityCertificate,
    CompetitionFixture,
    CompetitionParticipant,
    FixtureMatchEvent,
    FixtureOfficialAssignment,
)
from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.enums import (
    ComplianceCredentialStatus,
    CommunicationMessageType,
    CommunicationScopeType,
    EventType,
    FixtureStatus,
    MemberSubjectType,
    MedicalClearanceStatus,
    OfficialAssignmentStatus,
    RosterStatus,
)
from app.models.event import ComplianceCredential, Event, IncidentMedicalClearance
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.competition import (
    AthleteTransferCreate,
    CompetitionAdvanceCreate,
    CompetitionBroadcastCreate,
    CompetitionCreate,
    CompetitionEligibilityCheckCreate,
    CompetitionFixtureCreate,
    CompetitionFixtureGenerateCreate,
    CompetitionParticipantCreate,
    CompetitionScheduleOptimizeCreate,
    CompetitionTicketingCreate,
    FixtureMatchEventCreate,
    FixtureOfficialAssignmentCreate,
    FixtureOfficialResponseUpdate,
    FixtureResultUpdate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.communications import destination_for_channel, dispatch_message, initial_delivery_status


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


async def create_athlete_transfer_record(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: AthleteTransferCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    await get_organization(db, payload.organization_id)
    await ensure_manage_competition(authz, identity, payload.organization_id)
    athlete, person = await get_athlete_for_organization(db, payload.athlete_profile_id, payload.organization_id)
    from_team = None
    if payload.from_team_id is not None:
        from_team = await get_team_for_organization(db, payload.from_team_id, payload.organization_id)
    to_team = await get_team_for_organization(db, payload.to_team_id, payload.organization_id)
    now = datetime.now(UTC)
    decided_at = now if payload.status in approved_transfer_statuses() else None
    transfer = AthleteTransferRecord(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete.id,
        from_team_id=from_team.id if from_team else None,
        to_team_id=to_team.id,
        transfer_type=payload.transfer_type,
        status=payload.status,
        requested_on=payload.requested_on or now.date(),
        effective_on=payload.effective_on,
        window_label=payload.window_label,
        previous_registration_ref=payload.previous_registration_ref,
        clearance_reference=payload.clearance_reference,
        reviewed_by_person_id=identity.person_id if payload.status in approved_transfer_statuses() else None,
        decided_at=decided_at,
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    return athlete_transfer_row(transfer, person.display_name, from_team.name if from_team else None, to_team.name)


async def list_athlete_transfer_records(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    athlete_profile_id: UUID | None = None,
    team_id: UUID | None = None,
) -> list[dict[str, object]]:
    await get_organization(db, organization_id)
    await ensure_manage_competition(authz, identity, organization_id)
    from_team = Team.__table__.alias("from_team")
    to_team = Team.__table__.alias("to_team")
    statement = (
        select(
            AthleteTransferRecord,
            Person.display_name,
            from_team.c.name.label("from_team_name"),
            to_team.c.name.label("to_team_name"),
        )
        .join(AthleteProfile, AthleteProfile.id == AthleteTransferRecord.athlete_profile_id)
        .join(Person, Person.id == AthleteProfile.person_id)
        .outerjoin(from_team, from_team.c.id == AthleteTransferRecord.from_team_id)
        .join(to_team, to_team.c.id == AthleteTransferRecord.to_team_id)
        .where(AthleteTransferRecord.organization_id == organization_id)
    )
    if athlete_profile_id is not None:
        statement = statement.where(AthleteTransferRecord.athlete_profile_id == athlete_profile_id)
    if team_id is not None:
        statement = statement.where(
            (AthleteTransferRecord.from_team_id == team_id) | (AthleteTransferRecord.to_team_id == team_id)
        )
    rows = (
        await db.execute(
            statement.order_by(
                AthleteTransferRecord.requested_on.desc(),
                AthleteTransferRecord.created_at.desc(),
            )
        )
    ).all()
    return [
        athlete_transfer_row(transfer, athlete_name, from_team_name, to_team_name)
        for transfer, athlete_name, from_team_name, to_team_name in rows
    ]


async def issue_competition_eligibility_certificate(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionEligibilityCheckCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    athlete, person = await get_athlete_for_organization(db, payload.athlete_profile_id, competition.organization_id)
    team = await get_team_for_organization(db, payload.team_id, competition.organization_id)
    checks = await build_competition_eligibility_checks(db, competition, athlete, person, team, payload)
    blocker_count = sum(1 for check in checks if check["status"] == "blocker")
    warning_count = sum(1 for check in checks if check["status"] == "warning")
    status_value = "eligible" if blocker_count == 0 else "ineligible"
    summary = eligibility_summary(person.display_name, team.name, competition.name, blocker_count, warning_count)
    certificate_number = competition_eligibility_certificate_number(competition.id, athlete.id, team.id)
    existing = await db.scalar(
        select(CompetitionEligibilityCertificate).where(
            CompetitionEligibilityCertificate.competition_id == competition_id,
            CompetitionEligibilityCertificate.athlete_profile_id == athlete.id,
            CompetitionEligibilityCertificate.team_id == team.id,
        )
    )
    if existing is None:
        existing = CompetitionEligibilityCertificate(
            organization_id=competition.organization_id,
            competition_id=competition_id,
            athlete_profile_id=athlete.id,
            team_id=team.id,
            certificate_number=certificate_number,
        )
        db.add(existing)
    existing.transfer_record_id = payload.transfer_record_id
    existing.issued_by_person_id = identity.person_id
    existing.status = status_value
    existing.valid_from = competition.starts_on or date.today()
    existing.valid_until = payload.valid_until or competition.ends_on
    existing.blocker_count = blocker_count
    existing.warning_count = warning_count
    existing.eligibility_summary = summary
    existing.checks_json = json.dumps(checks, default=str)
    await db.commit()
    await db.refresh(existing)
    return competition_eligibility_row(existing, person.display_name, team.name)


async def list_competition_eligibility_certificates(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    authz: AuthorizationService,
) -> list[dict[str, object]]:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    rows = (
        await db.execute(
            select(CompetitionEligibilityCertificate, Person.display_name, Team.name)
            .join(AthleteProfile, AthleteProfile.id == CompetitionEligibilityCertificate.athlete_profile_id)
            .join(Person, Person.id == AthleteProfile.person_id)
            .join(Team, Team.id == CompetitionEligibilityCertificate.team_id)
            .where(CompetitionEligibilityCertificate.competition_id == competition_id)
            .order_by(
                CompetitionEligibilityCertificate.status,
                Team.name,
                Person.display_name,
            )
        )
    ).all()
    return [
        competition_eligibility_row(certificate, athlete_name, team_name)
        for certificate, athlete_name, team_name in rows
    ]


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


async def advance_competition_round(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionAdvanceCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    team_names = {
        team.id: team.name
        for _, team in await list_competition_participants(db, competition_id)
    }
    source_fixtures = (
        await db.scalars(
            select(CompetitionFixture)
            .where(CompetitionFixture.competition_id == competition_id)
            .where(CompetitionFixture.stage_label == payload.source_stage_label)
            .where(CompetitionFixture.round_label == payload.source_round_label)
            .order_by(CompetitionFixture.scheduled_at, CompetitionFixture.created_at)
        )
    ).all()
    if not source_fixtures:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No source fixtures found")

    winners: list[UUID] = []
    for fixture in source_fixtures:
        winner_id = fixture_winner_team_id(fixture)
        if winner_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="All source fixtures need confirmed non-draw winners before advancement",
            )
        winners.append(winner_id)
    if len(winners) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least two winners are required to create the next round",
        )

    existing_next = (
        await db.scalars(
            select(CompetitionFixture)
            .where(CompetitionFixture.competition_id == competition_id)
            .where(CompetitionFixture.stage_label == payload.next_stage_label)
            .where(CompetitionFixture.round_label == payload.next_round_label)
        )
    ).all()
    existing_matchups = {
        frozenset((fixture.home_team_id, fixture.away_team_id))
        for fixture in existing_next
    }
    byes: list[UUID] = []
    created: list[CompetitionFixture] = []
    skipped = 0
    for slot_index, (home_team_id, away_team_id) in enumerate(advance_pairings(winners)):
        if away_team_id is None:
            byes.append(home_team_id)
            continue
        matchup = frozenset((home_team_id, away_team_id))
        if matchup in existing_matchups:
            skipped += 1
            continue
        fixture = CompetitionFixture(
            organization_id=competition.organization_id,
            competition_id=competition_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            round_label=payload.next_round_label,
            stage_label=payload.next_stage_label,
            scheduled_at=payload.scheduled_at + timedelta(minutes=slot_index * payload.match_spacing_minutes),
            venue_name=payload.venue_name,
            notes=(
                f"Advanced from {payload.source_stage_label} {payload.source_round_label} "
                "by AfroLete tournament automation."
            ),
        )
        db.add(fixture)
        created.append(fixture)
        existing_matchups.add(matchup)
    await db.commit()
    for fixture in created:
        await db.refresh(fixture)
    return {
        "competition_id": competition_id,
        "source_stage_label": payload.source_stage_label,
        "source_round_label": payload.source_round_label,
        "next_stage_label": payload.next_stage_label,
        "next_round_label": payload.next_round_label,
        "winners": [team_names.get(team_id, str(team_id)) for team_id in winners],
        "byes": [team_names.get(team_id, str(team_id)) for team_id in byes],
        "created": len(created),
        "skipped": skipped,
        "fixtures": created,
    }


async def optimize_competition_schedule(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionScheduleOptimizeCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    fixtures = (
        await db.scalars(
            select(CompetitionFixture)
            .where(CompetitionFixture.competition_id == competition_id)
            .order_by(CompetitionFixture.stage_label, CompetitionFixture.round_label, CompetitionFixture.scheduled_at)
        )
    ).all()
    if not fixtures:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fixtures found")

    protected_finals = 0
    moved: list[CompetitionFixture] = []
    unchanged = 0
    last_team_time: dict[UUID, datetime] = {}
    venue_available_at: dict[str, datetime] = {}
    next_slot = normalized_schedule_datetime(payload.starts_at)
    for fixture in fixtures:
        if payload.preserve_final_results and fixture.status == FixtureStatus.FINAL:
            protected_finals += 1
            remember_schedule_constraint(fixture, last_team_time, venue_available_at, payload.match_spacing_minutes)
            continue
        venue_name = payload.venue_name or fixture.venue_name or "Competition venue"
        scheduled_at = optimized_fixture_time(
            next_slot,
            fixture,
            venue_name,
            last_team_time,
            venue_available_at,
            payload.team_rest_minutes,
        )
        changed = fixture.scheduled_at != scheduled_at or fixture.venue_name != venue_name
        if changed:
            fixture.scheduled_at = scheduled_at
            fixture.venue_name = venue_name
            fixture.notes = fixture_schedule_notes(fixture.notes)
            moved.append(fixture)
        else:
            unchanged += 1
        remember_schedule_constraint(fixture, last_team_time, venue_available_at, payload.match_spacing_minutes)
        next_slot = scheduled_at + timedelta(minutes=payload.match_spacing_minutes)
    await db.commit()
    for fixture in moved:
        await db.refresh(fixture)
    return {
        "competition_id": competition_id,
        "moved": len(moved),
        "unchanged": unchanged,
        "protected_finals": protected_finals,
        "team_rest_minutes": payload.team_rest_minutes,
        "match_spacing_minutes": payload.match_spacing_minutes,
        "fixtures": moved,
    }


async def broadcast_competition_update(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionBroadcastCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    recipient_ids = await competition_broadcast_recipients(db, competition_id, payload.include_guardians)
    if not recipient_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No competition recipients")
    subject = payload.subject or f"{competition.name} competition update"
    body = payload.body or await competition_broadcast_body(db, competition_id, competition)
    now = datetime.now(UTC)
    message = CommunicationMessage(
        organization_id=competition.organization_id,
        template_id=None,
        created_by_person_id=identity.person_id,
        message_type=CommunicationMessageType.ANNOUNCEMENT,
        channel=payload.channel,
        scope_type=CommunicationScopeType.ORGANIZATION,
        scope_id=competition.organization_id,
        subject=subject,
        body=body,
        urgent=payload.urgent,
        quiet_hours_override=payload.urgent,
        scheduled_for=None,
        sent_at=now,
        status="sent",
    )
    db.add(message)
    await db.flush()
    for person_id in sorted(recipient_ids, key=str):
        person = await db.get(Person, person_id)
        if person is None:
            continue
        db.add(
            MessageRecipient(
                message_id=message.id,
                person_id=person.id,
                destination=destination_for_channel(person, payload.channel),
                delivery_status=initial_delivery_status(person, payload.channel),
            )
        )
    await db.commit()
    await db.refresh(message)
    summary = await dispatch_message(db, identity, message.id, authz)
    return {
        "competition_id": competition_id,
        "message_id": message.id,
        "subject": message.subject,
        "channel": message.channel,
        "recipient_count": len(recipient_ids),
        "attempted": summary.attempted,
        "delivered": summary.delivered,
        "queued": summary.queued,
        "failed": summary.failed,
        "suppressed": summary.suppressed,
        "transport_mode": summary.transport_mode,
    }


async def create_competition_ticketing(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition_id: UUID,
    payload: CompetitionTicketingCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    competition = await get_competition(db, competition_id)
    await ensure_manage_competition(authz, identity, competition.organization_id)
    fixture = await get_competition_fixture(db, payload.fixture_id, competition_id)
    event = await ensure_fixture_event(db, identity, competition, fixture, authz)
    product_name = payload.name or default_ticket_product_name(competition, fixture)
    existing = await db.scalar(
        select(TicketProduct).where(
            TicketProduct.organization_id == competition.organization_id,
            TicketProduct.event_id == event.id,
            TicketProduct.name == product_name,
        )
    )
    if existing is not None:
        if payload.capacity < existing.sold_count:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ticket capacity cannot be lower than tickets already sold",
            )
        existing.price = payload.price
        existing.currency = payload.currency
        existing.capacity = payload.capacity
        existing.access_zone = payload.access_zone or fixture.venue_name
        fixture.notes = fixture_ticketing_notes(fixture.notes, product_name)
        await db.commit()
        await db.refresh(existing)
        await db.refresh(fixture)
        return competition_ticketing_row(competition_id, fixture, existing)

    product = TicketProduct(
        organization_id=competition.organization_id,
        event_id=event.id,
        name=product_name,
        price=payload.price,
        currency=payload.currency,
        capacity=payload.capacity,
        access_zone=payload.access_zone or fixture.venue_name,
    )
    db.add(product)
    fixture.notes = fixture_ticketing_notes(fixture.notes, product_name)
    await db.commit()
    await db.refresh(product)
    await db.refresh(fixture)
    return competition_ticketing_row(competition_id, fixture, product)


async def list_competition_ticketing(
    db: AsyncSession,
    competition_id: UUID,
) -> list[dict[str, object]]:
    await get_competition(db, competition_id)
    rows = (
        await db.execute(
            select(CompetitionFixture, TicketProduct)
            .join(TicketProduct, TicketProduct.event_id == CompetitionFixture.event_id)
            .where(CompetitionFixture.competition_id == competition_id)
            .order_by(CompetitionFixture.scheduled_at, TicketProduct.created_at.desc())
        )
    ).all()
    return [
        competition_ticketing_row(competition_id, fixture, product)
        for fixture, product in rows
    ]


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


async def list_my_official_assignments(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID | None = None,
    status_filter: OfficialAssignmentStatus | None = None,
) -> list[dict[str, object]]:
    home_team = aliased(Team)
    away_team = aliased(Team)
    statement = (
        select(
            FixtureOfficialAssignment,
            CompetitionFixture,
            Competition,
            Organization,
            home_team.name,
            away_team.name,
        )
        .join(CompetitionFixture, CompetitionFixture.id == FixtureOfficialAssignment.fixture_id)
        .join(Competition, Competition.id == CompetitionFixture.competition_id)
        .join(Organization, Organization.id == Competition.organization_id)
        .join(home_team, home_team.id == CompetitionFixture.home_team_id)
        .join(away_team, away_team.id == CompetitionFixture.away_team_id)
        .where(FixtureOfficialAssignment.person_id == identity.person_id)
    )
    if organization_id is not None:
        statement = statement.where(Competition.organization_id == organization_id)
    if status_filter is not None:
        statement = statement.where(FixtureOfficialAssignment.status == status_filter)
    rows = (
        await db.execute(
            statement.order_by(
                CompetitionFixture.scheduled_at.asc(),
                Competition.name.asc(),
            ).limit(100)
        )
    ).all()
    return [
        official_assignment_portal_read(
            assignment,
            fixture,
            competition,
            organization,
            home_team_name,
            away_team_name,
        )
        for assignment, fixture, competition, organization, home_team_name, away_team_name in rows
    ]


async def update_my_official_assignment_response(
    db: AsyncSession,
    identity: CurrentIdentity,
    assignment_id: UUID,
    payload: FixtureOfficialResponseUpdate,
) -> dict[str, object]:
    assignment = await db.get(FixtureOfficialAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official assignment not found")
    if assignment.person_id != identity.person_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    fixture = await get_fixture(db, assignment.fixture_id)
    assignment.status = payload.status
    assignment.conflict_notes = payload.conflict_notes.strip() if payload.conflict_notes else None
    await db.commit()
    await db.refresh(assignment)
    rows = await list_my_official_assignments(
        db,
        identity,
        organization_id=fixture.organization_id,
    )
    return next(row for row in rows if row["id"] == assignment.id)


def official_assignment_portal_read(
    assignment: FixtureOfficialAssignment,
    fixture: CompetitionFixture,
    competition: Competition,
    organization: Organization,
    home_team_name: str,
    away_team_name: str,
) -> dict[str, object]:
    response_required = assignment.status == OfficialAssignmentStatus.PROPOSED
    if assignment.status == OfficialAssignmentStatus.ACCEPTED:
        action_label = "Accepted - await match-day confirmation"
    elif assignment.status == OfficialAssignmentStatus.CONFIRMED:
        action_label = "Confirmed - prepare match report and arrival checks"
    elif assignment.status == OfficialAssignmentStatus.DECLINED:
        action_label = "Declined - organizer should assign cover"
    else:
        action_label = "Respond to assignment"
    return {
        "id": assignment.id,
        "organization_id": competition.organization_id,
        "organization_name": organization.name,
        "competition_id": competition.id,
        "competition_name": competition.name,
        "sport": competition.sport,
        "fixture_id": fixture.id,
        "home_team_name": home_team_name,
        "away_team_name": away_team_name,
        "round_label": fixture.round_label,
        "stage_label": fixture.stage_label,
        "scheduled_at": fixture.scheduled_at,
        "venue_name": fixture.venue_name,
        "fixture_status": fixture.status,
        "role": assignment.role,
        "status": assignment.status,
        "certification_level": assignment.certification_level,
        "conflict_notes": assignment.conflict_notes,
        "response_required": response_required,
        "action_label": action_label,
    }


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
    winner_id = fixture_winner_team_id(fixture)
    return team_names.get(winner_id) if winner_id is not None else None


def fixture_winner_team_id(fixture: CompetitionFixture) -> UUID | None:
    if (
        fixture.status != FixtureStatus.FINAL
        or fixture.home_score is None
        or fixture.away_score is None
        or fixture.home_score == fixture.away_score
    ):
        return None
    return fixture.home_team_id if fixture.home_score > fixture.away_score else fixture.away_team_id


def advance_pairings(team_ids: list[UUID]) -> list[tuple[UUID, UUID | None]]:
    pairs: list[tuple[UUID, UUID | None]] = []
    index = 0
    while index < len(team_ids):
        home = team_ids[index]
        away = team_ids[index + 1] if index + 1 < len(team_ids) else None
        pairs.append((home, away))
        index += 2
    return pairs


def optimized_fixture_time(
    candidate: datetime,
    fixture: CompetitionFixture,
    venue_name: str,
    last_team_time: dict[UUID, datetime],
    venue_available_at: dict[str, datetime],
    team_rest_minutes: int,
) -> datetime:
    candidate = normalized_schedule_datetime(candidate)
    for team_id in (fixture.home_team_id, fixture.away_team_id):
        if team_id in last_team_time:
            candidate = max(candidate, last_team_time[team_id] + timedelta(minutes=team_rest_minutes))
    if venue_name in venue_available_at:
        candidate = max(candidate, venue_available_at[venue_name])
    return candidate


def remember_schedule_constraint(
    fixture: CompetitionFixture,
    last_team_time: dict[UUID, datetime],
    venue_available_at: dict[str, datetime],
    match_spacing_minutes: int,
) -> None:
    scheduled_at = normalized_schedule_datetime(fixture.scheduled_at)
    last_team_time[fixture.home_team_id] = scheduled_at
    last_team_time[fixture.away_team_id] = scheduled_at
    if fixture.venue_name:
        venue_available_at[fixture.venue_name] = scheduled_at + timedelta(minutes=match_spacing_minutes)


def normalized_schedule_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def fixture_schedule_notes(existing: str | None) -> str:
    entry = "Schedule optimized by AfroLete to reduce rest-window and venue conflicts."
    if existing and entry not in existing:
        return f"{existing}\n{entry}"
    return existing or entry


async def competition_broadcast_recipients(
    db: AsyncSession,
    competition_id: UUID,
    include_guardians: bool,
) -> set[UUID]:
    rows = (
        await db.execute(
            select(AthleteProfile.person_id)
            .join(TeamRosterEntry, TeamRosterEntry.athlete_profile_id == AthleteProfile.id)
            .join(CompetitionParticipant, CompetitionParticipant.team_id == TeamRosterEntry.team_id)
            .where(CompetitionParticipant.competition_id == competition_id)
        )
    ).all()
    person_ids = {person_id for (person_id,) in rows}
    if include_guardians and person_ids:
        guardian_rows = (
            await db.execute(
                select(GuardianRelationship.guardian_person_id).where(
                    GuardianRelationship.athlete_person_id.in_(person_ids)
                )
            )
        ).all()
        person_ids.update(guardian_id for (guardian_id,) in guardian_rows)
    return person_ids


async def competition_broadcast_body(
    db: AsyncSession,
    competition_id: UUID,
    competition: Competition,
) -> str:
    standings = await competition_standings(db, competition_id)
    fixtures = (
        await db.scalars(
            select(CompetitionFixture)
            .where(CompetitionFixture.competition_id == competition_id)
            .order_by(CompetitionFixture.scheduled_at)
        )
    ).all()
    leader = standings[0]["team_name"] if standings else "No leader yet"
    next_fixture = next((fixture for fixture in fixtures if fixture.status != FixtureStatus.FINAL), None)
    next_line = (
        f"Next fixture is scheduled for {next_fixture.scheduled_at} at {next_fixture.venue_name or 'the assigned venue'}."
        if next_fixture
        else "No pending fixtures remain."
    )
    final_count = sum(1 for fixture in fixtures if fixture.status == FixtureStatus.FINAL)
    return (
        f"{competition.name} update: {len(fixtures)} fixtures, {final_count} confirmed results, "
        f"current leader {leader}. {next_line}"
    )


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


async def build_competition_eligibility_checks(
    db: AsyncSession,
    competition: Competition,
    athlete: AthleteProfile,
    person: Person,
    team: Team,
    payload: CompetitionEligibilityCheckCreate,
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    as_of = competition.starts_on or date.today()
    if payload.require_team_registration:
        participant = await db.scalar(
            select(CompetitionParticipant).where(
                CompetitionParticipant.competition_id == competition.id,
                CompetitionParticipant.team_id == team.id,
                CompetitionParticipant.status == "active",
            )
        )
        checks.append(
            eligibility_check(
                "team_registration",
                "Team registration",
                "pass" if participant else "blocker",
                "critical",
                f"{team.name} is registered for {competition.name}."
                if participant
                else f"{team.name} is not registered for {competition.name}.",
                "Register the team as a competition participant before clearing the athlete."
                if not participant
                else "No action required.",
            )
        )
    if payload.require_active_roster:
        roster_entry = await db.scalar(
            select(TeamRosterEntry).where(
                TeamRosterEntry.team_id == team.id,
                TeamRosterEntry.athlete_profile_id == athlete.id,
                TeamRosterEntry.status.in_(active_roster_statuses()),
            )
        )
        checks.append(
            eligibility_check(
                "active_roster",
                "Active roster",
                "pass" if roster_entry else "blocker",
                "critical",
                f"{person.display_name} is active on {team.name}."
                if roster_entry
                else f"{person.display_name} is not active on {team.name}.",
                "Add the athlete to the roster as active, starter, bench, substitute, or reserve."
                if not roster_entry
                else "No action required.",
            )
        )
    if payload.min_age is not None or payload.max_age is not None:
        age = athlete_age_on(person.date_of_birth, as_of)
        age_ok = age is not None
        if age is not None and payload.min_age is not None and age < payload.min_age:
            age_ok = False
        if age is not None and payload.max_age is not None and age > payload.max_age:
            age_ok = False
        checks.append(
            eligibility_check(
                "age_band",
                "Age band",
                "pass" if age_ok else "blocker",
                "critical",
                f"{person.display_name} is {age} on {as_of.isoformat()}."
                if age is not None
                else "Athlete date of birth is missing.",
                "Update the athlete date of birth or move them to the correct age category."
                if not age_ok
                else "No action required.",
            )
        )
    if payload.require_transfer_clearance:
        checks.append(await transfer_clearance_check(db, competition, athlete, team, payload.transfer_record_id))
    if payload.require_medical_clearance:
        checks.append(await medical_clearance_check(db, competition.organization_id, athlete, person, as_of))
    if payload.require_compliance_credential:
        checks.append(await compliance_credential_check(db, competition.organization_id, person, as_of))
    if payload.max_players_per_team is not None:
        roster_count = await db.scalar(
            select(func.count(TeamRosterEntry.id)).where(
                TeamRosterEntry.team_id == team.id,
                TeamRosterEntry.status.in_(active_roster_statuses()),
            )
        )
        count = int(roster_count or 0)
        checks.append(
            eligibility_check(
                "team_quota",
                "Team roster quota",
                "pass" if count <= payload.max_players_per_team else "blocker",
                "warning",
                f"{team.name} has {count} active rostered athletes against a limit of {payload.max_players_per_team}.",
                "Move players to the bench/reserve ruleset or request a competition quota waiver."
                if count > payload.max_players_per_team
                else "No action required.",
            )
        )
    checks.extend(
        status_policy_check("academic_status", "Academic standing", payload.academic_status, academic_clear_statuses())
    )
    checks.extend(
        status_policy_check(
            "citizenship_status",
            "Citizenship or residency",
            payload.citizenship_status,
            citizenship_clear_statuses(),
        )
    )
    checks.extend(
        status_policy_check(
            "disciplinary_status",
            "Disciplinary standing",
            payload.disciplinary_status,
            disciplinary_clear_statuses(),
        )
    )
    return checks


async def transfer_clearance_check(
    db: AsyncSession,
    competition: Competition,
    athlete: AthleteProfile,
    team: Team,
    transfer_record_id: UUID | None,
) -> dict[str, str]:
    transfer = await db.get(AthleteTransferRecord, transfer_record_id) if transfer_record_id else None
    if transfer_record_id is not None:
        if (
            transfer is None
            or transfer.organization_id != competition.organization_id
            or transfer.athlete_profile_id != athlete.id
            or transfer.to_team_id != team.id
        ):
            return eligibility_check(
                "transfer_clearance",
                "Transfer clearance",
                "blocker",
                "critical",
                "The supplied transfer clearance does not match this athlete and destination team.",
                "Select the correct approved transfer record or issue a new clearance.",
            )
        if transfer.status not in approved_transfer_statuses():
            return eligibility_check(
                "transfer_clearance",
                "Transfer clearance",
                "blocker",
                "critical",
                f"Transfer record is {transfer.status}.",
                "Approve or clear the transfer before issuing competition eligibility.",
            )
        return eligibility_check(
            "transfer_clearance",
            "Transfer clearance",
            "pass",
            "critical",
            f"Transfer clearance {transfer.clearance_reference or transfer.id} is approved for {team.name}.",
            "No action required.",
        )
    latest_transfer = await db.scalar(
        select(AthleteTransferRecord)
        .where(
            AthleteTransferRecord.organization_id == competition.organization_id,
            AthleteTransferRecord.athlete_profile_id == athlete.id,
            AthleteTransferRecord.to_team_id == team.id,
            AthleteTransferRecord.status.in_(approved_transfer_statuses()),
        )
        .order_by(AthleteTransferRecord.effective_on.desc(), AthleteTransferRecord.created_at.desc())
    )
    if latest_transfer is not None:
        return eligibility_check(
            "transfer_clearance",
            "Transfer clearance",
            "pass",
            "critical",
            f"Approved transfer clearance {latest_transfer.clearance_reference or latest_transfer.id} is on file.",
            "No action required.",
        )
    active_elsewhere = (
        await db.scalars(
            select(TeamRosterEntry)
            .where(
                TeamRosterEntry.athlete_profile_id == athlete.id,
                TeamRosterEntry.team_id != team.id,
                TeamRosterEntry.status.in_(active_roster_statuses()),
            )
            .limit(1)
        )
    ).first()
    return eligibility_check(
        "transfer_clearance",
        "Transfer clearance",
        "blocker" if active_elsewhere else "pass",
        "critical",
        "Athlete has an active roster record on another team and no approved transfer clearance."
        if active_elsewhere
        else "No prior active team transfer clearance is required.",
        "Create and approve a transfer clearance before competition registration."
        if active_elsewhere
        else "No action required.",
    )


async def medical_clearance_check(
    db: AsyncSession,
    organization_id: UUID,
    athlete: AthleteProfile,
    person: Person,
    as_of: date,
) -> dict[str, str]:
    clearance = await db.scalar(
        select(IncidentMedicalClearance)
        .where(
            IncidentMedicalClearance.organization_id == organization_id,
            IncidentMedicalClearance.athlete_person_id == athlete.person_id,
        )
        .order_by(IncidentMedicalClearance.assessed_at.desc(), IncidentMedicalClearance.created_at.desc())
    )
    if clearance is None:
        return eligibility_check(
            "medical_clearance",
            "Medical clearance",
            "blocker",
            "critical",
            f"No medical clearance is on file for {person.display_name}.",
            "Record a cleared medical review or disable this rule only where competition policy allows.",
        )
    valid_date = clearance.valid_until is None or clearance.valid_until >= as_of
    clear = clearance.status == MedicalClearanceStatus.CLEARED and valid_date
    return eligibility_check(
        "medical_clearance",
        "Medical clearance",
        "pass" if clear else "blocker",
        "critical",
        f"Medical clearance status is {clearance.status}."
        if valid_date
        else f"Medical clearance expired on {clearance.valid_until}.",
        "Update the medical clearance before match participation."
        if not clear
        else "No action required.",
    )


async def compliance_credential_check(
    db: AsyncSession,
    organization_id: UUID,
    person: Person,
    as_of: date,
) -> dict[str, str]:
    credential = await db.scalar(
        select(ComplianceCredential)
        .where(
            ComplianceCredential.organization_id == organization_id,
            ComplianceCredential.person_id == person.id,
        )
        .order_by(ComplianceCredential.expires_at.desc(), ComplianceCredential.created_at.desc())
    )
    if credential is None:
        return eligibility_check(
            "compliance_credential",
            "Compliance credential",
            "blocker",
            "warning",
            f"No required compliance credential is on file for {person.display_name}.",
            "Verify the credential required by this competition.",
        )
    valid_date = credential.expires_at is None or credential.expires_at >= as_of
    clear = credential.status == ComplianceCredentialStatus.VERIFIED and valid_date
    return eligibility_check(
        "compliance_credential",
        "Compliance credential",
        "pass" if clear else "blocker",
        "warning",
        f"Credential {credential.title} is {credential.status}."
        if valid_date
        else f"Credential {credential.title} expired on {credential.expires_at}.",
        "Verify or renew the credential before competition participation."
        if not clear
        else "No action required.",
    )


def status_policy_check(
    key: str,
    label: str,
    value: str | None,
    clear_values: set[str],
) -> list[dict[str, str]]:
    if value is None:
        return []
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return [
        eligibility_check(
            key,
            label,
            "pass" if normalized in clear_values else "blocker",
            "warning",
            f"{label} is recorded as {value}.",
            "Resolve the status with the competition registrar before issuing clearance."
            if normalized not in clear_values
            else "No action required.",
        )
    ]


def eligibility_check(
    key: str,
    label: str,
    status_value: str,
    severity: str,
    detail: str,
    recommendation: str,
) -> dict[str, str]:
    return {
        "key": key,
        "label": label,
        "status": status_value,
        "severity": severity,
        "detail": detail,
        "recommendation": recommendation,
    }


def active_roster_statuses() -> tuple[RosterStatus, ...]:
    return (
        RosterStatus.ACTIVE,
        RosterStatus.STARTER,
        RosterStatus.BENCH,
        RosterStatus.SUBSTITUTE,
        RosterStatus.RESERVE,
    )


def approved_transfer_statuses() -> set[str]:
    return {"approved", "cleared", "completed", "registered"}


def academic_clear_statuses() -> set[str]:
    return {"eligible", "clear", "good", "verified", "not_applicable", "na"}


def citizenship_clear_statuses() -> set[str]:
    return {"eligible", "clear", "verified", "resident", "citizen", "not_applicable", "na"}


def disciplinary_clear_statuses() -> set[str]:
    return {"clear", "none", "good", "no_open_case", "not_applicable", "na"}


def athlete_age_on(born_on: date | None, as_of: date) -> int | None:
    if born_on is None:
        return None
    years = as_of.year - born_on.year
    if (as_of.month, as_of.day) < (born_on.month, born_on.day):
        years -= 1
    return years


def eligibility_summary(
    athlete_name: str,
    team_name: str,
    competition_name: str,
    blocker_count: int,
    warning_count: int,
) -> str:
    if blocker_count:
        return (
            f"{athlete_name} is not yet eligible for {team_name} in {competition_name}: "
            f"{blocker_count} blocking issue(s), {warning_count} warning(s)."
        )
    if warning_count:
        return (
            f"{athlete_name} is eligible for {team_name} in {competition_name} "
            f"with {warning_count} registrar warning(s)."
        )
    return f"{athlete_name} is eligible for {team_name} in {competition_name}."


def competition_eligibility_certificate_number(
    competition_id: UUID,
    athlete_profile_id: UUID,
    team_id: UUID,
) -> str:
    return f"AFL-ELG-{competition_id.hex[:8]}-{athlete_profile_id.hex[:8]}-{team_id.hex[:6]}"


def athlete_transfer_row(
    transfer: AthleteTransferRecord,
    athlete_name: str,
    from_team_name: str | None,
    to_team_name: str,
) -> dict[str, object]:
    return {
        "id": transfer.id,
        "organization_id": transfer.organization_id,
        "athlete_profile_id": transfer.athlete_profile_id,
        "athlete_name": athlete_name,
        "from_team_id": transfer.from_team_id,
        "from_team_name": from_team_name,
        "to_team_id": transfer.to_team_id,
        "to_team_name": to_team_name,
        "transfer_type": transfer.transfer_type,
        "status": transfer.status,
        "requested_on": transfer.requested_on,
        "effective_on": transfer.effective_on,
        "window_label": transfer.window_label,
        "previous_registration_ref": transfer.previous_registration_ref,
        "clearance_reference": transfer.clearance_reference,
        "reviewed_by_person_id": transfer.reviewed_by_person_id,
        "decided_at": transfer.decided_at,
        "reason": transfer.reason,
        "notes": transfer.notes,
    }


def competition_eligibility_row(
    certificate: CompetitionEligibilityCertificate,
    athlete_name: str,
    team_name: str,
) -> dict[str, object]:
    return {
        "id": certificate.id,
        "organization_id": certificate.organization_id,
        "competition_id": certificate.competition_id,
        "athlete_profile_id": certificate.athlete_profile_id,
        "athlete_name": athlete_name,
        "team_id": certificate.team_id,
        "team_name": team_name,
        "transfer_record_id": certificate.transfer_record_id,
        "status": certificate.status,
        "certificate_number": certificate.certificate_number,
        "valid_from": certificate.valid_from,
        "valid_until": certificate.valid_until,
        "blocker_count": certificate.blocker_count,
        "warning_count": certificate.warning_count,
        "eligibility_summary": certificate.eligibility_summary,
        "checks": decode_certificate_checks(certificate.checks_json),
    }


def decode_certificate_checks(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    checks: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        checks.append(
            {
                "key": str(item.get("key") or "unknown"),
                "label": str(item.get("label") or "Eligibility check"),
                "status": str(item.get("status") or "warning"),
                "severity": str(item.get("severity") or "warning"),
                "detail": str(item.get("detail") or ""),
                "recommendation": str(item.get("recommendation") or ""),
            }
        )
    return checks


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


async def get_competition_fixture(
    db: AsyncSession,
    fixture_id: UUID,
    competition_id: UUID,
) -> CompetitionFixture:
    fixture = await get_fixture(db, fixture_id)
    if fixture.competition_id != competition_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fixture not found")
    return fixture


async def ensure_fixture_event(
    db: AsyncSession,
    identity: CurrentIdentity,
    competition: Competition,
    fixture: CompetitionFixture,
    authz: AuthorizationService,
) -> Event:
    if fixture.event_id is not None:
        event = await db.get(Event, fixture.event_id)
        if event is not None and event.organization_id == competition.organization_id:
            return event

    event = Event(
        organization_id=competition.organization_id,
        team_id=fixture.home_team_id,
        event_type=EventType.MATCH,
        title=default_fixture_event_title(competition, fixture),
        starts_at=fixture.scheduled_at,
        ends_at=None,
        timezone="UTC",
        venue_name=fixture.venue_name,
        notes=f"Ticketed fixture for {competition.name}.",
    )
    db.add(event)
    await db.flush()
    fixture.event_id = event.id
    await authz.touch(
        Relationship(
            resource_type="event",
            resource_id=str(event.id),
            relation="organizer",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    )
    await authz.touch(
        Relationship(
            resource_type="event",
            resource_id=str(event.id),
            relation="parent_org",
            subject_type="organization",
            subject_id=str(competition.organization_id),
        )
    )
    await authz.touch(
        Relationship(
            resource_type="event",
            resource_id=str(event.id),
            relation="team",
            subject_type="team",
            subject_id=str(fixture.home_team_id),
        )
    )
    return event


def competition_ticketing_row(
    competition_id: UUID,
    fixture: CompetitionFixture,
    product: TicketProduct,
) -> dict[str, object]:
    return {
        "competition_id": competition_id,
        "fixture_id": fixture.id,
        "event_id": product.event_id,
        "ticket_product_id": product.id,
        "name": product.name,
        "price": product.price,
        "currency": product.currency,
        "capacity": product.capacity,
        "sold_count": product.sold_count,
        "access_zone": product.access_zone,
        "status": product.status,
        "scheduled_at": fixture.scheduled_at,
        "venue_name": fixture.venue_name,
    }


def default_ticket_product_name(
    competition: Competition,
    fixture: CompetitionFixture,
) -> str:
    round_label = fixture.round_label or "fixture"
    return f"{competition.name} {round_label} admission"


def default_fixture_event_title(
    competition: Competition,
    fixture: CompetitionFixture,
) -> str:
    round_label = fixture.round_label or "Fixture"
    return f"{competition.name} {round_label}"


def fixture_ticketing_notes(existing: str | None, product_name: str) -> str:
    entry = f"Ticket sales opened for {product_name}."
    if existing and entry not in existing:
        return f"{existing}\n{entry}"
    return existing or entry


async def get_team_for_organization(db: AsyncSession, team_id: UUID, organization_id: UUID) -> Team:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


async def get_athlete_for_organization(
    db: AsyncSession,
    athlete_profile_id: UUID,
    organization_id: UUID,
) -> tuple[AthleteProfile, Person]:
    row = await db.execute(
        select(AthleteProfile, Person)
        .join(Person, Person.id == AthleteProfile.person_id)
        .where(
            AthleteProfile.id == athlete_profile_id,
            AthleteProfile.organization_id == organization_id,
        )
    )
    result = row.first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    athlete, person = result
    return athlete, person


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
