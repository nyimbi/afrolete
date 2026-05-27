from datetime import datetime
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import MetricCategory, MetricSource, MetricVerificationStatus


class PerformanceMetricDefinition(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_metric_definitions"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "sport",
            "code",
            name="uq_performance_metric_definitions_org_sport_code",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[MetricCategory] = mapped_column(
        enum_type(MetricCategory), nullable=False, index=True
    )
    unit: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(Text)
    min_value: Mapped[float | None] = mapped_column(Float)
    max_value: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    higher_is_better: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class AthletePerformanceObservation(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_performance_observations"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    metric_definition_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_metric_definitions.id"), index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    value: Mapped[float] = mapped_column(Float, nullable=False)
    raw_value: Mapped[str | None] = mapped_column(String(160))
    observed_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    source: Mapped[MetricSource] = mapped_column(enum_type(MetricSource), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    verification_status: Mapped[MetricVerificationStatus] = mapped_column(
        enum_type(MetricVerificationStatus),
        default=MetricVerificationStatus.VERIFIED,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)


class AthleteAssessment(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_assessments"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    assessed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    assessed_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    physical_score: Mapped[float] = mapped_column(Float, nullable=False)
    technical_score: Mapped[float] = mapped_column(Float, nullable=False)
    tactical_score: Mapped[float] = mapped_column(Float, nullable=False)
    mental_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[MetricVerificationStatus] = mapped_column(
        enum_type(MetricVerificationStatus),
        default=MetricVerificationStatus.VERIFIED,
        nullable=False,
        index=True,
    )
