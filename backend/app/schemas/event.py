from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    AttendanceStatus,
    CommunicationChannel,
    EventType,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
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
