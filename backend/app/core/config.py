from functools import lru_cache

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
    database_url: str = "sqlite+aiosqlite:///./afrolete.local.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    keycloak_issuer: AnyHttpUrl = "https://auth.lindela.io/realms/lindela"
    keycloak_audience: str = "afrolete-api"

    spicedb_endpoint: str = "62.84.181.55:50051"
    spicedb_key: str = ""
    spicedb_insecure: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

