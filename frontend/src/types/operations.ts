export type UUID = string;

export type OrganizationType =
  | "club"
  | "school"
  | "academy"
  | "association"
  | "federation"
  | "event_operator";

export type MembershipRole =
  | "owner"
  | "admin"
  | "coach"
  | "staff"
  | "athlete"
  | "guardian"
  | "viewer"
  | "agent";

export type SportFormat = "team" | "individual" | "mixed";
export type TeamRole =
  | "player"
  | "captain"
  | "vice_captain"
  | "coach"
  | "assistant_coach"
  | "manager"
  | "medic"
  | "analyst"
  | "substitute"
  | "reserve"
  | "bench"
  | "individual_athlete";

export type RosterStatus =
  | "active"
  | "starter"
  | "bench"
  | "substitute"
  | "reserve"
  | "injured"
  | "suspended"
  | "inactive";

export type EventType =
  | "training"
  | "match"
  | "meeting"
  | "tournament"
  | "assessment"
  | "community";

export type AttendanceStatus =
  | "invited"
  | "confirmed"
  | "declined"
  | "present"
  | "absent"
  | "late"
  | "excused";

export type ConsentScopeType = "organization" | "team" | "event";
export type ConsentCaptureChannel = "web_link" | "sms" | "whatsapp" | "telegram" | "email" | "manual";
export type ConsentStatus = "pending" | "granted" | "denied" | "revoked" | "expired";
export type ParticipationClearanceStatus =
  | "cleared"
  | "minor_requires_consent"
  | "consent_denied"
  | "consent_expired"
  | "no_guardian";

export type AgentKind =
  | "coaching"
  | "operations"
  | "safeguarding"
  | "analytics"
  | "communications"
  | "scouting";

export type AgentTaskStatus =
  | "queued"
  | "running"
  | "waiting_for_review"
  | "completed"
  | "failed"
  | "cancelled";

export type MetricCategory =
  | "physical"
  | "technical"
  | "tactical"
  | "mental"
  | "wellness"
  | "competition";

export type MetricSource =
  | "manual"
  | "coach_evaluation"
  | "self_assessment"
  | "official_stats"
  | "video_analysis"
  | "audio_narration"
  | "wearable"
  | "agent_extracted";

export type MetricVerificationStatus = "pending_review" | "verified" | "rejected";
export type TrainingPlanStatus = "draft" | "active" | "completed" | "archived";
export type TrainingSessionStatus = "planned" | "in_progress" | "completed" | "cancelled";
export type CompetitionType = "league" | "tournament" | "cup" | "friendly_series";
export type CompetitionFormat =
  | "round_robin"
  | "single_elimination"
  | "double_elimination"
  | "group_knockout"
  | "swiss"
  | "friendly";
export type CompetitionStatus = "draft" | "scheduled" | "active" | "completed" | "cancelled";
export type FixtureStatus = "draft" | "scheduled" | "live" | "final" | "postponed" | "cancelled";
export type OfficialRole =
  | "referee"
  | "assistant_referee"
  | "fourth_official"
  | "scorer"
  | "timekeeper"
  | "match_commissioner";
export type OfficialAssignmentStatus = "proposed" | "accepted" | "declined" | "confirmed";
export type MatchEventType =
  | "goal"
  | "own_goal"
  | "assist"
  | "yellow_card"
  | "red_card"
  | "substitution"
  | "injury"
  | "note";
export type CommunicationMessageType = "announcement" | "alert" | "reminder" | "request" | "report";
export type CommunicationChannel = "in_app" | "push" | "email" | "sms" | "whatsapp" | "telegram";
export type CommunicationScopeType = "organization" | "team" | "event" | "person";
export type MessageDeliveryStatus = "queued" | "sent" | "delivered" | "read" | "failed" | "suppressed";
export type NotificationFrequency = "immediate" | "daily_digest" | "weekly_digest";
export type ChannelPreference = "app" | "email" | "sms" | "all";
export type FacilityType = "field" | "court" | "stadium" | "gym" | "pool" | "clubhouse" | "storage" | "other";
export type FacilityStatus = "available" | "booked" | "maintenance" | "closed" | "retired";
export type AssetCondition = "new" | "good" | "fair" | "poor" | "unusable";
export type EquipmentStatus = "available" | "checked_out" | "maintenance" | "lost" | "retired";
export type CheckoutStatus = "checked_out" | "returned" | "overdue" | "lost" | "damaged";
export type WorkOrderPriority = "low" | "medium" | "high" | "critical";
export type WorkOrderStatus = "open" | "assigned" | "in_progress" | "completed" | "cancelled";
export type FacilityBookingStatus =
  | "requested"
  | "approved"
  | "confirmed"
  | "checked_in"
  | "completed"
  | "cancelled";
export type CommercialStatus =
  | "draft"
  | "active"
  | "pledged"
  | "paid"
  | "partial"
  | "overdue"
  | "completed"
  | "cancelled";
export type TicketStatus = "issued" | "checked_in" | "void" | "refunded";
export type ReportCategory =
  | "performance"
  | "administrative"
  | "operational"
  | "financial"
  | "compliance"
  | "intelligence";
export type ReportFormat = "online" | "pdf" | "excel" | "csv" | "api";
export type ReportFrequency = "on_demand" | "daily" | "weekly" | "monthly" | "quarterly" | "on_trigger";
export type ReportRunStatus = "queued" | "running" | "ready" | "failed";
export type InsightSeverity = "info" | "watch" | "warning" | "critical";
export type InsightStatus = "new" | "acknowledged" | "actioned" | "dismissed";

export type LocalIdentity = {
  sub: string;
  email: string;
  name: string;
};

export type OrganizationRead = {
  id: UUID;
  name: string;
  slug: string;
  organization_type: OrganizationType;
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
  my_roles: MembershipRole[];
};

export type MembershipRead = {
  id: UUID;
  organization_id: UUID;
  subject_type: "person" | "organization" | "team";
  subject_id: UUID;
  role: MembershipRole;
  title: string | null;
  status: string;
};

export type TeamRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  sport: string;
  sport_format: SportFormat;
  age_group: string | null;
  gender_category: string | null;
  season_label: string | null;
};

export type TeamRosterEntryRead = {
  id: UUID;
  team_id: UUID;
  athlete_profile_id: UUID;
  role: TeamRole;
  primary_position: string | null;
  jersey_number: string | null;
  is_captain: boolean;
  status: RosterStatus;
};

export type EventRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  event_type: EventType;
  title: string;
  starts_at: string;
  ends_at: string | null;
  timezone: string;
  venue_name: string | null;
  notes: string | null;
};

export type AttendanceRecordRead = {
  id: UUID;
  event_id: UUID;
  person_id: UUID;
  status: AttendanceStatus;
  recorded_by_person_id: UUID | null;
  guardian_consent_id: UUID | null;
  note: string | null;
  clearance_status: ParticipationClearanceStatus | null;
};

export type AttendanceSeedRead = {
  event_id: UUID;
  created: number;
  existing: number;
};

export type GuardianRelationshipRead = {
  id: UUID;
  athlete_person_id: UUID;
  guardian_person_id: UUID;
  relationship_kind: string;
  relationship: string;
  can_sign_consent: boolean;
  can_view_medical: boolean;
  emergency_contact: boolean;
  can_pick_up: boolean;
  is_primary: boolean;
  notes: string | null;
};

export type ConsentRequestRead = {
  id: UUID;
  organization_id: UUID;
  athlete_person_id: UUID;
  guardian_person_id: UUID;
  scope_type: ConsentScopeType;
  scope_id: UUID | null;
  channel: ConsentCaptureChannel;
  destination: string;
  status: string;
  expires_at: string | null;
  sent_at: string | null;
  fulfilled_at: string | null;
  external_message_id: string | null;
  one_time_token: string | null;
};

export type FacilityRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  facility_type: FacilityType;
  status: FacilityStatus;
  sport: string | null;
  surface: string | null;
  capacity: number | null;
  location: string | null;
  dimensions: string | null;
  amenities: string | null;
  hourly_rate: string | null;
  maintenance_budget: string | null;
  condition: AssetCondition;
  insurance_policy_ref: string | null;
  last_inspection_on: string | null;
  notes: string | null;
};

export type EquipmentItemRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID | null;
  team_id: UUID | null;
  name: string;
  category: string;
  subcategory: string | null;
  brand: string | null;
  model: string | null;
  tag_code: string | null;
  serial_number: string | null;
  quantity_total: number;
  quantity_available: number;
  condition: AssetCondition;
  status: EquipmentStatus;
  storage_location: string | null;
  min_stock_level: number;
  reorder_point: number;
  unit_value: string | null;
  depreciation_rate: string | null;
  warranty_expires_on: string | null;
  last_audit_on: string | null;
  photo_url: string | null;
  notes: string | null;
};

export type EquipmentCheckoutRead = {
  id: UUID;
  organization_id: UUID;
  equipment_item_id: UUID;
  team_id: UUID | null;
  event_id: UUID | null;
  borrower_person_id: UUID | null;
  checked_out_by_person_id: UUID | null;
  returned_by_person_id: UUID | null;
  quantity: number;
  purpose: string;
  checked_out_at: string;
  due_at: string;
  returned_at: string | null;
  status: CheckoutStatus;
  condition_out: AssetCondition;
  condition_in: AssetCondition | null;
  condition_notes: string | null;
  damage_report: string | null;
  late_fee: string | null;
};

export type MaintenanceWorkOrderRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID | null;
  equipment_item_id: UUID | null;
  assigned_to_person_id: UUID | null;
  title: string;
  priority: WorkOrderPriority;
  status: WorkOrderStatus;
  due_at: string | null;
  completed_at: string | null;
  vendor: string | null;
  estimated_cost: string | null;
  actual_cost: string | null;
  safety_related: boolean;
  compliance_reference: string | null;
  notes: string | null;
};

export type FacilityBookingRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  team_id: UUID | null;
  event_id: UUID | null;
  requested_by_person_id: UUID | null;
  title: string;
  starts_at: string;
  ends_at: string;
  status: FacilityBookingStatus;
  requester_name: string | null;
  requester_email: string | null;
  expected_attendees: number | null;
  rate: string | null;
  deposit_required: string | null;
  insurance_certificate_ref: string | null;
  special_requirements: string | null;
  access_code: string | null;
};

export type AssetSummaryRead = {
  organization_id: UUID;
  facilities: number;
  equipment_items: number;
  stock_alerts: number;
  open_checkouts: number;
  overdue_checkouts: number;
  open_work_orders: number;
  safety_work_orders: number;
  upcoming_bookings: number;
  booked_hours: number;
  projected_booking_revenue: string;
};

export type SponsorRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  industry: string | null;
  contact_name: string | null;
  contact_email: string | null;
  website_url: string | null;
  brand_assets_url: string | null;
  notes: string | null;
};

export type SponsorshipAgreementRead = {
  id: UUID;
  organization_id: UUID;
  sponsor_id: UUID;
  event_id: UUID | null;
  name: string;
  tier: string;
  value_amount: string;
  currency: string;
  starts_on: string | null;
  ends_on: string | null;
  deliverables: string | null;
  activation_notes: string | null;
  roi_notes: string | null;
  status: CommercialStatus;
};

export type FundraisingCampaignRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  name: string;
  purpose: string;
  goal_amount: string;
  raised_amount: string;
  currency: string;
  starts_on: string | null;
  ends_on: string | null;
  public_url: string | null;
  status: CommercialStatus;
};

export type DonationRead = {
  id: UUID;
  organization_id: UUID;
  campaign_id: UUID;
  donor_name: string;
  donor_email: string | null;
  amount: string;
  currency: string;
  external_reference: string | null;
  message: string | null;
  status: CommercialStatus;
};

export type TicketProductRead = {
  id: UUID;
  organization_id: UUID;
  event_id: UUID;
  name: string;
  price: string;
  currency: string;
  capacity: number;
  sold_count: number;
  access_zone: string | null;
  status: CommercialStatus;
};

export type TicketOrderRead = {
  id: UUID;
  organization_id: UUID;
  ticket_product_id: UUID;
  buyer_name: string;
  buyer_email: string;
  quantity: number;
  total_amount: string;
  currency: string;
  external_payment_reference: string | null;
  status: CommercialStatus;
  ticket_ids: UUID[];
};

export type TicketRead = {
  id: UUID;
  organization_id: UUID;
  ticket_order_id: UUID;
  ticket_product_id: UUID;
  holder_name: string | null;
  qr_token: string;
  status: TicketStatus;
  checked_in_at: string | null;
  gate: string | null;
};

export type FinanceInvoiceRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID | null;
  team_id: UUID | null;
  sponsor_id: UUID | null;
  invoice_number: string;
  title: string;
  amount_due: string;
  amount_paid: string;
  currency: string;
  due_on: string | null;
  status: CommercialStatus;
  memo: string | null;
};

export type FinancePaymentRead = {
  id: UUID;
  organization_id: UUID;
  invoice_id: UUID;
  amount: string;
  currency: string;
  method: string;
  external_reference: string | null;
  received_at: string;
  notes: string | null;
};

export type CommercialSummaryRead = {
  organization_id: UUID;
  sponsorship_value: string;
  fundraising_goal: string;
  fundraising_raised: string;
  ticket_revenue: string;
  invoice_outstanding: string;
  active_sponsors: number;
  active_campaigns: number;
  tickets_sold: number;
  tickets_checked_in: number;
};

export type ReportDefinitionRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  category: ReportCategory;
  description: string | null;
  default_format: ReportFormat;
  parameter_schema: string | null;
  template: string | null;
  ai_assisted: boolean;
  status: string;
};

export type GeneratedReportRead = {
  id: UUID;
  organization_id: UUID;
  report_definition_id: UUID;
  requested_by_person_id: UUID | null;
  team_id: UUID | null;
  athlete_profile_id: UUID | null;
  competition_id: UUID | null;
  event_id: UUID | null;
  title: string;
  output_format: ReportFormat;
  status: ReportRunStatus;
  period_start: string | null;
  period_end: string | null;
  parameters: string | null;
  summary: string;
  findings: string | null;
  recommendations: string | null;
  artifact_url: string | null;
  shared_token: string | null;
  expires_at: string | null;
};

export type ScheduledReportRead = {
  id: UUID;
  organization_id: UUID;
  report_definition_id: UUID;
  name: string;
  frequency: ReportFrequency;
  delivery_channels: string;
  recipients: string | null;
  next_run_at: string | null;
  last_run_at: string | null;
  status: string;
};

export type IntelligenceInsightRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID | null;
  team_id: UUID | null;
  event_id: UUID | null;
  agent_id: UUID | null;
  title: string;
  insight_type: string;
  severity: InsightSeverity;
  status: InsightStatus;
  confidence: number;
  evidence: string | null;
  recommendation: string | null;
  model_name: string | null;
  reviewed_by_person_id: UUID | null;
};

export type PredictiveRiskScoreRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  model_name: string;
  score: number;
  risk_band: string;
  drivers: string | null;
  recommendation: string | null;
  valid_for_date: string;
};

export type ReportExportJobRead = {
  id: UUID;
  organization_id: UUID;
  generated_report_id: UUID;
  output_format: ReportFormat;
  destination: string;
  webhook_url: string | null;
  status: ReportRunStatus;
  completed_at: string | null;
};

export type ReportingSummaryRead = {
  organization_id: UUID;
  definitions: number;
  generated_reports: number;
  scheduled_reports: number;
  open_insights: number;
  critical_insights: number;
  high_risk_scores: number;
  export_jobs: number;
};

export type ActivityConsentRead = {
  id: UUID;
  organization_id: UUID;
  athlete_person_id: UUID;
  guardian_person_id: UUID;
  scope_type: ConsentScopeType;
  scope_id: UUID | null;
  status: ConsentStatus;
  source_request_id: UUID | null;
  capture_channel: ConsentCaptureChannel;
  valid_from: string | null;
  valid_until: string | null;
  signed_at: string | null;
  revoked_at: string | null;
  recorded_by_person_id: UUID | null;
  consent_text: string | null;
  notes: string | null;
};

export type ParticipationClearanceRead = {
  event_id: UUID;
  athlete_person_id: UUID;
  is_minor: boolean;
  guardian_required: boolean;
  status: ParticipationClearanceStatus;
  consent_id: UUID | null;
  reason: string;
};

export type AgentRead = {
  id: UUID;
  organization_id: UUID | null;
  name: string;
  kind: AgentKind;
  purpose: string;
  status: string;
  model_policy: string | null;
};

export type AgentAssignmentRead = {
  id: UUID;
  agent_id: UUID;
  organization_id: UUID;
  scope_type: string;
  scope_id: string;
  granted_by_person_id: UUID | null;
};

export type AgentTaskRead = {
  id: UUID;
  agent_id: UUID;
  organization_id: UUID;
  task_type: string;
  title: string;
  status: AgentTaskStatus;
  requested_by_person_id: UUID | null;
  input_ref: string | null;
  output_ref: string | null;
  review_notes: string | null;
};

export type MetricDefinitionRead = {
  id: UUID;
  organization_id: UUID;
  sport: string | null;
  code: string;
  name: string;
  category: MetricCategory;
  unit: string | null;
  description: string | null;
  min_value: number | null;
  max_value: number | null;
  weight: number;
  higher_is_better: boolean;
  status: string;
};

export type PerformanceObservationRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  metric_definition_id: UUID;
  event_id: UUID | null;
  recorded_by_person_id: UUID | null;
  value: number;
  raw_value: string | null;
  observed_at: string;
  source: MetricSource;
  confidence: number | null;
  verification_status: MetricVerificationStatus;
  notes: string | null;
};

export type AthleteAssessmentRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  event_id: UUID | null;
  assessed_by_person_id: UUID | null;
  assessed_at: string;
  physical_score: number;
  technical_score: number;
  tactical_score: number;
  mental_score: number;
  overall_score: number;
  summary: string | null;
  recommendations: string | null;
  verification_status: MetricVerificationStatus;
};

export type AthletePerformanceSummaryRead = {
  athlete_profile_id: UUID;
  latest_overall_score: number | null;
  observation_count: number;
  assessment_count: number;
  latest_assessment_id: UUID | null;
  rating: string | null;
};

export type TrainingDrillRead = {
  id: UUID;
  organization_id: UUID;
  sport: string | null;
  name: string;
  focus_area: string;
  category: string;
  min_age: number | null;
  max_age: number | null;
  equipment: string | null;
  description: string;
  coaching_points: string | null;
  default_duration_minutes: number;
  default_intensity: number;
  status: string;
};

export type TrainingPlanRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  athlete_profile_id: UUID | null;
  created_by_person_id: UUID | null;
  title: string;
  focus_area: string;
  period_start: string;
  period_end: string;
  status: TrainingPlanStatus;
  ai_generated: boolean;
  source_summary: string | null;
  load_guidance: string | null;
  recovery_protocol: string | null;
  progress_checkpoints: string | null;
};

export type TrainingPlanItemRead = {
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
};

export type TrainingSessionPlanRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID;
  plan_id: UUID | null;
  event_id: UUID | null;
  title: string;
  scheduled_for: string;
  duration_minutes: number;
  rpe_target: number;
  load_score: number;
  objectives: string | null;
  status: TrainingSessionStatus;
};

export type CompetitionRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  sport: string;
  competition_type: CompetitionType;
  format: CompetitionFormat;
  season_label: string | null;
  starts_on: string | null;
  ends_on: string | null;
  status: CompetitionStatus;
  points_for_win: number;
  points_for_draw: number;
  points_for_loss: number;
  tiebreakers: string | null;
  rules_summary: string | null;
};

export type CompetitionParticipantRead = {
  id: UUID;
  competition_id: UUID;
  team_id: UUID;
  team_name: string;
  seed: number | null;
  group_label: string | null;
  status: string;
};

export type CompetitionFixtureRead = {
  id: UUID;
  organization_id: UUID;
  competition_id: UUID;
  event_id: UUID | null;
  home_team_id: UUID;
  away_team_id: UUID;
  home_team_name: string;
  away_team_name: string;
  round_label: string | null;
  stage_label: string | null;
  scheduled_at: string;
  venue_name: string | null;
  status: FixtureStatus;
  home_score: number | null;
  away_score: number | null;
  result_confirmed_at: string | null;
  notes: string | null;
};

export type FixtureOfficialAssignmentRead = {
  id: UUID;
  fixture_id: UUID;
  person_id: UUID;
  role: OfficialRole;
  status: OfficialAssignmentStatus;
  certification_level: string | null;
  conflict_notes: string | null;
};

export type FixtureMatchEventRead = {
  id: UUID;
  fixture_id: UUID;
  team_id: UUID;
  athlete_profile_id: UUID | null;
  minute: number | null;
  event_type: MatchEventType;
  description: string | null;
};

export type CompetitionStandingRead = {
  competition_id: UUID;
  team_id: UUID;
  team_name: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
};

export type CommunicationTemplateRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  message_type: CommunicationMessageType;
  channel: CommunicationChannel;
  subject_template: string;
  body_template: string;
  variables: string | null;
  status: string;
};

export type CommunicationMessageRead = {
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
  scheduled_for: string | null;
  sent_at: string | null;
  status: string;
  recipient_count: number;
};

export type MessageRecipientRead = {
  id: UUID;
  message_id: UUID;
  person_id: UUID;
  person_name: string;
  destination: string | null;
  delivery_status: MessageDeliveryStatus;
  delivered_at: string | null;
  read_at: string | null;
  failure_reason: string | null;
};

export type NotificationPreferenceRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID;
  frequency: NotificationFrequency;
  channel_preference: ChannelPreference;
  language: string;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  emergency_override: boolean;
};
