from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
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
        person = await person_for_principal(db, principal)

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
        person = await person_for_principal(db, principal)
        user.person_id = person.id
        changed = True
    else:
        person = await db.get(Person, user.person_id)
        if person is None:
            person = await person_for_principal(db, principal)
            user.person_id = person.id
            changed = True
    if user.email != principal.email:
        user.email = principal.email
        changed = True
    if principal.display_name and user.display_name != principal.display_name:
        user.display_name = principal.display_name
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


async def person_for_principal(db: AsyncSession, principal: Principal) -> Person:
    person = await db.scalar(
        select(Person).where(func.lower(Person.primary_email) == principal.email.lower())
    )
    if person is not None:
        if not person.display_name and principal.display_name:
            person.display_name = principal.display_name
        return person

    person = Person(display_name=principal.display_name, primary_email=principal.email)
    db.add(person)
    await db.flush()
    return person
