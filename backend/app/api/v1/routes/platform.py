import asyncio
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
    Capability,
    HealthResponse,
    InfrastructureComponent,
    InfrastructureProbeResult,
    InfrastructureProbeSummary,
    InfrastructureStatus,
    PlatformSummary,
)

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
    return await _http_probe(
        key="keycloak",
        name="Keycloak",
        url=f"{issuer}/.well-known/openid-configuration",
        timeout_seconds=settings.infrastructure_probe_timeout_seconds,
        healthy_statuses={200},
    )


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
