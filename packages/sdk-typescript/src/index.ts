export type UUID = string;
export type ISODateTime = string;
export type ISODate = string;

export interface AfroLeteClientOptions {
  baseUrl: string;
  apiKey: string;
  fetch?: typeof fetch;
}

export interface AfroLeteRequestErrorDetails {
  status: number;
  statusText: string;
  body: unknown;
}

export class AfroLeteRequestError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly body: unknown;

  constructor(details: AfroLeteRequestErrorDetails) {
    super(`AfroLete request failed with ${details.status} ${details.statusText}`);
    this.name = "AfroLeteRequestError";
    this.status = details.status;
    this.statusText = details.statusText;
    this.body = details.body;
  }
}

export interface DeveloperApiKeyInspection {
  valid: boolean;
  organization_id: UUID;
  application_id: UUID;
  api_key_id: UUID;
  client_id: string;
  application_name: string;
  environment: string;
  scopes: string[];
  rate_limit_per_minute: number;
  usage_count: number;
  window_started_at: ISODateTime | null;
  window_request_count: number;
  quota_counter_mode: string;
}

export interface Organization {
  id: UUID;
  name: string;
  slug: string;
  organization_type: string;
  association_level: string | null;
  country_code: string | null;
  primary_sport: string | null;
  mission: string | null;
  public_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  website_url: string | null;
  subdomain: string | null;
  logo_url: string | null;
  brand_primary_color: string | null;
  brand_secondary_color: string | null;
  my_roles: string[];
}

export interface PersonCreate {
  organization_id: UUID;
  display_name: string;
  given_name?: string | null;
  family_name?: string | null;
  date_of_birth?: string | null;
  primary_email?: string | null;
  primary_phone?: string | null;
  country_code?: string | null;
  notes?: string | null;
  membership_role?: string;
  membership_title?: string | null;
}

export interface Person {
  id: UUID;
  organization_id: UUID;
  membership_id: UUID | null;
  display_name: string;
  given_name: string | null;
  family_name: string | null;
  date_of_birth: string | null;
  primary_email: string | null;
  primary_phone: string | null;
  country_code: string | null;
  notes: string | null;
  membership_role: string | null;
  membership_title: string | null;
}

export interface GuardianLinkCreate {
  organization_id: UUID;
  guardian_person_id?: UUID | null;
  guardian_email?: string | null;
  guardian_phone?: string | null;
  guardian_display_name?: string | null;
  relationship_kind?: string;
  relationship?: string | null;
  can_sign_consent?: boolean;
  can_view_medical?: boolean;
  emergency_contact?: boolean;
  can_pick_up?: boolean;
  is_primary?: boolean;
  notes?: string | null;
}

export interface GuardianRelationship {
  id: UUID;
  organization_id: UUID;
  athlete_person_id: UUID;
  guardian_person_id: UUID;
  guardian_display_name: string;
  relationship_kind: string;
  relationship: string;
  can_sign_consent: boolean;
  can_view_medical: boolean;
  emergency_contact: boolean;
  can_pick_up: boolean;
  is_primary: boolean;
  notes: string | null;
}

export interface ConsentRequestCreate {
  organization_id: UUID;
  guardian_person_id: UUID;
  scope_type: string;
  scope_id?: UUID | null;
  channel: string;
  destination?: string | null;
  expires_at?: string | null;
  external_message_id?: string | null;
  notes?: string | null;
}

export interface ConsentRequest {
  id: UUID;
  organization_id: UUID;
  athlete_person_id: UUID;
  guardian_person_id: UUID;
  scope_type: string;
  scope_id: UUID | null;
  channel: string;
  destination: string;
  status: string;
  expires_at: string | null;
  sent_at: string | null;
  fulfilled_at: string | null;
  external_message_id: string | null;
  one_time_token: string;
}

export interface Event {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  event_type: string;
  title: string;
  starts_at: ISODateTime;
  ends_at: ISODateTime | null;
  timezone: string | null;
  venue_name: string | null;
  notes: string | null;
}

export interface Team {
  id: UUID;
  organization_id: UUID;
  name: string;
  sport: string;
  sport_format: string;
  age_group: string | null;
  gender_category: string | null;
  season_label: string | null;
}

export interface TeamCreate {
  organization_id: UUID;
  name: string;
  sport: string;
  sport_format?: string;
  age_group?: string | null;
  gender_category?: string | null;
  season_label?: string | null;
}

export interface TeamMemberAdd {
  person_id: UUID;
  role?: string;
  status?: string;
  primary_position?: string | null;
  jersey_number?: string | null;
  is_captain?: boolean;
}

export interface TeamRosterEntry {
  id: UUID;
  team_id: UUID;
  athlete_profile_id: UUID;
  role: string;
  primary_position: string | null;
  jersey_number: string | null;
  is_captain: boolean;
  status: string;
}

export interface EventCreate {
  organization_id: UUID;
  team_id?: UUID | null;
  event_type: string;
  title: string;
  starts_at: ISODateTime;
  ends_at?: ISODateTime | null;
  timezone?: string | null;
  venue_name?: string | null;
  notes?: string | null;
}

export type AttendanceStatus =
  | "invited"
  | "confirmed"
  | "declined"
  | "present"
  | "absent"
  | "late"
  | "excused";

export interface AttendanceRecordUpsert {
  person_id: UUID;
  status: AttendanceStatus;
  note?: string | null;
}

export interface AttendanceRecord {
  id: UUID;
  event_id: UUID;
  person_id: UUID;
  status: AttendanceStatus;
  recorded_by_person_id: UUID | null;
  guardian_consent_id: UUID | null;
  note: string | null;
  clearance_status: string | null;
  medical_clearance_status: string | null;
  medical_clearance_id: UUID | null;
  medical_clearance_reason: string | null;
  attendance_policy_code: string | null;
  attendance_policy_decision: string | null;
  attendance_policy_warnings: string[];
}

export type CommunicationMessageType =
  | "announcement"
  | "reminder"
  | "alert"
  | "request"
  | "report";

export type CommunicationChannel =
  | "email"
  | "sms"
  | "whatsapp"
  | "telegram"
  | "push"
  | "in_app";

export type CommunicationScopeType = "organization" | "team" | "event" | "person";

export type MessageDeliveryStatus =
  | "queued"
  | "sent"
  | "delivered"
  | "read"
  | "failed"
  | "suppressed";

export interface CommunicationTemplateCreate {
  organization_id: UUID;
  name: string;
  message_type: CommunicationMessageType;
  channel?: CommunicationChannel;
  subject_template: string;
  body_template: string;
  variables?: string | null;
}

export interface CommunicationTemplate {
  id: UUID;
  organization_id: UUID;
  name: string;
  message_type: CommunicationMessageType;
  channel: CommunicationChannel;
  subject_template: string;
  body_template: string;
  variables: string | null;
  status: string;
}

export interface CommunicationMessageCreate {
  organization_id: UUID;
  template_id?: UUID | null;
  message_type: CommunicationMessageType;
  channel?: CommunicationChannel;
  scope_type: CommunicationScopeType;
  scope_id: UUID;
  recipient_person_ids?: UUID[];
  subject: string;
  body: string;
  urgent?: boolean;
  quiet_hours_override?: boolean;
  scheduled_for?: ISODateTime | null;
  copy_guardians_for_minors?: boolean;
}

export interface CommunicationMessage {
  id: UUID;
  organization_id: UUID;
  template_id: UUID | null;
  created_by_person_id: UUID | null;
  message_type: CommunicationMessageType;
  channel: CommunicationChannel;
  scope_type: CommunicationScopeType;
  scope_id: UUID;
  subject: string;
  body: string;
  urgent: boolean;
  quiet_hours_override: boolean;
  scheduled_for: ISODateTime | null;
  sent_at: ISODateTime | null;
  status: string;
  recipient_count: number;
  escalates_message_id: UUID | null;
  escalation_level: number;
  escalation_triggered_at: ISODateTime | null;
  escalation_reason: string | null;
}

export interface MessageRecipient {
  id: UUID;
  message_id: UUID;
  person_id: UUID;
  person_name: string;
  destination: string | null;
  delivery_status: MessageDeliveryStatus;
  delivered_at: ISODateTime | null;
  read_at: ISODateTime | null;
  failure_reason: string | null;
}

export interface CommunicationDispatchSummary {
  message_id: UUID;
  attempted: number;
  sent: number;
  delivered: number;
  failed: number;
  suppressed: number;
  queued: number;
  transport_mode: string;
}

export type BillingMoney = string;
export type BillingCycle = "monthly" | "quarterly" | "annual";
export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "paused"
  | "cancelled";
export type BillingInvoiceStatus = "draft" | "open" | "paid" | "partial" | "void" | "uncollectible";
export type UsageUnit = "athlete" | "team" | "agent_task" | "report" | "storage_gb" | "message";

export interface BillingPlan {
  id: UUID;
  code: string;
  name: string;
  description: string | null;
  base_price: BillingMoney;
  currency: string;
  billing_cycle: BillingCycle;
  included_athletes: number;
  included_teams: number;
  included_agent_tasks: number;
  included_storage_gb: number;
  per_athlete_price: BillingMoney;
  per_agent_task_price: BillingMoney;
  features: string | null;
  status: string;
}

export interface BillingSubscription {
  id: UUID;
  organization_id: UUID;
  billing_plan_id: UUID;
  billing_cycle: BillingCycle;
  current_period_start: ISODate;
  current_period_end: ISODate;
  trial_ends_on: ISODate | null;
  next_billing_on: ISODate | null;
  seats_purchased: number;
  negotiated_price: BillingMoney | null;
  discount_code: string | null;
  external_customer_id: string | null;
  external_subscription_id: string | null;
  notes: string | null;
  status: SubscriptionStatus;
  cancel_at_period_end: boolean;
}

export interface BillingUsageMeter {
  id: UUID;
  code: string;
  name: string;
  unit: UsageUnit;
  included_quantity: number;
  overage_price: BillingMoney;
  aggregation: string;
  status: string;
}

export interface BillingUsageRecordCreate {
  organization_id: UUID;
  subscription_id: UUID;
  usage_meter_id: UUID;
  quantity: number;
  source?: string;
  external_reference?: string | null;
  notes?: string | null;
}

export interface BillingUsageRecord extends BillingUsageRecordCreate {
  id: UUID;
  recorded_at: ISODateTime;
}

export interface BillingInvoice {
  id: UUID;
  organization_id: UUID;
  subscription_id: UUID;
  invoice_number: string;
  period_start: ISODate;
  period_end: ISODate;
  subtotal: BillingMoney;
  tax_amount: BillingMoney;
  discount_amount: BillingMoney;
  total: BillingMoney;
  amount_paid: BillingMoney;
  currency: string;
  due_on: ISODate | null;
  status: BillingInvoiceStatus;
  line_items: string | null;
  external_invoice_id: string | null;
  dunning_count: number;
  dunning_last_sent_at: ISODateTime | null;
  dunning_last_severity: string | null;
  late_fee_total: BillingMoney;
  late_fee_count: number;
  late_fee_last_applied_on: ISODate | null;
  payment_retry_count: number;
  payment_retry_last_attempted_at: ISODateTime | null;
  payment_retry_next_attempt_at: ISODateTime | null;
  payment_retry_last_status: string | null;
  payment_retry_last_failure_reason: string | null;
  payment_retry_last_provider_reference: string | null;
}

export interface BillingEntitlement {
  id: UUID;
  organization_id: UUID;
  subscription_id: UUID;
  feature_key: string;
  limit_value: number | null;
  used_value: number;
  status: string;
  source: string;
}

export interface BillingSummary {
  organization_id: UUID;
  active_subscriptions: number;
  plans: number;
  usage_meters: number;
  usage_records: number;
  open_invoices: number;
  monthly_recurring_revenue: BillingMoney;
  invoice_outstanding: BillingMoney;
  entitlements: number;
}

export interface Agent {
  id: UUID;
  organization_id: UUID | null;
  name: string;
  kind: string;
  purpose: string;
  status: string;
  model_policy: string | null;
}

export interface AgentTaskCreate {
  organization_id: UUID;
  task_type: string;
  title: string;
  input_ref?: string | null;
}

export interface AgentTask {
  id: UUID;
  agent_id: UUID;
  organization_id: UUID;
  task_type: string;
  title: string;
  status: string;
  requested_by_person_id: UUID | null;
  input_ref: string | null;
  output_ref: string | null;
  review_notes: string | null;
  review_assigned_to_person_id: UUID | null;
  review_due_at: ISODateTime | null;
  review_priority: string;
  review_assignment_notes: string | null;
  approval_required_count: number;
  approval_approved_count: number;
  approval_rejected_count: number;
  approval_pending_count: number;
  approval_status: string;
  approval_last_decided_at: ISODateTime | null;
  governance_policy_rule_id: UUID | null;
  governance_policy_code: string | null;
  governance_policy_decision: string | null;
  governance_policy_risk_level: string | null;
  governance_policy_rationale: string | null;
}

export interface TrainingDrill {
  id: UUID;
  organization_id: UUID;
  sport: string;
  name: string;
  focus_area: string;
  category: string;
  min_age: number | null;
  max_age: number | null;
  equipment: string | null;
  description: string | null;
  coaching_points: string | null;
  default_duration_minutes: number | null;
  default_intensity: number | null;
  status: string;
}

export interface TrainingDrillCreate {
  organization_id: UUID;
  sport: string;
  name: string;
  focus_area: string;
  category: string;
  min_age?: number | null;
  max_age?: number | null;
  equipment?: string | null;
  description?: string | null;
  coaching_points?: string | null;
  default_duration_minutes?: number | null;
  default_intensity?: number | null;
  status?: string;
}

export interface TrainingPlan {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  athlete_profile_id: UUID | null;
  created_by_person_id: UUID | null;
  title: string;
  focus_area: string;
  period_start: ISODate;
  period_end: ISODate;
  status: string;
  ai_generated: boolean;
  source_summary: string | null;
  load_guidance: string | null;
  recovery_protocol: string | null;
  progress_checkpoints: string | null;
}

export interface TrainingPlanCreate {
  organization_id: UUID;
  team_id?: UUID | null;
  athlete_profile_id?: UUID | null;
  title: string;
  focus_area: string;
  period_start: ISODate;
  period_end: ISODate;
  ai_generated?: boolean;
  source_summary?: string | null;
  load_guidance?: string | null;
  recovery_protocol?: string | null;
  progress_checkpoints?: string | null;
}

export interface TrainingPlanItem {
  id: UUID;
  plan_id: UUID;
  drill_id: UUID | null;
  sequence: number;
  day_label: string;
  title: string;
  focus_area: string;
  duration_minutes: number;
  intensity: number;
  notes: string | null;
}

export interface TrainingPlanItemCreate {
  drill_id?: UUID | null;
  sequence?: number;
  day_label: string;
  title: string;
  focus_area: string;
  duration_minutes: number;
  intensity: number;
  notes?: string | null;
}

export interface TrainingSession {
  id: UUID;
  organization_id: UUID;
  team_id: UUID;
  plan_id: UUID | null;
  event_id: UUID | null;
  title: string;
  scheduled_for: ISODateTime;
  duration_minutes: number;
  rpe_target: number;
  load_score: number;
  objectives: string | null;
  status: string;
}

export interface TrainingSessionCreate {
  organization_id: UUID;
  team_id: UUID;
  plan_id?: UUID | null;
  event_id?: UUID | null;
  title: string;
  scheduled_for: ISODateTime;
  duration_minutes: number;
  rpe_target: number;
  objectives?: string | null;
}

export interface TrainingSessionFeedback {
  id: UUID;
  organization_id: UUID;
  session_plan_id: UUID;
  athlete_profile_id: UUID | null;
  recorded_by_person_id: UUID | null;
  readiness_score: number;
  soreness_score: number;
  sleep_quality: number;
  mood_score: number;
  actual_rpe: number | null;
  actual_duration_minutes: number | null;
  completed: boolean;
  feedback: string | null;
  coach_notes: string | null;
  recorded_at: ISODateTime;
  readiness_band: string;
  load_delta: number | null;
  recommendation: string;
}

export interface TrainingSessionFeedbackCreate {
  athlete_profile_id?: UUID | null;
  readiness_score: number;
  soreness_score?: number;
  sleep_quality?: number;
  mood_score?: number;
  actual_rpe?: number | null;
  actual_duration_minutes?: number | null;
  completed?: boolean;
  feedback?: string | null;
  coach_notes?: string | null;
}

export interface TrainingAvailabilityCreate {
  organization_id: UUID;
  team_id: UUID;
  starts_at: ISODateTime;
  days?: number;
  duration_minutes?: number;
  earliest_hour?: number;
  latest_hour?: number;
}

export interface TrainingAvailabilitySlot {
  starts_at: ISODateTime;
  ends_at: ISODateTime;
  conflict_count: number;
  conflicts: string[];
  score: number;
  recommendation: string;
}

export interface TrainingAvailability {
  organization_id: UUID;
  team_id: UUID;
  duration_minutes: number;
  slots: TrainingAvailabilitySlot[];
}

export interface TrainingCalendarArtifact {
  organization_id: UUID;
  team_id: UUID | null;
  generated_at: ISODateTime;
  starts_at: ISODateTime;
  ends_at: ISODateTime;
  session_count: number;
  content_type: string;
  download_filename: string;
  content: string;
  checksum: string;
  size_bytes: number;
}

export interface PerformanceMetricDefinition {
  id: UUID;
  organization_id: UUID;
  sport: string | null;
  code: string;
  name: string;
  category: string;
  unit: string | null;
  description: string | null;
  min_value: number | null;
  max_value: number | null;
  weight: number;
  higher_is_better: boolean;
  status: string;
}

export interface PerformanceObservationCreate {
  organization_id: UUID;
  metric_definition_id: UUID;
  event_id?: UUID | null;
  value: number;
  raw_value?: string | null;
  observed_at?: ISODateTime | null;
  source?: string;
  confidence?: number | null;
  verification_status?: string;
  notes?: string | null;
}

export interface PerformanceObservation {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  metric_definition_id: UUID;
  event_id: UUID | null;
  recorded_by_person_id: UUID | null;
  value: number;
  raw_value: string | null;
  observed_at: ISODateTime;
  source: string;
  confidence: number | null;
  verification_status: string;
  notes: string | null;
}

interface QueryValue {
  toString(): string;
}

type QueryParams = Record<string, QueryValue | null | undefined>;

export class AfroLeteClient {
  readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly fetcher: typeof fetch;

  readonly organization = {
    get: (params: { organizationId: UUID }): Promise<Organization> =>
      this.request<Organization>("/organization", {
        query: { organization_id: params.organizationId },
      }),
  };

  readonly people = {
    create: (payload: PersonCreate): Promise<Person> =>
      this.request<Person>("/people", {
        method: "POST",
        body: payload,
      }),
    linkGuardian: (
      athletePersonId: UUID,
      payload: GuardianLinkCreate,
    ): Promise<GuardianRelationship> =>
      this.request<GuardianRelationship>(`/people/${athletePersonId}/guardians`, {
        method: "POST",
        body: payload,
      }),
    createConsentRequest: (
      athletePersonId: UUID,
      payload: ConsentRequestCreate,
    ): Promise<ConsentRequest> =>
      this.request<ConsentRequest>(`/people/${athletePersonId}/consent-requests`, {
        method: "POST",
        body: payload,
      }),
  };

  readonly events = {
    list: (params: { organizationId: UUID; teamId?: UUID | null }): Promise<Event[]> =>
      this.request<Event[]>("/events", {
        query: { organization_id: params.organizationId, team_id: params.teamId },
      }),
    create: (payload: EventCreate): Promise<Event> =>
      this.request<Event>("/events", {
        method: "POST",
        body: payload,
      }),
    attendance: {
      list: (eventId: UUID, params: { organizationId: UUID }): Promise<AttendanceRecord[]> =>
        this.request<AttendanceRecord[]>(`/events/${eventId}/attendance`, {
          query: { organization_id: params.organizationId },
        }),
      record: (
        eventId: UUID,
        params: { organizationId: UUID },
        payload: AttendanceRecordUpsert,
      ): Promise<AttendanceRecord> =>
        this.request<AttendanceRecord>(`/events/${eventId}/attendance`, {
          method: "POST",
          query: { organization_id: params.organizationId },
          body: payload,
        }),
    },
  };

  readonly agents = {
    list: (params: { organizationId: UUID }): Promise<Agent[]> =>
      this.request<Agent[]>("/agents", {
        query: { organization_id: params.organizationId },
      }),
    tasks: {
      list: (params: { organizationId: UUID; agentId?: UUID | null }): Promise<AgentTask[]> =>
        this.request<AgentTask[]>("/agents/tasks", {
          query: { organization_id: params.organizationId, agent_id: params.agentId },
        }),
      queue: (agentId: UUID, payload: AgentTaskCreate): Promise<AgentTask> =>
        this.request<AgentTask>(`/agents/${agentId}/tasks`, {
          method: "POST",
          body: payload,
        }),
    },
  };

  readonly communications = {
    templates: {
      list: (params: { organizationId: UUID }): Promise<CommunicationTemplate[]> =>
        this.request<CommunicationTemplate[]>("/communications/templates", {
          query: { organization_id: params.organizationId },
        }),
      create: (payload: CommunicationTemplateCreate): Promise<CommunicationTemplate> =>
        this.request<CommunicationTemplate>("/communications/templates", {
          method: "POST",
          body: payload,
        }),
    },
    messages: {
      list: (params: { organizationId: UUID }): Promise<CommunicationMessage[]> =>
        this.request<CommunicationMessage[]>("/communications/messages", {
          query: { organization_id: params.organizationId },
        }),
      create: (payload: CommunicationMessageCreate): Promise<CommunicationMessage> =>
        this.request<CommunicationMessage>("/communications/messages", {
          method: "POST",
          body: payload,
        }),
      recipients: (
        messageId: UUID,
        params: { organizationId: UUID },
      ): Promise<MessageRecipient[]> =>
        this.request<MessageRecipient[]>(`/communications/messages/${messageId}/recipients`, {
          query: { organization_id: params.organizationId },
        }),
      dispatch: (
        messageId: UUID,
        params: { organizationId: UUID },
      ): Promise<CommunicationDispatchSummary> =>
        this.request<CommunicationDispatchSummary>(`/communications/messages/${messageId}/dispatch`, {
          method: "POST",
          query: { organization_id: params.organizationId },
        }),
    },
  };

  readonly billing = {
    plans: {
      list: (): Promise<BillingPlan[]> =>
        this.request<BillingPlan[]>("/billing/plans"),
    },
    subscriptions: {
      list: (params: { organizationId: UUID }): Promise<BillingSubscription[]> =>
        this.request<BillingSubscription[]>("/billing/subscriptions", {
          query: { organization_id: params.organizationId },
        }),
    },
    meters: {
      list: (): Promise<BillingUsageMeter[]> =>
        this.request<BillingUsageMeter[]>("/billing/meters"),
    },
    usage: {
      list: (params: { organizationId: UUID }): Promise<BillingUsageRecord[]> =>
        this.request<BillingUsageRecord[]>("/billing/usage", {
          query: { organization_id: params.organizationId },
        }),
      record: (payload: BillingUsageRecordCreate): Promise<BillingUsageRecord> =>
        this.request<BillingUsageRecord>("/billing/usage", {
          method: "POST",
          body: payload,
        }),
    },
    invoices: {
      list: (params: { organizationId: UUID }): Promise<BillingInvoice[]> =>
        this.request<BillingInvoice[]>("/billing/invoices", {
          query: { organization_id: params.organizationId },
        }),
    },
    entitlements: {
      list: (params: { organizationId: UUID }): Promise<BillingEntitlement[]> =>
        this.request<BillingEntitlement[]>("/billing/entitlements", {
          query: { organization_id: params.organizationId },
        }),
    },
    summary: {
      get: (params: { organizationId: UUID }): Promise<BillingSummary> =>
        this.request<BillingSummary>("/billing/summary", {
          query: { organization_id: params.organizationId },
        }),
    },
  };

  readonly teams = {
    list: (params: { organizationId: UUID }): Promise<Team[]> =>
      this.request<Team[]>("/teams", {
        query: { organization_id: params.organizationId },
      }),
    create: (payload: TeamCreate): Promise<Team> =>
      this.request<Team>("/teams", {
        method: "POST",
        body: payload,
      }),
    addMember: (teamId: UUID, payload: TeamMemberAdd): Promise<TeamRosterEntry> =>
      this.request<TeamRosterEntry>(`/teams/${teamId}/members`, {
        method: "POST",
        body: payload,
      }),
  };

  readonly training = {
    drills: {
      list: (params: { organizationId: UUID; sport?: string | null }): Promise<TrainingDrill[]> =>
        this.request<TrainingDrill[]>("/training/drills", {
          query: { organization_id: params.organizationId, sport: params.sport },
        }),
      create: (payload: TrainingDrillCreate): Promise<TrainingDrill> =>
        this.request<TrainingDrill>("/training/drills", {
          method: "POST",
          body: payload,
        }),
    },
    plans: {
      list: (params: {
        organizationId: UUID;
        teamId?: UUID | null;
        athleteProfileId?: UUID | null;
      }): Promise<TrainingPlan[]> =>
        this.request<TrainingPlan[]>("/training/plans", {
          query: {
            organization_id: params.organizationId,
            team_id: params.teamId,
            athlete_profile_id: params.athleteProfileId,
          },
        }),
      create: (payload: TrainingPlanCreate): Promise<TrainingPlan> =>
        this.request<TrainingPlan>("/training/plans", {
          method: "POST",
          body: payload,
        }),
      items: {
        list: (planId: UUID, params: { organizationId: UUID }): Promise<TrainingPlanItem[]> =>
          this.request<TrainingPlanItem[]>(`/training/plans/${planId}/items`, {
            query: { organization_id: params.organizationId },
          }),
        add: (
          planId: UUID,
          params: { organizationId: UUID },
          payload: TrainingPlanItemCreate,
        ): Promise<TrainingPlanItem> =>
          this.request<TrainingPlanItem>(`/training/plans/${planId}/items`, {
            method: "POST",
            query: { organization_id: params.organizationId },
            body: payload,
          }),
      },
    },
    sessions: {
      list: (params: { organizationId: UUID; teamId?: UUID | null }): Promise<TrainingSession[]> =>
        this.request<TrainingSession[]>("/training/sessions", {
          query: { organization_id: params.organizationId, team_id: params.teamId },
        }),
      create: (payload: TrainingSessionCreate): Promise<TrainingSession> =>
        this.request<TrainingSession>("/training/sessions", {
          method: "POST",
          body: payload,
        }),
      feedback: {
        list: (
          sessionPlanId: UUID,
          params: { organizationId: UUID },
        ): Promise<TrainingSessionFeedback[]> =>
          this.request<TrainingSessionFeedback[]>(`/training/sessions/${sessionPlanId}/feedback`, {
            query: { organization_id: params.organizationId },
          }),
        record: (
          sessionPlanId: UUID,
          params: { organizationId: UUID },
          payload: TrainingSessionFeedbackCreate,
        ): Promise<TrainingSessionFeedback> =>
          this.request<TrainingSessionFeedback>(`/training/sessions/${sessionPlanId}/feedback`, {
            method: "POST",
            query: { organization_id: params.organizationId },
            body: payload,
          }),
      },
    },
    availability: {
      suggest: (payload: TrainingAvailabilityCreate): Promise<TrainingAvailability> =>
        this.request<TrainingAvailability>("/training/availability", {
          method: "POST",
          body: payload,
        }),
    },
    calendar: {
      export: (params: {
        organizationId: UUID;
        teamId?: UUID | null;
        startsAt?: ISODateTime | null;
        endsAt?: ISODateTime | null;
      }): Promise<TrainingCalendarArtifact> =>
        this.request<TrainingCalendarArtifact>("/training/calendar-artifact", {
          query: {
            organization_id: params.organizationId,
            team_id: params.teamId,
            starts_at: params.startsAt,
            ends_at: params.endsAt,
          },
        }),
    },
  };

  readonly performance = {
    metrics: {
      list: (params: { organizationId: UUID; sport?: string | null }): Promise<PerformanceMetricDefinition[]> =>
        this.request<PerformanceMetricDefinition[]>("/performance/metrics", {
          query: { organization_id: params.organizationId, sport: params.sport },
        }),
    },
    observations: {
      list: (
        athleteProfileId: UUID,
        params: { organizationId: UUID },
      ): Promise<PerformanceObservation[]> =>
        this.request<PerformanceObservation[]>(`/performance/athletes/${athleteProfileId}/observations`, {
          query: { organization_id: params.organizationId },
        }),
      create: (
        athleteProfileId: UUID,
        payload: PerformanceObservationCreate,
      ): Promise<PerformanceObservation> =>
        this.request<PerformanceObservation>(`/performance/athletes/${athleteProfileId}/observations`, {
          method: "POST",
          body: payload,
        }),
    },
  };

  constructor(options: AfroLeteClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.apiKey = options.apiKey;
    this.fetcher = options.fetch ?? fetch;
  }

  me(): Promise<DeveloperApiKeyInspection> {
    return this.request<DeveloperApiKeyInspection>("/me");
  }

  private async request<T>(
    path: string,
    options: {
      method?: "GET" | "POST";
      query?: QueryParams;
      body?: unknown;
    } = {},
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}/api/v1/sdk${path}`);
    for (const [key, value] of Object.entries(options.query ?? {})) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, value.toString());
      }
    }

    const headers: HeadersInit = {
      Accept: "application/json",
      "X-Afrolete-API-Key": this.apiKey,
    };
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
    }

    const requestInit: RequestInit = {
      method: options.method ?? "GET",
      headers,
    };
    if (options.body !== undefined) {
      requestInit.body = JSON.stringify(options.body);
    }

    const response = await this.fetcher(url, requestInit);
    const body = await parseJsonResponse(response);
    if (!response.ok) {
      throw new AfroLeteRequestError({
        status: response.status,
        statusText: response.statusText,
        body,
      });
    }
    return body as T;
  }
}

async function parseJsonResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text.length === 0) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}
