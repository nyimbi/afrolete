from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    AttendanceStatus,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    ConsentStatus,
    EventType,
    GuardianRelationshipKind,
    ParticipationClearanceStatus,
)


class GuardianRelationshipCreate(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID | None = None
    guardian_email: str | None = Field(default=None, max_length=320)
    guardian_phone: str | None = Field(default=None, max_length=64)
    guardian_display_name: str | None = Field(default=None, min_length=2, max_length=240)
    relationship_kind: GuardianRelationshipKind = GuardianRelationshipKind.PARENT
    relationship: str | None = Field(default=None, max_length=80)
    can_sign_consent: bool = True
    can_view_medical: bool = False
    emergency_contact: bool = True
    can_pick_up: bool = False
    is_primary: bool = False
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def guardian_reference_required(self) -> "GuardianRelationshipCreate":
        if (
            self.guardian_person_id is None
            and self.guardian_email is None
            and self.guardian_phone is None
        ):
            raise ValueError("guardian_person_id, guardian_email, or guardian_phone is required")
        return self


class GuardianRelationshipRead(BaseModel):
    id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    relationship_kind: GuardianRelationshipKind
    relationship: str
    can_sign_consent: bool
    can_view_medical: bool
    emergency_contact: bool
    can_pick_up: bool
    is_primary: bool
    notes: str | None


class FamilyAthleteSummaryRead(BaseModel):
    athlete_person_id: UUID
    athlete_name: str
    relationship: str
    relationship_kind: GuardianRelationshipKind
    can_sign_consent: bool
    can_view_medical: bool
    emergency_contact: bool
    pending_consent_requests: int
    latest_consent_status: ConsentStatus | None
    latest_consent_scope_type: ConsentScopeType | None
    latest_consent_signed_at: datetime | None


class FamilyEventSummaryRead(BaseModel):
    athlete_person_id: UUID
    athlete_name: str
    event_id: UUID
    team_id: UUID | None
    event_type: EventType
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    venue_name: str | None
    attendance_status: AttendanceStatus | None
    clearance_status: ParticipationClearanceStatus
    guardian_required: bool
    consent_id: UUID | None
    reason: str


class ActivityConsentCreate(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None = None
    status: ConsentStatus = ConsentStatus.GRANTED
    valid_from: date | None = None
    valid_until: date | None = None
    signed_at: datetime | None = None
    consent_text: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def scoped_consent_reference_required(self) -> "ActivityConsentCreate":
        if self.scope_type != ConsentScopeType.ORGANIZATION and self.scope_id is None:
            raise ValueError("team and event consents require scope_id")
        return self


class ConsentRequestCreate(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None = None
    channel: ConsentCaptureChannel
    destination: str | None = Field(default=None, max_length=320)
    expires_at: datetime | None = None
    external_message_id: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def scoped_request_reference_required(self) -> "ConsentRequestCreate":
        if self.scope_type != ConsentScopeType.ORGANIZATION and self.scope_id is None:
            raise ValueError("team and event consent requests require scope_id")
        return self


class ConsentRequestRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None
    channel: ConsentCaptureChannel
    destination: str
    status: ConsentRequestStatus
    expires_at: datetime | None
    sent_at: datetime | None
    fulfilled_at: datetime | None
    external_message_id: str | None
    one_time_token: str | None = None


class TokenConsentCapture(BaseModel):
    token: str = Field(min_length=16, max_length=200)
    status: ConsentStatus = ConsentStatus.GRANTED
    consent_text: str | None = Field(default=None, max_length=4000)
    response_payload: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)


class KnownChannelConsentCapture(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    channel: ConsentCaptureChannel
    source_address: str = Field(min_length=3, max_length=320)
    scope_type: ConsentScopeType
    scope_id: UUID | None = None
    status: ConsentStatus = ConsentStatus.GRANTED
    response_payload: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def scoped_response_reference_required(self) -> "KnownChannelConsentCapture":
        if self.scope_type != ConsentScopeType.ORGANIZATION and self.scope_id is None:
            raise ValueError("team and event consent responses require scope_id")
        return self


class ActivityConsentRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None
    status: ConsentStatus
    source_request_id: UUID | None
    capture_channel: ConsentCaptureChannel
    valid_from: date | None
    valid_until: date | None
    signed_at: datetime | None
    revoked_at: datetime | None
    recorded_by_person_id: UUID | None
    consent_text: str | None
    notes: str | None


class ParticipationClearanceRead(BaseModel):
    event_id: UUID
    athlete_person_id: UUID
    is_minor: bool
    guardian_required: bool
    status: ParticipationClearanceStatus
    consent_id: UUID | None = None
    reason: str
