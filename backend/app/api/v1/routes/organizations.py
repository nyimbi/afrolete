from datetime import date
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
    MemberDuesCollectionRailCreate,
    MemberDuesCollectionRailRead,
    MemberDuesCollectionRailUpdate,
    MemberSubscriptionCheckoutLinkRead,
    MemberSubscriptionCheckoutSettlementCreate,
    MemberSubscriptionCheckoutSettlementRead,
    MemberSubscriptionChargeRead,
    MemberSubscriptionChargeRunCreate,
    MemberSubscriptionChargeRunRead,
    MemberSubscriptionChargeWaiverCreate,
    MemberSubscriptionChargeWaiverRead,
    MemberSubscriptionReceivablesSummaryRead,
    MemberSubscriptionCreate,
    MemberSubscriptionHostedCheckoutRead,
    MemberSubscriptionPaymentCreate,
    MemberSubscriptionPaymentRead,
    MemberSubscriptionPaymentPlanCreate,
    MemberSubscriptionPaymentPlanRead,
    MemberSubscriptionPaymentPlanUpdate,
    MemberSubscriptionPlanCreate,
    MemberSubscriptionPlanRead,
    MemberSubscriptionRead,
    MemberSubscriptionRenewalCampaignCreate,
    MemberSubscriptionRenewalCampaignRead,
    MemberSubscriptionRenewalOfferAcceptCreate,
    MemberSubscriptionRenewalOfferRead,
    MemberSubscriptionRenewalOfferRunCreate,
    MemberSubscriptionRenewalOfferRunRead,
    MemberSubscriptionUpdate,
    MemberSubscriptionPlanUpdate,
    MemberSubscriptionStatementArtifactRead,
    MemberSubscriptionStatementRead,
    MemberSubscriptionStatementSendCreate,
    MemberSubscriptionStatementSendRead,
    MemberSubscriptionReminderRunCreate,
    MemberSubscriptionReminderRunRead,
    MembershipRead,
    OrganizationAwardCategoryCreate,
    OrganizationAwardCategoryRead,
    OrganizationAwardNominationCreate,
    OrganizationAwardNominationRead,
    OrganizationAwardProgramCreate,
    OrganizationAwardProgramRead,
    OrganizationAwardRecipientCreate,
    OrganizationAwardRecipientRead,
    OrganizationAwardVoteCreate,
    OrganizationAwardVoteRead,
    OrganizationComplianceDocumentCreate,
    OrganizationComplianceDocumentRead,
    OrganizationComplianceDocumentSummaryRead,
    OrganizationComplianceDocumentVersionCreate,
    OrganizationComplianceDocumentVersionRead,
    OrganizationDataMigrationProjectCreate,
    OrganizationDataMigrationProjectRead,
    OrganizationDataMigrationRunCreate,
    OrganizationDataMigrationRunRead,
    OrganizationCreate,
    OrganizationDirectoryRead,
    OrganizationExternalReportCreate,
    OrganizationExternalReportRead,
    OrganizationExternalReportStatusUpdate,
    OrganizationExternalReportSummaryRead,
    OrganizationFinancialAidAppealCreate,
    OrganizationFinancialAidAppealRead,
    OrganizationFinancialAidAppealReview,
    OrganizationFinancialAidApplicationCreate,
    OrganizationFinancialAidApplicationRead,
    OrganizationFinancialAidApplicationReview,
    OrganizationFinancialAidRenewalCreate,
    OrganizationFinancialAidRenewalRead,
    OrganizationFinancialAidRenewalReview,
    OrganizationFinancialAidSummaryRead,
    OrganizationFinancialAidProgramCreate,
    OrganizationFinancialAidProgramRead,
    OrganizationGroupCreate,
    OrganizationGroupMemberAdd,
    OrganizationGroupMembershipRead,
    OrganizationGroupRead,
    OrganizationHandleAvailabilityRead,
    OrganizationMarketProfileCreate,
    OrganizationMarketProfileRead,
    OrganizationMarketProfileSummaryRead,
    OrganizationOnboardingCreate,
    OrganizationOnboardingRead,
    OrganizationProgramCreate,
    OrganizationProgramRead,
    OrganizationPublicSiteRead,
    OrganizationRecoveryDrillCreate,
    OrganizationRecoveryDrillRead,
    OrganizationRecoveryPlanCreate,
    OrganizationRecoveryPlanRead,
    OrganizationRead,
    OrganizationSeasonCreate,
    OrganizationSeasonRead,
    PublicRegistrationDocumentUpload,
    PublicRegistrationPacketUpdate,
    PublicRegistrationInquiryCreate,
    PublicSiteFundraisingCampaignRead,
    PublicSiteEventRead,
    PublicSiteSponsorRead,
    PublicSiteFanChallengeRead,
    PublicSiteFanLeaderboardEntryRead,
    PublicSiteSupporterTierRead,
    PublicSiteTeamRead,
    PublicSiteTicketProductRead,
    PublicSupporterChallengeProgressCreate,
    PublicSupporterChallengeProgressRead,
    PublicSupporterSignupCreate,
    PublicSupporterSignupRead,
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
    RegistrationLaunchCommandCenterRead,
    RegistrationLearningPathCreate,
    RegistrationLearningPathRead,
    RegistrationOnboardingPresetRead,
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
    create_or_update_organization_award_vote,
    create_organization_award_category,
    create_organization_award_nomination,
    create_organization_award_program,
    create_organization_award_recipient,
    create_compliance_document,
    create_compliance_document_version,
    create_data_migration_project,
    create_data_migration_run,
    create_organization_external_report,
    create_organization_financial_aid_appeal,
    create_organization_financial_aid_application,
    create_organization_financial_aid_program,
    create_organization_financial_aid_renewal,
    create_recovery_drill,
    create_recovery_plan,
    add_organization_group_member,
    create_member_dues_collection_rail,
    create_member_subscription,
    create_member_subscription_checkout_link,
    create_member_subscription_payment_plan,
    create_member_subscription_plan,
    create_member_subscription_renewal_campaign,
    accept_member_subscription_renewal_offer,
    run_member_subscription_charge_generation,
    run_member_subscription_renewal_offer_generation,
    export_member_subscription_statement_artifact,
    create_organization_group,
    create_organization_market_profile,
    create_organization_program,
    create_organization_season,
    create_public_registration_inquiry,
    create_committee,
    create_onboarding_starter_team,
    create_organization,
    registration_launch_command_center,
    get_public_registration_account_readiness,
    get_member_subscription_hosted_checkout,
    get_member_subscription_statement,
    get_registration_payment_hosted_checkout,
    get_organization_for_identity,
    get_public_registration_inquiry,
    get_public_site,
    ensure_manage_organization,
    import_registration_inquiries,
    organization_external_report_summary,
    organization_handle_availability,
    organization_market_profile_summary,
    list_family_registration_inquiries,
    list_organization_award_categories,
    list_organization_award_nominations,
    list_organization_award_programs,
    list_organization_award_recipients,
    compliance_document_summary,
    document_days_until_expiry,
    list_data_migration_projects,
    list_data_migration_runs,
    list_compliance_documents,
    list_compliance_document_versions,
    list_organization_external_reports,
    list_organization_financial_aid_appeals,
    list_organization_financial_aid_applications,
    list_organization_financial_aid_programs,
    list_organization_financial_aid_renewals,
    organization_financial_aid_summary,
    list_organization_group_members,
    list_organization_groups,
    list_organization_programs,
    list_organization_seasons,
    list_recovery_drills,
    list_recovery_plans,
    list_member_subscription_charges,
    list_member_dues_collection_rails,
    list_member_subscription_payment_plans,
    list_member_subscription_plans,
    list_member_subscription_renewal_campaigns,
    list_member_subscription_renewal_offers,
    list_member_subscriptions,
    member_subscription_receivables_summary,
    update_member_dues_collection_rail,
    list_organization_market_profiles,
    list_committees,
    list_organizations_for_identity,
    list_registration_inquiries,
    onboarding_checklist,
    organization_public_registration_documents,
    public_site_path,
    public_supporter_challenge_progress,
    public_supporter_signup,
    queue_onboarding_concierge_agent_task,
    registration_packet_summary,
    registration_inquiry_import_template,
    registration_learning_path,
    registration_onboarding_presets,
    registration_readiness,
    record_member_subscription_payment,
    run_member_subscription_reminders,
    send_member_subscription_statement,
    update_member_subscription,
    update_member_subscription_payment_plan,
    update_member_subscription_plan,
    update_organization_external_report_status,
    review_organization_financial_aid_appeal,
    review_organization_financial_aid_application,
    review_organization_financial_aid_renewal,
    waive_member_subscription_charge,
    queue_registration_inquiry_agent_review,
    search_public_organizations,
    settle_member_subscription_checkout,
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
    (
        organization,
        teams,
        events,
        sponsors,
        sponsorships,
        campaigns,
        ticket_products,
        supporter_tiers,
        fan_challenges,
        fan_leaderboard,
        challenge_completion_counts,
        supporter_completed_challenge_counts,
    ) = item
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
        supporter_tiers=[
            PublicSiteSupporterTierRead(
                id=tier.id,
                name=tier.name,
                slug=tier.slug,
                monthly_price=tier.monthly_price,
                currency=tier.currency,
                benefits=tier.benefits,
                voting_weight=tier.voting_weight,
                trial_days=tier.trial_days,
            )
            for tier in supporter_tiers
        ],
        fan_challenges=[
            PublicSiteFanChallengeRead(
                id=challenge.id,
                title=challenge.title,
                description=challenge.description,
                challenge_type=challenge.challenge_type,
                target_activity_type=challenge.target_activity_type,
                target_count=challenge.target_count,
                points_reward=challenge.points_reward,
                badge_name=challenge.badge_name,
                starts_at=challenge.starts_at,
                ends_at=challenge.ends_at,
                completion_count=challenge_completion_counts.get(challenge.id, 0),
            )
            for challenge in fan_challenges
        ],
        fan_leaderboard=[
            PublicSiteFanLeaderboardEntryRead(
                rank=index,
                supporter_profile_id=supporter.id,
                supporter_name=supporter.display_name,
                tier_name=tier.name if tier else None,
                engagement_points=supporter.engagement_points,
                completed_challenge_count=supporter_completed_challenge_counts.get(supporter.id, 0),
            )
            for index, (supporter, tier) in enumerate(fan_leaderboard, start=1)
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


@router.post("/registration-learning-path", response_model=RegistrationLearningPathRead)
async def registration_learning_path_route(
    payload: RegistrationLearningPathCreate,
) -> RegistrationLearningPathRead:
    return registration_learning_path(payload)


@router.get("/onboarding-presets", response_model=list[RegistrationOnboardingPresetRead])
async def registration_onboarding_presets_route(
    organization_type: OrganizationType | None = Query(default=None),
) -> list[RegistrationOnboardingPresetRead]:
    return registration_onboarding_presets(organization_type)


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
    launch_center, launch_agent_task = await registration_launch_command_center(
        db,
        identity,
        organization.id,
        authz,
    )
    launch_center.agent_task = to_agent_task_read(launch_agent_task) if launch_agent_task else None
    return OrganizationOnboardingRead(
        organization=to_organization_read((organization, roles)),
        starter_team=to_team_read(starter_team),
        concierge_task=to_agent_task_read(concierge_task),
        launch_center=launch_center,
        public_site_path=public_site_path(organization),
        registration_page_path=launch_center.registration_page_path,
        admissions_path=launch_center.admissions_path,
        family_portal_path=launch_center.family_portal_path,
        dashboard_path=launch_center.dashboard_path,
        owner_email=identity.email,
        owner_display_name=identity.display_name,
        checklist=onboarding_checklist(organization, payload.launch_goal),
    )


@router.get("/{organization_id}/registration-launch-center", response_model=RegistrationLaunchCommandCenterRead)
async def get_registration_launch_center_route(
    organization_id: UUID,
    base_url: str = Query(default="https://afrolete.lindela.io", max_length=500),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RegistrationLaunchCommandCenterRead:
    launch_center, launch_agent_task = await registration_launch_command_center(
        db,
        identity,
        organization_id,
        authz,
        base_url=base_url,
    )
    launch_center.agent_task = to_agent_task_read(launch_agent_task) if launch_agent_task else None
    return launch_center


@router.post("/{organization_id}/registration-launch-center/agent-task", response_model=RegistrationLaunchCommandCenterRead)
async def queue_registration_launch_center_agent_task_route(
    organization_id: UUID,
    base_url: str = Query(default="https://afrolete.lindela.io", max_length=500),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> RegistrationLaunchCommandCenterRead:
    launch_center, launch_agent_task = await registration_launch_command_center(
        db,
        identity,
        organization_id,
        authz,
        base_url=base_url,
        ensure_agent_task=True,
    )
    launch_center.agent_task = to_agent_task_read(launch_agent_task) if launch_agent_task else None
    return launch_center


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


@router.post("/public/{site}/supporters", response_model=PublicSupporterSignupRead, status_code=201)
async def create_public_supporter_route(
    site: str,
    payload: PublicSupporterSignupCreate,
    db: AsyncSession = Depends(get_db),
) -> PublicSupporterSignupRead:
    return await public_supporter_signup(db, site, payload)


@router.post(
    "/public/{site}/fan-challenges/{challenge_id}/progress",
    response_model=PublicSupporterChallengeProgressRead,
    status_code=201,
)
async def advance_public_supporter_challenge_route(
    site: str,
    challenge_id: UUID,
    payload: PublicSupporterChallengeProgressCreate,
    db: AsyncSession = Depends(get_db),
) -> PublicSupporterChallengeProgressRead:
    return await public_supporter_challenge_progress(db, site, challenge_id, payload)


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


def to_organization_program_read(program) -> OrganizationProgramRead:
    return OrganizationProgramRead(
        id=program.id,
        organization_id=program.organization_id,
        name=program.name,
        program_type=program.program_type,
        sport=program.sport,
        age_group=program.age_group,
        gender_category=program.gender_category,
        description=program.description,
        capacity=program.capacity,
        starts_on=program.starts_on,
        ends_on=program.ends_on,
        status=program.status,
    )


def to_organization_season_read(season) -> OrganizationSeasonRead:
    return OrganizationSeasonRead(
        id=season.id,
        organization_id=season.organization_id,
        name=season.name,
        sport=season.sport,
        starts_on=season.starts_on,
        ends_on=season.ends_on,
        registration_opens_on=season.registration_opens_on,
        registration_closes_on=season.registration_closes_on,
        status=season.status,
        notes=season.notes,
    )


def to_organization_group_read(item) -> OrganizationGroupRead:
    group, member_count = item
    return OrganizationGroupRead(
        id=group.id,
        organization_id=group.organization_id,
        name=group.name,
        group_type=group.group_type,
        program_id=group.program_id,
        season_id=group.season_id,
        team_id=group.team_id,
        lead_person_id=group.lead_person_id,
        sport=group.sport,
        age_group=group.age_group,
        description=group.description,
        capacity=group.capacity,
        status=group.status,
        member_count=member_count,
    )


def to_organization_group_membership_read(item) -> OrganizationGroupMembershipRead:
    membership, subject_label = item
    return OrganizationGroupMembershipRead(
        id=membership.id,
        group_id=membership.group_id,
        subject_type=membership.subject_type,
        subject_id=membership.subject_id,
        subject_label=subject_label,
        role=membership.role,
        status=membership.status,
        notes=membership.notes,
    )


@router.post("/{organization_id}/programs", response_model=OrganizationProgramRead, status_code=201)
async def create_organization_program_route(
    organization_id: UUID,
    payload: OrganizationProgramCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationProgramRead:
    return to_organization_program_read(
        await create_organization_program(db, identity, organization_id, payload, authz)
    )


@router.get("/{organization_id}/programs", response_model=list[OrganizationProgramRead])
async def list_organization_programs_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationProgramRead]:
    await ensure_manage_organization(db, identity, organization_id, authz)
    return [to_organization_program_read(program) for program in await list_organization_programs(db, organization_id)]


@router.post("/{organization_id}/seasons", response_model=OrganizationSeasonRead, status_code=201)
async def create_organization_season_route(
    organization_id: UUID,
    payload: OrganizationSeasonCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationSeasonRead:
    return to_organization_season_read(
        await create_organization_season(db, identity, organization_id, payload, authz)
    )


@router.get("/{organization_id}/seasons", response_model=list[OrganizationSeasonRead])
async def list_organization_seasons_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationSeasonRead]:
    await ensure_manage_organization(db, identity, organization_id, authz)
    return [to_organization_season_read(season) for season in await list_organization_seasons(db, organization_id)]


@router.post("/{organization_id}/groups", response_model=OrganizationGroupRead, status_code=201)
async def create_organization_group_route(
    organization_id: UUID,
    payload: OrganizationGroupCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationGroupRead:
    group = await create_organization_group(db, identity, organization_id, payload, authz)
    rows = await list_organization_groups(db, organization_id)
    return to_organization_group_read(next(row for row in rows if row[0].id == group.id))


@router.get("/{organization_id}/groups", response_model=list[OrganizationGroupRead])
async def list_organization_groups_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationGroupRead]:
    await ensure_manage_organization(db, identity, organization_id, authz)
    return [to_organization_group_read(row) for row in await list_organization_groups(db, organization_id)]


@router.post("/groups/{group_id}/members", response_model=OrganizationGroupMembershipRead, status_code=201)
async def add_organization_group_member_route(
    group_id: UUID,
    payload: OrganizationGroupMemberAdd,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationGroupMembershipRead:
    membership = await add_organization_group_member(db, identity, group_id, payload, authz)
    rows = await list_organization_group_members(db, identity, group_id, authz)
    return to_organization_group_membership_read(next(row for row in rows if row[0].id == membership.id))


@router.get("/groups/{group_id}/members", response_model=list[OrganizationGroupMembershipRead])
async def list_organization_group_members_route(
    group_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationGroupMembershipRead]:
    return [
        to_organization_group_membership_read(row)
        for row in await list_organization_group_members(db, identity, group_id, authz)
    ]


def to_organization_award_program_read(item) -> OrganizationAwardProgramRead:
    program, category_count, nomination_count, recipient_count = item
    return OrganizationAwardProgramRead(
        id=program.id,
        organization_id=program.organization_id,
        name=program.name,
        season_label=program.season_label,
        level=program.level,
        frequency=program.frequency,
        nomination_opens_at=program.nomination_opens_at,
        nomination_closes_at=program.nomination_closes_at,
        voting_opens_at=program.voting_opens_at,
        voting_closes_at=program.voting_closes_at,
        eligibility_summary=program.eligibility_summary,
        ceremony_name=program.ceremony_name,
        ceremony_at=program.ceremony_at,
        ceremony_venue=program.ceremony_venue,
        certificate_template=program.certificate_template,
        status=program.status,
        notes=program.notes,
        category_count=category_count,
        nomination_count=nomination_count,
        recipient_count=recipient_count,
    )


def to_organization_award_category_read(item) -> OrganizationAwardCategoryRead:
    category, nomination_count, recipient_count = item
    return OrganizationAwardCategoryRead(
        id=category.id,
        organization_id=category.organization_id,
        program_id=category.program_id,
        name=category.name,
        award_type=category.award_type,
        judging_method=category.judging_method,
        criteria=category.criteria,
        max_recipients=category.max_recipients,
        voter_roles=category.voter_roles,
        status=category.status,
        nomination_count=nomination_count,
        recipient_count=recipient_count,
    )


def to_organization_award_nomination_read(item) -> OrganizationAwardNominationRead:
    nomination, nominee_label, vote_count, weighted_score = item
    return OrganizationAwardNominationRead(
        id=nomination.id,
        organization_id=nomination.organization_id,
        program_id=nomination.program_id,
        category_id=nomination.category_id,
        nominee_subject_type=nomination.nominee_subject_type,
        nominee_subject_id=nomination.nominee_subject_id,
        nominee_label=nominee_label,
        nominated_by_person_id=nomination.nominated_by_person_id,
        title=nomination.title,
        nomination_summary=nomination.nomination_summary,
        evidence_url=nomination.evidence_url,
        status=nomination.status,
        finalist=nomination.finalist,
        score=nomination.score,
        vote_count=vote_count,
        weighted_score=weighted_score,
    )


def to_organization_award_vote_read(item) -> OrganizationAwardVoteRead:
    vote, voter_label = item
    return OrganizationAwardVoteRead(
        id=vote.id,
        organization_id=vote.organization_id,
        nomination_id=vote.nomination_id,
        voter_person_id=vote.voter_person_id,
        voter_label=voter_label,
        score=vote.score,
        weight=vote.weight,
        comment=vote.comment,
    )


def to_organization_award_recipient_read(item) -> OrganizationAwardRecipientRead:
    recipient, recipient_label = item
    return OrganizationAwardRecipientRead(
        id=recipient.id,
        organization_id=recipient.organization_id,
        program_id=recipient.program_id,
        category_id=recipient.category_id,
        nomination_id=recipient.nomination_id,
        recipient_subject_type=recipient.recipient_subject_type,
        recipient_subject_id=recipient.recipient_subject_id,
        recipient_label=recipient_label,
        certificate_number=recipient.certificate_number,
        awarded_on=recipient.awarded_on,
        public_citation=recipient.public_citation,
        certificate_url=recipient.certificate_url,
        status=recipient.status,
    )


@router.post(
    "/{organization_id}/award-programs",
    response_model=OrganizationAwardProgramRead,
    status_code=201,
)
async def create_organization_award_program_route(
    organization_id: UUID,
    payload: OrganizationAwardProgramCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationAwardProgramRead:
    program = await create_organization_award_program(db, identity, organization_id, payload, authz)
    rows = await list_organization_award_programs(db, identity, organization_id, authz)
    return to_organization_award_program_read(next(row for row in rows if row[0].id == program.id))


@router.get("/{organization_id}/award-programs", response_model=list[OrganizationAwardProgramRead])
async def list_organization_award_programs_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationAwardProgramRead]:
    return [
        to_organization_award_program_read(row)
        for row in await list_organization_award_programs(db, identity, organization_id, authz)
    ]


@router.post(
    "/award-programs/{program_id}/categories",
    response_model=OrganizationAwardCategoryRead,
    status_code=201,
)
async def create_organization_award_category_route(
    program_id: UUID,
    payload: OrganizationAwardCategoryCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationAwardCategoryRead:
    category = await create_organization_award_category(db, identity, program_id, payload, authz)
    rows = await list_organization_award_categories(db, identity, program_id, authz)
    return to_organization_award_category_read(next(row for row in rows if row[0].id == category.id))


@router.get("/award-programs/{program_id}/categories", response_model=list[OrganizationAwardCategoryRead])
async def list_organization_award_categories_route(
    program_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationAwardCategoryRead]:
    return [
        to_organization_award_category_read(row)
        for row in await list_organization_award_categories(db, identity, program_id, authz)
    ]


@router.post(
    "/award-categories/{category_id}/nominations",
    response_model=OrganizationAwardNominationRead,
    status_code=201,
)
async def create_organization_award_nomination_route(
    category_id: UUID,
    payload: OrganizationAwardNominationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationAwardNominationRead:
    nomination = await create_organization_award_nomination(db, identity, category_id, payload, authz)
    rows = await list_organization_award_nominations(db, identity, category_id, authz)
    return to_organization_award_nomination_read(
        next(row for row in rows if row[0].id == nomination.id)
    )


@router.get(
    "/award-categories/{category_id}/nominations",
    response_model=list[OrganizationAwardNominationRead],
)
async def list_organization_award_nominations_route(
    category_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationAwardNominationRead]:
    return [
        to_organization_award_nomination_read(row)
        for row in await list_organization_award_nominations(db, identity, category_id, authz)
    ]


@router.post(
    "/award-nominations/{nomination_id}/votes",
    response_model=OrganizationAwardVoteRead,
    status_code=201,
)
async def create_organization_award_vote_route(
    nomination_id: UUID,
    payload: OrganizationAwardVoteCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationAwardVoteRead:
    vote = await create_or_update_organization_award_vote(
        db,
        identity,
        nomination_id,
        payload,
        authz,
    )
    voter_label = identity.display_name if vote.voter_person_id == identity.person_id else None
    return to_organization_award_vote_read((vote, voter_label))


@router.post(
    "/award-categories/{category_id}/recipients",
    response_model=OrganizationAwardRecipientRead,
    status_code=201,
)
async def create_organization_award_recipient_route(
    category_id: UUID,
    payload: OrganizationAwardRecipientCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationAwardRecipientRead:
    recipient = await create_organization_award_recipient(db, identity, category_id, payload, authz)
    rows = await list_organization_award_recipients(db, identity, recipient.program_id, authz)
    return to_organization_award_recipient_read(next(row for row in rows if row[0].id == recipient.id))


@router.get(
    "/award-programs/{program_id}/recipients",
    response_model=list[OrganizationAwardRecipientRead],
)
async def list_organization_award_recipients_route(
    program_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationAwardRecipientRead]:
    return [
        to_organization_award_recipient_read(row)
        for row in await list_organization_award_recipients(db, identity, program_id, authz)
    ]


def to_compliance_document_read(row) -> OrganizationComplianceDocumentRead:
    document, version_count = row
    return OrganizationComplianceDocumentRead(
        id=document.id,
        organization_id=document.organization_id,
        title=document.title,
        category=document.category,
        document_type=document.document_type,
        subject_type=document.subject_type,
        subject_id=document.subject_id,
        owner_person_id=document.owner_person_id,
        issuer=document.issuer,
        reference_number=document.reference_number,
        status=document.status,
        renewal_status=document.renewal_status,
        effective_on=document.effective_on,
        expires_on=document.expires_on,
        next_review_on=document.next_review_on,
        retention_until=document.retention_until,
        auto_renewal_enabled=document.auto_renewal_enabled,
        storage_url=document.storage_url,
        checksum=document.checksum,
        current_version=document.current_version,
        confidentiality=document.confidentiality,
        tags=document.tags,
        notes=document.notes,
        version_count=version_count,
        days_until_expiry=document_days_until_expiry(document),
    )


def to_compliance_document_version_read(version) -> OrganizationComplianceDocumentVersionRead:
    return OrganizationComplianceDocumentVersionRead(
        id=version.id,
        organization_id=version.organization_id,
        document_id=version.document_id,
        version_number=version.version_number,
        storage_url=version.storage_url,
        checksum=version.checksum,
        filename=version.filename,
        content_type=version.content_type,
        size_bytes=version.size_bytes,
        change_summary=version.change_summary,
        uploaded_by_person_id=version.uploaded_by_person_id,
        verified_by_person_id=version.verified_by_person_id,
        verified_at=version.verified_at,
        status=version.status,
    )


@router.post(
    "/{organization_id}/compliance-documents",
    response_model=OrganizationComplianceDocumentRead,
    status_code=201,
)
async def create_compliance_document_route(
    organization_id: UUID,
    payload: OrganizationComplianceDocumentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationComplianceDocumentRead:
    document = await create_compliance_document(db, identity, organization_id, payload, authz)
    rows = await list_compliance_documents(db, organization_id)
    return to_compliance_document_read(next(row for row in rows if row[0].id == document.id))


@router.get("/{organization_id}/compliance-documents", response_model=list[OrganizationComplianceDocumentRead])
async def list_compliance_documents_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationComplianceDocumentRead]:
    await ensure_manage_organization(db, identity, organization_id, authz)
    return [to_compliance_document_read(row) for row in await list_compliance_documents(db, organization_id)]


@router.get("/{organization_id}/compliance-documents/summary", response_model=OrganizationComplianceDocumentSummaryRead)
async def compliance_document_summary_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationComplianceDocumentSummaryRead:
    await ensure_manage_organization(db, identity, organization_id, authz)
    return await compliance_document_summary(db, organization_id)


@router.post(
    "/compliance-documents/{document_id}/versions",
    response_model=OrganizationComplianceDocumentVersionRead,
    status_code=201,
)
async def create_compliance_document_version_route(
    document_id: UUID,
    payload: OrganizationComplianceDocumentVersionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationComplianceDocumentVersionRead:
    version, _ = await create_compliance_document_version(db, identity, document_id, payload, authz)
    return to_compliance_document_version_read(version)


@router.get(
    "/compliance-documents/{document_id}/versions",
    response_model=list[OrganizationComplianceDocumentVersionRead],
)
async def list_compliance_document_versions_route(
    document_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationComplianceDocumentVersionRead]:
    return [
        to_compliance_document_version_read(version)
        for version in await list_compliance_document_versions(db, identity, document_id, authz)
    ]


def to_data_migration_project_read(row) -> OrganizationDataMigrationProjectRead:
    project, run_count = row
    return OrganizationDataMigrationProjectRead(
        id=project.id,
        organization_id=project.organization_id,
        name=project.name,
        source_system=project.source_system,
        source_format=project.source_format,
        migration_type=project.migration_type,
        data_domains=project.data_domains,
        owner_person_id=project.owner_person_id,
        status=project.status,
        risk_level=project.risk_level,
        records_expected=project.records_expected,
        records_imported=project.records_imported,
        error_count=project.error_count,
        started_at=project.started_at,
        completed_at=project.completed_at,
        notes=project.notes,
        run_count=run_count,
    )


def to_data_migration_run_read(run) -> OrganizationDataMigrationRunRead:
    return OrganizationDataMigrationRunRead(
        id=run.id,
        organization_id=run.organization_id,
        project_id=run.project_id,
        run_type=run.run_type,
        status=run.status,
        input_artifact_url=run.input_artifact_url,
        mapping_summary=run.mapping_summary,
        started_at=run.started_at,
        finished_at=run.finished_at,
        records_seen=run.records_seen,
        records_created=run.records_created,
        records_updated=run.records_updated,
        records_skipped=run.records_skipped,
        error_count=run.error_count,
        checksum=run.checksum,
        report_url=run.report_url,
        notes=run.notes,
    )


def to_recovery_plan_read(row) -> OrganizationRecoveryPlanRead:
    plan, drill_count = row
    return OrganizationRecoveryPlanRead(
        id=plan.id,
        organization_id=plan.organization_id,
        name=plan.name,
        scope=plan.scope,
        rpo_minutes=plan.rpo_minutes,
        rto_minutes=plan.rto_minutes,
        backup_frequency=plan.backup_frequency,
        storage_location=plan.storage_location,
        retention_days=plan.retention_days,
        encryption_policy=plan.encryption_policy,
        status=plan.status,
        last_tested_at=plan.last_tested_at,
        next_test_due_at=plan.next_test_due_at,
        notes=plan.notes,
        drill_count=drill_count,
    )


def to_recovery_drill_read(drill) -> OrganizationRecoveryDrillRead:
    return OrganizationRecoveryDrillRead(
        id=drill.id,
        organization_id=drill.organization_id,
        recovery_plan_id=drill.recovery_plan_id,
        drill_type=drill.drill_type,
        status=drill.status,
        started_at=drill.started_at,
        finished_at=drill.finished_at,
        rpo_minutes_observed=drill.rpo_minutes_observed,
        rto_minutes_observed=drill.rto_minutes_observed,
        data_loss_summary=drill.data_loss_summary,
        result_summary=drill.result_summary,
        action_items=drill.action_items,
        evidence_url=drill.evidence_url,
        notes=drill.notes,
    )


@router.post(
    "/{organization_id}/data-migration-projects",
    response_model=OrganizationDataMigrationProjectRead,
    status_code=201,
)
async def create_data_migration_project_route(
    organization_id: UUID,
    payload: OrganizationDataMigrationProjectCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationDataMigrationProjectRead:
    project = await create_data_migration_project(db, identity, organization_id, payload, authz)
    rows = await list_data_migration_projects(db, organization_id)
    return to_data_migration_project_read(next(row for row in rows if row[0].id == project.id))


@router.get(
    "/{organization_id}/data-migration-projects",
    response_model=list[OrganizationDataMigrationProjectRead],
)
async def list_data_migration_projects_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationDataMigrationProjectRead]:
    return [to_data_migration_project_read(row) for row in await list_data_migration_projects(db, organization_id)]


@router.post(
    "/data-migration-projects/{project_id}/runs",
    response_model=OrganizationDataMigrationRunRead,
    status_code=201,
)
async def create_data_migration_run_route(
    project_id: UUID,
    payload: OrganizationDataMigrationRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationDataMigrationRunRead:
    run, _ = await create_data_migration_run(db, identity, project_id, payload, authz)
    return to_data_migration_run_read(run)


@router.get(
    "/data-migration-projects/{project_id}/runs",
    response_model=list[OrganizationDataMigrationRunRead],
)
async def list_data_migration_runs_route(
    project_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationDataMigrationRunRead]:
    return [
        to_data_migration_run_read(run)
        for run in await list_data_migration_runs(db, identity, project_id, authz)
    ]


@router.post(
    "/{organization_id}/recovery-plans",
    response_model=OrganizationRecoveryPlanRead,
    status_code=201,
)
async def create_recovery_plan_route(
    organization_id: UUID,
    payload: OrganizationRecoveryPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationRecoveryPlanRead:
    plan = await create_recovery_plan(db, identity, organization_id, payload, authz)
    rows = await list_recovery_plans(db, organization_id)
    return to_recovery_plan_read(next(row for row in rows if row[0].id == plan.id))


@router.get("/{organization_id}/recovery-plans", response_model=list[OrganizationRecoveryPlanRead])
async def list_recovery_plans_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationRecoveryPlanRead]:
    return [to_recovery_plan_read(row) for row in await list_recovery_plans(db, organization_id)]


@router.post(
    "/recovery-plans/{recovery_plan_id}/drills",
    response_model=OrganizationRecoveryDrillRead,
    status_code=201,
)
async def create_recovery_drill_route(
    recovery_plan_id: UUID,
    payload: OrganizationRecoveryDrillCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationRecoveryDrillRead:
    drill, _ = await create_recovery_drill(db, identity, recovery_plan_id, payload, authz)
    return to_recovery_drill_read(drill)


@router.get(
    "/recovery-plans/{recovery_plan_id}/drills",
    response_model=list[OrganizationRecoveryDrillRead],
)
async def list_recovery_drills_route(
    recovery_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OrganizationRecoveryDrillRead]:
    return [
        to_recovery_drill_read(drill)
        for drill in await list_recovery_drills(db, identity, recovery_plan_id, authz)
    ]


def to_member_subscription_plan_read(plan) -> MemberSubscriptionPlanRead:
    return MemberSubscriptionPlanRead(
        id=plan.id,
        organization_id=plan.organization_id,
        name=plan.name,
        description=plan.description,
        member_role=plan.member_role,
        amount=plan.amount,
        currency=plan.currency,
        billing_interval=plan.billing_interval,
        due_day=plan.due_day,
        grace_period_days=plan.grace_period_days,
        benefits=plan.benefits,
        status=plan.status,
    )


def to_member_subscription_read(item) -> MemberSubscriptionRead:
    subscription, plan, subject_label = item
    return MemberSubscriptionRead(
        id=subscription.id,
        organization_id=subscription.organization_id,
        plan_id=subscription.plan_id,
        plan_name=plan.name,
        membership_id=subscription.membership_id,
        subject_type=subscription.subject_type,
        subject_id=subscription.subject_id,
        subject_label=subject_label,
        starts_on=subscription.starts_on,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        next_due_on=subscription.next_due_on,
        status=subscription.status,
        balance_amount=subscription.balance_amount,
        currency=plan.currency,
        dues_last_reminded_at=subscription.dues_last_reminded_at,
        dues_reminder_message_id=subscription.dues_reminder_message_id,
        dues_reminder_count=subscription.dues_reminder_count,
        external_reference=subscription.external_reference,
        notes=subscription.notes,
    )


def to_member_subscription_charge_read(item) -> MemberSubscriptionChargeRead:
    charge, _subscription, plan, subject_label = item
    return MemberSubscriptionChargeRead(
        id=charge.id,
        organization_id=charge.organization_id,
        subscription_id=charge.subscription_id,
        plan_id=charge.plan_id,
        plan_name=plan.name,
        subject_label=subject_label,
        period_start=charge.period_start,
        period_end=charge.period_end,
        due_on=charge.due_on,
        amount=charge.amount,
        amount_paid=charge.amount_paid,
        amount_waived=charge.amount_waived,
        balance_amount=charge.balance_amount,
        currency=charge.currency,
        status=charge.status,
        source=charge.source,
        description=charge.description,
        paid_at=charge.paid_at,
        last_payment_id=charge.last_payment_id,
        waived_at=charge.waived_at,
        waived_by_person_id=charge.waived_by_person_id,
        waiver_reason=charge.waiver_reason,
        created_by_person_id=charge.created_by_person_id,
        created_at=charge.created_at,
    )


@router.post(
    "/{organization_id}/member-dues-collection-rails",
    response_model=MemberDuesCollectionRailRead,
    status_code=201,
)
async def create_member_dues_collection_rail_route(
    organization_id: UUID,
    payload: MemberDuesCollectionRailCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberDuesCollectionRailRead:
    return await create_member_dues_collection_rail(db, identity, organization_id, payload, authz)


@router.get(
    "/{organization_id}/member-dues-collection-rails",
    response_model=list[MemberDuesCollectionRailRead],
)
async def list_member_dues_collection_rails_route(
    organization_id: UUID,
    include_disabled: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> list[MemberDuesCollectionRailRead]:
    return await list_member_dues_collection_rails(db, organization_id, include_disabled=include_disabled)


@router.patch(
    "/member-dues-collection-rails/{rail_id}",
    response_model=MemberDuesCollectionRailRead,
)
async def update_member_dues_collection_rail_route(
    rail_id: UUID,
    payload: MemberDuesCollectionRailUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberDuesCollectionRailRead:
    return await update_member_dues_collection_rail(db, identity, rail_id, payload, authz)


@router.post(
    "/{organization_id}/member-subscription-plans",
    response_model=MemberSubscriptionPlanRead,
    status_code=201,
)
async def create_member_subscription_plan_route(
    organization_id: UUID,
    payload: MemberSubscriptionPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionPlanRead:
    return to_member_subscription_plan_read(
        await create_member_subscription_plan(db, identity, organization_id, payload, authz)
    )


@router.get("/{organization_id}/member-subscription-plans", response_model=list[MemberSubscriptionPlanRead])
async def list_member_subscription_plans_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[MemberSubscriptionPlanRead]:
    return [
        to_member_subscription_plan_read(plan)
        for plan in await list_member_subscription_plans(db, organization_id)
    ]


@router.patch(
    "/{organization_id}/member-subscription-plans/{plan_id}",
    response_model=MemberSubscriptionPlanRead,
)
async def update_member_subscription_plan_route(
    organization_id: UUID,
    plan_id: UUID,
    payload: MemberSubscriptionPlanUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionPlanRead:
    return to_member_subscription_plan_read(
        await update_member_subscription_plan(db, identity, organization_id, plan_id, payload, authz)
    )


@router.post(
    "/{organization_id}/member-subscriptions",
    response_model=MemberSubscriptionRead,
    status_code=201,
)
async def create_member_subscription_route(
    organization_id: UUID,
    payload: MemberSubscriptionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionRead:
    subscription = await create_member_subscription(db, identity, organization_id, payload, authz)
    rows = await list_member_subscriptions(db, organization_id)
    return to_member_subscription_read(next(row for row in rows if row[0].id == subscription.id))


@router.get("/{organization_id}/member-subscriptions", response_model=list[MemberSubscriptionRead])
async def list_member_subscriptions_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[MemberSubscriptionRead]:
    return [to_member_subscription_read(row) for row in await list_member_subscriptions(db, organization_id)]


@router.patch("/member-subscriptions/{subscription_id}", response_model=MemberSubscriptionRead)
async def update_member_subscription_route(
    subscription_id: UUID,
    payload: MemberSubscriptionUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionRead:
    subscription = await update_member_subscription(db, identity, subscription_id, payload, authz)
    rows = await list_member_subscriptions(db, subscription.organization_id)
    return to_member_subscription_read(next(row for row in rows if row[0].id == subscription.id))


@router.get(
    "/{organization_id}/member-subscription-charges/summary",
    response_model=MemberSubscriptionReceivablesSummaryRead,
)
async def member_subscription_receivables_summary_route(
    organization_id: UUID,
    as_of: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> MemberSubscriptionReceivablesSummaryRead:
    return await member_subscription_receivables_summary(db, organization_id, as_of)


@router.get("/{organization_id}/member-subscription-charges", response_model=list[MemberSubscriptionChargeRead])
async def list_member_subscription_charges_route(
    organization_id: UUID,
    subscription_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[MemberSubscriptionChargeRead]:
    return [
        to_member_subscription_charge_read(row)
        for row in await list_member_subscription_charges(db, organization_id, subscription_id)
    ]


@router.post(
    "/member-subscription-charges/{charge_id}/waive",
    response_model=MemberSubscriptionChargeWaiverRead,
)
async def waive_member_subscription_charge_route(
    charge_id: UUID,
    payload: MemberSubscriptionChargeWaiverCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionChargeWaiverRead:
    return await waive_member_subscription_charge(db, identity, charge_id, payload, authz)


@router.post(
    "/{organization_id}/member-subscription-charges/run",
    response_model=MemberSubscriptionChargeRunRead,
)
async def run_member_subscription_charges_route(
    organization_id: UUID,
    payload: MemberSubscriptionChargeRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionChargeRunRead:
    if payload.organization_id != organization_id:
        raise HTTPException(status_code=422, detail="organization_id mismatch")
    return await run_member_subscription_charge_generation(db, identity, payload, authz)


@router.post(
    "/{organization_id}/member-subscription-reminders/run",
    response_model=MemberSubscriptionReminderRunRead,
)
async def run_member_subscription_reminders_route(
    organization_id: UUID,
    payload: MemberSubscriptionReminderRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionReminderRunRead:
    if payload.organization_id != organization_id:
        raise HTTPException(status_code=422, detail="organization_id mismatch")
    return await run_member_subscription_reminders(db, identity, payload, authz)


@router.post(
    "/member-subscriptions/{subscription_id}/payments",
    response_model=MemberSubscriptionPaymentRead,
    status_code=201,
)
async def record_member_subscription_payment_route(
    subscription_id: UUID,
    payload: MemberSubscriptionPaymentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionPaymentRead:
    payment, subscription = await record_member_subscription_payment(db, identity, subscription_id, payload, authz)
    return MemberSubscriptionPaymentRead(
        id=payment.id,
        organization_id=payment.organization_id,
        subscription_id=payment.subscription_id,
        payment_plan_id=payment.payment_plan_id,
        amount=payment.amount,
        currency=payment.currency,
        provider=payment.provider,
        method=payment.method,
        external_payment_id=payment.external_payment_id,
        received_at=payment.received_at,
        status=payment.status,
        raw_reference=payment.raw_reference,
        notes=payment.notes,
        subscription_balance_amount=subscription.balance_amount,
        subscription_status=subscription.status,
    )


@router.post(
    "/member-subscriptions/{subscription_id}/payment-plans",
    response_model=MemberSubscriptionPaymentPlanRead,
    status_code=201,
)
async def create_member_subscription_payment_plan_route(
    subscription_id: UUID,
    payload: MemberSubscriptionPaymentPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionPaymentPlanRead:
    return await create_member_subscription_payment_plan(db, identity, subscription_id, payload, authz)


@router.get(
    "/{organization_id}/member-subscription-payment-plans",
    response_model=list[MemberSubscriptionPaymentPlanRead],
)
async def list_member_subscription_payment_plans_route(
    organization_id: UUID,
    subscription_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[MemberSubscriptionPaymentPlanRead]:
    return await list_member_subscription_payment_plans(db, organization_id, subscription_id)


@router.patch(
    "/member-subscription-payment-plans/{payment_plan_id}",
    response_model=MemberSubscriptionPaymentPlanRead,
)
async def update_member_subscription_payment_plan_route(
    payment_plan_id: UUID,
    payload: MemberSubscriptionPaymentPlanUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionPaymentPlanRead:
    return await update_member_subscription_payment_plan(db, identity, payment_plan_id, payload, authz)


@router.post(
    "/{organization_id}/member-subscription-renewal-campaigns",
    response_model=MemberSubscriptionRenewalCampaignRead,
    status_code=201,
)
async def create_member_subscription_renewal_campaign_route(
    organization_id: UUID,
    payload: MemberSubscriptionRenewalCampaignCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionRenewalCampaignRead:
    return await create_member_subscription_renewal_campaign(db, identity, organization_id, payload, authz)


@router.get(
    "/{organization_id}/member-subscription-renewal-campaigns",
    response_model=list[MemberSubscriptionRenewalCampaignRead],
)
async def list_member_subscription_renewal_campaigns_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[MemberSubscriptionRenewalCampaignRead]:
    return await list_member_subscription_renewal_campaigns(db, organization_id)


@router.post(
    "/{organization_id}/member-subscription-renewal-offers/run",
    response_model=MemberSubscriptionRenewalOfferRunRead,
)
async def run_member_subscription_renewal_offers_route(
    organization_id: UUID,
    payload: MemberSubscriptionRenewalOfferRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionRenewalOfferRunRead:
    return await run_member_subscription_renewal_offer_generation(db, identity, organization_id, payload, authz)


@router.get(
    "/{organization_id}/member-subscription-renewal-offers",
    response_model=list[MemberSubscriptionRenewalOfferRead],
)
async def list_member_subscription_renewal_offers_route(
    organization_id: UUID,
    campaign_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[MemberSubscriptionRenewalOfferRead]:
    return await list_member_subscription_renewal_offers(db, organization_id, campaign_id)


@router.post(
    "/member-subscription-renewal-offers/{offer_id}/accept",
    response_model=MemberSubscriptionRenewalOfferRead,
)
async def accept_member_subscription_renewal_offer_route(
    offer_id: UUID,
    payload: MemberSubscriptionRenewalOfferAcceptCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionRenewalOfferRead:
    return await accept_member_subscription_renewal_offer(db, identity, offer_id, payload, authz)


@router.post(
    "/{organization_id}/financial-aid-programs",
    response_model=OrganizationFinancialAidProgramRead,
    status_code=201,
)
async def create_organization_financial_aid_program_route(
    organization_id: UUID,
    payload: OrganizationFinancialAidProgramCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationFinancialAidProgramRead:
    return await create_organization_financial_aid_program(db, identity, organization_id, payload, authz)


@router.get("/{organization_id}/financial-aid-programs", response_model=list[OrganizationFinancialAidProgramRead])
async def list_organization_financial_aid_programs_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationFinancialAidProgramRead]:
    return await list_organization_financial_aid_programs(db, organization_id)


@router.post(
    "/{organization_id}/financial-aid-applications",
    response_model=OrganizationFinancialAidApplicationRead,
    status_code=201,
)
async def create_organization_financial_aid_application_route(
    organization_id: UUID,
    payload: OrganizationFinancialAidApplicationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationFinancialAidApplicationRead:
    return await create_organization_financial_aid_application(db, identity, organization_id, payload, authz)


@router.get("/{organization_id}/financial-aid-applications", response_model=list[OrganizationFinancialAidApplicationRead])
async def list_organization_financial_aid_applications_route(
    organization_id: UUID,
    program_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationFinancialAidApplicationRead]:
    return await list_organization_financial_aid_applications(db, organization_id, program_id)


@router.get("/{organization_id}/financial-aid-summary", response_model=OrganizationFinancialAidSummaryRead)
async def organization_financial_aid_summary_route(
    organization_id: UUID,
    program_id: UUID | None = Query(default=None),
    as_of: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> OrganizationFinancialAidSummaryRead:
    return await organization_financial_aid_summary(db, organization_id, program_id, as_of)


@router.post(
    "/{organization_id}/financial-aid-renewals",
    response_model=OrganizationFinancialAidRenewalRead,
    status_code=201,
)
async def create_organization_financial_aid_renewal_route(
    organization_id: UUID,
    payload: OrganizationFinancialAidRenewalCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationFinancialAidRenewalRead:
    return await create_organization_financial_aid_renewal(db, identity, organization_id, payload, authz)


@router.get("/{organization_id}/financial-aid-renewals", response_model=list[OrganizationFinancialAidRenewalRead])
async def list_organization_financial_aid_renewals_route(
    organization_id: UUID,
    application_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationFinancialAidRenewalRead]:
    return await list_organization_financial_aid_renewals(db, organization_id, application_id)


@router.patch(
    "/financial-aid-renewals/{renewal_id}/review",
    response_model=OrganizationFinancialAidRenewalRead,
)
async def review_organization_financial_aid_renewal_route(
    renewal_id: UUID,
    payload: OrganizationFinancialAidRenewalReview,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationFinancialAidRenewalRead:
    return await review_organization_financial_aid_renewal(db, identity, renewal_id, payload, authz)


@router.post(
    "/{organization_id}/financial-aid-appeals",
    response_model=OrganizationFinancialAidAppealRead,
    status_code=201,
)
async def create_organization_financial_aid_appeal_route(
    organization_id: UUID,
    payload: OrganizationFinancialAidAppealCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationFinancialAidAppealRead:
    return await create_organization_financial_aid_appeal(db, identity, organization_id, payload, authz)


@router.get("/{organization_id}/financial-aid-appeals", response_model=list[OrganizationFinancialAidAppealRead])
async def list_organization_financial_aid_appeals_route(
    organization_id: UUID,
    application_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationFinancialAidAppealRead]:
    return await list_organization_financial_aid_appeals(db, organization_id, application_id)


@router.patch(
    "/financial-aid-appeals/{appeal_id}/review",
    response_model=OrganizationFinancialAidAppealRead,
)
async def review_organization_financial_aid_appeal_route(
    appeal_id: UUID,
    payload: OrganizationFinancialAidAppealReview,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationFinancialAidAppealRead:
    return await review_organization_financial_aid_appeal(db, identity, appeal_id, payload, authz)


@router.patch(
    "/financial-aid-applications/{application_id}/review",
    response_model=OrganizationFinancialAidApplicationRead,
)
async def review_organization_financial_aid_application_route(
    application_id: UUID,
    payload: OrganizationFinancialAidApplicationReview,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationFinancialAidApplicationRead:
    return await review_organization_financial_aid_application(db, identity, application_id, payload, authz)


@router.get(
    "/member-subscriptions/{subscription_id}/statement",
    response_model=MemberSubscriptionStatementRead,
)
async def get_member_subscription_statement_route(
    subscription_id: UUID,
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionStatementRead:
    return await get_member_subscription_statement(
        db,
        identity,
        subscription_id,
        authz,
        period_start=period_start,
        period_end=period_end,
    )


@router.get(
    "/member-subscriptions/{subscription_id}/statement-artifact",
    response_model=MemberSubscriptionStatementArtifactRead,
)
async def export_member_subscription_statement_artifact_route(
    subscription_id: UUID,
    artifact_format: str = Query(default="txt", pattern="^(txt|csv)$"),
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionStatementArtifactRead:
    return await export_member_subscription_statement_artifact(
        db,
        identity,
        subscription_id,
        authz,
        artifact_format=artifact_format,
        period_start=period_start,
        period_end=period_end,
    )


@router.post(
    "/member-subscriptions/{subscription_id}/statement/send",
    response_model=MemberSubscriptionStatementSendRead,
)
async def send_member_subscription_statement_route(
    subscription_id: UUID,
    payload: MemberSubscriptionStatementSendCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionStatementSendRead:
    return await send_member_subscription_statement(db, identity, subscription_id, payload, authz)


@router.post(
    "/member-subscriptions/{subscription_id}/checkout-link",
    response_model=MemberSubscriptionCheckoutLinkRead,
)
async def create_member_subscription_checkout_link_route(
    subscription_id: UUID,
    provider: str = Query(default="mpesa", min_length=2, max_length=80),
    checkout_base_url: str = Query(default="/pay/sessions", min_length=1, max_length=800),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MemberSubscriptionCheckoutLinkRead:
    return await create_member_subscription_checkout_link(
        db,
        identity,
        subscription_id,
        provider,
        checkout_base_url,
        authz,
    )


@router.get(
    "/member-subscription-checkout-sessions/{session_id}",
    response_model=MemberSubscriptionHostedCheckoutRead,
)
async def get_member_subscription_checkout_session_route(
    session_id: str,
    subscription_id: UUID = Query(),
    provider: str = Query(default="mpesa", min_length=2, max_length=80),
    db: AsyncSession = Depends(get_db),
) -> MemberSubscriptionHostedCheckoutRead:
    return await get_member_subscription_hosted_checkout(db, session_id, subscription_id, provider)


@router.post(
    "/member-subscription-checkout-sessions/{session_id}/settle",
    response_model=MemberSubscriptionCheckoutSettlementRead,
)
async def settle_member_subscription_checkout_route(
    session_id: str,
    payload: MemberSubscriptionCheckoutSettlementCreate,
    db: AsyncSession = Depends(get_db),
) -> MemberSubscriptionCheckoutSettlementRead:
    return await settle_member_subscription_checkout(db, session_id, payload)


@router.post(
    "/{organization_id}/market-profiles",
    response_model=OrganizationMarketProfileRead,
    status_code=201,
)
async def create_market_profile_route(
    organization_id: UUID,
    payload: OrganizationMarketProfileCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationMarketProfileRead:
    return await create_organization_market_profile(db, identity, organization_id, payload, authz)


@router.get("/{organization_id}/market-profiles", response_model=list[OrganizationMarketProfileRead])
async def list_market_profiles_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationMarketProfileRead]:
    return await list_organization_market_profiles(db, organization_id)


@router.get(
    "/{organization_id}/market-profiles/summary",
    response_model=OrganizationMarketProfileSummaryRead,
)
async def market_profile_summary_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> OrganizationMarketProfileSummaryRead:
    return await organization_market_profile_summary(db, organization_id)


@router.post(
    "/{organization_id}/external-reports",
    response_model=OrganizationExternalReportRead,
    status_code=201,
)
async def create_external_report_route(
    organization_id: UUID,
    payload: OrganizationExternalReportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationExternalReportRead:
    return await create_organization_external_report(db, identity, organization_id, payload, authz)


@router.get(
    "/{organization_id}/external-reports/summary",
    response_model=OrganizationExternalReportSummaryRead,
)
async def external_report_summary_route(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> OrganizationExternalReportSummaryRead:
    return await organization_external_report_summary(db, organization_id)


@router.get("/{organization_id}/external-reports", response_model=list[OrganizationExternalReportRead])
async def list_external_reports_route(
    organization_id: UUID,
    status_filter: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationExternalReportRead]:
    return await list_organization_external_reports(db, organization_id, status_filter, target_type)


@router.patch(
    "/external-reports/{report_id}/status",
    response_model=OrganizationExternalReportRead,
)
async def update_external_report_status_route(
    report_id: UUID,
    payload: OrganizationExternalReportStatusUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OrganizationExternalReportRead:
    return await update_organization_external_report_status(db, identity, report_id, payload, authz)


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
