from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import httpx
import jwt
from jwt import PyJWKSet
from jwt.exceptions import InvalidTokenError, PyJWKError, PyJWTError

from app.core.config import Settings, get_settings


class TokenVerificationError(Exception):
    """Raised when a bearer token cannot be trusted as a Keycloak access token."""


@dataclass(frozen=True)
class TokenIdentity:
    keycloak_sub: str
    email: str
    display_name: str
    claims: dict[str, Any]


class KeycloakTokenVerifier:
    def __init__(
        self,
        settings: Settings,
        *,
        jwks_url: str | None = None,
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.issuer = str(settings.keycloak_issuer).rstrip("/")
        self.audience = settings.keycloak_audience
        self.algorithms = settings.keycloak_algorithms
        self.jwks_url = jwks_url or f"{self.issuer}/protocol/openid-connect/certs"
        self.timeout_seconds = settings.keycloak_http_timeout_seconds
        self.cache_ttl = timedelta(seconds=settings.keycloak_jwks_ttl_seconds)
        self._transport = http_transport
        self._jwks: PyJWKSet | None = None
        self._jwks_loaded_at: datetime | None = None

    async def verify(self, token: str) -> TokenIdentity:
        signing_key = await self._signing_key_for_token(token)
        try:
            claims = jwt.decode(
                token,
                key=signing_key.key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except InvalidTokenError as exc:
            raise TokenVerificationError("Invalid Keycloak bearer token") from exc

        return self._identity_from_claims(claims)

    async def _signing_key_for_token(self, token: str):
        try:
            header = jwt.get_unverified_header(token)
        except PyJWTError as exc:
            raise TokenVerificationError("Bearer token header is invalid") from exc

        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise TokenVerificationError("Bearer token is missing a key id")

        key = await self._lookup_signing_key(kid)
        if key is None:
            key = await self._lookup_signing_key(kid, force_refresh=True)
        if key is None:
            raise TokenVerificationError("Bearer token signing key is unknown")
        if key.algorithm_name not in self.algorithms:
            raise TokenVerificationError("Bearer token signing algorithm is not allowed")
        return key

    async def _lookup_signing_key(self, kid: str, *, force_refresh: bool = False):
        jwks = await self._get_jwks(force_refresh=force_refresh)
        for key in jwks.keys:
            if key.key_id == kid:
                return key
        return None

    async def _get_jwks(self, *, force_refresh: bool = False) -> PyJWKSet:
        now = datetime.now(UTC)
        cache_valid = (
            self._jwks is not None
            and self._jwks_loaded_at is not None
            and now - self._jwks_loaded_at < self.cache_ttl
        )
        if cache_valid and not force_refresh:
            return self._jwks

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                jwks = PyJWKSet.from_dict(response.json())
        except (httpx.HTTPError, PyJWKError, ValueError) as exc:
            raise TokenVerificationError("Unable to load Keycloak signing keys") from exc

        self._jwks = jwks
        self._jwks_loaded_at = now
        return jwks

    def _identity_from_claims(self, claims: dict[str, Any]) -> TokenIdentity:
        keycloak_sub = _claim_text(claims, "sub")
        email = _claim_text(claims, "email", required=False)
        preferred_username = _claim_text(claims, "preferred_username", required=False)

        if email is None:
            email = preferred_username
        if email is None:
            raise TokenVerificationError("Keycloak token is missing email identity")

        display_name = (
            _claim_text(claims, "name", required=False)
            or _joined_name(claims)
            or preferred_username
            or email
        )

        return TokenIdentity(
            keycloak_sub=keycloak_sub,
            email=email,
            display_name=display_name,
            claims=claims,
        )


def _claim_text(claims: dict[str, Any], key: str, *, required: bool = True) -> str | None:
    value = claims.get(key)
    if isinstance(value, str) and value.strip():
        return value
    if required:
        raise TokenVerificationError(f"Keycloak token is missing {key}")
    return None


def _joined_name(claims: dict[str, Any]) -> str | None:
    parts = [
        _claim_text(claims, "given_name", required=False),
        _claim_text(claims, "family_name", required=False),
    ]
    name = " ".join(part for part in parts if part)
    return name or None


@lru_cache(maxsize=1)
def get_keycloak_token_verifier() -> KeycloakTokenVerifier:
    return KeycloakTokenVerifier(get_settings())
