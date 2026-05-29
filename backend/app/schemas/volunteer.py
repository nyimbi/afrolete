from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VolunteerProfileCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, min_length=2, max_length=240)
    volunteer_type: str = Field(default="event_staff", min_length=2, max_length=80)
    certification_level: str | None = Field(default=None, max_length=120)
    availability: list[str] = Field(default_factory=list, max_length=30)
    skills: list[str] = Field(default_factory=list, max_length=40)
    background_check_status: str = Field(default="not_started", max_length=40)
    background_check_expires_on: date | None = None
    training_status: str = Field(default="not_started", max_length=40)
    onboarding_status: str = Field(default="invited", max_length=40)
    reliability_score: float = Field(default=0.8, ge=0, le=1)
    emergency_contact: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class VolunteerProfileRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    person_name: str
    person_email: str | None
    volunteer_type: str
    certification_level: str | None
    availability: list[str]
    skills: list[str]
    background_check_status: str
    background_check_expires_on: date | None
    training_status: str
    onboarding_status: str
    reliability_score: float
    emergency_contact: str | None
    notes: str | None
    status: str


class VolunteerOpportunityCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    event_id: UUID | None = None
    title: str = Field(min_length=2, max_length=240)
    role_type: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=4000)
    required_skills: list[str] = Field(default_factory=list, max_length=40)
    starts_at: datetime
    ends_at: datetime | None = None
    location: str | None = Field(default=None, max_length=240)
    slots_required: int = Field(default=1, ge=1, le=500)
    min_age: int | None = Field(default=None, ge=12, le=100)
    background_check_required: bool = False
    training_required: bool = False
    public_signup: bool = True
    priority: str = Field(default="normal", max_length=40)


class VolunteerOpportunityRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    event_id: UUID | None
    title: str
    role_type: str
    description: str | None
    required_skills: list[str]
    starts_at: datetime
    ends_at: datetime | None
    location: str | None
    slots_required: int
    assigned_count: int
    open_slots: int
    min_age: int | None
    background_check_required: bool
    training_required: bool
    public_signup: bool
    priority: str
    status: str


class VolunteerAssignmentCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    volunteer_profile_id: UUID
    status: str = Field(default="assigned", max_length=40)
    notes: str | None = Field(default=None, max_length=4000)


class VolunteerAssignmentUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    hours_logged: float | None = Field(default=None, ge=0, le=1000)
    notes: str | None = Field(default=None, max_length=4000)


class VolunteerAssignmentRead(BaseModel):
    id: UUID
    organization_id: UUID
    opportunity_id: UUID
    volunteer_profile_id: UUID
    person_id: UUID
    person_name: str
    opportunity_title: str
    role_type: str
    status: str
    match_score: float
    confirmed_at: datetime | None
    checked_in_at: datetime | None
    checked_out_at: datetime | None
    hours_logged: float
    notes: str | None


class VolunteerTrainingRecordCreate(BaseModel):
    organization_id: UUID
    volunteer_profile_id: UUID
    module_name: str = Field(min_length=2, max_length=200)
    role_type: str | None = Field(default=None, max_length=80)
    required: bool = True
    status: str = Field(default="assigned", max_length=40)
    completed_at: datetime | None = None
    expires_on: date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    certificate_url: str | None = Field(default=None, max_length=500)


class VolunteerTrainingRecordRead(BaseModel):
    id: UUID
    organization_id: UUID
    volunteer_profile_id: UUID
    module_name: str
    role_type: str | None
    required: bool
    status: str
    assigned_at: datetime
    completed_at: datetime | None
    expires_on: date | None
    score: float | None
    certificate_url: str | None


class VolunteerRecognitionCreate(BaseModel):
    organization_id: UUID
    volunteer_profile_id: UUID
    recognition_type: str = Field(default="badge", max_length=80)
    badge_code: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=240)
    points: int = Field(default=0, ge=0, le=1_000_000)
    awarded_on: date | None = None
    source_summary: str | None = Field(default=None, max_length=4000)


class VolunteerRecognitionRead(BaseModel):
    id: UUID
    organization_id: UUID
    volunteer_profile_id: UUID
    recognition_type: str
    badge_code: str
    title: str
    points: int
    awarded_on: date
    source_summary: str | None


class VolunteerSummaryRead(BaseModel):
    organization_id: UUID
    active_volunteers: int
    open_opportunities: int
    open_slots: int
    assigned_shifts: int
    confirmed_shifts: int
    completed_hours: float
    training_compliance_percent: float
    coverage_percent: float
    top_skills: list[str]
    shortage_roles: list[str]
