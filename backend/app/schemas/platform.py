from pydantic import BaseModel


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
