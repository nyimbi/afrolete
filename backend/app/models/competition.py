from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import (
    CompetitionFormat,
    CompetitionStatus,
    CompetitionType,
    FixtureStatus,
    MatchEventType,
    OfficialAssignmentStatus,
    OfficialRole,
)


class Competition(IdMixin, TimestampMixin, Base):
    __tablename__ = "competitions"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    sport: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    competition_type: Mapped[CompetitionType] = mapped_column(
        enum_type(CompetitionType),
        nullable=False,
        index=True,
    )
    format: Mapped[CompetitionFormat] = mapped_column(
        enum_type(CompetitionFormat),
        nullable=False,
        index=True,
    )
    season_label: Mapped[str | None] = mapped_column(String(80), index=True)
    starts_on: Mapped[date | None] = mapped_column(Date, index=True)
    ends_on: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[CompetitionStatus] = mapped_column(
        enum_type(CompetitionStatus),
        default=CompetitionStatus.DRAFT,
        nullable=False,
        index=True,
    )
    points_for_win: Mapped[int] = mapped_column(Integer, default=3)
    points_for_draw: Mapped[int] = mapped_column(Integer, default=1)
    points_for_loss: Mapped[int] = mapped_column(Integer, default=0)
    tiebreakers: Mapped[str | None] = mapped_column(Text)
    rules_summary: Mapped[str | None] = mapped_column(Text)


class CompetitionParticipant(IdMixin, TimestampMixin, Base):
    __tablename__ = "competition_participants"
    __table_args__ = (
        UniqueConstraint(
            "competition_id",
            "team_id",
            name="uq_competition_participants_competition_team",
        ),
    )

    competition_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("competitions.id"),
        index=True,
    )
    team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    seed: Mapped[int | None] = mapped_column(Integer, index=True)
    group_label: Mapped[str | None] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class AthleteTransferRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_transfer_records"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id"),
        index=True,
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("athlete_profiles.id"),
        index=True,
    )
    from_team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    to_team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    transfer_type: Mapped[str] = mapped_column(String(80), default="permanent", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="requested", nullable=False, index=True)
    requested_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_on: Mapped[date | None] = mapped_column(Date, index=True)
    window_label: Mapped[str | None] = mapped_column(String(120), index=True)
    previous_registration_ref: Mapped[str | None] = mapped_column(String(180), index=True)
    clearance_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class CompetitionEligibilityCertificate(IdMixin, TimestampMixin, Base):
    __tablename__ = "competition_eligibility_certificates"
    __table_args__ = (
        UniqueConstraint(
            "competition_id",
            "athlete_profile_id",
            "team_id",
            name="uq_competition_eligibility_certificates_scope",
        ),
        UniqueConstraint("certificate_number", name="uq_competition_eligibility_certificates_number"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id"),
        index=True,
    )
    competition_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("competitions.id"), index=True)
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("athlete_profiles.id"),
        index=True,
    )
    team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    transfer_record_id: Mapped[UUID | None] = mapped_column(
        GUID(),
        ForeignKey("athlete_transfer_records.id"),
        index=True,
    )
    issued_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    certificate_number: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    valid_from: Mapped[date | None] = mapped_column(Date, index=True)
    valid_until: Mapped[date | None] = mapped_column(Date, index=True)
    blocker_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    eligibility_summary: Mapped[str] = mapped_column(Text, nullable=False)
    checks_json: Mapped[str] = mapped_column(Text, nullable=False)


class CompetitionRegionalRuleProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "competition_regional_rule_profiles"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "country_code",
            "region_code",
            "sport",
            "age_group",
            "competition_format",
            name="uq_competition_regional_rule_profiles_scope",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    competition_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("competitions.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    region_code: Mapped[str | None] = mapped_column(String(80), index=True)
    governing_body: Mapped[str | None] = mapped_column(String(180), index=True)
    sport: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    age_group: Mapped[str | None] = mapped_column(String(80), index=True)
    competition_format: Mapped[str | None] = mapped_column(String(80), index=True)
    effective_from: Mapped[date | None] = mapped_column(Date, index=True)
    effective_until: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    min_age: Mapped[int | None] = mapped_column(Integer)
    max_age: Mapped[int | None] = mapped_column(Integer)
    roster_limit: Mapped[int | None] = mapped_column(Integer)
    match_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    substitution_limit: Mapped[int | None] = mapped_column(Integer)
    heat_policy: Mapped[str | None] = mapped_column(Text)
    eligibility_policy: Mapped[str | None] = mapped_column(Text)
    compliance_requirements: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class CompetitionRegionalRule(IdMixin, TimestampMixin, Base):
    __tablename__ = "competition_regional_rules"
    __table_args__ = (UniqueConstraint("profile_id", "category", "rule_key"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("competition_regional_rule_profiles.id"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    rule_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    rule_value: Mapped[str] = mapped_column(Text, nullable=False)
    applies_to: Mapped[str] = mapped_column(String(80), default="competition", nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(40), default="warning", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class CompetitionFixture(IdMixin, TimestampMixin, Base):
    __tablename__ = "competition_fixtures"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id"),
        index=True,
    )
    competition_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("competitions.id"),
        index=True,
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    home_team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    round_label: Mapped[str | None] = mapped_column(String(80), index=True)
    stage_label: Mapped[str | None] = mapped_column(String(80), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    venue_name: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[FixtureStatus] = mapped_column(
        enum_type(FixtureStatus),
        default=FixtureStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    result_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)


class FixtureOfficialAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "fixture_official_assignments"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "person_id",
            "role",
            name="uq_fixture_official_assignments_person_role",
        ),
    )

    fixture_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("competition_fixtures.id"),
        index=True,
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    role: Mapped[OfficialRole] = mapped_column(enum_type(OfficialRole), nullable=False, index=True)
    status: Mapped[OfficialAssignmentStatus] = mapped_column(
        enum_type(OfficialAssignmentStatus),
        default=OfficialAssignmentStatus.PROPOSED,
        nullable=False,
        index=True,
    )
    certification_level: Mapped[str | None] = mapped_column(String(120))
    conflict_notes: Mapped[str | None] = mapped_column(Text)


class FixtureMatchEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "fixture_match_events"

    fixture_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("competition_fixtures.id"),
        index=True,
    )
    team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(),
        ForeignKey("athlete_profiles.id"),
        index=True,
    )
    minute: Mapped[int | None] = mapped_column(Integer, index=True)
    event_type: Mapped[MatchEventType] = mapped_column(
        enum_type(MatchEventType),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
