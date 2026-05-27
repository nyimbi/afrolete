from urllib.parse import urlparse

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.platform import Capability, HealthResponse, InfrastructureComponent, InfrastructureStatus, PlatformSummary

router = APIRouter()


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
            details=["local filesystem artifact mode"],
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
        details=[f"bucket={settings.object_storage_bucket}", f"region={settings.object_storage_region}"],
    )


def _redis_component(settings: Settings) -> InfrastructureComponent:
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
