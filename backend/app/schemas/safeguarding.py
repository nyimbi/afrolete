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


class FamilyDashboardActionRead(BaseModel):
    priority: str
    action_type: str
    title: str
    detail: str
    athlete_person_id: UUID | None = None
    event_id: UUID | None = None
    consent_request_id: UUID | None = None
    due_at: datetime | None = None


class FamilyScheduleConflictRead(BaseModel):
    starts_at: datetime
    ends_at: datetime
    athlete_names: list[str]
    event_titles: list[str]
    event_ids: list[UUID]
    recommendation: str


class FamilyDashboardRead(BaseModel):
    organization_id: UUID
    guardian_person_id: UUID
    generated_at: datetime
    child_count: int
    pending_consent_count: int
    unread_message_count: int
    urgent_unread_count: int
    upcoming_event_count: int
    rsvp_needed_count: int
    clearance_blocked_count: int
    schedule_conflict_count: int
    active_goal_count: int
    award_count: int
    ai_recommendation_count: int
    open_ai_appeal_count: int
    next_event_at: datetime | None
    next_action_label: str
    action_items: list[FamilyDashboardActionRead]
    schedule_conflicts: list[FamilyScheduleConflictRead]


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


class SafeguardingIncidentEvidenceUploadCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    content_base64: str = Field(min_length=1)
    evidence_type: str = Field(default="document", min_length=2, max_length=80)
    review_status: str = Field(default="needs_review", pattern="^(needs_review|accepted|rejected)$")
    notes: str | None = Field(default=None, max_length=2000)


class SafeguardingIncidentEvidenceUploadRead(BaseModel):
    incident_id: UUID
    organization_id: UUID
    filename: str
    content_type: str
    evidence_type: str
    review_status: str
    size_bytes: int
    checksum: str
    evidence_url: str
    storage_key: str
    uploaded_at: datetime
    incident: "SafeguardingIncidentRead"


class SafeguardingIncidentEvidenceLinkCreate(BaseModel):
    storage_key: str = Field(min_length=1, max_length=800)
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    checksum: str | None = Field(default=None, max_length=64)
    ttl_seconds: int | None = Field(default=None, ge=60, le=86400)


class SafeguardingIncidentEvidenceLinkRead(BaseModel):
    incident_id: UUID
    organization_id: UUID
    signed_url: str
    expires_at: datetime
    filename: str
    content_type: str
    checksum: str
    size_bytes: int
    evidence_url: str
    storage_key: str


class SafeguardingIncidentEvidenceApprovalPolicyRead(BaseModel):
    incident_id: UUID
    organization_id: UUID
    incident_title: str
    incident_status: SafeguardingIncidentStatus
    incident_severity: SafeguardingIncidentSeverity
    filename: str
    content_type: str
    evidence_type: str
    review_status: str
    policy_risk_level: str
    approval_required: bool
    approval_status: str
    required_approval_levels: list[str]
    missing_approval_levels: list[str]
    recommended_review_status: str
    acceptance_blocked_by_policy: bool
    policy_summary: str
    rationale: list[str]
    matched_rule_codes: list[str] = Field(default_factory=list)


class SafeguardingEvidencePolicyRuleCreate(BaseModel):
    organization_id: UUID
    rule_code: str = Field(min_length=2, max_length=120, pattern="^[A-Za-z0-9_.-]+$")
    title: str = Field(min_length=2, max_length=240)
    active: bool = True
    incident_type: SafeguardingIncidentType | None = None
    minimum_severity: SafeguardingIncidentSeverity | None = None
    evidence_type_contains: str | None = Field(default=None, max_length=120)
    medical_follow_up_values: str | None = Field(default=None, max_length=240)
    regulatory_required: bool | None = None
    athlete_linked_required: bool | None = None
    required_approval_level: str = Field(default="safeguarding_lead", min_length=2, max_length=80)
    risk_level: str = Field(default="high", pattern="^(low|medium|high|critical)$")
    recommended_review_status: str = Field(default="escalated", pattern="^(needs_review|accepted|rejected|escalated)$")
    block_acceptance: bool = True
    rationale: str = Field(min_length=2, max_length=2000)


class SafeguardingEvidencePolicyRuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=240)
    active: bool | None = None
    incident_type: SafeguardingIncidentType | None = None
    minimum_severity: SafeguardingIncidentSeverity | None = None
    evidence_type_contains: str | None = Field(default=None, max_length=120)
    medical_follow_up_values: str | None = Field(default=None, max_length=240)
    regulatory_required: bool | None = None
    athlete_linked_required: bool | None = None
    required_approval_level: str | None = Field(default=None, min_length=2, max_length=80)
    risk_level: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    recommended_review_status: str | None = Field(default=None, pattern="^(needs_review|accepted|rejected|escalated)$")
    block_acceptance: bool | None = None
    rationale: str | None = Field(default=None, min_length=2, max_length=2000)


class SafeguardingEvidencePolicyRuleRead(BaseModel):
    id: UUID
    organization_id: UUID
    rule_code: str
    title: str
    active: bool
    incident_type: SafeguardingIncidentType | None
    minimum_severity: SafeguardingIncidentSeverity | None
    evidence_type_contains: str | None
    medical_follow_up_values: str | None
    regulatory_required: bool | None
    athlete_linked_required: bool | None
    required_approval_level: str
    risk_level: str
    recommended_review_status: str
    block_acceptance: bool
    rationale: str
    created_at: datetime
    updated_at: datetime


class SafeguardingIncidentEvidenceReviewItemRead(BaseModel):
    incident_id: UUID
    organization_id: UUID
    incident_title: str
    incident_status: SafeguardingIncidentStatus
    incident_severity: SafeguardingIncidentSeverity
    filename: str
    content_type: str
    evidence_type: str
    review_status: str
    size_bytes: int
    checksum: str
    evidence_url: str
    storage_key: str
    uploaded_at: datetime
    latest_reviewed_at: datetime | None = None
    latest_review_notes: str | None = None
    approval_policy: SafeguardingIncidentEvidenceApprovalPolicyRead | None = None


class SafeguardingIncidentEvidenceReviewActionCreate(BaseModel):
    storage_key: str = Field(min_length=1, max_length=800)
    filename: str = Field(min_length=1, max_length=240)
    checksum: str | None = Field(default=None, max_length=64)
    review_status: str = Field(pattern="^(needs_review|accepted|rejected|escalated)$")
    review_notes: str | None = Field(default=None, max_length=2000)
    escalate_incident: bool = False
    regulatory_report_required: bool | None = None


class SafeguardingIncidentEvidenceReviewActionRead(BaseModel):
    incident_id: UUID
    organization_id: UUID
    filename: str
    review_status: str
    reviewer_person_id: UUID | None
    reviewed_at: datetime
    checksum: str
    size_bytes: int
    storage_key: str
    incident_status: SafeguardingIncidentStatus
    incident_severity: SafeguardingIncidentSeverity
    regulatory_report_required: bool
    action_summary: str
    resolution_notes: str | None
    approval_policy: SafeguardingIncidentEvidenceApprovalPolicyRead | None = None


class SafeguardingIncidentAccessControlRead(BaseModel):
    incident_id: UUID
    organization_id: UUID
    relationship_count: int
    touched_relationships: list[str]
    can_manage_case: bool
    can_review_evidence: bool
    synced_at: datetime


class SafeguardingIncidentAccessGrantCreate(BaseModel):
    person_id: UUID
    relation: str = Field(
        pattern="^(case_manager|assigned_to|evidence_reviewer|medical_viewer|regulator|guardian|reporter)$"
    )
    reason: str | None = Field(default=None, max_length=2000)


class SafeguardingIncidentAccessGrantRevoke(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class SafeguardingIncidentAccessGrantRead(BaseModel):
    id: UUID
    organization_id: UUID
    incident_id: UUID
    person_id: UUID
    relation: str
    active: bool
    granted_by_person_id: UUID | None
    revoked_by_person_id: UUID | None
    granted_reason: str | None
    revoked_reason: str | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime


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


class BackgroundCheckEvidenceDocumentUploadCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    content_base64: str = Field(min_length=1)
    document_type: str = Field(default="screening_report", min_length=2, max_length=80)
    review_status: str = Field(default="needs_review", pattern="^(needs_review|accepted|rejected|escalated)$")
    provider_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=2000)


class BackgroundCheckEvidenceDocumentReviewCreate(BaseModel):
    review_status: str = Field(pattern="^(needs_review|accepted|rejected|escalated)$")
    review_notes: str | None = Field(default=None, max_length=2000)
    check_status: BackgroundCheckStatus | None = None
    risk_level: str | None = Field(default=None, max_length=40)
    result_summary: str | None = Field(default=None, max_length=4000)


class BackgroundCheckEvidenceDocumentRead(BaseModel):
    id: UUID
    organization_id: UUID
    background_check_id: UUID
    person_id: UUID
    uploaded_by_person_id: UUID | None
    reviewed_by_person_id: UUID | None
    filename: str
    content_type: str
    document_type: str
    review_status: str
    size_bytes: int
    checksum: str
    storage_key: str
    evidence_url: str
    provider_reference: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    notes: str | None
    background_check_status: BackgroundCheckStatus
    background_check_risk_level: str
    created_at: datetime
    updated_at: datetime


class BackgroundCheckEvidenceDocumentLinkCreate(BaseModel):
    ttl_seconds: int | None = Field(default=None, ge=60, le=86400)


class BackgroundCheckEvidenceDocumentLinkRead(BaseModel):
    document_id: UUID
    background_check_id: UUID
    organization_id: UUID
    signed_url: str
    expires_at: datetime
    filename: str
    content_type: str
    checksum: str
    size_bytes: int
    evidence_url: str
    storage_key: str


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
