from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AthleteWellnessCheckInCreate(BaseModel):
    organization_id: UUID
    check_in_at: datetime | None = None
    mood_score: int = Field(ge=1, le=10)
    stress_score: int = Field(ge=1, le=10)
    sleep_hours: float = Field(ge=0, le=24)
    energy_score: int = Field(ge=1, le=10)
    soreness_score: int = Field(ge=1, le=10)
    resilience_score: int | None = Field(default=None, ge=1, le=10)
    support_requested: bool = False
    notes: str | None = Field(default=None, max_length=4000)


class AthleteWellnessCheckInRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    submitted_by_person_id: UUID | None
    check_in_at: datetime
    mood_score: int
    stress_score: int
    sleep_hours: float
    energy_score: int
    soreness_score: int
    resilience_score: int | None
    support_requested: bool
    risk_band: str
    notes: str | None
    created_at: datetime


class AthleteAcademicRecordCreate(BaseModel):
    organization_id: UUID
    school_name: str | None = Field(default=None, max_length=180)
    term_label: str = Field(min_length=2, max_length=120)
    grade_level: str | None = Field(default=None, max_length=80)
    gpa: float | None = Field(default=None, ge=0, le=5)
    attendance_rate: float | None = Field(default=None, ge=0, le=100)
    study_hours_weekly: float | None = Field(default=None, ge=0, le=80)
    missing_assignment_count: int = Field(default=0, ge=0)
    next_review_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class AthleteAcademicRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    recorded_by_person_id: UUID | None
    school_name: str | None
    term_label: str
    grade_level: str | None
    gpa: float | None
    attendance_rate: float | None
    study_hours_weekly: float | None
    missing_assignment_count: int
    eligibility_status: str
    risk_level: str
    next_review_on: date | None
    notes: str | None
    created_at: datetime


class AthleteLifeSkillAssignmentCreate(BaseModel):
    organization_id: UUID
    module_code: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=220)
    category: str = Field(min_length=2, max_length=80)
    level: str = Field(default="foundation", min_length=2, max_length=40)
    due_on: date | None = None
    evidence_notes: str | None = Field(default=None, max_length=4000)


class AthleteLifeSkillProgressUpdate(BaseModel):
    status: str = Field(default="in_progress", min_length=2, max_length=40)
    progress_percent: int = Field(ge=0, le=100)
    evidence_notes: str | None = Field(default=None, max_length=4000)


class AthleteLifeSkillAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    assigned_by_person_id: UUID | None
    module_code: str
    title: str
    category: str
    level: str
    status: str
    progress_percent: int
    due_on: date | None
    completed_at: datetime | None
    evidence_notes: str | None
    created_at: datetime


class AthleteScholarshipApplicationCreate(BaseModel):
    organization_id: UUID
    program_name: str = Field(min_length=2, max_length=220)
    scholarship_type: str = Field(default="athletic", min_length=2, max_length=80)
    donor_or_fund: str | None = Field(default=None, max_length=220)
    amount_requested: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    deadline_on: date | None = None
    submitted_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class AthleteScholarshipApplicationReview(BaseModel):
    status: str = Field(min_length=2, max_length=40)
    amount_awarded: float | None = Field(default=None, ge=0)
    decided_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class AthleteScholarshipApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    created_by_person_id: UUID | None
    program_name: str
    scholarship_type: str
    donor_or_fund: str | None
    amount_requested: float
    amount_awarded: float | None
    currency: str
    status: str
    eligibility_score: int
    committee_recommendation: str
    deadline_on: date | None
    submitted_on: date | None
    decided_on: date | None
    notes: str | None
    created_at: datetime


class AthleteDevelopmentActionRead(BaseModel):
    key: str
    priority: str
    title: str
    detail: str
    owner: str


class AthleteDevelopmentDashboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    athlete_profile_id: UUID
    athlete_name: str
    generated_at: datetime
    development_score: int
    wellness_risk_band: str
    academic_eligibility_status: str
    scholarship_readiness_score: int
    life_skill_progress_percent: int
    latest_wellness: AthleteWellnessCheckInRead | None
    latest_academic: AthleteAcademicRecordRead | None
    scholarship_applications: list[AthleteScholarshipApplicationRead]
    life_skill_assignments: list[AthleteLifeSkillAssignmentRead]
    actions: list[AthleteDevelopmentActionRead]
