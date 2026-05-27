from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import (
    CommunicationMessage,
    CommunicationTemplate,
    MessageRecipient,
    NotificationPreference,
)
from app.models.enums import (
    CommunicationChannel,
    CommunicationScopeType,
    MemberSubjectType,
    MessageDeliveryStatus,
)
from app.models.event import AttendanceRecord, Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.communication import (
    CommunicationMessageCreate,
    CommunicationTemplateCreate,
    MessageRecipientUpdate,
    NotificationPreferenceUpsert,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_communications(
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


async def create_template(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CommunicationTemplateCreate,
    authz: AuthorizationService,
) -> CommunicationTemplate:
    await get_organization(db, payload.organization_id)
    await ensure_manage_communications(authz, identity, payload.organization_id)
    existing = await db.scalar(
        select(CommunicationTemplate).where(
            CommunicationTemplate.organization_id == payload.organization_id,
            CommunicationTemplate.name == payload.name,
            CommunicationTemplate.channel == payload.channel,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Template exists")

    template = CommunicationTemplate(**payload.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def list_templates(
    db: AsyncSession,
    organization_id: UUID,
) -> list[CommunicationTemplate]:
    return list(
        (
            await db.scalars(
                select(CommunicationTemplate)
                .where(CommunicationTemplate.organization_id == organization_id)
                .order_by(CommunicationTemplate.message_type, CommunicationTemplate.name)
            )
        ).all()
    )


async def create_message(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CommunicationMessageCreate,
    authz: AuthorizationService,
) -> CommunicationMessage:
    await get_organization(db, payload.organization_id)
    await ensure_manage_communications(authz, identity, payload.organization_id)
    if payload.template_id is not None:
        template = await db.get(CommunicationTemplate, payload.template_id)
        if template is None or template.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    recipient_ids = await expand_recipients(db, payload)
    if not recipient_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No recipients")

    message = CommunicationMessage(
        created_by_person_id=identity.person_id,
        status="sent" if payload.scheduled_for is None else "scheduled",
        sent_at=datetime.now(UTC) if payload.scheduled_for is None else None,
        **payload.model_dump(exclude={"recipient_person_ids", "copy_guardians_for_minors"}),
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
                person_id=person_id,
                destination=destination_for_channel(person, payload.channel),
                delivery_status=initial_delivery_status(person, payload.channel),
            )
        )

    await db.commit()
    await db.refresh(message)
    return message


async def list_messages(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[CommunicationMessage, int]]:
    rows = (
        await db.execute(
            select(CommunicationMessage, func.count(MessageRecipient.id))
            .outerjoin(MessageRecipient, MessageRecipient.message_id == CommunicationMessage.id)
            .where(CommunicationMessage.organization_id == organization_id)
            .group_by(CommunicationMessage.id)
            .order_by(CommunicationMessage.created_at.desc())
        )
    ).all()
    return [(message, int(count or 0)) for message, count in rows]


async def list_recipients(
    db: AsyncSession,
    message_id: UUID,
) -> list[tuple[MessageRecipient, Person]]:
    await get_message(db, message_id)
    return list(
        (
            await db.execute(
                select(MessageRecipient, Person)
                .join(Person, Person.id == MessageRecipient.person_id)
                .where(MessageRecipient.message_id == message_id)
                .order_by(Person.display_name)
            )
        ).all()
    )


async def update_recipient_status(
    db: AsyncSession,
    identity: CurrentIdentity,
    recipient_id: UUID,
    payload: MessageRecipientUpdate,
    authz: AuthorizationService,
) -> MessageRecipient:
    recipient = await db.get(MessageRecipient, recipient_id)
    if recipient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
    message = await get_message(db, recipient.message_id)
    await ensure_manage_communications(authz, identity, message.organization_id)

    recipient.delivery_status = payload.delivery_status
    recipient.failure_reason = payload.failure_reason
    now = datetime.now(UTC)
    if payload.delivery_status in {
        MessageDeliveryStatus.DELIVERED,
        MessageDeliveryStatus.READ,
    }:
        recipient.delivered_at = recipient.delivered_at or now
    if payload.delivery_status == MessageDeliveryStatus.READ:
        recipient.read_at = now

    await db.commit()
    await db.refresh(recipient)
    return recipient


async def upsert_preference(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: NotificationPreferenceUpsert,
    authz: AuthorizationService,
) -> NotificationPreference:
    await get_organization(db, payload.organization_id)
    await ensure_manage_communications(authz, identity, payload.organization_id)
    await ensure_person_in_organization_context(db, payload.organization_id, payload.person_id)
    existing = await db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.organization_id == payload.organization_id,
            NotificationPreference.person_id == payload.person_id,
        )
    )
    if existing is None:
        existing = NotificationPreference(**payload.model_dump())
        db.add(existing)
    else:
        for field, value in payload.model_dump().items():
            setattr(existing, field, value)
    await db.commit()
    await db.refresh(existing)
    return existing


async def get_message(db: AsyncSession, message_id: UUID) -> CommunicationMessage:
    message = await db.get(CommunicationMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def expand_recipients(
    db: AsyncSession,
    payload: CommunicationMessageCreate,
) -> set[UUID]:
    recipient_ids = set(payload.recipient_person_ids)
    if payload.scope_type == CommunicationScopeType.ORGANIZATION:
        if payload.scope_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        recipient_ids.update(await organization_member_person_ids(db, payload.organization_id))
    elif payload.scope_type == CommunicationScopeType.TEAM:
        recipient_ids.update(await team_person_ids(db, payload.organization_id, payload.scope_id))
    elif payload.scope_type == CommunicationScopeType.EVENT:
        recipient_ids.update(await event_person_ids(db, payload.organization_id, payload.scope_id))
    elif payload.scope_type == CommunicationScopeType.PERSON:
        await ensure_person_in_organization_context(db, payload.organization_id, payload.scope_id)
        recipient_ids.add(payload.scope_id)

    for person_id in list(recipient_ids):
        await ensure_person_in_organization_context(db, payload.organization_id, person_id)
        if payload.copy_guardians_for_minors and await is_minor(db, person_id):
            recipient_ids.update(await guardian_person_ids(db, person_id))
    return recipient_ids


async def organization_member_person_ids(db: AsyncSession, organization_id: UUID) -> set[UUID]:
    rows = (
        await db.execute(
            select(Membership.subject_id)
            .where(Membership.organization_id == organization_id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(Membership.status == "active")
        )
    ).all()
    return {person_id for (person_id,) in rows}


async def team_person_ids(db: AsyncSession, organization_id: UUID, team_id: UUID) -> set[UUID]:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    rows = (
        await db.execute(
            select(AthleteProfile.person_id)
            .join(TeamRosterEntry, TeamRosterEntry.athlete_profile_id == AthleteProfile.id)
            .where(TeamRosterEntry.team_id == team_id)
        )
    ).all()
    return {person_id for (person_id,) in rows}


async def event_person_ids(db: AsyncSession, organization_id: UUID, event_id: UUID) -> set[UUID]:
    event = await db.get(Event, event_id)
    if event is None or event.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    attendance_rows = (
        await db.execute(select(AttendanceRecord.person_id).where(AttendanceRecord.event_id == event_id))
    ).all()
    if attendance_rows:
        return {person_id for (person_id,) in attendance_rows}
    if event.team_id is not None:
        return await team_person_ids(db, organization_id, event.team_id)
    return set()


async def ensure_person_in_organization_context(
    db: AsyncSession,
    organization_id: UUID,
    person_id: UUID,
) -> None:
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
    if membership is not None:
        return
    athlete = await db.scalar(
        select(AthleteProfile).where(
            AthleteProfile.organization_id == organization_id,
            AthleteProfile.person_id == person_id,
        )
    )
    if athlete is not None:
        return
    guardian = await db.scalar(
        select(GuardianRelationship)
        .join(Person, Person.id == GuardianRelationship.athlete_person_id)
        .join(AthleteProfile, AthleteProfile.person_id == Person.id)
        .where(AthleteProfile.organization_id == organization_id)
        .where(GuardianRelationship.guardian_person_id == person_id)
    )
    if guardian is not None:
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")


async def is_minor(db: AsyncSession, person_id: UUID) -> bool:
    person = await db.get(Person, person_id)
    if person is None or person.date_of_birth is None:
        return False
    today = date.today()
    age = today.year - person.date_of_birth.year - (
        (today.month, today.day) < (person.date_of_birth.month, person.date_of_birth.day)
    )
    return age < 18


async def guardian_person_ids(db: AsyncSession, athlete_person_id: UUID) -> set[UUID]:
    rows = (
        await db.execute(
            select(GuardianRelationship.guardian_person_id).where(
                GuardianRelationship.athlete_person_id == athlete_person_id,
                GuardianRelationship.can_sign_consent.is_(True),
            )
        )
    ).all()
    return {person_id for (person_id,) in rows}


def destination_for_channel(person: Person, channel: CommunicationChannel) -> str | None:
    if channel == CommunicationChannel.EMAIL:
        return person.primary_email
    if channel in {
        CommunicationChannel.SMS,
        CommunicationChannel.WHATSAPP,
        CommunicationChannel.TELEGRAM,
        CommunicationChannel.PUSH,
    }:
        return person.primary_phone
    return str(person.id)


def initial_delivery_status(person: Person, channel: CommunicationChannel) -> MessageDeliveryStatus:
    destination = destination_for_channel(person, channel)
    if destination is None and channel != CommunicationChannel.IN_APP:
        return MessageDeliveryStatus.SUPPRESSED
    return MessageDeliveryStatus.QUEUED
