from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field
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


class OrganizationOnboardingRead(BaseModel):
    organization: OrganizationRead
    starter_team: TeamRead | None = None
    concierge_task: AgentTaskRead | None = None
    public_site_path: str
    registration_page_path: str
    admissions_path: str
    family_portal_path: str
    dashboard_path: str
    owner_email: str
    owner_display_name: str
    checklist: list[str]


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


class RegistrationInquiryImportRowErrorRead(BaseModel):
    row_number: int
    message: str
    row: dict[str, str | None] = Field(default_factory=dict)


class RegistrationInquiryImportRead(BaseModel):
    organization_id: UUID
    created_count: int
    error_count: int
    inquiries: list[RegistrationInquiryRead] = Field(default_factory=list)
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


class MemberAdd(BaseModel):
    subject_type: MemberSubjectType = MemberSubjectType.PERSON
    subject_id: UUID | None = None
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, min_length=2, max_length=240)
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
