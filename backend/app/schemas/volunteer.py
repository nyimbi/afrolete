from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CommunicationChannel
from app.schemas.safeguarding import BackgroundCheckProviderSubmissionRead


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


class VolunteerBackgroundCheckSubmitCreate(BaseModel):
    provider: str = Field(default="youth_sport_staff", min_length=2, max_length=120)
    check_type: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class VolunteerBackgroundCheckSubmissionRead(BaseModel):
    volunteer_profile: VolunteerProfileRead
    background_check_id: UUID
    created_background_check: bool
    submission: BackgroundCheckProviderSubmissionRead


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


class VolunteerNeedRequestCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    event_id: UUID | None = None
    title: str = Field(min_length=2, max_length=240)
    role_type: str = Field(min_length=2, max_length=80)
    needed_count: int = Field(default=1, ge=1, le=500)
    required_skills: list[str] = Field(default_factory=list, max_length=40)
    needed_by: datetime | None = None
    priority: str = Field(default="normal", max_length=40)
    notes: str | None = Field(default=None, max_length=4000)
    create_opportunity: bool = False


class VolunteerNeedRequestUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    opportunity_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)


class VolunteerNeedRequestRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    event_id: UUID | None
    requested_by_person_id: UUID | None
    title: str
    role_type: str
    needed_count: int
    required_skills: list[str]
    needed_by: datetime | None
    priority: str
    status: str
    notes: str | None
    opportunity_id: UUID | None


class PublicVolunteerSignupCreate(BaseModel):
    opportunity_id: UUID
    display_name: str = Field(min_length=2, max_length=240)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    availability: list[str] = Field(default_factory=list, max_length=30)
    skills: list[str] = Field(default_factory=list, max_length=40)
    emergency_contact: str | None = Field(default=None, max_length=240)
    message: str | None = Field(default=None, max_length=2000)
    source_url: str | None = Field(default=None, max_length=500)


class PublicVolunteerSignupRead(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    opportunity_title: str
    volunteer_profile_id: UUID
    assignment_id: UUID
    person_id: UUID
    person_name: str
    person_email: str | None
    status: str
    match_score: float
    onboarding_status: str
    message: str | None


class PublicVolunteerGroupSignupCreate(BaseModel):
    opportunity_id: UUID
    company_name: str = Field(min_length=2, max_length=240)
    coordinator_name: str = Field(min_length=2, max_length=240)
    coordinator_email: str = Field(min_length=3, max_length=320)
    coordinator_phone: str | None = Field(default=None, max_length=64)
    group_size: int = Field(ge=2, le=500)
    requested_slots: int = Field(ge=1, le=500)
    skills: list[str] = Field(default_factory=list, max_length=40)
    availability: list[str] = Field(default_factory=list, max_length=30)
    message: str | None = Field(default=None, max_length=4000)
    source_url: str | None = Field(default=None, max_length=500)


class VolunteerGroupApplicationUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    approved_slots: int | None = Field(default=None, ge=0, le=500)
    review_notes: str | None = Field(default=None, max_length=4000)


class VolunteerGroupApplicationRead(BaseModel):
    id: UUID
    organization_id: UUID
    opportunity_id: UUID
    opportunity_title: str
    company_name: str
    coordinator_name: str
    coordinator_email: str
    coordinator_phone: str | None
    group_size: int
    requested_slots: int
    approved_slots: int
    skills: list[str]
    availability: list[str]
    message: str | None
    source_url: str | None
    status: str
    reviewed_by_person_id: UUID | None
    reviewed_at: datetime | None
    review_notes: str | None


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


class VolunteerObligationCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, min_length=2, max_length=240)
    team_id: UUID | None = None
    season_label: str = Field(min_length=2, max_length=80)
    category: str = Field(default="family_service", max_length=80)
    required_hours: float = Field(ge=0, le=10_000)
    completed_hours: float = Field(default=0, ge=0, le=10_000)
    waived_hours: float = Field(default=0, ge=0, le=10_000)
    due_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class VolunteerObligationUpdate(BaseModel):
    completed_hours: float | None = Field(default=None, ge=0, le=10_000)
    waived_hours: float | None = Field(default=None, ge=0, le=10_000)
    status: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=4000)


class VolunteerObligationRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    person_name: str
    person_email: str | None
    team_id: UUID | None
    season_label: str
    category: str
    required_hours: float
    completed_hours: float
    waived_hours: float
    remaining_hours: float
    due_on: date | None
    status: str
    notes: str | None


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
    pending_group_applications: int
    approved_group_slots: int
    open_need_requests: int
    obligation_deficit_hours: float
    completed_hours: float
    training_compliance_percent: float
    coverage_percent: float
    top_skills: list[str]
    shortage_roles: list[str]


class VolunteerReminderRunCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    due_within_days: int = Field(default=7, ge=0, le=365)
    repeat_after_hours: int = Field(default=24, ge=0, le=8760)
    limit: int = Field(default=50, ge=1, le=500)
    dry_run: bool = False


class VolunteerReminderRunRead(BaseModel):
    organization_id: UUID
    eligible_count: int
    reminded_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool
    coverage_gap_count: int
    obligation_count: int
    training_count: int
    recipient_count: int
    message_ids: list[UUID]


class VolunteerCoordinationMessageCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    channel: CommunicationChannel = CommunicationChannel.IN_APP
    subject: str | None = Field(default=None, min_length=2, max_length=240)
    body: str = Field(min_length=2, max_length=8000)
    urgent: bool = False
    include_statuses: list[str] = Field(
        default_factory=lambda: ["assigned", "confirmed", "checked_in", "invited"],
        max_length=12,
    )


class VolunteerCoordinationMessageRead(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    opportunity_title: str
    channel: CommunicationChannel
    subject: str
    body: str
    urgent: bool
    eligible_assignment_count: int
    recipient_count: int
    assignment_ids: list[UUID]
    recipient_person_ids: list[UUID]
    message_id: UUID | None
    skipped_reasons: list[str]


class VolunteerSubstitutePoolMemberCreate(BaseModel):
    organization_id: UUID
    volunteer_profile_id: UUID
    team_id: UUID | None = None
    role_type: str = Field(min_length=2, max_length=80)
    availability: list[str] = Field(default_factory=list, max_length=30)
    priority: int = Field(default=50, ge=0, le=100)
    max_dispatches_per_month: int = Field(default=4, ge=1, le=100)
    status: str = Field(default="available", max_length=40)
    notes: str | None = Field(default=None, max_length=4000)


class VolunteerSubstitutePoolMemberRead(BaseModel):
    id: UUID
    organization_id: UUID
    volunteer_profile_id: UUID
    person_id: UUID
    person_name: str
    person_email: str | None
    team_id: UUID | None
    role_type: str
    availability: list[str]
    priority: int
    max_dispatches_per_month: int
    status: str
    last_contacted_at: datetime | None
    notes: str | None


class VolunteerSubstituteDispatchCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    limit: int = Field(default=3, ge=1, le=50)
    channel: CommunicationChannel = CommunicationChannel.IN_APP
    message: str | None = Field(default=None, max_length=2000)


class VolunteerSubstituteDispatchRead(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    opportunity_title: str
    open_slots_before: int
    candidate_count: int
    dispatched_count: int
    assignment_ids: list[UUID]
    message_id: UUID | None
    recipient_count: int
    skipped_reasons: list[str]
