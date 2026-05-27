from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    ChannelPreference,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    MessageDeliveryStatus,
    NotificationFrequency,
)


class CommunicationTemplateCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    message_type: CommunicationMessageType
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    subject_template: str = Field(min_length=2, max_length=240)
    body_template: str = Field(min_length=2, max_length=8000)
    variables: str | None = Field(default=None, max_length=4000)


class CommunicationTemplateRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    message_type: CommunicationMessageType
    channel: CommunicationChannel
    subject_template: str
    body_template: str
    variables: str | None
    status: str


class CommunicationMessageCreate(BaseModel):
    organization_id: UUID
    template_id: UUID | None = None
    message_type: CommunicationMessageType
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    scope_type: CommunicationScopeType
    scope_id: UUID
    recipient_person_ids: list[UUID] = Field(default_factory=list)
    subject: str = Field(min_length=2, max_length=240)
    body: str = Field(min_length=2, max_length=8000)
    urgent: bool = False
    quiet_hours_override: bool = False
    scheduled_for: datetime | None = None
    copy_guardians_for_minors: bool = True

    @model_validator(mode="after")
    def emergency_can_override_quiet_hours(self) -> "CommunicationMessageCreate":
        if self.quiet_hours_override and not self.urgent:
            raise ValueError("quiet_hours_override requires urgent=true")
        return self


class CommunicationMessageRead(BaseModel):
    id: UUID
    organization_id: UUID
    template_id: UUID | None
    created_by_person_id: UUID | None
    message_type: CommunicationMessageType
    channel: CommunicationChannel
    scope_type: CommunicationScopeType
    scope_id: UUID
    subject: str
    body: str
    urgent: bool
    quiet_hours_override: bool
    scheduled_for: datetime | None
    sent_at: datetime | None
    status: str
    recipient_count: int = 0


class MessageRecipientRead(BaseModel):
    id: UUID
    message_id: UUID
    person_id: UUID
    person_name: str
    destination: str | None
    delivery_status: MessageDeliveryStatus
    delivered_at: datetime | None
    read_at: datetime | None
    failure_reason: str | None


class MessageRecipientUpdate(BaseModel):
    delivery_status: MessageDeliveryStatus
    failure_reason: str | None = Field(default=None, max_length=2000)


class CommunicationDispatchSummary(BaseModel):
    message_id: UUID
    attempted: int
    sent: int
    delivered: int
    failed: int
    suppressed: int
    queued: int
    transport_mode: str


class DeliveryWebhookEvent(BaseModel):
    recipient_id: UUID
    delivery_status: MessageDeliveryStatus
    failure_reason: str | None = Field(default=None, max_length=2000)
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class NotificationPreferenceUpsert(BaseModel):
    organization_id: UUID
    person_id: UUID
    frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    channel_preference: ChannelPreference = ChannelPreference.ALL
    language: str = Field(default="en", min_length=2, max_length=16)
    quiet_hours_start: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    quiet_hours_end: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    emergency_override: bool = True


class NotificationPreferenceRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    frequency: NotificationFrequency
    channel_preference: ChannelPreference
    language: str
    quiet_hours_start: str | None
    quiet_hours_end: str | None
    emergency_override: bool
