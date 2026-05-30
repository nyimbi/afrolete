from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class ProductTourProgress(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_tour_progress"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "person_id",
            "tour_key",
            name="uq_product_tour_progress_org_person_tour",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    tour_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    surface: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(120), default="coach", nullable=False, index=True)
    current_step_key: Mapped[str | None] = mapped_column(String(120), index=True)
    completed_steps_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    skipped_steps_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    star_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    last_feedback: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ProductHelpInteraction(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_help_interactions"

    organization_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    surface: Mapped[str | None] = mapped_column(String(120), index=True)
    role: Mapped[str | None] = mapped_column(String(120), index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    selected_article_key: Mapped[str | None] = mapped_column(String(120), index=True)
