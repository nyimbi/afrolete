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
    certification_expires_on: date | None
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
    completed_at: datetime
    enrollment: CoachEducationEnrollmentRead


class CoachEducationDashboardRead(BaseModel):
    organization_id: UUID
    active_enrollment_count: int
    certified_count: int
    average_xp: int
    total_xp: int
    leaderboard: list[dict[str, Any]]
    daily_challenges: list[CoachEducationChallengeRead]
    recommended_next_actions: list[str]
    enrollments: list[CoachEducationEnrollmentRead]
