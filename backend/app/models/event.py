from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import (
    AttendanceStatus,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    ConsentStatus,
    EventType,
)


class Event(IdMixin, TimestampMixin, Base):
    __tablename__ = "events"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_type: Mapped[EventType] = mapped_column(enum_type(EventType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    venue_name: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)


class AttendanceRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("event_id", "person_id"),)

    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[AttendanceStatus] = mapped_column(enum_type(AttendanceStatus), nullable=False)
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    guardian_consent_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("activity_consents.id"), index=True
    )
    note: Mapped[str | None] = mapped_column(Text)


class ConsentRequest(IdMixin, TimestampMixin, Base):
    __tablename__ = "consent_requests"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    guardian_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    scope_type: Mapped[ConsentScopeType] = mapped_column(
        enum_type(ConsentScopeType),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[UUID | None] = mapped_column(GUID(), index=True)
    channel: Mapped[ConsentCaptureChannel] = mapped_column(
        enum_type(ConsentCaptureChannel),
        nullable=False,
        index=True,
    )
    destination: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[ConsentRequestStatus] = mapped_column(
        enum_type(ConsentRequestStatus),
        default=ConsentRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_message_id: Mapped[str | None] = mapped_column(String(240), index=True)
    response_payload: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class ActivityConsent(IdMixin, TimestampMixin, Base):
    __tablename__ = "activity_consents"
    __table_args__ = (
        UniqueConstraint(
            "athlete_person_id",
            "guardian_person_id",
            "scope_type",
            "scope_id",
            name="uq_activity_consents_guardian_scope",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    guardian_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    scope_type: Mapped[ConsentScopeType] = mapped_column(
        enum_type(ConsentScopeType),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[UUID | None] = mapped_column(GUID(), index=True)
    status: Mapped[ConsentStatus] = mapped_column(
        enum_type(ConsentStatus),
        default=ConsentStatus.PENDING,
        nullable=False,
        index=True,
    )
    source_request_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("consent_requests.id"), index=True
    )
    capture_channel: Mapped[ConsentCaptureChannel] = mapped_column(
        enum_type(ConsentCaptureChannel),
        default=ConsentCaptureChannel.MANUAL,
        nullable=False,
        index=True,
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    consent_text: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
