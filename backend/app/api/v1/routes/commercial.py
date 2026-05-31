from typing import Any
from datetime import date
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.commercial import (
    AccountingExportRead,
    AccountingSyncRead,
    CommercialInvoiceCheckoutSettlementCreate,
    CommercialInvoiceCheckoutSettlementRead,
    CommercialInvoiceHostedCheckoutRead,
    CommercialSummaryRead,
    CommercialInvoiceProviderCheckoutCreate,
    CommercialInvoiceProviderCheckoutRead,
    CommercialRefundCreate,
    CommercialRefundRead,
    CommercialSettlementPayoutCallbackCreate,
    CommercialSettlementPayoutCallbackRead,
    CommercialSettlementPayoutRead,
    CommercialTaxFilingRead,
    DonationCreate,
    DonationRead,
    DonorDashboardRead,
    DonorInteractionCreate,
    DonorInteractionRead,
    DonorProfileCreate,
    DonorProfileRead,
    DonorStewardshipPlanCreate,
    DonorStewardshipPlanRead,
    FinanceInvoiceCreate,
    FinanceInvoiceRead,
    FinancePaymentCreate,
    FinancePaymentRead,
    FinancialBudgetCreate,
    FinancialBudgetLineCreate,
    FinancialBudgetLineRead,
    FinancialBudgetRead,
    FinancialBudgetSummaryRead,
    FinancialForecastScenarioCreate,
    FinancialForecastScenarioRead,
    FinancialStatementCreate,
    FinancialStatementPackageRead,
    FundraisingCampaignCreate,
    FundraisingCampaignRead,
    GrantApplicationApprovalCreate,
    GrantApplicationApprovalDecision,
    GrantApplicationApprovalRead,
    GrantApplicationCreate,
    GrantApplicationRead,
    GrantDashboardRead,
    GrantOpportunityCreate,
    GrantOpportunityRead,
    GrantReportCreate,
    GrantReportRead,
    MerchandiseFulfillmentUpdate,
    MerchandiseOrderCreate,
    MerchandiseOrderRead,
    MerchandiseProductCreate,
    MerchandiseProductRead,
    MerchandiseStoreDashboardRead,
    PaymentSettlementRead,
    SponsorCreate,
    SponsorActivationCampaignCreate,
    SponsorActivationCampaignRead,
    SponsorActivationDashboardRead,
    SponsorActivationPlacementCreate,
    SponsorActivationPlacementRead,
    SponsorContentApprovalCreate,
    SponsorContentApprovalRead,
    SponsorContentAssetCreate,
    SponsorContentAssetRead,
    SponsorContentDashboardRead,
    SponsorCouponRedemptionCreate,
    SponsorCouponRedemptionRead,
    SponsorDigitalSignagePlaylistRead,
    SponsorDigitalSignagePlaybackCreate,
    SponsorDigitalSignagePlaybackRead,
    SponsorInteractionCreate,
    SponsorInteractionRead,
    SponsorPortalRead,
    SponsorRead,
    SponsorStewardshipDashboardRead,
    SponsorshipDashboardRead,
    SponsorshipAgreementCreate,
    SponsorshipAgreementRead,
    SponsorshipDeliverableMilestoneCreate,
    SponsorshipDeliverableMilestoneRead,
    TaxQuoteRead,
    ComplimentaryTicketCreate,
    TicketAccessDashboardRead,
    TicketBundleOfferCreate,
    TicketBundleOfferRead,
    TicketCheckIn,
    TicketOrderCreate,
    TicketOrderRead,
    TicketProductCreate,
    TicketProductRead,
    TicketRead,
    TicketResaleListingCreate,
    TicketResaleListingRead,
    TicketResalePurchaseCreate,
    TicketSeatAssignmentCreate,
    TicketSeatAssignmentRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.commercial import (
    accounting_export,
    check_in_ticket,
    commercial_summary,
    create_campaign,
    create_donor_interaction,
    create_donor_profile,
    create_donor_stewardship_plan,
    create_grant_application,
    create_grant_application_approval,
    create_grant_opportunity,
    create_grant_report,
    create_invoice,
    create_financial_budget,
    create_financial_budget_line,
    create_financial_forecast_scenario,
    create_merchandise_order,
    create_merchandise_product,
    create_commercial_invoice_provider_checkout,
    create_sponsor,
    create_sponsor_activation_campaign,
    create_sponsor_activation_placement,
    create_sponsor_content_asset,
    create_sponsor_interaction,
    create_sponsorship_milestone,
    create_sponsorship,
    create_ticket_bundle_offer,
    create_ticket_order,
    create_ticket_product,
    create_ticket_resale_listing,
    deliver_commercial_tax_filing,
    complete_donor_stewardship_plan,
    decide_grant_application_approval,
    donor_dashboard,
    execute_payment_settlement_payout,
    generate_financial_statement_package,
    get_commercial_invoice_hosted_checkout,
    ingest_commercial_invoice_payment_webhook,
    issue_complimentary_tickets,
    financial_budget_summary,
    list_commercial_settlement_payouts,
    list_campaigns,
    list_donations,
    list_donor_interactions,
    list_donor_profiles,
    list_donor_stewardship_plans,
    list_financial_budget_lines,
    list_financial_budgets,
    list_financial_forecast_scenarios,
    list_financial_statement_packages,
    list_grant_application_approvals,
    list_grant_applications,
    list_grant_opportunities,
    list_grant_reports,
    grant_application_approval_counts,
    list_invoices,
    list_commercial_payment_sessions,
    list_sponsors,
    list_sponsor_activation_campaigns,
    list_sponsor_activation_placements,
    list_sponsor_content_assets,
    list_sponsor_content_reviews,
    list_sponsor_coupon_redemptions,
    list_sponsor_interactions,
    list_sponsorship_milestones,
    list_sponsorships,
    list_ticket_bundle_offers,
    list_ticket_products,
    list_ticket_resale_listings,
    list_ticket_seat_assignments,
    list_tickets,
    grant_dashboard,
    list_merchandise_orders,
    list_merchandise_products,
    payment_settlement,
    purchase_ticket_resale_listing,
    record_donation,
    review_sponsor_content_asset,
    record_sponsor_coupon_redemption,
    record_sponsor_digital_signage_playback,
    record_payment,
    reconcile_commercial_settlement_payout_callback,
    refund_invoice,
    refund_ticket,
    settle_commercial_invoice_checkout,
    sponsor_portal,
    sponsor_activation_dashboard,
    sponsor_content_dashboard,
    sponsor_digital_signage_playlist,
    sponsorship_dashboard,
    sponsor_stewardship_dashboard,
    sync_accounting_export,
    tax_quote,
    ticket_access_dashboard,
    assign_ticket_seat,
    merchandise_order_read,
    merchandise_store_dashboard,
    update_merchandise_fulfillment,
    validate_commercial_payout_callback_signature,
    validate_commercial_invoice_payment_webhook_signature,
)

router = APIRouter(prefix="/commercial", tags=["commercial"])


def sponsor_read(sponsor) -> SponsorRead:
    return SponsorRead(**fields(sponsor, SponsorRead))


def sponsorship_read(agreement) -> SponsorshipAgreementRead:
    return SponsorshipAgreementRead(**fields(agreement, SponsorshipAgreementRead))


def campaign_read(campaign) -> FundraisingCampaignRead:
    return FundraisingCampaignRead(**fields(campaign, FundraisingCampaignRead))


def donation_read(donation) -> DonationRead:
    return DonationRead(**fields(donation, DonationRead))


def grant_opportunity_read(opportunity) -> GrantOpportunityRead:
    return GrantOpportunityRead(**fields(opportunity, GrantOpportunityRead))


async def grant_application_read(db: AsyncSession, application, opportunity=None) -> GrantApplicationRead:
    approval_status, pending, approved, rejected = await grant_application_approval_counts(db, application.id)
    return GrantApplicationRead(
        **fields(application, GrantApplicationRead),
        funder_name=opportunity.funder_name if opportunity else None,
        program_name=opportunity.program_name if opportunity else None,
        approval_status=approval_status,
        approval_pending_count=pending,
        approval_approved_count=approved,
        approval_rejected_count=rejected,
    )


def grant_report_read(report, application=None) -> GrantReportRead:
    return GrantReportRead(
        **fields(report, GrantReportRead),
        project_title=application.project_title if application else None,
    )


def merchandise_product_read(product) -> MerchandiseProductRead:
    return MerchandiseProductRead(**fields(product, MerchandiseProductRead))


def ticket_product_read(product) -> TicketProductRead:
    return TicketProductRead(**fields(product, TicketProductRead))


def ticket_read(ticket) -> TicketRead:
    return TicketRead(**fields(ticket, TicketRead))


def invoice_read(invoice) -> FinanceInvoiceRead:
    return FinanceInvoiceRead(**fields(invoice, FinanceInvoiceRead))


def payment_read(payment) -> FinancePaymentRead:
    return FinancePaymentRead(**fields(payment, FinancePaymentRead))


def order_read(order, tickets) -> TicketOrderRead:
    return TicketOrderRead(
        id=order.id,
        organization_id=order.organization_id,
        ticket_product_id=order.ticket_product_id,
        buyer_name=order.buyer_name,
        buyer_email=order.buyer_email,
        quantity=order.quantity,
        total_amount=order.total_amount,
        currency=order.currency,
        external_payment_reference=order.external_payment_reference,
        status=order.status,
        ticket_ids=[ticket.id for ticket in tickets],
    )


def fields(model, schema_type) -> dict:
    return {name: getattr(model, name) for name in schema_type.model_fields if hasattr(model, name)}


@router.post("/sponsors", response_model=SponsorRead, status_code=status.HTTP_201_CREATED)
async def create_sponsor_route(
    payload: SponsorCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorRead:
    return sponsor_read(await create_sponsor(db, identity, payload, authz))


@router.get("/sponsors", response_model=list[SponsorRead])
async def list_sponsors_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorRead]:
    return [sponsor_read(sponsor) for sponsor in await list_sponsors(db, organization_id)]


@router.post("/sponsorships", response_model=SponsorshipAgreementRead, status_code=status.HTTP_201_CREATED)
async def create_sponsorship_route(
    payload: SponsorshipAgreementCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorshipAgreementRead:
    return sponsorship_read(await create_sponsorship(db, identity, payload, authz))


@router.get("/sponsorships", response_model=list[SponsorshipAgreementRead])
async def list_sponsorships_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorshipAgreementRead]:
    return [
        sponsorship_read(agreement)
        for agreement in await list_sponsorships(db, organization_id)
    ]


@router.post(
    "/sponsorship-milestones",
    response_model=SponsorshipDeliverableMilestoneRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_sponsorship_milestone_route(
    payload: SponsorshipDeliverableMilestoneCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorshipDeliverableMilestoneRead:
    return await create_sponsorship_milestone(db, identity, payload, authz)


@router.get("/sponsorship-milestones", response_model=list[SponsorshipDeliverableMilestoneRead])
async def list_sponsorship_milestones_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorshipDeliverableMilestoneRead]:
    return await list_sponsorship_milestones(db, organization_id)


@router.post(
    "/sponsor-interactions",
    response_model=SponsorInteractionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_sponsor_interaction_route(
    payload: SponsorInteractionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorInteractionRead:
    return await create_sponsor_interaction(db, identity, payload, authz)


@router.get("/sponsor-interactions", response_model=list[SponsorInteractionRead])
async def list_sponsor_interactions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorInteractionRead]:
    return await list_sponsor_interactions(db, organization_id)


@router.get("/sponsor-stewardship-dashboard", response_model=SponsorStewardshipDashboardRead)
async def sponsor_stewardship_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> SponsorStewardshipDashboardRead:
    return await sponsor_stewardship_dashboard(db, organization_id)


@router.post(
    "/sponsor-activations",
    response_model=SponsorActivationCampaignRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_sponsor_activation_route(
    payload: SponsorActivationCampaignCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorActivationCampaignRead:
    return await create_sponsor_activation_campaign(db, identity, payload, authz)


@router.get("/sponsor-activations", response_model=list[SponsorActivationCampaignRead])
async def list_sponsor_activation_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorActivationCampaignRead]:
    return await list_sponsor_activation_campaigns(db, organization_id)


@router.post(
    "/sponsor-coupon-redemptions",
    response_model=SponsorCouponRedemptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_sponsor_coupon_redemption_route(
    payload: SponsorCouponRedemptionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorCouponRedemptionRead:
    return await record_sponsor_coupon_redemption(db, identity, payload, authz)


@router.get("/sponsor-coupon-redemptions", response_model=list[SponsorCouponRedemptionRead])
async def list_sponsor_coupon_redemptions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorCouponRedemptionRead]:
    return await list_sponsor_coupon_redemptions(db, organization_id)


@router.get("/sponsor-activation-dashboard", response_model=SponsorActivationDashboardRead)
async def sponsor_activation_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> SponsorActivationDashboardRead:
    return await sponsor_activation_dashboard(db, organization_id)


@router.post(
    "/sponsor-content-assets",
    response_model=SponsorContentAssetRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_sponsor_content_asset_route(
    payload: SponsorContentAssetCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorContentAssetRead:
    return await create_sponsor_content_asset(db, identity, payload, authz)


@router.get("/sponsor-content-assets", response_model=list[SponsorContentAssetRead])
async def list_sponsor_content_assets_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorContentAssetRead]:
    return await list_sponsor_content_assets(db, organization_id)


@router.post(
    "/sponsor-content-approvals",
    response_model=SponsorContentApprovalRead,
    status_code=status.HTTP_201_CREATED,
)
async def review_sponsor_content_asset_route(
    payload: SponsorContentApprovalCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorContentApprovalRead:
    return await review_sponsor_content_asset(db, identity, payload, authz)


@router.get("/sponsor-content-approvals", response_model=list[SponsorContentApprovalRead])
async def list_sponsor_content_reviews_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorContentApprovalRead]:
    return await list_sponsor_content_reviews(db, organization_id)


@router.post(
    "/sponsor-placements",
    response_model=SponsorActivationPlacementRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_sponsor_activation_placement_route(
    payload: SponsorActivationPlacementCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorActivationPlacementRead:
    return await create_sponsor_activation_placement(db, identity, payload, authz)


@router.get("/sponsor-placements", response_model=list[SponsorActivationPlacementRead])
async def list_sponsor_activation_placements_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorActivationPlacementRead]:
    return await list_sponsor_activation_placements(db, organization_id)


@router.get("/sponsor-content-dashboard", response_model=SponsorContentDashboardRead)
async def sponsor_content_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> SponsorContentDashboardRead:
    return await sponsor_content_dashboard(db, organization_id)


@router.get("/sponsor-digital-signage-playlist", response_model=SponsorDigitalSignagePlaylistRead)
async def sponsor_digital_signage_playlist_route(
    organization_id: UUID = Query(),
    screen_name: str = Query(default="Main scoreboard", max_length=120),
    location_name: str | None = Query(default=None, max_length=180),
    event_id: UUID | None = Query(default=None),
    slot_count: int = Query(default=12, ge=1, le=60),
    slot_seconds: int = Query(default=12, ge=5, le=120),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorDigitalSignagePlaylistRead:
    return await sponsor_digital_signage_playlist(
        db,
        identity,
        organization_id,
        authz,
        screen_name=screen_name,
        location_name=location_name,
        event_id=event_id,
        slot_count=slot_count,
        slot_seconds=slot_seconds,
    )


@router.post(
    "/sponsor-digital-signage-playback",
    response_model=SponsorDigitalSignagePlaybackRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_sponsor_digital_signage_playback_route(
    payload: SponsorDigitalSignagePlaybackCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorDigitalSignagePlaybackRead:
    return await record_sponsor_digital_signage_playback(db, identity, payload, authz)


@router.post("/campaigns", response_model=FundraisingCampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign_route(
    payload: FundraisingCampaignCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FundraisingCampaignRead:
    return campaign_read(await create_campaign(db, identity, payload, authz))


@router.get("/campaigns", response_model=list[FundraisingCampaignRead])
async def list_campaigns_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FundraisingCampaignRead]:
    return [campaign_read(campaign) for campaign in await list_campaigns(db, organization_id)]


@router.post("/donations", response_model=DonationRead, status_code=status.HTTP_201_CREATED)
async def record_donation_route(
    payload: DonationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DonationRead:
    return donation_read(await record_donation(db, identity, payload, authz))


@router.get("/donations", response_model=list[DonationRead])
async def list_donations_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[DonationRead]:
    return [donation_read(donation) for donation in await list_donations(db, organization_id)]


@router.post("/donors", response_model=DonorProfileRead, status_code=status.HTTP_201_CREATED)
async def create_donor_profile_route(
    payload: DonorProfileCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DonorProfileRead:
    return await create_donor_profile(db, identity, payload, authz)


@router.get("/donors", response_model=list[DonorProfileRead])
async def list_donor_profiles_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[DonorProfileRead]:
    return await list_donor_profiles(db, organization_id)


@router.post("/donor-interactions", response_model=DonorInteractionRead, status_code=status.HTTP_201_CREATED)
async def create_donor_interaction_route(
    payload: DonorInteractionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DonorInteractionRead:
    return await create_donor_interaction(db, identity, payload, authz)


@router.get("/donor-interactions", response_model=list[DonorInteractionRead])
async def list_donor_interactions_route(
    organization_id: UUID = Query(),
    donor_profile_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[DonorInteractionRead]:
    return await list_donor_interactions(db, organization_id, donor_profile_id)


@router.post("/donor-stewardship-plans", response_model=DonorStewardshipPlanRead, status_code=status.HTTP_201_CREATED)
async def create_donor_stewardship_plan_route(
    payload: DonorStewardshipPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DonorStewardshipPlanRead:
    return await create_donor_stewardship_plan(db, identity, payload, authz)


@router.get("/donor-stewardship-plans", response_model=list[DonorStewardshipPlanRead])
async def list_donor_stewardship_plans_route(
    organization_id: UUID = Query(),
    donor_profile_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[DonorStewardshipPlanRead]:
    return await list_donor_stewardship_plans(db, organization_id, donor_profile_id)


@router.patch("/donor-stewardship-plans/{plan_id}/complete", response_model=DonorStewardshipPlanRead)
async def complete_donor_stewardship_plan_route(
    plan_id: UUID,
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DonorStewardshipPlanRead:
    return await complete_donor_stewardship_plan(db, identity, plan_id, organization_id, authz)


@router.get("/donor-dashboard", response_model=DonorDashboardRead)
async def donor_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> DonorDashboardRead:
    return await donor_dashboard(db, organization_id)


@router.post("/grants/opportunities", response_model=GrantOpportunityRead, status_code=status.HTTP_201_CREATED)
async def create_grant_opportunity_route(
    payload: GrantOpportunityCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantOpportunityRead:
    return grant_opportunity_read(await create_grant_opportunity(db, identity, payload, authz))


@router.get("/grants/opportunities", response_model=list[GrantOpportunityRead])
async def list_grant_opportunities_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[GrantOpportunityRead]:
    return [
        grant_opportunity_read(opportunity)
        for opportunity in await list_grant_opportunities(db, organization_id)
    ]


@router.post("/grants/applications", response_model=GrantApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_grant_application_route(
    payload: GrantApplicationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantApplicationRead:
    application = await create_grant_application(db, identity, payload, authz)
    opportunity = await list_grant_opportunities(db, payload.organization_id)
    opportunity_by_id = {item.id: item for item in opportunity}
    return await grant_application_read(db, application, opportunity_by_id.get(application.grant_opportunity_id))


@router.get("/grants/applications", response_model=list[GrantApplicationRead])
async def list_grant_applications_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[GrantApplicationRead]:
    return [
        await grant_application_read(db, application, opportunity)
        for application, opportunity in await list_grant_applications(db, organization_id)
    ]


@router.post("/grants/application-approvals", response_model=GrantApplicationApprovalRead, status_code=status.HTTP_201_CREATED)
async def create_grant_application_approval_route(
    payload: GrantApplicationApprovalCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantApplicationApprovalRead:
    return await create_grant_application_approval(db, identity, payload, authz)


@router.get("/grants/application-approvals", response_model=list[GrantApplicationApprovalRead])
async def list_grant_application_approvals_route(
    organization_id: UUID = Query(),
    grant_application_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[GrantApplicationApprovalRead]:
    return await list_grant_application_approvals(db, organization_id, grant_application_id)


@router.patch("/grants/application-approvals/{approval_id}", response_model=GrantApplicationApprovalRead)
async def decide_grant_application_approval_route(
    approval_id: UUID,
    payload: GrantApplicationApprovalDecision,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantApplicationApprovalRead:
    return await decide_grant_application_approval(db, identity, approval_id, payload, authz)


@router.post("/grants/reports", response_model=GrantReportRead, status_code=status.HTTP_201_CREATED)
async def create_grant_report_route(
    payload: GrantReportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantReportRead:
    report = await create_grant_report(db, identity, payload, authz)
    applications = await list_grant_applications(db, payload.organization_id)
    application_by_id = {application.id: application for application, _ in applications}
    return grant_report_read(report, application_by_id.get(report.grant_application_id))


@router.get("/grants/reports", response_model=list[GrantReportRead])
async def list_grant_reports_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[GrantReportRead]:
    return [
        grant_report_read(report, application)
        for report, application in await list_grant_reports(db, organization_id)
    ]


@router.get("/grants/dashboard", response_model=GrantDashboardRead)
async def grant_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> GrantDashboardRead:
    return await grant_dashboard(db, organization_id)


@router.post("/merchandise/products", response_model=MerchandiseProductRead, status_code=status.HTTP_201_CREATED)
async def create_merchandise_product_route(
    payload: MerchandiseProductCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MerchandiseProductRead:
    return merchandise_product_read(await create_merchandise_product(db, identity, payload, authz))


@router.get("/merchandise/products", response_model=list[MerchandiseProductRead])
async def list_merchandise_products_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[MerchandiseProductRead]:
    return [
        merchandise_product_read(product)
        for product in await list_merchandise_products(db, organization_id)
    ]


@router.post("/merchandise/orders", response_model=MerchandiseOrderRead, status_code=status.HTTP_201_CREATED)
async def create_merchandise_order_route(
    payload: MerchandiseOrderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MerchandiseOrderRead:
    order, lines, products = await create_merchandise_order(db, identity, payload, authz)
    return merchandise_order_read(order, lines, products)


@router.get("/merchandise/orders", response_model=list[MerchandiseOrderRead])
async def list_merchandise_orders_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[MerchandiseOrderRead]:
    return [
        merchandise_order_read(order, lines, products)
        for order, lines, products in await list_merchandise_orders(db, organization_id)
    ]


@router.patch("/merchandise/orders/{order_id}/fulfillment", response_model=MerchandiseOrderRead)
async def update_merchandise_fulfillment_route(
    order_id: UUID,
    payload: MerchandiseFulfillmentUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MerchandiseOrderRead:
    order, lines, products = await update_merchandise_fulfillment(db, identity, order_id, payload, authz)
    return merchandise_order_read(order, lines, products)


@router.get("/merchandise/dashboard", response_model=MerchandiseStoreDashboardRead)
async def merchandise_store_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> MerchandiseStoreDashboardRead:
    return await merchandise_store_dashboard(db, organization_id)


@router.post("/tickets/products", response_model=TicketProductRead, status_code=status.HTTP_201_CREATED)
async def create_ticket_product_route(
    payload: TicketProductCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketProductRead:
    return ticket_product_read(await create_ticket_product(db, identity, payload, authz))


@router.get("/tickets/products", response_model=list[TicketProductRead])
async def list_ticket_products_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[TicketProductRead]:
    return [
        ticket_product_read(product)
        for product in await list_ticket_products(db, organization_id)
    ]


@router.post("/tickets/bundles", response_model=TicketBundleOfferRead, status_code=status.HTTP_201_CREATED)
async def create_ticket_bundle_offer_route(
    payload: TicketBundleOfferCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketBundleOfferRead:
    return await create_ticket_bundle_offer(db, identity, payload, authz)


@router.get("/tickets/bundles", response_model=list[TicketBundleOfferRead])
async def list_ticket_bundle_offers_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[TicketBundleOfferRead]:
    return await list_ticket_bundle_offers(db, organization_id)


@router.post("/tickets/orders", response_model=TicketOrderRead, status_code=status.HTTP_201_CREATED)
async def create_ticket_order_route(
    payload: TicketOrderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketOrderRead:
    order, tickets = await create_ticket_order(db, identity, payload, authz)
    return order_read(order, tickets)


@router.post("/tickets/complimentary", response_model=TicketOrderRead, status_code=status.HTTP_201_CREATED)
async def issue_complimentary_tickets_route(
    payload: ComplimentaryTicketCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketOrderRead:
    order, tickets = await issue_complimentary_tickets(db, identity, payload, authz)
    return order_read(order, tickets)


@router.get("/tickets", response_model=list[TicketRead])
async def list_tickets_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[TicketRead]:
    return [ticket_read(ticket) for ticket in await list_tickets(db, organization_id)]


@router.post("/tickets/seats", response_model=TicketSeatAssignmentRead, status_code=status.HTTP_201_CREATED)
async def assign_ticket_seat_route(
    payload: TicketSeatAssignmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketSeatAssignmentRead:
    return await assign_ticket_seat(db, identity, payload, authz)


@router.get("/tickets/seats", response_model=list[TicketSeatAssignmentRead])
async def list_ticket_seat_assignments_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[TicketSeatAssignmentRead]:
    return await list_ticket_seat_assignments(db, organization_id)


@router.post("/tickets/resale-listings", response_model=TicketResaleListingRead, status_code=status.HTTP_201_CREATED)
async def create_ticket_resale_listing_route(
    payload: TicketResaleListingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketResaleListingRead:
    return await create_ticket_resale_listing(db, identity, payload, authz)


@router.get("/tickets/resale-listings", response_model=list[TicketResaleListingRead])
async def list_ticket_resale_listings_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[TicketResaleListingRead]:
    return await list_ticket_resale_listings(db, organization_id)


@router.post("/tickets/resale-listings/{listing_id}/purchase", response_model=TicketResaleListingRead)
async def purchase_ticket_resale_listing_route(
    listing_id: UUID,
    payload: TicketResalePurchaseCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketResaleListingRead:
    return await purchase_ticket_resale_listing(db, identity, listing_id, payload, authz)


@router.get("/tickets/access-dashboard", response_model=TicketAccessDashboardRead)
async def ticket_access_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> TicketAccessDashboardRead:
    return await ticket_access_dashboard(db, organization_id)


@router.patch("/tickets/{ticket_id}/check-in", response_model=TicketRead)
async def check_in_ticket_route(
    ticket_id: UUID,
    payload: TicketCheckIn,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketRead:
    return ticket_read(await check_in_ticket(db, identity, ticket_id, payload, authz))


@router.post("/tickets/{ticket_id}/refund", response_model=CommercialRefundRead)
async def refund_ticket_route(
    ticket_id: UUID,
    payload: CommercialRefundCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialRefundRead:
    return await refund_ticket(db, identity, ticket_id, payload, authz)


@router.post("/invoices", response_model=FinanceInvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice_route(
    payload: FinanceInvoiceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinanceInvoiceRead:
    return invoice_read(await create_invoice(db, identity, payload, authz))


@router.get("/invoices", response_model=list[FinanceInvoiceRead])
async def list_invoices_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FinanceInvoiceRead]:
    return [invoice_read(invoice) for invoice in await list_invoices(db, organization_id)]


@router.get(
    "/invoice-checkout-sessions/{session_id}",
    response_model=CommercialInvoiceHostedCheckoutRead,
)
async def get_commercial_invoice_checkout_session_route(
    session_id: str,
    invoice_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceHostedCheckoutRead:
    return await get_commercial_invoice_hosted_checkout(db, session_id, invoice_id, provider)


@router.post(
    "/invoice-checkout-sessions/{session_id}/provider-session",
    response_model=CommercialInvoiceProviderCheckoutRead,
)
async def create_commercial_invoice_provider_checkout_route(
    session_id: str,
    payload: CommercialInvoiceProviderCheckoutCreate,
    invoice_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceProviderCheckoutRead:
    return await create_commercial_invoice_provider_checkout(db, session_id, invoice_id, provider, payload)


@router.get("/payment-sessions", response_model=list[CommercialInvoiceProviderCheckoutRead])
async def list_commercial_payment_sessions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[CommercialInvoiceProviderCheckoutRead]:
    return await list_commercial_payment_sessions(db, organization_id)


@router.post(
    "/invoice-checkout-sessions/{session_id}/settle",
    response_model=CommercialInvoiceCheckoutSettlementRead,
)
async def settle_commercial_invoice_checkout_route(
    session_id: str,
    payload: CommercialInvoiceCheckoutSettlementCreate,
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceCheckoutSettlementRead:
    return await settle_commercial_invoice_checkout(db, session_id, payload)


@router.post(
    "/invoice-payment-webhooks",
    response_model=CommercialInvoiceCheckoutSettlementRead,
)
async def commercial_invoice_payment_webhook_route(
    request: Request,
    payload: dict[str, Any],
    provider: str | None = Query(default=None),
    x_afrolete_commercial_timestamp: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Timestamp",
    ),
    x_afrolete_commercial_signature: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Signature",
    ),
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceCheckoutSettlementRead:
    signature_required, signature_validated = await validate_commercial_invoice_payment_webhook_signature(
        await request.body(),
        x_afrolete_commercial_timestamp,
        x_afrolete_commercial_signature,
    )
    return await ingest_commercial_invoice_payment_webhook(
        db,
        payload,
        provider_hint=provider,
        signature_required=signature_required,
        signature_validated=signature_validated,
    )


@router.post("/invoices/{invoice_id}/refund", response_model=CommercialRefundRead)
async def refund_invoice_route(
    invoice_id: UUID,
    payload: CommercialRefundCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialRefundRead:
    return await refund_invoice(db, identity, invoice_id, payload, authz)


@router.post("/payments", response_model=FinancePaymentRead, status_code=status.HTTP_201_CREATED)
async def record_payment_route(
    payload: FinancePaymentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinancePaymentRead:
    return payment_read(await record_payment(db, identity, payload, authz))


@router.post("/budgets", response_model=FinancialBudgetRead, status_code=status.HTTP_201_CREATED)
async def create_financial_budget_route(
    payload: FinancialBudgetCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinancialBudgetRead:
    return await create_financial_budget(db, identity, payload, authz)


@router.get("/budgets", response_model=list[FinancialBudgetRead])
async def list_financial_budgets_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FinancialBudgetRead]:
    return await list_financial_budgets(db, organization_id)


@router.post("/budgets/lines", response_model=FinancialBudgetLineRead, status_code=status.HTTP_201_CREATED)
async def create_financial_budget_line_route(
    payload: FinancialBudgetLineCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinancialBudgetLineRead:
    return await create_financial_budget_line(db, identity, payload, authz)


@router.get("/budgets/{budget_id}/lines", response_model=list[FinancialBudgetLineRead])
async def list_financial_budget_lines_route(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FinancialBudgetLineRead]:
    return await list_financial_budget_lines(db, budget_id)


@router.post("/budgets/scenarios", response_model=FinancialForecastScenarioRead, status_code=status.HTTP_201_CREATED)
async def create_financial_forecast_scenario_route(
    payload: FinancialForecastScenarioCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinancialForecastScenarioRead:
    return await create_financial_forecast_scenario(db, identity, payload, authz)


@router.get("/budgets/{budget_id}/scenarios", response_model=list[FinancialForecastScenarioRead])
async def list_financial_forecast_scenarios_route(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FinancialForecastScenarioRead]:
    return await list_financial_forecast_scenarios(db, budget_id)


@router.get("/budgets/{budget_id}/summary", response_model=FinancialBudgetSummaryRead)
async def financial_budget_summary_route(
    budget_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> FinancialBudgetSummaryRead:
    return await financial_budget_summary(db, organization_id, budget_id)


@router.post("/financial-statements", response_model=FinancialStatementPackageRead, status_code=status.HTTP_201_CREATED)
async def generate_financial_statement_package_route(
    payload: FinancialStatementCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinancialStatementPackageRead:
    return await generate_financial_statement_package(db, identity, payload, authz)


@router.get("/financial-statements", response_model=list[FinancialStatementPackageRead])
async def list_financial_statement_packages_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FinancialStatementPackageRead]:
    return await list_financial_statement_packages(db, organization_id)


@router.get("/tax-quote", response_model=TaxQuoteRead)
async def tax_quote_route(
    organization_id: UUID = Query(),
    subtotal: Decimal = Query(ge=0),
    tax_rate: Decimal = Query(default=Decimal("0"), ge=0, le=100),
    jurisdiction: str = Query(default="local"),
    reverse_charge: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> TaxQuoteRead:
    return await tax_quote(db, organization_id, subtotal, tax_rate, jurisdiction, reverse_charge)


@router.post("/tax-filing/deliver", response_model=CommercialTaxFilingRead)
async def deliver_commercial_tax_filing_route(
    organization_id: UUID = Query(),
    period_start: date = Query(),
    period_end: date = Query(),
    jurisdiction: str = Query(default="KE", min_length=2, max_length=8),
    tax_rate: Decimal = Query(default=Decimal("0"), ge=0, le=100),
    reverse_charge: bool = Query(default=False),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialTaxFilingRead:
    return await deliver_commercial_tax_filing(
        db,
        identity,
        organization_id,
        period_start,
        period_end,
        jurisdiction,
        tax_rate,
        reverse_charge,
        authz,
    )


@router.get("/settlements", response_model=PaymentSettlementRead)
async def payment_settlement_route(
    organization_id: UUID = Query(),
    provider: str = Query(default="manual"),
    fee_rate: Decimal = Query(default=Decimal("2.90"), ge=0, le=100),
    fixed_fee: Decimal = Query(default=Decimal("0.30"), ge=0),
    db: AsyncSession = Depends(get_db),
) -> PaymentSettlementRead:
    return await payment_settlement(db, organization_id, provider, fee_rate, fixed_fee)


@router.post("/settlements/payout", response_model=CommercialSettlementPayoutRead)
async def execute_payment_settlement_payout_route(
    organization_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    fee_rate: Decimal = Query(default=Decimal("2.90"), ge=0, le=100),
    fixed_fee: Decimal = Query(default=Decimal("0.30"), ge=0),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialSettlementPayoutRead:
    return await execute_payment_settlement_payout(db, identity, organization_id, provider, fee_rate, fixed_fee, authz)


@router.get("/settlements/payouts", response_model=list[CommercialSettlementPayoutRead])
async def list_commercial_settlement_payouts_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[CommercialSettlementPayoutRead]:
    return await list_commercial_settlement_payouts(db, organization_id)


@router.post("/settlements/payout-callbacks", response_model=CommercialSettlementPayoutCallbackRead)
async def commercial_settlement_payout_callback_route(
    request: Request,
    payload: CommercialSettlementPayoutCallbackCreate,
    x_afrolete_commercial_payout_timestamp: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Payout-Timestamp",
    ),
    x_afrolete_commercial_payout_signature: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Payout-Signature",
    ),
    db: AsyncSession = Depends(get_db),
) -> CommercialSettlementPayoutCallbackRead:
    signature_required, signature_validated = await validate_commercial_payout_callback_signature(
        await request.body(),
        x_afrolete_commercial_payout_timestamp,
        x_afrolete_commercial_payout_signature,
    )
    return await reconcile_commercial_settlement_payout_callback(
        db,
        payload,
        signature_required=signature_required,
        signature_validated=signature_validated,
    )


@router.get("/accounting-export", response_model=AccountingExportRead)
async def accounting_export_route(
    organization_id: UUID = Query(),
    system: str = Query(default="generic"),
    basis: str = Query(default="cash"),
    db: AsyncSession = Depends(get_db),
) -> AccountingExportRead:
    return await accounting_export(db, organization_id, system, basis)


@router.post("/accounting-export/sync", response_model=AccountingSyncRead)
async def sync_accounting_export_route(
    organization_id: UUID = Query(),
    system: str = Query(default="generic"),
    basis: str = Query(default="cash"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AccountingSyncRead:
    return await sync_accounting_export(db, identity, organization_id, system, basis, authz)


@router.get("/sponsorship-dashboard", response_model=list[SponsorshipDashboardRead])
async def sponsorship_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorshipDashboardRead]:
    return await sponsorship_dashboard(db, organization_id)


@router.get("/sponsor-portal", response_model=SponsorPortalRead)
async def sponsor_portal_route(
    organization_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> SponsorPortalRead:
    return await sponsor_portal(db, identity, organization_id)


@router.get("/summary", response_model=CommercialSummaryRead)
async def commercial_summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> CommercialSummaryRead:
    return await commercial_summary(db, organization_id)
