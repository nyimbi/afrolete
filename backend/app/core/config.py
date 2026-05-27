from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AFROLETE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "local"
    api_prefix: str = "/api/v1"
    auth_mode: Literal["local", "keycloak"] = "local"
    authz_mode: Literal["memory", "spicedb"] = "memory"
    database_url: str = "postgresql+asyncpg:///afrolete"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    keycloak_issuer: AnyHttpUrl = "https://auth.lindela.io/realms/lindela"
    keycloak_audience: str = "afrolete-api"
    keycloak_algorithms: list[str] = Field(default_factory=lambda: ["RS256"])
    keycloak_jwks_ttl_seconds: int = 300
    keycloak_http_timeout_seconds: float = 5.0

    spicedb_endpoint: str = "62.84.181.55:50051"
    spicedb_key: str = ""
    spicedb_insecure: bool = True
    spicedb_request_timeout_seconds: float = 3.0

    communication_delivery_mode: Literal["record_only", "webhook"] = "record_only"
    communication_webhook_url: str = ""
    communication_email_webhook_url: str = ""
    communication_sms_webhook_url: str = ""
    communication_whatsapp_webhook_url: str = ""
    communication_telegram_webhook_url: str = ""
    communication_push_webhook_url: str = ""
    communication_webhook_key: str = ""
    communication_delivery_timeout_seconds: float = 5.0

    agent_execution_mode: Literal["deterministic", "webhook"] = "deterministic"
    agent_webhook_url: str = ""
    agent_webhook_key: str = ""
    agent_default_model: str = "afrolete-local-planner"
    agent_execution_timeout_seconds: float = 10.0

    billing_payment_webhook_signing_key: str = ""
    billing_payment_webhook_tolerance_seconds: int = 300
    billing_dunning_delivery_mode: Literal["record_only", "webhook"] = "record_only"
    billing_dunning_webhook_url: str = ""
    billing_dunning_webhook_key: str = ""
    billing_dunning_timeout_seconds: float = 5.0

    report_artifact_dir: str = "data/report-artifacts"
    report_artifact_url_prefix: str = "local://reports"
    report_artifact_signing_key: str = "local-report-artifact-key"
    report_artifact_url_ttl_seconds: int = 900

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @field_validator("keycloak_algorithms", mode="before")
    @classmethod
    def parse_keycloak_algorithms(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [algorithm.strip() for algorithm in value.split(",") if algorithm.strip()]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
