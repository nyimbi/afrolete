from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.identity import AppUser
from app.models.organization import Membership
from app.models.team import Team
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
