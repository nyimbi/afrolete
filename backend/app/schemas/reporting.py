from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    InsightSeverity,
    InsightStatus,
    ReportCategory,
    ReportFormat,
    ReportFrequency,
    ReportRunStatus,
)


class ReportDefinitionCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    category: ReportCategory
    description: str | None = Field(default=None, max_length=4000)
    default_format: ReportFormat = ReportFormat.ONLINE
    parameter_schema: str | None = Field(default=None, max_length=8000)
    template: str | None = Field(default=None, max_length=8000)
    ai_assisted: bool = False


class ReportDefinitionRead(ReportDefinitionCreate):
    id: UUID
    status: str


class GeneratedReportCreate(BaseModel):
    organization_id: UUID
    report_definition_id: UUID
    team_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    competition_id: UUID | None = None
    event_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    output_format: ReportFormat = ReportFormat.ONLINE
    period_start: date | None = None
    period_end: date | None = None
    parameters: str | None = Field(default=None, max_length=8000)


class GeneratedReportRead(GeneratedReportCreate):
    id: UUID
    requested_by_person_id: UUID | None
    status: ReportRunStatus
    summary: str
    findings: str | None
    recommendations: str | None
    artifact_url: str | None
    shared_token: str | None
    expires_at: datetime | None


class ScheduledReportCreate(BaseModel):
    organization_id: UUID
    report_definition_id: UUID
    name: str = Field(min_length=2, max_length=180)
    frequency: ReportFrequency = ReportFrequency.WEEKLY
    delivery_channels: str = Field(default="in_app", max_length=240)
    recipients: str | None = Field(default=None, max_length=4000)
    next_run_at: datetime | None = None


class ScheduledReportRead(ScheduledReportCreate):
    id: UUID
    last_run_at: datetime | None
    status: str


class IntelligenceInsightCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID | None = None
    team_id: UUID | None = None
    event_id: UUID | None = None
    agent_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    insight_type: str = Field(min_length=2, max_length=80)
    severity: InsightSeverity = InsightSeverity.INFO
    confidence: float = Field(default=0.75, ge=0, le=1)
    evidence: str | None = Field(default=None, max_length=8000)
    recommendation: str | None = Field(default=None, max_length=8000)
    model_name: str | None = Field(default=None, max_length=120)


class IntelligenceInsightUpdate(BaseModel):
    status: InsightStatus


class IntelligenceInsightRead(IntelligenceInsightCreate):
    id: UUID
    status: InsightStatus
    reviewed_by_person_id: UUID | None


class PredictiveRiskScoreCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    model_name: str = Field(min_length=2, max_length=120)
    score: int = Field(ge=0, le=100)
    drivers: str | None = Field(default=None, max_length=8000)
    recommendation: str | None = Field(default=None, max_length=8000)
    valid_for_date: date


class PredictiveRiskScoreRead(PredictiveRiskScoreCreate):
    id: UUID
    risk_band: str


class ReportExportJobCreate(BaseModel):
    organization_id: UUID
    generated_report_id: UUID
    output_format: ReportFormat
    destination: str = Field(min_length=2, max_length=500)
    webhook_url: str | None = Field(default=None, max_length=500)


class ReportExportJobRead(ReportExportJobCreate):
    id: UUID
    status: ReportRunStatus
    completed_at: datetime | None


class RenderedReportRead(BaseModel):
    report_id: UUID
    organization_id: UUID
    output_format: ReportFormat
    artifact_url: str
    content_type: str
    size_bytes: int
    page_count: int | None
    sheet_count: int | None
    checksum: str
    body_preview: str
    rendered_at: datetime


class ReportArtifactAccessRead(BaseModel):
    report_id: UUID
    organization_id: UUID
    output_format: ReportFormat
    artifact_url: str
    signed_url: str
    expires_at: datetime
    content_type: str
    filename: str
    checksum: str
    size_bytes: int


class ReportVerificationRead(BaseModel):
    report_id: UUID
    organization_id: UUID
    passed: bool
    score: int
    findings: list[str]
    recommendation: str
    verified_at: datetime


class ReportChartRead(BaseModel):
    chart_key: str
    title: str
    chart_type: str
    labels: list[str]
    values: list[float]
    insight: str


class ReportingBenchmarkRead(BaseModel):
    model_name: str
    sample_size: int
    average_score: float
    high_risk_count: int
    benchmark_band: str
    recommendation: str


class ReportingSummaryRead(BaseModel):
    organization_id: UUID
    definitions: int
    generated_reports: int
    scheduled_reports: int
    open_insights: int
    critical_insights: int
    high_risk_scores: int
    export_jobs: int
