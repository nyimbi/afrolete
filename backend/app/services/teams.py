from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Person
from app.models.enums import TeamRole
from app.models.team import (
    AthleteProfile,
    Team,
    TeamCommittee,
    TeamCommitteeMembership,
    TeamRosterEntry,
)
from app.schemas.team import TeamCommitteeCreate, TeamCommitteeMemberAdd, TeamCreate, TeamMemberAdd
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship


def team_member_relation(role: TeamRole) -> str:
    if role == TeamRole.PLAYER:
        return "athlete"
    return role.value


async def create_team(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: TeamCreate,
    authz: AuthorizationService,
) -> Team:
    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(payload.organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        can_manage = await authz.check(
            resource_type="organization",
            resource_id=str(payload.organization_id),
            permission="manage",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    team = Team(
        organization_id=payload.organization_id,
        name=payload.name,
        sport=payload.sport,
        sport_format=payload.sport_format,
        age_group=payload.age_group,
        gender_category=payload.gender_category,
        season_label=payload.season_label,
    )
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
    return team


async def list_teams_for_organization(
    db: AsyncSession,
    organization_id: UUID,
) -> list[Team]:
    return list(
        (
            await db.scalars(
                select(Team).where(Team.organization_id == organization_id).order_by(Team.name)
            )
        ).all()
    )


async def add_team_member(
    db: AsyncSession,
    identity: CurrentIdentity,
    team_id: UUID,
    payload: TeamMemberAdd,
    authz: AuthorizationService,
) -> TeamRosterEntry:
    team = await db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    can_manage = await authz.check(
        resource_type="team",
        resource_id=str(team_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        can_manage = await authz.check(
            resource_type="organization",
            resource_id=str(team.organization_id),
            permission="manage_roster",
            subject_type="user",
            subject_id=str(identity.user_id),
        ) or await authz.check(
            resource_type="organization",
            resource_id=str(team.organization_id),
            permission="manage",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

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

    existing = await db.scalar(
        select(TeamRosterEntry).where(
            TeamRosterEntry.team_id == team_id,
            TeamRosterEntry.athlete_profile_id == athlete_profile.id,
        )
    )
    if existing is not None:
        return existing

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
    return roster_entry


async def create_team_committee(
    db: AsyncSession,
    identity: CurrentIdentity,
    team_id: UUID,
    payload: TeamCommitteeCreate,
    authz: AuthorizationService,
) -> TeamCommittee:
    team = await db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(team.organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=403, detail="Forbidden")

    committee = TeamCommittee(team_id=team_id, name=payload.name, mandate=payload.mandate)
    db.add(committee)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="team",
            resource_id=str(team_id),
            relation="committee",
            subject_type="team_committee",
            subject_id=str(committee.id),
        )
    )
    await db.commit()
    await db.refresh(committee)
    return committee


async def add_team_committee_member(
    db: AsyncSession,
    identity: CurrentIdentity,
    team_committee_id: UUID,
    payload: TeamCommitteeMemberAdd,
    authz: AuthorizationService,
) -> TeamCommitteeMembership:
    committee = await db.get(TeamCommittee, team_committee_id)
    if committee is None:
        raise HTTPException(status_code=404, detail="Team committee not found")

    team = await db.get(Team, committee.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(team.organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=403, detail="Forbidden")

    person = await db.get(Person, payload.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    existing = await db.scalar(
        select(TeamCommitteeMembership).where(
            TeamCommitteeMembership.team_committee_id == team_committee_id,
            TeamCommitteeMembership.person_id == payload.person_id,
            TeamCommitteeMembership.role == payload.role,
        )
    )
    if existing is not None:
        return existing

    membership = TeamCommitteeMembership(
        team_committee_id=team_committee_id,
        person_id=payload.person_id,
        role=payload.role,
        title=payload.title,
    )
    db.add(membership)
    await authz.touch(
        Relationship(
            resource_type="team_committee",
            resource_id=str(team_committee_id),
            relation=payload.role.value,
            subject_type="person",
            subject_id=str(payload.person_id),
        )
    )
    await db.commit()
    await db.refresh(membership)
    return membership
