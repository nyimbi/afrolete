from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin
from app.models.enums import CommitteeRole, RosterStatus, SportFormat, TeamRole


class Team(IdMixin, TimestampMixin, Base):
    __tablename__ = "teams"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    sport: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    sport_format: Mapped[SportFormat] = mapped_column(
        Enum(SportFormat),
        default=SportFormat.TEAM,
        nullable=False,
        index=True,
    )
    age_group: Mapped[str | None] = mapped_column(String(80))
    gender_category: Mapped[str | None] = mapped_column(String(80))
    season_label: Mapped[str | None] = mapped_column(String(80))


class AthleteProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_profiles"
    __table_args__ = (UniqueConstraint("organization_id", "person_id"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    athlete_code: Mapped[str | None] = mapped_column(String(80), index=True)
    dominant_side: Mapped[str | None] = mapped_column(String(40))
    medical_visibility: Mapped[str] = mapped_column(String(40), default="restricted")
    development_notes: Mapped[str | None] = mapped_column(Text)


class TeamRosterEntry(IdMixin, TimestampMixin, Base):
    __tablename__ = "team_roster_entries"
    __table_args__ = (UniqueConstraint("team_id", "athlete_profile_id"),)

    team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    role: Mapped[TeamRole] = mapped_column(Enum(TeamRole), default=TeamRole.PLAYER, nullable=False)
    jersey_number: Mapped[str | None] = mapped_column(String(16))
    primary_position: Mapped[str | None] = mapped_column(String(80))
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[RosterStatus] = mapped_column(
        Enum(RosterStatus),
        default=RosterStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class GuardianRelationship(IdMixin, TimestampMixin, Base):
    __tablename__ = "guardian_relationships"
    __table_args__ = (UniqueConstraint("athlete_person_id", "guardian_person_id"),)

    athlete_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    guardian_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    relationship: Mapped[str] = mapped_column(String(80), nullable=False)
    can_sign_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_medical: Mapped[bool] = mapped_column(Boolean, default=False)
    emergency_contact: Mapped[bool] = mapped_column(Boolean, default=False)


class TeamCommittee(IdMixin, TimestampMixin, Base):
    __tablename__ = "team_committees"
    __table_args__ = (UniqueConstraint("team_id", "name"),)

    team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    mandate: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class TeamCommitteeMembership(IdMixin, TimestampMixin, Base):
    __tablename__ = "team_committee_memberships"
    __table_args__ = (
        UniqueConstraint(
            "team_committee_id",
            "person_id",
            "role",
            name="uq_team_committee_memberships_person_role",
        ),
    )

    team_committee_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("team_committees.id"), index=True
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    role: Mapped[CommitteeRole] = mapped_column(Enum(CommitteeRole), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
