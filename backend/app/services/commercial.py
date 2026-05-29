import json
import time
from typing import Any
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from decimal import InvalidOperation
import hmac
from hashlib import sha256
from re import sub
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.commercial import (
    CommercialPaymentSession,
    CommercialSettlementPayout,
    Donation,
    FinanceInvoice,
    FinancePayment,
    FundraisingCampaign,
    GrantApplication,
    GrantOpportunity,
    GrantReport,
    MerchandiseOrder,
    MerchandiseOrderLine,
    MerchandiseProduct,
    Sponsor,
    SponsorActivationCampaign,
    SponsorActivationPlacement,
    SponsorContentApprovalReview,
    SponsorContentAsset,
    SponsorCouponRedemption,
    SponsorInteractionLog,
    SponsorshipAgreement,
    SponsorshipDeliverableMilestone,
    Ticket,
    TicketOrder,
    TicketProduct,
)
from app.models.community import FanEngagementChallenge, SupporterProfile
from app.models.enums import CommercialStatus, TicketStatus
from app.models.event import Event
from app.models.organization import Organization
from app.models.team import Team
from app.schemas.commercial import (
    AccountingExportRead,
    AccountingExportRow,
    AccountingSyncRead,
    CommercialInvoiceCheckoutSettlementCreate,
    CommercialInvoiceCheckoutSettlementRead,
    CommercialInvoiceHostedCheckoutRead,
    CommercialInvoicePaymentWebhookCreate,
    CommercialInvoiceProviderCheckoutCreate,
    CommercialInvoiceProviderCheckoutRead,
    CommercialSummaryRead,
    CommercialRefundCreate,
    CommercialRefundRead,
    CommercialSettlementPayoutCallbackCreate,
    CommercialSettlementPayoutCallbackRead,
    CommercialSettlementPayoutRead,
    CommercialTaxFilingRead,
    DonationCreate,
    FinanceInvoiceCreate,
    FinancePaymentCreate,
    FundraisingCampaignCreate,
    GrantApplicationCreate,
    GrantDashboardRead,
    GrantOpportunityCreate,
    GrantReportCreate,
    MerchandiseFulfillmentUpdate,
    MerchandiseOrderCreate,
    MerchandiseOrderLineRead,
    MerchandiseOrderRead,
    MerchandiseProductCreate,
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
    SponsorInteractionCreate,
    SponsorInteractionRead,
    SponsorRenewalForecastRead,
    SponsorStewardshipDashboardRead,
    SponsorPortalAgreementRead,
    SponsorPortalInvoiceRead,
    SponsorPortalRead,
    SponsorPortalSponsorRead,
    SponsorPortalSummaryRead,
    SponsorshipDashboardRead,
    SponsorshipAgreementCreate,
    SponsorshipDeliverableMilestoneCreate,
    SponsorshipDeliverableMilestoneRead,
    TaxQuoteRead,
    TicketCheckIn,
    TicketOrderCreate,
    TicketProductCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.secrets import resolve_secret


async def ensure_manage_commercial(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_sponsor(db: AsyncSession, identity: CurrentIdentity, payload: SponsorCreate, authz: AuthorizationService) -> Sponsor:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    sponsor = Sponsor(**payload.model_dump())
    db.add(sponsor)
    await db.commit()
    await db.refresh(sponsor)
    return sponsor


async def list_sponsors(db: AsyncSession, organization_id: UUID) -> list[Sponsor]:
    return list((await db.scalars(select(Sponsor).where(Sponsor.organization_id == organization_id).order_by(Sponsor.name))).all())


async def create_sponsorship(db: AsyncSession, identity: CurrentIdentity, payload: SponsorshipAgreementCreate, authz: AuthorizationService) -> SponsorshipAgreement:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    if payload.event_id is not None:
        await get_event_for_organization(db, payload.event_id, payload.organization_id)
    agreement = SponsorshipAgreement(**payload.model_dump())
    db.add(agreement)
    await db.commit()
    await db.refresh(agreement)
    return agreement


async def list_sponsorships(db: AsyncSession, organization_id: UUID) -> list[SponsorshipAgreement]:
    return list((await db.scalars(select(SponsorshipAgreement).where(SponsorshipAgreement.organization_id == organization_id).order_by(SponsorshipAgreement.created_at.desc()))).all())


async def create_sponsorship_milestone(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SponsorshipDeliverableMilestoneCreate,
    authz: AuthorizationService,
) -> SponsorshipDeliverableMilestoneRead:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    agreement = await get_sponsorship_for_organization(db, payload.sponsorship_agreement_id, payload.organization_id)
    if agreement.sponsor_id != payload.sponsor_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agreement belongs to another sponsor")
    milestone = SponsorshipDeliverableMilestone(**payload.model_dump())
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return await sponsorship_milestone_read(db, milestone)


async def list_sponsorship_milestones(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SponsorshipDeliverableMilestoneRead]:
    milestones = list(
        (
            await db.scalars(
                select(SponsorshipDeliverableMilestone)
                .where(SponsorshipDeliverableMilestone.organization_id == organization_id)
                .order_by(SponsorshipDeliverableMilestone.due_on.is_(None), SponsorshipDeliverableMilestone.due_on)
            )
        ).all()
    )
    return [await sponsorship_milestone_read(db, milestone) for milestone in milestones]


async def create_sponsor_interaction(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SponsorInteractionCreate,
    authz: AuthorizationService,
) -> SponsorInteractionRead:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    if payload.sponsorship_agreement_id is not None:
        agreement = await get_sponsorship_for_organization(db, payload.sponsorship_agreement_id, payload.organization_id)
        if agreement.sponsor_id != payload.sponsor_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agreement belongs to another sponsor")
    interaction = SponsorInteractionLog(
        **payload.model_dump(exclude={"occurred_at", "contact_email", "sentiment"}),
        contact_email=payload.contact_email.strip().lower() if payload.contact_email else None,
        sentiment=payload.sentiment.strip().lower(),
        occurred_at=payload.occurred_at or datetime.now(UTC),
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return await sponsor_interaction_read(db, interaction)


async def list_sponsor_interactions(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SponsorInteractionRead]:
    interactions = list(
        (
            await db.scalars(
                select(SponsorInteractionLog)
                .where(SponsorInteractionLog.organization_id == organization_id)
                .order_by(SponsorInteractionLog.occurred_at.desc())
            )
        ).all()
    )
    return [await sponsor_interaction_read(db, interaction) for interaction in interactions]


async def sponsor_stewardship_dashboard(
    db: AsyncSession,
    organization_id: UUID,
) -> SponsorStewardshipDashboardRead:
    sponsors = await list_sponsors(db, organization_id)
    agreements = await list_sponsorships(db, organization_id)
    milestones = list(
        (
            await db.scalars(
                select(SponsorshipDeliverableMilestone).where(
                    SponsorshipDeliverableMilestone.organization_id == organization_id
                )
            )
        ).all()
    )
    interactions = list(
        (await db.scalars(select(SponsorInteractionLog).where(SponsorInteractionLog.organization_id == organization_id))).all()
    )
    activation_counts = await sponsor_activation_counts_by_sponsor(db, organization_id)
    content_counts = await sponsor_content_counts_by_sponsor(db, organization_id)
    today = date.today()
    forecasts = [
        sponsor_renewal_forecast(
            sponsor,
            [agreement for agreement in agreements if agreement.sponsor_id == sponsor.id],
            [milestone for milestone in milestones if milestone.sponsor_id == sponsor.id],
            [interaction for interaction in interactions if interaction.sponsor_id == sponsor.id],
            activation_counts.get(sponsor.id, 0),
            content_counts.get(sponsor.id, 0),
            today,
        )
        for sponsor in sponsors
    ]
    follow_up_due_count = sum(1 for interaction in interactions if interaction.follow_up_on and interaction.follow_up_on <= today)
    overdue_milestone_count = sum(1 for milestone in milestones if milestone.due_on and milestone.due_on < today and milestone.status != "completed")
    return SponsorStewardshipDashboardRead(
        organization_id=organization_id,
        sponsor_count=len(sponsors),
        milestone_count=len(milestones),
        overdue_milestone_count=overdue_milestone_count,
        interaction_count=len(interactions),
        follow_up_due_count=follow_up_due_count,
        forecasts=sorted(forecasts, key=lambda item: item.renewal_score, reverse=True),
        recommendations=sponsor_stewardship_recommendations(forecasts, overdue_milestone_count, follow_up_due_count),
    )


async def create_sponsor_activation_campaign(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SponsorActivationCampaignCreate,
    authz: AuthorizationService,
) -> SponsorActivationCampaignRead:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    if payload.sponsorship_agreement_id is not None:
        await get_sponsorship_for_organization(db, payload.sponsorship_agreement_id, payload.organization_id)
    if payload.fan_challenge_id is not None:
        await get_fan_challenge_for_organization(db, payload.fan_challenge_id, payload.organization_id)
    campaign = SponsorActivationCampaign(
        **payload.model_dump(exclude={"coupon_code"}),
        coupon_code=normalize_coupon_code(payload.coupon_code),
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return await sponsor_activation_campaign_read(db, campaign)


async def list_sponsor_activation_campaigns(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SponsorActivationCampaignRead]:
    campaigns = list(
        (
            await db.scalars(
                select(SponsorActivationCampaign)
                .where(SponsorActivationCampaign.organization_id == organization_id)
                .order_by(SponsorActivationCampaign.created_at.desc())
            )
        ).all()
    )
    return [await sponsor_activation_campaign_read(db, campaign) for campaign in campaigns]


async def record_sponsor_coupon_redemption(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SponsorCouponRedemptionCreate,
    authz: AuthorizationService,
) -> SponsorCouponRedemptionRead:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    campaign = await get_activation_by_coupon(db, payload.organization_id, payload.coupon_code)
    supporter = None
    if payload.supporter_profile_id is not None:
        supporter = await db.get(SupporterProfile, payload.supporter_profile_id)
        if supporter is None or supporter.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supporter profile not found")
    redemption = SponsorCouponRedemption(
        organization_id=payload.organization_id,
        activation_campaign_id=campaign.id,
        supporter_profile_id=payload.supporter_profile_id,
        redeemer_name=payload.redeemer_name,
        redeemer_email=payload.redeemer_email.strip().lower(),
        source=payload.source,
        order_reference=payload.order_reference,
        discount_amount=payload.discount_amount,
        purchase_amount=payload.purchase_amount,
        redeemed_at=datetime.now(UTC),
    )
    campaign.redemption_count += 1
    campaign.conversion_value += payload.purchase_amount
    if supporter is not None:
        supporter.engagement_points += sponsor_activation_points(payload.purchase_amount)
        supporter.last_engagement_at = redemption.redeemed_at
    db.add(redemption)
    await db.commit()
    await db.refresh(redemption)
    await db.refresh(campaign)
    return await sponsor_coupon_redemption_read(db, redemption, campaign)


async def list_sponsor_coupon_redemptions(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SponsorCouponRedemptionRead]:
    rows = (
        await db.execute(
            select(SponsorCouponRedemption, SponsorActivationCampaign)
            .join(SponsorActivationCampaign, SponsorActivationCampaign.id == SponsorCouponRedemption.activation_campaign_id)
            .where(SponsorCouponRedemption.organization_id == organization_id)
            .order_by(SponsorCouponRedemption.redeemed_at.desc())
        )
    ).all()
    return [
        await sponsor_coupon_redemption_read(db, redemption, campaign)
        for redemption, campaign in rows
    ]


async def sponsor_activation_dashboard(db: AsyncSession, organization_id: UUID) -> SponsorActivationDashboardRead:
    campaigns = list(
        (
            await db.scalars(
                select(SponsorActivationCampaign).where(SponsorActivationCampaign.organization_id == organization_id)
            )
        ).all()
    )
    total_impressions = sum(campaign.impression_count for campaign in campaigns)
    total_signups = sum(campaign.signup_count for campaign in campaigns)
    total_redemptions = sum(campaign.redemption_count for campaign in campaigns)
    conversion_value = sum((campaign.conversion_value for campaign in campaigns), Decimal("0"))
    top_campaign = max(campaigns, key=lambda item: item.redemption_count, default=None)
    return SponsorActivationDashboardRead(
        organization_id=organization_id,
        campaign_count=len(campaigns),
        active_campaign_count=sum(1 for campaign in campaigns if campaign.status == CommercialStatus.ACTIVE),
        total_impressions=total_impressions,
        total_signups=total_signups,
        total_redemptions=total_redemptions,
        conversion_value=conversion_value,
        top_coupon_code=top_campaign.coupon_code if top_campaign else None,
        roi_signal=sponsor_activation_roi_signal(total_redemptions, conversion_value),
        recommendations=sponsor_activation_recommendations(campaigns, total_redemptions, conversion_value),
    )


async def create_sponsor_content_asset(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SponsorContentAssetCreate,
    authz: AuthorizationService,
) -> SponsorContentAssetRead:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    if payload.sponsorship_agreement_id is not None:
        await get_sponsorship_for_organization(db, payload.sponsorship_agreement_id, payload.organization_id)
    asset = SponsorContentAsset(**payload.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return await sponsor_content_asset_read(db, asset)


async def list_sponsor_content_assets(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SponsorContentAssetRead]:
    assets = list(
        (
            await db.scalars(
                select(SponsorContentAsset)
                .where(SponsorContentAsset.organization_id == organization_id)
                .order_by(SponsorContentAsset.created_at.desc())
            )
        ).all()
    )
    return [await sponsor_content_asset_read(db, asset) for asset in assets]


async def review_sponsor_content_asset(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SponsorContentApprovalCreate,
    authz: AuthorizationService,
) -> SponsorContentApprovalRead:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    asset = await get_sponsor_content_asset_for_organization(db, payload.content_asset_id, payload.organization_id)
    decision = normalize_content_decision(payload.decision)
    review = SponsorContentApprovalReview(
        organization_id=payload.organization_id,
        content_asset_id=payload.content_asset_id,
        reviewer_name=payload.reviewer_name,
        reviewer_email=payload.reviewer_email.strip().lower() if payload.reviewer_email else None,
        decision=decision,
        notes=payload.notes,
        decided_at=datetime.now(UTC),
    )
    asset.approval_status = decision
    if decision == "approved":
        asset.approved_at = review.decided_at
        asset.approved_by_name = payload.reviewer_name
    elif decision in {"changes_requested", "rejected"}:
        asset.approved_at = None
        asset.approved_by_name = None
    db.add(review)
    await db.commit()
    await db.refresh(review)
    await db.refresh(asset)
    return sponsor_content_approval_read(review, asset)


async def list_sponsor_content_reviews(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SponsorContentApprovalRead]:
    rows = (
        await db.execute(
            select(SponsorContentApprovalReview, SponsorContentAsset)
            .join(SponsorContentAsset, SponsorContentAsset.id == SponsorContentApprovalReview.content_asset_id)
            .where(SponsorContentApprovalReview.organization_id == organization_id)
            .order_by(SponsorContentApprovalReview.decided_at.desc())
        )
    ).all()
    return [sponsor_content_approval_read(review, asset) for review, asset in rows]


async def create_sponsor_activation_placement(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SponsorActivationPlacementCreate,
    authz: AuthorizationService,
) -> SponsorActivationPlacementRead:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    asset = None
    if payload.content_asset_id is not None:
        asset = await get_sponsor_content_asset_for_organization(db, payload.content_asset_id, payload.organization_id)
        if asset.sponsor_id != payload.sponsor_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content asset belongs to another sponsor")
    if payload.activation_campaign_id is not None:
        campaign = await db.get(SponsorActivationCampaign, payload.activation_campaign_id)
        if campaign is None or campaign.organization_id != payload.organization_id or campaign.sponsor_id != payload.sponsor_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor activation campaign not found")
    if payload.event_id is not None:
        await get_event_for_organization(db, payload.event_id, payload.organization_id)
    placement = SponsorActivationPlacement(**payload.model_dump())
    if asset is not None:
        asset.usage_count += 1
    db.add(placement)
    await db.commit()
    await db.refresh(placement)
    return await sponsor_activation_placement_read(db, placement)


async def list_sponsor_activation_placements(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SponsorActivationPlacementRead]:
    placements = list(
        (
            await db.scalars(
                select(SponsorActivationPlacement)
                .where(SponsorActivationPlacement.organization_id == organization_id)
                .order_by(SponsorActivationPlacement.created_at.desc())
            )
        ).all()
    )
    return [await sponsor_activation_placement_read(db, placement) for placement in placements]


async def sponsor_content_dashboard(db: AsyncSession, organization_id: UUID) -> SponsorContentDashboardRead:
    assets = list(
        (await db.scalars(select(SponsorContentAsset).where(SponsorContentAsset.organization_id == organization_id))).all()
    )
    placements = list(
        (
            await db.scalars(
                select(SponsorActivationPlacement).where(SponsorActivationPlacement.organization_id == organization_id)
            )
        ).all()
    )
    now = datetime.now(UTC)
    expiring_before = now + timedelta(days=30)
    return SponsorContentDashboardRead(
        organization_id=organization_id,
        asset_count=len(assets),
        approved_asset_count=sum(1 for asset in assets if asset.approval_status == "approved"),
        pending_asset_count=sum(1 for asset in assets if asset.approval_status == "pending_review"),
        expiring_asset_count=sum(1 for asset in assets if asset.expires_at and now <= asset.expires_at <= expiring_before),
        placement_count=len(placements),
        planned_placement_count=sum(1 for placement in placements if placement.status == "planned"),
        total_expected_impressions=sum(placement.expected_impressions for placement in placements),
        total_actual_impressions=sum(placement.actual_impressions for placement in placements),
        recommendations=sponsor_content_recommendations(assets, placements),
    )


async def create_campaign(db: AsyncSession, identity: CurrentIdentity, payload: FundraisingCampaignCreate, authz: AuthorizationService) -> FundraisingCampaign:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    campaign = FundraisingCampaign(**payload.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def list_campaigns(db: AsyncSession, organization_id: UUID) -> list[FundraisingCampaign]:
    return list((await db.scalars(select(FundraisingCampaign).where(FundraisingCampaign.organization_id == organization_id).order_by(FundraisingCampaign.created_at.desc()))).all())


async def record_donation(db: AsyncSession, identity: CurrentIdentity, payload: DonationCreate, authz: AuthorizationService) -> Donation:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    campaign = await get_campaign_for_organization(db, payload.campaign_id, payload.organization_id)
    donation = Donation(**payload.model_dump())
    campaign.raised_amount += payload.amount
    if campaign.raised_amount >= campaign.goal_amount:
        campaign.status = CommercialStatus.COMPLETED
    db.add(donation)
    await db.commit()
    await db.refresh(donation)
    return donation


async def create_grant_opportunity(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: GrantOpportunityCreate,
    authz: AuthorizationService,
) -> GrantOpportunity:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    opportunity = GrantOpportunity(**payload.model_dump())
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)
    return opportunity


async def list_grant_opportunities(db: AsyncSession, organization_id: UUID) -> list[GrantOpportunity]:
    return list(
        (
            await db.scalars(
                select(GrantOpportunity)
                .where(GrantOpportunity.organization_id == organization_id)
                .order_by(GrantOpportunity.due_on, GrantOpportunity.created_at.desc())
            )
        ).all()
    )


async def create_grant_application(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: GrantApplicationCreate,
    authz: AuthorizationService,
) -> GrantApplication:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_grant_opportunity_for_organization(db, payload.grant_opportunity_id, payload.organization_id)
    application = GrantApplication(**payload.model_dump())
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


async def list_grant_applications(db: AsyncSession, organization_id: UUID) -> list[tuple[GrantApplication, GrantOpportunity | None]]:
    rows = (
        await db.execute(
            select(GrantApplication, GrantOpportunity)
            .join(GrantOpportunity, GrantOpportunity.id == GrantApplication.grant_opportunity_id, isouter=True)
            .where(GrantApplication.organization_id == organization_id)
            .order_by(GrantApplication.created_at.desc())
        )
    ).all()
    return [(application, opportunity) for application, opportunity in rows]


async def create_grant_report(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: GrantReportCreate,
    authz: AuthorizationService,
) -> GrantReport:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_grant_application_for_organization(db, payload.grant_application_id, payload.organization_id)
    report = GrantReport(**payload.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def list_grant_reports(db: AsyncSession, organization_id: UUID) -> list[tuple[GrantReport, GrantApplication | None]]:
    rows = (
        await db.execute(
            select(GrantReport, GrantApplication)
            .join(GrantApplication, GrantApplication.id == GrantReport.grant_application_id, isouter=True)
            .where(GrantReport.organization_id == organization_id)
            .order_by(GrantReport.due_on, GrantReport.created_at.desc())
        )
    ).all()
    return [(report, application) for report, application in rows]


async def grant_dashboard(db: AsyncSession, organization_id: UUID) -> GrantDashboardRead:
    opportunities = await list_grant_opportunities(db, organization_id)
    applications = [application for application, _ in await list_grant_applications(db, organization_id)]
    reports = [report for report, _ in await list_grant_reports(db, organization_id)]
    today = date.today()
    soon = today.toordinal() + 45
    due_soon = [
        opportunity
        for opportunity in opportunities
        if opportunity.due_on is not None and today.toordinal() <= opportunity.due_on.toordinal() <= soon
    ]
    overdue_reports = [
        report
        for report in reports
        if report.due_on < today and report.status not in {"submitted", "accepted", "complete", "completed"}
    ]
    submitted_count = sum(1 for application in applications if application.status in {"submitted", "under_review", "awarded"})
    awarded_count = sum(1 for application in applications if application.status == "awarded" or application.awarded_amount > 0)
    readiness_score = grant_readiness_score(
        opportunity_count=len(opportunities),
        application_count=len(applications),
        submitted_count=submitted_count,
        awarded_count=awarded_count,
        overdue_report_count=len(overdue_reports),
    )
    return GrantDashboardRead(
        organization_id=organization_id,
        opportunity_count=len(opportunities),
        active_opportunity_count=sum(1 for opportunity in opportunities if opportunity.status in {"open", "active"}),
        application_count=len(applications),
        submitted_application_count=submitted_count,
        awarded_application_count=awarded_count,
        report_count=len(reports),
        due_soon_count=len(due_soon),
        overdue_report_count=len(overdue_reports),
        requested_amount=sum((application.requested_amount for application in applications), Decimal("0")),
        awarded_amount=sum((application.awarded_amount for application in applications), Decimal("0")),
        match_required_amount=sum((opportunity.matching_required for opportunity in opportunities), Decimal("0")),
        readiness_score=readiness_score,
        pipeline_status="ready" if readiness_score >= 80 else "attention" if readiness_score >= 50 else "blocked",
        recommendations=grant_recommendations(opportunities, applications, reports, due_soon, overdue_reports),
        next_deadline_on=next((opportunity.due_on for opportunity in opportunities if opportunity.due_on is not None), None),
    )


def grant_readiness_score(
    *,
    opportunity_count: int,
    application_count: int,
    submitted_count: int,
    awarded_count: int,
    overdue_report_count: int,
) -> int:
    score = 20
    if opportunity_count:
        score += 20
    if application_count:
        score += 20
    if submitted_count:
        score += 20
    if awarded_count:
        score += 20
    if overdue_report_count:
        score -= min(30, overdue_report_count * 10)
    return max(0, min(score, 100))


def grant_recommendations(
    opportunities: list[GrantOpportunity],
    applications: list[GrantApplication],
    reports: list[GrantReport],
    due_soon: list[GrantOpportunity],
    overdue_reports: list[GrantReport],
) -> list[str]:
    recommendations: list[str] = []
    if not opportunities:
        recommendations.append("Add grant opportunities from federations, ministries, foundations, and corporate CSR programs.")
    if due_soon:
        recommendations.append(f"Prioritize {due_soon[0].program_name}; the deadline is {due_soon[0].due_on}.")
    if not applications and opportunities:
        recommendations.append("Draft at least one grant application with project narrative, budget summary, and impact metrics.")
    if any(application.status == "draft" for application in applications):
        recommendations.append("Move draft applications to submitted once board, school, or association approvals are complete.")
    if any(application.status == "awarded" for application in applications) and not reports:
        recommendations.append("Create funder report schedules for awarded grants before spending begins.")
    if overdue_reports:
        recommendations.append(f"Resolve {len(overdue_reports)} overdue grant report(s) before pursuing additional awards.")
    if not recommendations:
        recommendations.append("Grant pipeline is operating; keep deadlines, report evidence, and impact metrics current.")
    return recommendations[:6]


async def create_merchandise_product(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: MerchandiseProductCreate,
    authz: AuthorizationService,
) -> MerchandiseProduct:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    existing = await db.scalar(
        select(MerchandiseProduct).where(
            MerchandiseProduct.organization_id == payload.organization_id,
            MerchandiseProduct.sku == payload.sku,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Merchandise SKU already exists")
    product = MerchandiseProduct(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def list_merchandise_products(db: AsyncSession, organization_id: UUID) -> list[MerchandiseProduct]:
    return list(
        (
            await db.scalars(
                select(MerchandiseProduct)
                .where(MerchandiseProduct.organization_id == organization_id)
                .order_by(MerchandiseProduct.category, MerchandiseProduct.name)
            )
        ).all()
    )


async def create_merchandise_order(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: MerchandiseOrderCreate,
    authz: AuthorizationService,
) -> tuple[MerchandiseOrder, list[MerchandiseOrderLine], dict[UUID, MerchandiseProduct]]:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    product_ids = [line.merchandise_product_id for line in payload.lines]
    products = list(
        (
            await db.scalars(
                select(MerchandiseProduct).where(
                    MerchandiseProduct.organization_id == payload.organization_id,
                    MerchandiseProduct.id.in_(product_ids),
                )
            )
        ).all()
    )
    products_by_id = {product.id: product for product in products}
    if len(products_by_id) != len(set(product_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchandise product not found")
    for line in payload.lines:
        product = products_by_id[line.merchandise_product_id]
        if product.status != CommercialStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{product.name} is not active")
        if product.inventory_count < line.quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{product.name} inventory is too low")
        if (line.personalization_name or line.personalization_number) and not product.personalization_enabled:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{product.name} does not allow personalization")

    currency = products[0].currency if products else "USD"
    total = sum((products_by_id[line.merchandise_product_id].price * line.quantity for line in payload.lines), Decimal("0"))
    order = MerchandiseOrder(
        organization_id=payload.organization_id,
        buyer_person_id=payload.buyer_person_id,
        buyer_name=payload.buyer_name,
        buyer_email=payload.buyer_email,
        delivery_method=payload.delivery_method,
        delivery_address=payload.delivery_address,
        total_amount=total,
        currency=currency,
        external_payment_reference=payload.external_payment_reference,
        notes=payload.notes,
        status=CommercialStatus.PAID,
        fulfillment_status="queued",
    )
    db.add(order)
    await db.flush()
    order_lines: list[MerchandiseOrderLine] = []
    for line in payload.lines:
        product = products_by_id[line.merchandise_product_id]
        product.inventory_count -= line.quantity
        order_line = MerchandiseOrderLine(
            organization_id=payload.organization_id,
            merchandise_order_id=order.id,
            merchandise_product_id=product.id,
            quantity=line.quantity,
            unit_price=product.price,
            line_total=product.price * line.quantity,
            size=line.size,
            color=line.color,
            personalization_name=line.personalization_name,
            personalization_number=line.personalization_number,
            fulfillment_status="queued",
        )
        db.add(order_line)
        order_lines.append(order_line)
    await db.commit()
    await db.refresh(order)
    for line in order_lines:
        await db.refresh(line)
    return order, order_lines, products_by_id


async def list_merchandise_orders(db: AsyncSession, organization_id: UUID) -> list[tuple[MerchandiseOrder, list[MerchandiseOrderLine], dict[UUID, MerchandiseProduct]]]:
    orders = list(
        (
            await db.scalars(
                select(MerchandiseOrder)
                .where(MerchandiseOrder.organization_id == organization_id)
                .order_by(MerchandiseOrder.created_at.desc())
            )
        ).all()
    )
    if not orders:
        return []
    order_ids = [order.id for order in orders]
    lines = list(
        (
            await db.scalars(
                select(MerchandiseOrderLine)
                .where(MerchandiseOrderLine.merchandise_order_id.in_(order_ids))
                .order_by(MerchandiseOrderLine.created_at)
            )
        ).all()
    )
    product_ids = list({line.merchandise_product_id for line in lines})
    products = list(
        (
            await db.scalars(
                select(MerchandiseProduct).where(MerchandiseProduct.id.in_(product_ids))
            )
        ).all()
    ) if product_ids else []
    products_by_id = {product.id: product for product in products}
    lines_by_order: dict[UUID, list[MerchandiseOrderLine]] = {}
    for line in lines:
        lines_by_order.setdefault(line.merchandise_order_id, []).append(line)
    return [(order, lines_by_order.get(order.id, []), products_by_id) for order in orders]


async def update_merchandise_fulfillment(
    db: AsyncSession,
    identity: CurrentIdentity,
    merchandise_order_id: UUID,
    payload: MerchandiseFulfillmentUpdate,
    authz: AuthorizationService,
) -> tuple[MerchandiseOrder, list[MerchandiseOrderLine], dict[UUID, MerchandiseProduct]]:
    order = await db.get(MerchandiseOrder, merchandise_order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchandise order not found")
    await ensure_manage_commercial(authz, identity, order.organization_id)
    lines = list(
        (
            await db.scalars(
                select(MerchandiseOrderLine).where(MerchandiseOrderLine.merchandise_order_id == order.id)
            )
        ).all()
    )
    order.fulfillment_status = payload.fulfillment_status
    order.notes = payload.notes if payload.notes is not None else order.notes
    if payload.fulfillment_status in {"fulfilled", "shipped", "picked_up"}:
        order.fulfilled_at = datetime.now(UTC)
        for line in lines:
            line.fulfillment_status = payload.fulfillment_status
    await db.commit()
    await db.refresh(order)
    product_ids = [line.merchandise_product_id for line in lines]
    products = list(
        (
            await db.scalars(select(MerchandiseProduct).where(MerchandiseProduct.id.in_(product_ids)))
        ).all()
    ) if product_ids else []
    return order, lines, {product.id: product for product in products}


async def merchandise_store_dashboard(db: AsyncSession, organization_id: UUID) -> MerchandiseStoreDashboardRead:
    products = await list_merchandise_products(db, organization_id)
    order_rows = await list_merchandise_orders(db, organization_id)
    orders = [order for order, _, _ in order_rows]
    lines = [line for _, order_lines, _ in order_rows for line in order_lines]
    cost_by_product = {product.id: product.cost for product in products}
    gross_revenue = sum((order.total_amount for order in orders), Decimal("0"))
    estimated_cost = sum((cost_by_product.get(line.merchandise_product_id, Decimal("0")) * line.quantity for line in lines), Decimal("0"))
    low_stock_products = [
        product for product in products if product.inventory_count <= product.reorder_point and product.status == CommercialStatus.ACTIVE
    ]
    return MerchandiseStoreDashboardRead(
        organization_id=organization_id,
        product_count=len(products),
        active_product_count=sum(1 for product in products if product.status == CommercialStatus.ACTIVE),
        low_stock_count=len(low_stock_products),
        order_count=len(orders),
        queued_order_count=sum(1 for order in orders if order.fulfillment_status in {"queued", "processing"}),
        fulfilled_order_count=sum(1 for order in orders if order.fulfillment_status in {"fulfilled", "shipped", "picked_up"}),
        units_sold=sum(line.quantity for line in lines),
        gross_revenue=gross_revenue,
        estimated_margin=gross_revenue - estimated_cost,
        recommendations=merchandise_recommendations(products, orders, low_stock_products),
    )


def merchandise_order_read(
    order: MerchandiseOrder,
    lines: list[MerchandiseOrderLine],
    products_by_id: dict[UUID, MerchandiseProduct],
) -> MerchandiseOrderRead:
    return MerchandiseOrderRead(
        id=order.id,
        organization_id=order.organization_id,
        buyer_person_id=order.buyer_person_id,
        buyer_name=order.buyer_name,
        buyer_email=order.buyer_email,
        delivery_method=order.delivery_method,
        delivery_address=order.delivery_address,
        total_amount=order.total_amount,
        currency=order.currency,
        external_payment_reference=order.external_payment_reference,
        status=order.status,
        fulfillment_status=order.fulfillment_status,
        fulfilled_at=order.fulfilled_at,
        notes=order.notes,
        lines=[
            MerchandiseOrderLineRead(
                id=line.id,
                organization_id=line.organization_id,
                merchandise_order_id=line.merchandise_order_id,
                merchandise_product_id=line.merchandise_product_id,
                product_name=products_by_id.get(line.merchandise_product_id).name if products_by_id.get(line.merchandise_product_id) else None,
                sku=products_by_id.get(line.merchandise_product_id).sku if products_by_id.get(line.merchandise_product_id) else None,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.line_total,
                size=line.size,
                color=line.color,
                personalization_name=line.personalization_name,
                personalization_number=line.personalization_number,
                fulfillment_status=line.fulfillment_status,
            )
            for line in lines
        ],
    )


def merchandise_recommendations(
    products: list[MerchandiseProduct],
    orders: list[MerchandiseOrder],
    low_stock_products: list[MerchandiseProduct],
) -> list[str]:
    recommendations: list[str] = []
    if not products:
        recommendations.append("Create first store products for jerseys, training gear, supporter items, or event merchandise.")
    if low_stock_products:
        recommendations.append(f"Reorder {low_stock_products[0].name}; stock is at or below the reorder point.")
    if not orders and products:
        recommendations.append("Publish the store link through public site, family portal, and matchday QR channels.")
    if any(order.fulfillment_status == "queued" for order in orders):
        recommendations.append("Pack queued orders and update fulfillment status for pickup or shipping.")
    if not any(product.personalization_enabled for product in products):
        recommendations.append("Offer personalized jerseys or training tops to increase store conversion.")
    if not recommendations:
        recommendations.append("Merchandise store is active; keep stock, fulfillment, and campaign links current.")
    return recommendations[:6]


async def create_ticket_product(db: AsyncSession, identity: CurrentIdentity, payload: TicketProductCreate, authz: AuthorizationService) -> TicketProduct:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_event_for_organization(db, payload.event_id, payload.organization_id)
    ticket_product = TicketProduct(**payload.model_dump())
    db.add(ticket_product)
    await db.commit()
    await db.refresh(ticket_product)
    return ticket_product


async def list_ticket_products(db: AsyncSession, organization_id: UUID) -> list[TicketProduct]:
    return list((await db.scalars(select(TicketProduct).where(TicketProduct.organization_id == organization_id).order_by(TicketProduct.created_at.desc()))).all())


async def create_ticket_order(db: AsyncSession, identity: CurrentIdentity, payload: TicketOrderCreate, authz: AuthorizationService) -> tuple[TicketOrder, list[Ticket]]:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    ticket_product = await get_ticket_product_for_organization(db, payload.ticket_product_id, payload.organization_id)
    if ticket_product.sold_count + payload.quantity > ticket_product.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket capacity exceeded")
    order = TicketOrder(
        organization_id=payload.organization_id,
        ticket_product_id=payload.ticket_product_id,
        buyer_name=payload.buyer_name,
        buyer_email=payload.buyer_email,
        quantity=payload.quantity,
        total_amount=ticket_product.price * payload.quantity,
        currency=ticket_product.currency,
        external_payment_reference=payload.external_payment_reference,
    )
    db.add(order)
    await db.flush()
    tickets = [
        Ticket(
            organization_id=payload.organization_id,
            ticket_order_id=order.id,
            ticket_product_id=ticket_product.id,
            holder_name=payload.buyer_name,
            qr_token=f"tkt_{uuid4().hex}",
        )
        for _ in range(payload.quantity)
    ]
    ticket_product.sold_count += payload.quantity
    db.add_all(tickets)
    await db.commit()
    await db.refresh(order)
    return order, tickets


async def list_tickets(db: AsyncSession, organization_id: UUID) -> list[Ticket]:
    return list((await db.scalars(select(Ticket).where(Ticket.organization_id == organization_id).order_by(Ticket.created_at.desc()))).all())


async def check_in_ticket(db: AsyncSession, identity: CurrentIdentity, ticket_id: UUID, payload: TicketCheckIn, authz: AuthorizationService) -> Ticket:
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    await ensure_manage_commercial(authz, identity, ticket.organization_id)
    if ticket.status != TicketStatus.ISSUED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket cannot be checked in")
    ticket.status = TicketStatus.CHECKED_IN
    ticket.checked_in_at = datetime.now(UTC)
    ticket.gate = payload.gate
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def refund_ticket(
    db: AsyncSession,
    identity: CurrentIdentity,
    ticket_id: UUID,
    payload: CommercialRefundCreate,
    authz: AuthorizationService,
) -> CommercialRefundRead:
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    await ensure_manage_commercial(authz, identity, ticket.organization_id)
    if ticket.status == TicketStatus.REFUNDED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket already refunded")
    order = await db.get(TicketOrder, ticket.ticket_order_id)
    product = await db.get(TicketProduct, ticket.ticket_product_id)
    if order is None or product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket order not found")

    refund_amount = payload.amount or product.price
    ticket.status = TicketStatus.REFUNDED
    product.sold_count = max(product.sold_count - 1, 0)
    remaining_issued = await tickets_remaining_in_order(db, order.id, excluding_ticket_id=ticket.id)
    order.status = CommercialStatus.CANCELLED if remaining_issued == 0 else CommercialStatus.PARTIAL
    await db.commit()
    await db.refresh(ticket)
    return CommercialRefundRead(
        refund_id=f"refund_{uuid4().hex}",
        organization_id=ticket.organization_id,
        target_type="ticket",
        target_id=ticket.id,
        amount=refund_amount,
        currency=order.currency,
        reason=payload.reason,
        status="processed",
        external_reference=payload.external_reference,
    )


async def create_invoice(db: AsyncSession, identity: CurrentIdentity, payload: FinanceInvoiceCreate, authz: AuthorizationService) -> FinanceInvoice:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.sponsor_id is not None:
        await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    invoice = FinanceInvoice(**payload.model_dump())
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


async def list_invoices(db: AsyncSession, organization_id: UUID) -> list[FinanceInvoice]:
    return list((await db.scalars(select(FinanceInvoice).where(FinanceInvoice.organization_id == organization_id).order_by(FinanceInvoice.created_at.desc()))).all())


async def record_payment(db: AsyncSession, identity: CurrentIdentity, payload: FinancePaymentCreate, authz: AuthorizationService) -> FinancePayment:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    invoice = await get_invoice_for_organization(db, payload.invoice_id, payload.organization_id)
    payment = FinancePayment(received_at=datetime.now(UTC), **payload.model_dump())
    invoice.amount_paid += payload.amount
    invoice.status = CommercialStatus.PAID if invoice.amount_paid >= invoice.amount_due else CommercialStatus.PARTIAL
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def get_commercial_invoice_hosted_checkout(
    db: AsyncSession,
    session_id: str,
    invoice_id: UUID,
    provider: str,
) -> CommercialInvoiceHostedCheckoutRead:
    invoice = await db.get(FinanceInvoice, invoice_id)
    if invoice is None or invoice.sponsor_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor invoice checkout session not found")
    expected_session_id = commercial_invoice_checkout_session_id(invoice, provider)
    if not hmac.compare_digest(expected_session_id, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid checkout session")
    return commercial_invoice_hosted_checkout_read(invoice, provider, session_id)


async def create_commercial_invoice_provider_checkout(
    db: AsyncSession,
    session_id: str,
    invoice_id: UUID,
    provider: str,
    payload: CommercialInvoiceProviderCheckoutCreate,
    settings: Settings | None = None,
) -> CommercialInvoiceProviderCheckoutRead:
    invoice = await db.get(FinanceInvoice, invoice_id)
    if invoice is None or invoice.sponsor_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor invoice checkout session not found")
    expected_session_id = commercial_invoice_checkout_session_id(invoice, provider)
    if not hmac.compare_digest(expected_session_id, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid checkout session")
    open_amount = commercial_invoice_open_amount(invoice)
    if open_amount <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice is already paid")

    selected_settings = settings or get_settings()
    created_at = datetime.now(UTC)
    local_redirect_url = commercial_invoice_checkout_session_url("/pay/sessions", session_id, invoice, provider)
    existing = await db.scalar(
        select(CommercialPaymentSession).where(
            CommercialPaymentSession.organization_id == invoice.organization_id,
            CommercialPaymentSession.provider == provider,
            CommercialPaymentSession.local_session_id == session_id,
        )
    )
    session = existing or CommercialPaymentSession(
        organization_id=invoice.organization_id,
        invoice_id=invoice.id,
        sponsor_id=invoice.sponsor_id,
        provider=provider,
        local_session_id=session_id,
        provider_session_id=commercial_invoice_provider_session_id(invoice, provider),
        client_reference=f"sponsor-invoice-checkout:{invoice.id}",
        amount=open_amount,
        currency=invoice.currency,
        redirect_url=local_redirect_url,
        created_at=created_at,
    )
    session.invoice_id = invoice.id
    session.sponsor_id = invoice.sponsor_id
    session.mode = selected_settings.commercial_payment_session_mode
    session.status = "creating"
    session.provider_session_id = commercial_invoice_provider_session_id(invoice, provider)
    session.client_reference = f"sponsor-invoice-checkout:{invoice.id}"
    session.amount = open_amount
    session.currency = invoice.currency
    session.redirect_url = local_redirect_url
    session.success_url = payload.success_url
    session.cancel_url = payload.cancel_url
    session.customer_email = payload.customer_email
    session.payment_method = payload.payment_method
    session.webhook_configured = bool(selected_settings.commercial_payment_session_webhook_url)
    session.provider_status_code = None
    session.provider_response = None
    session.failure_reason = None
    db.add(session)
    if selected_settings.commercial_payment_session_mode == "local":
        session.status = "local_ready"
        session.failure_reason = "Local payment-session mode; using AfroLete hosted checkout page."
        await db.commit()
        await db.refresh(session)
        return commercial_payment_session_read(session)
    if not selected_settings.commercial_payment_session_webhook_url:
        session.status = "configuration_required"
        session.failure_reason = "Payment session webhook mode is enabled but no webhook URL is configured."
        await db.commit()
        await db.refresh(session)
        return commercial_payment_session_read(session)

    provider_payload = commercial_invoice_provider_checkout_payload(invoice, commercial_payment_session_read(session), payload)
    raw_body = json.dumps(provider_payload, sort_keys=True, default=str).encode()
    timestamp = str(int(time.time()))
    headers = await commercial_payment_session_headers(selected_settings, raw_body, timestamp)
    try:
        async with httpx.AsyncClient(timeout=selected_settings.commercial_payment_session_timeout_seconds) as client:
            response = await client.post(
                selected_settings.commercial_payment_session_webhook_url,
                json=provider_payload,
                headers=headers,
            )
        response_payload = response.json() if response.content else {}
        if not isinstance(response_payload, dict):
            response_payload = {}
        delivered = 200 <= response.status_code < 300
        session.status = "created" if delivered else "failed"
        session.provider_status_code = response.status_code
        session.provider_session_id = str(response_payload.get("provider_session_id") or response_payload.get("id") or session.provider_session_id)
        session.redirect_url = str(response_payload.get("redirect_url") or response_payload.get("url") or session.redirect_url)
        session.provider_response = commercial_payment_session_provider_response(response.status_code, response.text)
        session.failure_reason = None if delivered else f"Payment session webhook returned {response.status_code}: {response.text[:500]}"
    except (ValueError, httpx.HTTPError) as error:
        session.status = "failed"
        session.failure_reason = f"Payment session webhook failed: {error}"

    await db.commit()
    await db.refresh(session)
    return commercial_payment_session_read(session)


async def list_commercial_payment_sessions(
    db: AsyncSession,
    organization_id: UUID,
) -> list[CommercialInvoiceProviderCheckoutRead]:
    await get_organization(db, organization_id)
    sessions = list(
        (
            await db.scalars(
                select(CommercialPaymentSession)
                .where(CommercialPaymentSession.organization_id == organization_id)
                .order_by(CommercialPaymentSession.created_at.desc())
            )
        ).all()
    )
    return [commercial_payment_session_read(session) for session in sessions]


async def settle_commercial_invoice_checkout(
    db: AsyncSession,
    session_id: str,
    payload: CommercialInvoiceCheckoutSettlementCreate,
    signature_required: bool = False,
    signature_validated: bool = False,
) -> CommercialInvoiceCheckoutSettlementRead:
    invoice = await db.get(FinanceInvoice, payload.invoice_id)
    if invoice is None or invoice.sponsor_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor invoice checkout session not found")
    expected_session_id = commercial_invoice_checkout_session_id(invoice, payload.provider)
    if not hmac.compare_digest(expected_session_id, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid checkout session")
    if payload.currency is not None and payload.currency.upper() != invoice.currency:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment currency mismatch")

    open_amount = commercial_invoice_open_amount(invoice)
    accepted = payload.status == "succeeded" and open_amount > 0
    payment: FinancePayment | None = None
    message = "Checkout event recorded as non-settling."
    if accepted:
        amount = (payload.amount or open_amount).quantize(Decimal("0.01"))
        if amount > open_amount:
            amount = open_amount
        external_reference = payload.external_payment_id or f"{payload.provider}:{session_id}"
        existing_payment = await db.scalar(
            select(FinancePayment).where(
                FinancePayment.organization_id == invoice.organization_id,
                FinancePayment.external_reference == external_reference,
            )
        )
        if existing_payment is not None:
            payment = existing_payment
            message = "Payment event was already applied."
        else:
            payment = FinancePayment(
                organization_id=invoice.organization_id,
                invoice_id=invoice.id,
                amount=amount,
                currency=invoice.currency,
                method=payload.method,
                external_reference=external_reference,
                received_at=datetime.now(UTC),
                notes=payload.raw_reference or f"Sponsor invoice checkout settled via {payload.provider}.",
            )
            invoice.amount_paid += amount
            invoice.status = CommercialStatus.PAID if invoice.amount_paid >= invoice.amount_due else CommercialStatus.PARTIAL
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            await db.refresh(invoice)
            message = "Sponsor invoice payment applied."

    return CommercialInvoiceCheckoutSettlementRead(
        invoice_id=invoice.id,
        provider=payload.provider,
        accepted=accepted,
        signature_required=signature_required,
        signature_validated=signature_validated,
        payment_id=payment.id if payment is not None else None,
        invoice_status=invoice.status.value,
        amount_paid=invoice.amount_paid,
        open_amount=commercial_invoice_open_amount(invoice),
        session_status=commercial_invoice_checkout_session_status(invoice),
        message=message,
    )


async def ingest_commercial_invoice_payment_webhook(
    db: AsyncSession,
    payload: CommercialInvoicePaymentWebhookCreate | dict[str, Any],
    provider_hint: str | None = None,
    signature_required: bool = False,
    signature_validated: bool = False,
) -> CommercialInvoiceCheckoutSettlementRead:
    normalized = normalize_commercial_invoice_payment_webhook(payload, provider_hint)
    if normalized.invoice_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Commercial payment webhook invoice_id required")
    if normalized.session_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Commercial payment webhook session_id required")
    success_events = {
        "payment.succeeded",
        "invoice.paid",
        "charge.succeeded",
        "checkout.session.completed",
        "mpesa.stk_callback",
        "PAYMENT.CAPTURE.COMPLETED",
    }
    settlement_status = (
        "succeeded"
        if normalized.status == "succeeded" and normalized.event_type in success_events
        else normalized.status if normalized.status in {"failed", "cancelled"} else "pending"
    )
    settlement_payload = CommercialInvoiceCheckoutSettlementCreate(
        invoice_id=normalized.invoice_id,
        provider=normalized.provider,
        amount=normalized.amount,
        currency=normalized.currency,
        method=normalized.method,
        external_payment_id=normalized.external_payment_id,
        status=settlement_status,
        raw_reference=normalized.raw_reference,
    )
    return await settle_commercial_invoice_checkout(
        db,
        normalized.session_id,
        settlement_payload,
        signature_required=signature_required,
        signature_validated=signature_validated,
    )


async def refund_invoice(
    db: AsyncSession,
    identity: CurrentIdentity,
    invoice_id: UUID,
    payload: CommercialRefundCreate,
    authz: AuthorizationService,
) -> CommercialRefundRead:
    invoice = await get_invoice_for_organization_by_id(db, invoice_id)
    await ensure_manage_commercial(authz, identity, invoice.organization_id)
    refund_amount = payload.amount or invoice.amount_paid
    if refund_amount <= 0 or refund_amount > invoice.amount_paid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid refund amount")
    invoice.amount_paid -= refund_amount
    invoice.status = (
        CommercialStatus.PAID
        if invoice.amount_paid >= invoice.amount_due
        else CommercialStatus.PARTIAL
        if invoice.amount_paid > 0
        else CommercialStatus.ACTIVE
    )
    await db.commit()
    await db.refresh(invoice)
    return CommercialRefundRead(
        refund_id=f"refund_{uuid4().hex}",
        organization_id=invoice.organization_id,
        target_type="invoice",
        target_id=invoice.id,
        amount=refund_amount,
        currency=invoice.currency,
        reason=payload.reason,
        status="processed",
        external_reference=payload.external_reference,
    )


async def tax_quote(
    db: AsyncSession,
    organization_id: UUID,
    subtotal: Decimal,
    tax_rate: Decimal,
    jurisdiction: str,
    reverse_charge: bool = False,
) -> TaxQuoteRead:
    await get_organization(db, organization_id)
    effective_rate = Decimal("0") if reverse_charge else tax_rate
    tax_amount = (subtotal * effective_rate / Decimal("100")).quantize(Decimal("0.01"))
    return TaxQuoteRead(
        organization_id=organization_id,
        jurisdiction=jurisdiction,
        subtotal=subtotal.quantize(Decimal("0.01")),
        tax_rate=effective_rate,
        tax_amount=tax_amount,
        total=(subtotal + tax_amount).quantize(Decimal("0.01")),
        reverse_charge=reverse_charge,
        rationale="Tax estimate for checkout, invoicing, and donation receipt review.",
    )


async def deliver_commercial_tax_filing(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    period_start: date,
    period_end: date,
    jurisdiction: str,
    tax_rate: Decimal,
    reverse_charge: bool,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> CommercialTaxFilingRead:
    await ensure_manage_commercial(authz, identity, organization_id)
    if period_end < period_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="period_end must be on or after period_start")
    selected_settings = settings or get_settings()
    invoices = [
        invoice
        for invoice in await list_invoices(db, organization_id)
        if period_start <= commercial_invoice_filing_date(invoice) <= period_end
    ]
    taxable_subtotal = sum((invoice.amount_due for invoice in invoices), Decimal("0")).quantize(Decimal("0.01"))
    effective_rate = Decimal("0") if reverse_charge else tax_rate
    tax_amount = (taxable_subtotal * effective_rate / Decimal("100")).quantize(Decimal("0.01"))
    gross_total = (taxable_subtotal + tax_amount).quantize(Decimal("0.01"))
    outstanding_total = sum((commercial_invoice_open_amount(invoice) for invoice in invoices), Decimal("0")).quantize(Decimal("0.01"))
    currency = commercial_filing_currency(invoices)
    filed_at = datetime.now(UTC)
    filing_reference = commercial_tax_filing_reference(organization_id, jurisdiction, period_start, period_end)

    result = CommercialTaxFilingRead(
        organization_id=organization_id,
        jurisdiction=jurisdiction.upper(),
        period_start=period_start,
        period_end=period_end,
        invoice_count=len(invoices),
        taxable_subtotal=taxable_subtotal,
        tax_rate=effective_rate,
        tax_amount=tax_amount,
        gross_total=gross_total,
        outstanding_total=outstanding_total,
        currency=currency,
        reverse_charge=reverse_charge,
        filing_reference=filing_reference,
        delivery_mode=selected_settings.commercial_tax_filing_delivery_mode,
        delivery_attempted=False,
        delivered=False,
        destination=selected_settings.commercial_tax_filing_webhook_url or None,
        provider_status_code=None,
        failure_reason=None,
        filed_at=filed_at,
    )
    if selected_settings.commercial_tax_filing_delivery_mode == "record_only":
        return result.model_copy(update={"failure_reason": "Record-only filing mode; commercial tax package prepared for manual submission."})
    if not selected_settings.commercial_tax_filing_webhook_url:
        return result.model_copy(update={"failure_reason": "Commercial tax filing webhook mode is enabled but no webhook URL is configured."})

    payload = commercial_tax_filing_payload(result)
    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(time.time()))
    headers = await commercial_tax_filing_headers(selected_settings, raw_body, timestamp)
    try:
        async with httpx.AsyncClient(timeout=selected_settings.commercial_tax_filing_timeout_seconds) as client:
            response = await client.post(
                selected_settings.commercial_tax_filing_webhook_url,
                json=payload,
                headers=headers,
            )
        delivered = 200 <= response.status_code < 300
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "delivered": delivered,
                "provider_status_code": response.status_code,
                "failure_reason": None if delivered else f"Commercial tax filing webhook returned {response.status_code}: {response.text[:500]}",
            }
        )
    except httpx.HTTPError as error:
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "failure_reason": f"Commercial tax filing webhook failed: {error}",
            }
        )


async def payment_settlement(
    db: AsyncSession,
    organization_id: UUID,
    provider: str,
    fee_rate: Decimal,
    fixed_fee: Decimal,
) -> PaymentSettlementRead:
    await get_organization(db, organization_id)
    ticket_products = await list_ticket_products(db, organization_id)
    payments = await list_payments(db, organization_id)
    donations = await list_donations(db, organization_id)
    gross_ticket_revenue = sum((item.price * item.sold_count for item in ticket_products), Decimal("0"))
    gross_invoice_payments = sum((payment.amount for payment in payments), Decimal("0"))
    gross_donations = sum((donation.amount for donation in donations), Decimal("0"))
    gross_amount = gross_ticket_revenue + gross_invoice_payments + gross_donations
    line_count = len(ticket_products) + len(payments) + len(donations)
    fee_amount = ((gross_amount * fee_rate / Decimal("100")) + (fixed_fee * line_count)).quantize(Decimal("0.01"))
    return PaymentSettlementRead(
        organization_id=organization_id,
        provider=provider,
        currency="USD",
        gross_ticket_revenue=gross_ticket_revenue.quantize(Decimal("0.01")),
        gross_invoice_payments=gross_invoice_payments.quantize(Decimal("0.01")),
        gross_donations=gross_donations.quantize(Decimal("0.01")),
        gross_amount=gross_amount.quantize(Decimal("0.01")),
        fee_amount=fee_amount,
        net_amount=(gross_amount - fee_amount).quantize(Decimal("0.01")),
        payout_reference=f"SETTLE-{datetime.now(UTC).strftime('%Y%m%d')}-{str(organization_id)[:8]}",
        line_count=line_count,
    )


async def execute_payment_settlement_payout(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    provider: str,
    fee_rate: Decimal,
    fixed_fee: Decimal,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> CommercialSettlementPayoutRead:
    await ensure_manage_commercial(authz, identity, organization_id)
    settlement = await payment_settlement(db, organization_id, provider, fee_rate, fixed_fee)
    selected_settings = settings or get_settings()
    batch_reference = commercial_payout_batch_reference(settlement)
    existing = await db.scalar(
        select(CommercialSettlementPayout).where(
            CommercialSettlementPayout.organization_id == organization_id,
            CommercialSettlementPayout.provider == provider,
            CommercialSettlementPayout.payout_batch_reference == batch_reference,
        )
    )
    if existing is not None and existing.status in {"paid", "queued", "delivered", "prepared"}:
        return commercial_settlement_payout_read(existing)

    executed_at = datetime.now(UTC)
    payout = existing or CommercialSettlementPayout(
        organization_id=organization_id,
        provider=provider,
        currency=settlement.currency,
        payout_reference=settlement.payout_reference,
        payout_batch_reference=batch_reference,
        idempotency_key=commercial_payout_idempotency_key(settlement, batch_reference),
        status="prepared",
        delivery_mode=selected_settings.commercial_payout_delivery_mode,
        delivery_attempted=False,
        delivered=False,
        gross_amount=settlement.gross_amount,
        fee_amount=settlement.fee_amount,
        net_amount=settlement.net_amount,
        line_count=settlement.line_count,
        destination=selected_settings.commercial_payout_webhook_url or None,
        provider_status_code=None,
        provider_response=None,
        failure_reason=None,
        processed_by_person_id=identity.person_id,
        executed_at=executed_at,
    )
    payout.currency = settlement.currency
    payout.payout_reference = settlement.payout_reference
    payout.idempotency_key = commercial_payout_idempotency_key(settlement, batch_reference)
    payout.delivery_mode = selected_settings.commercial_payout_delivery_mode
    payout.gross_amount = settlement.gross_amount
    payout.fee_amount = settlement.fee_amount
    payout.net_amount = settlement.net_amount
    payout.line_count = settlement.line_count
    payout.destination = selected_settings.commercial_payout_webhook_url or None
    payout.processed_by_person_id = identity.person_id
    payout.executed_at = executed_at
    db.add(payout)

    if selected_settings.commercial_payout_delivery_mode == "record_only":
        payout.status = "prepared"
        payout.failure_reason = "Record-only payout mode; settlement prepared for manual payout."
        await db.commit()
        await db.refresh(payout)
        return commercial_settlement_payout_read(payout)
    if not selected_settings.commercial_payout_webhook_url:
        payout.status = "failed"
        payout.failure_reason = "Commercial payout webhook mode is enabled but no webhook URL is configured."
        await db.commit()
        await db.refresh(payout)
        return commercial_settlement_payout_read(payout)

    payload = commercial_payout_payload(commercial_settlement_payout_read(payout))
    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(time.time()))
    headers = await commercial_payout_headers(selected_settings, raw_body, timestamp)
    payout.delivery_attempted = True
    try:
        async with httpx.AsyncClient(timeout=selected_settings.commercial_payout_timeout_seconds) as client:
            response = await client.post(
                selected_settings.commercial_payout_webhook_url,
                json=payload,
                headers=headers,
            )
        delivered = 200 <= response.status_code < 300
        payout.delivered = delivered
        payout.status = "queued" if delivered else "failed"
        payout.provider_status_code = response.status_code
        payout.provider_response = commercial_payout_provider_response(response.status_code, response.text)
        payout.failure_reason = None if delivered else f"Commercial payout webhook returned {response.status_code}: {response.text[:500]}"
    except httpx.HTTPError as error:
        payout.status = "failed"
        payout.failure_reason = f"Commercial payout webhook failed: {error}"

    await db.commit()
    await db.refresh(payout)
    return commercial_settlement_payout_read(payout)


async def list_commercial_settlement_payouts(
    db: AsyncSession,
    organization_id: UUID,
) -> list[CommercialSettlementPayoutRead]:
    await get_organization(db, organization_id)
    payouts = list(
        (
            await db.scalars(
                select(CommercialSettlementPayout)
                .where(CommercialSettlementPayout.organization_id == organization_id)
                .order_by(CommercialSettlementPayout.executed_at.desc())
            )
        ).all()
    )
    return [commercial_settlement_payout_read(payout) for payout in payouts]


async def reconcile_commercial_settlement_payout_callback(
    db: AsyncSession,
    payload: CommercialSettlementPayoutCallbackCreate,
    *,
    signature_required: bool = False,
    signature_validated: bool = False,
) -> CommercialSettlementPayoutCallbackRead:
    filters = []
    if payload.payout_reference is not None:
        filters.append(CommercialSettlementPayout.payout_reference == payload.payout_reference)
    if payload.payout_batch_reference is not None:
        filters.append(CommercialSettlementPayout.payout_batch_reference == payload.payout_batch_reference)
    if payload.idempotency_key is not None:
        filters.append(CommercialSettlementPayout.idempotency_key == payload.idempotency_key)
    if not filters:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payout reference, batch reference, or idempotency key required",
        )
    payout = (
        await db.scalars(
            select(CommercialSettlementPayout)
            .where(CommercialSettlementPayout.provider == payload.provider)
            .where(or_(*filters))
        )
    ).first()
    if payout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commercial settlement payout not found")

    matched_by = commercial_payout_callback_match(payload, payout)
    payout_status = normalize_commercial_payout_status(payload.status)
    reconciled_at = datetime.now(UTC)
    payout.status = payout_status
    payout.delivered = payout_status in {"paid", "queued"}
    payout.provider_status_code = payload.provider_status_code
    payout.external_event_id = payload.external_event_id
    payout.reconciled_at = reconciled_at
    payout.callback_payload = commercial_payout_callback_response(
        payload,
        signature_required=signature_required,
        signature_validated=signature_validated,
        matched_by=matched_by,
        reconciled_at=reconciled_at,
    )
    payout.provider_response = payout.callback_payload
    payout.failure_reason = None if payout_status in {"paid", "queued"} else payload.notes or f"Commercial payout callback reconciled as {payout_status}."

    await db.commit()
    await db.refresh(payout)
    read = commercial_settlement_payout_read(payout)
    return CommercialSettlementPayoutCallbackRead(
        accepted=True,
        signature_required=signature_required,
        signature_validated=signature_validated,
        matched_by=matched_by,
        payout_reference=payout.payout_reference,
        payout_batch_reference=payout.payout_batch_reference,
        payout_status=payout.status,
        message=f"Commercial settlement payout callback reconciled as {payout.status}.",
        payout=read,
    )


async def accounting_export(
    db: AsyncSession,
    organization_id: UUID,
    system: str,
    basis: str,
) -> AccountingExportRead:
    await get_organization(db, organization_id)
    rows: list[AccountingExportRow] = []
    for payment in await list_payments(db, organization_id):
        rows.append(
            AccountingExportRow(
                row_type="invoice_payment",
                source_id=payment.id,
                account_code="1000:cash",
                memo=payment.notes or payment.method,
                debit=payment.amount,
                credit=Decimal("0"),
                currency=payment.currency,
                external_reference=payment.external_reference,
            )
        )
        rows.append(
            AccountingExportRow(
                row_type="invoice_revenue",
                source_id=payment.id,
                account_code="4100:program_revenue",
                memo=payment.notes or payment.method,
                debit=Decimal("0"),
                credit=payment.amount,
                currency=payment.currency,
                external_reference=payment.external_reference,
            )
        )
    for donation in await list_donations(db, organization_id):
        rows.append(
            AccountingExportRow(
                row_type="donation_revenue",
                source_id=donation.id,
                account_code="4200:donations",
                memo=donation.message or donation.donor_name,
                debit=Decimal("0"),
                credit=donation.amount,
                currency=donation.currency,
                external_reference=donation.external_reference,
            )
        )
    debit_total = sum((row.debit for row in rows), Decimal("0"))
    credit_total = sum((row.credit for row in rows), Decimal("0"))
    return AccountingExportRead(
        organization_id=organization_id,
        basis=basis,
        system=system,
        rows=rows,
        debit_total=debit_total.quantize(Decimal("0.01")),
        credit_total=credit_total.quantize(Decimal("0.01")),
    )


async def sync_accounting_export(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    system: str,
    basis: str,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> AccountingSyncRead:
    await ensure_manage_commercial(authz, identity, organization_id)
    export = await accounting_export(db, organization_id, system, basis)
    selected_settings = settings or get_settings()
    sync_reference = commercial_accounting_sync_reference(export)
    webhook_configured = bool(selected_settings.commercial_accounting_webhook_url)
    if selected_settings.commercial_accounting_sync_mode != "webhook" or not webhook_configured:
        return AccountingSyncRead(
            organization_id=organization_id,
            basis=basis,
            system=system,
            mode=selected_settings.commercial_accounting_sync_mode,
            delivered=False,
            row_count=len(export.rows),
            debit_total=export.debit_total,
            credit_total=export.credit_total,
            sync_reference=sync_reference,
            failure_reason=None if webhook_configured else "Accounting webhook URL is not configured.",
            webhook_configured=webhook_configured,
        )

    payload = commercial_accounting_sync_payload(export, sync_reference)
    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(time.time()))
    headers = await commercial_accounting_sync_headers(selected_settings, raw_body, timestamp)
    provider_status_code: int | None = None
    failure_reason: str | None = None
    delivered = False
    try:
        async with httpx.AsyncClient(timeout=selected_settings.commercial_accounting_timeout_seconds) as client:
            response = await client.post(
                selected_settings.commercial_accounting_webhook_url,
                json=payload,
                headers=headers,
            )
        provider_status_code = response.status_code
        delivered = 200 <= response.status_code < 300
        if not delivered:
            failure_reason = f"Accounting webhook returned {response.status_code}: {response.text[:500]}"
    except httpx.HTTPError as error:
        failure_reason = f"Accounting webhook failed: {error}"

    return AccountingSyncRead(
        organization_id=organization_id,
        basis=basis,
        system=system,
        mode=selected_settings.commercial_accounting_sync_mode,
        delivered=delivered,
        row_count=len(export.rows),
        debit_total=export.debit_total,
        credit_total=export.credit_total,
        sync_reference=sync_reference,
        provider_status_code=provider_status_code,
        failure_reason=failure_reason,
        webhook_configured=webhook_configured,
    )


async def sponsorship_dashboard(db: AsyncSession, organization_id: UUID) -> list[SponsorshipDashboardRead]:
    sponsors = await list_sponsors(db, organization_id)
    agreements = await list_sponsorships(db, organization_id)
    activation_counts = await sponsor_activation_counts_by_sponsor(db, organization_id)
    dashboards = []
    for sponsor in sponsors:
        sponsor_agreements = [agreement for agreement in agreements if agreement.sponsor_id == sponsor.id]
        contracted_value = sum((agreement.value_amount for agreement in sponsor_agreements), Decimal("0"))
        active_value = sum(
            (agreement.value_amount for agreement in sponsor_agreements if agreement.status == CommercialStatus.ACTIVE),
            Decimal("0"),
        )
        deliverable_count = sum(count_deliverables(agreement.deliverables) for agreement in sponsor_agreements)
        activation_count = sum(1 for agreement in sponsor_agreements if agreement.activation_notes) + activation_counts.get(
            sponsor.id,
            0,
        )
        roi_score = min(100, int((active_value / contracted_value * 70) if contracted_value else 0) + min(deliverable_count * 5, 20) + min(activation_count * 10, 10))
        dashboards.append(
            SponsorshipDashboardRead(
                sponsor_id=sponsor.id,
                sponsor_name=sponsor.name,
                agreement_count=len(sponsor_agreements),
                contracted_value=contracted_value.quantize(Decimal("0.01")),
                active_value=active_value.quantize(Decimal("0.01")),
                deliverable_count=deliverable_count,
                activation_count=activation_count,
                roi_score=roi_score,
                recommendation=sponsorship_recommendation(roi_score),
            )
        )
    return dashboards


async def sponsor_portal(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID | None = None,
) -> SponsorPortalRead:
    email = identity.email.strip().casefold()
    if not email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sponsor email required")

    sponsor_query = select(Sponsor).where(func.lower(Sponsor.contact_email) == email)
    if organization_id is not None:
        sponsor_query = sponsor_query.where(Sponsor.organization_id == organization_id)
    sponsors = list((await db.scalars(sponsor_query.order_by(Sponsor.name))).all())
    if not sponsors:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor portal not found")

    organization_ids = {sponsor.organization_id for sponsor in sponsors}
    organizations = {
        organization.id: organization
        for organization in (
            await db.scalars(select(Organization).where(Organization.id.in_(organization_ids)))
        ).all()
    }
    sponsor_ids = [sponsor.id for sponsor in sponsors]
    agreements = list(
        (
            await db.scalars(
                select(SponsorshipAgreement)
                .where(SponsorshipAgreement.sponsor_id.in_(sponsor_ids))
                .order_by(SponsorshipAgreement.created_at.desc())
            )
        ).all()
    )
    invoices = list(
        (
            await db.scalars(
                select(FinanceInvoice)
                .where(FinanceInvoice.sponsor_id.in_(sponsor_ids))
                .order_by(FinanceInvoice.due_on.is_(None), FinanceInvoice.due_on, FinanceInvoice.created_at.desc())
            )
        ).all()
    )
    event_ids = {agreement.event_id for agreement in agreements if agreement.event_id is not None}
    events = {
        event.id: event
        for event in (
            await db.scalars(select(Event).where(Event.id.in_(event_ids)))
        ).all()
    } if event_ids else {}
    sponsors_by_id = {sponsor.id: sponsor for sponsor in sponsors}

    active_value = sum(
        (agreement.value_amount for agreement in agreements if agreement.status == CommercialStatus.ACTIVE),
        Decimal("0"),
    )
    outstanding_invoice_amount = sum(
        (commercial_invoice_open_amount(invoice) for invoice in invoices),
        Decimal("0"),
    )
    deliverable_count = sum(count_deliverables(agreement.deliverables) for agreement in agreements)
    activation_count = sum(1 for agreement in agreements if agreement.activation_notes)
    upcoming_event_count = sum(
        1
        for agreement in agreements
        if agreement.event_id in events and utc_datetime(events[agreement.event_id].starts_at) >= datetime.now(UTC)
    )
    roi_score = min(
        100,
        (60 if active_value > 0 else 0)
        + min(deliverable_count * 5, 25)
        + min(activation_count * 10, 15),
    )

    portal_invoices: list[SponsorPortalInvoiceRead] = []
    for invoice in invoices:
        if invoice.organization_id not in organizations or invoice.sponsor_id is None:
            continue
        provider = "manual_gateway"
        session_id = commercial_invoice_checkout_session_id(invoice, provider)
        open_amount = commercial_invoice_open_amount(invoice)
        portal_invoices.append(
            SponsorPortalInvoiceRead(
                id=invoice.id,
                organization_id=invoice.organization_id,
                organization_name=organizations[invoice.organization_id].name,
                sponsor_id=invoice.sponsor_id,
                invoice_number=invoice.invoice_number,
                title=invoice.title,
                amount_due=invoice.amount_due,
                amount_paid=invoice.amount_paid,
                outstanding_amount=open_amount,
                currency=invoice.currency,
                due_on=invoice.due_on,
                status=invoice.status,
                memo=invoice.memo,
                payment_session_id=session_id if open_amount > 0 else None,
                payment_session_url=(
                    commercial_invoice_checkout_session_url("/pay/sessions", session_id, invoice, provider)
                    if open_amount > 0
                    else None
                ),
                payment_session_status=commercial_invoice_checkout_session_status(invoice),
            )
        )

    return SponsorPortalRead(
        identity_email=email,
        sponsors=[
            SponsorPortalSponsorRead(
                id=sponsor.id,
                organization_id=sponsor.organization_id,
                organization_name=organizations[sponsor.organization_id].name,
                organization_slug=organizations[sponsor.organization_id].slug,
                sponsor_name=sponsor.name,
                industry=sponsor.industry,
                contact_name=sponsor.contact_name,
                contact_email=sponsor.contact_email,
                website_url=sponsor.website_url,
                brand_assets_url=sponsor.brand_assets_url,
                public_site_path=f"/site/{organizations[sponsor.organization_id].slug}",
            )
            for sponsor in sponsors
            if sponsor.organization_id in organizations
        ],
        agreements=[
            SponsorPortalAgreementRead(
                id=agreement.id,
                organization_id=agreement.organization_id,
                organization_name=organizations[agreement.organization_id].name,
                sponsor_id=agreement.sponsor_id,
                sponsor_name=sponsors_by_id[agreement.sponsor_id].name,
                event_id=agreement.event_id,
                event_title=events[agreement.event_id].title if agreement.event_id in events else None,
                event_starts_at=events[agreement.event_id].starts_at if agreement.event_id in events else None,
                event_venue_name=events[agreement.event_id].venue_name if agreement.event_id in events else None,
                name=agreement.name,
                tier=agreement.tier,
                value_amount=agreement.value_amount,
                currency=agreement.currency,
                starts_on=agreement.starts_on,
                ends_on=agreement.ends_on,
                deliverables=split_deliverables(agreement.deliverables),
                activation_notes=agreement.activation_notes,
                roi_notes=agreement.roi_notes,
                status=agreement.status,
            )
            for agreement in agreements
            if agreement.organization_id in organizations and agreement.sponsor_id in sponsors_by_id
        ],
        invoices=portal_invoices,
        summary=SponsorPortalSummaryRead(
            sponsor_count=len(sponsors),
            agreement_count=len(agreements),
            active_value=active_value.quantize(Decimal("0.01")),
            outstanding_invoice_amount=max(outstanding_invoice_amount, Decimal("0")).quantize(Decimal("0.01")),
            deliverable_count=deliverable_count,
            activation_count=activation_count,
            upcoming_event_count=upcoming_event_count,
            recommendation=sponsorship_recommendation(roi_score),
        ),
    )


async def commercial_summary(db: AsyncSession, organization_id: UUID) -> CommercialSummaryRead:
    sponsors = await list_sponsors(db, organization_id)
    sponsorships = await list_sponsorships(db, organization_id)
    campaigns = await list_campaigns(db, organization_id)
    ticket_products = await list_ticket_products(db, organization_id)
    tickets = await list_tickets(db, organization_id)
    invoices = await list_invoices(db, organization_id)
    return CommercialSummaryRead(
        organization_id=organization_id,
        sponsorship_value=sum((item.value_amount for item in sponsorships), Decimal("0")),
        fundraising_goal=sum((item.goal_amount for item in campaigns), Decimal("0")),
        fundraising_raised=sum((item.raised_amount for item in campaigns), Decimal("0")),
        ticket_revenue=sum((item.price * item.sold_count for item in ticket_products), Decimal("0")),
        invoice_outstanding=sum((item.amount_due - item.amount_paid for item in invoices), Decimal("0")),
        active_sponsors=len(sponsors),
        active_campaigns=sum(1 for item in campaigns if item.status == CommercialStatus.ACTIVE),
        tickets_sold=len(tickets),
        tickets_checked_in=sum(1 for ticket in tickets if ticket.status == TicketStatus.CHECKED_IN),
    )


async def list_donations(db: AsyncSession, organization_id: UUID) -> list[Donation]:
    return list(
        (
            await db.scalars(
                select(Donation)
                .where(Donation.organization_id == organization_id)
                .order_by(Donation.created_at.desc())
            )
        ).all()
    )


async def list_payments(db: AsyncSession, organization_id: UUID) -> list[FinancePayment]:
    return list(
        (
            await db.scalars(
                select(FinancePayment)
                .where(FinancePayment.organization_id == organization_id)
                .order_by(FinancePayment.received_at.desc())
            )
        ).all()
    )


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_sponsor_for_organization(db: AsyncSession, sponsor_id: UUID, organization_id: UUID) -> Sponsor:
    sponsor = await db.get(Sponsor, sponsor_id)
    if sponsor is None or sponsor.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor not found")
    return sponsor


async def get_sponsorship_for_organization(
    db: AsyncSession,
    sponsorship_agreement_id: UUID,
    organization_id: UUID,
) -> SponsorshipAgreement:
    agreement = await db.get(SponsorshipAgreement, sponsorship_agreement_id)
    if agreement is None or agreement.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsorship agreement not found")
    return agreement


async def get_fan_challenge_for_organization(
    db: AsyncSession,
    fan_challenge_id: UUID,
    organization_id: UUID,
) -> FanEngagementChallenge:
    challenge = await db.get(FanEngagementChallenge, fan_challenge_id)
    if challenge is None or challenge.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fan challenge not found")
    return challenge


async def get_activation_by_coupon(
    db: AsyncSession,
    organization_id: UUID,
    coupon_code: str,
) -> SponsorActivationCampaign:
    campaign = await db.scalar(
        select(SponsorActivationCampaign).where(
            SponsorActivationCampaign.organization_id == organization_id,
            SponsorActivationCampaign.coupon_code == normalize_coupon_code(coupon_code),
        )
    )
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor activation coupon not found")
    return campaign


async def get_sponsor_content_asset_for_organization(
    db: AsyncSession,
    content_asset_id: UUID,
    organization_id: UUID,
) -> SponsorContentAsset:
    asset = await db.get(SponsorContentAsset, content_asset_id)
    if asset is None or asset.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor content asset not found")
    return asset


async def get_sponsorship_milestone_for_organization(
    db: AsyncSession,
    milestone_id: UUID,
    organization_id: UUID,
) -> SponsorshipDeliverableMilestone:
    milestone = await db.get(SponsorshipDeliverableMilestone, milestone_id)
    if milestone is None or milestone.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsorship milestone not found")
    return milestone


async def get_campaign_for_organization(db: AsyncSession, campaign_id: UUID, organization_id: UUID) -> FundraisingCampaign:
    campaign = await db.get(FundraisingCampaign, campaign_id)
    if campaign is None or campaign.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


async def get_grant_opportunity_for_organization(
    db: AsyncSession,
    grant_opportunity_id: UUID,
    organization_id: UUID,
) -> GrantOpportunity:
    opportunity = await db.get(GrantOpportunity, grant_opportunity_id)
    if opportunity is None or opportunity.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant opportunity not found")
    return opportunity


async def get_grant_application_for_organization(
    db: AsyncSession,
    grant_application_id: UUID,
    organization_id: UUID,
) -> GrantApplication:
    application = await db.get(GrantApplication, grant_application_id)
    if application is None or application.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant application not found")
    return application


async def get_ticket_product_for_organization(db: AsyncSession, ticket_product_id: UUID, organization_id: UUID) -> TicketProduct:
    ticket_product = await db.get(TicketProduct, ticket_product_id)
    if ticket_product is None or ticket_product.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket product not found")
    return ticket_product


async def get_invoice_for_organization(db: AsyncSession, invoice_id: UUID, organization_id: UUID) -> FinanceInvoice:
    invoice = await db.get(FinanceInvoice, invoice_id)
    if invoice is None or invoice.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


async def get_invoice_for_organization_by_id(db: AsyncSession, invoice_id: UUID) -> FinanceInvoice:
    invoice = await db.get(FinanceInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


async def get_team_for_organization(db: AsyncSession, team_id: UUID, organization_id: UUID) -> Team:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


async def get_event_for_organization(db: AsyncSession, event_id: UUID, organization_id: UUID) -> Event:
    event = await db.get(Event, event_id)
    if event is None or event.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


async def tickets_remaining_in_order(
    db: AsyncSession,
    order_id: UUID,
    excluding_ticket_id: UUID,
) -> int:
    tickets = list(
        (
            await db.scalars(
                select(Ticket).where(
                    Ticket.ticket_order_id == order_id,
                    Ticket.id != excluding_ticket_id,
                    Ticket.status != TicketStatus.REFUNDED,
                )
            )
        ).all()
    )
    return len(tickets)


def count_deliverables(deliverables: str | None) -> int:
    return len(split_deliverables(deliverables))


def split_deliverables(deliverables: str | None) -> list[str]:
    if not deliverables:
        return []
    return [part.strip() for part in deliverables.replace("\n", ",").split(",") if part.strip()]


def utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def commercial_invoice_checkout_session_id(invoice: FinanceInvoice, provider: str) -> str:
    token = sha256(f"commercial-session:{invoice.id}:{invoice.invoice_number}:{invoice.amount_due}:{provider}".encode()).hexdigest()
    provider_token = sub(r"[^a-z0-9]+", "-", provider.lower()).strip("-")[:24] or "processor"
    return f"cics_{provider_token}_{token[:24]}"


def commercial_invoice_provider_session_id(invoice: FinanceInvoice, provider: str) -> str:
    token = sha256(
        f"commercial-provider-session:{invoice.id}:{invoice.invoice_number}:{commercial_invoice_open_amount(invoice)}:{provider}".encode()
    ).hexdigest()
    provider_token = sub(r"[^a-z0-9]+", "-", provider.lower()).strip("-")[:24] or "processor"
    return f"cpay_{provider_token}_{token[:24]}"


def commercial_invoice_checkout_session_url(
    base_url: str,
    session_id: str,
    invoice: FinanceInvoice,
    provider: str,
) -> str:
    provider_token = quote(provider, safe="")
    return f"{base_url.rstrip('/')}/{session_id}?invoice_id={invoice.id}&provider={provider_token}&kind=commercial"


def commercial_invoice_open_amount(invoice: FinanceInvoice) -> Decimal:
    return max(invoice.amount_due - invoice.amount_paid, Decimal("0.00")).quantize(Decimal("0.01"))


def commercial_invoice_checkout_session_status(invoice: FinanceInvoice) -> str:
    return "paid" if commercial_invoice_open_amount(invoice) <= 0 else "ready"


def commercial_invoice_hosted_checkout_read(
    invoice: FinanceInvoice,
    provider: str,
    session_id: str,
) -> CommercialInvoiceHostedCheckoutRead:
    if invoice.sponsor_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor invoice checkout session not found")
    open_amount = commercial_invoice_open_amount(invoice)
    return CommercialInvoiceHostedCheckoutRead(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        organization_id=invoice.organization_id,
        sponsor_id=invoice.sponsor_id,
        billed_person_id=invoice.person_id,
        title=invoice.title,
        memo=invoice.memo,
        due_on=invoice.due_on,
        amount_due=invoice.amount_due,
        amount_paid=invoice.amount_paid,
        open_amount=open_amount,
        currency=invoice.currency,
        status=invoice.status.value,
        provider=provider,
        session_id=session_id,
        session_status=commercial_invoice_checkout_session_status(invoice),
        client_reference=f"sponsor-invoice-checkout:{invoice.id}",
        payment_methods=["card", "mobile_money", "bank_transfer", "cash_office"],
        settlement_endpoint=f"/api/v1/commercial/invoice-checkout-sessions/{session_id}/settle",
        checkout_summary=(
            f"{invoice.title} has {open_amount} {invoice.currency} outstanding."
            if open_amount > 0
            else f"{invoice.title} is fully paid."
        ),
    )


def commercial_invoice_provider_checkout_payload(
    invoice: FinanceInvoice,
    session: CommercialInvoiceProviderCheckoutRead,
    payload: CommercialInvoiceProviderCheckoutCreate,
) -> dict[str, Any]:
    return {
        "event_type": "commercial.invoice_payment_session.create",
        "organization_id": str(invoice.organization_id),
        "invoice_id": str(invoice.id),
        "sponsor_id": str(invoice.sponsor_id),
        "invoice_number": invoice.invoice_number,
        "title": invoice.title,
        "provider": session.provider,
        "provider_session_id": session.provider_session_id,
        "local_session_id": session.local_session_id,
        "client_reference": session.client_reference,
        "amount": str(session.amount),
        "currency": session.currency,
        "payment_method": payload.payment_method,
        "customer_email": payload.customer_email,
        "success_url": payload.success_url,
        "cancel_url": payload.cancel_url,
        "webhook_event": "commercial.invoice_payment_webhook",
        "created_at": session.created_at.isoformat(),
    }


def commercial_payment_session_provider_response(status_code: int, body: str) -> str:
    return json.dumps(
        {
            "provider_status_code": status_code,
            "body": body[:1000],
        },
        sort_keys=True,
    )


def commercial_payment_session_read(session: CommercialPaymentSession) -> CommercialInvoiceProviderCheckoutRead:
    return CommercialInvoiceProviderCheckoutRead(
        id=session.id,
        invoice_id=session.invoice_id,
        organization_id=session.organization_id,
        sponsor_id=session.sponsor_id,
        provider=session.provider,
        mode=session.mode,
        status=session.status,
        provider_session_id=session.provider_session_id,
        local_session_id=session.local_session_id,
        client_reference=session.client_reference,
        amount=session.amount,
        currency=session.currency,
        redirect_url=session.redirect_url,
        success_url=session.success_url,
        cancel_url=session.cancel_url,
        customer_email=session.customer_email,
        payment_method=session.payment_method,
        provider_status_code=session.provider_status_code,
        provider_response=session.provider_response,
        failure_reason=session.failure_reason,
        webhook_configured=session.webhook_configured,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


async def commercial_payment_session_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Afrolete-Commercial-Session-Timestamp": timestamp,
    }
    key = await resolve_commercial_secret(
        settings,
        env_value=settings.commercial_payment_session_webhook_key,
        path=settings.commercial_payment_session_webhook_key_secret_path,
        field_name=settings.commercial_payment_session_webhook_key_secret_field,
        label="commercial payment session webhook key",
    )
    if key:
        headers["X-Afrolete-Commercial-Session-Key"] = key
        headers["X-Afrolete-Commercial-Session-Signature"] = "sha256=" + hmac.new(
            key.encode(),
            timestamp.encode() + b"." + raw_body,
            sha256,
        ).hexdigest()
    return headers


def normalize_commercial_invoice_payment_webhook(
    payload: CommercialInvoicePaymentWebhookCreate | dict[str, Any],
    provider_hint: str | None = None,
) -> CommercialInvoicePaymentWebhookCreate:
    if isinstance(payload, CommercialInvoicePaymentWebhookCreate):
        return payload
    provider_payload = payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else payload
    provider = (provider_hint or str(payload.get("provider") or "")).strip().lower()
    if not provider:
        provider = detect_commercial_payment_provider(provider_payload)
    if has_commercial_internal_payment_shape(payload) or has_commercial_internal_payment_shape(provider_payload):
        normalized = dict(provider_payload if has_commercial_internal_payment_shape(provider_payload) else payload)
        normalized["provider"] = normalized.get("provider") or provider or "provider_neutral"
        return CommercialInvoicePaymentWebhookCreate.model_validate(normalized)
    if provider == "stripe":
        return normalize_stripe_commercial_payment(provider_payload)
    if provider in {"mpesa", "m-pesa", "safaricom_mpesa"}:
        return normalize_mpesa_commercial_payment(provider_payload)
    if provider == "paypal":
        return normalize_paypal_commercial_payment(provider_payload)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported commercial payment webhook payload")


def has_commercial_internal_payment_shape(payload: dict[str, Any]) -> bool:
    return bool(payload.get("invoice_id") and payload.get("session_id"))


def detect_commercial_payment_provider(payload: dict[str, Any]) -> str:
    if "Body" in payload and isinstance(payload.get("Body"), dict):
        return "mpesa"
    if "data" in payload and "type" in payload:
        return "stripe"
    if "resource" in payload and "event_type" in payload:
        return "paypal"
    return "provider_neutral"


def normalize_stripe_commercial_payment(payload: dict[str, Any]) -> CommercialInvoicePaymentWebhookCreate:
    event_type = str(payload.get("type") or "payment.succeeded")
    obj = nested_dict(payload, "data", "object")
    metadata = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    amount = decimal_minor_units(obj.get("amount_total") or obj.get("amount_paid"))
    payment_status = str(obj.get("payment_status") or obj.get("status") or "").lower()
    return CommercialInvoicePaymentWebhookCreate(
        invoice_id=uuid_or_none(metadata.get("invoice_id") or metadata.get("afrolete_invoice_id")),
        session_id=string_or_none(metadata.get("session_id") or metadata.get("afrolete_session_id")),
        provider="stripe",
        event_type=event_type,
        amount=amount,
        currency=string_or_none(obj.get("currency"), upper=True),
        method="stripe_checkout",
        external_payment_id=string_or_none(obj.get("payment_intent") or obj.get("id")),
        status="succeeded" if event_type == "checkout.session.completed" or payment_status == "paid" else "pending",
        raw_reference=json.dumps(payload, sort_keys=True)[:2000],
    )


def normalize_mpesa_commercial_payment(payload: dict[str, Any]) -> CommercialInvoicePaymentWebhookCreate:
    callback = nested_dict(payload, "Body", "stkCallback")
    items = callback_metadata_items(callback)
    result_code = str(callback.get("ResultCode") or "")
    metadata = callback.get("Metadata") if isinstance(callback.get("Metadata"), dict) else payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    return CommercialInvoicePaymentWebhookCreate(
        invoice_id=uuid_or_none(metadata.get("invoice_id") or metadata.get("afrolete_invoice_id")),
        session_id=string_or_none(metadata.get("session_id") or metadata.get("afrolete_session_id")),
        provider="mpesa",
        event_type="mpesa.stk_callback",
        amount=decimal_or_none(items.get("Amount")),
        currency=string_or_none(metadata.get("currency"), upper=True) or "KES",
        method="mpesa_stk",
        external_payment_id=string_or_none(items.get("MpesaReceiptNumber") or callback.get("CheckoutRequestID")),
        status="succeeded" if result_code == "0" else "failed",
        raw_reference=json.dumps(payload, sort_keys=True)[:2000],
    )


def normalize_paypal_commercial_payment(payload: dict[str, Any]) -> CommercialInvoicePaymentWebhookCreate:
    event_type = str(payload.get("event_type") or "")
    resource = payload.get("resource") if isinstance(payload.get("resource"), dict) else {}
    purchase_unit = first_dict(resource.get("purchase_units"))
    capture = first_dict(nested_dict(purchase_unit, "payments").get("captures"))
    amount_payload = capture.get("amount") if isinstance(capture.get("amount"), dict) else resource.get("amount", {})
    reference_metadata = parse_payment_reference(str(purchase_unit.get("reference_id") or resource.get("custom_id") or ""))
    return CommercialInvoicePaymentWebhookCreate(
        invoice_id=uuid_or_none(reference_metadata.get("invoice_id") or resource.get("invoice_id")),
        session_id=string_or_none(reference_metadata.get("session_id")),
        provider="paypal",
        event_type=event_type or "PAYMENT.CAPTURE.COMPLETED",
        amount=decimal_or_none(amount_payload.get("value")),
        currency=string_or_none(amount_payload.get("currency_code"), upper=True),
        method="paypal_checkout",
        external_payment_id=string_or_none(capture.get("id") or resource.get("id")),
        status="succeeded" if event_type == "PAYMENT.CAPTURE.COMPLETED" or capture.get("status") == "COMPLETED" else "pending",
        raw_reference=json.dumps(payload, sort_keys=True)[:2000],
    )


def nested_dict(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def first_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
    return value if isinstance(value, dict) else {}


def callback_metadata_items(callback: dict[str, Any]) -> dict[str, Any]:
    metadata = callback.get("CallbackMetadata")
    items = metadata.get("Item") if isinstance(metadata, dict) else []
    result: dict[str, Any] = {}
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("Name"):
                result[str(item["Name"])] = item.get("Value")
    return result


def parse_payment_reference(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in value.replace("|", ";").split(";"):
        if "=" not in part:
            continue
        key, item_value = part.split("=", 1)
        result[key.strip()] = item_value.strip()
    return result


def uuid_or_none(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def string_or_none(value: Any, upper: bool = False) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper() if upper else text


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid payment amount") from exc


def decimal_minor_units(value: Any) -> Decimal | None:
    amount = decimal_or_none(value)
    if amount is None:
        return None
    return (amount / Decimal("100")).quantize(Decimal("0.01"))


def commercial_accounting_sync_reference(export: AccountingExportRead) -> str:
    payload = commercial_accounting_sync_payload(export, sync_reference=None)
    digest = sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return f"acct_{export.system}_{export.basis}_{digest[:16]}"


def commercial_accounting_sync_payload(
    export: AccountingExportRead,
    sync_reference: str | None,
) -> dict[str, Any]:
    return {
        "organization_id": str(export.organization_id),
        "system": export.system,
        "basis": export.basis,
        "sync_reference": sync_reference,
        "row_count": len(export.rows),
        "debit_total": str(export.debit_total),
        "credit_total": str(export.credit_total),
        "rows": [
            {
                "row_type": row.row_type,
                "source_id": str(row.source_id),
                "account_code": row.account_code,
                "memo": row.memo,
                "debit": str(row.debit),
                "credit": str(row.credit),
                "currency": row.currency,
                "external_reference": row.external_reference,
            }
            for row in export.rows
        ],
    }


async def commercial_accounting_sync_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Afrolete-Commercial-Accounting-Timestamp": timestamp,
    }
    key = await resolve_commercial_secret(
        settings,
        env_value=settings.commercial_accounting_webhook_key,
        path=settings.commercial_accounting_webhook_key_secret_path,
        field_name=settings.commercial_accounting_webhook_key_secret_field,
        label="commercial accounting webhook key",
    )
    if key:
        headers["X-Afrolete-Commercial-Accounting-Key"] = key
        headers["X-Afrolete-Commercial-Accounting-Signature"] = "sha256=" + hmac.new(
            key.encode(),
            timestamp.encode() + b"." + raw_body,
            sha256,
        ).hexdigest()
    return headers


def commercial_invoice_filing_date(invoice: FinanceInvoice) -> date:
    if invoice.due_on is not None:
        return invoice.due_on
    created_at = invoice.created_at
    if created_at.tzinfo is None:
        return created_at.date()
    return created_at.astimezone(UTC).date()


def commercial_filing_currency(invoices: list[FinanceInvoice]) -> str:
    currencies = {invoice.currency for invoice in invoices}
    if len(currencies) == 1:
        return next(iter(currencies))
    return "mixed" if currencies else "USD"


def commercial_tax_filing_reference(
    organization_id: UUID,
    jurisdiction: str,
    period_start: date,
    period_end: date,
) -> str:
    return (
        f"COMTAX-{jurisdiction.upper()}-{str(organization_id)[:8]}-"
        f"{period_start.strftime('%Y%m%d')}-{period_end.strftime('%Y%m%d')}"
    )


def commercial_tax_filing_payload(filing: CommercialTaxFilingRead) -> dict[str, Any]:
    return {
        "event_type": "commercial.tax_filing",
        "organization_id": str(filing.organization_id),
        "jurisdiction": filing.jurisdiction,
        "period_start": filing.period_start.isoformat(),
        "period_end": filing.period_end.isoformat(),
        "invoice_count": filing.invoice_count,
        "taxable_subtotal": str(filing.taxable_subtotal),
        "tax_rate": str(filing.tax_rate),
        "tax_amount": str(filing.tax_amount),
        "gross_total": str(filing.gross_total),
        "outstanding_total": str(filing.outstanding_total),
        "currency": filing.currency,
        "reverse_charge": filing.reverse_charge,
        "filing_reference": filing.filing_reference,
        "filed_at": filing.filed_at.isoformat(),
    }


async def commercial_tax_filing_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Afrolete-Commercial-Tax-Timestamp": timestamp,
    }
    key = await resolve_commercial_secret(
        settings,
        env_value=settings.commercial_tax_filing_webhook_key,
        path=settings.commercial_tax_filing_webhook_key_secret_path,
        field_name=settings.commercial_tax_filing_webhook_key_secret_field,
        label="commercial tax filing webhook key",
    )
    if key:
        headers["X-Afrolete-Commercial-Tax-Key"] = key
        headers["X-Afrolete-Commercial-Tax-Signature"] = "sha256=" + hmac.new(
            key.encode(),
            timestamp.encode() + b"." + raw_body,
            sha256,
        ).hexdigest()
    return headers


def commercial_payout_batch_reference(settlement: PaymentSettlementRead) -> str:
    payload = {
        "organization_id": str(settlement.organization_id),
        "provider": settlement.provider,
        "payout_reference": settlement.payout_reference,
        "gross_amount": str(settlement.gross_amount),
        "fee_amount": str(settlement.fee_amount),
        "net_amount": str(settlement.net_amount),
        "currency": settlement.currency,
        "line_count": settlement.line_count,
    }
    digest = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"payout_{settlement.provider}_{digest[:16]}"


def commercial_payout_payload(payout: CommercialSettlementPayoutRead) -> dict[str, Any]:
    return {
        "event_type": "commercial.settlement_payout",
        "organization_id": str(payout.organization_id),
        "provider": payout.provider,
        "idempotency_key": payout.idempotency_key,
        "payout_reference": payout.payout_reference,
        "payout_batch_reference": payout.payout_batch_reference,
        "gross_amount": str(payout.gross_amount),
        "fee_amount": str(payout.fee_amount),
        "net_amount": str(payout.net_amount),
        "currency": payout.currency,
        "line_count": payout.line_count,
        "executed_at": payout.executed_at.isoformat(),
    }


async def commercial_payout_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Afrolete-Commercial-Payout-Timestamp": timestamp,
    }
    key = await resolve_commercial_secret(
        settings,
        env_value=settings.commercial_payout_webhook_key,
        path=settings.commercial_payout_webhook_key_secret_path,
        field_name=settings.commercial_payout_webhook_key_secret_field,
        label="commercial payout webhook key",
    )
    if key:
        headers["X-Afrolete-Commercial-Payout-Key"] = key
        headers["X-Afrolete-Commercial-Payout-Signature"] = "sha256=" + hmac.new(
            key.encode(),
            timestamp.encode() + b"." + raw_body,
            sha256,
        ).hexdigest()
    return headers


def commercial_payout_idempotency_key(settlement: PaymentSettlementRead, batch_reference: str) -> str:
    token = sha256(
        f"commercial-payout:{settlement.organization_id}:{settlement.provider}:{batch_reference}:{settlement.net_amount}".encode()
    ).hexdigest()
    provider_token = sub(r"[^a-z0-9]+", "-", settlement.provider.lower()).strip("-")[:24] or "provider"
    return f"csp_{provider_token}_{token[:24]}"


def commercial_payout_provider_response(status_code: int, body: str) -> str:
    return json.dumps(
        {
            "provider_status_code": status_code,
            "body": body[:1000],
        },
        sort_keys=True,
    )


def normalize_commercial_payout_status(status_value: str) -> str:
    normalized = status_value.strip().lower().replace("-", "_")
    if normalized in {"paid", "succeeded", "success", "completed", "complete", "settled"}:
        return "paid"
    if normalized in {"queued", "pending", "processing", "submitted", "accepted"}:
        return "queued"
    if normalized in {"failed", "failure", "rejected", "declined", "error"}:
        return "failed"
    if normalized in {"cancelled", "canceled", "voided"}:
        return "cancelled"
    if normalized in {"returned", "reversed", "refunded", "chargeback"}:
        return "returned"
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported commercial payout callback status")


def commercial_payout_callback_match(
    payload: CommercialSettlementPayoutCallbackCreate,
    payout: CommercialSettlementPayout,
) -> str:
    if payload.payout_reference and payload.payout_reference == payout.payout_reference:
        return "payout_reference"
    if payload.payout_batch_reference and payload.payout_batch_reference == payout.payout_batch_reference:
        return "payout_batch_reference"
    return "idempotency_key"


def commercial_payout_callback_response(
    payload: CommercialSettlementPayoutCallbackCreate,
    *,
    signature_required: bool,
    signature_validated: bool,
    matched_by: str,
    reconciled_at: datetime,
) -> str:
    return json.dumps(
        {
            "provider": payload.provider,
            "payout_reference": payload.payout_reference,
            "payout_batch_reference": payload.payout_batch_reference,
            "idempotency_key": payload.idempotency_key,
            "status": payload.status,
            "external_event_id": payload.external_event_id,
            "provider_status_code": payload.provider_status_code,
            "matched_by": matched_by,
            "signature_required": signature_required,
            "signature_validated": signature_validated,
            "reconciled_at": reconciled_at.isoformat(),
            "raw_payload": payload.raw_payload,
        },
        sort_keys=True,
    )


def commercial_settlement_payout_read(payout: CommercialSettlementPayout) -> CommercialSettlementPayoutRead:
    return CommercialSettlementPayoutRead(
        id=payout.id,
        organization_id=payout.organization_id,
        provider=payout.provider,
        currency=payout.currency,
        status=payout.status,
        delivery_mode=payout.delivery_mode,
        delivery_attempted=payout.delivery_attempted,
        delivered=payout.delivered,
        payout_reference=payout.payout_reference,
        payout_batch_reference=payout.payout_batch_reference,
        idempotency_key=payout.idempotency_key,
        gross_amount=payout.gross_amount,
        fee_amount=payout.fee_amount,
        net_amount=payout.net_amount,
        line_count=payout.line_count,
        destination=payout.destination,
        provider_status_code=payout.provider_status_code,
        provider_response=payout.provider_response,
        failure_reason=payout.failure_reason,
        processed_by_person_id=payout.processed_by_person_id,
        executed_at=payout.executed_at,
        reconciled_at=payout.reconciled_at,
        external_event_id=payout.external_event_id,
    )


async def validate_commercial_payout_callback_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = await resolve_commercial_secret(
        selected_settings,
        env_value=selected_settings.commercial_payout_callback_signing_key,
        path=selected_settings.commercial_payout_callback_signing_key_secret_path,
        field_name=selected_settings.commercial_payout_callback_signing_key_secret_field,
        label="commercial payout callback signing key",
    )
    if not signing_key:
        return False, False
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing commercial payout callback signature")
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid commercial payout callback timestamp") from exc
    age = abs(int(time.time()) - timestamp)
    if age > selected_settings.commercial_payout_callback_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale commercial payout callback signature")
    expected = hmac.new(
        signing_key.encode(),
        timestamp_header.encode() + b"." + raw_body,
        sha256,
    ).hexdigest()
    submitted = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid commercial payout callback signature")
    return True, True


async def validate_commercial_invoice_payment_webhook_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = await resolve_commercial_secret(
        selected_settings,
        env_value=selected_settings.commercial_payment_webhook_signing_key,
        path=selected_settings.commercial_payment_webhook_signing_key_secret_path,
        field_name=selected_settings.commercial_payment_webhook_signing_key_secret_field,
        label="commercial payment webhook signing key",
    )
    if not signing_key:
        return False, False
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing commercial payment webhook signature")
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid commercial payment webhook timestamp") from exc
    age = abs(int(time.time()) - timestamp)
    if age > selected_settings.commercial_payment_webhook_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale commercial payment webhook signature")
    expected = hmac.new(
        signing_key.encode(),
        timestamp_header.encode() + b"." + raw_body,
        sha256,
    ).hexdigest()
    submitted = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid commercial payment webhook signature")
    return True, True


async def resolve_commercial_secret(
    settings: Settings,
    *,
    env_value: str,
    path: str,
    field_name: str,
    label: str,
) -> str:
    return await resolve_secret(
        settings,
        env_value=env_value,
        path=path,
        field_name=field_name,
        label=label,
    )


def sponsorship_recommendation(roi_score: int) -> str:
    if roi_score >= 85:
        return "Renew and expand; activation is performing well."
    if roi_score >= 60:
        return "Keep active; add measurable deliverables and conversion tracking."
    return "Needs activation plan and sponsor-facing proof of value."


async def sponsor_activation_counts_by_sponsor(db: AsyncSession, organization_id: UUID) -> dict[UUID, int]:
    rows = (
        await db.execute(
            select(SponsorActivationCampaign.sponsor_id, func.count(SponsorActivationCampaign.id))
            .where(SponsorActivationCampaign.organization_id == organization_id)
            .group_by(SponsorActivationCampaign.sponsor_id)
        )
    ).all()
    return {sponsor_id: int(count) for sponsor_id, count in rows}


async def sponsor_content_counts_by_sponsor(db: AsyncSession, organization_id: UUID) -> dict[UUID, int]:
    rows = (
        await db.execute(
            select(SponsorContentAsset.sponsor_id, func.count(SponsorContentAsset.id))
            .where(SponsorContentAsset.organization_id == organization_id)
            .group_by(SponsorContentAsset.sponsor_id)
        )
    ).all()
    return {sponsor_id: int(count) for sponsor_id, count in rows}


async def sponsorship_milestone_read(
    db: AsyncSession,
    milestone: SponsorshipDeliverableMilestone,
) -> SponsorshipDeliverableMilestoneRead:
    sponsor = await db.get(Sponsor, milestone.sponsor_id)
    agreement = await db.get(SponsorshipAgreement, milestone.sponsorship_agreement_id)
    return SponsorshipDeliverableMilestoneRead(
        id=milestone.id,
        organization_id=milestone.organization_id,
        sponsor_id=milestone.sponsor_id,
        sponsorship_agreement_id=milestone.sponsorship_agreement_id,
        title=milestone.title,
        deliverable_type=milestone.deliverable_type,
        due_on=milestone.due_on,
        completed_on=milestone.completed_on,
        status=milestone.status,
        owner_name=milestone.owner_name,
        evidence_url=milestone.evidence_url,
        notes=milestone.notes,
        sponsor_name=sponsor.name if sponsor else None,
        agreement_name=agreement.name if agreement else None,
    )


async def sponsor_interaction_read(db: AsyncSession, interaction: SponsorInteractionLog) -> SponsorInteractionRead:
    sponsor = await db.get(Sponsor, interaction.sponsor_id)
    agreement = (
        await db.get(SponsorshipAgreement, interaction.sponsorship_agreement_id)
        if interaction.sponsorship_agreement_id
        else None
    )
    return SponsorInteractionRead(
        id=interaction.id,
        organization_id=interaction.organization_id,
        sponsor_id=interaction.sponsor_id,
        sponsorship_agreement_id=interaction.sponsorship_agreement_id,
        sponsor_name=sponsor.name if sponsor else None,
        agreement_name=agreement.name if agreement else None,
        contact_name=interaction.contact_name,
        contact_email=interaction.contact_email,
        interaction_type=interaction.interaction_type,
        subject=interaction.subject,
        summary=interaction.summary,
        sentiment=interaction.sentiment,
        follow_up_on=interaction.follow_up_on,
        occurred_at=interaction.occurred_at,
    )


def sponsor_renewal_forecast(
    sponsor: Sponsor,
    agreements: list[SponsorshipAgreement],
    milestones: list[SponsorshipDeliverableMilestone],
    interactions: list[SponsorInteractionLog],
    activation_count: int,
    content_count: int,
    today: date,
) -> SponsorRenewalForecastRead:
    active_value = sum((agreement.value_amount for agreement in agreements if agreement.status == CommercialStatus.ACTIVE), Decimal("0"))
    completed = sum(1 for milestone in milestones if milestone.status == "completed")
    overdue = sum(1 for milestone in milestones if milestone.due_on and milestone.due_on < today and milestone.status != "completed")
    upcoming = sum(
        1
        for milestone in milestones
        if milestone.due_on and today <= milestone.due_on <= today + timedelta(days=30) and milestone.status != "completed"
    )
    positive_interactions = sum(1 for interaction in interactions if interaction.sentiment in {"positive", "renewal_ready"})
    latest_interaction = max((interaction.occurred_at for interaction in interactions), default=None)
    score = min(
        100,
        (35 if active_value > 0 else 0)
        + min(completed * 12, 30)
        + min(activation_count * 10, 15)
        + min(content_count * 5, 10)
        + min(positive_interactions * 5, 10)
        - min(overdue * 15, 45),
    )
    signal = "renewal_ready" if score >= 80 else "nurture" if score >= 55 else "at_risk"
    return SponsorRenewalForecastRead(
        sponsor_id=sponsor.id,
        sponsor_name=sponsor.name,
        active_value=active_value.quantize(Decimal("0.01")),
        renewal_score=max(0, score),
        renewal_signal=signal,
        milestone_count=len(milestones),
        completed_milestone_count=completed,
        overdue_milestone_count=overdue,
        upcoming_milestone_count=upcoming,
        interaction_count=len(interactions),
        last_interaction_at=latest_interaction,
        next_best_action=sponsor_next_best_action(signal, overdue, upcoming, len(interactions), activation_count),
    )


def sponsor_next_best_action(signal: str, overdue: int, upcoming: int, interaction_count: int, activation_count: int) -> str:
    if overdue:
        return "Resolve overdue sponsor deliverables before renewal outreach."
    if interaction_count == 0:
        return "Log a sponsor check-in and confirm success metrics."
    if activation_count == 0:
        return "Launch a measurable activation or coupon campaign."
    if upcoming:
        return "Prepare evidence for upcoming sponsor deliverables."
    if signal == "renewal_ready":
        return "Schedule renewal conversation with ROI proof."
    return "Send stewardship update with content, activation, and invoice status."


def sponsor_stewardship_recommendations(
    forecasts: list[SponsorRenewalForecastRead],
    overdue_milestone_count: int,
    follow_up_due_count: int,
) -> list[str]:
    recommendations: list[str] = []
    if overdue_milestone_count:
        recommendations.append("Clear overdue sponsor milestones before pitching renewals.")
    if follow_up_due_count:
        recommendations.append("Complete due sponsor follow-ups and record outcomes.")
    if any(forecast.renewal_signal == "renewal_ready" for forecast in forecasts):
        recommendations.append("Package ROI evidence for renewal-ready sponsors.")
    if any(forecast.interaction_count == 0 for forecast in forecasts):
        recommendations.append("Log sponsor communication touchpoints for every active partner.")
    if not forecasts:
        recommendations.append("Create sponsors and agreements before stewardship forecasting.")
    return recommendations[:5]


def normalize_coupon_code(value: str) -> str:
    normalized = sub(r"[^A-Z0-9_-]+", "-", value.strip().upper()).strip("-")
    return normalized[:80] or "SPONSOR"


def sponsor_activation_points(purchase_amount: Decimal) -> int:
    return min(500, max(25, int(purchase_amount)))


async def sponsor_activation_campaign_read(
    db: AsyncSession,
    campaign: SponsorActivationCampaign,
) -> SponsorActivationCampaignRead:
    sponsor = await db.get(Sponsor, campaign.sponsor_id)
    challenge = await db.get(FanEngagementChallenge, campaign.fan_challenge_id) if campaign.fan_challenge_id else None
    return SponsorActivationCampaignRead(
        id=campaign.id,
        organization_id=campaign.organization_id,
        sponsor_id=campaign.sponsor_id,
        sponsorship_agreement_id=campaign.sponsorship_agreement_id,
        fan_challenge_id=campaign.fan_challenge_id,
        title=campaign.title,
        objective=campaign.objective,
        offer_summary=campaign.offer_summary,
        coupon_code=campaign.coupon_code,
        discount_type=campaign.discount_type,
        discount_value=campaign.discount_value,
        target_url=campaign.target_url,
        starts_at=campaign.starts_at,
        ends_at=campaign.ends_at,
        status=campaign.status,
        sponsor_name=sponsor.name if sponsor else None,
        challenge_title=challenge.title if challenge else None,
        impression_count=campaign.impression_count,
        signup_count=campaign.signup_count,
        redemption_count=campaign.redemption_count,
        conversion_value=campaign.conversion_value,
    )


async def sponsor_coupon_redemption_read(
    db: AsyncSession,
    redemption: SponsorCouponRedemption,
    campaign: SponsorActivationCampaign | None = None,
) -> SponsorCouponRedemptionRead:
    campaign = campaign or await db.get(SponsorActivationCampaign, redemption.activation_campaign_id)
    sponsor = await db.get(Sponsor, campaign.sponsor_id) if campaign else None
    return SponsorCouponRedemptionRead(
        id=redemption.id,
        organization_id=redemption.organization_id,
        activation_campaign_id=redemption.activation_campaign_id,
        coupon_code=campaign.coupon_code if campaign else "",
        sponsor_name=sponsor.name if sponsor else None,
        supporter_profile_id=redemption.supporter_profile_id,
        redeemer_name=redemption.redeemer_name,
        redeemer_email=redemption.redeemer_email,
        source=redemption.source,
        order_reference=redemption.order_reference,
        discount_amount=redemption.discount_amount,
        purchase_amount=redemption.purchase_amount,
        status=redemption.status,
        redeemed_at=redemption.redeemed_at,
    )


def sponsor_activation_roi_signal(total_redemptions: int, conversion_value: Decimal) -> str:
    if total_redemptions >= 25 or conversion_value >= Decimal("1000"):
        return "strong"
    if total_redemptions >= 5 or conversion_value > 0:
        return "building"
    return "needs_distribution"


def sponsor_activation_recommendations(
    campaigns: list[SponsorActivationCampaign],
    total_redemptions: int,
    conversion_value: Decimal,
) -> list[str]:
    recommendations: list[str] = []
    if not campaigns:
        recommendations.append("Create a sponsor activation campaign with a measurable coupon code.")
    if campaigns and not total_redemptions:
        recommendations.append("Publish the coupon through the public fan zone and matchday communications.")
    if campaigns and conversion_value == 0:
        recommendations.append("Connect coupon redemption tracking to merchandise, tickets, or sponsor landing pages.")
    if total_redemptions:
        recommendations.append("Share redemption and conversion results with sponsors before renewal conversations.")
    return recommendations[:5]


def normalize_content_decision(value: str) -> str:
    decision = value.strip().lower().replace(" ", "_").replace("-", "_")
    allowed = {"pending_review", "approved", "changes_requested", "rejected", "expired"}
    if decision not in allowed:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported sponsor content decision")
    return decision


async def sponsor_content_asset_read(db: AsyncSession, asset: SponsorContentAsset) -> SponsorContentAssetRead:
    sponsor = await db.get(Sponsor, asset.sponsor_id)
    return SponsorContentAssetRead(
        id=asset.id,
        organization_id=asset.organization_id,
        sponsor_id=asset.sponsor_id,
        sponsorship_agreement_id=asset.sponsorship_agreement_id,
        title=asset.title,
        asset_type=asset.asset_type,
        channel=asset.channel,
        format=asset.format,
        asset_url=asset.asset_url,
        thumbnail_url=asset.thumbnail_url,
        usage_guidelines=asset.usage_guidelines,
        rights_summary=asset.rights_summary,
        player_rights_required=asset.player_rights_required,
        expires_at=asset.expires_at,
        version=asset.version,
        sponsor_name=sponsor.name if sponsor else None,
        approval_status=asset.approval_status,
        approved_at=asset.approved_at,
        approved_by_name=asset.approved_by_name,
        usage_count=asset.usage_count,
        impression_count=asset.impression_count,
        engagement_count=asset.engagement_count,
    )


def sponsor_content_approval_read(
    review: SponsorContentApprovalReview,
    asset: SponsorContentAsset | None = None,
) -> SponsorContentApprovalRead:
    return SponsorContentApprovalRead(
        id=review.id,
        organization_id=review.organization_id,
        content_asset_id=review.content_asset_id,
        reviewer_name=review.reviewer_name,
        reviewer_email=review.reviewer_email,
        decision=review.decision,
        notes=review.notes,
        content_title=asset.title if asset else None,
        decided_at=review.decided_at,
    )


async def sponsor_activation_placement_read(
    db: AsyncSession,
    placement: SponsorActivationPlacement,
) -> SponsorActivationPlacementRead:
    sponsor = await db.get(Sponsor, placement.sponsor_id)
    asset = await db.get(SponsorContentAsset, placement.content_asset_id) if placement.content_asset_id else None
    campaign = (
        await db.get(SponsorActivationCampaign, placement.activation_campaign_id)
        if placement.activation_campaign_id
        else None
    )
    event = await db.get(Event, placement.event_id) if placement.event_id else None
    return SponsorActivationPlacementRead(
        id=placement.id,
        organization_id=placement.organization_id,
        sponsor_id=placement.sponsor_id,
        content_asset_id=placement.content_asset_id,
        activation_campaign_id=placement.activation_campaign_id,
        event_id=placement.event_id,
        placement_name=placement.placement_name,
        placement_type=placement.placement_type,
        channel=placement.channel,
        scheduled_at=placement.scheduled_at,
        location_name=placement.location_name,
        staff_requirements=placement.staff_requirements,
        inventory_checklist=placement.inventory_checklist,
        weather_contingency=placement.weather_contingency,
        expected_impressions=placement.expected_impressions,
        notes=placement.notes,
        sponsor_name=sponsor.name if sponsor else None,
        content_title=asset.title if asset else None,
        campaign_title=campaign.title if campaign else None,
        event_title=event.title if event else None,
        status=placement.status,
        actual_impressions=placement.actual_impressions,
        actual_engagements=placement.actual_engagements,
    )


def sponsor_content_recommendations(
    assets: list[SponsorContentAsset],
    placements: list[SponsorActivationPlacement],
) -> list[str]:
    recommendations: list[str] = []
    if not assets:
        recommendations.append("Upload sponsor brand assets, campaign creative, and rights notes before activation.")
    if any(asset.approval_status == "pending_review" for asset in assets):
        recommendations.append("Review pending sponsor content before placing it on public channels.")
    if assets and not placements:
        recommendations.append("Schedule approved sponsor content into event, social, newsletter, or venue placements.")
    if any(asset.player_rights_required and asset.approval_status != "approved" for asset in assets):
        recommendations.append("Confirm player image rights before using athlete-facing sponsor creative.")
    if placements:
        recommendations.append("Collect post-placement impressions and engagement to strengthen sponsor ROI reporting.")
    return recommendations[:5]
