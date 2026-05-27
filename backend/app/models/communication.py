from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import (
    ChannelPreference,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    MessageDeliveryStatus,
    NotificationFrequency,
)


class CommunicationTemplate(IdMixin, TimestampMixin, Base):
    __tablename__ = "communication_templates"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            "channel",
            name="uq_communication_templates_org_name_channel",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    message_type: Mapped[CommunicationMessageType] = mapped_column(
        enum_type(CommunicationMessageType),
        nullable=False,
        index=True,
    )
    channel: Mapped[CommunicationChannel] = mapped_column(
        enum_type(CommunicationChannel),
        nullable=False,
        index=True,
    )
    subject_template: Mapped[str] = mapped_column(String(240), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class CommunicationMessage(IdMixin, TimestampMixin, Base):
    __tablename__ = "communication_messages"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id"),
        index=True,
    )
    template_id: Mapped[UUID | None] = mapped_column(
        GUID(),
        ForeignKey("communication_templates.id"),
        index=True,
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    message_type: Mapped[CommunicationMessageType] = mapped_column(
        enum_type(CommunicationMessageType),
        nullable=False,
        index=True,
    )
    channel: Mapped[CommunicationChannel] = mapped_column(
        enum_type(CommunicationChannel),
        nullable=False,
        index=True,
    )
    scope_type: Mapped[CommunicationScopeType] = mapped_column(
        enum_type(CommunicationScopeType),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[UUID] = mapped_column(GUID(), index=True)
    subject: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    urgent: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    quiet_hours_override: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)


class MessageRecipient(IdMixin, TimestampMixin, Base):
    __tablename__ = "message_recipients"
    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "person_id",
            name="uq_message_recipients_message_person",
        ),
    )

    message_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("communication_messages.id"),
        index=True,
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    destination: Mapped[str | None] = mapped_column(String(320), index=True)
    delivery_status: Mapped[MessageDeliveryStatus] = mapped_column(
        enum_type(MessageDeliveryStatus),
        default=MessageDeliveryStatus.QUEUED,
        nullable=False,
        index=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text)


class NotificationPreference(IdMixin, TimestampMixin, Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "person_id",
            name="uq_notification_preferences_org_person",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id"),
        index=True,
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    frequency: Mapped[NotificationFrequency] = mapped_column(
        enum_type(NotificationFrequency),
        default=NotificationFrequency.IMMEDIATE,
        nullable=False,
        index=True,
    )
    channel_preference: Mapped[ChannelPreference] = mapped_column(
        enum_type(ChannelPreference),
        default=ChannelPreference.ALL,
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(16), default="en")
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5))
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5))
    emergency_override: Mapped[bool] = mapped_column(Boolean, default=True)
