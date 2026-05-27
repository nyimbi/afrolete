from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AppUser, Person
from app.services.auth.principal import Principal


@dataclass(frozen=True)
class CurrentIdentity:
    user_id: UUID
    person_id: UUID
    keycloak_sub: str
    email: str
    display_name: str


async def get_or_create_identity(db: AsyncSession, principal: Principal) -> CurrentIdentity:
    changed = False
    user = await db.scalar(select(AppUser).where(AppUser.keycloak_sub == principal.keycloak_sub))
    if user is None:
        person = Person(display_name=principal.display_name, primary_email=principal.email)
        db.add(person)
        await db.flush()

        user = AppUser(
            keycloak_sub=principal.keycloak_sub,
            person_id=person.id,
            email=principal.email,
            display_name=principal.display_name,
        )
        db.add(user)
        await db.flush()
        changed = True
    elif user.person_id is None:
        person = Person(display_name=user.display_name or user.email, primary_email=user.email)
        db.add(person)
        await db.flush()
        user.person_id = person.id
        changed = True
    else:
        person = await db.get(Person, user.person_id)
        if person is None:
            person = Person(display_name=user.display_name or user.email, primary_email=user.email)
            db.add(person)
            await db.flush()
            user.person_id = person.id
            changed = True

    await db.flush()
    if changed:
        await db.commit()
        await db.refresh(user)

    if user.person_id is None:
        raise RuntimeError("Identity bridge failed to assign a person")

    return CurrentIdentity(
        user_id=user.id,
        person_id=user.person_id,
        keycloak_sub=user.keycloak_sub,
        email=user.email,
        display_name=user.display_name or user.email,
    )
