import grpc
import pytest

from authzed.api.v1 import CheckPermissionResponse, WriteRelationshipsResponse

from app.core.config import Settings, get_settings
from app.services.authz.service import (
    Relationship,
    SpiceDBAuthorizationService,
    get_configured_authorization_service,
)


class FakePermissionsStub:
    def __init__(self, permissionship: int) -> None:
        self.permissionship = permissionship
        self.write_request = None
        self.check_request = None
        self.metadata = None
        self.timeout = None

    async def WriteRelationships(self, request, *, metadata, timeout):
        self.write_request = request
        self.metadata = metadata
        self.timeout = timeout
        return WriteRelationshipsResponse()

    async def CheckPermission(self, request, *, metadata, timeout):
        self.check_request = request
        self.metadata = metadata
        self.timeout = timeout
        return CheckPermissionResponse(permissionship=self.permissionship)


class FailingPermissionsStub(FakePermissionsStub):
    async def CheckPermission(self, request, *, metadata, timeout):
        raise grpc.RpcError("unavailable")


@pytest.mark.asyncio
async def test_spicedb_touch_writes_relationship() -> None:
    stub = FakePermissionsStub(CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION)
    service = SpiceDBAuthorizationService(
        Settings(spicedb_key="test-key"),
        permissions_stub=stub,
    )
    relationship = Relationship(
        resource_type="organization",
        resource_id="org-1",
        relation="owner",
        subject_type="user",
        subject_id="user-1",
    )

    await service.touch(relationship)

    update = stub.write_request.updates[0]
    assert update.operation == update.OPERATION_TOUCH
    assert update.relationship.resource.object_type == "organization"
    assert update.relationship.resource.object_id == "org-1"
    assert update.relationship.relation == "owner"
    assert update.relationship.subject.object.object_type == "user"
    assert update.relationship.subject.object.object_id == "user-1"
    assert stub.metadata == (("authorization", "Bearer test-key"),)
    assert stub.timeout == 3.0


@pytest.mark.asyncio
async def test_spicedb_check_returns_true_for_has_permission() -> None:
    stub = FakePermissionsStub(CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION)
    service = SpiceDBAuthorizationService(
        Settings(spicedb_key="test-key"),
        permissions_stub=stub,
    )

    allowed = await service.check(
        resource_type="team",
        resource_id="team-1",
        permission="manage_roster",
        subject_type="user",
        subject_id="user-1",
    )

    assert allowed is True
    assert stub.check_request.resource.object_type == "team"
    assert stub.check_request.resource.object_id == "team-1"
    assert stub.check_request.permission == "manage_roster"
    assert stub.check_request.subject.object.object_type == "user"
    assert stub.check_request.subject.object.object_id == "user-1"


@pytest.mark.asyncio
async def test_spicedb_check_fails_closed_on_rpc_error() -> None:
    service = SpiceDBAuthorizationService(
        Settings(spicedb_key="test-key"),
        permissions_stub=FailingPermissionsStub(
            CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
        ),
    )

    allowed = await service.check(
        resource_type="team",
        resource_id="team-1",
        permission="manage_roster",
        subject_type="user",
        subject_id="user-1",
    )

    assert allowed is False


def test_spicedb_mode_requires_preshared_key(monkeypatch) -> None:
    monkeypatch.setenv("AFROLETE_AUTHZ_MODE", "spicedb")
    monkeypatch.delenv("AFROLETE_SPICEDB_KEY", raising=False)
    get_settings.cache_clear()
    get_configured_authorization_service.cache_clear()

    try:
        try:
            get_configured_authorization_service()
        except RuntimeError as exc:
            assert "AFROLETE_SPICEDB_KEY" in str(exc)
        else:
            raise AssertionError("Expected missing SpiceDB key to fail")
    finally:
        get_settings.cache_clear()
        get_configured_authorization_service.cache_clear()
