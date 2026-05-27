import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import create_app
from app.services.auth.keycloak import (
    KeycloakTokenVerifier,
    TokenIdentity,
    TokenVerificationError,
    get_keycloak_token_verifier,
)
from app.services.authz.service import authorization_service


ISSUER = "https://auth.example.test/realms/afrolete"
AUDIENCE = "afrolete-api"


class StubVerifier:
    async def verify(self, token: str) -> TokenIdentity:
        if token != "valid-token":
            raise TokenVerificationError("bad test token")
        return TokenIdentity(
            keycloak_sub="kc-keycloak-user",
            email="keycloak@example.com",
            display_name="Keycloak User",
            claims={"sub": "kc-keycloak-user"},
        )


@pytest.fixture
def rsa_private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def jwks_for_key(private_key, kid: str) -> dict:
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": [jwk]}


def access_token(private_key, kid: str, *, audience: str = AUDIENCE, issuer: str = ISSUER) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": issuer,
            "aud": audience,
            "sub": "kc-athlete-admin",
            "email": "admin@example.com",
            "name": "Athlete Admin",
            "preferred_username": "athlete-admin",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


@pytest.mark.asyncio
async def test_keycloak_verifier_accepts_valid_rs256_token(rsa_private_key) -> None:
    kid = "test-key-1"

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == f"{ISSUER}/protocol/openid-connect/certs"
        return httpx.Response(200, json=jwks_for_key(rsa_private_key, kid))

    verifier = KeycloakTokenVerifier(
        Settings(
            auth_mode="keycloak",
            keycloak_issuer=ISSUER,
            keycloak_audience=AUDIENCE,
        ),
        http_transport=httpx.MockTransport(handler),
    )

    identity = await verifier.verify(access_token(rsa_private_key, kid))

    assert identity.keycloak_sub == "kc-athlete-admin"
    assert identity.email == "admin@example.com"
    assert identity.display_name == "Athlete Admin"


@pytest.mark.asyncio
async def test_keycloak_verifier_rejects_wrong_audience(rsa_private_key) -> None:
    kid = "test-key-2"

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=jwks_for_key(rsa_private_key, kid))

    verifier = KeycloakTokenVerifier(
        Settings(
            auth_mode="keycloak",
            keycloak_issuer=ISSUER,
            keycloak_audience=AUDIENCE,
        ),
        http_transport=httpx.MockTransport(handler),
    )

    with pytest.raises(TokenVerificationError):
        await verifier.verify(access_token(rsa_private_key, kid, audience="other-api"))


def test_keycloak_mode_provisions_identity_from_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    monkeypatch.setenv("AFROLETE_AUTH_MODE", "keycloak")
    get_settings.cache_clear()
    get_keycloak_token_verifier.cache_clear()
    authorization_service.relationships.clear()
    app = create_app()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_keycloak_token_verifier] = StubVerifier

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/organizations",
                headers={"Authorization": "Bearer valid-token"},
                json={
                    "name": "Keycloak Sports Club",
                    "organization_type": "club",
                    "country_code": "KE",
                    "primary_sport": "football",
                },
            )

        assert response.status_code == 201
        assert response.json()["my_roles"] == ["owner"]
    finally:
        app.dependency_overrides.clear()
        authorization_service.relationships.clear()
        get_settings.cache_clear()
        get_keycloak_token_verifier.cache_clear()
