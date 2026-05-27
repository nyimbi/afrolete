from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth.identity_bridge import CurrentIdentity, get_or_create_identity
from app.services.auth.principal import Principal, get_principal


async def get_current_identity(
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> CurrentIdentity:
    return await get_or_create_identity(db, principal)
