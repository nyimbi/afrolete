from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.communication import (
    CommunicationDispatchSummary,
    CommunicationMessageCreate,
    CommunicationMessageRead,
    CommunicationTemplateCreate,
    CommunicationTemplateRead,
    DeliveryWebhookEvent,
    MessageRecipientRead,
    MessageRecipientUpdate,
    NotificationPreferenceRead,
    NotificationPreferenceUpsert,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.communications import (
    create_message,
    create_template,
    dispatch_message,
    list_messages,
    list_recipients,
    list_templates,
    record_delivery_event,
    update_recipient_status,
    upsert_preference,
)

router = APIRouter(prefix="/communications", tags=["communications"])


def to_template_read(template) -> CommunicationTemplateRead:
    return CommunicationTemplateRead(
        id=template.id,
        organization_id=template.organization_id,
        name=template.name,
        message_type=template.message_type,
        channel=template.channel,
        subject_template=template.subject_template,
        body_template=template.body_template,
        variables=template.variables,
        status=template.status,
    )


def to_message_read(message, recipient_count: int = 0) -> CommunicationMessageRead:
    return CommunicationMessageRead(
        id=message.id,
        organization_id=message.organization_id,
        template_id=message.template_id,
        created_by_person_id=message.created_by_person_id,
        message_type=message.message_type,
        channel=message.channel,
        scope_type=message.scope_type,
        scope_id=message.scope_id,
        subject=message.subject,
        body=message.body,
        urgent=message.urgent,
        quiet_hours_override=message.quiet_hours_override,
        scheduled_for=message.scheduled_for,
        sent_at=message.sent_at,
        status=message.status,
        recipient_count=recipient_count,
    )


def to_recipient_read(recipient, person) -> MessageRecipientRead:
    return MessageRecipientRead(
        id=recipient.id,
        message_id=recipient.message_id,
        person_id=recipient.person_id,
        person_name=person.display_name,
        destination=recipient.destination,
        delivery_status=recipient.delivery_status,
        delivered_at=recipient.delivered_at,
        read_at=recipient.read_at,
        failure_reason=recipient.failure_reason,
    )


def to_preference_read(preference) -> NotificationPreferenceRead:
    return NotificationPreferenceRead(
        id=preference.id,
        organization_id=preference.organization_id,
        person_id=preference.person_id,
        frequency=preference.frequency,
        channel_preference=preference.channel_preference,
        language=preference.language,
        quiet_hours_start=preference.quiet_hours_start,
        quiet_hours_end=preference.quiet_hours_end,
        emergency_override=preference.emergency_override,
    )


@router.post("/templates", response_model=CommunicationTemplateRead, status_code=201)
async def create_template_route(
    payload: CommunicationTemplateCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommunicationTemplateRead:
    return to_template_read(await create_template(db, identity, payload, authz))


@router.get("/templates", response_model=list[CommunicationTemplateRead])
async def list_templates_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[CommunicationTemplateRead]:
    return [to_template_read(template) for template in await list_templates(db, organization_id)]


@router.post("/messages", response_model=CommunicationMessageRead, status_code=201)
async def create_message_route(
    payload: CommunicationMessageCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommunicationMessageRead:
    message = await create_message(db, identity, payload, authz)
    recipients = await list_recipients(db, message.id)
    return to_message_read(message, recipient_count=len(recipients))


@router.get("/messages", response_model=list[CommunicationMessageRead])
async def list_messages_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[CommunicationMessageRead]:
    return [
        to_message_read(message, recipient_count)
        for message, recipient_count in await list_messages(db, organization_id)
    ]


@router.get("/messages/{message_id}/recipients", response_model=list[MessageRecipientRead])
async def list_recipients_route(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[MessageRecipientRead]:
    return [to_recipient_read(recipient, person) for recipient, person in await list_recipients(db, message_id)]


@router.post("/messages/{message_id}/dispatch", response_model=CommunicationDispatchSummary)
async def dispatch_message_route(
    message_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommunicationDispatchSummary:
    return await dispatch_message(db, identity, message_id, authz)


@router.patch("/recipients/{recipient_id}", response_model=MessageRecipientRead)
async def update_recipient_route(
    recipient_id: UUID,
    payload: MessageRecipientUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MessageRecipientRead:
    recipient = await update_recipient_status(db, identity, recipient_id, payload, authz)
    rows = await list_recipients(db, recipient.message_id)
    _, person = next(row for row in rows if row[0].id == recipient.id)
    return to_recipient_read(recipient, person)


@router.post("/delivery-events", response_model=MessageRecipientRead)
async def record_delivery_event_route(
    payload: DeliveryWebhookEvent,
    x_afrolete_delivery_key: str | None = Header(default=None, alias="X-Afrolete-Delivery-Key"),
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> MessageRecipientRead:
    if settings.communication_webhook_key:
        if x_afrolete_delivery_key != settings.communication_webhook_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif settings.env != "local":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    recipient = await record_delivery_event(db, payload)
    rows = await list_recipients(db, recipient.message_id)
    _, person = next(row for row in rows if row[0].id == recipient.id)
    return to_recipient_read(recipient, person)


@router.put("/preferences", response_model=NotificationPreferenceRead)
async def upsert_preference_route(
    payload: NotificationPreferenceUpsert,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> NotificationPreferenceRead:
    return to_preference_read(await upsert_preference(db, identity, payload, authz))
