from __future__ import annotations

from typing import Required, TypedDict

UUID = str
ISODate = str
ISODateTime = str
JSONValue = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
JsonObject = dict[str, JSONValue]
QueryParams = dict[str, str | int | float | bool | None]


class DeveloperApiKeyInspection(TypedDict, total=False):
    valid: Required[bool]
    organization_id: Required[UUID]
    application_id: Required[UUID]
    api_key_id: Required[UUID]
    client_id: Required[str]
    application_name: Required[str]
    environment: Required[str]
    scopes: Required[list[str]]
    rate_limit_per_minute: Required[int]
    usage_count: Required[int]
    window_started_at: ISODateTime | None
    window_request_count: Required[int]
    quota_counter_mode: Required[str]


class Organization(TypedDict, total=False):
    id: Required[UUID]
    name: Required[str]
    slug: Required[str]
    organization_type: Required[str]
    association_level: str | None
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
    my_roles: Required[list[str]]


class PersonCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    display_name: Required[str]
    given_name: str | None
    family_name: str | None
    date_of_birth: ISODate | None
    primary_email: str | None
    primary_phone: str | None
    country_code: str | None
    notes: str | None
    membership_role: str
    membership_title: str | None


class Person(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    membership_id: UUID | None
    display_name: Required[str]
    given_name: str | None
    family_name: str | None
    date_of_birth: ISODate | None
    primary_email: str | None
    primary_phone: str | None
    country_code: str | None
    notes: str | None
    membership_role: str | None
    membership_title: str | None


class GuardianLinkCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    guardian_person_id: UUID | None
    guardian_email: str | None
    guardian_phone: str | None
    guardian_display_name: str | None
    relationship_kind: str
    relationship: str | None
    can_sign_consent: bool
    can_view_medical: bool
    emergency_contact: bool
    can_pick_up: bool
    is_primary: bool
    notes: str | None


class GuardianRelationship(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    athlete_person_id: Required[UUID]
    guardian_person_id: Required[UUID]
    guardian_display_name: Required[str]
    relationship_kind: Required[str]
    relationship: Required[str]
    can_sign_consent: Required[bool]
    can_view_medical: Required[bool]
    emergency_contact: Required[bool]
    can_pick_up: Required[bool]
    is_primary: Required[bool]
    notes: str | None


class ConsentRequestCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    guardian_person_id: Required[UUID]
    scope_type: Required[str]
    scope_id: UUID | None
    channel: Required[str]
    destination: str | None
    expires_at: ISODateTime | None
    external_message_id: str | None
    notes: str | None


class ConsentRequest(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    athlete_person_id: Required[UUID]
    guardian_person_id: Required[UUID]
    scope_type: Required[str]
    scope_id: UUID | None
    channel: Required[str]
    destination: Required[str]
    status: Required[str]
    expires_at: ISODateTime | None
    sent_at: ISODateTime | None
    fulfilled_at: ISODateTime | None
    external_message_id: str | None
    one_time_token: Required[str]


class TeamCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    name: Required[str]
    sport: Required[str]
    sport_format: str
    age_group: str | None
    gender_category: str | None
    season_label: str | None


class Team(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    name: Required[str]
    sport: Required[str]
    sport_format: Required[str]
    age_group: str | None
    gender_category: str | None
    season_label: str | None


class TeamMemberAdd(TypedDict, total=False):
    person_id: Required[UUID]
    role: str
    status: str
    primary_position: str | None
    jersey_number: str | None
    is_captain: bool


class TeamRosterEntry(TypedDict, total=False):
    id: Required[UUID]
    team_id: Required[UUID]
    athlete_profile_id: Required[UUID]
    role: Required[str]
    primary_position: str | None
    jersey_number: str | None
    is_captain: Required[bool]
    status: Required[str]


class EventCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    team_id: UUID | None
    event_type: Required[str]
    title: Required[str]
    starts_at: Required[ISODateTime]
    ends_at: ISODateTime | None
    timezone: str | None
    venue_name: str | None
    notes: str | None


class Event(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    team_id: UUID | None
    event_type: Required[str]
    title: Required[str]
    starts_at: Required[ISODateTime]
    ends_at: ISODateTime | None
    timezone: str | None
    venue_name: str | None
    notes: str | None


class AttendanceRecordUpsert(TypedDict, total=False):
    person_id: Required[UUID]
    status: Required[str]
    note: str | None


class AttendanceRecord(TypedDict, total=False):
    id: Required[UUID]
    event_id: Required[UUID]
    person_id: Required[UUID]
    status: Required[str]
    recorded_by_person_id: UUID | None
    guardian_consent_id: UUID | None
    note: str | None
    clearance_status: str | None
    medical_clearance_status: str | None
    medical_clearance_id: UUID | None
    medical_clearance_reason: str | None
    attendance_policy_code: str | None
    attendance_policy_decision: str | None
    attendance_policy_warnings: Required[list[str]]


class Agent(TypedDict, total=False):
    id: Required[UUID]
    organization_id: UUID | None
    name: Required[str]
    kind: Required[str]
    purpose: Required[str]
    status: Required[str]
    model_policy: str | None


class AgentTaskCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    task_type: Required[str]
    title: Required[str]
    input_ref: str | None


class AgentTask(TypedDict, total=False):
    id: Required[UUID]
    agent_id: Required[UUID]
    organization_id: Required[UUID]
    task_type: Required[str]
    title: Required[str]
    status: Required[str]
    requested_by_person_id: UUID | None
    input_ref: str | None
    output_ref: str | None
    review_notes: str | None
    review_assigned_to_person_id: UUID | None
    review_due_at: ISODateTime | None
    review_priority: Required[str]
    review_assignment_notes: str | None
    approval_required_count: Required[int]
    approval_approved_count: Required[int]
    approval_rejected_count: Required[int]
    approval_pending_count: Required[int]
    approval_status: Required[str]
    approval_last_decided_at: ISODateTime | None
    governance_policy_rule_id: UUID | None
    governance_policy_code: str | None
    governance_policy_decision: str | None
    governance_policy_risk_level: str | None
    governance_policy_rationale: str | None


class CommunicationTemplateCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    name: Required[str]
    message_type: Required[str]
    channel: str
    subject_template: Required[str]
    body_template: Required[str]
    variables: str | None


class CommunicationTemplate(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    name: Required[str]
    message_type: Required[str]
    channel: Required[str]
    subject_template: Required[str]
    body_template: Required[str]
    variables: str | None
    status: Required[str]


class CommunicationMessageCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    template_id: UUID | None
    message_type: Required[str]
    channel: str
    scope_type: Required[str]
    scope_id: Required[UUID]
    recipient_person_ids: list[UUID]
    subject: Required[str]
    body: Required[str]
    urgent: bool
    quiet_hours_override: bool
    scheduled_for: ISODateTime | None
    copy_guardians_for_minors: bool


class CommunicationMessage(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    template_id: UUID | None
    created_by_person_id: UUID | None
    message_type: Required[str]
    channel: Required[str]
    scope_type: Required[str]
    scope_id: Required[UUID]
    subject: Required[str]
    body: Required[str]
    urgent: Required[bool]
    quiet_hours_override: Required[bool]
    scheduled_for: ISODateTime | None
    sent_at: ISODateTime | None
    status: Required[str]
    recipient_count: Required[int]
    escalates_message_id: UUID | None
    escalation_level: Required[int]
    escalation_triggered_at: ISODateTime | None
    escalation_reason: str | None


class MessageRecipient(TypedDict, total=False):
    id: Required[UUID]
    message_id: Required[UUID]
    person_id: Required[UUID]
    person_name: Required[str]
    destination: str | None
    delivery_status: Required[str]
    delivered_at: ISODateTime | None
    read_at: ISODateTime | None
    failure_reason: str | None


class CommunicationDispatchSummary(TypedDict, total=False):
    message_id: Required[UUID]
    attempted: Required[int]
    sent: Required[int]
    delivered: Required[int]
    failed: Required[int]
    suppressed: Required[int]
    queued: Required[int]
    transport_mode: Required[str]


class BillingPlan(TypedDict, total=False):
    id: Required[UUID]
    code: Required[str]
    name: Required[str]
    description: str | None
    base_price: Required[str]
    currency: Required[str]
    billing_cycle: Required[str]
    included_athletes: Required[int]
    included_teams: Required[int]
    included_agent_tasks: Required[int]
    included_storage_gb: Required[int]
    per_athlete_price: Required[str]
    per_agent_task_price: Required[str]
    features: str | None
    status: Required[str]


class BillingSubscription(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    billing_plan_id: Required[UUID]
    billing_cycle: Required[str]
    current_period_start: Required[ISODate]
    current_period_end: Required[ISODate]
    trial_ends_on: ISODate | None
    next_billing_on: ISODate | None
    seats_purchased: Required[int]
    negotiated_price: str | None
    discount_code: str | None
    external_customer_id: str | None
    external_subscription_id: str | None
    notes: str | None
    status: Required[str]
    cancel_at_period_end: Required[bool]


class BillingUsageMeter(TypedDict, total=False):
    id: Required[UUID]
    code: Required[str]
    name: Required[str]
    unit: Required[str]
    included_quantity: Required[int]
    overage_price: Required[str]
    aggregation: Required[str]
    status: Required[str]


class BillingUsageRecordCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    subscription_id: Required[UUID]
    usage_meter_id: Required[UUID]
    quantity: Required[int]
    source: str
    external_reference: str | None
    notes: str | None


class BillingUsageRecord(BillingUsageRecordCreate, total=False):
    id: Required[UUID]
    recorded_at: Required[ISODateTime]


class BillingInvoice(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    subscription_id: Required[UUID]
    invoice_number: Required[str]
    period_start: Required[ISODate]
    period_end: Required[ISODate]
    subtotal: Required[str]
    tax_amount: Required[str]
    discount_amount: Required[str]
    total: Required[str]
    amount_paid: Required[str]
    currency: Required[str]
    due_on: ISODate | None
    status: Required[str]
    line_items: str | None
    external_invoice_id: str | None
    dunning_count: Required[int]
    dunning_last_sent_at: ISODateTime | None
    dunning_last_severity: str | None
    late_fee_total: Required[str]
    late_fee_count: Required[int]
    late_fee_last_applied_on: ISODate | None
    payment_retry_count: Required[int]
    payment_retry_last_attempted_at: ISODateTime | None
    payment_retry_next_attempt_at: ISODateTime | None
    payment_retry_last_status: str | None
    payment_retry_last_failure_reason: str | None
    payment_retry_last_provider_reference: str | None


class BillingEntitlement(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    subscription_id: Required[UUID]
    feature_key: Required[str]
    limit_value: int | None
    used_value: Required[int]
    status: Required[str]
    source: Required[str]


class BillingSummary(TypedDict, total=False):
    organization_id: Required[UUID]
    active_subscriptions: Required[int]
    plans: Required[int]
    usage_meters: Required[int]
    usage_records: Required[int]
    open_invoices: Required[int]
    monthly_recurring_revenue: Required[str]
    invoice_outstanding: Required[str]
    entitlements: Required[int]


class TrainingDrillCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    sport: Required[str]
    name: Required[str]
    focus_area: Required[str]
    category: Required[str]
    min_age: int | None
    max_age: int | None
    equipment: str | None
    description: str | None
    coaching_points: str | None
    default_duration_minutes: int | None
    default_intensity: int | None
    status: str


class TrainingDrill(TrainingDrillCreate, total=False):
    id: Required[UUID]


class TrainingPlanCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    team_id: UUID | None
    athlete_profile_id: UUID | None
    title: Required[str]
    focus_area: Required[str]
    period_start: Required[ISODate]
    period_end: Required[ISODate]
    ai_generated: bool
    source_summary: str | None
    load_guidance: str | None
    recovery_protocol: str | None
    progress_checkpoints: str | None


class TrainingPlan(TrainingPlanCreate, total=False):
    id: Required[UUID]
    created_by_person_id: UUID | None
    status: Required[str]
    ai_generated: Required[bool]


class TrainingPlanItemCreate(TypedDict, total=False):
    drill_id: UUID | None
    sequence: int
    day_label: Required[str]
    title: Required[str]
    focus_area: Required[str]
    duration_minutes: Required[int]
    intensity: Required[int]
    notes: str | None


class TrainingPlanItem(TrainingPlanItemCreate, total=False):
    id: Required[UUID]
    plan_id: Required[UUID]
    sequence: Required[int]


class TrainingSessionCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    team_id: Required[UUID]
    plan_id: UUID | None
    event_id: UUID | None
    title: Required[str]
    scheduled_for: Required[ISODateTime]
    duration_minutes: Required[int]
    rpe_target: Required[int]
    objectives: str | None


class TrainingSession(TrainingSessionCreate, total=False):
    id: Required[UUID]
    load_score: Required[float]
    status: Required[str]


class TrainingSessionFeedbackCreate(TypedDict, total=False):
    athlete_profile_id: UUID | None
    readiness_score: Required[int]
    soreness_score: int
    sleep_quality: int
    mood_score: int
    actual_rpe: int | None
    actual_duration_minutes: int | None
    completed: bool
    feedback: str | None
    coach_notes: str | None


class TrainingSessionFeedback(TrainingSessionFeedbackCreate, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    session_plan_id: Required[UUID]
    recorded_by_person_id: UUID | None
    soreness_score: Required[int]
    sleep_quality: Required[int]
    mood_score: Required[int]
    completed: Required[bool]
    recorded_at: Required[ISODateTime]
    readiness_band: Required[str]
    load_delta: float | None
    recommendation: Required[str]


class TrainingAvailabilityCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    team_id: Required[UUID]
    starts_at: Required[ISODateTime]
    days: int
    duration_minutes: int
    earliest_hour: int
    latest_hour: int


class TrainingAvailabilitySlot(TypedDict, total=False):
    starts_at: Required[ISODateTime]
    ends_at: Required[ISODateTime]
    conflict_count: Required[int]
    conflicts: Required[list[str]]
    score: Required[float]
    recommendation: Required[str]


class TrainingAvailability(TypedDict, total=False):
    organization_id: Required[UUID]
    team_id: Required[UUID]
    duration_minutes: Required[int]
    slots: Required[list[TrainingAvailabilitySlot]]


class TrainingCalendarArtifact(TypedDict, total=False):
    organization_id: Required[UUID]
    team_id: UUID | None
    generated_at: Required[ISODateTime]
    starts_at: Required[ISODateTime]
    ends_at: Required[ISODateTime]
    session_count: Required[int]
    content_type: Required[str]
    download_filename: Required[str]
    content: Required[str]
    checksum: Required[str]
    size_bytes: Required[int]


class PerformanceMetricDefinition(TypedDict, total=False):
    id: Required[UUID]
    organization_id: Required[UUID]
    sport: str | None
    code: Required[str]
    name: Required[str]
    category: Required[str]
    unit: str | None
    description: str | None
    min_value: float | None
    max_value: float | None
    weight: Required[float]
    higher_is_better: Required[bool]
    status: Required[str]


class PerformanceObservationCreate(TypedDict, total=False):
    organization_id: Required[UUID]
    metric_definition_id: Required[UUID]
    event_id: UUID | None
    value: Required[float]
    raw_value: str | None
    observed_at: ISODateTime | None
    source: str
    confidence: float | None
    verification_status: str
    notes: str | None


class PerformanceObservation(PerformanceObservationCreate, total=False):
    id: Required[UUID]
    athlete_profile_id: Required[UUID]
    recorded_by_person_id: UUID | None
    observed_at: Required[ISODateTime]
    source: Required[str]
    verification_status: Required[str]
