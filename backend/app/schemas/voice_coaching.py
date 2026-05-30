from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VoiceCoachProfileCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    sport: str = Field(default="football", min_length=2, max_length=80)
    voice_style: str = Field(default="professional_coach", min_length=2, max_length=80)
    feedback_frequency: str = Field(default="moderate", pattern="^(minimal|moderate|detailed)$")
    language: str = Field(default="en", min_length=2, max_length=16)
    terminology_level: str = Field(default="intermediate", min_length=2, max_length=40)
    preferred_device: str | None = Field(default="bone_conduction_headphones", max_length=120)
    safety_alerts_enabled: bool = True


class VoiceCoachProfileRead(VoiceCoachProfileCreate):
    id: UUID
    person_name: str | None
    status: str
    created_at: datetime


class VoiceCoachingSessionCreate(BaseModel):
    organization_id: UUID
    profile_id: UUID | None = None
    team_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    activity_type: str = Field(default="football_sprint_training", min_length=2, max_length=120)
    stage: str = Field(default="main", pattern="^(warmup|main|cool_down|match|recovery)$")
    intensity: int = Field(default=76, ge=0, le=100)
    elapsed_seconds: int | None = Field(default=240, ge=0)
    distance_m: float | None = Field(default=820.0, ge=0)
    heart_rate_bpm: int | None = Field(default=168, ge=30, le=240)
    speed_mps: float | None = Field(default=7.1, ge=0)
    context_note: str | None = Field(default=None, max_length=2000)


class VoiceCoachingCueRead(BaseModel):
    id: UUID
    category: str
    priority: str
    audio_layer: str
    trigger: str
    message: str
    delivery_mode: str
    suppressed_reason: str | None


class VoiceCoachingSessionRead(BaseModel):
    id: UUID
    organization_id: UUID
    profile_id: UUID
    team_id: UUID | None
    athlete_profile_id: UUID | None
    activity_type: str
    stage: str
    intensity: int
    elapsed_seconds: int | None
    distance_m: float | None
    heart_rate_bpm: int | None
    speed_mps: float | None
    context_note: str | None
    summary: str
    debrief: str
    next_actions: list[str]
    safety_flags: list[str]
    delivered_count: int
    suppressed_count: int
    model_policy: str
    started_at: datetime
    cues: list[VoiceCoachingCueRead]


class VoiceMetricQueryCreate(BaseModel):
    organization_id: UUID
    profile_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    query: str = Field(min_length=2, max_length=240)


class VoiceMetricQueryRead(BaseModel):
    organization_id: UUID
    query: str
    query_type: str
    answer: str
    evidence: list[str]
    recommended_actions: list[str]
    model_policy: str = "afrolete-hands-free-metric-query-v1"
