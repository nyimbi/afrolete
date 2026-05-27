from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.commercial import FinanceInvoice, Ticket
from app.models.competition import Competition
from app.models.enums import InsightSeverity, InsightStatus, ReportRunStatus
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
