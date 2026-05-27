from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin
from app.models.enums import MembershipRole, OrganizationType


class Organization(IdMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    organization_type: Mapped[OrganizationType] = mapped_column(Enum(OrganizationType), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))
    country_code: Mapped[str | None] = mapped_column(String(2))
    primary_sport: Mapped[str | None] = mapped_column(String(80))
    mission: Mapped[str | None] = mapped_column(Text)


class Membership(IdMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organization_id", "person_id", "role"),)

    organization_id: Mapped[str] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[str] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)

