from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.enums import OrganizationType
from app.schemas.communication import CommunicationMessageRead
from app.schemas.agent import AgentTaskRead
from app.schemas.organization import (
    CommitteeCreate,
    CommitteeMemberAdd,
    CommitteeMembershipRead,
    CommitteeRead,
    FamilyRegistrationInquiryRead,
    MemberAdd,
    MembershipRead,
    OrganizationCreate,
    OrganizationDirectoryRead,
    OrganizationHandleAvailabilityRead,
    OrganizationOnboardingCreate,
    OrganizationOnboardingRead,
    OrganizationPublicSiteRead,
    OrganizationRead,
    PublicRegistrationDocumentUpload,
    PublicRegistrationPacketUpdate,
    PublicRegistrationInquiryCreate,
    PublicSiteFundraisingCampaignRead,
    PublicSiteEventRead,
    PublicSiteSponsorRead,
    PublicSiteTeamRead,
    PublicSiteTicketProductRead,
    RegistrationInquiryAccountReadinessRead,
    RegistrationPacketRead,
    RegistrationInquiryConversionCreate,
    RegistrationInquiryConversionRead,
    RegistrationInquiryFollowUpCreate,
    RegistrationInquiryFollowUpRead,
    RegistrationInquiryImportCreate,
    RegistrationInquiryImportRead,
    RegistrationInquiryImportTemplateRead,
    RegistrationInquiryRead,
    RegistrationInquiryUpdate,
    RegistrationPaymentHostedCheckoutRead,
    RegistrationPaymentSessionCreate,
    RegistrationPaymentSessionRead,
    RegistrationPaymentSettlementCreate,
    RegistrationPaymentSettlementRead,
    RegistrationReadinessRead,
)
from app.schemas.team import TeamRead
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.organizations import (
    add_committee_member,
    add_member,
    convert_registration_inquiry,
    create_registration_inquiry_follow_up,
    create_registration_payment_session,
    create_public_registration_inquiry,
    create_committee,
    create_onboarding_starter_team,
    create_organization,
    get_public_registration_account_readiness,
    get_registration_payment_hosted_checkout,
    get_organization_for_identity,
    get_public_registration_inquiry,
    get_public_site,
    import_registration_inquiries,
    organization_handle_availability,
    list_family_registration_inquiries,
    list_committees,
    list_organizations_for_identity,
    list_registration_inquiries,
    onboarding_checklist,
    organization_public_registration_documents,
    public_site_path,
    queue_onboarding_concierge_agent_task,
    registration_packet_summary,
    registration_inquiry_import_template,
    registration_readiness,
    queue_registration_inquiry_agent_review,
    search_public_organizations,
    settle_registration_payment_checkout,
    upload_public_registration_document,
    update_public_registration_packet,
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
        registration_open=organization.registration_open,
        registration_fee_amount=organization.registration_fee_amount,
        registration_fee_currency=organization.registration_fee_currency,
        registration_payment_instructions=organization.registration_payment_instructions,
        registration_required_documents=organization_public_registration_documents(organization),
        my_roles=roles,
    )


def to_public_site_read(item) -> OrganizationPublicSiteRead:
    organization, teams, events, sponsors, sponsorships, campaigns, ticket_products = item
    events_by_id = {event.id: event for event in events}
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
        registration_open=organization.registration_open,
        registration_fee_amount=organization.registration_fee_amount,
        registration_fee_currency=organization.registration_fee_currency,
        registration_payment_instructions=organization.registration_payment_instructions,
        registration_required_documents=organization_public_registration_documents(organization),
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
        sponsors=[
            PublicSiteSponsorRead(
                sponsor_id=sponsor.id,
                name=sponsor.name,
                industry=sponsor.industry,
                website_url=sponsor.website_url,
                brand_assets_url=sponsor.brand_assets_url,
                tier=_top_sponsorship_tier(sponsor.id, sponsorships),
                active_value=sum(
                    (
                        agreement.value_amount
                        for agreement in sponsorships
                        if agreement.sponsor_id == sponsor.id
                    ),
                    Decimal("0"),
                ),
                currency=_top_sponsorship_currency(sponsor.id, sponsorships),
                deliverables=_public_deliverables(sponsor.id, sponsorships),
                activation_note=_top_activation_note(sponsor.id, sponsorships),
            )
            for sponsor in sponsors
            if any(agreement.sponsor_id == sponsor.id for agreement in sponsorships)
        ],
        fundraising_campaigns=[
            PublicSiteFundraisingCampaignRead(
                id=campaign.id,
                name=campaign.name,
                purpose=campaign.purpose,
                goal_amount=campaign.goal_amount,
                raised_amount=campaign.raised_amount,
                currency=campaign.currency,
                public_url=campaign.public_url,
                status=campaign.status.value,
            )
            for campaign in campaigns
        ],
        ticket_products=[
            PublicSiteTicketProductRead(
                id=product.id,
                event_id=product.event_id,
                event_title=events_by_id[product.event_id].title if product.event_id in events_by_id else None,
                event_starts_at=events_by_id[product.event_id].starts_at if product.event_id in events_by_id else None,
                venue_name=events_by_id[product.event_id].venue_name if product.event_id in events_by_id else None,
                name=product.name,
                price=product.price,
                currency=product.currency,
                capacity=product.capacity,
                sold_count=product.sold_count,
                available_count=max(product.capacity - product.sold_count, 0),
                access_zone=product.access_zone,
                status=product.status.value,
            )
            for product in ticket_products
        ],
    )


def to_directory_read(item) -> OrganizationDirectoryRead:
    organization, team_count, upcoming_event_count = item
    return OrganizationDirectoryRead(
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
        public_site_path=public_site_path(organization),
        team_count=team_count,
        upcoming_event_count=upcoming_event_count,
    )


def _top_sponsorship_tier(sponsor_id: UUID, sponsorships) -> str | None:
    return next((agreement.tier for agreement in sponsorships if agreement.sponsor_id == sponsor_id), None)


def _top_sponsorship_currency(sponsor_id: UUID, sponsorships) -> str | None:
    return next((agreement.currency for agreement in sponsorships if agreement.sponsor_id == sponsor_id), None)


def _top_activation_note(sponsor_id: UUID, sponsorships) -> str | None:
    return next(
        (
            agreement.activation_notes
            for agreement in sponsorships
            if agreement.sponsor_id == sponsor_id and agreement.activation_notes
        ),
        None,
    )


def _public_deliverables(sponsor_id: UUID, sponsorships) -> list[str]:
    deliverables: list[str] = []
    for agreement in sponsorships:
        if agreement.sponsor_id != sponsor_id or not agreement.deliverables:
            continue
        deliverables.extend(part.strip() for part in agreement.deliverables.split(",") if part.strip())
    return deliverables[:6]


def to_registration_inquiry_read(inquiry) -> RegistrationInquiryRead:
    packet = registration_packet_summary(inquiry)
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
        guardian_person_id=inquiry.guardian_person_id,
        guardian_contact_status=inquiry.guardian_contact_status,
        date_of_birth=inquiry.date_of_birth,
        emergency_contact_name=inquiry.emergency_contact_name,
        emergency_contact_phone=inquiry.emergency_contact_phone,
        medical_notes=inquiry.medical_notes,
        consent_signer_name=inquiry.consent_signer_name,
        guardian_consent_acknowledged_at=inquiry.guardian_consent_acknowledged_at,
        privacy_acknowledged_at=inquiry.privacy_acknowledged_at,
        payment_amount=inquiry.payment_amount,
        payment_currency=inquiry.payment_currency,
        payment_method=inquiry.payment_method,
        payment_reference=inquiry.payment_reference,
        payment_status=inquiry.payment_status,
        verification_status=inquiry.verification_status,
        packet_submitted_at=inquiry.packet_submitted_at,
        missing_documents=packet["missing_documents"],
        packet_complete=packet["packet_complete"],
        next_steps=packet["next_steps"],
        created_at=inquiry.created_at,
    )


def to_registration_packet_read(inquiry) -> RegistrationPacketRead:
    summary = registration_packet_summary(inquiry)
    return RegistrationPacketRead(
        inquiry=to_registration_inquiry_read(inquiry),
        **summary,
    )


def to_registration_payment_session_read(item) -> RegistrationPaymentSessionRead:
    inquiry, session_id, checkout_url, provider, hosted_checkout = item
    return RegistrationPaymentSessionRead(
        inquiry=to_registration_inquiry_read(inquiry),
        session_id=session_id,
        checkout_url=checkout_url,
        provider=provider,
        hosted_checkout=hosted_checkout,
    )


def to_registration_conversion_read(item) -> RegistrationInquiryConversionRead:
    inquiry, athlete, athlete_profile, roster_entry, guardian, guardian_invite, guardian_invite_url = item
    return RegistrationInquiryConversionRead(
        inquiry=to_registration_inquiry_read(inquiry),
        athlete_person_id=athlete.id,
        athlete_profile_id=athlete_profile.id,
        roster_entry_id=roster_entry.id if roster_entry is not None else None,
        guardian_person_id=guardian.id if guardian is not None else None,
        guardian_invite_message_id=guardian_invite.id if guardian_invite is not None else None,
        guardian_invite_portal_url=guardian_invite_url,
    )


def to_agent_task_read(task) -> AgentTaskRead:
    approval_pending_count = max(
        int(task.approval_required_count or 0)
        - int(task.approval_approved_count or 0)
        - int(task.approval_rejected_count or 0),
        0,
    )
    return AgentTaskRead(
        id=task.id,
        agent_id=task.agent_id,
        organization_id=task.organization_id,
        task_type=task.task_type,
        title=task.title,
        status=task.status,
        requested_by_person_id=task.requested_by_person_id,
        input_ref=task.input_ref,
        output_ref=task.output_ref,
        review_notes=task.review_notes,
        review_assigned_to_person_id=task.review_assigned_to_person_id,
        review_due_at=task.review_due_at,
        review_priority=task.review_priority or "normal",
        review_assignment_notes=task.review_assignment_notes,
        approval_required_count=task.approval_required_count or 0,
        approval_approved_count=task.approval_approved_count or 0,
        approval_rejected_count=task.approval_rejected_count or 0,
        approval_pending_count=approval_pending_count,
        approval_status=task.approval_status or "not_requested",
        approval_last_decided_at=task.approval_last_decided_at,
        governance_policy_rule_id=task.governance_policy_rule_id,
        governance_policy_code=task.governance_policy_code,
        governance_policy_decision=task.governance_policy_decision,
        governance_policy_risk_level=task.governance_policy_risk_level,
        governance_policy_rationale=task.governance_policy_rationale,
    )


def to_team_read(team) -> TeamRead:
    return TeamRead(
        id=team.id,
        organization_id=team.organization_id,
        name=team.name,
        sport=team.sport,
        sport_format=team.sport_format,
        age_group=team.age_group,
        gender_category=team.gender_category,
        season_label=team.season_label,
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


@router.get("/directory", response_model=list[OrganizationDirectoryRead])
async def search_public_organizations_route(
    q: str | None = Query(default=None, max_length=120),
    organization_type: OrganizationType | None = None,
    sport: str | None = Query(default=None, max_length=80),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    limit: int = Query(default=12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationDirectoryRead]:
    return [
        to_directory_read(item)
        for item in await search_public_organizations(
            db,
            query=q,
            organization_type=organization_type,
            sport=sport,
            country_code=country_code,
            limit=limit,
        )
    ]


@router.get("/my-registration-inquiries", response_model=list[FamilyRegistrationInquiryRead])
async def list_family_registration_inquiries_route(
    organization_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyRegistrationInquiryRead]:
    return await list_family_registration_inquiries(db, identity, organization_id)


@router.get("/handles/availability", response_model=OrganizationHandleAvailabilityRead)
async def organization_handle_availability_route(
    name: str | None = Query(default=None, min_length=2, max_length=240),
    slug: str | None = Query(default=None, min_length=2, max_length=120),
    subdomain: str | None = Query(default=None, min_length=2, max_length=120),
    db: AsyncSession = Depends(get_db),
) -> OrganizationHandleAvailabilityRead:
    return await organization_handle_availability(db, name=name, slug=slug, subdomain=subdomain)


@router.get("/registration-readiness", response_model=RegistrationReadinessRead)
async def registration_readiness_route(
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RegistrationReadinessRead:
    return await registration_readiness(db, identity, settings)


@router.post("/onboarding", response_model=OrganizationOnboardingRead, status_code=status.HTTP_201_CREATED)
async def create_organization_onboarding_route(
    payload: OrganizationOnboardingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationOnboardingRead:
    organization, roles = await create_organization(db, identity, payload.organization, authz)
    starter_team = await create_onboarding_starter_team(
        db,
        organization,
        payload.starter_team_name,
        payload.starter_team_sport,
        payload.starter_team_sport_format,
        payload.starter_team_age_group,
        payload.starter_team_gender_category,
        payload.starter_team_season_label,
        authz,
    )
    concierge_task = await queue_onboarding_concierge_agent_task(
        db,
        identity,
        organization,
        starter_team,
        payload.launch_goal,
        authz,
    )
    return OrganizationOnboardingRead(
        organization=to_organization_read((organization, roles)),
        starter_team=to_team_read(starter_team),
        concierge_task=to_agent_task_read(concierge_task),
        public_site_path=public_site_path(organization),
        registration_page_path=f"/register?mode=player&site={organization.subdomain or organization.slug}",
        admissions_path=f"/admissions?organization_id={organization.id}",
        family_portal_path=f"/family?organization_id={organization.id}",
        dashboard_path=f"/?organization_id={organization.id}",
        owner_email=identity.email,
        owner_display_name=identity.display_name,
        checklist=onboarding_checklist(organization, payload.launch_goal),
    )


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


@router.get(
    "/public/{site}/registration-inquiries/{inquiry_id}/account-readiness",
    response_model=RegistrationInquiryAccountReadinessRead,
)
async def get_public_registration_account_readiness_route(
    site: str,
    inquiry_id: UUID,
    email: str = Query(min_length=3, max_length=320),
    db: AsyncSession = Depends(get_db),
) -> RegistrationInquiryAccountReadinessRead:
    return await get_public_registration_account_readiness(db, site, inquiry_id, email)


@router.get(
    "/public/{site}/registration-inquiries/{inquiry_id}/packet",
    response_model=RegistrationPacketRead,
)
async def get_public_registration_packet_route(
    site: str,
    inquiry_id: UUID,
    email: str = Query(min_length=3, max_length=320),
    db: AsyncSession = Depends(get_db),
) -> RegistrationPacketRead:
    _organization, inquiry = await get_public_registration_inquiry(db, site, inquiry_id)
    if inquiry.email.strip().lower() != email.strip().lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inquiry email mismatch")
    return to_registration_packet_read(inquiry)


@router.patch(
    "/public/{site}/registration-inquiries/{inquiry_id}/packet",
    response_model=RegistrationPacketRead,
)
async def update_public_registration_packet_route(
    site: str,
    inquiry_id: UUID,
    payload: PublicRegistrationPacketUpdate,
    db: AsyncSession = Depends(get_db),
) -> RegistrationPacketRead:
    return to_registration_packet_read(
        await update_public_registration_packet(db, site, inquiry_id, payload)
    )


@router.post(
    "/public/{site}/registration-inquiries/{inquiry_id}/documents",
    response_model=RegistrationPacketRead,
)
async def upload_public_registration_document_route(
    site: str,
    inquiry_id: UUID,
    payload: PublicRegistrationDocumentUpload,
    db: AsyncSession = Depends(get_db),
) -> RegistrationPacketRead:
    return to_registration_packet_read(
        await upload_public_registration_document(db, site, inquiry_id, payload)
    )


@router.post(
    "/public/{site}/registration-inquiries/{inquiry_id}/payment-session",
    response_model=RegistrationPaymentSessionRead,
)
async def create_registration_payment_session_route(
    site: str,
    inquiry_id: UUID,
    payload: RegistrationPaymentSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> RegistrationPaymentSessionRead:
    return to_registration_payment_session_read(
        await create_registration_payment_session(db, site, inquiry_id, payload)
    )


@router.get(
    "/registration-checkout-sessions/{session_id}",
    response_model=RegistrationPaymentHostedCheckoutRead,
)
async def get_registration_payment_checkout_session_route(
    session_id: str,
    site: str = Query(),
    inquiry_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    db: AsyncSession = Depends(get_db),
) -> RegistrationPaymentHostedCheckoutRead:
    return await get_registration_payment_hosted_checkout(
        db,
        session_id,
        site,
        inquiry_id,
        provider,
    )


@router.post(
    "/registration-checkout-sessions/{session_id}/settle",
    response_model=RegistrationPaymentSettlementRead,
)
async def settle_registration_payment_checkout_route(
    session_id: str,
    payload: RegistrationPaymentSettlementCreate,
    site: str = Query(),
    db: AsyncSession = Depends(get_db),
) -> RegistrationPaymentSettlementRead:
    return await settle_registration_payment_checkout(db, session_id, site, payload)


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


@router.get("/{organization_id}/registration-inquiries/import-template", response_model=RegistrationInquiryImportTemplateRead)
async def registration_inquiry_import_template_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RegistrationInquiryImportTemplateRead:
    return await registration_inquiry_import_template(db, identity, organization_id, authz)


@router.post("/{organization_id}/registration-inquiries/import", response_model=RegistrationInquiryImportRead)
async def import_registration_inquiries_route(
    organization_id: UUID,
    payload: RegistrationInquiryImportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RegistrationInquiryImportRead:
    inquiries, preview_rows, errors = await import_registration_inquiries(db, identity, organization_id, payload, authz)
    return RegistrationInquiryImportRead(
        organization_id=organization_id,
        dry_run=payload.dry_run,
        created_count=len(inquiries),
        preview_count=len(preview_rows),
        error_count=len(errors),
        inquiries=[to_registration_inquiry_read(inquiry) for inquiry in inquiries],
        preview_rows=preview_rows,
        errors=errors,
    )


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
    "/{organization_id}/registration-inquiries/{inquiry_id}/agent-review",
    response_model=AgentTaskRead,
    status_code=201,
)
async def queue_registration_inquiry_agent_review_route(
    organization_id: UUID,
    inquiry_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentTaskRead:
    return to_agent_task_read(
        await queue_registration_inquiry_agent_review(db, identity, organization_id, inquiry_id, authz)
    )


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
