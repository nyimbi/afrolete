from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    AssociationLevel,
    CommitteeRole,
    MemberSubjectType,
    MembershipRole,
    OrganizationType,
    TeamRole,
)


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=240)
    slug: str | None = Field(default=None, max_length=120)
    organization_type: OrganizationType
    association_level: AssociationLevel | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    primary_sport: str | None = Field(default=None, max_length=80)
    mission: str | None = Field(default=None, max_length=2000)
    public_name: str | None = Field(default=None, max_length=240)
    contact_email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=64)
    website_url: str | None = Field(default=None, max_length=500)
    subdomain: str | None = Field(default=None, max_length=120)
    logo_url: str | None = Field(default=None, max_length=500)
    brand_primary_color: str | None = Field(default=None, max_length=16)
    brand_secondary_color: str | None = Field(default=None, max_length=16)


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_type: OrganizationType
    association_level: AssociationLevel | None
    country_code: str | None
    primary_sport: str | None
    mission: str | None
    public_name: str | None
    contact_email: str | None
    contact_phone: str | None
    website_url: str | None
    subdomain: str | None
    logo_url: str | None
    brand_primary_color: str | None
    brand_secondary_color: str | None
    my_roles: list[MembershipRole] = Field(default_factory=list)


class PublicSiteTeamRead(BaseModel):
    id: UUID
    name: str
    sport: str
    age_group: str | None
    gender_category: str | None
    season_label: str | None


class PublicSiteEventRead(BaseModel):
    id: UUID
    team_id: UUID | None
    event_type: str
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    venue_name: str | None


class OrganizationPublicSiteRead(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_type: OrganizationType
    country_code: str | None
    primary_sport: str | None
    mission: str | None
    public_name: str | None
    contact_email: str | None
    contact_phone: str | None
    website_url: str | None
    subdomain: str | None
    logo_url: str | None
    brand_primary_color: str | None
    brand_secondary_color: str | None
    teams: list[PublicSiteTeamRead]
    upcoming_events: list[PublicSiteEventRead]


class PublicRegistrationInquiryCreate(BaseModel):
    team_id: UUID | None = None
    athlete_name: str = Field(min_length=2, max_length=240)
    guardian_name: str | None = Field(default=None, max_length=240)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    age_group: str | None = Field(default=None, max_length=80)
    sport_interest: str | None = Field(default=None, max_length=120)
    message: str | None = Field(default=None, max_length=2000)
    source_url: str | None = Field(default=None, max_length=500)


class RegistrationInquiryRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    athlete_name: str
    guardian_name: str | None
    email: str
    phone: str | None
    age_group: str | None
    sport_interest: str | None
    message: str | None
    source_url: str | None
    status: str
    created_at: datetime


class RegistrationInquiryConversionCreate(BaseModel):
    team_id: UUID | None = None
    role: TeamRole = TeamRole.PLAYER
    create_guardian: bool = True
    jersey_number: str | None = Field(default=None, max_length=16)
    primary_position: str | None = Field(default=None, max_length=80)


class RegistrationInquiryConversionRead(BaseModel):
    inquiry: RegistrationInquiryRead
    athlete_person_id: UUID
    athlete_profile_id: UUID
    roster_entry_id: UUID | None
    guardian_person_id: UUID | None


class MemberAdd(BaseModel):
    subject_type: MemberSubjectType = MemberSubjectType.PERSON
    subject_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, min_length=2, max_length=240)
    role: MembershipRole
    title: str | None = Field(default=None, max_length=160)


class MembershipRead(BaseModel):
    id: UUID
    organization_id: UUID
    subject_type: MemberSubjectType
    subject_id: UUID
    role: MembershipRole
    title: str | None
    status: str


class CommitteeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    level: AssociationLevel | None = None
    mandate: str | None = Field(default=None, max_length=2000)


class CommitteeRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    level: AssociationLevel | None
    mandate: str | None
    status: str


class CommitteeMemberAdd(BaseModel):
    person_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, min_length=2, max_length=240)
    role: CommitteeRole
    title: str | None = Field(default=None, max_length=160)


class CommitteeMembershipRead(BaseModel):
    id: UUID
    committee_id: UUID
    person_id: UUID
    role: CommitteeRole
    title: str | None
    status: str
