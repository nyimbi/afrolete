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
