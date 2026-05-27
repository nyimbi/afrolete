import csv
import base64
import hmac
import io
import json
import time
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from html import escape as xml_escape
from pathlib import Path
from urllib.parse import quote
from uuid import UUID, uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.commercial import FinanceInvoice, Ticket
from app.models.competition import Competition
from app.models.enums import InsightSeverity, InsightStatus, ReportFormat, ReportRunStatus
from app.models.event import AttendanceRecord, ConsentRequest, Event
from app.models.organization import Membership, Organization
from app.models.performance import AthleteAssessment, AthletePerformanceObservation
from app.models.reporting import (
    GeneratedReport,
    IntelligenceInsight,
    PredictiveRiskScore,
    ReportDefinition,
    ReportExportJob,
    ScheduledReport,
)
from app.models.team import AthleteProfile, Team
from app.core.config import Settings, get_settings
from app.schemas.reporting import (
    GeneratedReportCreate,
    IntelligenceInsightCreate,
    IntelligenceInsightUpdate,
    PredictiveRiskScoreCreate,
    ReportDefinitionCreate,
    ReportExportJobCreate,
    ScheduledReportCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.storage.objects import get_object, put_object


async def ensure_manage_reporting(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_report_definition(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ReportDefinitionCreate,
    authz: AuthorizationService,
) -> ReportDefinition:
    await get_organization(db, payload.organization_id)
    await ensure_manage_reporting(authz, identity, payload.organization_id)
    definition = ReportDefinition(**payload.model_dump())
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    return definition


async def list_report_definitions(db: AsyncSession, organization_id: UUID) -> list[ReportDefinition]:
    return list(
        (
            await db.scalars(
                select(ReportDefinition)
                .where(ReportDefinition.organization_id == organization_id)
                .order_by(ReportDefinition.category, ReportDefinition.name)
            )
        ).all()
    )


async def generate_report(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: GeneratedReportCreate,
    authz: AuthorizationService,
) -> GeneratedReport:
    await ensure_manage_reporting(authz, identity, payload.organization_id)
    definition = await get_definition_for_organization(
        db,
        payload.report_definition_id,
        payload.organization_id,
    )
    summary, findings, recommendations = await synthesize_report_text(db, payload, definition)
    report = GeneratedReport(
        requested_by_person_id=identity.person_id,
        status=ReportRunStatus.READY,
        summary=summary,
        findings=findings,
        recommendations=recommendations,
        shared_token=f"rpt_{uuid4().hex}",
        expires_at=datetime.now(UTC) + timedelta(days=14),
        **payload.model_dump(),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def list_generated_reports(db: AsyncSession, organization_id: UUID) -> list[GeneratedReport]:
    return list(
        (
            await db.scalars(
                select(GeneratedReport)
                .where(GeneratedReport.organization_id == organization_id)
                .order_by(GeneratedReport.created_at.desc())
            )
        ).all()
    )


async def create_scheduled_report(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ScheduledReportCreate,
    authz: AuthorizationService,
) -> ScheduledReport:
    await ensure_manage_reporting(authz, identity, payload.organization_id)
    await get_definition_for_organization(db, payload.report_definition_id, payload.organization_id)
    schedule = ScheduledReport(**payload.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def list_scheduled_reports(db: AsyncSession, organization_id: UUID) -> list[ScheduledReport]:
    return list(
        (
            await db.scalars(
                select(ScheduledReport)
                .where(ScheduledReport.organization_id == organization_id)
                .order_by(ScheduledReport.next_run_at, ScheduledReport.name)
            )
        ).all()
    )


async def create_insight(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: IntelligenceInsightCreate,
    authz: AuthorizationService,
) -> IntelligenceInsight:
    await ensure_manage_reporting(authz, identity, payload.organization_id)
    await validate_scope_refs(db, payload.organization_id, payload.team_id, payload.athlete_profile_id, payload.event_id, payload.agent_id)
    insight = IntelligenceInsight(**payload.model_dump())
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight


async def list_insights(db: AsyncSession, organization_id: UUID) -> list[IntelligenceInsight]:
    return list(
        (
            await db.scalars(
                select(IntelligenceInsight)
                .where(IntelligenceInsight.organization_id == organization_id)
                .order_by(IntelligenceInsight.severity.desc(), IntelligenceInsight.created_at.desc())
            )
        ).all()
    )


async def update_insight_status(
    db: AsyncSession,
    identity: CurrentIdentity,
    insight_id: UUID,
    payload: IntelligenceInsightUpdate,
    authz: AuthorizationService,
) -> IntelligenceInsight:
    insight = await db.get(IntelligenceInsight, insight_id)
    if insight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    await ensure_manage_reporting(authz, identity, insight.organization_id)
    insight.status = payload.status
    insight.reviewed_by_person_id = identity.person_id
    await db.commit()
    await db.refresh(insight)
    return insight


async def create_risk_score(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PredictiveRiskScoreCreate,
    authz: AuthorizationService,
) -> PredictiveRiskScore:
    await ensure_manage_reporting(authz, identity, payload.organization_id)
    await get_athlete_for_organization(db, payload.athlete_profile_id, payload.organization_id)
    risk_score = PredictiveRiskScore(risk_band=risk_band(payload.score), **payload.model_dump())
    db.add(risk_score)
    await db.commit()
    await db.refresh(risk_score)
    return risk_score


async def list_risk_scores(db: AsyncSession, organization_id: UUID) -> list[PredictiveRiskScore]:
    return list(
        (
            await db.scalars(
                select(PredictiveRiskScore)
                .where(PredictiveRiskScore.organization_id == organization_id)
                .order_by(PredictiveRiskScore.valid_for_date.desc(), PredictiveRiskScore.score.desc())
            )
        ).all()
    )


async def create_export_job(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ReportExportJobCreate,
    authz: AuthorizationService,
) -> ReportExportJob:
    await ensure_manage_reporting(authz, identity, payload.organization_id)
    report = await db.get(GeneratedReport, payload.generated_report_id)
    if report is None or report.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    export = ReportExportJob(
        status=ReportRunStatus.READY,
        completed_at=datetime.now(UTC),
        **payload.model_dump(),
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


async def list_export_jobs(db: AsyncSession, organization_id: UUID) -> list[ReportExportJob]:
    return list(
        (
            await db.scalars(
                select(ReportExportJob)
                .where(ReportExportJob.organization_id == organization_id)
                .order_by(ReportExportJob.created_at.desc())
            )
        ).all()
    )


async def reporting_summary(db: AsyncSession, organization_id: UUID) -> dict:
    definitions = await list_report_definitions(db, organization_id)
    reports = await list_generated_reports(db, organization_id)
    schedules = await list_scheduled_reports(db, organization_id)
    insights = await list_insights(db, organization_id)
    risks = await list_risk_scores(db, organization_id)
    exports = await list_export_jobs(db, organization_id)
    return {
        "organization_id": organization_id,
        "definitions": len(definitions),
        "generated_reports": len(reports),
        "scheduled_reports": len(schedules),
        "open_insights": sum(1 for insight in insights if insight.status == InsightStatus.NEW),
        "critical_insights": sum(
            1
            for insight in insights
            if insight.severity in {InsightSeverity.WARNING, InsightSeverity.CRITICAL}
        ),
        "high_risk_scores": sum(1 for score in risks if score.score >= 70),
        "export_jobs": len(exports),
    }


async def render_report_artifact(
    db: AsyncSession,
    identity: CurrentIdentity,
    report_id: UUID,
    output_format: ReportFormat | None,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict:
    report = await get_report(db, report_id)
    await ensure_manage_reporting(authz, identity, report.organization_id)
    selected_format = output_format or report.output_format
    now = datetime.now(UTC)
    artifact = build_report_artifact(report, selected_format)
    checksum = artifact["checksum"]
    stored = persist_report_artifact(report, artifact, settings or get_settings())
    artifact_url = stored["artifact_url"]
    report.output_format = selected_format
    report.artifact_url = artifact_url
    report.status = ReportRunStatus.READY
    await db.commit()
    await db.refresh(report)
    return {
        "report_id": report.id,
        "organization_id": report.organization_id,
        "output_format": selected_format,
        "artifact_url": artifact_url,
        "content_type": artifact["content_type"],
        "size_bytes": len(artifact["content"]),
        "page_count": 1 if selected_format == ReportFormat.PDF else None,
        "sheet_count": 2 if selected_format == ReportFormat.EXCEL else None,
        "checksum": checksum,
        "body_preview": artifact["body_preview"],
        "rendered_at": now,
    }


async def downloadable_report_artifact(
    db: AsyncSession,
    identity: CurrentIdentity,
    report_id: UUID,
    output_format: ReportFormat | None,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    report = await get_report(db, report_id)
    await ensure_manage_reporting(authz, identity, report.organization_id)
    selected_format = output_format or report.output_format
    artifact = build_report_artifact(report, selected_format)
    stored = persist_report_artifact(report, artifact, settings or get_settings())
    report.output_format = selected_format
    report.artifact_url = stored["artifact_url"]
    report.status = ReportRunStatus.READY
    await db.commit()
    artifact.update(stored)
    return artifact


async def signed_report_artifact_access(
    db: AsyncSession,
    identity: CurrentIdentity,
    report_id: UUID,
    output_format: ReportFormat | None,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    report = await get_report(db, report_id)
    await ensure_manage_reporting(authz, identity, report.organization_id)
    selected_settings = settings or get_settings()
    selected_format = output_format or report.output_format
    artifact = build_report_artifact(report, selected_format)
    stored = persist_report_artifact(report, artifact, selected_settings)
    expires_at = datetime.now(UTC) + timedelta(
        seconds=selected_settings.report_artifact_url_ttl_seconds
    )
    signed_url = signed_report_artifact_url(
        selected_settings,
        report.organization_id,
        report.id,
        stored["storage_name"],
        expires_at,
    )
    report.output_format = selected_format
    report.artifact_url = stored["artifact_url"]
    report.status = ReportRunStatus.READY
    await db.commit()
    return {
        "report_id": report.id,
        "organization_id": report.organization_id,
        "output_format": selected_format,
        "artifact_url": stored["artifact_url"],
        "signed_url": signed_url,
        "expires_at": expires_at,
        "content_type": artifact["content_type"],
        "filename": artifact["filename"],
        "checksum": artifact["checksum"],
        "size_bytes": len(artifact["content"]),
    }


def read_signed_report_artifact(
    organization_id: UUID,
    report_id: UUID,
    filename: str,
    expires: int,
    signature: str,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid artifact name")
    if expires < int(time.time()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Artifact link expired")
    expected = report_artifact_signature(selected_settings, organization_id, report_id, filename, expires)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid artifact signature")

    content = get_object(
        selected_settings,
        local_root=selected_settings.report_artifact_dir,
        key=(Path(str(organization_id)) / str(report_id) / filename).as_posix(),
    )
    return {
        "content": content,
        "content_type": report_content_type_for_filename(filename),
        "filename": public_artifact_filename(filename),
        "checksum": sha256(content).hexdigest(),
    }


async def verify_report_artifact(
    db: AsyncSession,
    identity: CurrentIdentity,
    report_id: UUID,
    authz: AuthorizationService,
) -> dict:
    report = await get_report(db, report_id)
    await ensure_manage_reporting(authz, identity, report.organization_id)
    findings: list[str] = []
    score = 100
    if report.status != ReportRunStatus.READY:
        findings.append("Report is not marked ready.")
        score -= 25
    if not report.summary or len(report.summary) < 40:
        findings.append("Summary is too thin for stakeholder delivery.")
        score -= 20
    if not report.findings:
        findings.append("Findings are missing.")
        score -= 15
    if not report.recommendations:
        findings.append("Recommendations are missing.")
        score -= 15
    if report.period_start and report.period_end and report.period_start > report.period_end:
        findings.append("Report period is invalid.")
        score -= 25
    if not report.shared_token or not report.expires_at:
        findings.append("Share token or expiry is missing.")
        score -= 10
    elif report.expires_at < datetime.now(UTC):
        findings.append("Share token is expired.")
        score -= 15
    if not report.artifact_url:
        findings.append("Rendered artifact is missing.")
        score -= 10
    if not findings:
        findings.append("Report is ready for stakeholder review and export.")
    score = max(score, 0)
    return {
        "report_id": report.id,
        "organization_id": report.organization_id,
        "passed": score >= 80,
        "score": score,
        "findings": findings,
        "recommendation": "Publish or schedule delivery." if score >= 80 else "Render and complete missing narrative fields before delivery.",
        "verified_at": datetime.now(UTC),
    }


async def report_charts(db: AsyncSession, organization_id: UUID) -> list[dict]:
    summary = await reporting_summary(db, organization_id)
    risks = await list_risk_scores(db, organization_id)
    insights = await list_insights(db, organization_id)
    severity_counts = {
        "info": sum(1 for insight in insights if insight.severity == InsightSeverity.INFO),
        "watch": sum(1 for insight in insights if insight.severity == InsightSeverity.WATCH),
        "warning": sum(1 for insight in insights if insight.severity == InsightSeverity.WARNING),
        "critical": sum(1 for insight in insights if insight.severity == InsightSeverity.CRITICAL),
    }
    risk_counts = {
        "normal": sum(1 for risk in risks if risk.risk_band == "normal"),
        "watch": sum(1 for risk in risks if risk.risk_band == "watch"),
        "warning": sum(1 for risk in risks if risk.risk_band == "warning"),
        "high": sum(1 for risk in risks if risk.risk_band == "high"),
    }
    return [
        {
            "chart_key": "reporting-throughput",
            "title": "Reporting throughput",
            "chart_type": "bar",
            "labels": ["Definitions", "Generated", "Scheduled", "Exports"],
            "values": [
                float(summary["definitions"]),
                float(summary["generated_reports"]),
                float(summary["scheduled_reports"]),
                float(summary["export_jobs"]),
            ],
            "insight": "Use this to spot whether teams are creating reports without delivery automation.",
        },
        {
            "chart_key": "insight-severity",
            "title": "Insight severity",
            "chart_type": "donut",
            "labels": list(severity_counts),
            "values": [float(value) for value in severity_counts.values()],
            "insight": "Critical and warning insights should drive review queues before routine reports.",
        },
        {
            "chart_key": "risk-bands",
            "title": "Predictive risk bands",
            "chart_type": "stacked_bar",
            "labels": list(risk_counts),
            "values": [float(value) for value in risk_counts.values()],
            "insight": "High and warning risk bands should trigger training-load and safeguarding follow-ups.",
        },
    ]


async def reporting_benchmarks(db: AsyncSession, organization_id: UUID) -> list[dict]:
    risks = await list_risk_scores(db, organization_id)
    grouped: dict[str, list[PredictiveRiskScore]] = {}
    for risk in risks:
        grouped.setdefault(risk.model_name, []).append(risk)
    benchmarks: list[dict] = []
    for model_name, scores in sorted(grouped.items()):
        average = sum(score.score for score in scores) / len(scores)
        high_risk_count = sum(1 for score in scores if score.score >= 70)
        band = risk_band(round(average))
        benchmarks.append(
            {
                "model_name": model_name,
                "sample_size": len(scores),
                "average_score": round(average, 2),
                "high_risk_count": high_risk_count,
                "benchmark_band": band,
                "recommendation": benchmark_recommendation(band, high_risk_count),
            }
        )
    return benchmarks


async def generate_live_insight(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> IntelligenceInsight:
    await ensure_manage_reporting(authz, identity, organization_id)
    reports = await list_generated_reports(db, organization_id)
    risks = await list_risk_scores(db, organization_id)
    summary = await reporting_summary(db, organization_id)
    highest_risk = max((risk.score for risk in risks), default=0)
    severity = InsightSeverity.CRITICAL if highest_risk >= 85 else InsightSeverity.WARNING if highest_risk >= 70 else InsightSeverity.WATCH
    title = "AI reporting review: delivery and risk signals"
    evidence = (
        f"{summary['generated_reports']} reports, {summary['export_jobs']} exports, "
        f"{summary['open_insights']} open insights, highest risk score {highest_risk}."
    )
    recommendation = (
        "Prioritize high-risk athlete review before publishing the next stakeholder packet."
        if highest_risk >= 70
        else "Convert the latest report into scheduled delivery and keep monitoring trend changes."
    )
    insight = IntelligenceInsight(
        organization_id=organization_id,
        title=title,
        insight_type="ai_generated_reporting_review",
        severity=severity,
        confidence=0.82 if reports else 0.66,
        evidence=evidence,
        recommendation=recommendation,
        model_name="afrolete-deterministic-insight-v1",
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight


async def synthesize_report_text(
    db: AsyncSession,
    payload: GeneratedReportCreate,
    definition: ReportDefinition,
) -> tuple[str, str, str]:
    metrics = {
        "memberships": await count_rows(db, Membership, payload.organization_id),
        "teams": await count_rows(db, Team, payload.organization_id),
        "events": await count_rows(db, Event, payload.organization_id),
        "attendance_records": await count_related(db, AttendanceRecord, Event, payload.organization_id, "event_id"),
        "assessments": await count_rows(db, AthleteAssessment, payload.organization_id),
        "observations": await count_rows(db, AthletePerformanceObservation, payload.organization_id),
        "consent_requests": await count_rows(db, ConsentRequest, payload.organization_id),
        "competitions": await count_rows(db, Competition, payload.organization_id),
        "tickets": await count_rows(db, Ticket, payload.organization_id),
        "invoices": await count_rows(db, FinanceInvoice, payload.organization_id),
    }
    summary = f"{definition.name} generated with {metrics['events']} events, {metrics['teams']} teams, and {metrics['memberships']} memberships in scope."
    findings = (
        f"Attendance records: {metrics['attendance_records']}. "
        f"Performance observations: {metrics['observations']}. "
        f"Assessments: {metrics['assessments']}. "
        f"Consent requests: {metrics['consent_requests']}. "
        f"Competitions: {metrics['competitions']}. "
        f"Tickets: {metrics['tickets']}. "
        f"Invoices: {metrics['invoices']}."
    )
    recommendations = (
        "Use this report to schedule follow-up reviews, trigger stakeholder delivery, "
        "and queue AI agents for deeper anomaly detection where counts or risks change."
    )
    return summary, findings, recommendations


async def count_rows(db: AsyncSession, model, organization_id: UUID) -> int:
    return len((await db.scalars(select(model.id).where(model.organization_id == organization_id))).all())


async def count_related(db: AsyncSession, model, related_model, organization_id: UUID, fk_name: str) -> int:
    related_ids = (await db.scalars(select(related_model.id).where(related_model.organization_id == organization_id))).all()
    if not related_ids:
        return 0
    return len((await db.scalars(select(model.id).where(getattr(model, fk_name).in_(related_ids)))).all())


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_definition_for_organization(db: AsyncSession, definition_id: UUID, organization_id: UUID) -> ReportDefinition:
    definition = await db.get(ReportDefinition, definition_id)
    if definition is None or definition.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report definition not found")
    return definition


async def get_report(db: AsyncSession, report_id: UUID) -> GeneratedReport:
    report = await db.get(GeneratedReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


async def get_athlete_for_organization(db: AsyncSession, athlete_profile_id: UUID, organization_id: UUID) -> AthleteProfile:
    athlete = await db.get(AthleteProfile, athlete_profile_id)
    if athlete is None or athlete.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    return athlete


async def validate_scope_refs(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None,
    athlete_profile_id: UUID | None,
    event_id: UUID | None,
    agent_id: UUID | None,
) -> None:
    if team_id is not None:
        team = await db.get(Team, team_id)
        if team is None or team.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if athlete_profile_id is not None:
        await get_athlete_for_organization(db, athlete_profile_id, organization_id)
    if event_id is not None:
        event = await db.get(Event, event_id)
        if event is None or event.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if agent_id is not None:
        agent = await db.get(Agent, agent_id)
        if agent is None or agent.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")


def risk_band(score: int) -> str:
    if score >= 85:
        return "high"
    if score >= 70:
        return "warning"
    if score >= 40:
        return "watch"
    return "normal"


def render_body(report: GeneratedReport, output_format: ReportFormat) -> str:
    fields = [
        ("Title", report.title),
        ("Format", output_format.value),
        ("Summary", report.summary),
        ("Findings", report.findings or ""),
        ("Recommendations", report.recommendations or ""),
        ("Period", f"{report.period_start or 'open'} to {report.period_end or 'open'}"),
        ("Share", report.shared_token or ""),
    ]
    if output_format == ReportFormat.CSV:
        return "\n".join(f"{key},{value}" for key, value in fields)
    if output_format == ReportFormat.API:
        return str({key.lower(): value for key, value in fields})
    return "\n\n".join(f"{key}: {value}" for key, value in fields)


def report_rows(report: GeneratedReport) -> list[tuple[str, str]]:
    return [
        ("Title", report.title),
        ("Format", report.output_format.value),
        ("Summary", report.summary),
        ("Findings", report.findings or ""),
        ("Recommendations", report.recommendations or ""),
        ("Period start", str(report.period_start or "open")),
        ("Period end", str(report.period_end or "open")),
        ("Status", report.status.value),
        ("Share token", report.shared_token or ""),
    ]


def build_report_artifact(report: GeneratedReport, output_format: ReportFormat) -> dict[str, object]:
    text = render_body(report, output_format)
    if output_format == ReportFormat.PDF:
        content = build_pdf_bytes(report)
    elif output_format == ReportFormat.EXCEL:
        content = build_xlsx_bytes(report)
    elif output_format == ReportFormat.CSV:
        content = build_csv_bytes(report)
    elif output_format == ReportFormat.API:
        content = json.dumps(dict(report_rows(report)), indent=2, default=str).encode()
    else:
        content = build_html_bytes(report)
    return {
        "content": content,
        "content_type": report_content_type(output_format),
        "filename": report_filename(report, output_format),
        "checksum": sha256(content).hexdigest(),
        "body_preview": text[:600],
    }


def persist_report_artifact(
    report: GeneratedReport,
    artifact: dict[str, object],
    settings: Settings,
) -> dict[str, str]:
    checksum = str(artifact["checksum"])
    filename = str(artifact["filename"])
    storage_name = f"{checksum[:16]}-{filename}"
    relative_path = (Path(str(report.organization_id)) / str(report.id) / storage_name).as_posix()
    stored = put_object(
        settings,
        local_root=settings.report_artifact_dir,
        local_url_prefix=settings.report_artifact_url_prefix,
        key=relative_path,
        content=bytes(artifact["content"]),
        content_type=str(artifact["content_type"]),
    )
    return {
        "artifact_url": stored.url,
        "storage_path": stored.path,
        "storage_name": storage_name,
    }


def signed_report_artifact_url(
    settings: Settings,
    organization_id: UUID,
    report_id: UUID,
    storage_name: str,
    expires_at: datetime,
) -> str:
    expires = int(expires_at.timestamp())
    signature = report_artifact_signature(settings, organization_id, report_id, storage_name, expires)
    safe_name = quote(storage_name, safe="")
    return (
        f"{settings.api_prefix}/reporting/artifacts/{organization_id}/{report_id}/{safe_name}"
        f"?expires={expires}&signature={signature}"
    )


def report_artifact_signature(
    settings: Settings,
    organization_id: UUID,
    report_id: UUID,
    storage_name: str,
    expires: int,
) -> str:
    payload = f"{organization_id}/{report_id}/{storage_name}:{expires}"
    digest = hmac.new(
        report_artifact_signing_key(settings),
        payload.encode(),
        sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def report_artifact_signing_key(settings: Settings) -> bytes:
    key = settings.report_artifact_signing_key or settings.agent_webhook_key
    return (key or "local-report-artifact-key").encode()


def public_artifact_filename(storage_name: str) -> str:
    parts = storage_name.split("-", 1)
    return parts[1] if len(parts) == 2 else storage_name


def report_content_type_for_filename(filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower()
    return {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "json": "application/json",
        "api": "application/json",
        "html": "text/html",
        "online": "text/html",
    }.get(extension, "application/octet-stream")


def build_csv_bytes(report: GeneratedReport) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["field", "value"])
    writer.writerows(report_rows(report))
    return buffer.getvalue().encode()


def build_html_bytes(report: GeneratedReport) -> bytes:
    rows = "\n".join(
        f"<tr><th>{xml_escape(key)}</th><td>{xml_escape(value)}</td></tr>"
        for key, value in report_rows(report)
    )
    html = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{xml_escape(report.title)}</title></head><body>"
        f"<h1>{xml_escape(report.title)}</h1><table>{rows}</table></body></html>"
    )
    return html.encode()


def build_xlsx_bytes(report: GeneratedReport) -> bytes:
    rows = report_rows(report)
    sheet_rows = "\n".join(
        "<row r=\"{index}\"><c r=\"A{index}\" t=\"inlineStr\"><is><t>{key}</t></is></c>"
        "<c r=\"B{index}\" t=\"inlineStr\"><is><t>{value}</t></is></c></row>".format(
            index=index,
            key=xml_escape(key),
            value=xml_escape(value),
        )
        for index, (key, value) in enumerate(rows, start=1)
    )
    sheet = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        f"<sheetData>{sheet_rows}</sheetData></worksheet>"
    )
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
            "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
            "</Relationships>",
        )
        archive.writestr(
            "xl/workbook.xml",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
            "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
            "<sheets><sheet name=\"Report\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
            "</Relationships>",
        )
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()


def build_pdf_bytes(report: GeneratedReport) -> bytes:
    lines = [report.title, report.summary, report.findings or "", report.recommendations or ""]
    text_commands = ["BT", "/F1 12 Tf", "72 760 Td"]
    for index, line in enumerate(lines):
        if index:
            text_commands.append("0 -18 Td")
        text_commands.append(f"({pdf_escape(line[:110])}) Tj")
    text_commands.append("ET")
    stream = "\n".join(text_commands).encode()
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n",
    ]
    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for item in objects:
        offsets.append(output.tell())
        output.write(item)
    xref_at = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode())
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode())
    output.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    )
    return output.getvalue()


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def report_filename(report: GeneratedReport, output_format: ReportFormat) -> str:
    stem = "".join(character if character.isalnum() else "-" for character in report.title.lower()).strip("-")
    extension = "xlsx" if output_format == ReportFormat.EXCEL else output_format.value
    return f"{stem or 'afrolete-report'}.{extension}"


def report_content_type(output_format: ReportFormat) -> str:
    return {
        ReportFormat.PDF: "application/pdf",
        ReportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ReportFormat.CSV: "text/csv",
        ReportFormat.API: "application/json",
        ReportFormat.ONLINE: "text/html",
    }[output_format]


def benchmark_recommendation(band: str, high_risk_count: int) -> str:
    if band == "high":
        return "Escalate this model cohort for immediate coaching and welfare review."
    if band == "warning" or high_risk_count:
        return "Schedule targeted review for warning cohorts before the next fixture cycle."
    if band == "watch":
        return "Keep the cohort on routine monitoring and compare after the next assessment."
    return "Use this benchmark as the current healthy baseline."
