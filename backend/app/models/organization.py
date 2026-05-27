from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import (
    AssociationLevel,
    CommitteeRole,
    MemberSubjectType,
    MembershipRole,
    OrganizationType,
)


class Organization(IdMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    organization_type: Mapped[OrganizationType] = mapped_column(
        enum_type(OrganizationType), nullable=False
    )
    association_level: Mapped[AssociationLevel | None] = mapped_column(
        enum_type(AssociationLevel), index=True
    )
    parent_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("organizations.id"))
    country_code: Mapped[str | None] = mapped_column(String(2))
    primary_sport: Mapped[str | None] = mapped_column(String(80))
    mission: Mapped[str | None] = mapped_column(Text)
    public_name: Mapped[str | None] = mapped_column(String(240))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(64))
    website_url: Mapped[str | None] = mapped_column(String(500))
    subdomain: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    brand_primary_color: Mapped[str | None] = mapped_column(String(16))
    brand_secondary_color: Mapped[str | None] = mapped_column(String(16))


class Membership(IdMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "subject_type",
            "subject_id",
            "role",
            name="uq_memberships_subject_role",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    subject_type: Mapped[MemberSubjectType] = mapped_column(
        enum_type(MemberSubjectType),
        default=MemberSubjectType.PERSON,
        nullable=False,
        index=True,
    )
    subject_id: Mapped[UUID] = mapped_column(GUID(), index=True)
    role: Mapped[MembershipRole] = mapped_column(
        enum_type(MembershipRole), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class Committee(IdMixin, TimestampMixin, Base):
    __tablename__ = "committees"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    level: Mapped[AssociationLevel | None] = mapped_column(enum_type(AssociationLevel), index=True)
    mandate: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class CommitteeMembership(IdMixin, TimestampMixin, Base):
    __tablename__ = "committee_memberships"
    __table_args__ = (
        UniqueConstraint(
            "committee_id",
            "person_id",
            "role",
            name="uq_committee_memberships_person_role",
        ),
    )

    committee_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("committees.id"), index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    role: Mapped[CommitteeRole] = mapped_column(
        enum_type(CommitteeRole), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
