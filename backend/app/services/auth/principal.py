from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.services.auth.keycloak import (
    KeycloakTokenVerifier,
    TokenVerificationError,
    get_keycloak_token_verifier,
)


@dataclass(frozen=True)
class Principal:
    keycloak_sub: str
    email: str
    display_name: str


bearer_scheme = HTTPBearer(auto_error=False)


async def get_principal(
    x_afrolete_sub: str | None = Header(default=None),
    x_afrolete_email: str | None = Header(default=None),
    x_afrolete_name: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    verifier: KeycloakTokenVerifier = Depends(get_keycloak_token_verifier),
) -> Principal:
    settings = get_settings()
    if settings.auth_mode == "local":
        return _local_principal(x_afrolete_sub, x_afrolete_email, x_afrolete_name)

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        identity = await verifier.verify(credentials.credentials)
    except TokenVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        ) from exc

    return Principal(
        keycloak_sub=identity.keycloak_sub,
        email=identity.email,
        display_name=identity.display_name,
    )


def _local_principal(
    x_afrolete_sub: str | None,
    x_afrolete_email: str | None,
    x_afrolete_name: str | None,
) -> Principal:
    if not x_afrolete_sub or not x_afrolete_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing identity headers",
        )

    return Principal(
        keycloak_sub=x_afrolete_sub,
        email=x_afrolete_email,
        display_name=x_afrolete_name or x_afrolete_email,
    )
