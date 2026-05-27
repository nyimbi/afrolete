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

export type SafeguardingIncidentType =
  | "injury"
  | "medical"
  | "safeguarding"
  | "misconduct"
  | "facility"
  | "transport"
  | "weather"
  | "other";

export type SafeguardingIncidentSeverity = "low" | "medium" | "high" | "critical";
export type SafeguardingIncidentStatus = "open" | "triaged" | "investigating" | "resolved" | "closed";

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
export type BillingCycle = "monthly" | "quarterly" | "annual";
export type SubscriptionStatus = "trialing" | "active" | "past_due" | "paused" | "cancelled";
export type BillingInvoiceStatus = "draft" | "open" | "paid" | "partial" | "void" | "uncollectible";
export type UsageUnit = "athlete" | "team" | "agent_task" | "report" | "storage_gb" | "message";

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

export type PublicSiteTeamRead = {
  id: UUID;
  name: string;
  sport: string;
  age_group: string | null;
  gender_category: string | null;
  season_label: string | null;
};

export type PublicSiteEventRead = {
  id: UUID;
  team_id: UUID | null;
  event_type: string;
  title: string;
  starts_at: string;
  ends_at: string | null;
  timezone: string;
  venue_name: string | null;
};

export type OrganizationPublicSiteRead = {
  id: UUID;
  name: string;
  slug: string;
  organization_type: OrganizationType;
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
  teams: PublicSiteTeamRead[];
  upcoming_events: PublicSiteEventRead[];
};

export type RegistrationInquiryRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  athlete_name: string;
  guardian_name: string | null;
  email: string;
  phone: string | null;
  age_group: string | null;
  sport_interest: string | null;
  message: string | null;
  source_url: string | null;
  status: string;
  review_notes: string | null;
  follow_up_at: string | null;
  reviewed_by_person_id: UUID | null;
  reviewed_at: string | null;
  created_at: string;
};

export type RegistrationInquiryConversionRead = {
  inquiry: RegistrationInquiryRead;
  athlete_person_id: UUID;
  athlete_profile_id: UUID;
  roster_entry_id: UUID | null;
  guardian_person_id: UUID | null;
};

export type RegistrationInquiryFollowUpRead = {
  inquiry: RegistrationInquiryRead;
  message: CommunicationMessageRead;
  recipient_person_id: UUID;
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

export type FamilyAthleteSummaryRead = {
  athlete_person_id: UUID;
  athlete_name: string;
  relationship: string;
  relationship_kind: string;
  can_sign_consent: boolean;
  can_view_medical: boolean;
  emergency_contact: boolean;
  pending_consent_requests: number;
  latest_consent_status: ConsentStatus | null;
  latest_consent_scope_type: ConsentScopeType | null;
  latest_consent_signed_at: string | null;
};

export type FamilyEventSummaryRead = {
  athlete_person_id: UUID;
  athlete_name: string;
  event_id: UUID;
  team_id: UUID | null;
  event_type: EventType;
  title: string;
  starts_at: string;
  ends_at: string | null;
  timezone: string;
  venue_name: string | null;
  attendance_status: AttendanceStatus | null;
  clearance_status: ParticipationClearanceStatus;
  guardian_required: boolean;
  consent_id: UUID | null;
  reason: string;
};

export type FamilyConsentRequestRead = {
  id: UUID;
  organization_id: UUID;
  athlete_person_id: UUID;
  athlete_name: string;
  scope_type: ConsentScopeType;
  scope_id: UUID | null;
  channel: ConsentCaptureChannel;
  destination: string;
  status: string;
  expires_at: string | null;
  sent_at: string | null;
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

export type EquipmentFileRead = {
  id: UUID;
  organization_id: UUID;
  equipment_item_id: UUID;
  uploaded_by_person_id: UUID | null;
  filename: string;
  content_type: string;
  size_bytes: number;
  checksum: string;
  storage_url: string;
  notes: string | null;
};

export type EquipmentScanRead = {
  scanned_code: string;
  match_type: string;
  item: EquipmentItemRead;
};

export type EquipmentScanEventRead = {
  id: UUID;
  organization_id: UUID;
  equipment_item_id: UUID | null;
  scanned_code: string;
  match_type: string | null;
  item_name: string | null;
  reader_id: string;
  reader_location: string | null;
  source: string;
  movement: string;
  matched: boolean;
  scanned_at: string;
  external_reference: string | null;
  notes: string | null;
};

export type EquipmentReaderRead = {
  id: UUID;
  organization_id: UUID;
  reader_id: string;
  name: string;
  location: string | null;
  status: string;
  last_seen_at: string | null;
  last_scan_at: string | null;
  notes: string | null;
};

export type EquipmentReaderProvisionRead = {
  reader: EquipmentReaderRead;
  api_key: string;
};

export type ProcurementRecommendationRead = {
  equipment_item_id: UUID;
  item_name: string;
  category: string;
  quantity_available: number;
  reorder_point: number;
  recommended_quantity: number;
  estimated_cost: string;
  supplier_hint: string;
  urgency: string;
  rationale: string;
};

export type SupplierScoreRead = {
  supplier_name: string;
  work_orders: number;
  completed_orders: number;
  safety_orders: number;
  estimated_cost: string;
  actual_cost: string;
  score: number;
  recommendation: string;
};

export type SupplierOrderRead = {
  id: UUID;
  organization_id: UUID;
  equipment_item_id: UUID | null;
  supplier_name: string;
  item_name: string;
  quantity: number;
  unit_cost: string;
  total_cost: string;
  currency: string;
  status: string;
  external_reference: string | null;
  ordered_at: string | null;
  expected_delivery_at: string | null;
  received_at: string | null;
  notes: string | null;
};

export type SupplierOrderSubmissionRead = {
  order: SupplierOrderRead;
  submission_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  destination: string | null;
  provider_status_code: number | null;
  submitted_at: string;
  failure_reason: string | null;
};

export type SupplierInvoiceSyncRead = {
  order: SupplierOrderRead;
  sync_mode: string;
  sync_attempted: boolean;
  synced: boolean;
  destination: string | null;
  provider_status_code: number | null;
  synced_at: string;
  failure_reason: string | null;
};

export type EquipmentLeaseQuoteRead = {
  equipment_item_id: UUID;
  item_name: string;
  quantity: number;
  term_months: number;
  monthly_amount: string;
  total_amount: string;
  residual_value: string;
  rationale: string;
};

export type EquipmentLeaseInvoiceRead = {
  lease_quote: EquipmentLeaseQuoteRead;
  invoice: FinanceInvoiceRead;
};

export type EquipmentLeaseInstallmentRead = {
  id: UUID;
  organization_id: UUID;
  lease_schedule_id: UUID;
  sequence_number: number;
  due_on: string;
  amount: string;
  amount_paid: string;
  currency: string;
  status: string;
  paid_at: string | null;
};

export type EquipmentLeaseScheduleRead = {
  id: UUID;
  organization_id: UUID;
  equipment_item_id: UUID;
  finance_invoice_id: UUID;
  person_id: UUID | null;
  team_id: UUID | null;
  quantity: number;
  term_months: number;
  monthly_amount: string;
  total_amount: string;
  currency: string;
  starts_on: string;
  status: string;
  notes: string | null;
  invoice: FinanceInvoiceRead;
  installments: EquipmentLeaseInstallmentRead[];
};

export type EquipmentLeasePaymentRead = {
  schedule: EquipmentLeaseScheduleRead;
  payment: FinancePaymentRead;
  installments_paid: number;
  installments_partially_paid: number;
  amount_applied: string;
  remaining_balance: string;
};

export type AssetUtilizationRecommendationRead = {
  target_type: string;
  target_id: UUID;
  title: string;
  severity: string;
  recommendation: string;
  expected_impact: string;
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

export type CommercialRefundRead = {
  refund_id: string;
  organization_id: UUID;
  target_type: string;
  target_id: UUID;
  amount: string;
  currency: string;
  reason: string;
  status: string;
  external_reference: string | null;
};

export type TaxQuoteRead = {
  organization_id: UUID;
  jurisdiction: string;
  subtotal: string;
  tax_rate: string;
  tax_amount: string;
  total: string;
  reverse_charge: boolean;
  rationale: string;
};

export type PaymentSettlementRead = {
  organization_id: UUID;
  provider: string;
  currency: string;
  gross_ticket_revenue: string;
  gross_invoice_payments: string;
  gross_donations: string;
  gross_amount: string;
  fee_amount: string;
  net_amount: string;
  payout_reference: string;
  line_count: number;
};

export type AccountingExportRow = {
  row_type: string;
  source_id: UUID;
  account_code: string;
  memo: string;
  debit: string;
  credit: string;
  currency: string;
  external_reference: string | null;
};

export type AccountingExportRead = {
  organization_id: UUID;
  basis: string;
  system: string;
  rows: AccountingExportRow[];
  debit_total: string;
  credit_total: string;
};

export type SponsorshipDashboardRead = {
  sponsor_id: UUID;
  sponsor_name: string;
  agreement_count: number;
  contracted_value: string;
  active_value: string;
  deliverable_count: number;
  activation_count: number;
  roi_score: number;
  recommendation: string;
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

export type RenderedReportRead = {
  report_id: UUID;
  organization_id: UUID;
  output_format: ReportFormat;
  artifact_url: string;
  content_type: string;
  size_bytes: number;
  page_count: number | null;
  sheet_count: number | null;
  checksum: string;
  body_preview: string;
  rendered_at: string;
};

export type ReportArtifactAccessRead = {
  report_id: UUID;
  organization_id: UUID;
  output_format: ReportFormat;
  artifact_url: string;
  signed_url: string;
  expires_at: string;
  content_type: string;
  filename: string;
  checksum: string;
  size_bytes: number;
};

export type ReportVerificationRead = {
  report_id: UUID;
  organization_id: UUID;
  passed: boolean;
  score: number;
  findings: string[];
  recommendation: string;
  verified_at: string;
};

export type ReportChartRead = {
  chart_key: string;
  title: string;
  chart_type: string;
  labels: string[];
  values: number[];
  insight: string;
};

export type ReportingBenchmarkRead = {
  model_name: string;
  sample_size: number;
  average_score: number;
  high_risk_count: number;
  benchmark_band: string;
  recommendation: string;
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

export type BillingPlanRead = {
  id: UUID;
  code: string;
  name: string;
  description: string | null;
  base_price: string;
  currency: string;
  billing_cycle: BillingCycle;
  included_athletes: number;
  included_teams: number;
  included_agent_tasks: number;
  included_storage_gb: number;
  per_athlete_price: string;
  per_agent_task_price: string;
  features: string | null;
  status: string;
};

export type SubscriptionRead = {
  id: UUID;
  organization_id: UUID;
  billing_plan_id: UUID;
  status: SubscriptionStatus;
  billing_cycle: BillingCycle;
  current_period_start: string;
  current_period_end: string;
  trial_ends_on: string | null;
  next_billing_on: string | null;
  seats_purchased: number;
  negotiated_price: string | null;
  discount_code: string | null;
  external_customer_id: string | null;
  external_subscription_id: string | null;
  cancel_at_period_end: boolean;
  notes: string | null;
};

export type UsageMeterRead = {
  id: UUID;
  code: string;
  name: string;
  unit: UsageUnit;
  included_quantity: number;
  overage_price: string;
  aggregation: string;
  status: string;
};

export type UsageRecordRead = {
  id: UUID;
  organization_id: UUID;
  subscription_id: UUID;
  usage_meter_id: UUID;
  quantity: number;
  recorded_at: string;
  source: string;
  external_reference: string | null;
  notes: string | null;
};

export type SaaSInvoiceRead = {
  id: UUID;
  organization_id: UUID;
  subscription_id: UUID;
  invoice_number: string;
  period_start: string;
  period_end: string;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total: string;
  amount_paid: string;
  currency: string;
  due_on: string | null;
  status: BillingInvoiceStatus;
  line_items: string | null;
  external_invoice_id: string | null;
};

export type SaaSPaymentRead = {
  id: UUID;
  organization_id: UUID;
  invoice_id: UUID;
  amount: string;
  currency: string;
  provider: string;
  external_payment_id: string | null;
  received_at: string;
  status: string;
  notes: string | null;
};

export type BillingTaxQuoteRead = {
  organization_id: UUID;
  jurisdiction: string;
  subtotal: string;
  tax_rate: string;
  tax_amount: string;
  total: string;
  reverse_charge: boolean;
  filing_hint: string;
};

export type BillingProrationQuoteRead = {
  organization_id: UUID;
  subscription_id: UUID;
  current_price: string;
  new_price: string;
  effective_on: string;
  period_start: string;
  period_end: string;
  remaining_days: number;
  total_days: number;
  unused_credit: string;
  new_charge: string;
  net_amount: string;
  recommendation: string;
};

export type BillingTaxFilingRead = {
  organization_id: UUID;
  jurisdiction: string;
  period_start: string;
  period_end: string;
  invoice_count: number;
  taxable_subtotal: string;
  tax_amount: string;
  gross_total: string;
  outstanding_total: string;
  currency: string;
  filing_reference: string;
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  destination: string | null;
  provider_status_code: number | null;
  failure_reason: string | null;
  filed_at: string;
};

export type BillingPlanChangeRead = BillingProrationQuoteRead & {
  previous_billing_plan_id: UUID;
  new_billing_plan_id: UUID;
  previous_price: string;
  applied_price: string;
  subscription_status: SubscriptionStatus;
  applied_at: string;
};

export type BillingDunningNoticeRead = {
  organization_id: UUID;
  invoice_id: UUID;
  invoice_number: string;
  days_overdue: number;
  amount_due: string;
  severity: string;
  channel: string;
  message: string;
  next_action: string;
};

export type BillingDunningDeliveryRead = BillingDunningNoticeRead & {
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  destination: string | null;
  provider_status_code: number | null;
  failure_reason: string | null;
  delivered_at: string;
};

export type BillingPaymentWebhookRead = {
  organization_id: UUID;
  invoice_id: UUID;
  provider: string;
  event_type: string;
  accepted: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  payment_id: UUID | null;
  invoice_status: BillingInvoiceStatus;
  amount_paid: string;
  message: string;
};

export type BillingEntitlementRead = {
  id: UUID;
  organization_id: UUID;
  subscription_id: UUID;
  feature_key: string;
  limit_value: number | null;
  used_value: number;
  resets_on: string | null;
  status: string;
};

export type BillingSummaryRead = {
  organization_id: UUID;
  active_subscriptions: number;
  plans: number;
  usage_meters: number;
  usage_records: number;
  open_invoices: number;
  monthly_recurring_revenue: string;
  invoice_outstanding: string;
  entitlements: number;
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

export type SafeguardingIncidentRead = {
  id: UUID;
  organization_id: UUID;
  event_id: UUID | null;
  team_id: UUID | null;
  athlete_person_id: UUID | null;
  reported_by_person_id: UUID | null;
  assigned_to_person_id: UUID | null;
  incident_type: SafeguardingIncidentType;
  severity: SafeguardingIncidentSeverity;
  status: SafeguardingIncidentStatus;
  occurred_at: string;
  location: string | null;
  title: string;
  description: string;
  immediate_action: string | null;
  parent_notified_at: string | null;
  medical_follow_up_required: string;
  regulatory_report_required: boolean;
  resolution_notes: string | null;
  resolved_at: string | null;
  created_at: string;
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

export type AgentCredentialStatusRead = {
  execution_mode: string;
  default_model: string;
  webhook_configured: boolean;
  webhook_key_configured: boolean;
  credential_boundary: string;
  recommendation: string;
};

export type AgentGovernanceSummaryRead = {
  organization_id: UUID;
  agents: number;
  queued_tasks: number;
  running_tasks: number;
  waiting_for_review: number;
  completed_tasks: number;
  failed_tasks: number;
  cancelled_tasks: number;
  human_review_required: number;
  credential_status: AgentCredentialStatusRead;
};

export type AgentRunLedgerVerificationRead = {
  organization_id: UUID;
  total_records: number;
  verified_records: number;
  broken_records: UUID[];
  latest_record_hash: string | null;
  valid: boolean;
};

export type AgentRunRecordRead = {
  id: UUID;
  task_id: UUID;
  agent_id: UUID;
  agent_name: string;
  agent_kind: AgentKind;
  organization_id: UUID;
  event_type: string;
  task_type: string;
  title: string;
  status: AgentTaskStatus;
  model_policy: string;
  execution_mode: string;
  input_ref: string | null;
  output_ref: string | null;
  review_required: boolean;
  governance_notes: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  ledger_sequence: number;
  record_hash: string;
  previous_record_hash: string | null;
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

export type PerformanceIngestionRead = {
  observation: PerformanceObservationRead;
  evidence_ref: string;
  extractor: string;
  confidence: number;
  review_required: boolean;
  summary: string;
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

export type GeneratedTrainingPlanRead = {
  plan: TrainingPlanRead;
  items: TrainingPlanItemRead[];
  readiness_score: number;
  rationale: string;
  load_balance: string;
  next_competition_at: string | null;
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

export type TrainingSessionFeedbackRead = {
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
  recorded_at: string;
  readiness_band: string;
  load_delta: number | null;
  recommendation: string;
};

export type TrainingAvailabilitySlotRead = {
  starts_at: string;
  ends_at: string;
  conflict_count: number;
  conflicts: string[];
  score: number;
  recommendation: string;
};

export type TrainingAvailabilityRead = {
  organization_id: UUID;
  team_id: UUID;
  duration_minutes: number;
  slots: TrainingAvailabilitySlotRead[];
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

export type CompetitionFixtureGenerationRead = {
  competition_id: UUID;
  created: number;
  existing: number;
  rounds: number;
  fixtures: CompetitionFixtureRead[];
};

export type CompetitionAdvancementRead = {
  competition_id: UUID;
  source_stage_label: string;
  source_round_label: string;
  next_stage_label: string;
  next_round_label: string;
  winners: string[];
  byes: string[];
  created: number;
  skipped: number;
  fixtures: CompetitionFixtureRead[];
};

export type CompetitionScheduleOptimizationRead = {
  competition_id: UUID;
  moved: number;
  unchanged: number;
  protected_finals: number;
  team_rest_minutes: number;
  match_spacing_minutes: number;
  fixtures: CompetitionFixtureRead[];
};

export type CompetitionBroadcastRead = {
  competition_id: UUID;
  message_id: UUID;
  subject: string;
  channel: CommunicationChannel;
  recipient_count: number;
  attempted: number;
  delivered: number;
  queued: number;
  failed: number;
  suppressed: number;
  transport_mode: string;
};

export type CompetitionTicketingRead = {
  competition_id: UUID;
  fixture_id: UUID;
  event_id: UUID;
  ticket_product_id: UUID;
  name: string;
  price: string;
  currency: string;
  capacity: number;
  sold_count: number;
  access_zone: string | null;
  status: string;
  scheduled_at: string;
  venue_name: string | null;
};

export type CompetitionBracketMatchRead = {
  round_label: string;
  stage_label: string;
  slot: number;
  home_team_name: string | null;
  away_team_name: string | null;
  fixture_id: UUID | null;
  status: FixtureStatus | null;
  winner_team_name: string | null;
};

export type CompetitionBracketRoundRead = {
  round_label: string;
  stage_label: string;
  matches: CompetitionBracketMatchRead[];
};

export type CompetitionBracketRead = {
  competition_id: UUID;
  format: CompetitionFormat;
  rounds: CompetitionBracketRoundRead[];
};

export type CompetitionConflictRead = {
  competition_id: UUID;
  fixture_id: UUID | null;
  conflict_key: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
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

export type CommunicationInboxItemRead = {
  recipient_id: UUID;
  message_id: UUID;
  organization_id: UUID;
  subject: string;
  body: string;
  message_type: CommunicationMessageType;
  channel: CommunicationChannel;
  urgent: boolean;
  delivery_status: MessageDeliveryStatus;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  failure_reason: string | null;
};

export type CommunicationDispatchSummary = {
  message_id: UUID;
  attempted: number;
  sent: number;
  delivered: number;
  failed: number;
  suppressed: number;
  queued: number;
  transport_mode: string;
};

export type CommunicationDigestRead = {
  message_id: UUID;
  recipient_id: UUID;
  person_id: UUID;
  frequency: NotificationFrequency;
  channel: CommunicationChannel;
  item_count: number;
  subject: string;
  body: string;
};

export type CommunicationDigestRunRead = {
  organization_id: UUID;
  frequency: NotificationFrequency | null;
  considered: number;
  created: number;
  skipped: number;
  digests: CommunicationDigestRead[];
};

export type CommunicationDraftRead = {
  subject: string;
  body: string;
  model_name: string;
  review_required: boolean;
  rationale: string;
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
