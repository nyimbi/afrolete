from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CoachVoiceCommandSessionCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    event_id: UUID | None = None
    session_label: str = Field(default="Match voice commands", min_length=2, max_length=180)
    context_type: str = Field(default="match", pattern="^(match|training|meeting|emergency|operations)$")
    input_device: str = Field(default="coach_headset", min_length=2, max_length=120)
    language: str = Field(default="en", min_length=2, max_length=16)
    listening_mode: str = Field(default="push_to_talk", pattern="^(push_to_talk|always_on|manual_transcript)$")
    consent_recorded: bool = True
    raw_audio_retention_policy: str = Field(
        default="delete_raw_audio_after_transcription",
        min_length=2,
        max_length=120,
    )


class CoachVoiceCommandCreate(BaseModel):
    transcript: str = Field(min_length=2, max_length=2000)
    source_device: str | None = Field(default=None, max_length=120)
    latency_ms: int | None = Field(default=None, ge=0, le=60000)
    context: dict[str, Any] = Field(default_factory=dict)


class CoachVoiceCommandReviewCreate(BaseModel):
    decision: str = Field(default="confirm", pattern="^(confirm|reject|hold)$")
    notes: str | None = Field(default=None, max_length=4000)
    apply_to_official_record: bool = True
    fixture_id: UUID | None = None
    team_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    event_type: str | None = Field(default=None, max_length=80)


class CoachVoiceCommandShortcutCreate(BaseModel):
    organization_id: UUID
    phrase: str = Field(min_length=2, max_length=240)
    intent: str = Field(default="custom_command", min_length=2, max_length=80)
    action_sequence: list[str] = Field(default_factory=list, max_length=20)
    parameters: dict[str, Any] = Field(default_factory=dict)
    notification_policy: str = Field(default="coach_confirmation", min_length=2, max_length=80)
    auto_log: bool = True
    trained_sample_count: int = Field(default=0, ge=0, le=100000)
    sensitivity: float = Field(default=0.72, ge=0, le=1)


class CoachVoiceCommandShortcutRead(BaseModel):
    id: UUID
    organization_id: UUID
    created_by_person_id: UUID | None
    phrase: str
    intent: str
    action_sequence: list[str]
    parameters: dict[str, Any]
    notification_policy: str
    auto_log: bool
    trained_sample_count: int
    sensitivity: float
    status: str
    created_at: datetime


class CoachVoiceCommandRead(BaseModel):
    id: UUID
    organization_id: UUID
    session_id: UUID
    issued_by_person_id: UUID | None
    reviewed_by_person_id: UUID | None
    transcript: str
    normalized_transcript: str
    intent: str
    confidence: float
    command_status: str
    response_text: str
    entities: dict[str, Any]
    action_result: dict[str, Any]
    safety_flags: list[str]
    review_result: dict[str, Any]
    permission_scope: str
    requires_confirmation: bool
    review_decision: str | None
    review_notes: str | None
    confirmed_at: datetime | None
    source_device: str | None
    latency_ms: int | None
    model_policy: str
    processed_at: datetime


class CoachVoiceCommandSessionRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID | None
    team_id: UUID | None
    event_id: UUID | None
    session_label: str
    context_type: str
    input_device: str
    language: str
    listening_mode: str
    consent_recorded: bool
    raw_audio_retention_policy: str
    command_count: int
    status: str
    model_policy: str
    started_at: datetime
    last_command_at: datetime | None
    commands: list[CoachVoiceCommandRead] = Field(default_factory=list)
