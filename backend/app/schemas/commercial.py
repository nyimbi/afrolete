from typing import Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import CommercialStatus, TicketStatus


class SponsorCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    industry: str | None = Field(default=None, max_length=120)
    contact_name: str | None = Field(default=None, max_length=180)
    contact_email: str | None = Field(default=None, max_length=320)
    website_url: str | None = Field(default=None, max_length=500)
    brand_assets_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class SponsorRead(SponsorCreate):
    id: UUID


class SponsorshipAgreementCreate(BaseModel):
    organization_id: UUID
    sponsor_id: UUID
    event_id: UUID | None = None
    name: str = Field(min_length=2, max_length=220)
    tier: str = Field(min_length=2, max_length=80)
    value_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starts_on: date | None = None
    ends_on: date | None = None
    deliverables: str | None = Field(default=None, max_length=4000)
    activation_notes: str | None = Field(default=None, max_length=4000)
    roi_notes: str | None = Field(default=None, max_length=4000)


class SponsorshipAgreementRead(SponsorshipAgreementCreate):
    id: UUID
    status: CommercialStatus


class SponsorshipDeliverableMilestoneCreate(BaseModel):
    organization_id: UUID
    sponsor_id: UUID
    sponsorship_agreement_id: UUID
    title: str = Field(min_length=2, max_length=220)
    deliverable_type: str = Field(default="contract", min_length=2, max_length=80)
    due_on: date | None = None
    completed_on: date | None = None
    status: str = Field(default="planned", min_length=2, max_length=40)
    owner_name: str | None = Field(default=None, max_length=180)
    evidence_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class SponsorshipDeliverableMilestoneRead(SponsorshipDeliverableMilestoneCreate):
    id: UUID
    sponsor_name: str | None = None
    agreement_name: str | None = None


class SponsorInteractionCreate(BaseModel):
    organization_id: UUID
    sponsor_id: UUID
    sponsorship_agreement_id: UUID | None = None
    contact_name: str = Field(min_length=2, max_length=180)
    contact_email: str | None = Field(default=None, max_length=320)
    interaction_type: str = Field(default="email", min_length=2, max_length=80)
    subject: str = Field(min_length=2, max_length=220)
    summary: str = Field(min_length=2, max_length=4000)
    sentiment: str = Field(default="neutral", min_length=2, max_length=40)
    follow_up_on: date | None = None
    occurred_at: datetime | None = None


class SponsorInteractionRead(BaseModel):
    id: UUID
    organization_id: UUID
    sponsor_id: UUID
    sponsorship_agreement_id: UUID | None
    sponsor_name: str | None = None
    agreement_name: str | None = None
    contact_name: str
    contact_email: str | None
    interaction_type: str
    subject: str
    summary: str
    sentiment: str
    follow_up_on: date | None
    occurred_at: datetime


class SponsorRenewalForecastRead(BaseModel):
    sponsor_id: UUID
    sponsor_name: str
    active_value: Decimal
    renewal_score: int
    renewal_signal: str
    milestone_count: int
    completed_milestone_count: int
    overdue_milestone_count: int
    upcoming_milestone_count: int
    interaction_count: int
    last_interaction_at: datetime | None
    next_best_action: str


class SponsorStewardshipDashboardRead(BaseModel):
    organization_id: UUID
    sponsor_count: int
    milestone_count: int
    overdue_milestone_count: int
    interaction_count: int
    follow_up_due_count: int
    forecasts: list[SponsorRenewalForecastRead]
    recommendations: list[str]


class SponsorActivationCampaignCreate(BaseModel):
    organization_id: UUID
    sponsor_id: UUID
    sponsorship_agreement_id: UUID | None = None
    fan_challenge_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    objective: str = Field(min_length=2, max_length=240)
    offer_summary: str = Field(default="", max_length=4000)
    coupon_code: str = Field(min_length=2, max_length=80)
    discount_type: str = Field(default="percent", min_length=2, max_length=40)
    discount_value: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    target_url: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class SponsorActivationCampaignRead(SponsorActivationCampaignCreate):
    id: UUID
    status: CommercialStatus
    sponsor_name: str | None = None
    challenge_title: str | None = None
    impression_count: int
    signup_count: int
    redemption_count: int
    conversion_value: Decimal


class SponsorCouponRedemptionCreate(BaseModel):
    organization_id: UUID
    coupon_code: str = Field(min_length=2, max_length=80)
    supporter_profile_id: UUID | None = None
    redeemer_name: str = Field(min_length=2, max_length=180)
    redeemer_email: str = Field(min_length=3, max_length=320)
    source: str = Field(default="public_site", min_length=2, max_length=80)
    order_reference: str | None = Field(default=None, max_length=240)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    purchase_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)


class SponsorCouponRedemptionRead(BaseModel):
    id: UUID
    organization_id: UUID
    activation_campaign_id: UUID
    coupon_code: str
    sponsor_name: str | None = None
    supporter_profile_id: UUID | None
    redeemer_name: str
    redeemer_email: str
    source: str
    order_reference: str | None
    discount_amount: Decimal
    purchase_amount: Decimal
    status: CommercialStatus
    redeemed_at: datetime


class SponsorActivationDashboardRead(BaseModel):
    organization_id: UUID
    campaign_count: int
    active_campaign_count: int
    total_impressions: int
    total_signups: int
    total_redemptions: int
    conversion_value: Decimal
    top_coupon_code: str | None
    roi_signal: str
    recommendations: list[str]


class SponsorContentAssetCreate(BaseModel):
    organization_id: UUID
    sponsor_id: UUID
    sponsorship_agreement_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    asset_type: str = Field(default="brand_asset", min_length=2, max_length=80)
    channel: str = Field(default="digital", min_length=2, max_length=80)
    format: str = Field(default="link", min_length=2, max_length=80)
    asset_url: str = Field(min_length=3, max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    usage_guidelines: str | None = Field(default=None, max_length=4000)
    rights_summary: str | None = Field(default=None, max_length=4000)
    player_rights_required: bool = False
    expires_at: datetime | None = None
    version: int = Field(default=1, ge=1)


class SponsorContentAssetRead(SponsorContentAssetCreate):
    id: UUID
    sponsor_name: str | None = None
    approval_status: str
    approved_at: datetime | None
    approved_by_name: str | None
    usage_count: int
    impression_count: int
    engagement_count: int


class SponsorContentApprovalCreate(BaseModel):
    organization_id: UUID
    content_asset_id: UUID
    reviewer_name: str = Field(min_length=2, max_length=180)
    reviewer_email: str | None = Field(default=None, max_length=320)
    decision: str = Field(min_length=2, max_length=40)
    notes: str | None = Field(default=None, max_length=4000)


class SponsorContentApprovalRead(SponsorContentApprovalCreate):
    id: UUID
    content_title: str | None = None
    decided_at: datetime


class SponsorActivationPlacementCreate(BaseModel):
    organization_id: UUID
    sponsor_id: UUID
    content_asset_id: UUID | None = None
    activation_campaign_id: UUID | None = None
    event_id: UUID | None = None
    placement_name: str = Field(min_length=2, max_length=220)
    placement_type: str = Field(default="digital_signage", min_length=2, max_length=80)
    channel: str = Field(default="event_day", min_length=2, max_length=80)
    scheduled_at: datetime | None = None
    location_name: str | None = Field(default=None, max_length=180)
    staff_requirements: str | None = Field(default=None, max_length=4000)
    inventory_checklist: str | None = Field(default=None, max_length=4000)
    weather_contingency: str | None = Field(default=None, max_length=4000)
    expected_impressions: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=4000)


class SponsorActivationPlacementRead(SponsorActivationPlacementCreate):
    id: UUID
    sponsor_name: str | None = None
    content_title: str | None = None
    campaign_title: str | None = None
    event_title: str | None = None
    status: str
    actual_impressions: int
    actual_engagements: int


class SponsorDigitalSignagePlaylistItemRead(BaseModel):
    slot_index: int
    duration_seconds: int
    placement_id: UUID
    sponsor_id: UUID
    sponsor_name: str | None = None
    content_asset_id: UUID | None = None
    content_title: str
    asset_url: str | None = None
    thumbnail_url: str | None = None
    format: str
    placement_name: str
    placement_type: str
    channel: str
    location_name: str | None = None
    event_id: UUID | None = None
    event_title: str | None = None
    scheduled_at: datetime | None = None
    campaign_title: str | None = None
    coupon_code: str | None = None
    target_url: str | None = None
    rights_status: str
    expected_impressions: int
    warnings: list[str] = Field(default_factory=list)


class SponsorDigitalSignagePlaylistRead(BaseModel):
    organization_id: UUID
    screen_name: str
    location_name: str | None = None
    event_id: UUID | None = None
    generated_at: datetime
    slot_count: int
    total_duration_seconds: int
    approved_slot_count: int
    review_required_count: int
    rotation_policy: str
    items: list[SponsorDigitalSignagePlaylistItemRead]
    warnings: list[str] = Field(default_factory=list)


class SponsorDigitalSignagePlaybackCreate(BaseModel):
    organization_id: UUID
    placement_id: UUID
    content_asset_id: UUID | None = None
    activation_campaign_id: UUID | None = None
    screen_name: str = Field(default="Main scoreboard", min_length=2, max_length=120)
    device_id: str | None = Field(default=None, max_length=160)
    slot_index: int = Field(default=1, ge=1, le=10000)
    played_at: datetime | None = None
    duration_seconds: int = Field(default=12, ge=1, le=3600)
    estimated_impressions: int = Field(default=0, ge=0, le=1_000_000)
    engagements: int = Field(default=0, ge=0, le=1_000_000)
    playback_status: str = Field(default="played", min_length=2, max_length=40)
    evidence_ref: str | None = Field(default=None, max_length=500)


class SponsorDigitalSignagePlaybackRead(BaseModel):
    organization_id: UUID
    placement: SponsorActivationPlacementRead
    content_asset: SponsorContentAssetRead | None = None
    activation_campaign: SponsorActivationCampaignRead | None = None
    screen_name: str
    device_id: str | None = None
    slot_index: int
    played_at: datetime
    duration_seconds: int
    estimated_impressions: int
    engagements: int
    playback_status: str
    evidence_ref: str | None = None
    message: str


class SponsorContentDashboardRead(BaseModel):
    organization_id: UUID
    asset_count: int
    approved_asset_count: int
    pending_asset_count: int
    expiring_asset_count: int
    placement_count: int
    planned_placement_count: int
    total_expected_impressions: int
    total_actual_impressions: int
    recommendations: list[str]


class FundraisingCampaignCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    name: str = Field(min_length=2, max_length=220)
    purpose: str = Field(min_length=2, max_length=240)
    goal_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starts_on: date | None = None
    ends_on: date | None = None
    public_url: str | None = Field(default=None, max_length=500)


class FundraisingCampaignRead(FundraisingCampaignCreate):
    id: UUID
    raised_amount: Decimal
    status: CommercialStatus


class DonationCreate(BaseModel):
    organization_id: UUID
    campaign_id: UUID
    donor_profile_id: UUID | None = None
    donor_name: str = Field(min_length=2, max_length=180)
    donor_email: str | None = Field(default=None, max_length=320)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    external_reference: str | None = Field(default=None, max_length=240)
    message: str | None = Field(default=None, max_length=4000)


class DonationRead(DonationCreate):
    id: UUID
    status: CommercialStatus
    donor_lifetime_giving: Decimal | None = None


class DonationTaxReceiptCreate(BaseModel):
    issued_on: date | None = None
    tax_year: int | None = Field(default=None, ge=1900, le=2200)
    jurisdiction: str = Field(default="local", min_length=2, max_length=120)
    organization_tax_id: str | None = Field(default=None, max_length=120)
    deductible_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=4000)


class DonationTaxReceiptRead(BaseModel):
    id: UUID
    organization_id: UUID
    donation_id: UUID
    donor_profile_id: UUID | None
    receipt_number: str
    issued_on: date
    tax_year: int
    jurisdiction: str
    donor_name: str
    donor_email: str | None
    organization_name: str
    organization_tax_id: str | None
    deductible_amount: Decimal
    currency: str
    status: str
    content_markdown: str
    content_checksum: str
    download_filename: str
    notes: str | None


class DonorProfileCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=80)
    donor_type: str = Field(default="individual", pattern="^(individual|family|corporate|foundation|alumni|major_gift|in_kind)$")
    segment: str = Field(default="community", max_length=80)
    preferred_channel: str = Field(default="email", max_length=80)
    giving_capacity: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    next_ask_on: date | None = None
    tags: list[str] = Field(default_factory=list, max_length=40)
    notes: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="active", pattern="^(active|watch|paused|archived)$")


class DonorProfileRead(DonorProfileCreate):
    id: UUID
    lifetime_giving: Decimal
    last_gift_amount: Decimal | None
    last_gift_on: date | None
    donation_count: int = 0
    interaction_count: int = 0
    active_plan_count: int = 0


class DonorInteractionCreate(BaseModel):
    organization_id: UUID
    donor_profile_id: UUID
    campaign_id: UUID | None = None
    occurred_at: datetime | None = None
    interaction_type: str = Field(default="email", max_length=80)
    channel: str = Field(default="email", max_length=80)
    subject: str = Field(min_length=2, max_length=220)
    summary: str = Field(min_length=2, max_length=4000)
    sentiment: str = Field(default="neutral", pattern="^(positive|neutral|concern|negative)$")
    outcome: str | None = Field(default=None, max_length=120)
    owner_name: str | None = Field(default=None, max_length=180)
    next_follow_up_on: date | None = None
    status: str = Field(default="logged", pattern="^(logged|follow_up_due|completed|archived)$")


class DonorInteractionRead(DonorInteractionCreate):
    id: UUID
    donor_name: str | None = None
    donor_email: str | None = None
    campaign_name: str | None = None
    occurred_at: datetime


class DonorStewardshipPlanCreate(BaseModel):
    organization_id: UUID
    donor_profile_id: UUID
    name: str = Field(min_length=2, max_length=220)
    stage: str = Field(default="cultivation", pattern="^(identification|cultivation|solicitation|recognition|stewardship|renewal)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    target_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    due_on: date | None = None
    next_step: str = Field(default="", max_length=4000)
    recognition_level: str | None = Field(default=None, max_length=120)
    impact_story_needed: bool = False
    owner_name: str | None = Field(default=None, max_length=180)
    status: str = Field(default="active", pattern="^(active|completed|paused|archived)$")


class DonorStewardshipPlanRead(DonorStewardshipPlanCreate):
    id: UUID
    donor_name: str | None = None
    donor_email: str | None = None
    completed_on: date | None = None
    overdue: bool = False


class DonorDashboardRead(BaseModel):
    organization_id: UUID
    donor_count: int
    active_donor_count: int
    major_donor_count: int
    lifetime_giving: Decimal
    average_gift: Decimal
    interaction_count: int
    follow_up_due_count: int
    active_plan_count: int
    overdue_plan_count: int
    impact_story_needed_count: int
    top_donor_name: str | None
    top_donor_lifetime_giving: Decimal
    stewardship_health: str
    recommendations: list[str]


class GrantOpportunityCreate(BaseModel):
    organization_id: UUID
    funder_name: str = Field(min_length=2, max_length=180)
    program_name: str = Field(min_length=2, max_length=220)
    category: str = Field(min_length=2, max_length=120)
    impact_area: str = Field(min_length=2, max_length=220)
    award_ceiling: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    matching_required: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    opens_on: date | None = None
    due_on: date | None = None
    eligibility_summary: str | None = Field(default=None, max_length=4000)
    requirements: str | None = Field(default=None, max_length=4000)
    source_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="open", min_length=2, max_length=40)


class GrantOpportunityRead(GrantOpportunityCreate):
    id: UUID


class GrantOpportunityDiscoveryRunCreate(BaseModel):
    organization_id: UUID
    profile_name: str = Field(default="default", min_length=2, max_length=160)
    focus_terms: list[str] = Field(default_factory=list, max_length=40)
    excluded_terms: list[str] = Field(default_factory=list, max_length=40)
    minimum_score: Decimal = Field(default=Decimal("0"), ge=0, le=100, max_digits=5, decimal_places=2)
    limit: int = Field(default=25, ge=1, le=100)


class GrantOpportunityMatchUpdate(BaseModel):
    alert_status: str | None = Field(default=None, pattern="^(new|reviewed|dismissed|snoozed|applied)$")
    notes: str | None = Field(default=None, max_length=4000)


class GrantOpportunityMatchRead(BaseModel):
    id: UUID
    organization_id: UUID
    grant_opportunity_id: UUID
    profile_name: str
    funder_name: str | None = None
    program_name: str | None = None
    category: str | None = None
    impact_area: str | None = None
    award_ceiling: Decimal | None = None
    currency: str | None = None
    due_on: date | None = None
    opportunity_status: str | None = None
    match_score: Decimal
    fit_band: str
    success_probability: Decimal
    matched_terms: list[str]
    missing_terms: list[str]
    focus_terms: list[str]
    excluded_terms: list[str]
    alert_status: str
    recommended_action: str
    generated_at: datetime
    notes: str | None = None


class GrantOpportunityDiscoveryRunRead(BaseModel):
    organization_id: UUID
    profile_name: str
    generated_count: int
    reviewed_count: int
    alert_count: int
    high_fit_count: int
    average_score: Decimal
    matches: list[GrantOpportunityMatchRead]
    recommendations: list[str]


class GrantSavedSearchCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    profile_name: str = Field(default="default", min_length=2, max_length=160)
    focus_terms: list[str] = Field(default_factory=list, max_length=40)
    excluded_terms: list[str] = Field(default_factory=list, max_length=40)
    minimum_score: Decimal = Field(default=Decimal("0"), ge=0, le=100, max_digits=5, decimal_places=2)
    limit: int = Field(default=25, ge=1, le=100)
    alert_enabled: bool = True
    alert_frequency: str = Field(default="weekly", pattern="^(daily|weekly|monthly|manual)$")
    alert_channel: str = Field(default="email", min_length=2, max_length=80)
    status: str = Field(default="active", pattern="^(active|paused|archived)$")
    notes: str | None = Field(default=None, max_length=4000)


class GrantSavedSearchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    profile_name: str | None = Field(default=None, min_length=2, max_length=160)
    focus_terms: list[str] | None = Field(default=None, max_length=40)
    excluded_terms: list[str] | None = Field(default=None, max_length=40)
    minimum_score: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    limit: int | None = Field(default=None, ge=1, le=100)
    alert_enabled: bool | None = None
    alert_frequency: str | None = Field(default=None, pattern="^(daily|weekly|monthly|manual)$")
    alert_channel: str | None = Field(default=None, min_length=2, max_length=80)
    status: str | None = Field(default=None, pattern="^(active|paused|archived)$")
    notes: str | None = Field(default=None, max_length=4000)


class GrantSavedSearchRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    profile_name: str
    focus_terms: list[str]
    excluded_terms: list[str]
    minimum_score: Decimal
    limit: int
    alert_enabled: bool
    alert_frequency: str
    alert_channel: str
    last_run_at: datetime | None
    last_match_count: int
    last_high_fit_count: int
    last_alert_count: int
    status: str
    notes: str | None


class GrantSavedSearchRunRead(BaseModel):
    saved_search: GrantSavedSearchRead
    discovery_run: GrantOpportunityDiscoveryRunRead


class GrantSavedSearchRunRecordRead(BaseModel):
    id: UUID
    organization_id: UUID
    saved_search_id: UUID
    saved_search_name: str | None = None
    triggered_by: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    match_count: int
    high_fit_count: int
    alert_count: int
    average_score: Decimal
    dry_run: bool
    message: str | None


class GrantSavedSearchAlertRunCreate(BaseModel):
    organization_id: UUID
    run_at: datetime | None = None
    limit: int = Field(default=25, ge=1, le=200)
    dry_run: bool = False


class GrantSavedSearchAlertRunRead(BaseModel):
    organization_id: UUID | None
    run_at: datetime
    eligible_count: int
    executed_count: int
    skipped_count: int
    failed_count: int
    match_count: int
    high_fit_count: int
    alert_count: int
    dry_run: bool
    saved_search_ids: list[UUID]
    run_record_ids: list[UUID]
    results: list[GrantSavedSearchRunRecordRead]


class GrantApplicationCreate(BaseModel):
    organization_id: UUID
    grant_opportunity_id: UUID
    project_title: str = Field(min_length=2, max_length=220)
    requested_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    awarded_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: str = Field(default="draft", min_length=2, max_length=40)
    submitted_on: date | None = None
    decision_on: date | None = None
    reporting_due_on: date | None = None
    lead_person_id: UUID | None = None
    narrative: str | None = Field(default=None, max_length=8000)
    budget_summary: str | None = Field(default=None, max_length=8000)
    impact_metrics: str | None = Field(default=None, max_length=8000)
    external_reference: str | None = Field(default=None, max_length=240)


class GrantApplicationRead(GrantApplicationCreate):
    id: UUID
    funder_name: str | None = None
    program_name: str | None = None
    approval_status: str = "not_requested"
    approval_pending_count: int = 0
    approval_approved_count: int = 0
    approval_rejected_count: int = 0


class GrantApplicationApprovalCreate(BaseModel):
    organization_id: UUID
    grant_application_id: UUID
    approval_level: str = Field(default="board", min_length=2, max_length=80)
    reviewer_name: str = Field(min_length=2, max_length=180)
    reviewer_email: str | None = Field(default=None, max_length=320)
    request_notes: str | None = Field(default=None, max_length=4000)


class GrantApplicationApprovalDecision(BaseModel):
    status: str = Field(pattern="^(approved|rejected|cancelled)$")
    decision_notes: str | None = Field(default=None, max_length=4000)


class GrantApplicationApprovalRead(GrantApplicationApprovalCreate):
    id: UUID
    status: str
    decision_notes: str | None = None
    requested_at: datetime
    decided_at: datetime | None = None
    project_title: str | None = None
    funder_name: str | None = None


class GrantSubmissionPackageCreate(BaseModel):
    organization_id: UUID
    grant_application_id: UUID
    package_name: str = Field(min_length=2, max_length=220)
    submission_method: str = Field(
        default="online_portal",
        pattern="^(online_portal|email|mail|hand_delivery|api|manual)$",
    )
    portal_url: str | None = Field(default=None, max_length=500)
    checklist_items: list[str] = Field(default_factory=list, max_length=80)
    completed_checklist_items: list[str] = Field(default_factory=list, max_length=80)
    document_manifest: list[str] = Field(default_factory=list, max_length=80)
    prepared_by_name: str | None = Field(default=None, max_length=180)
    status: str = Field(default="draft", pattern="^(draft|ready|submitted|confirmed|blocked)$")
    confirmation_reference: str | None = Field(default=None, max_length=240)
    blockers: list[str] = Field(default_factory=list, max_length=80)
    notes: str | None = Field(default=None, max_length=4000)


class GrantSubmissionPackageUpdate(BaseModel):
    status: str = Field(pattern="^(draft|ready|submitted|confirmed|blocked)$")
    confirmation_reference: str | None = Field(default=None, max_length=240)
    completed_checklist_items: list[str] | None = Field(default=None, max_length=80)
    blockers: list[str] | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=4000)


class GrantSubmissionPackageRead(GrantSubmissionPackageCreate):
    id: UUID
    project_title: str | None = None
    funder_name: str | None = None
    approval_status: str = "not_requested"
    checklist_total_count: int = 0
    checklist_completed_count: int = 0
    document_count: int = 0
    blocker_count: int = 0
    ready_to_submit: bool = False
    submitted_at: datetime | None = None
    confirmed_at: datetime | None = None


class GrantAwardRecordCreate(BaseModel):
    organization_id: UUID
    grant_application_id: UUID
    record_type: str = Field(
        pattern="^(payment|expenditure|compliance|milestone|site_visit|document)$",
    )
    title: str = Field(min_length=2, max_length=220)
    amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    category: str | None = Field(default=None, max_length=120)
    due_on: date | None = None
    occurred_on: date | None = None
    status: str = Field(default="planned", min_length=2, max_length=40)
    requirement: str | None = Field(default=None, max_length=4000)
    evidence_url: str | None = Field(default=None, max_length=500)
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class GrantAwardRecordRead(GrantAwardRecordCreate):
    id: UUID
    project_title: str | None = None
    funder_name: str | None = None
    overdue: bool = False


class GrantAwardSummaryRead(BaseModel):
    organization_id: UUID
    grant_application_id: UUID
    project_title: str | None = None
    funder_name: str | None = None
    awarded_amount: Decimal
    currency: str
    funds_received: Decimal
    expenditures_to_date: Decimal
    funds_balance: Decimal
    budget_remaining: Decimal
    compliance_total_count: int
    compliance_open_count: int
    milestone_total_count: int
    milestone_completed_count: int
    overdue_count: int
    next_due_on: date | None = None
    health: str
    recommendations: list[str]


class GrantPortfolioFunderRead(BaseModel):
    funder_name: str
    application_count: int
    awarded_amount: Decimal
    funds_received: Decimal
    expenditures_to_date: Decimal
    utilization_rate: Decimal
    target_achievement_rate: Decimal
    participant_count: int
    cost_per_participant: Decimal | None = None
    roi_multiple: Decimal | None = None
    health: str
    success_factors: list[str]


class GrantPortfolioSummaryRead(BaseModel):
    organization_id: UUID
    grant_count: int
    awarded_amount: Decimal
    funds_received: Decimal
    expenditures_to_date: Decimal
    funds_balance: Decimal
    utilization_rate: Decimal
    average_target_achievement: Decimal
    participant_count: int
    average_cost_per_participant: Decimal | None = None
    success_story_count: int
    media_coverage_count: int
    report_count: int
    overdue_report_count: int
    open_compliance_count: int
    portfolio_health: str
    success_factors: list[str]
    recommendations: list[str]
    funders: list[GrantPortfolioFunderRead]


class GrantReportCreate(BaseModel):
    organization_id: UUID
    grant_application_id: UUID
    report_type: str = Field(min_length=2, max_length=80)
    due_on: date
    submitted_on: date | None = None
    status: str = Field(default="draft", min_length=2, max_length=40)
    narrative: str | None = Field(default=None, max_length=8000)
    metrics_summary: str | None = Field(default=None, max_length=8000)
    artifact_url: str | None = Field(default=None, max_length=500)
    external_reference: str | None = Field(default=None, max_length=240)


class GrantReportGenerateCreate(BaseModel):
    organization_id: UUID
    grant_application_id: UUID
    report_type: str = Field(default="interim_progress", min_length=2, max_length=80)
    due_on: date
    status: str = Field(default="draft", min_length=2, max_length=40)
    template_name: str = Field(default="standard_funder_report", min_length=2, max_length=120)
    narrative_notes: str | None = Field(default=None, max_length=4000)
    artifact_url: str | None = Field(default=None, max_length=500)
    external_reference: str | None = Field(default=None, max_length=240)


class GrantReportRead(GrantReportCreate):
    id: UUID
    project_title: str | None = None


class GrantDashboardRead(BaseModel):
    organization_id: UUID
    opportunity_count: int
    active_opportunity_count: int
    application_count: int
    submitted_application_count: int
    awarded_application_count: int
    report_count: int
    due_soon_count: int
    overdue_report_count: int
    requested_amount: Decimal
    awarded_amount: Decimal
    match_required_amount: Decimal
    readiness_score: int
    pipeline_status: str
    recommendations: list[str]
    next_deadline_on: date | None


class MerchandiseProductCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    name: str = Field(min_length=2, max_length=180)
    sku: str = Field(min_length=2, max_length=80)
    category: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    cost: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    inventory_count: int = Field(default=0, ge=0)
    reorder_point: int = Field(default=0, ge=0)
    personalization_enabled: bool = False
    variants: str | None = Field(default=None, max_length=4000)
    image_url: str | None = Field(default=None, max_length=500)


class MerchandiseProductRead(MerchandiseProductCreate):
    id: UUID
    status: CommercialStatus


class MerchandiseOrderLineCreate(BaseModel):
    merchandise_product_id: UUID
    quantity: int = Field(ge=1, le=100)
    size: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=80)
    personalization_name: str | None = Field(default=None, max_length=120)
    personalization_number: str | None = Field(default=None, max_length=20)


class MerchandiseOrderCreate(BaseModel):
    organization_id: UUID
    buyer_person_id: UUID | None = None
    buyer_name: str = Field(min_length=2, max_length=180)
    buyer_email: str = Field(min_length=3, max_length=320)
    delivery_method: str = Field(default="pickup", min_length=2, max_length=80)
    delivery_address: str | None = Field(default=None, max_length=2000)
    external_payment_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)
    lines: list[MerchandiseOrderLineCreate] = Field(min_length=1)


class MerchandiseOrderLineRead(BaseModel):
    id: UUID
    organization_id: UUID
    merchandise_order_id: UUID
    merchandise_product_id: UUID
    product_name: str | None = None
    sku: str | None = None
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    size: str | None
    color: str | None
    personalization_name: str | None
    personalization_number: str | None
    fulfillment_status: str


class MerchandiseOrderRead(BaseModel):
    id: UUID
    organization_id: UUID
    buyer_person_id: UUID | None
    buyer_name: str
    buyer_email: str
    delivery_method: str
    delivery_address: str | None
    total_amount: Decimal
    currency: str
    external_payment_reference: str | None
    status: CommercialStatus
    fulfillment_status: str
    fulfilled_at: datetime | None
    notes: str | None
    lines: list[MerchandiseOrderLineRead]


class MerchandiseFulfillmentUpdate(BaseModel):
    fulfillment_status: str = Field(min_length=2, max_length=40)
    notes: str | None = Field(default=None, max_length=4000)


class MerchandiseStoreDashboardRead(BaseModel):
    organization_id: UUID
    product_count: int
    active_product_count: int
    low_stock_count: int
    order_count: int
    queued_order_count: int
    fulfilled_order_count: int
    units_sold: int
    gross_revenue: Decimal
    estimated_margin: Decimal
    recommendations: list[str]


class TicketProductCreate(BaseModel):
    organization_id: UUID
    event_id: UUID
    name: str = Field(min_length=2, max_length=180)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    capacity: int = Field(ge=1)
    access_zone: str | None = Field(default=None, max_length=120)


class TicketProductRead(TicketProductCreate):
    id: UUID
    sold_count: int
    status: CommercialStatus


class TicketOrderCreate(BaseModel):
    organization_id: UUID
    ticket_product_id: UUID
    buyer_name: str = Field(min_length=2, max_length=180)
    buyer_email: str = Field(min_length=3, max_length=320)
    quantity: int = Field(ge=1, le=100)
    external_payment_reference: str | None = Field(default=None, max_length=240)


class TicketOrderRead(BaseModel):
    id: UUID
    organization_id: UUID
    ticket_product_id: UUID
    buyer_name: str
    buyer_email: str
    quantity: int
    total_amount: Decimal
    currency: str
    external_payment_reference: str | None
    status: CommercialStatus
    ticket_ids: list[UUID]


class TicketRead(BaseModel):
    id: UUID
    organization_id: UUID
    ticket_order_id: UUID
    ticket_product_id: UUID
    holder_name: str | None
    qr_token: str
    status: TicketStatus
    checked_in_at: datetime | None
    gate: str | None


class TicketCheckIn(BaseModel):
    gate: str | None = Field(default=None, max_length=80)


class TicketBundleOfferCreate(BaseModel):
    organization_id: UUID
    event_id: UUID
    ticket_product_id: UUID
    merchandise_product_id: UUID | None = None
    name: str = Field(min_length=2, max_length=180)
    package_type: str = Field(default="ticket_bundle", min_length=2, max_length=80)
    ticket_quantity: int = Field(default=1, ge=1, le=100)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    channel: str = Field(default="online", min_length=2, max_length=80)
    sales_limit: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class TicketBundleOfferRead(TicketBundleOfferCreate):
    id: UUID
    ticket_product_name: str | None = None
    merchandise_product_name: str | None = None
    sold_count: int
    status: CommercialStatus


class ComplimentaryTicketCreate(BaseModel):
    organization_id: UUID
    ticket_product_id: UUID
    recipient_name: str = Field(min_length=2, max_length=180)
    recipient_email: str = Field(min_length=3, max_length=320)
    quantity: int = Field(default=1, ge=1, le=100)
    reason: str = Field(default="sponsor_media_guest", min_length=2, max_length=120)
    sponsor_id: UUID | None = None


class TicketSeatAssignmentCreate(BaseModel):
    organization_id: UUID
    ticket_id: UUID
    event_id: UUID | None = None
    section: str = Field(min_length=1, max_length=80)
    row: str | None = Field(default=None, max_length=40)
    seat: str | None = Field(default=None, max_length=40)
    access_zone: str | None = Field(default=None, max_length=120)
    accessible: bool = False
    companion_seat: bool = False


class TicketSeatAssignmentRead(TicketSeatAssignmentCreate):
    id: UUID
    event_id: UUID
    holder_name: str | None = None
    ticket_status: TicketStatus | None = None
    assigned_at: datetime


class TicketResaleListingCreate(BaseModel):
    organization_id: UUID
    ticket_id: UUID
    seller_name: str = Field(min_length=2, max_length=180)
    seller_email: str = Field(min_length=3, max_length=320)
    resale_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=4000)


class TicketResalePurchaseCreate(BaseModel):
    organization_id: UUID
    buyer_name: str = Field(min_length=2, max_length=180)
    buyer_email: str = Field(min_length=3, max_length=320)


class TicketResaleListingRead(BaseModel):
    id: UUID
    organization_id: UUID
    event_id: UUID
    ticket_id: UUID
    seller_name: str
    seller_email: str
    resale_price: Decimal
    currency: str
    status: str
    buyer_name: str | None
    buyer_email: str | None
    listed_at: datetime
    sold_at: datetime | None
    notes: str | None


class TicketAccessDashboardRead(BaseModel):
    organization_id: UUID
    ticket_product_count: int
    ticket_count: int
    checked_in_count: int
    complimentary_count: int
    assigned_seat_count: int
    accessible_seat_count: int
    resale_listing_count: int
    resale_sold_count: int
    package_offer_count: int
    recommendations: list[str]


class CommercialRefundCreate(BaseModel):
    amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    reason: str = Field(min_length=2, max_length=500)
    external_reference: str | None = Field(default=None, max_length=240)


class CommercialRefundRead(BaseModel):
    refund_id: str
    organization_id: UUID
    target_type: str
    target_id: UUID
    amount: Decimal
    currency: str
    reason: str
    status: str
    external_reference: str | None


class FinanceInvoiceCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    team_id: UUID | None = None
    sponsor_id: UUID | None = None
    invoice_number: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=220)
    amount_due: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    due_on: date | None = None
    memo: str | None = Field(default=None, max_length=4000)


class FinanceInvoiceRead(FinanceInvoiceCreate):
    id: UUID
    amount_paid: Decimal
    status: CommercialStatus


class FinancePaymentCreate(BaseModel):
    organization_id: UUID
    invoice_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    method: str = Field(min_length=2, max_length=80)
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class FinancePaymentRead(FinancePaymentCreate):
    id: UUID
    received_at: datetime


class FinancialBudgetCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    fiscal_year: int = Field(ge=2000, le=2200)
    period_start: date
    period_end: date
    budget_type: str = Field(default="operating", pattern="^(operating|capital|grant|program|team|event|cash_flow)$")
    scope_type: str = Field(default="organization", pattern="^(organization|department|team|program|event|facility|grant)$")
    scope_id: UUID | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    beginning_cash_balance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    minimum_cash_reserve: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    assumptions: list[str] = Field(default_factory=list, max_length=40)
    notes: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="draft", pattern="^(draft|approved|active|locked|archived)$")

    @model_validator(mode="after")
    def valid_period(self) -> "FinancialBudgetCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class FinancialBudgetRead(FinancialBudgetCreate):
    id: UUID
    line_count: int = 0


class FinancialBudgetLineCreate(BaseModel):
    budget_id: UUID
    line_type: str = Field(pattern="^(revenue|expense)$")
    category: str = Field(min_length=2, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    amount_budgeted: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    amount_actual: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    forecast_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    cash_timing_month: str | None = Field(default=None, max_length=20)
    funding_source: str | None = Field(default=None, max_length=120)
    restricted: bool = False
    variance_reason: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="active", pattern="^(active|inactive|archived)$")


class FinancialBudgetLineRead(FinancialBudgetLineCreate):
    id: UUID
    organization_id: UUID
    variance_amount: Decimal
    variance_percent: Decimal | None


class FinancialForecastScenarioCreate(BaseModel):
    budget_id: UUID
    name: str = Field(min_length=2, max_length=180)
    scenario_type: str = Field(default="base", pattern="^(base|optimistic|conservative|stress|custom)$")
    revenue_adjustment_percent: Decimal = Field(default=Decimal("0"), ge=-100, le=500, max_digits=6, decimal_places=2)
    expense_adjustment_percent: Decimal = Field(default=Decimal("0"), ge=-100, le=500, max_digits=6, decimal_places=2)
    cash_adjustment_amount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    membership_growth_percent: Decimal = Field(default=Decimal("0"), ge=-100, le=500, max_digits=6, decimal_places=2)
    facility_utilization_percent: Decimal | None = Field(default=None, ge=0, le=100, max_digits=6, decimal_places=2)
    assumptions: list[str] = Field(default_factory=list, max_length=40)
    status: str = Field(default="active", pattern="^(active|inactive|archived)$")


class FinancialForecastScenarioRead(FinancialForecastScenarioCreate):
    id: UUID
    organization_id: UUID
    projected_revenue: Decimal
    projected_expense: Decimal
    projected_net_income: Decimal
    projected_ending_cash: Decimal
    reserve_gap: Decimal
    sensitivity_rank: list[str]


class FinancialBudgetSummaryRead(BaseModel):
    organization_id: UUID
    budget_id: UUID
    budget_name: str
    currency: str
    budgeted_revenue: Decimal
    actual_revenue: Decimal
    forecast_revenue: Decimal
    budgeted_expense: Decimal
    actual_expense: Decimal
    forecast_expense: Decimal
    budgeted_net_income: Decimal
    actual_net_income: Decimal
    forecast_net_income: Decimal
    revenue_variance: Decimal
    expense_variance: Decimal
    net_variance: Decimal
    ending_cash_position: Decimal
    minimum_cash_reserve: Decimal
    cash_buffer: Decimal
    cash_runway_days: int | None
    variance_alert_count: int
    scenario_count: int
    scenarios: list[FinancialForecastScenarioRead]
    recommendations: list[str]


class FinancialStatementLineRead(BaseModel):
    label: str
    amount: Decimal
    category: str
    source: str
    note: str | None = None


class FinancialStatementCreate(BaseModel):
    organization_id: UUID
    period_start: date
    period_end: date
    statement_type: str = Field(default="monthly", pattern="^(monthly|quarterly|annual|board|audit)$")
    basis: str = Field(default="management", pattern="^(cash|accrual|management)$")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    prepared_by_name: str | None = Field(default=None, max_length=180)

    @model_validator(mode="after")
    def valid_period(self) -> "FinancialStatementCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class FinancialStatementPackageRead(FinancialStatementCreate):
    id: UUID
    profit_loss: list[FinancialStatementLineRead]
    balance_sheet: list[FinancialStatementLineRead]
    cash_flow: list[FinancialStatementLineRead]
    total_revenue: Decimal
    total_expense: Decimal
    net_income: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_assets: Decimal
    net_cash_change: Decimal
    ending_cash: Decimal
    highlights: list[str]
    status: str
    generated_at: datetime


class TaxQuoteRead(BaseModel):
    organization_id: UUID
    jurisdiction: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    reverse_charge: bool = False
    rationale: str


class CommercialTaxFilingRead(BaseModel):
    organization_id: UUID
    jurisdiction: str
    period_start: date
    period_end: date
    invoice_count: int
    taxable_subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    gross_total: Decimal
    outstanding_total: Decimal
    currency: str
    reverse_charge: bool
    filing_reference: str
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    destination: str | None
    provider_status_code: int | None
    failure_reason: str | None
    filed_at: datetime


class PaymentSettlementRead(BaseModel):
    organization_id: UUID
    provider: str
    currency: str
    gross_ticket_revenue: Decimal
    gross_invoice_payments: Decimal
    gross_donations: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    payout_reference: str
    line_count: int


class CommercialSettlementPayoutRead(BaseModel):
    id: UUID | None = None
    organization_id: UUID
    provider: str
    currency: str
    status: str
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    payout_reference: str
    payout_batch_reference: str
    idempotency_key: str
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    line_count: int
    destination: str | None
    provider_status_code: int | None
    provider_response: str | None = None
    failure_reason: str | None
    processed_by_person_id: UUID | None = None
    executed_at: datetime
    reconciled_at: datetime | None = None
    external_event_id: str | None = None


class CommercialSettlementPayoutCallbackCreate(BaseModel):
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    payout_reference: str | None = Field(default=None, max_length=180)
    payout_batch_reference: str | None = Field(default=None, max_length=180)
    idempotency_key: str | None = Field(default=None, max_length=180)
    status: str = Field(default="paid", min_length=2, max_length=80)
    provider_status_code: int | None = Field(default=None, ge=100, le=599)
    external_event_id: str | None = Field(default=None, max_length=180)
    raw_payload: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CommercialSettlementPayoutCallbackRead(BaseModel):
    accepted: bool
    signature_required: bool = False
    signature_validated: bool = False
    matched_by: str
    payout_reference: str
    payout_batch_reference: str
    payout_status: str
    message: str
    payout: CommercialSettlementPayoutRead


class CommercialInvoiceHostedCheckoutRead(BaseModel):
    invoice_id: UUID
    invoice_number: str
    organization_id: UUID
    sponsor_id: UUID
    billed_person_id: UUID | None
    title: str
    memo: str | None
    due_on: date | None
    amount_due: Decimal
    amount_paid: Decimal
    open_amount: Decimal
    currency: str
    status: str
    provider: str
    session_id: str
    session_status: str
    client_reference: str
    payment_methods: list[str]
    settlement_endpoint: str
    checkout_summary: str


class CommercialInvoiceProviderCheckoutCreate(BaseModel):
    success_url: str | None = Field(default=None, max_length=800)
    cancel_url: str | None = Field(default=None, max_length=800)
    customer_email: str | None = Field(default=None, max_length=320)
    payment_method: str = Field(default="card", min_length=2, max_length=80)


class CommercialInvoiceProviderCheckoutRead(BaseModel):
    id: UUID | None = None
    invoice_id: UUID
    organization_id: UUID
    sponsor_id: UUID
    provider: str
    mode: str
    status: str
    provider_session_id: str
    local_session_id: str
    client_reference: str
    amount: Decimal
    currency: str
    redirect_url: str
    success_url: str | None
    cancel_url: str | None
    customer_email: str | None = None
    payment_method: str
    provider_status_code: int | None = None
    provider_response: str | None = None
    failure_reason: str | None = None
    webhook_configured: bool = False
    created_at: datetime
    updated_at: datetime | None = None


class CommercialInvoiceCheckoutSettlementCreate(BaseModel):
    invoice_id: UUID
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    method: str = Field(default="hosted_payment_page", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=240)
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=2000)


class CommercialInvoiceCheckoutSettlementRead(BaseModel):
    invoice_id: UUID
    provider: str
    accepted: bool
    signature_required: bool = False
    signature_validated: bool = False
    payment_id: UUID | None
    invoice_status: str
    amount_paid: Decimal
    open_amount: Decimal
    session_status: str
    message: str


class CommercialInvoicePaymentWebhookCreate(BaseModel):
    invoice_id: UUID | None = None
    session_id: str | None = Field(default=None, min_length=8, max_length=120)
    provider: str = Field(default="provider_neutral", min_length=2, max_length=80)
    event_type: str = Field(default="payment.succeeded", min_length=2, max_length=120)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    method: str = Field(default="provider_webhook", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=240)
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=2000)
    raw_payload: dict[str, Any] | None = None


class AccountingExportRow(BaseModel):
    row_type: str
    source_id: UUID
    account_code: str
    memo: str
    debit: Decimal
    credit: Decimal
    currency: str
    external_reference: str | None


class AccountingExportRead(BaseModel):
    organization_id: UUID
    basis: str
    system: str
    rows: list[AccountingExportRow]
    debit_total: Decimal
    credit_total: Decimal


class AccountingSyncRead(BaseModel):
    organization_id: UUID
    basis: str
    system: str
    mode: str
    delivered: bool
    row_count: int
    debit_total: Decimal
    credit_total: Decimal
    sync_reference: str
    provider_status_code: int | None = None
    failure_reason: str | None = None
    webhook_configured: bool


class SponsorshipDashboardRead(BaseModel):
    sponsor_id: UUID
    sponsor_name: str
    agreement_count: int
    contracted_value: Decimal
    active_value: Decimal
    deliverable_count: int
    activation_count: int
    roi_score: int
    recommendation: str


class SponsorPortalSponsorRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    organization_slug: str
    sponsor_name: str
    industry: str | None
    contact_name: str | None
    contact_email: str | None
    website_url: str | None
    brand_assets_url: str | None
    public_site_path: str


class SponsorPortalAgreementRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    sponsor_id: UUID
    sponsor_name: str
    event_id: UUID | None
    event_title: str | None
    event_starts_at: datetime | None
    event_venue_name: str | None
    name: str
    tier: str
    value_amount: Decimal
    currency: str
    starts_on: date | None
    ends_on: date | None
    deliverables: list[str] = Field(default_factory=list)
    activation_notes: str | None
    roi_notes: str | None
    status: CommercialStatus


class SponsorPortalInvoiceRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    sponsor_id: UUID
    invoice_number: str
    title: str
    amount_due: Decimal
    amount_paid: Decimal
    outstanding_amount: Decimal
    currency: str
    due_on: date | None
    status: CommercialStatus
    memo: str | None
    payment_session_id: str | None
    payment_session_url: str | None
    payment_session_status: str | None


class SponsorPortalSummaryRead(BaseModel):
    sponsor_count: int
    agreement_count: int
    active_value: Decimal
    outstanding_invoice_amount: Decimal
    deliverable_count: int
    activation_count: int
    upcoming_event_count: int
    recommendation: str


class SponsorPortalRead(BaseModel):
    identity_email: str
    sponsors: list[SponsorPortalSponsorRead]
    agreements: list[SponsorPortalAgreementRead]
    invoices: list[SponsorPortalInvoiceRead]
    summary: SponsorPortalSummaryRead


class CommercialSummaryRead(BaseModel):
    organization_id: UUID
    sponsorship_value: Decimal
    fundraising_goal: Decimal
    fundraising_raised: Decimal
    ticket_revenue: Decimal
    invoice_outstanding: Decimal
    active_sponsors: int
    active_campaigns: int
    tickets_sold: int
    tickets_checked_in: int
