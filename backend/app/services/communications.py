from datetime import UTC, date, datetime
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.communication import (
    CommunicationMessage,
    CommunicationTemplate,
    MessageRecipient,
    NotificationPreference,
)
from app.models.enums import (
    ChannelPreference,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    MemberSubjectType,
    MessageDeliveryStatus,
    NotificationFrequency,
)
from app.models.event import AttendanceRecord, Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.communication import (
    CommunicationDigestCreate,
    CommunicationDigestRead,
    CommunicationDigestRunCreate,
    CommunicationDigestRunRead,
    CommunicationDigestWorkerRunRead,
    CommunicationDispatchSummary,
    CommunicationDraftRead,
    CommunicationDraftRequest,
    CommunicationEscalationRunCreate,
    CommunicationEscalationRunRead,
    CommunicationMessageCreate,
    CommunicationTemplateCreate,
    DeliveryWebhookEvent,
    MessageRecipientUpdate,
    NotificationPreferenceUpsert,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.secrets import resolve_secret


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


async def create_message_for_recipients(
    db: AsyncSession,
    *,
    organization_id: UUID,
    message_type: CommunicationMessageType,
    channel: CommunicationChannel,
    scope_type: CommunicationScopeType,
    scope_id: UUID,
    recipient_person_ids: list[UUID],
    subject: str,
    body: str,
    urgent: bool = False,
    quiet_hours_override: bool = False,
    scheduled_for: datetime | None = None,
    created_by_person_id: UUID | None = None,
) -> CommunicationMessage:
    await get_organization(db, organization_id)
    recipient_ids = list(dict.fromkeys(recipient_person_ids))
    if not recipient_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No recipients")
    message = CommunicationMessage(
        organization_id=organization_id,
        template_id=None,
        created_by_person_id=created_by_person_id,
        message_type=message_type,
        channel=channel,
        scope_type=scope_type,
        scope_id=scope_id,
        subject=subject,
        body=body,
        urgent=urgent,
        quiet_hours_override=quiet_hours_override,
        scheduled_for=scheduled_for,
        sent_at=datetime.now(UTC) if scheduled_for is None else None,
        status="sent" if scheduled_for is None else "scheduled",
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
                destination=destination_for_channel(person, channel),
                delivery_status=initial_delivery_status(person, channel),
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


async def list_inbox_items(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    person_id: UUID,
    authz: AuthorizationService,
) -> list[tuple[MessageRecipient, CommunicationMessage]]:
    await ensure_view_person_messages(db, identity, organization_id, person_id, authz)
    rows = (
        await db.execute(
            select(MessageRecipient, CommunicationMessage)
            .join(CommunicationMessage, CommunicationMessage.id == MessageRecipient.message_id)
            .where(CommunicationMessage.organization_id == organization_id)
            .where(MessageRecipient.person_id == person_id)
            .order_by(
                CommunicationMessage.urgent.desc(),
                CommunicationMessage.sent_at.desc().nullslast(),
                CommunicationMessage.created_at.desc(),
            )
        )
    ).all()
    return list(rows)


async def inbox_rows_for_person(
    db: AsyncSession,
    organization_id: UUID,
    person_id: UUID,
) -> list[tuple[MessageRecipient, CommunicationMessage]]:
    rows = (
        await db.execute(
            select(MessageRecipient, CommunicationMessage)
            .join(CommunicationMessage, CommunicationMessage.id == MessageRecipient.message_id)
            .where(CommunicationMessage.organization_id == organization_id)
            .where(MessageRecipient.person_id == person_id)
            .order_by(
                CommunicationMessage.urgent.desc(),
                CommunicationMessage.sent_at.desc().nullslast(),
                CommunicationMessage.created_at.desc(),
            )
        )
    ).all()
    return list(rows)


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


async def mark_inbox_item_read(
    db: AsyncSession,
    identity: CurrentIdentity,
    recipient_id: UUID,
    authz: AuthorizationService,
) -> MessageRecipient:
    recipient = await db.get(MessageRecipient, recipient_id)
    if recipient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
    message = await get_message(db, recipient.message_id)
    if identity.person_id != recipient.person_id:
        await ensure_manage_communications(authz, identity, message.organization_id)

    now = datetime.now(UTC)
    recipient.delivery_status = MessageDeliveryStatus.READ
    recipient.delivered_at = recipient.delivered_at or now
    recipient.read_at = now
    recipient.failure_reason = None

    await db.commit()
    await db.refresh(recipient)
    return recipient


async def create_digest(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CommunicationDigestCreate,
    authz: AuthorizationService,
) -> CommunicationDigestRead:
    await ensure_view_person_messages(db, identity, payload.organization_id, payload.person_id, authz)
    return await create_digest_for_person(
        db,
        payload.organization_id,
        payload.person_id,
        payload.frequency,
        channel=payload.channel,
        created_by_person_id=identity.person_id,
    )


async def create_digest_for_person(
    db: AsyncSession,
    organization_id: UUID,
    person_id: UUID,
    frequency: NotificationFrequency = NotificationFrequency.DAILY_DIGEST,
    *,
    channel: CommunicationChannel | None = None,
    created_by_person_id: UUID | None = None,
) -> CommunicationDigestRead:
    rows = await inbox_rows_for_person(db, organization_id, person_id)
    source_rows = digest_source_rows(rows)
    person = await db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    channel = channel or await digest_channel_for_person(db, organization_id, person_id)
    subject = f"Digest: {frequency.value.replace('_', ' ')}"
    body = digest_body(person, source_rows)
    now = datetime.now(UTC)

    message = CommunicationMessage(
        organization_id=organization_id,
        template_id=None,
        created_by_person_id=created_by_person_id,
        message_type=CommunicationMessageType.REPORT,
        channel=channel,
        scope_type=CommunicationScopeType.PERSON,
        scope_id=person_id,
        subject=subject,
        body=body,
        urgent=False,
        quiet_hours_override=False,
        scheduled_for=None,
        sent_at=now,
        status="sent",
    )
    db.add(message)
    await db.flush()

    recipient = MessageRecipient(
        message_id=message.id,
        person_id=person_id,
        destination=destination_for_channel(person, channel),
        delivery_status=MessageDeliveryStatus.DELIVERED
        if channel == CommunicationChannel.IN_APP
        else initial_delivery_status(person, channel),
        delivered_at=now if channel == CommunicationChannel.IN_APP else None,
    )
    db.add(recipient)
    await db.commit()
    await db.refresh(message)
    await db.refresh(recipient)

    return CommunicationDigestRead(
        message_id=message.id,
        recipient_id=recipient.id,
        person_id=person_id,
        frequency=frequency,
        channel=channel,
        item_count=len(source_rows),
        subject=message.subject,
        body=message.body,
    )


async def run_digest_scheduler(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CommunicationDigestRunCreate,
    authz: AuthorizationService,
) -> CommunicationDigestRunRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_communications(authz, identity, payload.organization_id)
    return await run_digest_scheduler_for_organization(
        db,
        payload.organization_id,
        frequency=payload.frequency,
        limit=payload.limit,
        created_by_person_id=identity.person_id,
    )


async def run_digest_scheduler_for_organization(
    db: AsyncSession,
    organization_id: UUID,
    *,
    frequency: NotificationFrequency | None = None,
    limit: int = 100,
    created_by_person_id: UUID | None = None,
) -> CommunicationDigestRunRead:
    await get_organization(db, organization_id)
    if frequency == NotificationFrequency.IMMEDIATE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Digest scheduler frequency must be daily_digest or weekly_digest",
        )
    statement = select(NotificationPreference).where(
        NotificationPreference.organization_id == organization_id,
        NotificationPreference.frequency.in_(
            [NotificationFrequency.DAILY_DIGEST, NotificationFrequency.WEEKLY_DIGEST]
        ),
    )
    if frequency is not None:
        statement = statement.where(NotificationPreference.frequency == frequency)
    preferences = list(
        (await db.scalars(statement.order_by(NotificationPreference.updated_at.desc()).limit(limit))).all()
    )
    digests: list[CommunicationDigestRead] = []
    skipped = 0
    for preference in preferences:
        rows = await inbox_rows_for_person(db, organization_id, preference.person_id)
        source_rows = digest_source_rows(rows)
        if not source_rows:
            skipped += 1
            continue
        digests.append(
            await create_digest_for_person(
                db,
                organization_id,
                preference.person_id,
                preference.frequency,
                created_by_person_id=created_by_person_id,
            )
        )
    return CommunicationDigestRunRead(
        organization_id=organization_id,
        frequency=frequency,
        considered=len(preferences),
        created=len(digests),
        skipped=skipped,
        digests=digests,
    )


async def run_digest_scheduler_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    frequency: NotificationFrequency | None = None,
    limit: int = 100,
) -> CommunicationDigestWorkerRunRead:
    organization_ids = await digest_scheduler_organization_ids(db, organization_id, frequency, limit)
    executed_count = 0
    created_count = 0
    skipped_count = 0
    failed_count = 0
    digest_message_ids: list[UUID] = []

    for org_id in organization_ids:
        try:
            result = await run_digest_scheduler_for_organization(
                db,
                org_id,
                frequency=frequency,
                limit=limit,
            )
            executed_count += 1
            created_count += result.created
            skipped_count += result.skipped
            digest_message_ids.extend(digest.message_id for digest in result.digests)
        except Exception:
            failed_count += 1
            await db.rollback()

    return CommunicationDigestWorkerRunRead(
        organization_id=organization_id,
        frequency=frequency,
        eligible_count=len(organization_ids),
        executed_count=executed_count,
        created_count=created_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        organization_ids=organization_ids,
        digest_message_ids=digest_message_ids,
    )


async def draft_message(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CommunicationDraftRequest,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> CommunicationDraftRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_communications(authz, identity, payload.organization_id)
    await validate_message_scope(db, payload.organization_id, payload.scope_type, payload.scope_id)
    settings = settings or get_settings()
    scope_label = await scope_display_name(db, payload.scope_type, payload.scope_id)
    subject = clamp_text(f"{scope_label}: {payload.intent.strip()}", 240)
    guardian_line = (
        "Guardians are copied where safeguarding rules require it. "
        if payload.include_guardian_context
        else ""
    )
    body = (
        f"Hello {payload.audience},\n\n"
        f"{payload.intent.strip()}\n\n"
        f"Tone: {payload.tone.strip()}. {guardian_line}"
        "Please review the details, confirm any required action, and contact the organization "
        "if anything looks incorrect.\n\n"
        "AfroLete"
    )
    return CommunicationDraftRead(
        subject=subject,
        body=body[:8000],
        model_name=settings.agent_default_model,
        rationale=(
            "Deterministic AI-assist draft generated from message intent, audience, scope, "
            "and safeguarding context; human review remains required."
        ),
    )


async def dispatch_message(
    db: AsyncSession,
    identity: CurrentIdentity,
    message_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> CommunicationDispatchSummary:
    message = await get_message(db, message_id)
    await ensure_manage_communications(authz, identity, message.organization_id)
    settings = settings or get_settings()
    rows = await list_recipients(db, message.id)
    now = datetime.now(UTC)

    async with httpx.AsyncClient(timeout=settings.communication_delivery_timeout_seconds) as client:
        for recipient, person in rows:
            if recipient.delivery_status in {
                MessageDeliveryStatus.DELIVERED,
                MessageDeliveryStatus.READ,
                MessageDeliveryStatus.SUPPRESSED,
            }:
                continue

            if recipient.destination is None:
                recipient.delivery_status = MessageDeliveryStatus.SUPPRESSED
                recipient.failure_reason = "No destination for channel"
                continue

            if message.channel == CommunicationChannel.IN_APP:
                recipient.delivery_status = MessageDeliveryStatus.DELIVERED
                recipient.delivered_at = recipient.delivered_at or now
                recipient.failure_reason = None
                continue

            webhook_url = delivery_webhook_url_for(settings, message.channel)
            if settings.communication_delivery_mode != "webhook" or webhook_url is None:
                recipient.delivery_status = MessageDeliveryStatus.QUEUED
                recipient.failure_reason = f"No {message.channel.value} delivery webhook configured"
                continue

            await deliver_recipient(client, webhook_url, settings, message, recipient, person, now)

    await db.commit()
    return dispatch_summary(message.id, rows, settings.communication_delivery_mode)


async def run_message_escalation(
    db: AsyncSession,
    identity: CurrentIdentity,
    message_id: UUID,
    payload: CommunicationEscalationRunCreate,
    authz: AuthorizationService,
) -> CommunicationEscalationRunRead:
    message = await get_message(db, message_id)
    await ensure_manage_communications(authz, identity, message.organization_id)
    if not message.urgent:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only urgent messages can be escalated")
    rows = await list_recipients(db, message.id)
    pending_statuses = (
        {MessageDeliveryStatus.FAILED}
        if payload.failed_only
        else {
            MessageDeliveryStatus.QUEUED,
            MessageDeliveryStatus.FAILED,
            MessageDeliveryStatus.SUPPRESSED,
        }
    )
    targets = [recipient for recipient, _person in rows if recipient.delivery_status in pending_statuses]
    skipped_count = len(rows) - len(targets)
    channel = payload.channel or escalation_channel(message.channel)
    subject = payload.subject or f"Escalation L{payload.escalation_level}: {message.subject}"[:240]
    body = payload.body or escalation_body(message, targets, payload.escalation_level)
    if not targets:
        return CommunicationEscalationRunRead(
            original_message_id=message.id,
            escalation_message_id=None,
            channel=channel,
            escalation_level=payload.escalation_level,
            target_count=0,
            skipped_count=skipped_count,
            recipient_count=0,
            subject=subject,
            message="No unresolved urgent recipients need escalation.",
        )

    target_ids = [recipient.person_id for recipient in targets]
    escalation = await create_message(
        db,
        identity,
        CommunicationMessageCreate(
            organization_id=message.organization_id,
            message_type=message.message_type,
            channel=channel,
            scope_type=CommunicationScopeType.PERSON,
            scope_id=target_ids[0],
            recipient_person_ids=target_ids,
            subject=subject,
            body=body,
            urgent=True,
            quiet_hours_override=True,
            copy_guardians_for_minors=False,
        ),
        authz,
    )
    recipients = await list_recipients(db, escalation.id)
    return CommunicationEscalationRunRead(
        original_message_id=message.id,
        escalation_message_id=escalation.id,
        channel=channel,
        escalation_level=payload.escalation_level,
        target_count=len(targets),
        skipped_count=skipped_count,
        recipient_count=len(recipients),
        subject=subject,
        message=f"Escalated urgent message to {len(recipients)} unresolved recipients.",
    )


async def record_delivery_event(
    db: AsyncSession,
    payload: DeliveryWebhookEvent,
) -> MessageRecipient:
    recipient = await db.get(MessageRecipient, payload.recipient_id)
    if recipient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    now = datetime.now(UTC)
    recipient.delivery_status = payload.delivery_status
    recipient.failure_reason = payload.failure_reason
    if payload.delivery_status in {
        MessageDeliveryStatus.DELIVERED,
        MessageDeliveryStatus.READ,
    }:
        recipient.delivered_at = payload.delivered_at or recipient.delivered_at or now
    if payload.delivery_status == MessageDeliveryStatus.READ:
        recipient.read_at = payload.read_at or now

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


async def ensure_view_person_messages(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    person_id: UUID,
    authz: AuthorizationService,
) -> None:
    await ensure_person_in_organization_context(db, organization_id, person_id)
    if identity.person_id == person_id:
        return
    await ensure_manage_communications(authz, identity, organization_id)


async def validate_message_scope(
    db: AsyncSession,
    organization_id: UUID,
    scope_type: CommunicationScopeType,
    scope_id: UUID,
) -> None:
    if scope_type == CommunicationScopeType.ORGANIZATION:
        await get_organization(db, scope_id)
        if scope_id != organization_id:
            raise HTTPException(status_code=422, detail="Organization scope must match organization_id")
    elif scope_type == CommunicationScopeType.TEAM:
        team = await db.get(Team, scope_id)
        if team is None or team.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Team not found")
    elif scope_type == CommunicationScopeType.EVENT:
        event = await db.get(Event, scope_id)
        if event is None or event.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Event not found")
    elif scope_type == CommunicationScopeType.PERSON:
        await ensure_person_in_organization_context(db, organization_id, scope_id)


async def scope_display_name(
    db: AsyncSession,
    scope_type: CommunicationScopeType,
    scope_id: UUID,
) -> str:
    if scope_type == CommunicationScopeType.ORGANIZATION:
        organization = await db.get(Organization, scope_id)
        return organization.name if organization else "Organization"
    if scope_type == CommunicationScopeType.TEAM:
        team = await db.get(Team, scope_id)
        return team.name if team else "Team"
    if scope_type == CommunicationScopeType.EVENT:
        event = await db.get(Event, scope_id)
        return event.title if event else "Event"
    person = await db.get(Person, scope_id)
    return person.display_name if person else "Member"


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


async def digest_channel_for_person(
    db: AsyncSession,
    organization_id: UUID,
    person_id: UUID,
) -> CommunicationChannel:
    preference = await db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.organization_id == organization_id,
            NotificationPreference.person_id == person_id,
        )
    )
    if preference is None:
        return CommunicationChannel.IN_APP
    return {
        ChannelPreference.EMAIL: CommunicationChannel.EMAIL,
        ChannelPreference.SMS: CommunicationChannel.SMS,
        ChannelPreference.APP: CommunicationChannel.IN_APP,
        ChannelPreference.ALL: CommunicationChannel.IN_APP,
    }[preference.channel_preference]


async def digest_scheduler_organization_ids(
    db: AsyncSession,
    organization_id: UUID | None,
    frequency: NotificationFrequency | None,
    limit: int,
) -> list[UUID]:
    if organization_id is not None:
        statement = (
            select(NotificationPreference.organization_id)
            .where(NotificationPreference.organization_id == organization_id)
            .where(
                NotificationPreference.frequency.in_(
                    [NotificationFrequency.DAILY_DIGEST, NotificationFrequency.WEEKLY_DIGEST]
                )
            )
            .limit(1)
        )
        if frequency is not None:
            statement = statement.where(NotificationPreference.frequency == frequency)
        return [organization_id] if await db.scalar(statement) is not None else []
    statement = (
        select(NotificationPreference.organization_id)
        .where(
            NotificationPreference.frequency.in_(
                [NotificationFrequency.DAILY_DIGEST, NotificationFrequency.WEEKLY_DIGEST]
            )
        )
        .group_by(NotificationPreference.organization_id)
        .order_by(func.max(NotificationPreference.updated_at).desc())
        .limit(limit)
    )
    if frequency is not None:
        statement = statement.where(NotificationPreference.frequency == frequency)
    return list((await db.scalars(statement)).all())


def digest_body(
    person: Person,
    rows: list[tuple[MessageRecipient, CommunicationMessage]],
) -> str:
    if not rows:
        return f"Hello {person.display_name},\n\nNo unread AfroLete updates need action right now."

    lines = [
        f"Hello {person.display_name},",
        "",
        f"You have {len(rows)} AfroLete update{'s' if len(rows) != 1 else ''}:",
    ]
    for index, (recipient, message) in enumerate(rows, start=1):
        status_label = recipient.delivery_status.value.replace("_", " ")
        urgent = "urgent " if message.urgent else ""
        lines.append(f"{index}. {urgent}{message.subject} ({message.channel.value}, {status_label})")
    lines.extend(["", "Open your AfroLete inbox to review details and respond where needed."])
    return "\n".join(lines)


def digest_source_rows(
    rows: list[tuple[MessageRecipient, CommunicationMessage]],
) -> list[tuple[MessageRecipient, CommunicationMessage]]:
    return [
        (recipient, message)
        for recipient, message in rows
        if recipient.delivery_status != MessageDeliveryStatus.READ
        and not message.subject.lower().startswith("digest:")
    ][:20]


def clamp_text(value: str, max_length: int) -> str:
    return value if len(value) <= max_length else f"{value[: max_length - 3]}..."


async def deliver_recipient(
    client: httpx.AsyncClient,
    webhook_url: str,
    settings: Settings,
    message: CommunicationMessage,
    recipient: MessageRecipient,
    person: Person,
    now: datetime,
) -> None:
    try:
        headers = await delivery_headers(settings)
        if headers.failure_reason:
            recipient.delivery_status = MessageDeliveryStatus.FAILED
            recipient.failure_reason = headers.failure_reason
            return
        response = await client.post(
            webhook_url,
            json=delivery_payload(message, recipient, person),
            headers=headers.headers,
        )
        if 200 <= response.status_code < 300:
            recipient.delivery_status = MessageDeliveryStatus.SENT
            recipient.failure_reason = None
            return
        recipient.delivery_status = MessageDeliveryStatus.FAILED
        recipient.failure_reason = f"Webhook returned {response.status_code}: {response.text[:400]}"
    except httpx.HTTPError as error:
        recipient.delivery_status = MessageDeliveryStatus.FAILED
        recipient.failure_reason = str(error)[:400]
    finally:
        if recipient.delivery_status == MessageDeliveryStatus.SENT and message.channel == CommunicationChannel.PUSH:
            recipient.delivered_at = recipient.delivered_at or now


def delivery_payload(
    message: CommunicationMessage,
    recipient: MessageRecipient,
    person: Person,
) -> dict[str, object]:
    return {
        "event": "afrolete.communication.dispatch",
        "channel": message.channel.value,
        "message": {
            "id": str(message.id),
            "organization_id": str(message.organization_id),
            "type": message.message_type.value,
            "scope_type": message.scope_type.value,
            "scope_id": str(message.scope_id),
            "subject": message.subject,
            "body": message.body,
            "urgent": message.urgent,
            "quiet_hours_override": message.quiet_hours_override,
        },
        "recipient": {
            "id": str(recipient.id),
            "person_id": str(recipient.person_id),
            "name": person.display_name,
            "destination": recipient.destination,
        },
    }


class DeliveryHeaderResolution:
    def __init__(self, headers: dict[str, str], failure_reason: str | None = None) -> None:
        self.headers = headers
        self.failure_reason = failure_reason


async def delivery_headers(settings: Settings) -> DeliveryHeaderResolution:
    headers = {"User-Agent": "AfroLete-Communications/1.0"}
    key_resolution = await resolve_communication_webhook_key(settings)
    if key_resolution["failure_reason"]:
        return DeliveryHeaderResolution(headers, str(key_resolution["failure_reason"]))
    if key_resolution["key"]:
        headers["X-Afrolete-Delivery-Key"] = str(key_resolution["key"])
        headers["X-Afrolete-Delivery-Key-Source"] = str(key_resolution["source"])
    return DeliveryHeaderResolution(headers)


async def resolve_communication_webhook_key(settings: Settings) -> dict[str, str | None]:
    source = "openbao" if settings.communication_webhook_key_secret_path else "env"
    try:
        secret = await resolve_secret(
            settings,
            env_value=settings.communication_webhook_key,
            path=settings.communication_webhook_key_secret_path,
            field_name=settings.communication_webhook_key_secret_field,
            label="communication webhook key",
        )
    except HTTPException as exc:
        return {"key": None, "source": "openbao", "failure_reason": str(exc.detail)}
    if not secret:
        return {"key": None, "source": "unset", "failure_reason": None}
    return {"key": secret, "source": source, "failure_reason": None}


def delivery_webhook_url_for(settings: Settings, channel: CommunicationChannel) -> str | None:
    channel_urls = {
        CommunicationChannel.EMAIL: settings.communication_email_webhook_url,
        CommunicationChannel.SMS: settings.communication_sms_webhook_url,
        CommunicationChannel.WHATSAPP: settings.communication_whatsapp_webhook_url,
        CommunicationChannel.TELEGRAM: settings.communication_telegram_webhook_url,
        CommunicationChannel.PUSH: settings.communication_push_webhook_url,
    }
    url = channel_urls.get(channel) or settings.communication_webhook_url
    return url or None


def escalation_channel(channel: CommunicationChannel) -> CommunicationChannel:
    if channel in {CommunicationChannel.PUSH, CommunicationChannel.IN_APP, CommunicationChannel.EMAIL}:
        return CommunicationChannel.SMS
    if channel == CommunicationChannel.SMS:
        return CommunicationChannel.WHATSAPP
    if channel == CommunicationChannel.WHATSAPP:
        return CommunicationChannel.TELEGRAM
    return CommunicationChannel.SMS


def escalation_body(message: CommunicationMessage, targets: list[MessageRecipient], escalation_level: int) -> str:
    lines = [
        f"Escalation level: {escalation_level}",
        f"Original message: {message.subject}",
        f"Unresolved recipients: {len(targets)}",
        "",
        message.body,
    ]
    return "\n".join(lines)[:8000]


def dispatch_summary(
    message_id: UUID,
    rows: list[tuple[MessageRecipient, Person]],
    transport_mode: str,
) -> CommunicationDispatchSummary:
    counts = {
        MessageDeliveryStatus.SENT: 0,
        MessageDeliveryStatus.DELIVERED: 0,
        MessageDeliveryStatus.FAILED: 0,
        MessageDeliveryStatus.SUPPRESSED: 0,
        MessageDeliveryStatus.QUEUED: 0,
    }
    for recipient, _ in rows:
        if recipient.delivery_status in counts:
            counts[recipient.delivery_status] += 1

    return CommunicationDispatchSummary(
        message_id=message_id,
        attempted=len(rows),
        sent=counts[MessageDeliveryStatus.SENT],
        delivered=counts[MessageDeliveryStatus.DELIVERED],
        failed=counts[MessageDeliveryStatus.FAILED],
        suppressed=counts[MessageDeliveryStatus.SUPPRESSED],
        queued=counts[MessageDeliveryStatus.QUEUED],
        transport_mode=transport_mode,
    )
