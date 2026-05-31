from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CoachEducationModuleRead(BaseModel):
    key: str
    title: str
    duration_minutes: int
    format: str
    objective: str
    practice_task: str
    xp: int


class CoachEducationProgramRead(BaseModel):
    key: str
    title: str
    level: int
    certification_badge: str
    accreditation_provider: str
    cpd_hours_required: float
    specialization: str | None = None
    modules: list[CoachEducationModuleRead]


class CoachEducationChallengeRead(BaseModel):
    key: str
    title: str
    xp: int
    cadence: str
    action: str


class CoachEducationCatalogRead(BaseModel):
    programs: list[CoachEducationProgramRead]
    daily_challenges: list[CoachEducationChallengeRead]


class CoachEducationEnrollmentCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    program_key: str = Field(default="foundation_coach", min_length=2, max_length=120)
    role: str = Field(default="coach", min_length=2, max_length=120)
    skill_level: str = Field(default="intermediate", min_length=2, max_length=80)
    learning_style: str = Field(default="hands_on", min_length=2, max_length=80)
    accreditation_provider: str | None = Field(default=None, max_length=180)
    cpd_hours_required: float = Field(default=20.0, ge=0, le=500)
    mentor_person_id: UUID | None = None


class CoachEducationEnrollmentRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    person_name: str
    program_key: str
    program_title: str
    level: int
    role: str
    skill_level: str
    learning_style: str
    xp_points: int
    current_module_key: str | None
    completed_modules: list[str]
    badges: list[str]
    status: str
    accreditation_provider: str | None
    certificate_number: str | None
    certification_issued_on: date | None
    certification_expires_on: date | None
    renewal_due_on: date | None
    certification_state: str
    days_until_expiry: int | None
    cpd_hours_required: float
    cpd_hours_completed: float
    cpd_gap_hours: float
    portfolio_evidence_ref: str | None
    mentor_person_id: UUID | None
    mentor_name: str | None
    last_reviewed_by_person_id: UUID | None
    last_reviewed_at: datetime | None
    review_notes: str | None
    renewal_last_reminded_at: datetime | None
    renewal_reminder_message_id: UUID | None
    renewal_reminder_count: int
    progress_percent: int
    next_module: CoachEducationModuleRead | None
    last_activity_at: datetime | None
    created_at: datetime


class CoachEducationActivityCreate(BaseModel):
    activity_type: str = Field(default="module_completion", min_length=2, max_length=80)
    module_key: str = Field(min_length=2, max_length=120)
    title: str | None = Field(default=None, max_length=220)
    xp_awarded: int | None = Field(default=None, ge=0, le=1000)
    evidence_ref: str | None = Field(default=None, max_length=500)
    score_percent: float | None = Field(default=None, ge=0, le=100)
    cpd_hours: float = Field(default=0.0, ge=0, le=200)
    review_status: str = Field(default="accepted", min_length=2, max_length=40)
    feedback: str | None = Field(default=None, max_length=2000)


class CoachEducationActivityRead(BaseModel):
    id: UUID
    organization_id: UUID
    enrollment_id: UUID
    person_id: UUID
    activity_type: str
    module_key: str
    title: str
    xp_awarded: int
    evidence_ref: str | None
    score_percent: float | None
    cpd_hours: float
    reviewer_person_id: UUID | None
    review_status: str
    feedback: str | None
    completed_at: datetime
    enrollment: CoachEducationEnrollmentRead


class CoachEducationCertificationReviewCreate(BaseModel):
    action: str = Field(default="record_cpd", pattern="^(record_cpd|renew|suspend|revoke)$")
    cpd_hours_completed: float | None = Field(default=None, ge=0, le=500)
    portfolio_evidence_ref: str | None = Field(default=None, max_length=500)
    mentor_person_id: UUID | None = None
    certification_expires_on: date | None = None
    review_notes: str | None = Field(default=None, max_length=2000)


class CoachEducationCertificationReviewRead(BaseModel):
    enrollment: CoachEducationEnrollmentRead
    action: str
    certification_state: str
    cpd_gap_hours: float
    renewed: bool
    message: str


class CoachEducationRenewalReminderRunCreate(BaseModel):
    organization_id: UUID
    channel: str = Field(default="email", pattern="^(email|sms|whatsapp|telegram|push|in_app)$")
    as_of: date | None = None
    horizon_days: int = Field(default=45, ge=0, le=730)
    repeat_after_days: int = Field(default=14, ge=0, le=365)
    limit: int = Field(default=100, ge=1, le=500)
    dry_run: bool = False


class CoachEducationRenewalReminderItemRead(BaseModel):
    enrollment_id: UUID
    person_id: UUID
    person_name: str
    program_key: str
    program_title: str
    certification_state: str
    renewal_due_on: date | None
    certification_expires_on: date | None
    days_until_expiry: int | None
    cpd_gap_hours: float
    recipient_count: int
    action: str
    reason: str
    message_id: UUID | None = None


class CoachEducationRenewalReminderRunRead(BaseModel):
    organization_id: UUID | None
    channel: str
    as_of: date
    horizon_days: int
    repeat_after_days: int
    eligible_count: int
    executed_count: int
    reminded_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool
    enrollment_ids: list[UUID]
    message_ids: list[UUID]
    items: list[CoachEducationRenewalReminderItemRead]


class CoachEducationDashboardRead(BaseModel):
    organization_id: UUID
    active_enrollment_count: int
    certified_count: int
    renewal_due_count: int
    expired_count: int
    cpd_gap_count: int
    average_xp: int
    total_xp: int
    leaderboard: list[dict[str, Any]]
    daily_challenges: list[CoachEducationChallengeRead]
    recommended_next_actions: list[str]
    enrollments: list[CoachEducationEnrollmentRead]
