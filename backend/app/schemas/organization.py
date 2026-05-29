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
    TeamRole,
)
from app.schemas.communication import CommunicationMessageRead


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


class OrganizationOnboardingRead(BaseModel):
    organization: OrganizationRead
    public_site_path: str
    dashboard_path: str
    owner_email: str
    owner_display_name: str
    checklist: list[str]


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
    created_at: datetime


class RegistrationDocumentSubmission(BaseModel):
    document_type: str = Field(min_length=2, max_length=80)
    filename: str = Field(min_length=2, max_length=240)
    storage_url: str | None = Field(default=None, max_length=500)
    checksum: str | None = Field(default=None, max_length=128)
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


class RegistrationInquiryUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    review_notes: str | None = Field(default=None, max_length=4000)
    follow_up_at: datetime | None = None


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
    jersey_number: str | None = Field(default=None, max_length=16)
    primary_position: str | None = Field(default=None, max_length=80)


class RegistrationInquiryConversionRead(BaseModel):
    inquiry: RegistrationInquiryRead
    athlete_person_id: UUID
    athlete_profile_id: UUID
    roster_entry_id: UUID | None
    guardian_person_id: UUID | None


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
