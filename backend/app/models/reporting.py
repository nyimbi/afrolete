from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import (
    InsightSeverity,
    InsightStatus,
    ReportCategory,
    ReportFormat,
    ReportFrequency,
    ReportRunStatus,
)


class ReportDefinition(IdMixin, TimestampMixin, Base):
    __tablename__ = "report_definitions"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    category: Mapped[ReportCategory] = mapped_column(enum_type(ReportCategory), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    default_format: Mapped[ReportFormat] = mapped_column(
        enum_type(ReportFormat),
        default=ReportFormat.ONLINE,
        nullable=False,
        index=True,
    )
    parameter_schema: Mapped[str | None] = mapped_column(Text)
    template: Mapped[str | None] = mapped_column(Text)
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class GeneratedReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "generated_reports"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    report_definition_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("report_definitions.id"), index=True
    )
    requested_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    competition_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("competitions.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    output_format: Mapped[ReportFormat] = mapped_column(
        enum_type(ReportFormat),
        default=ReportFormat.ONLINE,
        nullable=False,
        index=True,
    )
    status: Mapped[ReportRunStatus] = mapped_column(
        enum_type(ReportRunStatus),
        default=ReportRunStatus.READY,
        nullable=False,
        index=True,
    )
    period_start: Mapped[date | None] = mapped_column(index=True)
    period_end: Mapped[date | None] = mapped_column(index=True)
    parameters: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)
    artifact_url: Mapped[str | None] = mapped_column(String(500))
    shared_token: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ScheduledReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "scheduled_reports"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    report_definition_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("report_definitions.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    frequency: Mapped[ReportFrequency] = mapped_column(
        enum_type(ReportFrequency),
        default=ReportFrequency.WEEKLY,
        nullable=False,
        index=True,
    )
    delivery_channels: Mapped[str] = mapped_column(String(240), default="in_app", nullable=False)
    recipients: Mapped[str | None] = mapped_column(Text)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class IntelligenceInsight(IdMixin, TimestampMixin, Base):
    __tablename__ = "intelligence_insights"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    agent_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("agents.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    insight_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    severity: Mapped[InsightSeverity] = mapped_column(
        enum_type(InsightSeverity),
        default=InsightSeverity.INFO,
        nullable=False,
        index=True,
    )
    status: Mapped[InsightStatus] = mapped_column(
        enum_type(InsightStatus),
        default=InsightStatus.NEW,
        nullable=False,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(120))
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))


class PredictiveRiskScore(IdMixin, TimestampMixin, Base):
    __tablename__ = "predictive_risk_scores"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    model_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    risk_band: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    drivers: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    valid_for_date: Mapped[date] = mapped_column(nullable=False, index=True)


class ReportExportJob(IdMixin, TimestampMixin, Base):
    __tablename__ = "report_export_jobs"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    generated_report_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("generated_reports.id"), index=True
    )
    output_format: Mapped[ReportFormat] = mapped_column(enum_type(ReportFormat), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(500), nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ReportRunStatus] = mapped_column(
        enum_type(ReportRunStatus),
        default=ReportRunStatus.QUEUED,
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
