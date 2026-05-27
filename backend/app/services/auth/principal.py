from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class Principal:
    keycloak_sub: str
    email: str
    display_name: str


async def get_principal(
    x_afrolete_sub: str | None = Header(default=None),
    x_afrolete_email: str | None = Header(default=None),
    x_afrolete_name: str | None = Header(default=None),
) -> Principal:
    """Local/test principal dependency.

    Production Keycloak validation will replace this dependency without changing
    downstream service boundaries.
    """

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
