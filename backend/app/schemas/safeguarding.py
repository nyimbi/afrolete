from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    AttendanceStatus,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    ConsentStatus,
    BackgroundCheckStatus,
    ComplianceCredentialStatus,
    ComplianceCredentialType,
    EventType,
    GuardianRelationshipKind,
    IncidentReportPackageStatus,
    InsuranceClaimStatus,
    InsuranceClaimType,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
    SafeguardingIncidentSeverity,
    SafeguardingIncidentStatus,
    SafeguardingIncidentType,
)


class GuardianRelationshipCreate(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID | None = None
    guardian_email: str | None = Field(default=None, max_length=320)
    guardian_phone: str | None = Field(default=None, max_length=64)
    guardian_display_name: str | None = Field(default=None, min_length=2, max_length=240)
    relationship_kind: GuardianRelationshipKind = GuardianRelationshipKind.PARENT
    relationship: str | None = Field(default=None, max_length=80)
    can_sign_consent: bool = True
    can_view_medical: bool = False
    emergency_contact: bool = True
    can_pick_up: bool = False
    is_primary: bool = False
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def guardian_reference_required(self) -> "GuardianRelationshipCreate":
        if (
            self.guardian_person_id is None
            and self.guardian_email is None
            and self.guardian_phone is None
        ):
            raise ValueError("guardian_person_id, guardian_email, or guardian_phone is required")
        return self


class GuardianRelationshipRead(BaseModel):
    id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    relationship_kind: GuardianRelationshipKind
    relationship: str
    can_sign_consent: bool
    can_view_medical: bool
    emergency_contact: bool
    can_pick_up: bool
    is_primary: bool
    notes: str | None


class FamilyAthleteSummaryRead(BaseModel):
    athlete_person_id: UUID
    athlete_name: str
    relationship: str
    relationship_kind: GuardianRelationshipKind
    can_sign_consent: bool
    can_view_medical: bool
    emergency_contact: bool
    pending_consent_requests: int
    latest_consent_status: ConsentStatus | None
    latest_consent_scope_type: ConsentScopeType | None
    latest_consent_signed_at: datetime | None


class FamilyPerformanceGoalRead(BaseModel):
    id: UUID
    title: str
    target_value: float
    current_value: float | None
    direction: str
    due_at: date | None
    status: str
    reward_badge: str | None
    notes: str | None


class FamilyPerformanceAwardRead(BaseModel):
    id: UUID
    title: str
    badge_code: str
    achievement_type: str
    achieved_value: float | None
    threshold_value: float | None
    awarded_at: datetime
    source_summary: str | None


class FamilyPerformanceSummaryRead(BaseModel):
    athlete_person_id: UUID
    athlete_profile_id: UUID
    athlete_name: str
    active_goal_count: int
    achieved_goal_count: int
    award_count: int
    goals: list[FamilyPerformanceGoalRead]
    awards: list[FamilyPerformanceAwardRead]


class FamilyEventSummaryRead(BaseModel):
    athlete_person_id: UUID
    athlete_name: str
    event_id: UUID
    team_id: UUID | None
    event_type: EventType
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    venue_name: str | None
    attendance_status: AttendanceStatus | None
    clearance_status: ParticipationClearanceStatus
    guardian_required: bool
    consent_id: UUID | None
    reason: str


class FamilyEventRsvpCreate(BaseModel):
    organization_id: UUID
    status: AttendanceStatus
    note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def response_status_allowed(self) -> "FamilyEventRsvpCreate":
        if self.status not in {AttendanceStatus.CONFIRMED, AttendanceStatus.DECLINED}:
            raise ValueError("family RSVP status must be confirmed or declined")
        return self


class ActivityConsentCreate(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None = None
    status: ConsentStatus = ConsentStatus.GRANTED
    valid_from: date | None = None
    valid_until: date | None = None
    signed_at: datetime | None = None
    consent_text: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def scoped_consent_reference_required(self) -> "ActivityConsentCreate":
        if self.scope_type != ConsentScopeType.ORGANIZATION and self.scope_id is None:
            raise ValueError("team and event consents require scope_id")
        return self


class ConsentRequestCreate(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None = None
    channel: ConsentCaptureChannel
    destination: str | None = Field(default=None, max_length=320)
    expires_at: datetime | None = None
    external_message_id: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def scoped_request_reference_required(self) -> "ConsentRequestCreate":
        if self.scope_type != ConsentScopeType.ORGANIZATION and self.scope_id is None:
            raise ValueError("team and event consent requests require scope_id")
        return self


class ConsentRequestRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None
    channel: ConsentCaptureChannel
    destination: str
    status: ConsentRequestStatus
    expires_at: datetime | None
    sent_at: datetime | None
    fulfilled_at: datetime | None
    external_message_id: str | None
    one_time_token: str | None = None


class FamilyConsentRequestRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_person_id: UUID
    athlete_name: str
    scope_type: ConsentScopeType
    scope_id: UUID | None
    channel: ConsentCaptureChannel
    destination: str
    status: ConsentRequestStatus
    expires_at: datetime | None
    sent_at: datetime | None
    notes: str | None


class FamilyConsentResponseCreate(BaseModel):
    status: ConsentStatus = ConsentStatus.GRANTED
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def response_status_allowed(self) -> "FamilyConsentResponseCreate":
        if self.status not in {ConsentStatus.GRANTED, ConsentStatus.DENIED}:
            raise ValueError("family consent response must be granted or denied")
        return self


class TokenConsentCapture(BaseModel):
    token: str = Field(min_length=16, max_length=200)
    status: ConsentStatus = ConsentStatus.GRANTED
    consent_text: str | None = Field(default=None, max_length=4000)
    response_payload: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)


class KnownChannelConsentCapture(BaseModel):
    organization_id: UUID
    athlete_person_id: UUID
    channel: ConsentCaptureChannel
    source_address: str = Field(min_length=3, max_length=320)
    scope_type: ConsentScopeType
    scope_id: UUID | None = None
    status: ConsentStatus = ConsentStatus.GRANTED
    response_payload: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def scoped_response_reference_required(self) -> "KnownChannelConsentCapture":
        if self.scope_type != ConsentScopeType.ORGANIZATION and self.scope_id is None:
            raise ValueError("team and event consent responses require scope_id")
        return self


class ActivityConsentRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    scope_type: ConsentScopeType
    scope_id: UUID | None
    status: ConsentStatus
    source_request_id: UUID | None
    capture_channel: ConsentCaptureChannel
    valid_from: date | None
    valid_until: date | None
    signed_at: datetime | None
    revoked_at: datetime | None
    recorded_by_person_id: UUID | None
    consent_text: str | None
    notes: str | None


class ParticipationClearanceRead(BaseModel):
    event_id: UUID
    athlete_person_id: UUID
    is_minor: bool
    guardian_required: bool
    status: ParticipationClearanceStatus
    consent_id: UUID | None = None
    reason: str


class SafeguardingIncidentCreate(BaseModel):
    organization_id: UUID
    event_id: UUID | None = None
    team_id: UUID | None = None
    athlete_person_id: UUID | None = None
    assigned_to_person_id: UUID | None = None
    incident_type: SafeguardingIncidentType
    severity: SafeguardingIncidentSeverity = SafeguardingIncidentSeverity.MEDIUM
    occurred_at: datetime
    location: str | None = Field(default=None, max_length=240)
    title: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=2, max_length=8000)
    immediate_action: str | None = Field(default=None, max_length=4000)
    parent_notified_at: datetime | None = None
    medical_follow_up_required: str = Field(default="unknown", max_length=40)
    regulatory_report_required: bool = False


class SafeguardingIncidentUpdate(BaseModel):
    status: SafeguardingIncidentStatus | None = None
    severity: SafeguardingIncidentSeverity | None = None
    assigned_to_person_id: UUID | None = None
    parent_notified_at: datetime | None = None
    medical_follow_up_required: str | None = Field(default=None, max_length=40)
    regulatory_report_required: bool | None = None
    resolution_notes: str | None = Field(default=None, max_length=4000)


class SafeguardingIncidentInvestigationActionCreate(BaseModel):
    action_type: str = Field(min_length=2, max_length=80)
    assign_to_self: bool = False
    assigned_to_person_id: UUID | None = None
    status: SafeguardingIncidentStatus | None = None
    severity: SafeguardingIncidentSeverity | None = None
    finding_summary: str | None = Field(default=None, max_length=2000)
    next_step: str | None = Field(default=None, max_length=1000)
    parent_notified: bool = False
    medical_follow_up_required: str | None = Field(default=None, max_length=40)
    regulatory_report_required: bool | None = None
    close_incident: bool = False


class SafeguardingIncidentInvestigationActionRead(BaseModel):
    incident_id: UUID
    organization_id: UUID
    action_type: str
    status: SafeguardingIncidentStatus
    severity: SafeguardingIncidentSeverity
    assigned_to_person_id: UUID | None
    regulatory_report_required: bool
    medical_follow_up_required: str
    action_summary: str
    resolution_notes: str | None
    actioned_at: datetime


class SafeguardingIncidentRead(BaseModel):
    id: UUID
    organization_id: UUID
    event_id: UUID | None
    team_id: UUID | None
    athlete_person_id: UUID | None
    reported_by_person_id: UUID | None
    assigned_to_person_id: UUID | None
    incident_type: SafeguardingIncidentType
    severity: SafeguardingIncidentSeverity
    status: SafeguardingIncidentStatus
    occurred_at: datetime
    location: str | None
    title: str
    description: str
    immediate_action: str | None
    parent_notified_at: datetime | None
    medical_follow_up_required: str
    regulatory_report_required: bool
    resolution_notes: str | None
    resolved_at: datetime | None
    created_at: datetime


class BackgroundCheckCreate(BaseModel):
    organization_id: UUID
    person_id: UUID
    provider: str = Field(min_length=2, max_length=120)
    check_type: str = Field(min_length=2, max_length=120)
    requested_at: datetime
    expires_at: date | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=2000)


class BackgroundCheckUpdate(BaseModel):
    status: BackgroundCheckStatus | None = None
    reviewed_by_person_id: UUID | None = None
    risk_level: str | None = Field(default=None, max_length=40)
    completed_at: datetime | None = None
    expires_at: date | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    result_summary: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)


class BackgroundCheckRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    requested_by_person_id: UUID | None
    reviewed_by_person_id: UUID | None
    provider: str
    check_type: str
    status: BackgroundCheckStatus
    risk_level: str
    requested_at: datetime
    completed_at: datetime | None
    expires_at: date | None
    external_reference: str | None
    result_summary: str | None
    notes: str | None
    created_at: datetime


class BackgroundCheckProviderResultCreate(BaseModel):
    organization_id: UUID | None = None
    background_check_id: UUID | None = None
    provider: str = Field(min_length=2, max_length=120)
    external_reference: str | None = Field(default=None, max_length=240)
    provider_result_id: str | None = Field(default=None, max_length=240)
    status: BackgroundCheckStatus | None = None
    provider_status: str | None = Field(default=None, max_length=80)
    risk_level: str | None = Field(default=None, max_length=40)
    completed_at: datetime | None = None
    expires_at: date | None = None
    result_summary: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=2000)
    raw_payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def has_locator(self) -> "BackgroundCheckProviderResultCreate":
        if self.background_check_id is None and self.external_reference is None:
            raise ValueError("background_check_id or external_reference is required")
        return self


class BackgroundCheckProviderResultRead(BaseModel):
    accepted: bool
    signature_required: bool
    signature_validated: bool
    organization_id: UUID
    background_check_id: UUID
    provider: str
    external_reference: str | None
    status: BackgroundCheckStatus
    risk_level: str
    message: str


class BackgroundCheckProviderSubmissionRead(BaseModel):
    background_check_id: UUID
    organization_id: UUID
    person_id: UUID
    provider: str
    check_type: str
    provider_profile: str
    provider_schema_id: str
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    provider_status_code: int | None
    external_reference: str | None
    check_status: BackgroundCheckStatus
    provider_payload: dict[str, Any]
    failure_reason: str | None
    submitted_at: datetime


class ComplianceCredentialCreate(BaseModel):
    organization_id: UUID
    person_id: UUID
    credential_type: ComplianceCredentialType
    title: str = Field(min_length=2, max_length=240)
    issuing_body: str | None = Field(default=None, max_length=240)
    credential_number: str | None = Field(default=None, max_length=160)
    issued_at: date | None = None
    expires_at: date | None = None
    renewal_due_at: date | None = None
    verification_url: str | None = Field(default=None, max_length=500)
    evidence_object_key: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class ComplianceCredentialUpdate(BaseModel):
    status: ComplianceCredentialStatus | None = None
    verified_by_person_id: UUID | None = None
    issuing_body: str | None = Field(default=None, max_length=240)
    credential_number: str | None = Field(default=None, max_length=160)
    issued_at: date | None = None
    expires_at: date | None = None
    renewal_due_at: date | None = None
    verification_url: str | None = Field(default=None, max_length=500)
    evidence_object_key: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class ComplianceCredentialRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    verified_by_person_id: UUID | None
    credential_type: ComplianceCredentialType
    status: ComplianceCredentialStatus
    title: str
    issuing_body: str | None
    credential_number: str | None
    issued_at: date | None
    expires_at: date | None
    renewal_due_at: date | None
    verification_url: str | None
    evidence_object_key: str | None
    notes: str | None
    created_at: datetime


class ComplianceQueueItemRead(BaseModel):
    source: str
    id: UUID
    person_id: UUID | None
    person_name: str | None
    title: str
    status: str
    due_on: date | None
    severity: str
    reason: str


class ComplianceSummaryRead(BaseModel):
    organization_id: UUID
    generated_at: datetime
    overall_compliance_percent: float
    total_background_checks: int
    clear_background_checks: int
    review_background_checks: int
    expired_background_checks: int
    total_credentials: int
    verified_credentials: int
    expiring_credentials: int
    expired_credentials: int
    revoked_credentials: int
    open_incidents: int
    critical_incidents: int
    regulatory_incidents: int
    blockers: list[ComplianceQueueItemRead]
    renewals_due: list[ComplianceQueueItemRead]
    investigation_queue: list[ComplianceQueueItemRead]


class ComplianceReconciliationRead(BaseModel):
    organization_id: UUID
    reconciled_at: datetime
    background_checks_expired: int
    credentials_expired: int
    credentials_expiring_soon: int


class ComplianceReconciliationWorkerRunRead(BaseModel):
    organization_id: UUID | None
    eligible_count: int
    executed_count: int
    skipped_count: int
    failed_count: int
    organization_ids: list[UUID]
    background_checks_expired: int
    credentials_expired: int
    credentials_expiring_soon: int


class IncidentReportPackageCreate(BaseModel):
    organization_id: UUID
    incident_id: UUID
    agency_name: str = Field(min_length=2, max_length=240)
    jurisdiction: str = Field(min_length=2, max_length=160)
    due_at: date | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    narrative: str | None = Field(default=None, max_length=12000)
    checklist_json: str | None = Field(default=None, max_length=12000)
    submission_payload: str | None = Field(default=None, max_length=12000)
    notes: str | None = Field(default=None, max_length=2000)


class IncidentReportPackageUpdate(BaseModel):
    status: IncidentReportPackageStatus | None = None
    due_at: date | None = None
    submitted_at: datetime | None = None
    accepted_at: datetime | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    narrative: str | None = Field(default=None, max_length=12000)
    checklist_json: str | None = Field(default=None, max_length=12000)
    submission_payload: str | None = Field(default=None, max_length=12000)
    notes: str | None = Field(default=None, max_length=2000)


class IncidentReportPackageRead(BaseModel):
    id: UUID
    organization_id: UUID
    incident_id: UUID
    prepared_by_person_id: UUID | None
    submitted_by_person_id: UUID | None
    agency_name: str
    jurisdiction: str
    status: IncidentReportPackageStatus
    due_at: date | None
    submitted_at: datetime | None
    accepted_at: datetime | None
    external_reference: str | None
    narrative: str
    checklist_json: str | None
    submission_payload: str | None
    notes: str | None
    created_at: datetime


class IncidentReportPackageArtifactRead(BaseModel):
    id: UUID
    organization_id: UUID
    incident_id: UUID
    generated_at: datetime
    download_filename: str
    content_type: str
    artifact_format: str
    content: str
    content_base64: str | None
    checksum: str
    size_bytes: int
    artifact_url: str
    storage_key: str


class IncidentReportPackageArtifactLinkRead(BaseModel):
    id: UUID
    organization_id: UUID
    incident_id: UUID
    generated_at: datetime
    artifact_format: str
    signed_url: str
    expires_at: datetime
    content_type: str
    filename: str
    checksum: str
    size_bytes: int
    artifact_url: str
    storage_key: str


class IncidentReportPackageProviderSubmissionRead(BaseModel):
    package_id: UUID
    organization_id: UUID
    incident_id: UUID
    agency_name: str
    jurisdiction: str
    provider_profile: str
    provider_schema_id: str
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    provider_status_code: int | None
    provider_reference: str | None
    package_status: IncidentReportPackageStatus
    artifact_url: str | None
    storage_key: str | None
    checksum: str | None
    failure_reason: str | None
    submitted_at: datetime


class IncidentInsuranceClaimCreate(BaseModel):
    organization_id: UUID
    incident_id: UUID
    claimant_person_id: UUID | None = None
    claim_type: InsuranceClaimType = InsuranceClaimType.INJURY_MEDICAL
    provider_name: str = Field(min_length=2, max_length=240)
    policy_number: str | None = Field(default=None, max_length=160)
    claim_number: str | None = Field(default=None, max_length=160)
    claimed_amount_cents: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    reserve_amount_cents: int = Field(default=0, ge=0)
    tracking_url: str | None = Field(default=None, max_length=500)
    documentation_checklist_json: str | None = Field(default=None, max_length=12000)
    submission_payload: str | None = Field(default=None, max_length=12000)
    notes: str | None = Field(default=None, max_length=4000)


class IncidentInsuranceClaimUpdate(BaseModel):
    status: InsuranceClaimStatus | None = None
    claimant_person_id: UUID | None = None
    policy_number: str | None = Field(default=None, max_length=160)
    claim_number: str | None = Field(default=None, max_length=160)
    coverage_verified_at: datetime | None = None
    submitted_at: datetime | None = None
    closed_at: datetime | None = None
    claimed_amount_cents: int | None = Field(default=None, ge=0)
    approved_amount_cents: int | None = Field(default=None, ge=0)
    paid_amount_cents: int | None = Field(default=None, ge=0)
    reserve_amount_cents: int | None = Field(default=None, ge=0)
    tracking_url: str | None = Field(default=None, max_length=500)
    documentation_checklist_json: str | None = Field(default=None, max_length=12000)
    submission_payload: str | None = Field(default=None, max_length=12000)
    communication_log: str | None = Field(default=None, max_length=12000)
    notes: str | None = Field(default=None, max_length=4000)


class IncidentInsuranceClaimRead(BaseModel):
    id: UUID
    organization_id: UUID
    incident_id: UUID
    claimant_person_id: UUID | None
    prepared_by_person_id: UUID | None
    submitted_by_person_id: UUID | None
    claim_type: InsuranceClaimType
    status: InsuranceClaimStatus
    provider_name: str
    policy_number: str | None
    claim_number: str | None
    coverage_verified_at: datetime | None
    submitted_at: datetime | None
    closed_at: datetime | None
    claimed_amount_cents: int
    approved_amount_cents: int
    paid_amount_cents: int
    currency: str
    reserve_amount_cents: int
    tracking_url: str | None
    documentation_checklist_json: str | None
    submission_payload: str | None
    communication_log: str | None
    notes: str | None
    created_at: datetime


class IncidentInsuranceClaimProviderSyncRead(BaseModel):
    claim_id: UUID
    organization_id: UUID
    action: str
    provider_profile: str
    provider_schema_id: str
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    provider_status_code: int | None
    provider_reference: str | None
    tracking_url: str | None
    claim_status: InsuranceClaimStatus
    failure_reason: str | None
    synced_at: datetime


class IncidentMedicalClearanceCreate(BaseModel):
    organization_id: UUID
    incident_id: UUID
    athlete_person_id: UUID | None = None
    clearance_type: str = Field(default="return_to_play", min_length=2, max_length=120)
    assessed_at: datetime | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    restrictions: str | None = Field(default=None, max_length=4000)
    return_to_play_stage: str | None = Field(default=None, max_length=120)
    provider_name: str | None = Field(default=None, max_length=240)
    documentation_object_key: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class IncidentMedicalClearanceUpdate(BaseModel):
    status: MedicalClearanceStatus | None = None
    reviewed_by_person_id: UUID | None = None
    assessed_at: datetime | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    restrictions: str | None = Field(default=None, max_length=4000)
    return_to_play_stage: str | None = Field(default=None, max_length=120)
    provider_name: str | None = Field(default=None, max_length=240)
    documentation_object_key: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class IncidentMedicalClearanceRead(BaseModel):
    id: UUID
    organization_id: UUID
    incident_id: UUID
    athlete_person_id: UUID
    reviewed_by_person_id: UUID | None
    status: MedicalClearanceStatus
    clearance_type: str
    assessed_at: datetime | None
    valid_from: date | None
    valid_until: date | None
    restrictions: str | None
    return_to_play_stage: str | None
    provider_name: str | None
    documentation_object_key: str | None
    notes: str | None
    created_at: datetime


class IncidentMedicalClearanceProviderSyncRead(BaseModel):
    clearance_id: UUID
    organization_id: UUID
    incident_id: UUID
    athlete_person_id: UUID
    action: str
    provider_profile: str
    provider_schema_id: str
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    provider_status_code: int | None
    provider_reference: str | None
    clearance_status: MedicalClearanceStatus
    documentation_object_key: str | None
    failure_reason: str | None
    synced_at: datetime
