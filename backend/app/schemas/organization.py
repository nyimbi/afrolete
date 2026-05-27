from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    AssociationLevel,
    CommitteeRole,
    MemberSubjectType,
    MembershipRole,
    OrganizationType,
)


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=240)
    slug: str | None = Field(default=None, max_length=120)
    organization_type: OrganizationType
    association_level: AssociationLevel | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    primary_sport: str | None = Field(default=None, max_length=80)
    mission: str | None = Field(default=None, max_length=2000)


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_type: OrganizationType
    association_level: AssociationLevel | None
    country_code: str | None
    primary_sport: str | None
    mission: str | None
    my_roles: list[MembershipRole] = Field(default_factory=list)


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
