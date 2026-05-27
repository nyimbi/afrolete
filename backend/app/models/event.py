from datetime import date, datetime
from uuid import UUID

from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import (
    AttendanceStatus,
    BackgroundCheckStatus,
    ComplianceCredentialStatus,
    ComplianceCredentialType,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    ConsentStatus,
    EventType,
    IncidentReportPackageStatus,
    InsuranceClaimStatus,
    InsuranceClaimType,
    MedicalClearanceStatus,
    SafeguardingIncidentSeverity,
    SafeguardingIncidentStatus,
    SafeguardingIncidentType,
    TravelPlanStatus,
    TravelRiskLevel,
    WeatherAlertLevel,
    WeatherDecision,
)


class Event(IdMixin, TimestampMixin, Base):
    __tablename__ = "events"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_type: Mapped[EventType] = mapped_column(enum_type(EventType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    venue_name: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)


class EventWeatherAssessment(IdMixin, TimestampMixin, Base):
    __tablename__ = "event_weather_assessments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    heat_index_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    wbgt_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    humidity_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    aqi: Mapped[int | None] = mapped_column(index=True)
    lightning_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), index=True)
    wind_speed_kph: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    wind_gust_kph: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    precipitation_mm_per_hr: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    alert_level: Mapped[WeatherAlertLevel] = mapped_column(
        enum_type(WeatherAlertLevel), nullable=False, index=True
    )
    decision: Mapped[WeatherDecision] = mapped_column(
        enum_type(WeatherDecision), nullable=False, index=True
    )
    recommended_actions: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class EventTravelPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "event_travel_plans"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    status: Mapped[TravelPlanStatus] = mapped_column(
        enum_type(TravelPlanStatus),
        default=TravelPlanStatus.DRAFT,
        nullable=False,
        index=True,
    )
    destination: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    travel_mode: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    route_summary: Mapped[str | None] = mapped_column(Text)
    vehicle_details: Mapped[str | None] = mapped_column(Text)
    driver_details: Mapped[str | None] = mapped_column(Text)
    staff_manifest: Mapped[str | None] = mapped_column(Text)
    passenger_manifest: Mapped[str | None] = mapped_column(Text)
    lodging_details: Mapped[str | None] = mapped_column(Text)
    meal_plan: Mapped[str | None] = mapped_column(Text)
    equipment_manifest: Mapped[str | None] = mapped_column(Text)
    emergency_contacts: Mapped[str | None] = mapped_column(Text)
    medical_access_plan: Mapped[str | None] = mapped_column(Text)
    route_weather_risk: Mapped[str | None] = mapped_column(String(80), index=True)
    driver_certification_status: Mapped[str | None] = mapped_column(String(80), index=True)
    vehicle_inspection_status: Mapped[str | None] = mapped_column(String(80), index=True)
    consent_required: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    consent_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cost_per_participant: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    risk_level: Mapped[TravelRiskLevel] = mapped_column(
        enum_type(TravelRiskLevel),
        default=TravelRiskLevel.MEDIUM,
        nullable=False,
        index=True,
    )
    risk_assessment: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class EventTravelApproval(IdMixin, TimestampMixin, Base):
    __tablename__ = "event_travel_approvals"
    __table_args__ = (UniqueConstraint("travel_plan_id", "approval_level"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    travel_plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("event_travel_plans.id"), index=True)
    approval_level: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    approver_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    decided_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class EventTravelChecklistItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "event_travel_checklist_items"
    __table_args__ = (UniqueConstraint("travel_plan_id", "checklist_type", "item_label"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    travel_plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("event_travel_plans.id"), index=True)
    checklist_type: Mapped[str] = mapped_column(String(80), default="pre_trip_inspection", nullable=False, index=True)
    item_label: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    completed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class EventTravelLocationUpdate(IdMixin, TimestampMixin, Base):
    __tablename__ = "event_travel_location_updates"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    travel_plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("event_travel_plans.id"), index=True)
    phase: Mapped[str] = mapped_column(String(40), default="en_route", nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    speed_kph: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    heading_degrees: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    notification_message_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("communication_messages.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class EventTravelExpense(IdMixin, TimestampMixin, Base):
    __tablename__ = "event_travel_expenses"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    travel_plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("event_travel_plans.id"), index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    vendor: Mapped[str | None] = mapped_column(String(180), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    incurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    paid_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reimbursement_status: Mapped[str] = mapped_column(String(40), default="submitted", nullable=False, index=True)
    approved_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reimbursed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class AttendanceRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("event_id", "person_id"),)

    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[AttendanceStatus] = mapped_column(enum_type(AttendanceStatus), nullable=False)
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    guardian_consent_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("activity_consents.id"), index=True
    )
    note: Mapped[str | None] = mapped_column(Text)


class ConsentRequest(IdMixin, TimestampMixin, Base):
    __tablename__ = "consent_requests"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    guardian_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    scope_type: Mapped[ConsentScopeType] = mapped_column(
        enum_type(ConsentScopeType),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[UUID | None] = mapped_column(GUID(), index=True)
    channel: Mapped[ConsentCaptureChannel] = mapped_column(
        enum_type(ConsentCaptureChannel),
        nullable=False,
        index=True,
    )
    destination: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[ConsentRequestStatus] = mapped_column(
        enum_type(ConsentRequestStatus),
        default=ConsentRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_message_id: Mapped[str | None] = mapped_column(String(240), index=True)
    response_payload: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class ActivityConsent(IdMixin, TimestampMixin, Base):
    __tablename__ = "activity_consents"
    __table_args__ = (
        UniqueConstraint(
            "athlete_person_id",
            "guardian_person_id",
            "scope_type",
            "scope_id",
            name="uq_activity_consents_guardian_scope",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    guardian_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    scope_type: Mapped[ConsentScopeType] = mapped_column(
        enum_type(ConsentScopeType),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[UUID | None] = mapped_column(GUID(), index=True)
    status: Mapped[ConsentStatus] = mapped_column(
        enum_type(ConsentStatus),
        default=ConsentStatus.PENDING,
        nullable=False,
        index=True,
    )
    source_request_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("consent_requests.id"), index=True
    )
    capture_channel: Mapped[ConsentCaptureChannel] = mapped_column(
        enum_type(ConsentCaptureChannel),
        default=ConsentCaptureChannel.MANUAL,
        nullable=False,
        index=True,
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    consent_text: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class SafeguardingIncident(IdMixin, TimestampMixin, Base):
    __tablename__ = "safeguarding_incidents"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    athlete_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reported_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    assigned_to_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    incident_type: Mapped[SafeguardingIncidentType] = mapped_column(
        enum_type(SafeguardingIncidentType), nullable=False, index=True
    )
    severity: Mapped[SafeguardingIncidentSeverity] = mapped_column(
        enum_type(SafeguardingIncidentSeverity), nullable=False, index=True
    )
    status: Mapped[SafeguardingIncidentStatus] = mapped_column(
        enum_type(SafeguardingIncidentStatus),
        default=SafeguardingIncidentStatus.OPEN,
        nullable=False,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(240))
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_action: Mapped[str | None] = mapped_column(Text)
    parent_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    medical_follow_up_required: Mapped[str] = mapped_column(String(40), default="unknown", index=True)
    regulatory_report_required: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class IncidentReportPackage(IdMixin, TimestampMixin, Base):
    __tablename__ = "incident_report_packages"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    incident_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("safeguarding_incidents.id"), index=True
    )
    prepared_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    submitted_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    agency_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    status: Mapped[IncidentReportPackageStatus] = mapped_column(
        enum_type(IncidentReportPackageStatus),
        default=IncidentReportPackageStatus.DRAFT,
        nullable=False,
        index=True,
    )
    due_at: Mapped[date | None] = mapped_column(Date, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    checklist_json: Mapped[str | None] = mapped_column(Text)
    submission_payload: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class IncidentInsuranceClaim(IdMixin, TimestampMixin, Base):
    __tablename__ = "incident_insurance_claims"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    incident_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("safeguarding_incidents.id"), index=True
    )
    claimant_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    prepared_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    submitted_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    claim_type: Mapped[InsuranceClaimType] = mapped_column(
        enum_type(InsuranceClaimType),
        nullable=False,
        index=True,
    )
    status: Mapped[InsuranceClaimStatus] = mapped_column(
        enum_type(InsuranceClaimStatus),
        default=InsuranceClaimStatus.DRAFT,
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    policy_number: Mapped[str | None] = mapped_column(String(160), index=True)
    claim_number: Mapped[str | None] = mapped_column(String(160), index=True)
    coverage_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    claimed_amount_cents: Mapped[int] = mapped_column(default=0, nullable=False)
    approved_amount_cents: Mapped[int] = mapped_column(default=0, nullable=False)
    paid_amount_cents: Mapped[int] = mapped_column(default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    reserve_amount_cents: Mapped[int] = mapped_column(default=0, nullable=False)
    tracking_url: Mapped[str | None] = mapped_column(String(500))
    documentation_checklist_json: Mapped[str | None] = mapped_column(Text)
    submission_payload: Mapped[str | None] = mapped_column(Text)
    communication_log: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class IncidentMedicalClearance(IdMixin, TimestampMixin, Base):
    __tablename__ = "incident_medical_clearances"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    incident_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("safeguarding_incidents.id"), index=True
    )
    athlete_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[MedicalClearanceStatus] = mapped_column(
        enum_type(MedicalClearanceStatus),
        default=MedicalClearanceStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )
    clearance_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    valid_from: Mapped[date | None] = mapped_column(Date, index=True)
    valid_until: Mapped[date | None] = mapped_column(Date, index=True)
    restrictions: Mapped[str | None] = mapped_column(Text)
    return_to_play_stage: Mapped[str | None] = mapped_column(String(120), index=True)
    provider_name: Mapped[str | None] = mapped_column(String(240))
    documentation_object_key: Mapped[str | None] = mapped_column(String(500), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class BackgroundCheck(IdMixin, TimestampMixin, Base):
    __tablename__ = "background_checks"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    requested_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    provider: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    check_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[BackgroundCheckStatus] = mapped_column(
        enum_type(BackgroundCheckStatus),
        default=BackgroundCheckStatus.REQUESTED,
        nullable=False,
        index=True,
    )
    risk_level: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False, index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[date | None] = mapped_column(Date, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    result_summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class ComplianceCredential(IdMixin, TimestampMixin, Base):
    __tablename__ = "compliance_credentials"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    verified_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    credential_type: Mapped[ComplianceCredentialType] = mapped_column(
        enum_type(ComplianceCredentialType),
        nullable=False,
        index=True,
    )
    status: Mapped[ComplianceCredentialStatus] = mapped_column(
        enum_type(ComplianceCredentialStatus),
        default=ComplianceCredentialStatus.PENDING,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    issuing_body: Mapped[str | None] = mapped_column(String(240), index=True)
    credential_number: Mapped[str | None] = mapped_column(String(160), index=True)
    issued_at: Mapped[date | None] = mapped_column(Date)
    expires_at: Mapped[date | None] = mapped_column(Date, index=True)
    renewal_due_at: Mapped[date | None] = mapped_column(Date, index=True)
    verification_url: Mapped[str | None] = mapped_column(String(500))
    evidence_object_key: Mapped[str | None] = mapped_column(String(500), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
