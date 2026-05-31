from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import CommercialStatus, TicketStatus


class Sponsor(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsors"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(120), index=True)
    contact_name: Mapped[str | None] = mapped_column(String(180))
    contact_email: Mapped[str | None] = mapped_column(String(320), index=True)
    website_url: Mapped[str | None] = mapped_column(String(500))
    brand_assets_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class SponsorshipAgreement(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsorship_agreements"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    value_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    starts_on: Mapped[date | None] = mapped_column(index=True)
    ends_on: Mapped[date | None] = mapped_column(index=True)
    deliverables: Mapped[str | None] = mapped_column(Text)
    activation_notes: Mapped[str | None] = mapped_column(Text)
    roi_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class SponsorshipDeliverableMilestone(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsorship_deliverable_milestones"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    sponsorship_agreement_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsorship_agreements.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    deliverable_type: Mapped[str] = mapped_column(String(80), default="contract", nullable=False, index=True)
    due_on: Mapped[date | None] = mapped_column(index=True)
    completed_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(40), default="planned", nullable=False, index=True)
    owner_name: Mapped[str | None] = mapped_column(String(180), index=True)
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class SponsorInteractionLog(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsor_interaction_logs"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    sponsorship_agreement_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("sponsorship_agreements.id"), index=True
    )
    contact_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), index=True)
    interaction_type: Mapped[str] = mapped_column(String(80), default="email", nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(40), default="neutral", nullable=False, index=True)
    follow_up_on: Mapped[date | None] = mapped_column(index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class SponsorActivationCampaign(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsor_activation_campaigns"
    __table_args__ = (UniqueConstraint("organization_id", "coupon_code"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    sponsorship_agreement_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("sponsorship_agreements.id"), index=True
    )
    fan_challenge_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("fan_engagement_challenges.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    objective: Mapped[str] = mapped_column(String(240), nullable=False)
    offer_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    coupon_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    discount_type: Mapped[str] = mapped_column(String(40), default="percent", nullable=False, index=True)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    target_url: Mapped[str | None] = mapped_column(String(500))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    impression_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    signup_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    redemption_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversion_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)


class SponsorCouponRedemption(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsor_coupon_redemptions"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    activation_campaign_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("sponsor_activation_campaigns.id"), index=True
    )
    supporter_profile_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("supporter_profiles.id"), index=True)
    redeemer_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    redeemer_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(80), default="public_site", nullable=False, index=True)
    order_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    purchase_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.PAID,
        nullable=False,
        index=True,
    )
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class SponsorContentAsset(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsor_content_assets"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    sponsorship_agreement_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("sponsorship_agreements.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(80), default="link", nullable=False, index=True)
    asset_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    usage_guidelines: Mapped[str | None] = mapped_column(Text)
    rights_summary: Mapped[str | None] = mapped_column(Text)
    player_rights_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(40), default="pending_review", nullable=False, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    approved_by_name: Mapped[str | None] = mapped_column(String(180))
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    impression_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class SponsorContentApprovalReview(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsor_content_approval_reviews"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    content_asset_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsor_content_assets.id"), index=True)
    reviewer_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    reviewer_email: Mapped[str | None] = mapped_column(String(320), index=True)
    decision: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class SponsorActivationPlacement(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsor_activation_placements"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    content_asset_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("sponsor_content_assets.id"), index=True)
    activation_campaign_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("sponsor_activation_campaigns.id"), index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    placement_name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    placement_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    location_name: Mapped[str | None] = mapped_column(String(180), index=True)
    staff_requirements: Mapped[str | None] = mapped_column(Text)
    inventory_checklist: Mapped[str | None] = mapped_column(Text)
    weather_contingency: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="planned", nullable=False, index=True)
    expected_impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actual_impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actual_engagements: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class FundraisingCampaign(IdMixin, TimestampMixin, Base):
    __tablename__ = "fundraising_campaigns"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(240), nullable=False)
    goal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    raised_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    starts_on: Mapped[date | None] = mapped_column(index=True)
    ends_on: Mapped[date | None] = mapped_column(index=True)
    public_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class Donation(IdMixin, TimestampMixin, Base):
    __tablename__ = "donations"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    campaign_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("fundraising_campaigns.id"), index=True)
    donor_profile_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("donor_profiles.id"), index=True)
    donor_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    donor_email: Mapped[str | None] = mapped_column(String(320), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.PAID,
        nullable=False,
        index=True,
    )


class DonorProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "donor_profiles"
    __table_args__ = (UniqueConstraint("organization_id", "email", name="uq_donor_profiles_org_email"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(80), index=True)
    donor_type: Mapped[str] = mapped_column(String(80), default="individual", nullable=False, index=True)
    segment: Mapped[str] = mapped_column(String(80), default="community", nullable=False, index=True)
    preferred_channel: Mapped[str] = mapped_column(String(80), default="email", nullable=False, index=True)
    giving_capacity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    lifetime_giving: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    last_gift_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    last_gift_on: Mapped[date | None] = mapped_column(index=True)
    next_ask_on: Mapped[date | None] = mapped_column(index=True)
    tags_json: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class DonorInteraction(IdMixin, TimestampMixin, Base):
    __tablename__ = "donor_interactions"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    donor_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("donor_profiles.id"), index=True)
    campaign_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("fundraising_campaigns.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    interaction_type: Mapped[str] = mapped_column(String(80), default="email", nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(80), default="email", nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(40), default="neutral", nullable=False, index=True)
    outcome: Mapped[str | None] = mapped_column(String(120), index=True)
    owner_name: Mapped[str | None] = mapped_column(String(180), index=True)
    next_follow_up_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(40), default="logged", nullable=False, index=True)


class DonorStewardshipPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "donor_stewardship_plans"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    donor_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("donor_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(80), default="cultivation", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(40), default="medium", nullable=False, index=True)
    target_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    due_on: Mapped[date | None] = mapped_column(index=True)
    completed_on: Mapped[date | None] = mapped_column(index=True)
    next_step: Mapped[str] = mapped_column(Text, default="", nullable=False)
    recognition_level: Mapped[str | None] = mapped_column(String(120), index=True)
    impact_story_needed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    owner_name: Mapped[str | None] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class GrantOpportunity(IdMixin, TimestampMixin, Base):
    __tablename__ = "grant_opportunities"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    funder_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    program_name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    impact_area: Mapped[str] = mapped_column(String(220), nullable=False)
    award_ceiling: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    matching_required: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    opens_on: Mapped[date | None] = mapped_column(index=True)
    due_on: Mapped[date | None] = mapped_column(index=True)
    eligibility_summary: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)


class GrantApplication(IdMixin, TimestampMixin, Base):
    __tablename__ = "grant_applications"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    grant_opportunity_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("grant_opportunities.id"), index=True)
    project_title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    awarded_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    submitted_on: Mapped[date | None] = mapped_column(index=True)
    decision_on: Mapped[date | None] = mapped_column(index=True)
    reporting_due_on: Mapped[date | None] = mapped_column(index=True)
    lead_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    narrative: Mapped[str | None] = mapped_column(Text)
    budget_summary: Mapped[str | None] = mapped_column(Text)
    impact_metrics: Mapped[str | None] = mapped_column(Text)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)


class GrantApplicationApproval(IdMixin, TimestampMixin, Base):
    __tablename__ = "grant_application_approvals"
    __table_args__ = (
        UniqueConstraint("grant_application_id", "approval_level", name="uq_grant_application_approvals_level"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    grant_application_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("grant_applications.id"), index=True)
    approval_level: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    reviewer_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    reviewer_email: Mapped[str | None] = mapped_column(String(320), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    request_notes: Mapped[str | None] = mapped_column(Text)
    decision_notes: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class GrantReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "grant_reports"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    grant_application_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("grant_applications.id"), index=True)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    due_on: Mapped[date] = mapped_column(index=True)
    submitted_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    narrative: Mapped[str | None] = mapped_column(Text)
    metrics_summary: Mapped[str | None] = mapped_column(Text)
    artifact_url: Mapped[str | None] = mapped_column(String(500))
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)


class MerchandiseProduct(IdMixin, TimestampMixin, Base):
    __tablename__ = "merchandise_products"
    __table_args__ = (UniqueConstraint("organization_id", "sku"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    inventory_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    personalization_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    variants: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class MerchandiseOrder(IdMixin, TimestampMixin, Base):
    __tablename__ = "merchandise_orders"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    buyer_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    buyer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    buyer_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    delivery_method: Mapped[str] = mapped_column(String(80), default="pickup", nullable=False, index=True)
    delivery_address: Mapped[str | None] = mapped_column(Text)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    external_payment_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.PAID,
        nullable=False,
        index=True,
    )
    fulfillment_status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False, index=True)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class MerchandiseOrderLine(IdMixin, TimestampMixin, Base):
    __tablename__ = "merchandise_order_lines"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    merchandise_order_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("merchandise_orders.id"), index=True)
    merchandise_product_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("merchandise_products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    size: Mapped[str | None] = mapped_column(String(40), index=True)
    color: Mapped[str | None] = mapped_column(String(80), index=True)
    personalization_name: Mapped[str | None] = mapped_column(String(120))
    personalization_number: Mapped[str | None] = mapped_column(String(20))
    fulfillment_status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False, index=True)


class TicketProduct(IdMixin, TimestampMixin, Base):
    __tablename__ = "ticket_products"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    sold_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    access_zone: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class TicketOrder(IdMixin, TimestampMixin, Base):
    __tablename__ = "ticket_orders"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    ticket_product_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("ticket_products.id"), index=True)
    buyer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    buyer_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    external_payment_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.PAID,
        nullable=False,
        index=True,
    )


class Ticket(IdMixin, TimestampMixin, Base):
    __tablename__ = "tickets"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    ticket_order_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("ticket_orders.id"), index=True)
    ticket_product_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("ticket_products.id"), index=True)
    holder_name: Mapped[str | None] = mapped_column(String(180))
    qr_token: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    status: Mapped[TicketStatus] = mapped_column(
        enum_type(TicketStatus),
        default=TicketStatus.ISSUED,
        nullable=False,
        index=True,
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    gate: Mapped[str | None] = mapped_column(String(80))


class TicketBundleOffer(IdMixin, TimestampMixin, Base):
    __tablename__ = "ticket_bundle_offers"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    ticket_product_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("ticket_products.id"), index=True)
    merchandise_product_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("merchandise_products.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    package_type: Mapped[str] = mapped_column(String(80), default="ticket_bundle", nullable=False, index=True)
    ticket_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    channel: Mapped[str] = mapped_column(String(80), default="online", nullable=False, index=True)
    sales_limit: Mapped[int | None] = mapped_column(Integer)
    sold_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class TicketSeatAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "ticket_seat_assignments"
    __table_args__ = (UniqueConstraint("ticket_id"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    ticket_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("tickets.id"), index=True)
    section: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    row: Mapped[str | None] = mapped_column(String(40), index=True)
    seat: Mapped[str | None] = mapped_column(String(40), index=True)
    access_zone: Mapped[str | None] = mapped_column(String(120), index=True)
    accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    companion_seat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class TicketResaleListing(IdMixin, TimestampMixin, Base):
    __tablename__ = "ticket_resale_listings"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    ticket_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("tickets.id"), index=True)
    seller_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    seller_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    resale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="listed", nullable=False, index=True)
    buyer_name: Mapped[str | None] = mapped_column(String(180), index=True)
    buyer_email: Mapped[str | None] = mapped_column(String(320), index=True)
    listed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class FinanceInvoice(IdMixin, TimestampMixin, Base):
    __tablename__ = "finance_invoices"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    sponsor_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    due_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.DRAFT,
        nullable=False,
        index=True,
    )
    memo: Mapped[str | None] = mapped_column(Text)


class FinancePayment(IdMixin, TimestampMixin, Base):
    __tablename__ = "finance_payments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    invoice_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("finance_invoices.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    method: Mapped[str] = mapped_column(String(80), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class FinancialBudget(IdMixin, TimestampMixin, Base):
    __tablename__ = "financial_budgets"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", "fiscal_year", name="uq_financial_budgets_org_name_year"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(nullable=False, index=True)
    budget_type: Mapped[str] = mapped_column(String(80), default="operating", nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(80), default="organization", nullable=False, index=True)
    scope_id: Mapped[UUID | None] = mapped_column(GUID(), index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    beginning_cash_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    minimum_cash_reserve: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    assumptions_json: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)


class FinancialBudgetLine(IdMixin, TimestampMixin, Base):
    __tablename__ = "financial_budget_lines"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    budget_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("financial_budgets.id"), index=True)
    line_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    department: Mapped[str | None] = mapped_column(String(120), index=True)
    amount_budgeted: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_actual: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    forecast_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cash_timing_month: Mapped[str | None] = mapped_column(String(20), index=True)
    funding_source: Mapped[str | None] = mapped_column(String(120), index=True)
    restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    variance_reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class FinancialForecastScenario(IdMixin, TimestampMixin, Base):
    __tablename__ = "financial_forecast_scenarios"
    __table_args__ = (
        UniqueConstraint("budget_id", "name", name="uq_financial_forecast_scenarios_budget_name"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    budget_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("financial_budgets.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    scenario_type: Mapped[str] = mapped_column(String(60), default="base", nullable=False, index=True)
    revenue_adjustment_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    expense_adjustment_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    cash_adjustment_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    membership_growth_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    facility_utilization_percent: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    assumptions_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class FinancialStatementPackage(IdMixin, TimestampMixin, Base):
    __tablename__ = "financial_statement_packages"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    statement_type: Mapped[str] = mapped_column(String(80), default="monthly", nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(nullable=False, index=True)
    basis: Mapped[str] = mapped_column(String(40), default="management", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    prepared_by_name: Mapped[str | None] = mapped_column(String(180), index=True)
    profit_loss_json: Mapped[str] = mapped_column(Text, nullable=False)
    balance_sheet_json: Mapped[str] = mapped_column(Text, nullable=False)
    cash_flow_json: Mapped[str] = mapped_column(Text, nullable=False)
    highlights_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="generated", nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class CommercialPaymentSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "commercial_payment_sessions"
    __table_args__ = (UniqueConstraint("organization_id", "provider", "local_session_id"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    invoice_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("finance_invoices.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(40), default="local", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="local_ready", nullable=False, index=True)
    provider_session_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    local_session_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    client_reference: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    redirect_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    success_url: Mapped[str | None] = mapped_column(String(800))
    cancel_url: Mapped[str | None] = mapped_column(String(800))
    customer_email: Mapped[str | None] = mapped_column(String(320), index=True)
    payment_method: Mapped[str] = mapped_column(String(80), default="card", nullable=False, index=True)
    webhook_configured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    provider_status_code: Mapped[int | None] = mapped_column(Integer)
    provider_response: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)


class CommercialSettlementPayout(IdMixin, TimestampMixin, Base):
    __tablename__ = "commercial_settlement_payouts"
    __table_args__ = (UniqueConstraint("organization_id", "provider", "payout_batch_reference"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    payout_reference: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    payout_batch_reference: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="prepared", nullable=False, index=True)
    delivery_mode: Mapped[str] = mapped_column(String(40), default="record_only", nullable=False, index=True)
    delivery_attempted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)
    destination: Mapped[str | None] = mapped_column(String(500))
    provider_status_code: Mapped[int | None] = mapped_column(Integer)
    provider_response: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    processed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    external_event_id: Mapped[str | None] = mapped_column(String(180), index=True)
    callback_payload: Mapped[str | None] = mapped_column(Text)
