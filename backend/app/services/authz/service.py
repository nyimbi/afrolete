from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Relationship:
    resource_type: str
    resource_id: str
    relation: str
    subject_type: str
    subject_id: str


class AuthorizationService(Protocol):
    async def touch(self, relationship: Relationship) -> None: ...

    async def check(
        self,
        *,
        resource_type: str,
        resource_id: str,
        permission: str,
        subject_type: str,
        subject_id: str,
    ) -> bool: ...


@dataclass
class InMemoryAuthorizationService:
    relationships: set[Relationship] = field(default_factory=set)

    async def touch(self, relationship: Relationship) -> None:
        self.relationships.add(relationship)

    async def check(
        self,
        *,
        resource_type: str,
        resource_id: str,
        permission: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        direct_permissions = {
            "manage": {"owner", "admin"},
            "manage_roster": {
                "owner",
                "admin",
                "coach",
                "assistant_coach",
                "staff",
                "manager",
                "captain",
            },
            "view": {
                "owner",
                "admin",
                "coach",
                "assistant_coach",
                "staff",
                "manager",
                "medic",
                "analyst",
                "guardian",
                "athlete",
                "player",
                "captain",
                "vice_captain",
                "substitute",
                "reserve",
                "bench",
                "individual_athlete",
                "viewer",
            },
        }
        allowed_relations = direct_permissions.get(permission, {permission})
        return any(
            relationship.resource_type == resource_type
            and relationship.resource_id == resource_id
            and relationship.subject_type == subject_type
            and relationship.subject_id == subject_id
            and relationship.relation in allowed_relations
            for relationship in self.relationships
        )


authorization_service = InMemoryAuthorizationService()


async def get_authorization_service() -> AuthorizationService:
    return authorization_service
