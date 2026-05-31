from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from decimal import Decimal

from app.models.enums import (
    AssociationLevel,
    CommitteeRole,
    CommunicationChannel,
    MemberSubjectType,
    MembershipRole,
    OrganizationType,
    SportFormat,
    TeamRole,
)
from app.schemas.team import TeamRead
from app.schemas.communication import CommunicationMessageRead
from app.schemas.agent import AgentTaskRead


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=240)
    slug: str | None = Field(default=None, max_length=120)
    organization_type: OrganizationType
    association_level: AssociationLevel | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    primary_sport: str | None = Field(default=None, max_length=80)
    mission: str | None = Field(default=None, max_length=2000)
    public_name: str | None = Field(default=None, max_length=240)
    contact_email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=64)
    website_url: str | None = Field(default=None, max_length=500)
    subdomain: str | None = Field(default=None, max_length=120)
    logo_url: str | None = Field(default=None, max_length=500)
    brand_primary_color: str | None = Field(default=None, max_length=16)
    brand_secondary_color: str | None = Field(default=None, max_length=16)
    registration_open: bool = True
    registration_fee_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    registration_fee_currency: str | None = Field(default=None, min_length=3, max_length=3)
    registration_payment_instructions: str | None = Field(default=None, max_length=2000)
    registration_required_documents: list[str] = Field(default_factory=list, max_length=12)


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_type: OrganizationType
    association_level: AssociationLevel | None
    country_code: str | None
    primary_sport: str | None
    mission: str | None
    public_name: str | None
    contact_email: str | None
    contact_phone: str | None
    website_url: str | None
    subdomain: str | None
    logo_url: str | None
    brand_primary_color: str | None
    brand_secondary_color: str | None
    registration_open: bool
    registration_fee_amount: Decimal | None
    registration_fee_currency: str | None
    registration_payment_instructions: str | None
    registration_required_documents: list[str] = Field(default_factory=list)
    my_roles: list[MembershipRole] = Field(default_factory=list)


class OrganizationProgramCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    program_type: str = Field(default="athlete_development", min_length=2, max_length=80)
    sport: str | None = Field(default=None, max_length=80)
    age_group: str | None = Field(default=None, max_length=80)
    gender_category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=4000)
    capacity: int | None = Field(default=None, ge=0)
    starts_on: date | None = None
    ends_on: date | None = None
    status: str = Field(default="active", pattern="^(planned|active|paused|completed|archived)$")


class OrganizationProgramRead(OrganizationProgramCreate):
    id: UUID
    organization_id: UUID


class OrganizationSeasonCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    sport: str | None = Field(default=None, max_length=80)
    starts_on: date
    ends_on: date
    registration_opens_on: date | None = None
    registration_closes_on: date | None = None
    status: str = Field(default="planned", pattern="^(planned|registration_open|active|completed|archived)$")
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationSeasonRead(OrganizationSeasonCreate):
    id: UUID
    organization_id: UUID


class OrganizationGroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    group_type: str = Field(default="cohort", min_length=2, max_length=80)
    program_id: UUID | None = None
    season_id: UUID | None = None
    team_id: UUID | None = None
    lead_person_id: UUID | None = None
    sport: str | None = Field(default=None, max_length=80)
    age_group: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=4000)
    capacity: int | None = Field(default=None, ge=0)
    status: str = Field(default="active", pattern="^(planned|active|paused|completed|archived)$")


class OrganizationGroupRead(OrganizationGroupCreate):
    id: UUID
    organization_id: UUID
    member_count: int = 0


class OrganizationGroupMemberAdd(BaseModel):
    subject_type: MemberSubjectType = MemberSubjectType.PERSON
    subject_id: UUID
    role: str = Field(default="member", min_length=2, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)


class OrganizationGroupMembershipRead(BaseModel):
    id: UUID
    group_id: UUID
    subject_type: MemberSubjectType
    subject_id: UUID
    subject_label: str | None = None
    role: str
    status: str
    notes: str | None


class OrganizationAwardProgramCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    season_label: str | None = Field(default=None, max_length=80)
    level: str = Field(default="club", min_length=2, max_length=80)
    frequency: str = Field(default="seasonal", min_length=2, max_length=80)
    nomination_opens_at: datetime | None = None
    nomination_closes_at: datetime | None = None
    voting_opens_at: datetime | None = None
    voting_closes_at: datetime | None = None
    eligibility_summary: str | None = Field(default=None, max_length=4000)
    ceremony_name: str | None = Field(default=None, max_length=180)
    ceremony_at: datetime | None = None
    ceremony_venue: str | None = Field(default=None, max_length=240)
    certificate_template: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="draft", pattern="^(draft|nominations_open|voting_open|closed|awarded|archived)$")
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationAwardProgramRead(OrganizationAwardProgramCreate):
    id: UUID
    organization_id: UUID
    category_count: int = 0
    nomination_count: int = 0
    recipient_count: int = 0


class OrganizationAwardCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    award_type: str = Field(default="individual", min_length=2, max_length=80)
    judging_method: str = Field(default="committee", min_length=2, max_length=80)
    criteria: str | None = Field(default=None, max_length=4000)
    max_recipients: int = Field(default=1, ge=1, le=100)
    voter_roles: str | None = Field(default=None, max_length=1000)
    status: str = Field(default="active", pattern="^(active|paused|closed|archived)$")


class OrganizationAwardCategoryRead(OrganizationAwardCategoryCreate):
    id: UUID
    organization_id: UUID
    program_id: UUID
    nomination_count: int = 0
    recipient_count: int = 0


class OrganizationAwardNominationCreate(BaseModel):
    nominee_subject_type: MemberSubjectType = MemberSubjectType.PERSON
    nominee_subject_id: UUID
    title: str = Field(min_length=2, max_length=180)
    nomination_summary: str = Field(min_length=3, max_length=8000)
    evidence_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="submitted", pattern="^(submitted|accepted|shortlisted|rejected|withdrawn)$")
    finalist: bool = False
    score: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)


class OrganizationAwardNominationRead(OrganizationAwardNominationCreate):
    id: UUID
    organization_id: UUID
    program_id: UUID
    category_id: UUID
    nominee_label: str | None = None
    nominated_by_person_id: UUID | None
    vote_count: int = 0
    weighted_score: Decimal = Decimal("0")


class OrganizationAwardVoteCreate(BaseModel):
    voter_person_id: UUID | None = None
    score: Decimal = Field(ge=0, le=100, max_digits=8, decimal_places=2)
    weight: Decimal = Field(default=Decimal("1"), ge=0, le=100, max_digits=8, decimal_places=2)
    comment: str | None = Field(default=None, max_length=2000)


class OrganizationAwardVoteRead(BaseModel):
    id: UUID
    organization_id: UUID
    nomination_id: UUID
    voter_person_id: UUID
    voter_label: str | None = None
    score: Decimal
    weight: Decimal
    comment: str | None


class OrganizationAwardRecipientCreate(BaseModel):
    nomination_id: UUID | None = None
    recipient_subject_type: MemberSubjectType = MemberSubjectType.PERSON
    recipient_subject_id: UUID
    awarded_on: date
    public_citation: str = Field(min_length=3, max_length=8000)
    certificate_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="awarded", pattern="^(awarded|announced|withheld|revoked)$")


class OrganizationAwardRecipientRead(OrganizationAwardRecipientCreate):
    id: UUID
    organization_id: UUID
    program_id: UUID
    category_id: UUID
    recipient_label: str | None = None
    certificate_number: str


class PublicSiteTeamRead(BaseModel):
    id: UUID
    name: str
    sport: str
    age_group: str | None
    gender_category: str | None
    season_label: str | None


class PublicSiteEventRead(BaseModel):
    id: UUID
    team_id: UUID | None
    event_type: str
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    venue_name: str | None


class PublicSiteSponsorRead(BaseModel):
    sponsor_id: UUID
    name: str
    industry: str | None
    website_url: str | None
    brand_assets_url: str | None
    tier: str | None
    active_value: Decimal
    currency: str | None
    deliverables: list[str] = Field(default_factory=list)
    activation_note: str | None


class PublicSiteFundraisingCampaignRead(BaseModel):
    id: UUID
    name: str
    purpose: str
    goal_amount: Decimal
    raised_amount: Decimal
    currency: str
    public_url: str | None
    status: str


class PublicSiteTicketProductRead(BaseModel):
    id: UUID
    event_id: UUID
    event_title: str | None
    event_starts_at: datetime | None
    venue_name: str | None
    name: str
    price: Decimal
    currency: str
    capacity: int
    sold_count: int
    available_count: int
    access_zone: str | None
    status: str


class PublicSiteSupporterTierRead(BaseModel):
    id: UUID
    name: str
    slug: str
    monthly_price: Decimal
    currency: str
    benefits: str
    voting_weight: int
    trial_days: int


class PublicSiteFanChallengeRead(BaseModel):
    id: UUID
    title: str
    description: str
    challenge_type: str
    target_activity_type: str
    target_count: int
    points_reward: int
    badge_name: str | None
    starts_at: datetime
    ends_at: datetime | None
    completion_count: int = 0


class PublicSiteFanLeaderboardEntryRead(BaseModel):
    rank: int
    supporter_profile_id: UUID
    supporter_name: str
    tier_name: str | None
    engagement_points: int
    completed_challenge_count: int


class OrganizationPublicSiteRead(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_type: OrganizationType
    country_code: str | None
    primary_sport: str | None
    mission: str | None
    public_name: str | None
    contact_email: str | None
    contact_phone: str | None
    website_url: str | None
    subdomain: str | None
    logo_url: str | None
    brand_primary_color: str | None
    brand_secondary_color: str | None
    registration_open: bool
    registration_fee_amount: Decimal | None
    registration_fee_currency: str | None
    registration_payment_instructions: str | None
    registration_required_documents: list[str] = Field(default_factory=list)
    teams: list[PublicSiteTeamRead]
    upcoming_events: list[PublicSiteEventRead]
    sponsors: list[PublicSiteSponsorRead]
    fundraising_campaigns: list[PublicSiteFundraisingCampaignRead]
    ticket_products: list[PublicSiteTicketProductRead]
    supporter_tiers: list[PublicSiteSupporterTierRead] = Field(default_factory=list)
    fan_challenges: list[PublicSiteFanChallengeRead] = Field(default_factory=list)
    fan_leaderboard: list[PublicSiteFanLeaderboardEntryRead] = Field(default_factory=list)


class PublicSupporterSignupCreate(BaseModel):
    tier_id: UUID | None = None
    display_name: str = Field(min_length=2, max_length=180)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    interests: list[str] = Field(default_factory=list, max_length=12)
    message: str | None = Field(default=None, max_length=2000)
    source_url: str | None = Field(default=None, max_length=500)


class PublicSupporterSignupRead(BaseModel):
    supporter_profile_id: UUID
    organization_id: UUID
    display_name: str
    email: str
    tier_id: UUID | None
    tier_name: str | None
    engagement_points: int
    status: str
    signup_status: str
    points_awarded: int
    next_actions: list[str] = Field(default_factory=list)


class PublicSupporterChallengeProgressCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    progress_count: int = Field(default=1, ge=1, le=10000)


class PublicSupporterChallengeProgressRead(BaseModel):
    supporter_profile_id: UUID
    supporter_name: str
    challenge_id: UUID
    challenge_title: str
    progress_count: int
    target_count: int
    points_awarded: int
    status: str
    completed_at: datetime | None


class OrganizationDirectoryRead(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_type: OrganizationType
    country_code: str | None
    primary_sport: str | None
    mission: str | None
    public_name: str | None
    contact_email: str | None
    contact_phone: str | None
    website_url: str | None
    subdomain: str | None
    logo_url: str | None
    brand_primary_color: str | None
    brand_secondary_color: str | None
    public_site_path: str
    team_count: int
    upcoming_event_count: int


class OrganizationOnboardingCreate(BaseModel):
    organization: OrganizationCreate
    launch_goal: str | None = Field(default=None, max_length=500)
    starter_team_name: str | None = Field(default=None, min_length=2, max_length=180)
    starter_team_sport: str | None = Field(default=None, min_length=2, max_length=80)
    starter_team_sport_format: SportFormat = SportFormat.TEAM
    starter_team_age_group: str | None = Field(default=None, max_length=80)
    starter_team_gender_category: str | None = Field(default=None, max_length=80)
    starter_team_season_label: str | None = Field(default=None, max_length=80)


class RegistrationLaunchLinkRead(BaseModel):
    key: str
    label: str
    url: str
    qr_payload: str
    description: str


class RegistrationLaunchCopyRead(BaseModel):
    channel: str
    label: str
    subject: str | None = None
    body: str
    share_url: str
    character_count: int


class RegistrationLaunchMetricRead(BaseModel):
    key: str
    label: str
    value: int
    detail: str
    status: str


class RegistrationLaunchReadinessCheckRead(BaseModel):
    key: str
    label: str
    status: str
    detail: str
    action_label: str | None = None
    href: str | None = None


class RegistrationLaunchCommandCenterRead(BaseModel):
    organization_id: UUID
    organization_name: str
    organization_type: OrganizationType
    public_name: str | None
    launch_status: str
    readiness_score: int
    public_site_path: str
    registration_page_path: str
    admissions_path: str
    family_portal_path: str
    dashboard_path: str
    launch_links: list[RegistrationLaunchLinkRead] = Field(default_factory=list)
    channel_copies: list[RegistrationLaunchCopyRead] = Field(default_factory=list)
    metrics: list[RegistrationLaunchMetricRead] = Field(default_factory=list)
    readiness_checks: list[RegistrationLaunchReadinessCheckRead] = Field(default_factory=list)
    staff_actions: list[str] = Field(default_factory=list)
    agent_task: AgentTaskRead | None = None


class OrganizationOnboardingRead(BaseModel):
    organization: OrganizationRead
    starter_team: TeamRead | None = None
    concierge_task: AgentTaskRead | None = None
    launch_center: RegistrationLaunchCommandCenterRead | None = None
    public_site_path: str
    registration_page_path: str
    admissions_path: str
    family_portal_path: str
    dashboard_path: str
    owner_email: str
    owner_display_name: str
    checklist: list[str]


class RegistrationOnboardingPresetRead(BaseModel):
    key: str
    label: str
    organization_type: OrganizationType
    audience: str
    description: str
    primary_sport: str
    launch_goal: str
    starter_team_name: str
    starter_team_sport_format: SportFormat
    starter_team_age_group: str | None = None
    starter_team_gender_category: str | None = None
    starter_team_season_label: str | None = None
    registration_required_documents: list[str] = Field(default_factory=list)
    registration_fee_currency: str
    registration_payment_instructions: str
    checklist: list[str] = Field(default_factory=list)


class RegistrationReadinessStepRead(BaseModel):
    key: str
    label: str
    status: str
    detail: str
    action_label: str | None = None
    href: str | None = None


class RegistrationReadinessOrganizationRead(BaseModel):
    id: UUID
    name: str
    public_name: str | None
    organization_type: OrganizationType
    registration_open: bool
    public_site_path: str
    registration_page_path: str
    admissions_path: str


class RegistrationReadinessFamilyInquiryRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_public_name: str | None
    athlete_name: str
    packet_complete: bool
    payment_status: str
    next_steps: list[str]
    public_site_path: str


class RegistrationOnboardingMissionRead(BaseModel):
    key: str
    audience: str
    title: str
    status: str
    progress_percent: int
    xp: int
    detail: str
    action_label: str
    href: str


class RegistrationLearningPathCreate(BaseModel):
    role: str = Field(default="club_manager", min_length=2, max_length=80)
    primary_goal: str = Field(default="launch_registration", min_length=2, max_length=120)
    skill_level: str = Field(default="beginner", min_length=2, max_length=40)
    learning_style: str = Field(default="hands_on", min_length=2, max_length=40)
    accessibility_mode: str | None = Field(default=None, max_length=80)


class RegistrationLearningModuleRead(BaseModel):
    key: str
    title: str
    duration_minutes: int
    format: str
    objective: str
    practice_task: str
    completion_badge: str


class RegistrationLearningPathRead(BaseModel):
    role: str
    primary_goal: str
    skill_level: str
    learning_style: str
    path_title: str
    estimated_minutes: int
    difficulty: str
    first_action: str
    modules: list[RegistrationLearningModuleRead]
    accessibility_supports: list[str] = Field(default_factory=list)


class RegistrationReadinessRead(BaseModel):
    auth_mode: str
    identity_email: str
    identity_display_name: str
    managed_organization_count: int
    registration_open_count: int
    public_directory_count: int
    admissions_inquiry_count: int
    admissions_ready_count: int
    family_registration_count: int
    family_packet_complete_count: int
    steps: list[RegistrationReadinessStepRead]
    missions: list[RegistrationOnboardingMissionRead] = Field(default_factory=list)
    organizations: list[RegistrationReadinessOrganizationRead] = Field(default_factory=list)
    family_registrations: list[RegistrationReadinessFamilyInquiryRead] = Field(default_factory=list)


class OrganizationHandleAvailabilityRead(BaseModel):
    desired_slug: str
    slug_available: bool
    slug_suggestions: list[str] = Field(default_factory=list)
    desired_subdomain: str | None = None
    subdomain_available: bool | None = None
    subdomain_suggestions: list[str] = Field(default_factory=list)


class PublicRegistrationInquiryCreate(BaseModel):
    team_id: UUID | None = None
    athlete_name: str = Field(min_length=2, max_length=240)
    guardian_name: str | None = Field(default=None, max_length=240)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    age_group: str | None = Field(default=None, max_length=80)
    sport_interest: str | None = Field(default=None, max_length=120)
    message: str | None = Field(default=None, max_length=2000)
    source_url: str | None = Field(default=None, max_length=500)


class RegistrationInquiryRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    athlete_name: str
    guardian_name: str | None
    email: str
    phone: str | None
    age_group: str | None
    sport_interest: str | None
    message: str | None
    source_url: str | None
    status: str
    review_notes: str | None
    follow_up_at: datetime | None
    reviewed_by_person_id: UUID | None
    reviewed_at: datetime | None
    guardian_person_id: UUID | None
    guardian_contact_status: str
    date_of_birth: date | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    medical_notes: str | None
    consent_signer_name: str | None
    guardian_consent_acknowledged_at: datetime | None
    privacy_acknowledged_at: datetime | None
    payment_amount: Decimal | None
    payment_currency: str | None
    payment_method: str | None
    payment_reference: str | None
    payment_status: str
    verification_status: str
    packet_submitted_at: datetime | None
    missing_documents: list[str] = Field(default_factory=list)
    packet_complete: bool = False
    next_steps: list[str] = Field(default_factory=list)
    created_at: datetime


class RegistrationInquiryImportCreate(BaseModel):
    csv_text: str = Field(min_length=1, max_length=200_000)
    source_url: str | None = Field(default=None, max_length=500)
    dry_run: bool = False


class RegistrationInquiryImportTemplateRead(BaseModel):
    organization_id: UUID
    filename: str
    columns: list[str]
    csv_text: str


class RegistrationInquiryImportRowErrorRead(BaseModel):
    row_number: int
    message: str
    row: dict[str, str | None] = Field(default_factory=dict)


class RegistrationInquiryImportPreviewRowRead(BaseModel):
    row_number: int
    athlete_name: str
    guardian_name: str | None
    email: str
    phone: str | None
    age_group: str | None
    sport_interest: str | None
    team_id: UUID | None
    team_name: str | None
    payment_status: str
    required_documents: list[str] = Field(default_factory=list)


class RegistrationInquiryImportRead(BaseModel):
    organization_id: UUID
    dry_run: bool = False
    created_count: int
    preview_count: int = 0
    error_count: int
    inquiries: list[RegistrationInquiryRead] = Field(default_factory=list)
    preview_rows: list[RegistrationInquiryImportPreviewRowRead] = Field(default_factory=list)
    errors: list[RegistrationInquiryImportRowErrorRead] = Field(default_factory=list)


class RegistrationInquiryAccountReadinessRead(BaseModel):
    inquiry_id: UUID
    guardian_person_id: UUID | None
    guardian_email: str | None
    guardian_contact_status: str
    account_status: str
    can_create_account: bool
    can_sign_in: bool
    recommended_action: str


class FamilyRegistrationInquiryRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    organization_public_name: str | None
    organization_slug: str
    public_site_path: str
    athlete_name: str
    guardian_name: str | None
    email: str
    status: str
    verification_status: str
    guardian_contact_status: str
    account_status: str
    payment_status: str
    packet_complete: bool
    missing_documents: list[str]
    next_steps: list[str]
    created_at: datetime
    packet_submitted_at: datetime | None


class RegistrationDocumentSubmission(BaseModel):
    document_type: str = Field(min_length=2, max_length=80)
    filename: str = Field(min_length=2, max_length=240)
    storage_url: str | None = Field(default=None, max_length=500)
    checksum: str | None = Field(default=None, max_length=128)
    content_type: str | None = Field(default=None, max_length=120)
    size_bytes: int | None = None
    notes: str | None = Field(default=None, max_length=500)


class PublicRegistrationDocumentUpload(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    document_type: str = Field(min_length=2, max_length=80)
    filename: str = Field(min_length=2, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    content_base64: str = Field(min_length=4)
    notes: str | None = Field(default=None, max_length=500)


class PublicRegistrationPacketUpdate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    date_of_birth: date | None = None
    emergency_contact_name: str | None = Field(default=None, max_length=240)
    emergency_contact_phone: str | None = Field(default=None, max_length=64)
    medical_notes: str | None = Field(default=None, max_length=2000)
    consent_signer_name: str | None = Field(default=None, max_length=240)
    guardian_consent_acknowledged: bool = False
    privacy_acknowledged: bool = False
    documents: list[RegistrationDocumentSubmission] = Field(default_factory=list, max_length=12)
    payment_amount: Decimal | None = None
    payment_currency: str | None = Field(default=None, min_length=3, max_length=3)
    payment_method: str | None = Field(default=None, max_length=80)
    payment_reference: str | None = Field(default=None, max_length=240)
    payment_status: str | None = Field(default=None, max_length=40)


class RegistrationPacketRead(BaseModel):
    inquiry: RegistrationInquiryRead
    required_documents: list[str]
    submitted_documents: list[RegistrationDocumentSubmission]
    missing_documents: list[str]
    consent_complete: bool
    medical_complete: bool
    emergency_contact_complete: bool
    payment_complete: bool
    packet_complete: bool
    next_steps: list[str]


class RegistrationPaymentSessionCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    checkout_base_url: str = Field(default="/pay/sessions", min_length=1, max_length=800)
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    payment_method: str | None = Field(default=None, max_length=80)


class RegistrationPaymentHostedCheckoutRead(BaseModel):
    inquiry_id: UUID
    organization_id: UUID
    athlete_name: str
    guardian_name: str | None
    guardian_email: str
    registration_reference: str
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
    public_registration_path: str
    family_portal_path: str


class RegistrationPaymentSessionRead(BaseModel):
    inquiry: RegistrationInquiryRead
    session_id: str
    checkout_url: str
    provider: str
    hosted_checkout: RegistrationPaymentHostedCheckoutRead


class RegistrationPaymentSettlementCreate(BaseModel):
    inquiry_id: UUID
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    method: str = Field(default="hosted_payment_page", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=240)
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=2000)


class RegistrationPaymentSettlementRead(BaseModel):
    inquiry_id: UUID
    provider: str
    accepted: bool
    payment_reference: str | None
    payment_status: str
    amount_paid: Decimal
    open_amount: Decimal
    session_status: str
    message: str


class RegistrationInquiryUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    review_notes: str | None = Field(default=None, max_length=4000)
    follow_up_at: datetime | None = None
    payment_status: str | None = Field(default=None, max_length=40)
    payment_method: str | None = Field(default=None, max_length=80)
    payment_reference: str | None = Field(default=None, max_length=240)


class RegistrationInquiryFollowUpCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    subject: str = Field(min_length=2, max_length=240)
    body: str = Field(min_length=2, max_length=8000)
    urgent: bool = False
    quiet_hours_override: bool = False


class RegistrationInquiryConversionCreate(BaseModel):
    team_id: UUID | None = None
    role: TeamRole = TeamRole.PLAYER
    create_guardian: bool = True
    send_guardian_invite: bool = True
    guardian_invite_channel: CommunicationChannel = CommunicationChannel.EMAIL
    guardian_portal_url: str = Field(default="https://afrolete.lindela.io/family", max_length=500)
    jersey_number: str | None = Field(default=None, max_length=16)
    primary_position: str | None = Field(default=None, max_length=80)


class RegistrationInquiryConversionRead(BaseModel):
    inquiry: RegistrationInquiryRead
    athlete_person_id: UUID
    athlete_profile_id: UUID
    roster_entry_id: UUID | None
    guardian_person_id: UUID | None
    guardian_invite_message_id: UUID | None = None
    guardian_invite_portal_url: str | None = None


class RegistrationInquiryFollowUpRead(BaseModel):
    inquiry: RegistrationInquiryRead
    message: CommunicationMessageRead
    recipient_person_id: UUID


class OrganizationDataMigrationProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    source_system: str = Field(min_length=2, max_length=120)
    source_format: str = Field(default="csv", min_length=2, max_length=80)
    migration_type: str = Field(
        default="initial_import",
        pattern="^(initial_import|historical_backfill|consolidation|emergency_restore)$",
    )
    data_domains: str | None = Field(default=None, max_length=4000)
    owner_person_id: UUID | None = None
    status: str = Field(default="planning", pattern="^(planning|mapping|validating|importing|reconciled|completed|blocked|cancelled)$")
    risk_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    records_expected: int | None = Field(default=None, ge=0)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationDataMigrationProjectRead(OrganizationDataMigrationProjectCreate):
    id: UUID
    organization_id: UUID
    records_imported: int
    error_count: int
    run_count: int


class OrganizationDataMigrationRunCreate(BaseModel):
    run_type: str = Field(
        default="validation",
        pattern="^(mapping_preview|validation|dry_run|import|reconciliation|rollback)$",
    )
    status: str = Field(default="queued", pattern="^(queued|running|succeeded|failed|partial|cancelled)$")
    input_artifact_url: str | None = Field(default=None, max_length=500)
    mapping_summary: str | None = Field(default=None, max_length=8000)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    records_seen: int = Field(default=0, ge=0)
    records_created: int = Field(default=0, ge=0)
    records_updated: int = Field(default=0, ge=0)
    records_skipped: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    checksum: str | None = Field(default=None, max_length=128)
    report_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationDataMigrationRunRead(OrganizationDataMigrationRunCreate):
    id: UUID
    organization_id: UUID
    project_id: UUID


class OrganizationRecoveryPlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    scope: str = Field(default="tenant_operational_data", min_length=2, max_length=160)
    rpo_minutes: int = Field(default=60, ge=0, le=60 * 24 * 30)
    rto_minutes: int = Field(default=240, ge=0, le=60 * 24 * 30)
    backup_frequency: str = Field(default="daily", min_length=2, max_length=80)
    storage_location: str | None = Field(default=None, max_length=500)
    retention_days: int = Field(default=90, ge=1, le=3650)
    encryption_policy: str | None = Field(default=None, max_length=240)
    status: str = Field(default="draft", pattern="^(draft|active|testing|failed|retired)$")
    last_tested_at: datetime | None = None
    next_test_due_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationRecoveryPlanRead(OrganizationRecoveryPlanCreate):
    id: UUID
    organization_id: UUID
    drill_count: int


class OrganizationRecoveryDrillCreate(BaseModel):
    drill_type: str = Field(
        default="restore_test",
        pattern="^(restore_test|failover_rehearsal|table_restore|full_environment_rebuild)$",
    )
    status: str = Field(default="planned", pattern="^(planned|running|passed|failed|blocked|cancelled)$")
    started_at: datetime | None = None
    finished_at: datetime | None = None
    rpo_minutes_observed: int | None = Field(default=None, ge=0)
    rto_minutes_observed: int | None = Field(default=None, ge=0)
    data_loss_summary: str | None = Field(default=None, max_length=4000)
    result_summary: str | None = Field(default=None, max_length=4000)
    action_items: str | None = Field(default=None, max_length=4000)
    evidence_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationRecoveryDrillRead(OrganizationRecoveryDrillCreate):
    id: UUID
    organization_id: UUID
    recovery_plan_id: UUID


class OrganizationComplianceDocumentCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    category: str = Field(
        default="legal_regulatory",
        pattern="^(legal_regulatory|health_safety|personnel|player_student|property_facilities|financial|other)$",
    )
    document_type: str = Field(min_length=2, max_length=120)
    subject_type: str | None = Field(default=None, max_length=80)
    subject_id: UUID | None = None
    owner_person_id: UUID | None = None
    issuer: str | None = Field(default=None, max_length=180)
    reference_number: str | None = Field(default=None, max_length=180)
    status: str = Field(default="draft", pattern="^(draft|pending_review|verified|expired|archived|rejected)$")
    renewal_status: str = Field(default="not_required", pattern="^(not_required|not_started|in_progress|submitted|renewed|blocked)$")
    effective_on: date | None = None
    expires_on: date | None = None
    next_review_on: date | None = None
    retention_until: date | None = None
    auto_renewal_enabled: bool = False
    storage_url: str | None = Field(default=None, max_length=500)
    checksum: str | None = Field(default=None, max_length=128)
    confidentiality: str = Field(default="internal", pattern="^(public|internal|restricted|confidential)$")
    tags: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationComplianceDocumentRead(OrganizationComplianceDocumentCreate):
    id: UUID
    organization_id: UUID
    current_version: int
    version_count: int
    days_until_expiry: int | None


class OrganizationComplianceDocumentVersionCreate(BaseModel):
    storage_url: str | None = Field(default=None, max_length=500)
    checksum: str | None = Field(default=None, max_length=128)
    filename: str | None = Field(default=None, max_length=240)
    content_type: str | None = Field(default=None, max_length=120)
    size_bytes: int | None = Field(default=None, ge=0)
    change_summary: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="current", pattern="^(draft|current|superseded|rejected)$")


class OrganizationComplianceDocumentVersionRead(OrganizationComplianceDocumentVersionCreate):
    id: UUID
    organization_id: UUID
    document_id: UUID
    version_number: int
    uploaded_by_person_id: UUID | None
    verified_by_person_id: UUID | None
    verified_at: datetime | None


class OrganizationComplianceDocumentSummaryRead(BaseModel):
    organization_id: UUID
    total_documents: int
    verified_documents: int
    expired_documents: int
    expiring_soon_documents: int
    auto_renewal_documents: int
    category_counts: dict[str, int]
    renewal_status_counts: dict[str, int]


class MemberAdd(BaseModel):
    subject_type: MemberSubjectType = MemberSubjectType.PERSON
    subject_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, min_length=2, max_length=240)
    date_of_birth: date | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    role: MembershipRole
    title: str | None = Field(default=None, max_length=160)


class MembershipRead(BaseModel):
    id: UUID
    organization_id: UUID
    subject_type: MemberSubjectType
    subject_id: UUID
    role: MembershipRole
    title: str | None
    status: str


class MemberSubscriptionPlanCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=180,
        description="Club-managed dues or membership-fee plan; not an AfroLete hosting subscription.",
    )
    description: str | None = Field(
        default=None,
        max_length=4000,
        description="Member-facing dues description controlled by the tenant organization.",
    )
    member_role: str | None = Field(default=None, max_length=80)
    amount: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Amount the tenant organization charges its member.",
    )
    currency: str = Field(default="KES", min_length=3, max_length=3)
    billing_interval: str = Field(default="monthly", pattern="^(weekly|monthly|quarterly|term|season|annual|one_time)$")
    due_day: int | None = Field(default=None, ge=1, le=31)
    grace_period_days: int = Field(default=7, ge=0, le=120)
    benefits: str | None = Field(default=None, max_length=4000)


class MemberSubscriptionPlanRead(MemberSubscriptionPlanCreate):
    id: UUID
    organization_id: UUID
    status: str


class MemberSubscriptionCreate(BaseModel):
    plan_id: UUID
    membership_id: UUID | None = None
    subject_type: MemberSubjectType | None = None
    subject_id: UUID | None = None
    starts_on: date
    current_period_start: date
    current_period_end: date
    next_due_on: date | None = None
    status: str = Field(default="active", pattern="^(trialing|active|past_due|paused|cancelled)$")
    balance_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    external_reference: str | None = Field(default=None, max_length=180)
    notes: str | None = Field(default=None, max_length=4000)


class MemberSubscriptionRead(BaseModel):
    id: UUID
    organization_id: UUID
    plan_id: UUID
    plan_name: str
    membership_id: UUID | None
    subject_type: MemberSubjectType
    subject_id: UUID
    subject_label: str | None = None
    starts_on: date
    current_period_start: date
    current_period_end: date
    next_due_on: date | None
    status: str
    balance_amount: Decimal
    currency: str
    dues_last_reminded_at: datetime | None = None
    dues_reminder_message_id: UUID | None = None
    dues_reminder_count: int = 0
    external_reference: str | None
    notes: str | None


class MemberSubscriptionPaymentCreate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
        description="Payment collected by or on behalf of the club for member dues.",
    )
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    provider: str = Field(default="mpesa", min_length=2, max_length=80)
    method: str = Field(default="mobile_money", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=180)
    received_at: datetime | None = None
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)


class MemberSubscriptionPaymentRead(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    amount: Decimal
    currency: str
    provider: str
    method: str
    external_payment_id: str | None
    received_at: datetime
    status: str
    raw_reference: str | None
    notes: str | None
    subscription_balance_amount: Decimal
    subscription_status: str


class MemberSubscriptionChargeRead(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    plan_id: UUID
    plan_name: str
    subject_label: str | None = None
    period_start: date
    period_end: date
    due_on: date | None
    amount: Decimal
    amount_paid: Decimal
    balance_amount: Decimal
    currency: str
    status: str
    source: str
    description: str | None
    paid_at: datetime | None
    last_payment_id: UUID | None
    created_by_person_id: UUID | None
    created_at: datetime


class MemberSubscriptionReceivablesSummaryRead(BaseModel):
    organization_id: UUID
    as_of: date
    charge_count: int
    open_charge_count: int
    partial_charge_count: int
    paid_charge_count: int
    total_charged: Decimal
    total_collected: Decimal
    outstanding_balance: Decimal
    current_balance: Decimal
    overdue_balance: Decimal
    aging_buckets: dict[str, Decimal]
    next_due_on: date | None
    oldest_open_due_on: date | None
    status_counts: dict[str, int]
    collection_rate_percent: Decimal
    next_actions: list[str]


class MemberSubscriptionChargeRunCreate(BaseModel):
    organization_id: UUID
    charge_on: date | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False


class MemberSubscriptionChargeRunItemRead(BaseModel):
    subscription_id: UUID
    charge_id: UUID | None = None
    plan_name: str
    subject_label: str | None
    period_start: date | None = None
    period_end: date | None = None
    due_on: date | None = None
    amount: Decimal
    currency: str
    action: str
    reason: str


class MemberSubscriptionChargeRunRead(BaseModel):
    organization_id: UUID | None
    charge_on: date
    eligible_count: int
    executed_count: int
    charged_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool
    subscription_ids: list[UUID]
    charge_ids: list[UUID]
    total_charged: Decimal
    items: list[MemberSubscriptionChargeRunItemRead]


class MemberSubscriptionHostedCheckoutRead(BaseModel):
    subscription_id: UUID
    organization_id: UUID
    plan_id: UUID
    plan_name: str
    receivable_owner_type: str
    receivable_note: str
    platform_hosting_charge: bool
    subject_label: str | None
    dues_reference: str
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


class MemberSubscriptionCheckoutLinkRead(BaseModel):
    subscription_id: UUID
    provider: str
    session_id: str
    checkout_url: str
    hosted_checkout: MemberSubscriptionHostedCheckoutRead


class MemberSubscriptionCheckoutSettlementCreate(BaseModel):
    subscription_id: UUID
    provider: str = Field(default="mpesa", min_length=2, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    method: str = Field(default="hosted_payment_page", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=240)
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=2000)


class MemberSubscriptionCheckoutSettlementRead(BaseModel):
    subscription_id: UUID
    provider: str
    accepted: bool
    payment_id: UUID | None
    subscription_status: str
    amount_paid: Decimal
    open_amount: Decimal
    session_status: str
    message: str


class MemberSubscriptionReminderRunCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    as_of: date | None = None
    due_within_days: int = Field(default=7, ge=0, le=365)
    repeat_after_days: int = Field(default=7, ge=0, le=365)
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False


class MemberSubscriptionReminderItemRead(BaseModel):
    subscription_id: UUID
    plan_name: str
    subject_label: str | None
    next_due_on: date | None
    days_until_due: int | None
    balance_amount: Decimal
    currency: str
    recipient_count: int = 0
    action: str
    reason: str
    message_id: UUID | None = None


class MemberSubscriptionReminderRunRead(BaseModel):
    organization_id: UUID | None
    channel: CommunicationChannel
    as_of: date
    due_within_days: int
    repeat_after_days: int
    eligible_count: int
    executed_count: int
    reminded_count: int
    skipped_count: int
    failed_count: int
    marked_past_due_count: int
    dry_run: bool = False
    subscription_ids: list[UUID]
    message_ids: list[UUID]
    items: list[MemberSubscriptionReminderItemRead]


class OrganizationMarketProfileCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    country_code: str = Field(min_length=2, max_length=2)
    region_code: str | None = Field(default=None, max_length=80)
    locale: str = Field(default="en-KE", min_length=2, max_length=16)
    timezone: str = Field(default="Africa/Nairobi", min_length=2, max_length=80)
    default_currency: str = Field(default="KES", min_length=3, max_length=3)
    reporting_currency: str = Field(default="KES", min_length=3, max_length=3)
    exchange_rate_source: str | None = Field(default=None, max_length=160)
    exchange_rate_margin_bps: int = Field(default=0, ge=-1000, le=1000)
    season_rate_lock: bool = False
    primary_payment_method: str = Field(default="mpesa", min_length=2, max_length=80)
    supported_payment_methods: list[str] = Field(default_factory=list, max_length=20)
    mobile_money_providers: list[str] = Field(default_factory=list, max_length=20)
    cash_collection_points: list[str] = Field(default_factory=list, max_length=20)
    bank_integrations: list[str] = Field(default_factory=list, max_length=20)
    tax_authority: str | None = Field(default=None, max_length=180)
    tax_registration_number: str | None = Field(default=None, max_length=120)
    tax_profile: str | None = Field(default=None, max_length=120)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=1, max_digits=6, decimal_places=4)
    tax_exempt_categories: list[str] = Field(default_factory=list, max_length=20)
    government_reporting_agencies: list[str] = Field(default_factory=list, max_length=20)
    federation_reporting_templates: list[str] = Field(default_factory=list, max_length=20)
    compliance_notes: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="active", pattern="^(active|draft|retired)$")


class OrganizationMarketProfileRead(OrganizationMarketProfileCreate):
    id: UUID
    organization_id: UUID


class OrganizationMarketProfileSummaryRead(BaseModel):
    organization_id: UUID
    profile_count: int
    active_profile_count: int
    country_count: int
    primary_currencies: list[str]
    payment_methods: list[str]
    mobile_money_providers: list[str]
    tax_authorities: list[str]
    government_reporting_agencies: list[str]
    federation_reporting_templates: list[str]
    compliance_ready: bool
    next_actions: list[str]


class OrganizationExternalReportCreate(BaseModel):
    market_profile_id: UUID | None = None
    name: str = Field(min_length=2, max_length=180)
    report_code: str = Field(min_length=2, max_length=120)
    report_type: str = Field(default="federation", min_length=2, max_length=80)
    target_agency: str = Field(min_length=2, max_length=180)
    target_type: str = Field(
        default="federation",
        pattern="^(government|federation|education|health_safety|financial|anti_doping|grant|other)$",
    )
    reporting_period_start: date
    reporting_period_end: date
    due_on: date
    submission_format: str = Field(default="pdf", pattern="^(pdf|xlsx|csv|xml|json|portal|api)$")
    data_elements: list[str] = Field(default_factory=list, max_length=40)
    source_summary: str | None = Field(default=None, max_length=4000)
    generated_payload: str | None = Field(default=None, max_length=12000)
    submission_payload: str | None = Field(default=None, max_length=12000)
    status: str = Field(default="draft", pattern="^(draft|ready|submitted|accepted|rejected|overdue|cancelled)$")
    external_reference: str | None = Field(default=None, max_length=180)
    submitted_at: datetime | None = None
    accepted_at: datetime | None = None
    rejection_reason: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_period(self) -> "OrganizationExternalReportCreate":
        if self.reporting_period_end < self.reporting_period_start:
            raise ValueError("reporting_period_end must be on or after reporting_period_start")
        return self


class OrganizationExternalReportStatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|ready|submitted|accepted|rejected|overdue|cancelled)$")
    external_reference: str | None = Field(default=None, max_length=180)
    submitted_at: datetime | None = None
    accepted_at: datetime | None = None
    rejection_reason: str | None = Field(default=None, max_length=4000)
    submission_payload: str | None = Field(default=None, max_length=12000)
    notes: str | None = Field(default=None, max_length=4000)


class OrganizationExternalReportRead(OrganizationExternalReportCreate):
    id: UUID
    organization_id: UUID
    market_profile_name: str | None = None
    days_until_due: int


class OrganizationExternalReportSummaryRead(BaseModel):
    organization_id: UUID
    total_reports: int
    submitted_reports: int
    accepted_reports: int
    rejected_reports: int
    overdue_reports: int
    upcoming_reports: int
    target_type_counts: dict[str, int]
    next_actions: list[str]


class CommitteeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    level: AssociationLevel | None = None
    mandate: str | None = Field(default=None, max_length=2000)


class CommitteeRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    level: AssociationLevel | None
    mandate: str | None
    status: str


class CommitteeMemberAdd(BaseModel):
    person_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, min_length=2, max_length=240)
    role: CommitteeRole
    title: str | None = Field(default=None, max_length=160)


class CommitteeMembershipRead(BaseModel):
    id: UUID
    committee_id: UUID
    person_id: UUID
    role: CommitteeRole
    title: str | None
    status: str
