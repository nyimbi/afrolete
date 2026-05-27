from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.organization import (
    CommitteeCreate,
    CommitteeMemberAdd,
    CommitteeMembershipRead,
    CommitteeRead,
    MemberAdd,
    MembershipRead,
    OrganizationCreate,
    OrganizationRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.organizations import (
    add_committee_member,
    add_member,
    create_committee,
    create_organization,
    get_organization_for_identity,
    list_committees,
    list_organizations_for_identity,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


def to_organization_read(item) -> OrganizationRead:
    organization, roles = item
    return OrganizationRead(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        organization_type=organization.organization_type,
        association_level=organization.association_level,
        country_code=organization.country_code,
        primary_sport=organization.primary_sport,
        mission=organization.mission,
        public_name=organization.public_name,
        contact_email=organization.contact_email,
        contact_phone=organization.contact_phone,
        website_url=organization.website_url,
        subdomain=organization.subdomain,
        logo_url=organization.logo_url,
        brand_primary_color=organization.brand_primary_color,
        brand_secondary_color=organization.brand_secondary_color,
        my_roles=roles,
    )


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization_route(
    payload: OrganizationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationRead:
    return to_organization_read(await create_organization(db, identity, payload, authz))


@router.get("", response_model=list[OrganizationRead])
async def list_organizations_route(
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationRead]:
    return [
        to_organization_read(item) for item in await list_organizations_for_identity(db, identity)
    ]


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_organization_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    return to_organization_read(await get_organization_for_identity(db, identity, organization_id))


@router.post("/{organization_id}/members", response_model=MembershipRead, status_code=201)
async def add_member_route(
    organization_id: UUID,
    payload: MemberAdd,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MembershipRead:
    membership = await add_member(db, identity, organization_id, payload, authz)
    return MembershipRead(
        id=membership.id,
        organization_id=membership.organization_id,
        subject_type=membership.subject_type,
        subject_id=membership.subject_id,
        role=membership.role,
        title=membership.title,
        status=membership.status,
    )


def to_committee_read(committee) -> CommitteeRead:
    return CommitteeRead(
        id=committee.id,
        organization_id=committee.organization_id,
        name=committee.name,
        level=committee.level,
        mandate=committee.mandate,
        status=committee.status,
    )


@router.post("/{organization_id}/committees", response_model=CommitteeRead, status_code=201)
async def create_committee_route(
    organization_id: UUID,
    payload: CommitteeCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommitteeRead:
    return to_committee_read(await create_committee(db, identity, organization_id, payload, authz))


@router.get("/{organization_id}/committees", response_model=list[CommitteeRead])
async def list_committees_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CommitteeRead]:
    return [
        to_committee_read(committee) for committee in await list_committees(db, organization_id)
    ]


@router.post(
    "/committees/{committee_id}/members", response_model=CommitteeMembershipRead, status_code=201
)
async def add_committee_member_route(
    committee_id: UUID,
    payload: CommitteeMemberAdd,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommitteeMembershipRead:
    membership = await add_committee_member(db, identity, committee_id, payload, authz)
    return CommitteeMembershipRead(
        id=membership.id,
        committee_id=membership.committee_id,
        person_id=membership.person_id,
        role=membership.role,
        title=membership.title,
        status=membership.status,
    )
