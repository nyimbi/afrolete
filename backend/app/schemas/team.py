from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CommitteeRole, RosterStatus, SportFormat, TeamRole


class TeamCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    sport: str = Field(min_length=2, max_length=80)
    sport_format: SportFormat = SportFormat.TEAM
    age_group: str | None = Field(default=None, max_length=80)
    gender_category: str | None = Field(default=None, max_length=80)
    season_label: str | None = Field(default=None, max_length=80)


class TeamRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    sport: str
    sport_format: SportFormat
    age_group: str | None
    gender_category: str | None
    season_label: str | None


class TeamMemberAdd(BaseModel):
    person_id: UUID
    role: TeamRole = TeamRole.PLAYER
    status: RosterStatus = RosterStatus.ACTIVE
    primary_position: str | None = Field(default=None, max_length=80)
    jersey_number: str | None = Field(default=None, max_length=16)
    is_captain: bool = False


class TeamRosterEntryRead(BaseModel):
    id: UUID
    team_id: UUID
    athlete_profile_id: UUID
    role: TeamRole
    primary_position: str | None
    jersey_number: str | None
    is_captain: bool
    status: RosterStatus


class TeamCommitteeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    mandate: str | None = Field(default=None, max_length=2000)


class TeamCommitteeRead(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    mandate: str | None
    status: str


class TeamCommitteeMemberAdd(BaseModel):
    person_id: UUID
    role: CommitteeRole
    title: str | None = Field(default=None, max_length=160)


class TeamCommitteeMembershipRead(BaseModel):
    id: UUID
    team_committee_id: UUID
    person_id: UUID
    role: CommitteeRole
    title: str | None
    status: str
