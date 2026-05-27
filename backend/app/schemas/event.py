from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    AttendanceStatus,
    ConsentCaptureChannel,
    CommunicationChannel,
    EventType,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
    TravelPlanStatus,
    TravelRiskLevel,
    WeatherAlertLevel,
    WeatherDecision,
)


class EventCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    event_type: EventType
    title: str = Field(min_length=2, max_length=240)
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str = Field(default="UTC", max_length=80)
    venue_name: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def ends_after_start(self) -> "EventCreate":
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class EventRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    event_type: EventType
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    venue_name: str | None
    notes: str | None


class EventWeatherAssessmentCreate(BaseModel):
    source: str = Field(default="manual", min_length=2, max_length=80)
    observed_at: datetime
    temperature_c: float | None = Field(default=None, ge=-80, le=80)
    heat_index_c: float | None = Field(default=None, ge=-80, le=90)
    wbgt_c: float | None = Field(default=None, ge=-50, le=60)
    humidity_percent: float | None = Field(default=None, ge=0, le=100)
    aqi: int | None = Field(default=None, ge=0, le=500)
    lightning_distance_km: float | None = Field(default=None, ge=0, le=500)
    wind_speed_kph: float | None = Field(default=None, ge=0, le=400)
    wind_gust_kph: float | None = Field(default=None, ge=0, le=500)
    precipitation_mm_per_hr: float | None = Field(default=None, ge=0, le=500)
    notes: str | None = Field(default=None, max_length=4000)


class EventWeatherAssessmentRead(EventWeatherAssessmentCreate):
    id: UUID
    organization_id: UUID
    event_id: UUID
    alert_level: WeatherAlertLevel
    decision: WeatherDecision
    recommended_actions: str


class EventWeatherAlertCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.PUSH
    subject: str | None = Field(default=None, min_length=2, max_length=240)
    body: str | None = Field(default=None, min_length=2, max_length=8000)
    copy_guardians_for_minors: bool = True


class EventWeatherAlertRead(BaseModel):
    event_id: UUID
    assessment_id: UUID
    message_id: UUID
    recipient_count: int
    channel: CommunicationChannel
    subject: str
    urgent: bool


class EventTravelPlanCreate(BaseModel):
    destination: str = Field(min_length=2, max_length=240)
    travel_mode: str = Field(min_length=2, max_length=80)
    departure_at: datetime | None = None
    return_at: datetime | None = None
    route_summary: str | None = Field(default=None, max_length=8000)
    vehicle_details: str | None = Field(default=None, max_length=8000)
    driver_details: str | None = Field(default=None, max_length=8000)
    staff_manifest: str | None = Field(default=None, max_length=8000)
    passenger_manifest: str | None = Field(default=None, max_length=12000)
    lodging_details: str | None = Field(default=None, max_length=8000)
    meal_plan: str | None = Field(default=None, max_length=8000)
    equipment_manifest: str | None = Field(default=None, max_length=8000)
    emergency_contacts: str | None = Field(default=None, max_length=8000)
    medical_access_plan: str | None = Field(default=None, max_length=8000)
    route_weather_risk: str | None = Field(default=None, max_length=80)
    driver_certification_status: str | None = Field(default=None, max_length=80)
    vehicle_inspection_status: str | None = Field(default=None, max_length=80)
    consent_required: bool = True
    consent_due_at: datetime | None = None
    estimated_cost: float | None = Field(default=None, ge=0)
    cost_per_participant: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def return_after_departure(self) -> "EventTravelPlanCreate":
        if self.departure_at is not None and self.return_at is not None and self.return_at <= self.departure_at:
            raise ValueError("return_at must be after departure_at")
        return self


class EventTravelPlanUpdate(BaseModel):
    status: TravelPlanStatus | None = None
    route_summary: str | None = Field(default=None, max_length=8000)
    vehicle_details: str | None = Field(default=None, max_length=8000)
    driver_details: str | None = Field(default=None, max_length=8000)
    staff_manifest: str | None = Field(default=None, max_length=8000)
    passenger_manifest: str | None = Field(default=None, max_length=12000)
    lodging_details: str | None = Field(default=None, max_length=8000)
    meal_plan: str | None = Field(default=None, max_length=8000)
    equipment_manifest: str | None = Field(default=None, max_length=8000)
    emergency_contacts: str | None = Field(default=None, max_length=8000)
    medical_access_plan: str | None = Field(default=None, max_length=8000)
    route_weather_risk: str | None = Field(default=None, max_length=80)
    driver_certification_status: str | None = Field(default=None, max_length=80)
    vehicle_inspection_status: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=4000)


class EventTravelPlanRead(EventTravelPlanCreate):
    id: UUID
    organization_id: UUID
    event_id: UUID
    status: TravelPlanStatus
    risk_level: TravelRiskLevel
    risk_assessment: str


class EventTravelConsentRequestCreate(BaseModel):
    channel: ConsentCaptureChannel = ConsentCaptureChannel.EMAIL
    expires_at: datetime | None = None
    include_unknown_age: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelConsentRequestItemRead(BaseModel):
    request_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    destination: str
    one_time_token: str


class EventTravelConsentBatchRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    created: int
    existing: int
    skipped_no_guardian: int
    skipped_not_minor: int
    requests: list[EventTravelConsentRequestItemRead]


class EventTravelConsentReminderCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    subject: str | None = Field(default=None, max_length=240)
    body: str | None = Field(default=None, max_length=4000)


class EventTravelConsentReminderRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    message_id: UUID
    pending_request_count: int
    recipient_count: int


class EventTravelManifestParticipantRead(BaseModel):
    person_id: UUID
    display_name: str
    guardian_names: list[str]
    guardian_contacts: list[str]
    medical_clearance_status: MedicalClearanceStatus | None
    medical_clearance_reason: str


class EventTravelManifestRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    destination: str
    participant_count: int
    emergency_contacts: str | None
    medical_access_plan: str | None
    participants: list[EventTravelManifestParticipantRead]


class EventTravelFeeInvoiceCreate(BaseModel):
    amount_per_participant: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    due_on: date | None = None
    bill_guardians_for_minors: bool = True
    memo: str | None = Field(default=None, max_length=4000)


class EventTravelFeeInvoiceItemRead(BaseModel):
    invoice_id: UUID
    invoice_number: str
    billed_person_id: UUID
    athlete_person_id: UUID
    amount_due: Decimal
    status: str


class EventTravelFeeInvoiceBatchRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    created: int
    existing: int
    skipped_no_payer: int
    total_amount_due: Decimal
    invoices: list[EventTravelFeeInvoiceItemRead]


class EventTravelApprovalCreate(BaseModel):
    approval_level: str = Field(default="school", min_length=2, max_length=80)
    approver_person_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelApprovalUpdate(BaseModel):
    status: str = Field(pattern="^(pending|approved|rejected|cancelled)$")
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelApprovalRead(BaseModel):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    approval_level: str
    status: str
    approver_person_id: UUID | None
    decided_by_person_id: UUID | None
    decided_at: datetime | None
    notes: str | None


class AttendanceRecordUpsert(BaseModel):
    person_id: UUID
    status: AttendanceStatus
    note: str | None = Field(default=None, max_length=2000)


class AttendanceRecordRead(BaseModel):
    id: UUID
    event_id: UUID
    person_id: UUID
    status: AttendanceStatus
    recorded_by_person_id: UUID | None
    guardian_consent_id: UUID | None
    note: str | None
    clearance_status: ParticipationClearanceStatus | None = None
    medical_clearance_status: MedicalClearanceStatus | None = None
    medical_clearance_id: UUID | None = None
    medical_clearance_reason: str | None = None


class AttendanceSeedRead(BaseModel):
    event_id: UUID
    created: int
    existing: int
