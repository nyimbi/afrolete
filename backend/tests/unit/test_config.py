from app.core.config import Settings


def test_plain_postgresql_url_uses_async_driver() -> None:
    settings = Settings(database_url="postgresql:///afrolete")

    assert settings.database_url == "postgresql+asyncpg:///afrolete"


def test_postgres_alias_uses_async_driver() -> None:
    settings = Settings(database_url="postgres://user:pass@db.example.test/afrolete")

    assert settings.database_url == "postgresql+asyncpg://user:pass@db.example.test/afrolete"


def test_explicit_database_driver_is_preserved() -> None:
    settings = Settings(database_url="sqlite+aiosqlite://")

    assert settings.database_url == "sqlite+aiosqlite://"
