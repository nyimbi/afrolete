import asyncio
import hashlib
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.platform import (
    AuthEndpointRead,
    AuthReadiness,
    AuthorizationReadiness,
    AuthorizationResourceRead,
    AuthorizationSchemaRead,
    Capability,
    HealthResponse,
    InfrastructureComponent,
    InfrastructureProbeResult,
    InfrastructureProbeSummary,
    InfrastructureStatus,
    PlatformSummary,
    SecretReadiness,
    SecretReadinessItem,
)

router = APIRouter()

SPICEDB_SCHEMA_PATH = Path(__file__).resolve().parents[5] / "infra" / "spicedb" / "afrolete.zed"


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok", service="afrolete-api", version="0.1.0")


@router.get("/platform", response_model=PlatformSummary)
async def platform_summary() -> PlatformSummary:
    return PlatformSummary(
        product="AfroLete",
        architecture="FastAPI backend, TypeScript frontend, Keycloak, SpiceDB, Postgres",
        capabilities=[
            Capability(
                key="tenant-operations",
                name="Tenant Operations",
                status="foundation",
                description="Organizations, memberships, teams, athletes, guardians, events.",
            ),
            Capability(
                key="ai-agents",
                name="AI Agents",
                status="foundation",
                description="Agents are modeled as governed actors with assignments and tasks.",
            ),
            Capability(
                key="authz",
                name="Resource Authorization",
                status="foundation",
                description="SpiceDB is the intended authorization system for resources.",
            ),
        ],
    )


@router.get("/infrastructure/auth-readiness", response_model=AuthReadiness)
async def auth_readiness(settings: Settings = Depends(get_settings)) -> AuthReadiness:
    return _auth_readiness(settings)


@router.get("/infrastructure/authorization-readiness", response_model=AuthorizationReadiness)
async def authorization_readiness(settings: Settings = Depends(get_settings)) -> AuthorizationReadiness:
    return _authorization_readiness(settings)


@router.get("/infrastructure/authorization-schema", response_model=AuthorizationSchemaRead)
async def authorization_schema() -> AuthorizationSchemaRead:
    return _authorization_schema()


@router.get("/infrastructure/secrets-readiness", response_model=SecretReadiness)
async def secrets_readiness(settings: Settings = Depends(get_settings)) -> SecretReadiness:
    return _secrets_readiness(settings)


@router.get("/infrastructure", response_model=InfrastructureStatus)
async def infrastructure_status(settings: Settings = Depends(get_settings)) -> InfrastructureStatus:
    return InfrastructureStatus(
        environment=settings.env,
        components=[
            _database_component(settings),
            _keycloak_component(settings),
            _spicedb_component(settings),
            _openbao_component(settings),
            _object_storage_component(settings),
            _redis_component(settings),
            _temporal_component(settings),
        ],
    )


@router.get("/infrastructure/probes", response_model=InfrastructureProbeSummary)
async def infrastructure_probes(
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> InfrastructureProbeSummary:
    results = await asyncio.gather(
        _database_probe(db),
        _keycloak_probe(settings),
        _spicedb_probe(settings),
        _openbao_probe(settings),
        _object_storage_probe(settings),
        _redis_probe(settings),
        _temporal_probe(settings),
    )
    return InfrastructureProbeSummary(
        environment=settings.env,
        timeout_seconds=settings.infrastructure_probe_timeout_seconds,
        results=list(results),
    )


def _database_component(settings: Settings) -> InfrastructureComponent:
    is_postgres = settings.database_url.startswith(("postgresql", "postgres"))
    return InfrastructureComponent(
        key="postgres",
        name="PostgreSQL",
        status="configured" if is_postgres else "misconfigured",
        mode="postgresql" if is_postgres else "unsupported",
        configured=bool(settings.database_url and is_postgres),
        endpoint=_safe_database_endpoint(settings.database_url),
        details=["async SQLAlchemy URL normalized for Postgres"] if is_postgres else ["expected a PostgreSQL URL"],
    )


def _keycloak_component(settings: Settings) -> InfrastructureComponent:
    configured = settings.auth_mode == "keycloak" and bool(settings.keycloak_issuer and settings.keycloak_audience)
    return InfrastructureComponent(
        key="keycloak",
        name="Keycloak",
        status="active" if configured else "standby",
        mode=settings.auth_mode,
        configured=configured,
        endpoint=str(settings.keycloak_issuer),
        details=[f"audience={settings.keycloak_audience}"],
    )


def _authorization_readiness(settings: Settings) -> AuthorizationReadiness:
    resources = _authorization_resources()
    schema = _authorization_schema()
    relationship_count = sum(len(resource.relations) for resource in resources)
    permission_count = sum(len(resource.permissions) for resource in resources)
    if settings.authz_mode != "spicedb":
        return AuthorizationReadiness(
            mode=settings.authz_mode,
            provider="memory",
            status="standby",
            endpoint=None,
            insecure_transport=False,
            schema_hash=schema.sha256,
            schema_path=schema.path,
            resources=resources,
            relationship_count=relationship_count,
            permission_count=permission_count,
            warnings=["Production SaaS mode should use SpiceDB authorization instead of local memory relationships."],
            next_actions=["Set AFROLETE_AUTHZ_MODE=spicedb and provide the OpenBao-managed SpiceDB key."],
        )

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions = [
        "Apply the AfroLete authorization schema to SpiceDB before enabling tenant traffic.",
        "Run a live relationship write/check/delete smoke test with a disposable tenant object.",
        "Verify OpenBao key resolution and key rotation procedure before production rollout.",
    ]
    if not settings.spicedb_endpoint:
        blockers.append("SpiceDB endpoint is not configured.")
    if not settings.spicedb_key:
        blockers.append("SpiceDB API key is not configured.")
    if settings.spicedb_insecure and settings.env not in {"local", "demo", "test"}:
        warnings.append("SpiceDB is configured for insecure transport outside local/demo/test mode.")
    return AuthorizationReadiness(
        mode=settings.authz_mode,
        provider="spicedb",
        status="blocked" if blockers else "ready_with_warnings" if warnings else "ready",
        endpoint=settings.spicedb_endpoint,
        insecure_transport=settings.spicedb_insecure,
        schema_hash=schema.sha256,
        schema_path=schema.path,
        resources=resources,
        relationship_count=relationship_count,
        permission_count=permission_count,
        blockers=blockers,
        warnings=warnings,
        next_actions=next_actions,
    )


def _authorization_schema(path: Path = SPICEDB_SCHEMA_PATH) -> AuthorizationSchemaRead:
    content = path.read_text(encoding="utf-8")
    resource_types = re.findall(r"^definition\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{", content, flags=re.MULTILINE)
    relations = re.findall(r"^\s*relation\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:", content, flags=re.MULTILINE)
    permissions = re.findall(r"^\s*permission\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=", content, flags=re.MULTILINE)
    return AuthorizationSchemaRead(
        path=str(path.relative_to(Path(__file__).resolve().parents[5])),
        sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        resource_types=resource_types,
        relation_count=len(relations),
        permission_count=len(permissions),
        content=content,
    )


def _authorization_resources() -> list[AuthorizationResourceRead]:
    return [
        AuthorizationResourceRead(
            resource_type="organization",
            relations=[
                "owner",
                "admin",
                "coach",
                "assistant_coach",
                "staff",
                "manager",
                "captain",
                "guardian",
                "athlete",
                "member_team",
                "assigned_agent",
            ],
            permissions=["manage", "manage_roster", "view", "analyze"],
            notes=["Tenant root for clubs, schools, academies, associations, and federations."],
        ),
        AuthorizationResourceRead(
            resource_type="team",
            relations=[
                "parent_org",
                "owner",
                "coach",
                "assistant_coach",
                "captain",
                "vice_captain",
                "player",
                "guardian",
                "assigned_agent",
            ],
            permissions=["manage", "manage_roster", "view", "analyze"],
            notes=["Roster, guardian, player, and staff access rolls up to tenant organizations."],
        ),
        AuthorizationResourceRead(
            resource_type="event",
            relations=["parent_org", "team", "organizer", "participant", "guardian", "assigned_agent"],
            permissions=["manage", "manage_roster", "view", "analyze"],
            notes=["Scheduling, attendance, travel, and consent checks depend on event scope relations."],
        ),
        AuthorizationResourceRead(
            resource_type="athlete_profile",
            relations=["parent_org", "team", "athlete", "guardian", "coach", "medical_viewer", "assigned_agent"],
            permissions=["manage", "manage_roster", "view", "view_medical", "analyze"],
            notes=["Performance, medical visibility, guardian access, and AI coaching use profile scope."],
        ),
        AuthorizationResourceRead(
            resource_type="safeguarding_incident",
            relations=[
                "parent_org",
                "event",
                "team",
                "reporter",
                "case_manager",
                "assigned_to",
                "athlete",
                "guardian",
                "medical_viewer",
                "evidence_reviewer",
                "regulator",
                "assigned_agent",
            ],
            permissions=["manage", "view", "view_medical", "review_evidence", "analyze"],
            notes=["Incident access grants and evidence review use this dedicated case resource."],
        ),
        AuthorizationResourceRead(
            resource_type="agent",
            relations=["owner", "assigned_to", "reviewer"],
            permissions=["manage", "view", "analyze"],
            notes=["AI agents are first-class subjects and resources with human review boundaries."],
        ),
        AuthorizationResourceRead(
            resource_type="developer_application",
            relations=["owner", "operator", "reviewer"],
            permissions=["manage", "view"],
            notes=["Developer platform ownership and OAuth consent administration."],
        ),
    ]


def _secrets_readiness(settings: Settings) -> SecretReadiness:
    specs = _secret_specs(settings)
    any_vault_path = any(_setting(settings, spec.get("path_attr")) for spec in specs)
    items = [_secret_item(settings, spec, any_vault_path) for spec in specs]
    configured_count = sum(1 for item in items if item.status in {"vault_path", "inline", "local_default", "runtime_token"})
    vault_path_count = sum(1 for item in items if item.status == "vault_path")
    inline_count = sum(1 for item in items if item.status in {"inline", "runtime_token"})
    local_default_count = sum(1 for item in items if item.status == "local_default")
    missing_required = [item for item in items if item.status == "missing" and item.required]
    production_like = settings.env not in {"local", "demo", "test"}

    blockers: list[str] = []
    warnings: list[str] = []
    if missing_required:
        blockers.append(f"{len(missing_required)} required secret class(es) are missing.")
    if any_vault_path and not settings.openbao_token:
        blockers.append("OpenBao token is required to resolve configured secret paths.")
    if production_like and not settings.openbao_token:
        blockers.append("OpenBao token is not configured for production secret custody.")
    if production_like and local_default_count:
        blockers.append(f"{local_default_count} local development signing key(s) remain in production-like mode.")
    if inline_count:
        warnings.append(f"{inline_count} secret class(es) are configured inline; prefer OpenBao secret paths.")
    if settings.env in {"local", "demo", "test"} and local_default_count:
        warnings.append(f"{local_default_count} local default signing key(s) are acceptable only for local/demo/test.")
    if not vault_path_count:
        warnings.append("No secret classes are configured through OpenBao paths yet.")

    next_actions = [
        "Move integration, signing, and storage credentials to OpenBao KV paths.",
        "Inject only the OpenBao runtime token through the deployment secret mechanism.",
        "Run a live OpenBao resolution smoke test before enabling production traffic.",
    ]
    return SecretReadiness(
        environment=settings.env,
        provider="openbao" if settings.openbao_addr else "environment",
        status="blocked" if blockers else "ready_with_warnings" if warnings else "ready",
        configured_count=configured_count,
        vault_path_count=vault_path_count,
        inline_count=inline_count,
        missing_required_count=len(missing_required),
        local_default_count=local_default_count,
        items=items,
        blockers=blockers,
        warnings=warnings,
        next_actions=next_actions,
    )


def _secret_item(settings: Settings, spec: dict[str, object], any_vault_path: bool) -> SecretReadinessItem:
    path_attr = str(spec.get("path_attr") or "")
    inline_attr = str(spec.get("inline_attr") or "")
    secret_path_configured = bool(_setting(settings, path_attr))
    inline_value = _setting(settings, inline_attr)
    inline_configured = bool(inline_value)
    required = bool(spec.get("required"))
    local_defaults = {str(value) for value in spec.get("local_defaults", ())}
    details = [str(detail) for detail in spec.get("details", ())]

    if spec["key"] == "openbao-runtime-token":
        required = required or any_vault_path or settings.env not in {"local", "demo", "test"}
        if inline_configured:
            status = "runtime_token"
            details.append("runtime vault token configured")
        elif required:
            status = "missing"
            details.append("required to resolve configured vault paths")
        else:
            status = "not_required"
            details.append("not required in local/demo/test without vault paths")
    elif secret_path_configured:
        status = "vault_path"
        details.append("OpenBao path configured")
    elif inline_configured and inline_value in local_defaults:
        status = "local_default"
        details.append("local development default configured")
    elif inline_configured:
        status = "inline"
        details.append("inline value configured")
    elif required:
        status = "missing"
        details.append("required by active runtime mode")
    else:
        status = "not_required"
        details.append("not required by current runtime mode")

    return SecretReadinessItem(
        key=str(spec["key"]),
        name=str(spec["name"]),
        domain=str(spec["domain"]),
        status=status,
        required=required,
        secret_path_configured=secret_path_configured,
        inline_configured=inline_configured,
        details=details,
    )


def _secret_specs(settings: Settings) -> list[dict[str, object]]:
    webhook = "required for webhook mode"
    signing = "required for signed artifact URLs or callback verification"
    return [
        {
            "key": "openbao-runtime-token",
            "name": "OpenBao runtime token",
            "domain": "secret-vault",
            "inline_attr": "openbao_token",
            "required": settings.env not in {"local", "demo", "test"},
            "details": ["deployment-scoped vault access token"],
        },
        {
            "key": "spicedb-api-key",
            "name": "SpiceDB API key",
            "domain": "authorization",
            "inline_attr": "spicedb_key",
            "required": settings.authz_mode == "spicedb",
            "details": ["required when SpiceDB authorization mode is active"],
        },
        {
            "key": "communication-delivery",
            "name": "Communication delivery webhook key",
            "domain": "communications",
            "inline_attr": "communication_webhook_key",
            "path_attr": "communication_webhook_key_secret_path",
            "required": settings.communication_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "agent-execution",
            "name": "AI agent execution webhook key",
            "domain": "ai-agents",
            "inline_attr": "agent_webhook_key",
            "path_attr": "agent_webhook_key_secret_path",
            "required": settings.agent_execution_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "training-plan-generation",
            "name": "Training plan generation webhook key",
            "domain": "training",
            "inline_attr": "training_plan_generation_webhook_key",
            "path_attr": "training_plan_generation_webhook_key_secret_path",
            "required": settings.training_plan_generation_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "report-artifact-signing",
            "name": "Report artifact signing key",
            "domain": "reporting",
            "inline_attr": "report_artifact_signing_key",
            "path_attr": "report_artifact_signing_key_secret_path",
            "required": True,
            "local_defaults": ("local-report-artifact-key",),
            "details": [signing],
        },
        {
            "key": "reporting-insight-generation",
            "name": "Reporting insight generation webhook key",
            "domain": "reporting",
            "inline_attr": "reporting_insight_generation_webhook_key",
            "path_attr": "reporting_insight_generation_webhook_key_secret_path",
            "required": settings.reporting_insight_generation_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "billing-payment-webhook-signing",
            "name": "Billing payment webhook signing key",
            "domain": "billing",
            "inline_attr": "billing_payment_webhook_signing_key",
            "path_attr": "billing_payment_webhook_signing_key_secret_path",
            "required": False,
            "details": ["required when billing payment callbacks are enabled"],
        },
        {
            "key": "billing-payment-retry",
            "name": "Billing payment retry webhook key",
            "domain": "billing",
            "inline_attr": "billing_payment_retry_webhook_key",
            "path_attr": "billing_payment_retry_webhook_key_secret_path",
            "required": settings.billing_payment_retry_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "billing-dunning",
            "name": "Billing dunning webhook key",
            "domain": "billing",
            "inline_attr": "billing_dunning_webhook_key",
            "path_attr": "billing_dunning_webhook_key_secret_path",
            "required": settings.billing_dunning_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "billing-tax-filing",
            "name": "Billing tax filing webhook key",
            "domain": "billing",
            "inline_attr": "billing_tax_filing_webhook_key",
            "path_attr": "billing_tax_filing_webhook_key_secret_path",
            "required": settings.billing_tax_filing_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "commercial-payment-webhook-signing",
            "name": "Commercial payment webhook signing key",
            "domain": "commerce",
            "inline_attr": "commercial_payment_webhook_signing_key",
            "path_attr": "commercial_payment_webhook_signing_key_secret_path",
            "required": False,
            "details": ["required when commercial payment callbacks are enabled"],
        },
        {
            "key": "commercial-payment-session",
            "name": "Commercial payment session webhook key",
            "domain": "commerce",
            "inline_attr": "commercial_payment_session_webhook_key",
            "path_attr": "commercial_payment_session_webhook_key_secret_path",
            "required": settings.commercial_payment_session_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "commercial-accounting",
            "name": "Commercial accounting webhook key",
            "domain": "commerce",
            "inline_attr": "commercial_accounting_webhook_key",
            "path_attr": "commercial_accounting_webhook_key_secret_path",
            "required": settings.commercial_accounting_sync_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "commercial-tax-filing",
            "name": "Commercial tax filing webhook key",
            "domain": "commerce",
            "inline_attr": "commercial_tax_filing_webhook_key",
            "path_attr": "commercial_tax_filing_webhook_key_secret_path",
            "required": settings.commercial_tax_filing_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "commercial-payout",
            "name": "Commercial payout webhook key",
            "domain": "commerce",
            "inline_attr": "commercial_payout_webhook_key",
            "path_attr": "commercial_payout_webhook_key_secret_path",
            "required": settings.commercial_payout_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "commercial-payout-callback-signing",
            "name": "Commercial payout callback signing key",
            "domain": "commerce",
            "inline_attr": "commercial_payout_callback_signing_key",
            "path_attr": "commercial_payout_callback_signing_key_secret_path",
            "required": False,
            "details": ["required when payout callbacks are enabled"],
        },
        {
            "key": "travel-manifest-signing",
            "name": "Travel manifest signing key",
            "domain": "travel",
            "inline_attr": "travel_manifest_signing_key",
            "path_attr": "travel_manifest_signing_key_secret_path",
            "required": True,
            "local_defaults": ("local-travel-manifest-key",),
            "details": [signing],
        },
        {
            "key": "travel-fee-payment-webhook-signing",
            "name": "Travel fee payment webhook signing key",
            "domain": "travel",
            "inline_attr": "travel_fee_payment_webhook_signing_key",
            "path_attr": "travel_fee_payment_webhook_signing_key_secret_path",
            "required": False,
            "details": ["required when travel fee callbacks are enabled"],
        },
        {
            "key": "travel-expense-payout-callback-signing",
            "name": "Travel expense payout callback signing key",
            "domain": "travel",
            "inline_attr": "travel_expense_payout_callback_signing_key",
            "path_attr": "travel_expense_payout_callback_signing_key_secret_path",
            "required": False,
            "details": ["required when travel payout callbacks are enabled"],
        },
        {
            "key": "travel-device-ingest",
            "name": "Travel device ingest key",
            "domain": "travel",
            "inline_attr": "travel_device_ingest_key",
            "path_attr": "travel_device_ingest_key_secret_path",
            "required": False,
            "details": ["required when travel device ingest is exposed"],
        },
        {
            "key": "safeguarding-screening-webhook-signing",
            "name": "Safeguarding screening webhook signing key",
            "domain": "safeguarding",
            "inline_attr": "safeguarding_screening_webhook_signing_key",
            "path_attr": "safeguarding_screening_webhook_signing_key_secret_path",
            "required": False,
            "details": ["required when background-screening callbacks are enabled"],
        },
        {
            "key": "safeguarding-screening-submission",
            "name": "Safeguarding screening submission webhook key",
            "domain": "safeguarding",
            "inline_attr": "safeguarding_screening_submission_webhook_key",
            "path_attr": "safeguarding_screening_submission_webhook_key_secret_path",
            "required": settings.safeguarding_screening_submission_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "safeguarding-incident-evidence-signing",
            "name": "Safeguarding incident evidence signing key",
            "domain": "safeguarding",
            "inline_attr": "safeguarding_incident_evidence_signing_key",
            "path_attr": "safeguarding_incident_evidence_signing_key_secret_path",
            "required": True,
            "local_defaults": ("local-safeguarding-evidence-key",),
            "details": [signing],
        },
        {
            "key": "safeguarding-regulatory-report",
            "name": "Safeguarding regulatory report webhook key",
            "domain": "safeguarding",
            "inline_attr": "safeguarding_regulatory_report_webhook_key",
            "path_attr": "safeguarding_regulatory_report_webhook_key_secret_path",
            "required": settings.safeguarding_regulatory_report_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "safeguarding-insurance-claim",
            "name": "Safeguarding insurance claim webhook key",
            "domain": "safeguarding",
            "inline_attr": "safeguarding_insurance_claim_webhook_key",
            "path_attr": "safeguarding_insurance_claim_webhook_key_secret_path",
            "required": settings.safeguarding_insurance_claim_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "safeguarding-medical-clearance",
            "name": "Safeguarding medical clearance webhook key",
            "domain": "safeguarding",
            "inline_attr": "safeguarding_medical_clearance_webhook_key",
            "path_attr": "safeguarding_medical_clearance_webhook_key_secret_path",
            "required": settings.safeguarding_medical_clearance_delivery_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "safeguarding-incident-artifact-signing",
            "name": "Safeguarding incident artifact signing key",
            "domain": "safeguarding",
            "inline_attr": "safeguarding_incident_artifact_signing_key",
            "path_attr": "safeguarding_incident_artifact_signing_key_secret_path",
            "required": True,
            "local_defaults": ("local-safeguarding-artifact-key",),
            "details": [signing],
        },
        {
            "key": "performance-wearable-webhook-signing",
            "name": "Performance wearable webhook signing key",
            "domain": "performance",
            "inline_attr": "performance_wearable_webhook_signing_key",
            "path_attr": "performance_wearable_webhook_signing_key_secret_path",
            "required": False,
            "details": ["required when wearable webhook ingestion is exposed"],
        },
        {
            "key": "performance-match-tracking-webhook-signing",
            "name": "Performance match tracking provider webhook signing key",
            "domain": "performance",
            "inline_attr": "performance_match_tracking_webhook_signing_key",
            "path_attr": "performance_match_tracking_webhook_signing_key_secret_path",
            "required": False,
            "details": ["required when external camera or match tracking provider callbacks are exposed"],
        },
        {
            "key": "performance-model-extraction",
            "name": "Performance model extraction webhook key",
            "domain": "performance",
            "inline_attr": "performance_model_extraction_webhook_key",
            "path_attr": "performance_model_extraction_webhook_key_secret_path",
            "required": settings.performance_model_extraction_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "performance-forecast",
            "name": "Performance forecast webhook key",
            "domain": "performance",
            "inline_attr": "performance_forecast_webhook_key",
            "path_attr": "performance_forecast_webhook_key_secret_path",
            "required": settings.performance_forecast_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "performance-pose-worker-bearer",
            "name": "Performance pose worker bearer token",
            "domain": "performance",
            "inline_attr": "performance_pose_worker_bearer_token",
            "required": bool(settings.performance_pose_worker_api_base_url and settings.auth_mode == "keycloak"),
            "details": ["required when the pose worker posts to a Keycloak-protected API"],
        },
        {
            "key": "object-storage-access-key",
            "name": "Object storage access credential",
            "domain": "object-storage",
            "inline_attr": "object_storage_access_key",
            "path_attr": "object_storage_access_key_secret_path",
            "required": settings.object_storage_mode == "s3",
            "details": ["required when object storage mode is s3"],
        },
        {
            "key": "object-storage-secret-key",
            "name": "Object storage secret credential",
            "domain": "object-storage",
            "inline_attr": "object_storage_secret_key",
            "path_attr": "object_storage_secret_key_secret_path",
            "required": settings.object_storage_mode == "s3",
            "details": ["required when object storage mode is s3"],
        },
        {
            "key": "supplier-order-submission",
            "name": "Supplier order submission webhook key",
            "domain": "assets",
            "inline_attr": "supplier_order_webhook_key",
            "path_attr": "supplier_order_webhook_key_secret_path",
            "required": settings.supplier_order_submission_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "supplier-invoice-sync",
            "name": "Supplier invoice sync webhook key",
            "domain": "assets",
            "inline_attr": "supplier_invoice_webhook_key",
            "path_attr": "supplier_invoice_webhook_key_secret_path",
            "required": settings.supplier_invoice_sync_mode == "webhook",
            "details": [webhook],
        },
        {
            "key": "asset-accounting-sync",
            "name": "Asset accounting sync webhook key",
            "domain": "assets",
            "inline_attr": "asset_accounting_webhook_key",
            "path_attr": "asset_accounting_webhook_key_secret_path",
            "required": settings.asset_accounting_sync_mode == "webhook",
            "details": [webhook],
        },
    ]


def _setting(settings: Settings, attr: object) -> str:
    if not attr:
        return ""
    return str(getattr(settings, str(attr), "") or "")


def _auth_readiness(settings: Settings) -> AuthReadiness:
    if settings.auth_mode != "keycloak":
        return AuthReadiness(
            mode=settings.auth_mode,
            provider="local",
            status="standby",
            warnings=["Production SaaS mode should use Keycloak bearer-token authentication."],
            next_actions=["Set AFROLETE_AUTH_MODE=keycloak before deployed tenant onboarding."],
        )

    issuer = str(settings.keycloak_issuer).rstrip("/") if settings.keycloak_issuer else ""
    endpoints = _keycloak_expected_endpoints(issuer)
    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []
    if not issuer:
        blockers.append("Keycloak issuer is not configured.")
    if not settings.keycloak_audience:
        blockers.append("Keycloak API audience is not configured.")
    if not settings.keycloak_algorithms:
        blockers.append("No Keycloak token signing algorithms are allowed.")
    if issuer and not issuer.startswith("https://") and settings.env not in {"local", "demo", "test"}:
        warnings.append("Issuer is not HTTPS outside local/demo/test mode.")
    warnings.append("Realm self-registration must be enabled in Keycloak for the account creation entrypoint.")
    next_actions.extend(
        [
            "Allow the frontend origin as a valid redirect URI for the Keycloak web client.",
            "Enable realm self-registration or route account creation through an approved identity workflow.",
            "Smoke test account creation, callback, token audience, and API bearer authorization together.",
        ]
    )
    return AuthReadiness(
        mode=settings.auth_mode,
        provider="keycloak",
        issuer=issuer or None,
        audience=settings.keycloak_audience or None,
        status="blocked" if blockers else "ready_with_warnings" if warnings else "ready",
        endpoints=endpoints,
        blockers=blockers,
        warnings=warnings,
        next_actions=next_actions,
    )


def _keycloak_expected_endpoints(issuer: str) -> list[AuthEndpointRead]:
    if not issuer:
        return []
    base = issuer.rstrip("/")
    return [
        AuthEndpointRead(
            key="openid-configuration",
            name="OIDC discovery",
            url=f"{base}/.well-known/openid-configuration",
            configured=True,
        ),
        AuthEndpointRead(
            key="authorization",
            name="Authorization",
            url=f"{base}/protocol/openid-connect/auth",
            configured=True,
        ),
        AuthEndpointRead(
            key="registration",
            name="Account creation",
            url=f"{base}/protocol/openid-connect/registrations",
            configured=True,
        ),
        AuthEndpointRead(
            key="token",
            name="Token exchange",
            url=f"{base}/protocol/openid-connect/token",
            configured=True,
        ),
        AuthEndpointRead(
            key="jwks",
            name="Signing keys",
            url=f"{base}/protocol/openid-connect/certs",
            configured=True,
        ),
        AuthEndpointRead(
            key="logout",
            name="Logout",
            url=f"{base}/protocol/openid-connect/logout",
            required=False,
            configured=True,
        ),
        AuthEndpointRead(
            key="userinfo",
            name="UserInfo",
            url=f"{base}/protocol/openid-connect/userinfo",
            required=False,
            configured=True,
        ),
    ]


def _spicedb_component(settings: Settings) -> InfrastructureComponent:
    configured = settings.authz_mode == "spicedb" and bool(settings.spicedb_endpoint and settings.spicedb_key)
    details = ["insecure transport enabled"] if settings.spicedb_insecure else ["TLS transport expected"]
    if settings.authz_mode == "spicedb" and not settings.spicedb_key:
        details.append("API key missing")
    return InfrastructureComponent(
        key="spicedb",
        name="SpiceDB",
        status="active" if configured else "standby",
        mode=settings.authz_mode,
        configured=configured,
        endpoint=settings.spicedb_endpoint,
        details=details,
    )


def _openbao_component(settings: Settings) -> InfrastructureComponent:
    if settings.env == "demo" and not settings.openbao_token:
        return InfrastructureComponent(
            key="openbao",
            name="OpenBao",
            status="standby",
            mode="demo",
            configured=False,
            endpoint=settings.openbao_addr,
            details=["demo mode uses environment/local defaults without a vault token"],
        )
    configured = bool(settings.openbao_addr and settings.openbao_token)
    details = ["namespace configured"] if settings.openbao_namespace else ["root namespace"]
    if settings.openbao_addr and not settings.openbao_token:
        details.append("token missing")
    return InfrastructureComponent(
        key="openbao",
        name="OpenBao",
        status="configured" if configured else "missing-token",
        mode="kv",
        configured=configured,
        endpoint=settings.openbao_addr,
        details=details,
    )


def _object_storage_component(settings: Settings) -> InfrastructureComponent:
    if settings.object_storage_mode == "local":
        return InfrastructureComponent(
            key="object-storage",
            name="Object Storage",
            status="local",
            mode="local",
            configured=True,
            endpoint=settings.report_artifact_dir,
            details=[
                "local filesystem artifact mode",
                f"lifecycle_retention_days={settings.object_storage_lifecycle_retention_days}",
            ],
        )
    has_credentials = bool(
        settings.object_storage_access_key
        or settings.object_storage_access_key_secret_path
        or settings.object_storage_secret_key
        or settings.object_storage_secret_key_secret_path
    )
    configured = bool(settings.object_storage_endpoint and settings.object_storage_bucket and has_credentials)
    return InfrastructureComponent(
        key="object-storage",
        name="Object Storage",
        status="configured" if configured else "missing-credentials",
        mode=settings.object_storage_mode,
        configured=configured,
        endpoint=settings.object_storage_endpoint,
        details=[
            f"bucket={settings.object_storage_bucket}",
            f"region={settings.object_storage_region}",
            f"lifecycle_retention_days={settings.object_storage_lifecycle_retention_days}",
            f"lifecycle_prefixes={len(settings.object_storage_lifecycle_prefixes)}",
        ],
    )


def _redis_component(settings: Settings) -> InfrastructureComponent:
    if settings.env == "demo":
        return InfrastructureComponent(
            key="redis",
            name="Redis",
            status="standby",
            mode="demo",
            configured=False,
            endpoint=_safe_url_without_credentials(settings.redis_url),
            details=["not required for the local Docker demo"],
        )
    return InfrastructureComponent(
        key="redis",
        name="Redis",
        status="configured" if settings.redis_url else "missing-url",
        mode="cache",
        configured=bool(settings.redis_url),
        endpoint=_safe_url_without_credentials(settings.redis_url),
        details=["cache and short-lived coordination backend"],
    )


def _temporal_component(settings: Settings) -> InfrastructureComponent:
    if settings.env == "demo":
        return InfrastructureComponent(
            key="temporal",
            name="Temporal",
            status="standby",
            mode="demo",
            configured=False,
            endpoint=settings.temporal_address,
            details=["not required for the local Docker demo"],
        )
    return InfrastructureComponent(
        key="temporal",
        name="Temporal",
        status="configured" if settings.temporal_address and settings.temporal_namespace else "missing-config",
        mode="workflow",
        configured=bool(settings.temporal_address and settings.temporal_namespace),
        endpoint=settings.temporal_address,
        details=[f"namespace={settings.temporal_namespace}"],
    )


def _safe_database_endpoint(database_url: str) -> str:
    parsed = urlparse(database_url)
    database = parsed.path.lstrip("/") or "default"
    host = parsed.hostname or "local"
    return f"{parsed.scheme}://{host}/{database}"


def _safe_url_without_credentials(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.scheme:
        return value
    host = parsed.hostname or "local"
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or ""
    return f"{parsed.scheme}://{host}{port}{path}"


async def _database_probe(db: AsyncSession) -> InfrastructureProbeResult:
    started = time.perf_counter()
    checked_at = _checked_at()
    try:
        await db.execute(text("select 1"))
    except Exception as exc:
        return _probe_result(
            "postgres",
            "PostgreSQL",
            "unreachable",
            False,
            started,
            checked_at,
            [type(exc).__name__],
        )
    return _probe_result("postgres", "PostgreSQL", "healthy", True, started, checked_at, ["select 1 succeeded"])


async def _keycloak_probe(settings: Settings) -> InfrastructureProbeResult:
    if settings.auth_mode != "keycloak":
        return _skipped_probe("keycloak", "Keycloak", "auth mode is local")
    issuer = str(settings.keycloak_issuer).rstrip("/")
    started = time.perf_counter()
    checked_at = _checked_at()
    url = f"{issuer}/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=settings.infrastructure_probe_timeout_seconds, follow_redirects=False) as client:
            response = await client.get(url)
            response.raise_for_status()
            discovery = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return _probe_result("keycloak", "Keycloak", "unreachable", False, started, checked_at, [type(exc).__name__])
    required = {
        "authorization_endpoint",
        "token_endpoint",
        "jwks_uri",
        "issuer",
    }
    missing = sorted(key for key in required if not discovery.get(key))
    issuer_mismatch = discovery.get("issuer") != issuer
    details = _keycloak_discovery_details(discovery, issuer)
    if missing or issuer_mismatch:
        problems = [f"missing: {', '.join(missing)}"] if missing else []
        if issuer_mismatch:
            problems.append("issuer mismatch")
        return _probe_result(
            "keycloak",
            "Keycloak",
            "unhealthy",
            False,
            started,
            checked_at,
            [*problems, *details],
        )
    return _probe_result("keycloak", "Keycloak", "healthy", True, started, checked_at, details)


def _keycloak_discovery_details(discovery: dict[str, object], expected_issuer: str) -> list[str]:
    details: list[str] = []
    issuer = discovery.get("issuer")
    details.append("issuer matched" if issuer == expected_issuer else "issuer mismatch")
    for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        details.append(f"{key} {'discovered' if discovery.get(key) else 'missing'}")
    details.append("registration endpoint derived")
    return details


async def _spicedb_probe(settings: Settings) -> InfrastructureProbeResult:
    if settings.authz_mode != "spicedb":
        return _skipped_probe("spicedb", "SpiceDB", "authorization mode is memory")
    if not settings.spicedb_key:
        return _skipped_probe("spicedb", "SpiceDB", "API key missing")
    return await _tcp_probe(
        key="spicedb",
        name="SpiceDB",
        endpoint=settings.spicedb_endpoint,
        default_port=50051,
        timeout_seconds=settings.infrastructure_probe_timeout_seconds,
    )


async def _openbao_probe(settings: Settings) -> InfrastructureProbeResult:
    if settings.env == "demo" and not settings.openbao_token:
        return _skipped_probe("openbao", "OpenBao", "demo mode does not require a vault token")
    if not settings.openbao_addr:
        return _skipped_probe("openbao", "OpenBao", "address missing")
    return await _http_probe(
        key="openbao",
        name="OpenBao",
        url=f"{settings.openbao_addr.rstrip('/')}/v1/sys/health",
        timeout_seconds=settings.infrastructure_probe_timeout_seconds,
        healthy_statuses={200, 429, 472, 473},
    )


async def _object_storage_probe(settings: Settings) -> InfrastructureProbeResult:
    if settings.object_storage_mode == "local":
        started = time.perf_counter()
        checked_at = _checked_at()
        path = Path(settings.report_artifact_dir)
        reachable = path.exists() and path.is_dir()
        return _probe_result(
            "object-storage",
            "Object Storage",
            "healthy" if reachable else "unreachable",
            reachable,
            started,
            checked_at,
            [f"local path {'exists' if reachable else 'missing'}"],
        )
    if not settings.object_storage_endpoint:
        return _skipped_probe("object-storage", "Object Storage", "endpoint missing")
    parsed = urlparse(settings.object_storage_endpoint)
    if parsed.scheme in {"http", "https"}:
        return await _http_probe(
            key="object-storage",
            name="Object Storage",
            url=settings.object_storage_endpoint,
            timeout_seconds=settings.infrastructure_probe_timeout_seconds,
            healthy_statuses={200, 301, 302, 307, 308, 403},
        )
    return await _tcp_probe(
        key="object-storage",
        name="Object Storage",
        endpoint=settings.object_storage_endpoint,
        default_port=9000,
        timeout_seconds=settings.infrastructure_probe_timeout_seconds,
    )


async def _redis_probe(settings: Settings) -> InfrastructureProbeResult:
    if settings.env == "demo":
        return _skipped_probe("redis", "Redis", "not required for the local Docker demo")
    if not settings.redis_url:
        return _skipped_probe("redis", "Redis", "URL missing")
    parsed = urlparse(settings.redis_url)
    endpoint = f"{parsed.hostname or '127.0.0.1'}:{parsed.port or 6379}"
    return await _tcp_probe(
        key="redis",
        name="Redis",
        endpoint=endpoint,
        default_port=6379,
        timeout_seconds=settings.infrastructure_probe_timeout_seconds,
    )


async def _temporal_probe(settings: Settings) -> InfrastructureProbeResult:
    if settings.env == "demo":
        return _skipped_probe("temporal", "Temporal", "not required for the local Docker demo")
    if not settings.temporal_address:
        return _skipped_probe("temporal", "Temporal", "address missing")
    return await _tcp_probe(
        key="temporal",
        name="Temporal",
        endpoint=settings.temporal_address,
        default_port=7233,
        timeout_seconds=settings.infrastructure_probe_timeout_seconds,
    )


async def _http_probe(
    *,
    key: str,
    name: str,
    url: str,
    timeout_seconds: float,
    healthy_statuses: set[int],
) -> InfrastructureProbeResult:
    started = time.perf_counter()
    checked_at = _checked_at()
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        return _probe_result(key, name, "unreachable", False, started, checked_at, [type(exc).__name__])
    healthy = response.status_code in healthy_statuses
    return _probe_result(
        key,
        name,
        "healthy" if healthy else "unhealthy",
        healthy,
        started,
        checked_at,
        [f"HTTP {response.status_code}"],
    )


async def _tcp_probe(
    *,
    key: str,
    name: str,
    endpoint: str,
    default_port: int,
    timeout_seconds: float,
) -> InfrastructureProbeResult:
    started = time.perf_counter()
    checked_at = _checked_at()
    host, port = _parse_host_port(endpoint, default_port)
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout_seconds)
        writer.close()
        await writer.wait_closed()
        del reader
    except (OSError, TimeoutError, ValueError) as exc:
        return _probe_result(key, name, "unreachable", False, started, checked_at, [type(exc).__name__])
    return _probe_result(key, name, "reachable", True, started, checked_at, [f"TCP {host}:{port}"])


def _parse_host_port(endpoint: str, default_port: int) -> tuple[str, int]:
    parsed = urlparse(endpoint if "://" in endpoint else f"tcp://{endpoint}")
    host = parsed.hostname or endpoint.rsplit(":", 1)[0]
    return host, parsed.port or default_port


def _probe_result(
    key: str,
    name: str,
    status: str,
    reachable: bool,
    started: float,
    checked_at: str,
    details: list[str],
) -> InfrastructureProbeResult:
    return InfrastructureProbeResult(
        key=key,
        name=name,
        status=status,
        reachable=reachable,
        latency_ms=max(0, round((time.perf_counter() - started) * 1000)),
        checked_at=checked_at,
        details=details,
    )


def _skipped_probe(key: str, name: str, reason: str) -> InfrastructureProbeResult:
    return InfrastructureProbeResult(
        key=key,
        name=name,
        status="skipped",
        reachable=None,
        checked_at=_checked_at(),
        details=[reason],
    )


def _checked_at() -> str:
    return datetime.now(UTC).isoformat()
