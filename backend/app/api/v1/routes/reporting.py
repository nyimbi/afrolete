from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.reporting import (
    GeneratedReportCreate,
    GeneratedReportRead,
    IntelligenceInsightCreate,
    IntelligenceInsightRead,
    IntelligenceInsightUpdate,
    PredictiveRiskScoreCreate,
    PredictiveRiskScoreRead,
    RenderedReportRead,
    ReportChartRead,
    ReportDefinitionCreate,
    ReportDefinitionRead,
    ReportExportJobCreate,
    ReportExportJobRead,
    ReportVerificationRead,
    ReportingBenchmarkRead,
    ReportingSummaryRead,
    ScheduledReportCreate,
    ScheduledReportRead,
)
from app.models.enums import ReportFormat
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.reporting import (
    create_export_job,
    create_insight,
    create_report_definition,
    create_risk_score,
    create_scheduled_report,
    downloadable_report_artifact,
    generate_live_insight,
    generate_report,
    list_export_jobs,
    list_generated_reports,
    list_insights,
    list_report_definitions,
    list_risk_scores,
    list_scheduled_reports,
    render_report_artifact,
    report_charts,
    reporting_benchmarks,
    reporting_summary,
    update_insight_status,
    verify_report_artifact,
)

router = APIRouter(prefix="/reporting", tags=["reporting"])


def read(model, schema_type):
    return schema_type(**{name: getattr(model, name) for name in schema_type.model_fields})


@router.post("/definitions", response_model=ReportDefinitionRead, status_code=status.HTTP_201_CREATED)
async def create_definition_route(
    payload: ReportDefinitionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ReportDefinitionRead:
    return read(await create_report_definition(db, identity, payload, authz), ReportDefinitionRead)


@router.get("/definitions", response_model=list[ReportDefinitionRead])
async def list_definitions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[ReportDefinitionRead]:
    return [
        read(definition, ReportDefinitionRead)
        for definition in await list_report_definitions(db, organization_id)
    ]


@router.post("/reports", response_model=GeneratedReportRead, status_code=status.HTTP_201_CREATED)
async def generate_report_route(
    payload: GeneratedReportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GeneratedReportRead:
    return read(await generate_report(db, identity, payload, authz), GeneratedReportRead)


@router.get("/reports", response_model=list[GeneratedReportRead])
async def list_reports_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[GeneratedReportRead]:
    return [
        read(report, GeneratedReportRead)
        for report in await list_generated_reports(db, organization_id)
    ]


@router.post("/reports/{report_id}/render", response_model=RenderedReportRead)
async def render_report_route(
    report_id: UUID,
    output_format: ReportFormat | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RenderedReportRead:
    return RenderedReportRead(
        **await render_report_artifact(db, identity, report_id, output_format, authz)
    )


@router.post("/reports/{report_id}/verify", response_model=ReportVerificationRead)
async def verify_report_route(
    report_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ReportVerificationRead:
    return ReportVerificationRead(**await verify_report_artifact(db, identity, report_id, authz))


@router.get("/reports/{report_id}/download")
async def download_report_route(
    report_id: UUID,
    output_format: ReportFormat | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> Response:
    artifact = await downloadable_report_artifact(db, identity, report_id, output_format, authz)
    return Response(
        content=artifact["content"],
        media_type=artifact["content_type"],
        headers={
            "Content-Disposition": f"attachment; filename={artifact['filename']}",
            "X-Afrolete-Report-Checksum": str(artifact["checksum"]),
            "X-Afrolete-Artifact-Url": str(artifact["artifact_url"]),
        },
    )


@router.post("/schedules", response_model=ScheduledReportRead, status_code=status.HTTP_201_CREATED)
async def create_schedule_route(
    payload: ScheduledReportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ScheduledReportRead:
    return read(await create_scheduled_report(db, identity, payload, authz), ScheduledReportRead)


@router.get("/schedules", response_model=list[ScheduledReportRead])
async def list_schedules_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduledReportRead]:
    return [
        read(schedule, ScheduledReportRead)
        for schedule in await list_scheduled_reports(db, organization_id)
    ]


@router.post("/insights", response_model=IntelligenceInsightRead, status_code=status.HTTP_201_CREATED)
async def create_insight_route(
    payload: IntelligenceInsightCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IntelligenceInsightRead:
    return read(await create_insight(db, identity, payload, authz), IntelligenceInsightRead)


@router.get("/insights", response_model=list[IntelligenceInsightRead])
async def list_insights_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[IntelligenceInsightRead]:
    return [read(insight, IntelligenceInsightRead) for insight in await list_insights(db, organization_id)]


@router.post("/insights/generate", response_model=IntelligenceInsightRead, status_code=status.HTTP_201_CREATED)
async def generate_insight_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IntelligenceInsightRead:
    return read(
        await generate_live_insight(db, identity, organization_id, authz),
        IntelligenceInsightRead,
    )


@router.patch("/insights/{insight_id}", response_model=IntelligenceInsightRead)
async def update_insight_route(
    insight_id: UUID,
    payload: IntelligenceInsightUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IntelligenceInsightRead:
    return read(await update_insight_status(db, identity, insight_id, payload, authz), IntelligenceInsightRead)


@router.post("/risk-scores", response_model=PredictiveRiskScoreRead, status_code=status.HTTP_201_CREATED)
async def create_risk_score_route(
    payload: PredictiveRiskScoreCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PredictiveRiskScoreRead:
    return read(await create_risk_score(db, identity, payload, authz), PredictiveRiskScoreRead)


@router.get("/risk-scores", response_model=list[PredictiveRiskScoreRead])
async def list_risk_scores_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[PredictiveRiskScoreRead]:
    return [read(score, PredictiveRiskScoreRead) for score in await list_risk_scores(db, organization_id)]


@router.post("/exports", response_model=ReportExportJobRead, status_code=status.HTTP_201_CREATED)
async def create_export_route(
    payload: ReportExportJobCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ReportExportJobRead:
    return read(await create_export_job(db, identity, payload, authz), ReportExportJobRead)


@router.get("/exports", response_model=list[ReportExportJobRead])
async def list_exports_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[ReportExportJobRead]:
    return [read(export, ReportExportJobRead) for export in await list_export_jobs(db, organization_id)]


@router.get("/charts", response_model=list[ReportChartRead])
async def charts_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[ReportChartRead]:
    return [ReportChartRead(**chart) for chart in await report_charts(db, organization_id)]


@router.get("/benchmarks", response_model=list[ReportingBenchmarkRead])
async def benchmarks_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[ReportingBenchmarkRead]:
    return [
        ReportingBenchmarkRead(**benchmark)
        for benchmark in await reporting_benchmarks(db, organization_id)
    ]


@router.get("/summary", response_model=ReportingSummaryRead)
async def summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> ReportingSummaryRead:
    return ReportingSummaryRead(**await reporting_summary(db, organization_id))
