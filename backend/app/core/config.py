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
    communication_webhook_key_secret_path: str = ""
    communication_webhook_key_secret_field: str = "value"
    communication_delivery_timeout_seconds: float = 5.0

    agent_execution_mode: Literal["deterministic", "webhook"] = "deterministic"
    agent_webhook_url: str = ""
    agent_webhook_key: str = ""
    agent_webhook_key_secret_path: str = ""
    agent_webhook_key_secret_field: str = "value"
    agent_default_model: str = "afrolete-local-planner"
    agent_execution_timeout_seconds: float = 10.0
    agent_webhook_tolerance_seconds: int = 300

    openbao_addr: str = "https://vault.lindela.io"
    openbao_token: str = ""
    openbao_namespace: str = ""
    openbao_timeout_seconds: float = 3.0

    billing_payment_webhook_signing_key: str = ""
    billing_payment_webhook_tolerance_seconds: int = 300
    billing_dunning_delivery_mode: Literal["record_only", "webhook"] = "record_only"
    billing_dunning_webhook_url: str = ""
    billing_dunning_webhook_key: str = ""
    billing_dunning_timeout_seconds: float = 5.0
    billing_tax_filing_delivery_mode: Literal["record_only", "webhook"] = "record_only"
    billing_tax_filing_webhook_url: str = ""
    billing_tax_filing_webhook_key: str = ""
    billing_tax_filing_timeout_seconds: float = 5.0

    report_artifact_dir: str = "data/report-artifacts"
    report_artifact_url_prefix: str = "local://reports"
    report_artifact_signing_key: str = "local-report-artifact-key"
    report_artifact_url_ttl_seconds: int = 900
    equipment_file_dir: str = "data/equipment-files"
    equipment_file_url_prefix: str = "local://equipment-files"
    travel_receipt_file_dir: str = "data/travel-receipts"
    travel_receipt_file_url_prefix: str = "local://travel-receipts"
    travel_checklist_file_dir: str = "data/travel-checklist-files"
    travel_checklist_file_url_prefix: str = "local://travel-checklist-files"
    travel_manifest_file_dir: str = "data/travel-manifests"
    travel_manifest_file_url_prefix: str = "local://travel-manifests"
    travel_manifest_signing_key: str = "local-travel-manifest-key"
    travel_manifest_url_ttl_seconds: int = 900
    travel_fee_payment_webhook_signing_key: str = ""
    travel_fee_payment_webhook_tolerance_seconds: int = 300
    travel_expense_payout_callback_signing_key: str = ""
    travel_expense_payout_callback_tolerance_seconds: int = 300
    travel_device_ingest_key: str = ""
    travel_device_ingest_tolerance_seconds: int = 300
    travel_device_ingest_event_retention_days: int = 30
    travel_device_provider_idempotency_days: dict[str, int] = Field(default_factory=dict)
    travel_device_secret_storage_mode: Literal["database", "database_with_vault_reference"] = "database"
    travel_device_secret_vault_provider: str = "openbao"
    travel_device_secret_vault_path_prefix: str = "secret/data/afrolete/travel-devices"
    object_storage_mode: Literal["local", "s3"] = "local"
    object_storage_endpoint: str = "http://127.0.0.1:9000"
    object_storage_region: str = "us-east-1"
    object_storage_bucket: str = "afrolete"
    object_storage_access_key: str = ""
    object_storage_access_key_secret_path: str = ""
    object_storage_access_key_secret_field: str = "access_key"
    object_storage_secret_key: str = ""
    object_storage_secret_key_secret_path: str = ""
    object_storage_secret_key_secret_field: str = "secret_key"
    object_storage_public_url: str = ""
    supplier_order_submission_mode: Literal["record_only", "webhook"] = "record_only"
    supplier_order_webhook_url: str = ""
    supplier_order_webhook_key: str = ""
    supplier_order_submission_timeout_seconds: float = 5.0
    supplier_invoice_sync_mode: Literal["record_only", "webhook"] = "record_only"
    supplier_invoice_webhook_url: str = ""
    supplier_invoice_webhook_key: str = ""
    supplier_invoice_sync_timeout_seconds: float = 5.0

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

    @field_validator("travel_device_provider_idempotency_days", mode="before")
    @classmethod
    def parse_provider_idempotency_days(cls, value: str | dict[str, int]) -> dict[str, int]:
        if isinstance(value, str):
            windows: dict[str, int] = {}
            for entry in value.split(","):
                if not entry.strip():
                    continue
                provider, _, days = entry.partition("=")
                if provider.strip() and days.strip():
                    windows[provider.strip().lower()] = max(int(days.strip()), 1)
            return windows
        return {provider.lower(): max(int(days), 1) for provider, days in value.items()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
