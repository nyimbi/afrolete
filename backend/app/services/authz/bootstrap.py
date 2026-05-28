from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, SafeguardingIncident
from app.models.identity import AppUser
from app.models.organization import Membership
from app.models.team import GuardianRelationship, Team
from app.services.authz.service import AuthorizationService, Relationship
from app.services.organizations import organization_member_relation


async def bootstrap_local_authorization(db: AsyncSession, authz: AuthorizationService) -> None:
    """Hydrate in-memory authz from persisted demo/local memberships."""
    rows = (
        await db.execute(
            select(Membership, AppUser)
            .join(AppUser, AppUser.person_id == Membership.subject_id)
            .where(Membership.status == "active")
        )
    ).all()
    for membership, user in rows:
        await authz.touch(
            Relationship(
                resource_type="organization",
                resource_id=str(membership.organization_id),
                relation=organization_member_relation(membership.subject_type, membership.role),
                subject_type="user",
                subject_id=str(user.id),
            )
        )

    teams = (await db.scalars(select(Team))).all()
    for team in teams:
        await authz.touch(
            Relationship(
                resource_type="organization",
                resource_id=str(team.organization_id),
                relation="member_team",
                subject_type="team",
                subject_id=str(team.id),
            )
        )

    events = (await db.scalars(select(Event))).all()
    for event in events:
        await authz.touch(
            Relationship(
                resource_type="event",
                resource_id=str(event.id),
                relation="parent_org",
                subject_type="organization",
                subject_id=str(event.organization_id),
            )
        )
        if event.team_id is not None:
            await authz.touch(
                Relationship(
                    resource_type="event",
                    resource_id=str(event.id),
                    relation="team",
                    subject_type="team",
                    subject_id=str(event.team_id),
                )
            )

    incidents = (await db.scalars(select(SafeguardingIncident))).all()
    for incident in incidents:
        await authz.touch(
            Relationship(
                resource_type="safeguarding_incident",
                resource_id=str(incident.id),
                relation="parent_org",
                subject_type="organization",
                subject_id=str(incident.organization_id),
            )
        )
        if incident.event_id is not None:
            await authz.touch(
                Relationship(
                    resource_type="safeguarding_incident",
                    resource_id=str(incident.id),
                    relation="event",
                    subject_type="event",
                    subject_id=str(incident.event_id),
                )
            )
        if incident.team_id is not None:
            await authz.touch(
                Relationship(
                    resource_type="safeguarding_incident",
                    resource_id=str(incident.id),
                    relation="team",
                    subject_type="team",
                    subject_id=str(incident.team_id),
                )
            )
        await touch_incident_person_subjects(db, authz, incident, "reporter", incident.reported_by_person_id)
        await touch_incident_person_subjects(db, authz, incident, "assigned_to", incident.assigned_to_person_id)
        await touch_incident_person_subjects(db, authz, incident, "athlete", incident.athlete_person_id)
        if incident.athlete_person_id is not None:
            guardians = (
                await db.scalars(
                    select(GuardianRelationship).where(
                        GuardianRelationship.athlete_person_id == incident.athlete_person_id
                    )
                )
            ).all()
            for guardian in guardians:
                await touch_incident_person_subjects(db, authz, incident, "guardian", guardian.guardian_person_id)
                if guardian.can_view_medical:
                    await touch_incident_person_subjects(db, authz, incident, "medical_viewer", guardian.guardian_person_id)


async def touch_incident_person_subjects(
    db: AsyncSession,
    authz: AuthorizationService,
    incident: SafeguardingIncident,
    relation: str,
    person_id,
) -> None:
    if person_id is None:
        return
    await authz.touch(
        Relationship(
            resource_type="safeguarding_incident",
            resource_id=str(incident.id),
            relation=relation,
            subject_type="person",
            subject_id=str(person_id),
        )
    )
    user_ids = (await db.scalars(select(AppUser.id).where(AppUser.person_id == person_id))).all()
    for user_id in user_ids:
        await authz.touch(
            Relationship(
                resource_type="safeguarding_incident",
                resource_id=str(incident.id),
                relation=relation,
                subject_type="user",
                subject_id=str(user_id),
            )
        )
