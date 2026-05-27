from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class Person(IdMixin, TimestampMixin, Base):
    __tablename__ = "persons"

    display_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    given_name: Mapped[str | None] = mapped_column(String(120))
    family_name: Mapped[str | None] = mapped_column(String(120))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    primary_email: Mapped[str | None] = mapped_column(String(320), index=True)
    primary_phone: Mapped[str | None] = mapped_column(String(64))
    country_code: Mapped[str | None] = mapped_column(String(2))
    notes: Mapped[str | None] = mapped_column(Text)


class AppUser(IdMixin, TimestampMixin, Base):
    __tablename__ = "app_users"

    keycloak_sub: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(240))
    locale: Mapped[str] = mapped_column(String(32), default="en")
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
