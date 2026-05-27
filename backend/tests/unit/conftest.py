from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.identity import Person
from app.services.authz.service import authorization_service


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def client(db_session: AsyncSession) -> Iterator[TestClient]:
    authorization_service.relationships.clear()
    app = create_app()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    authorization_service.relationships.clear()


@pytest.fixture
def identity_headers() -> dict[str, str]:
    return {
        "X-Afrolete-Sub": "kc-owner-1",
        "X-Afrolete-Email": "owner@example.com",
        "X-Afrolete-Name": "Owner Example",
    }


@pytest.fixture
async def athlete_person(db_session: AsyncSession) -> Person:
    person = Person(display_name="Athlete Example", primary_email="athlete@example.com")
    db_session.add(person)
    await db_session.commit()
    await db_session.refresh(person)
    return person
