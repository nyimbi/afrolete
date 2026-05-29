from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class Capability(BaseModel):
    key: str
    name: str
    status: str
    description: str


class PlatformSummary(BaseModel):
    product: str
    architecture: str
    capabilities: list[Capability]


class InfrastructureComponent(BaseModel):
    key: str
    name: str
    status: str
    mode: str
    configured: bool
    endpoint: str | None = None
    details: list[str] = Field(default_factory=list)


class InfrastructureStatus(BaseModel):
    environment: str
    components: list[InfrastructureComponent]


class InfrastructureProbeResult(BaseModel):
    key: str
    name: str
    status: str
    reachable: bool | None = None
    latency_ms: int | None = None
    checked_at: str
    details: list[str] = Field(default_factory=list)


class InfrastructureProbeSummary(BaseModel):
    environment: str
    timeout_seconds: float
    results: list[InfrastructureProbeResult]


class AuthEndpointRead(BaseModel):
    key: str
    name: str
    url: str | None = None
    required: bool = True
    configured: bool


class AuthReadiness(BaseModel):
    mode: str
    provider: str
    issuer: str | None = None
    audience: str | None = None
    status: str
    endpoints: list[AuthEndpointRead] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class AuthorizationResourceRead(BaseModel):
    resource_type: str
    relations: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AuthorizationReadiness(BaseModel):
    mode: str
    provider: str
    status: str
    endpoint: str | None = None
    insecure_transport: bool
    schema_hash: str | None = None
    schema_path: str | None = None
    resources: list[AuthorizationResourceRead] = Field(default_factory=list)
    relationship_count: int
    permission_count: int
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class AuthorizationSchemaRead(BaseModel):
    path: str
    sha256: str
    resource_types: list[str] = Field(default_factory=list)
    relation_count: int
    permission_count: int
    content: str
