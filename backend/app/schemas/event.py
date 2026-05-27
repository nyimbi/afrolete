from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import AttendanceStatus, EventType, ParticipationClearanceStatus


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


class AttendanceSeedRead(BaseModel):
    event_id: UUID
    created: int
    existing: int
