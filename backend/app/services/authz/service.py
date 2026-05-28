from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

import grpc
from authzed.api.v1 import (
    CheckPermissionRequest,
    CheckPermissionResponse,
    Consistency,
    ObjectReference,
    Relationship as SpiceDBRelationship,
    RelationshipUpdate,
    SubjectReference,
    WriteRelationshipsRequest,
)
from authzed.api.v1.permission_service_pb2_grpc import PermissionsServiceStub

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class Relationship:
    resource_type: str
    resource_id: str
    relation: str
    subject_type: str
    subject_id: str


class AuthorizationService(Protocol):
    async def touch(self, relationship: Relationship) -> None: ...

    async def delete(self, relationship: Relationship) -> None: ...

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

    async def delete(self, relationship: Relationship) -> None:
        self.relationships.discard(relationship)

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
            "manage": {"owner", "admin", "case_manager", "assigned_to"},
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
                "reporter",
                "case_manager",
                "assigned_to",
                "medical_viewer",
                "evidence_reviewer",
                "regulator",
            },
            "view_medical": {"owner", "admin", "case_manager", "assigned_to", "medical_viewer", "guardian"},
            "review_evidence": {"owner", "admin", "case_manager", "assigned_to", "evidence_reviewer"},
            "analyze": {"owner", "admin", "case_manager", "assigned_to", "assigned_agent"},
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


class SpiceDBAuthorizationService:
    def __init__(
        self,
        settings: Settings,
        *,
        permissions_stub: PermissionsServiceStub | None = None,
    ) -> None:
        self.request_timeout_seconds = settings.spicedb_request_timeout_seconds
        self._metadata = (("authorization", f"Bearer {settings.spicedb_key}"),)
        self._stub = permissions_stub or PermissionsServiceStub(self._channel(settings))

    def _channel(self, settings: Settings):
        if settings.spicedb_insecure:
            return grpc.aio.insecure_channel(settings.spicedb_endpoint)
        return grpc.aio.secure_channel(
            settings.spicedb_endpoint,
            grpc.ssl_channel_credentials(),
        )

    async def touch(self, relationship: Relationship) -> None:
        await self._stub.WriteRelationships(
            WriteRelationshipsRequest(
                updates=[
                    RelationshipUpdate(
                        operation=RelationshipUpdate.OPERATION_TOUCH,
                        relationship=self._relationship(relationship),
                    )
                ]
            ),
            metadata=self._metadata,
            timeout=self.request_timeout_seconds,
        )

    async def delete(self, relationship: Relationship) -> None:
        await self._stub.WriteRelationships(
            WriteRelationshipsRequest(
                updates=[
                    RelationshipUpdate(
                        operation=RelationshipUpdate.OPERATION_DELETE,
                        relationship=self._relationship(relationship),
                    )
                ]
            ),
            metadata=self._metadata,
            timeout=self.request_timeout_seconds,
        )

    async def check(
        self,
        *,
        resource_type: str,
        resource_id: str,
        permission: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        try:
            response = await self._stub.CheckPermission(
                CheckPermissionRequest(
                    consistency=Consistency(fully_consistent=True),
                    resource=ObjectReference(
                        object_type=resource_type,
                        object_id=resource_id,
                    ),
                    permission=permission,
                    subject=SubjectReference(
                        object=ObjectReference(
                            object_type=subject_type,
                            object_id=subject_id,
                        )
                    ),
                ),
                metadata=self._metadata,
                timeout=self.request_timeout_seconds,
            )
        except grpc.RpcError:
            return False

        return response.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION

    def _relationship(self, relationship: Relationship) -> SpiceDBRelationship:
        return SpiceDBRelationship(
            resource=ObjectReference(
                object_type=relationship.resource_type,
                object_id=relationship.resource_id,
            ),
            relation=relationship.relation,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=relationship.subject_type,
                    object_id=relationship.subject_id,
                )
            ),
        )


authorization_service = InMemoryAuthorizationService()


@lru_cache(maxsize=1)
def get_configured_authorization_service() -> AuthorizationService:
    settings = get_settings()
    if settings.authz_mode == "spicedb":
        if not settings.spicedb_key:
            raise RuntimeError("AFROLETE_SPICEDB_KEY is required when AFROLETE_AUTHZ_MODE=spicedb")
        return SpiceDBAuthorizationService(settings)
    return authorization_service


async def get_authorization_service() -> AuthorizationService:
    return get_configured_authorization_service()
