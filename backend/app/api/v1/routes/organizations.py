from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.communication import CommunicationMessageRead
from app.schemas.organization import (
    CommitteeCreate,
    CommitteeMemberAdd,
    CommitteeMembershipRead,
    CommitteeRead,
    MemberAdd,
    MembershipRead,
    OrganizationCreate,
    OrganizationPublicSiteRead,
    OrganizationRead,
    PublicRegistrationInquiryCreate,
    PublicSiteEventRead,
    PublicSiteTeamRead,
    RegistrationInquiryConversionCreate,
    RegistrationInquiryConversionRead,
    RegistrationInquiryFollowUpCreate,
    RegistrationInquiryFollowUpRead,
    RegistrationInquiryRead,
    RegistrationInquiryUpdate,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.organizations import (
    add_committee_member,
    add_member,
    convert_registration_inquiry,
    create_registration_inquiry_follow_up,
    create_public_registration_inquiry,
    create_committee,
    create_organization,
    get_organization_for_identity,
    get_public_site,
    list_committees,
    list_organizations_for_identity,
    list_registration_inquiries,
    update_registration_inquiry,
)
from app.services.communications import list_recipients

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


def to_public_site_read(item) -> OrganizationPublicSiteRead:
    organization, teams, events = item
    return OrganizationPublicSiteRead(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        organization_type=organization.organization_type,
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
        teams=[
            PublicSiteTeamRead(
                id=team.id,
                name=team.name,
                sport=team.sport,
                age_group=team.age_group,
                gender_category=team.gender_category,
                season_label=team.season_label,
            )
            for team in teams
        ],
        upcoming_events=[
            PublicSiteEventRead(
                id=event.id,
                team_id=event.team_id,
                event_type=event.event_type.value,
                title=event.title,
                starts_at=event.starts_at,
                ends_at=event.ends_at,
                timezone=event.timezone,
                venue_name=event.venue_name,
            )
            for event in events
        ],
    )


def to_registration_inquiry_read(inquiry) -> RegistrationInquiryRead:
    return RegistrationInquiryRead(
        id=inquiry.id,
        organization_id=inquiry.organization_id,
        team_id=inquiry.team_id,
        athlete_name=inquiry.athlete_name,
        guardian_name=inquiry.guardian_name,
        email=inquiry.email,
        phone=inquiry.phone,
        age_group=inquiry.age_group,
        sport_interest=inquiry.sport_interest,
        message=inquiry.message,
        source_url=inquiry.source_url,
        status=inquiry.status,
        review_notes=inquiry.review_notes,
        follow_up_at=inquiry.follow_up_at,
        reviewed_by_person_id=inquiry.reviewed_by_person_id,
        reviewed_at=inquiry.reviewed_at,
        created_at=inquiry.created_at,
    )


def to_registration_conversion_read(item) -> RegistrationInquiryConversionRead:
    inquiry, athlete, athlete_profile, roster_entry, guardian = item
    return RegistrationInquiryConversionRead(
        inquiry=to_registration_inquiry_read(inquiry),
        athlete_person_id=athlete.id,
        athlete_profile_id=athlete_profile.id,
        roster_entry_id=roster_entry.id if roster_entry is not None else None,
        guardian_person_id=guardian.id if guardian is not None else None,
    )


def to_communication_message_read(message, recipient_count: int = 0) -> CommunicationMessageRead:
    return CommunicationMessageRead(
        id=message.id,
        organization_id=message.organization_id,
        template_id=message.template_id,
        created_by_person_id=message.created_by_person_id,
        message_type=message.message_type,
        channel=message.channel,
        scope_type=message.scope_type,
        scope_id=message.scope_id,
        subject=message.subject,
        body=message.body,
        urgent=message.urgent,
        quiet_hours_override=message.quiet_hours_override,
        scheduled_for=message.scheduled_for,
        sent_at=message.sent_at,
        status=message.status,
        recipient_count=recipient_count,
    )


def to_registration_follow_up_read(item, recipient_count: int) -> RegistrationInquiryFollowUpRead:
    inquiry, message, recipient = item
    return RegistrationInquiryFollowUpRead(
        inquiry=to_registration_inquiry_read(inquiry),
        message=to_communication_message_read(message, recipient_count=recipient_count),
        recipient_person_id=recipient.id,
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


@router.get("/public/{site}", response_model=OrganizationPublicSiteRead)
async def get_public_site_route(
    site: str,
    db: AsyncSession = Depends(get_db),
) -> OrganizationPublicSiteRead:
    return to_public_site_read(await get_public_site(db, site))


@router.post("/public/{site}/registration-inquiries", response_model=RegistrationInquiryRead, status_code=201)
async def create_public_registration_inquiry_route(
    site: str,
    payload: PublicRegistrationInquiryCreate,
    db: AsyncSession = Depends(get_db),
) -> RegistrationInquiryRead:
    return to_registration_inquiry_read(await create_public_registration_inquiry(db, site, payload))


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_organization_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    return to_organization_read(await get_organization_for_identity(db, identity, organization_id))


@router.get("/{organization_id}/registration-inquiries", response_model=list[RegistrationInquiryRead])
async def list_registration_inquiries_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[RegistrationInquiryRead]:
    return [
        to_registration_inquiry_read(inquiry)
        for inquiry in await list_registration_inquiries(db, identity, organization_id, authz)
    ]


@router.patch("/{organization_id}/registration-inquiries/{inquiry_id}", response_model=RegistrationInquiryRead)
async def update_registration_inquiry_route(
    organization_id: UUID,
    inquiry_id: UUID,
    payload: RegistrationInquiryUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RegistrationInquiryRead:
    return to_registration_inquiry_read(
        await update_registration_inquiry(db, identity, organization_id, inquiry_id, payload, authz)
    )


@router.post(
    "/{organization_id}/registration-inquiries/{inquiry_id}/follow-up",
    response_model=RegistrationInquiryFollowUpRead,
)
async def create_registration_inquiry_follow_up_route(
    organization_id: UUID,
    inquiry_id: UUID,
    payload: RegistrationInquiryFollowUpCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RegistrationInquiryFollowUpRead:
    item = await create_registration_inquiry_follow_up(
        db,
        identity,
        organization_id,
        inquiry_id,
        payload,
        authz,
    )
    recipients = await list_recipients(db, item[1].id)
    return to_registration_follow_up_read(item, recipient_count=len(recipients))


@router.post(
    "/{organization_id}/registration-inquiries/{inquiry_id}/convert",
    response_model=RegistrationInquiryConversionRead,
)
async def convert_registration_inquiry_route(
    organization_id: UUID,
    inquiry_id: UUID,
    payload: RegistrationInquiryConversionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RegistrationInquiryConversionRead:
    return to_registration_conversion_read(
        await convert_registration_inquiry(db, identity, organization_id, inquiry_id, payload, authz)
    )


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
