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


class CommunicationInboxItemRead(BaseModel):
    recipient_id: UUID
    message_id: UUID
    organization_id: UUID
    subject: str
    body: str
    message_type: CommunicationMessageType
    channel: CommunicationChannel
    urgent: bool
    delivery_status: MessageDeliveryStatus
    sent_at: datetime | None
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


class CommunicationEscalationRunCreate(BaseModel):
    channel: CommunicationChannel | None = None
    escalation_level: int = Field(default=2, ge=1, le=5)
    failed_only: bool = False
    subject: str | None = Field(default=None, min_length=2, max_length=240)
    body: str | None = Field(default=None, min_length=2, max_length=8000)


class CommunicationEscalationRunRead(BaseModel):
    original_message_id: UUID
    escalation_message_id: UUID | None
    channel: CommunicationChannel
    escalation_level: int
    target_count: int
    skipped_count: int
    recipient_count: int
    subject: str
    message: str


class DeliveryWebhookEvent(BaseModel):
    recipient_id: UUID
    delivery_status: MessageDeliveryStatus
    failure_reason: str | None = Field(default=None, max_length=2000)
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class CommunicationDigestCreate(BaseModel):
    organization_id: UUID
    person_id: UUID
    frequency: NotificationFrequency = NotificationFrequency.DAILY_DIGEST
    channel: CommunicationChannel | None = None


class CommunicationDigestRead(BaseModel):
    message_id: UUID
    recipient_id: UUID
    person_id: UUID
    frequency: NotificationFrequency
    channel: CommunicationChannel
    item_count: int
    subject: str
    body: str


class CommunicationDigestRunCreate(BaseModel):
    organization_id: UUID
    frequency: NotificationFrequency | None = None
    limit: int = Field(default=100, ge=1, le=500)


class CommunicationDigestRunRead(BaseModel):
    organization_id: UUID
    frequency: NotificationFrequency | None
    considered: int
    created: int
    skipped: int
    digests: list[CommunicationDigestRead]


class CommunicationDigestWorkerRunRead(BaseModel):
    organization_id: UUID | None
    frequency: NotificationFrequency | None
    eligible_count: int
    executed_count: int
    created_count: int
    skipped_count: int
    failed_count: int
    organization_ids: list[UUID]
    digest_message_ids: list[UUID]


class CommunicationDraftRequest(BaseModel):
    organization_id: UUID
    message_type: CommunicationMessageType = CommunicationMessageType.ANNOUNCEMENT
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    scope_type: CommunicationScopeType
    scope_id: UUID
    intent: str = Field(min_length=4, max_length=1000)
    tone: str = Field(default="clear and supportive", min_length=2, max_length=120)
    audience: str = Field(default="members and guardians", min_length=2, max_length=180)
    include_guardian_context: bool = True


class CommunicationDraftRead(BaseModel):
    subject: str
    body: str
    model_name: str
    review_required: bool = True
    rationale: str


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
