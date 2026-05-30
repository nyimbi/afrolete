from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    CommunicationChannel,
    CompetitionFormat,
    CompetitionStatus,
    CompetitionType,
    FixtureStatus,
    MatchEventType,
    OfficialAssignmentStatus,
    OfficialRole,
)


class CompetitionCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=240)
    sport: str = Field(min_length=2, max_length=80)
    competition_type: CompetitionType
    format: CompetitionFormat
    season_label: str | None = Field(default=None, max_length=80)
    starts_on: date | None = None
    ends_on: date | None = None
    points_for_win: int = Field(default=3, ge=0, le=10)
    points_for_draw: int = Field(default=1, ge=0, le=10)
    points_for_loss: int = Field(default=0, ge=0, le=10)
    tiebreakers: str | None = Field(default=None, max_length=2000)
    rules_summary: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_date_range(self) -> "CompetitionCreate":
        if self.starts_on is not None and self.ends_on is not None and self.ends_on < self.starts_on:
            raise ValueError("ends_on must be on or after starts_on")
        return self


class CompetitionRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    sport: str
    competition_type: CompetitionType
    format: CompetitionFormat
    season_label: str | None
    starts_on: date | None
    ends_on: date | None
    status: CompetitionStatus
    points_for_win: int
    points_for_draw: int
    points_for_loss: int
    tiebreakers: str | None
    rules_summary: str | None


class CompetitionParticipantCreate(BaseModel):
    team_id: UUID
    seed: int | None = Field(default=None, ge=1)
    group_label: str | None = Field(default=None, max_length=80)


class CompetitionParticipantRead(BaseModel):
    id: UUID
    competition_id: UUID
    team_id: UUID
    team_name: str
    seed: int | None
    group_label: str | None
    status: str


class AthleteTransferCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    from_team_id: UUID | None = None
    to_team_id: UUID
    transfer_type: str = Field(default="permanent", min_length=2, max_length=80)
    status: str = Field(default="requested", min_length=2, max_length=40)
    requested_on: date | None = None
    effective_on: date | None = None
    window_label: str | None = Field(default=None, max_length=120)
    previous_registration_ref: str | None = Field(default=None, max_length=180)
    clearance_reference: str | None = Field(default=None, max_length=180)
    reason: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)


class AthleteTransferRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    athlete_name: str
    from_team_id: UUID | None
    from_team_name: str | None
    to_team_id: UUID
    to_team_name: str
    transfer_type: str
    status: str
    requested_on: date
    effective_on: date | None
    window_label: str | None
    previous_registration_ref: str | None
    clearance_reference: str | None
    reviewed_by_person_id: UUID | None
    decided_at: datetime | None
    reason: str | None
    notes: str | None


class CompetitionEligibilityCheckCreate(BaseModel):
    athlete_profile_id: UUID
    team_id: UUID
    transfer_record_id: UUID | None = None
    min_age: int | None = Field(default=None, ge=3, le=100)
    max_age: int | None = Field(default=None, ge=3, le=100)
    require_active_roster: bool = True
    require_team_registration: bool = True
    require_transfer_clearance: bool = True
    require_medical_clearance: bool = True
    require_compliance_credential: bool = False
    max_players_per_team: int | None = Field(default=None, ge=1, le=200)
    academic_status: str | None = Field(default=None, max_length=80)
    citizenship_status: str | None = Field(default=None, max_length=80)
    disciplinary_status: str | None = Field(default=None, max_length=80)
    valid_until: date | None = None

    @model_validator(mode="after")
    def valid_age_range(self) -> "CompetitionEligibilityCheckCreate":
        if self.min_age is not None and self.max_age is not None and self.max_age < self.min_age:
            raise ValueError("max_age must be greater than or equal to min_age")
        return self


class CompetitionEligibilityCheckRead(BaseModel):
    key: str
    label: str
    status: str
    severity: str
    detail: str
    recommendation: str


class CompetitionEligibilityCertificateRead(BaseModel):
    id: UUID
    organization_id: UUID
    competition_id: UUID
    athlete_profile_id: UUID
    athlete_name: str
    team_id: UUID
    team_name: str
    transfer_record_id: UUID | None
    status: str
    certificate_number: str
    valid_from: date | None
    valid_until: date | None
    blocker_count: int
    warning_count: int
    eligibility_summary: str
    checks: list[CompetitionEligibilityCheckRead]


class CompetitionFixtureCreate(BaseModel):
    home_team_id: UUID
    away_team_id: UUID
    event_id: UUID | None = None
    round_label: str | None = Field(default=None, max_length=80)
    stage_label: str | None = Field(default=None, max_length=80)
    scheduled_at: datetime
    venue_name: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def teams_are_different(self) -> "CompetitionFixtureCreate":
        if self.home_team_id == self.away_team_id:
            raise ValueError("home_team_id and away_team_id must differ")
        return self


class CompetitionFixtureGenerateCreate(BaseModel):
    starts_at: datetime
    interval_days: int = Field(default=7, ge=1, le=30)
    match_spacing_minutes: int = Field(default=120, ge=30, le=720)
    venue_name: str | None = Field(default=None, max_length=200)
    stage_label: str = Field(default="Regular season", max_length=80)
    double_round_robin: bool = False


class CompetitionAdvanceCreate(BaseModel):
    source_stage_label: str = Field(default="League", max_length=80)
    source_round_label: str = Field(default="Round 1", max_length=80)
    next_stage_label: str = Field(default="Knockout", max_length=80)
    next_round_label: str = Field(default="Next round", max_length=80)
    scheduled_at: datetime
    match_spacing_minutes: int = Field(default=120, ge=30, le=720)
    venue_name: str | None = Field(default=None, max_length=200)


class CompetitionScheduleOptimizeCreate(BaseModel):
    starts_at: datetime
    match_spacing_minutes: int = Field(default=120, ge=30, le=720)
    team_rest_minutes: int = Field(default=240, ge=60, le=2880)
    venue_name: str | None = Field(default=None, max_length=200)
    preserve_final_results: bool = True


class CompetitionFixtureRead(BaseModel):
    id: UUID
    organization_id: UUID
    competition_id: UUID
    event_id: UUID | None
    home_team_id: UUID
    away_team_id: UUID
    home_team_name: str
    away_team_name: str
    round_label: str | None
    stage_label: str | None
    scheduled_at: datetime
    venue_name: str | None
    status: FixtureStatus
    home_score: int | None
    away_score: int | None
    result_confirmed_at: datetime | None
    notes: str | None


class CompetitionFixtureGenerationRead(BaseModel):
    competition_id: UUID
    created: int
    existing: int
    rounds: int
    fixtures: list[CompetitionFixtureRead]


class CompetitionAdvancementRead(BaseModel):
    competition_id: UUID
    source_stage_label: str
    source_round_label: str
    next_stage_label: str
    next_round_label: str
    winners: list[str]
    byes: list[str]
    created: int
    skipped: int
    fixtures: list[CompetitionFixtureRead]


class CompetitionScheduleOptimizationRead(BaseModel):
    competition_id: UUID
    moved: int
    unchanged: int
    protected_finals: int
    team_rest_minutes: int
    match_spacing_minutes: int
    fixtures: list[CompetitionFixtureRead]


class CompetitionBroadcastCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.IN_APP
    subject: str | None = Field(default=None, max_length=240)
    body: str | None = Field(default=None, max_length=8000)
    urgent: bool = False
    include_guardians: bool = True


class CompetitionBroadcastRead(BaseModel):
    competition_id: UUID
    message_id: UUID
    subject: str
    channel: CommunicationChannel
    recipient_count: int
    attempted: int
    delivered: int
    queued: int
    failed: int
    suppressed: int
    transport_mode: str


class CompetitionTicketingCreate(BaseModel):
    fixture_id: UUID
    name: str | None = Field(default=None, max_length=180)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    capacity: int = Field(ge=1)
    access_zone: str | None = Field(default=None, max_length=120)


class CompetitionTicketingRead(BaseModel):
    competition_id: UUID
    fixture_id: UUID
    event_id: UUID
    ticket_product_id: UUID
    name: str
    price: Decimal
    currency: str
    capacity: int
    sold_count: int
    access_zone: str | None
    status: str
    scheduled_at: datetime
    venue_name: str | None


class FixtureResultUpdate(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    confirmed: bool = True
    notes: str | None = Field(default=None, max_length=4000)


class FixtureOfficialAssignmentCreate(BaseModel):
    person_id: UUID
    role: OfficialRole = OfficialRole.REFEREE
    status: OfficialAssignmentStatus = OfficialAssignmentStatus.PROPOSED
    certification_level: str | None = Field(default=None, max_length=120)
    conflict_notes: str | None = Field(default=None, max_length=4000)


class FixtureOfficialAssignmentRead(BaseModel):
    id: UUID
    fixture_id: UUID
    person_id: UUID
    role: OfficialRole
    status: OfficialAssignmentStatus
    certification_level: str | None
    conflict_notes: str | None


class FixtureOfficialResponseUpdate(BaseModel):
    status: OfficialAssignmentStatus
    conflict_notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_official_response(self) -> "FixtureOfficialResponseUpdate":
        if self.status not in {
            OfficialAssignmentStatus.ACCEPTED,
            OfficialAssignmentStatus.DECLINED,
        }:
            raise ValueError("official response must be accepted or declined")
        if self.status == OfficialAssignmentStatus.DECLINED and not (
            self.conflict_notes and self.conflict_notes.strip()
        ):
            raise ValueError("declined official assignments require conflict notes")
        return self


class MyOfficialAssignmentRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    competition_id: UUID
    competition_name: str
    sport: str
    fixture_id: UUID
    home_team_name: str
    away_team_name: str
    round_label: str | None
    stage_label: str | None
    scheduled_at: datetime
    venue_name: str | None
    fixture_status: FixtureStatus
    role: OfficialRole
    status: OfficialAssignmentStatus
    certification_level: str | None
    conflict_notes: str | None
    response_required: bool
    action_label: str


class FixtureMatchEventCreate(BaseModel):
    team_id: UUID
    athlete_profile_id: UUID | None = None
    minute: int | None = Field(default=None, ge=0, le=200)
    event_type: MatchEventType
    description: str | None = Field(default=None, max_length=4000)


class FixtureMatchEventRead(BaseModel):
    id: UUID
    fixture_id: UUID
    team_id: UUID
    athlete_profile_id: UUID | None
    minute: int | None
    event_type: MatchEventType
    description: str | None


class CompetitionStandingRead(BaseModel):
    competition_id: UUID
    team_id: UUID
    team_name: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class CompetitionBracketMatchRead(BaseModel):
    round_label: str
    stage_label: str
    slot: int
    home_team_name: str | None
    away_team_name: str | None
    fixture_id: UUID | None
    status: FixtureStatus | None
    winner_team_name: str | None


class CompetitionBracketRoundRead(BaseModel):
    round_label: str
    stage_label: str
    matches: list[CompetitionBracketMatchRead]


class CompetitionBracketRead(BaseModel):
    competition_id: UUID
    format: CompetitionFormat
    rounds: list[CompetitionBracketRoundRead]


class CompetitionConflictRead(BaseModel):
    competition_id: UUID
    fixture_id: UUID | None
    conflict_key: str
    severity: str
    title: str
    description: str
    recommendation: str
