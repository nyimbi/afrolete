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

export type WeatherAlertLevel = "information" | "advisory" | "warning" | "critical";
export type WeatherDecision = "proceed" | "monitor" | "modify" | "delay" | "cancel" | "evacuate";
export type TravelPlanStatus = "draft" | "ready" | "in_progress" | "completed" | "cancelled";
export type TravelRiskLevel = "low" | "medium" | "high" | "critical";

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
  | "no_guardian"
  | "medical_clearance_required"
  | "medical_not_cleared"
  | "medical_clearance_expired";

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
export type IncidentReportPackageStatus =
  | "draft"
  | "ready"
  | "submitted"
  | "accepted"
  | "rejected"
  | "withdrawn";
export type InsuranceClaimType =
  | "injury_medical"
  | "liability"
  | "equipment_damage"
  | "property_damage"
  | "travel"
  | "other";
export type InsuranceClaimStatus =
  | "draft"
  | "ready"
  | "submitted"
  | "acknowledged"
  | "in_review"
  | "approved"
  | "partially_paid"
  | "paid"
  | "denied"
  | "closed";
export type MedicalClearanceStatus =
  | "pending_review"
  | "restricted"
  | "cleared"
  | "not_cleared"
  | "expired";
export type BackgroundCheckStatus =
  | "requested"
  | "in_progress"
  | "clear"
  | "review_required"
  | "failed"
  | "expired";
export type ComplianceCredentialType =
  | "safeguarding_training"
  | "first_aid"
  | "coaching_license"
  | "officiating_license"
  | "driver_certification"
  | "background_check"
  | "medical_license"
  | "other";
export type ComplianceCredentialStatus = "pending" | "verified" | "expiring_soon" | "expired" | "revoked";

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
export type EmergencyActionPlanStatus = "draft" | "active" | "under_review" | "retired";
export type EmergencyActivationStatus = "active" | "resolved" | "cancelled" | "reviewed";
export type EmergencyType =
  | "medical"
  | "fire"
  | "weather"
  | "security"
  | "evacuation"
  | "missing_person"
  | "other";
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

export type EventWeatherAssessmentRead = {
  id: UUID;
  organization_id: UUID;
  event_id: UUID;
  source: string;
  observed_at: string;
  temperature_c: number | null;
  heat_index_c: number | null;
  wbgt_c: number | null;
  humidity_percent: number | null;
  aqi: number | null;
  lightning_distance_km: number | null;
  wind_speed_kph: number | null;
  wind_gust_kph: number | null;
  precipitation_mm_per_hr: number | null;
  alert_level: WeatherAlertLevel;
  decision: WeatherDecision;
  recommended_actions: string;
  notes: string | null;
};

export type EventWeatherAlertRead = {
  event_id: UUID;
  assessment_id: UUID;
  message_id: UUID;
  recipient_count: number;
  channel: CommunicationChannel;
  subject: string;
  urgent: boolean;
};

export type EventWeatherAutomationRunItemRead = {
  assessment_id: UUID;
  alert_level: WeatherAlertLevel;
  decision: WeatherDecision;
  action: string;
  message_id: UUID | null;
  recipient_count: number;
  reason: string;
};

export type EventWeatherAutomationRunRead = {
  event_id: UUID;
  channel: CommunicationChannel;
  minimum_alert_level: WeatherAlertLevel;
  dry_run: boolean;
  candidate_count: number;
  dispatched_count: number;
  skipped_count: number;
  items: EventWeatherAutomationRunItemRead[];
};

export type EventTravelPlanRead = {
  id: UUID;
  organization_id: UUID;
  event_id: UUID;
  status: TravelPlanStatus;
  destination: string;
  travel_mode: string;
  departure_at: string | null;
  return_at: string | null;
  route_summary: string | null;
  vehicle_details: string | null;
  driver_details: string | null;
  staff_manifest: string | null;
  passenger_manifest: string | null;
  lodging_details: string | null;
  meal_plan: string | null;
  equipment_manifest: string | null;
  emergency_contacts: string | null;
  medical_access_plan: string | null;
  route_weather_risk: string | null;
  driver_certification_status: string | null;
  vehicle_inspection_status: string | null;
  consent_required: boolean;
  consent_due_at: string | null;
  estimated_cost: number | null;
  cost_per_participant: number | null;
  risk_level: TravelRiskLevel;
  risk_assessment: string;
  notes: string | null;
};

export type EventTravelConsentRequestItemRead = {
  request_id: UUID;
  athlete_person_id: UUID;
  guardian_person_id: UUID;
  destination: string;
  one_time_token: string;
};

export type EventTravelConsentBatchRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  created: number;
  existing: number;
  skipped_no_guardian: number;
  skipped_not_minor: number;
  requests: EventTravelConsentRequestItemRead[];
};

export type EventTravelConsentReminderRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  message_id: UUID;
  pending_request_count: number;
  recipient_count: number;
};

export type EventTravelConsentReminderRunPlanRead = {
  travel_plan_id: UUID;
  destination: string;
  travel_mode: string;
  consent_due_at: string | null;
  status: TravelPlanStatus;
};

export type EventTravelConsentReminderRunRead = {
  event_id: UUID;
  due_by: string;
  due_plan_count: number;
  pending_request_count: number;
  message_id: UUID | null;
  recipient_count: number;
  channel: CommunicationChannel;
  plans: EventTravelConsentReminderRunPlanRead[];
};

export type EventTravelManifestParticipantRead = {
  person_id: UUID;
  display_name: string;
  guardian_names: string[];
  guardian_contacts: string[];
  medical_clearance_status: MedicalClearanceStatus | null;
  medical_clearance_reason: string;
};

export type EventTravelManifestRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  destination: string;
  participant_count: number;
  emergency_contacts: string | null;
  medical_access_plan: string | null;
  participants: EventTravelManifestParticipantRead[];
};

export type EventTravelManifestExportRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  filename: string;
  content_type: string;
  content: string;
};

export type EventTravelManifestOfflineLinkRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  filename: string;
  content_type: string;
  size_bytes: number;
  checksum: string;
  signed_url: string;
  expires_at: string;
};

export type EventTravelFeeInvoiceItemRead = {
  invoice_id: UUID;
  invoice_number: string;
  billed_person_id: UUID;
  athlete_person_id: UUID;
  amount_due: string;
  status: string;
};

export type EventTravelFeeInvoiceBatchRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  created: number;
  existing: number;
  skipped_no_payer: number;
  total_amount_due: string;
  invoices: EventTravelFeeInvoiceItemRead[];
};

export type EventTravelFeeCheckoutItemRead = {
  invoice_id: UUID;
  invoice_number: string;
  billed_person_id: UUID | null;
  amount_due: string;
  amount_paid: string;
  open_amount: string;
  currency: string;
  status: string;
  provider: string;
  checkout_url: string;
  session_id: string;
  session_url: string;
  session_status: string;
  client_reference: string;
  success_url: string | null;
  cancel_url: string | null;
  expires_at: string | null;
};

export type EventTravelFeeCheckoutBatchRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  provider: string;
  checkout_count: number;
  total_open_amount: string;
  checkouts: EventTravelFeeCheckoutItemRead[];
};

export type EventTravelFeeReconciliationPaymentRead = {
  payment_id: UUID;
  amount: string;
  currency: string;
  method: string;
  external_reference: string | null;
  received_at: string;
};

export type EventTravelFeeReconciliationExceptionRead = {
  code: string;
  severity: string;
  invoice_id: UUID | null;
  invoice_number: string | null;
  detail: string;
  recommended_action: string;
};

export type EventTravelFeeReconciliationItemRead = {
  invoice_id: UUID;
  invoice_number: string;
  billed_person_id: UUID | null;
  amount_due: string;
  amount_paid: string;
  open_amount: string;
  currency: string;
  status: string;
  session_id: string;
  session_status: string;
  payment_count: number;
  last_payment_reference: string | null;
  payments: EventTravelFeeReconciliationPaymentRead[];
  exceptions: EventTravelFeeReconciliationExceptionRead[];
};

export type EventTravelFeeReconciliationRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  provider: string;
  invoice_count: number;
  paid_count: number;
  partial_count: number;
  unpaid_count: number;
  total_due: string;
  total_paid: string;
  total_open: string;
  exception_count: number;
  exceptions: EventTravelFeeReconciliationExceptionRead[];
  reconciled_at: string;
  items: EventTravelFeeReconciliationItemRead[];
};

export type EventTravelFeeReconciliationResolutionRead = {
  travel_plan_id: UUID;
  invoice_id: UUID;
  action: string;
  payment_id: UUID | null;
  message: string;
  reconciliation: EventTravelFeeReconciliationRead;
};

export type EventTravelFeeHostedCheckoutRead = {
  invoice_id: UUID;
  invoice_number: string;
  organization_id: UUID;
  billed_person_id: UUID | null;
  title: string;
  memo: string | null;
  due_on: string | null;
  amount_due: string;
  amount_paid: string;
  open_amount: string;
  currency: string;
  status: string;
  provider: string;
  session_id: string;
  session_status: string;
  client_reference: string;
  payment_methods: string[];
  settlement_endpoint: string;
  checkout_summary: string;
};

export type EventTravelFeeCheckoutSettlementRead = {
  invoice_id: UUID;
  provider: string;
  accepted: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  payment_id: UUID | null;
  invoice_status: string;
  amount_paid: string;
  open_amount: string;
  session_status: string;
  message: string;
};

export type EventTravelApprovalRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  approval_level: string;
  status: string;
  approver_person_id: UUID | null;
  decided_by_person_id: UUID | null;
  decided_at: string | null;
  notes: string | null;
};

export type EventTravelApprovalRoutingRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  recommended_levels: string[];
  created: number;
  existing: number;
  rationale: string[];
  approvals: EventTravelApprovalRead[];
};

export type EventTravelChecklistItemRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  checklist_type: string;
  item_label: string;
  status: string;
  completed_by_person_id: UUID | null;
  completed_at: string | null;
  evidence_url: string | null;
  notes: string | null;
};

export type EventTravelChecklistEvidenceUploadRead = {
  checklist_item_id: UUID;
  filename: string;
  content_type: string;
  size_bytes: number;
  checksum: string;
  evidence_url: string;
  checklist_item: EventTravelChecklistItemRead;
};

export type EventTravelLocationUpdateRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  phase: string;
  source: string;
  recorded_at: string;
  recorded_by_person_id: UUID | null;
  latitude: string;
  longitude: string;
  speed_kph: string | null;
  heading_degrees: string | null;
  notification_message_id: UUID | null;
  notification_recipient_count: number;
  notes: string | null;
};

export type EventTravelTelemetryStreamRead = {
  travel_plan_id: UUID;
  stream_url: string;
  content_type: string;
  update_count: number;
  latest_update_id: UUID | null;
  latest_recorded_at: string | null;
  replay_window_seconds: number;
};

export type EventTravelMapPathRead = {
  sequence: number;
  latitude: string;
  longitude: string;
  recorded_at: string;
  phase: string;
  source: string;
};

export type EventTravelMapMarkerRead = {
  label: string;
  marker_type: string;
  latitude: string;
  longitude: string;
  recorded_at: string | null;
  status: string | null;
};

export type EventTravelMapBoundsRead = {
  min_latitude: string | null;
  max_latitude: string | null;
  min_longitude: string | null;
  max_longitude: string | null;
};

export type EventTravelMapRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  destination: string;
  provider_hint: string;
  path: EventTravelMapPathRead[];
  markers: EventTravelMapMarkerRead[];
  bounds: EventTravelMapBoundsRead;
  latest_phase: string | null;
  latest_recorded_at: string | null;
};

export type EventTravelGeofenceCheckRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  latest_update_id: UUID;
  label: string;
  center_latitude: string;
  center_longitude: string;
  radius_km: string;
  distance_km: string;
  boundary_type: string;
  polygon_vertices: number;
  inside: boolean;
  breached: boolean;
  message_id: UUID | null;
  recipient_count: number;
  recommendation: string;
};

export type EventTravelGeofenceZoneRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  label: string;
  center_latitude: string;
  center_longitude: string;
  radius_km: string;
  polygon_coordinates: { latitude: string; longitude: string }[] | null;
  provider: string | null;
  provider_zone_id: string | null;
  provider_revision: string | null;
  alert_on_breach: boolean;
  channel: CommunicationChannel;
  active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type EventTravelDeviceRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  provider: string;
  device_id: string;
  label: string;
  status: "active" | "standby" | "disabled" | "lost" | "maintenance";
  assigned_vehicle: string | null;
  installed_at: string | null;
  notes: string | null;
  last_seen_at: string | null;
  last_location_update_id: UUID | null;
  last_battery_percent: string | null;
  last_accuracy_meters: string | null;
  secret_configured: boolean;
  secret_storage_mode: string;
  secret_vault_provider: string | null;
  secret_vault_reference: string | null;
  secret_rotated_at: string | null;
  created_at: string;
  updated_at: string;
};

export type EventTravelDeviceSecretRead = {
  id: UUID;
  travel_plan_id: UUID;
  provider: string;
  device_id: string;
  label: string;
  ingest_secret: string;
  secret_storage_mode: string;
  secret_vault_provider: string | null;
  secret_vault_reference: string | null;
  secret_rotated_at: string;
};

export type EventTravelDeviceFleetItemRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  event_id: UUID;
  destination: string;
  provider: string;
  device_id: string;
  label: string;
  status: string;
  assigned_vehicle: string | null;
  last_seen_at: string | null;
  last_battery_percent: string | null;
  last_accuracy_meters: string | null;
  secret_configured: boolean;
  secret_storage_mode: string;
  secret_vault_provider: string | null;
  secret_vault_reference: string | null;
};

export type EventTravelDeviceFleetInventoryRead = {
  organization_id: UUID;
  total_devices: number;
  active_devices: number;
  maintenance_devices: number;
  disabled_devices: number;
  lost_devices: number;
  stale_devices: number;
  low_battery_devices: number;
  devices: EventTravelDeviceFleetItemRead[];
};

export type EventTravelDeviceLocationIngestRead = {
  travel_plan_id: UUID;
  device_id: string;
  provider: string;
  device_registration_id: UUID | null;
  device_status: string | null;
  replay_protected: boolean;
  external_event_id: string | null;
  replay_retention_days: number | null;
  replay_retention_source: string | null;
  replay_events_pruned: number;
  signature_required: boolean;
  signature_validated: boolean;
  update: EventTravelLocationUpdateRead;
};

export type EventTravelDriverRatingRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  driver_name: string;
  driver_person_id: UUID | null;
  vehicle_label: string | null;
  overall_score: number;
  safety_score: number | null;
  punctuality_score: number | null;
  communication_score: number | null;
  vehicle_condition_score: number | null;
  would_use_again: boolean;
  incident_reported: boolean;
  reviewer_person_id: UUID | null;
  reviewed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type EventTravelDriverRatingSummaryRead = {
  travel_plan_id: UUID;
  rating_count: number;
  average_overall_score: string | null;
  would_use_again_count: number;
  incident_reported_count: number;
};

export type EventTravelBackupDriverRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  driver_name: string;
  driver_person_id: UUID | null;
  phone: string | null;
  vehicle_label: string | null;
  capacity: number;
  license_status: string;
  background_check_status: string;
  availability_status: "standby" | "available" | "dispatched" | "unavailable";
  response_minutes: number | null;
  priority: number;
  dispatched_at: string | null;
  dispatched_by_person_id: UUID | null;
  dispatch_message_id: UUID | null;
  dispatch_reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type EventTravelBackupDriverDispatchRead = {
  travel_plan_id: UUID;
  driver: EventTravelBackupDriverRead;
  eligible_driver_count: number;
  message_id: UUID | null;
  recipient_count: number;
  rationale: string[];
};

export type EventTravelDriverMarketplaceCandidateRead = {
  driver: EventTravelBackupDriverRead;
  match_score: string;
  verified: boolean;
  rating_count: number;
  average_rating: string | null;
  incident_reported_count: number;
  response_minutes: number | null;
  marketplace_status: string;
  rationale: string[];
};

export type EventTravelDriverMarketplaceRead = {
  travel_plan_id: UUID;
  candidate_count: number;
  verified_candidate_count: number;
  recommended_driver_id: UUID | null;
  candidates: EventTravelDriverMarketplaceCandidateRead[];
};

export type EventTravelExpenseRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  category: string;
  vendor: string | null;
  amount: string;
  currency: string;
  incurred_at: string;
  paid_by_person_id: UUID | null;
  reimbursement_status: string;
  approved_by_person_id: UUID | null;
  reimbursed_at: string | null;
  payout_provider: string | null;
  payout_reference: string | null;
  payout_status: string | null;
  payout_requested_at: string | null;
  payout_processed_by_person_id: UUID | null;
  payout_adapter_mode: string | null;
  payout_destination: string | null;
  payout_idempotency_key: string | null;
  payout_provider_status_code: number | null;
  payout_provider_response: string | null;
  receipt_url: string | null;
  notes: string | null;
};

export type EventTravelExpensePayoutRead = {
  expense_id: UUID;
  provider: string;
  payout_reference: string;
  payout_status: string;
  amount: string;
  currency: string;
  processed_at: string;
  adapter_mode: string;
  destination: string | null;
  idempotency_key: string;
  provider_status_code: number | null;
  provider_response: string | null;
  expense: EventTravelExpenseRead;
};

export type EventTravelExpensePayoutCallbackRead = {
  accepted: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  matched_by: string;
  payout_reference: string | null;
  payout_status: string;
  reimbursement_status: string;
  message: string;
  expense: EventTravelExpenseRead;
};

export type EventTravelReceiptUploadRead = {
  expense_id: UUID;
  filename: string;
  content_type: string;
  size_bytes: number;
  checksum: string;
  receipt_url: string;
  expense: EventTravelExpenseRead;
};

export type EventTravelCarpoolRideRead = {
  id: UUID;
  organization_id: UUID;
  travel_plan_id: UUID;
  ride_type: string;
  status: string;
  rider_person_id: UUID | null;
  driver_person_id: UUID | null;
  pickup_location: string;
  pickup_latitude: string | null;
  pickup_longitude: string | null;
  dropoff_location: string | null;
  dropoff_latitude: string | null;
  dropoff_longitude: string | null;
  seats_requested: number;
  seats_available: number;
  departure_window_start: string | null;
  departure_window_end: string | null;
  match_score: string | null;
  matched_at: string | null;
  notes: string | null;
};

export type EventTravelCarpoolAutoMatchPairRead = {
  request_id: UUID;
  offer_id: UUID;
  score: string;
  pickup_distance_km: string | null;
  dropoff_distance_km: string | null;
  seats_requested: number;
  seats_available: number;
  pickup_match: string;
  window_match: string;
};

export type EventTravelCarpoolAutoMatchRead = {
  travel_plan_id: UUID;
  matched_count: number;
  request_count: number;
  offer_count: number;
  pairs: EventTravelCarpoolAutoMatchPairRead[];
  rides: EventTravelCarpoolRideRead[];
};

export type EventTravelReadinessRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  ready: boolean;
  recommended_status: TravelPlanStatus;
  risk_level: TravelRiskLevel;
  blockers: string[];
  warnings: string[];
  approval_count: number;
  pending_approval_count: number;
  rejected_approval_count: number;
  checklist_count: number;
  pending_checklist_count: number;
  blocked_checklist_count: number;
  pending_consent_request_count: number;
};

export type EventTravelRouteStopRead = {
  sequence: number;
  stop_type: string;
  label: string;
  location: string;
  pickup_window_start: string | null;
  pickup_window_end: string | null;
  seats: number;
  notes: string | null;
};

export type EventTravelRouteOptimizationRead = {
  event_id: UUID;
  travel_plan_id: UUID;
  strategy: string;
  recommended_strategy: string;
  destination: string;
  stop_count: number;
  recommended_departure_at: string | null;
  estimated_duration_minutes: number;
  traffic_delay_minutes: number;
  weather_delay_minutes: number;
  reroute_required: boolean;
  reroute_reason: string | null;
  latest_weather_alert_level: WeatherAlertLevel | null;
  latest_weather_decision: WeatherDecision | null;
  risk_level: TravelRiskLevel;
  warnings: string[];
  reroute_actions: string[];
  route_summary: string;
  stops: EventTravelRouteStopRead[];
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
  medical_clearance_status: MedicalClearanceStatus | null;
  medical_clearance_id: UUID | null;
  medical_clearance_reason: string | null;
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

export type FamilyPerformanceGoalRead = {
  id: UUID;
  title: string;
  target_value: number;
  current_value: number | null;
  direction: string;
  due_at: string | null;
  status: string;
  reward_badge: string | null;
  notes: string | null;
};

export type FamilyPerformanceAwardRead = {
  id: UUID;
  title: string;
  badge_code: string;
  achievement_type: string;
  achieved_value: number | null;
  threshold_value: number | null;
  awarded_at: string;
  source_summary: string | null;
};

export type FamilyPerformanceSummaryRead = {
  athlete_person_id: UUID;
  athlete_profile_id: UUID;
  athlete_name: string;
  active_goal_count: number;
  achieved_goal_count: number;
  award_count: number;
  goals: FamilyPerformanceGoalRead[];
  awards: FamilyPerformanceAwardRead[];
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

export type EmergencyActionPlanRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID | null;
  title: string;
  emergency_type: EmergencyType;
  status: EmergencyActionPlanStatus;
  effective_from: string | null;
  review_due_on: string | null;
  emergency_contacts: string;
  evacuation_routes: string | null;
  medical_protocols: string | null;
  weather_protocols: string | null;
  communication_protocols: string | null;
  incident_command_roles: string | null;
  escalation_matrix: string | null;
  external_agency_contacts: string | null;
  equipment_locations: string | null;
  assembly_points: string | null;
  special_needs_plan: string | null;
  notes: string | null;
};

export type EmergencyPlanActivationRead = {
  id: UUID;
  organization_id: UUID;
  plan_id: UUID;
  facility_id: UUID | null;
  incident_id: UUID | null;
  activated_by_person_id: UUID | null;
  closed_by_person_id: UUID | null;
  emergency_type: EmergencyType;
  status: EmergencyActivationStatus;
  location_detail: string;
  activated_at: string;
  closed_at: string | null;
  escalation_level: number;
  assigned_responders: string | null;
  guidance_steps: string | null;
  communication_log: string | null;
  outcome_summary: string | null;
  response_time_seconds: number | null;
  notes: string | null;
};

export type EmergencyActivationAlertRead = {
  activation_id: UUID;
  message_id: UUID;
  recipient_count: number;
  channel: CommunicationChannel;
  subject: string;
  urgent: boolean;
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

export type DeveloperApplicationRead = {
  id: UUID;
  organization_id: UUID;
  owner_person_id: UUID | null;
  name: string;
  app_type: string;
  client_id: string;
  redirect_uris: string[];
  scopes: string[];
  contact_email: string | null;
  status: string;
  last_rotated_at: string | null;
  notes: string | null;
};

export type DeveloperApplicationProvisionedRead = {
  application: DeveloperApplicationRead;
  client_secret: string;
  secret_hint: string;
};

export type DeveloperApiKeyRead = {
  id: UUID;
  organization_id: UUID;
  application_id: UUID;
  name: string;
  key_prefix: string;
  scopes: string[];
  environment: string;
  status: string;
  expires_at: string | null;
  last_used_at: string | null;
  last_used_ip: string | null;
  usage_count: number;
  rate_limit_per_minute: number;
  window_started_at: string | null;
  window_request_count: number;
  last_rate_limited_at: string | null;
  refresh_token_family_id: UUID | null;
  refresh_parent_key_id: UUID | null;
  refresh_expires_at: string | null;
  refresh_rotated_at: string | null;
  refresh_reused_at: string | null;
  notes: string | null;
};

export type DeveloperApiKeyProvisionedRead = {
  api_key: DeveloperApiKeyRead;
  key: string;
  secret_hint: string;
};

export type DeveloperOAuthAuthorizationRead = {
  id: UUID;
  organization_id: UUID;
  application_id: UUID;
  client_id: string;
  application_name: string;
  redirect_uri: string;
  requested_scopes: string[];
  granted_scopes: string[];
  state: string | null;
  code_challenge_method: string | null;
  public_client: boolean;
  status: string;
  expires_at: string;
  consented_at: string | null;
  redeemed_at: string | null;
  authorization_code: string | null;
  redirect_url: string | null;
};

export type DeveloperOAuthTokenRead = {
  access_token: string;
  refresh_token: string | null;
  token_type: string;
  auth_header: string;
  api_key: DeveloperApiKeyRead;
  scopes: string[];
  expires_in: number | null;
  refresh_expires_in: number | null;
};

export type DeveloperWebhookSubscriptionRead = {
  id: UUID;
  organization_id: UUID;
  application_id: UUID | null;
  name: string;
  target_url: string;
  event_types: string[];
  delivery_mode: string;
  status: string;
  failure_count: number;
  last_delivery_status: string | null;
  last_delivered_at: string | null;
};

export type DeveloperWebhookSubscriptionProvisionedRead = {
  subscription: DeveloperWebhookSubscriptionRead;
  signing_secret: string;
  secret_hint: string;
};

export type DeveloperWebhookDeliveryRead = {
  id: UUID;
  organization_id: UUID;
  subscription_id: UUID;
  application_id: UUID | null;
  event_type: string;
  event_id: string;
  target_url: string;
  delivery_mode: string;
  status: string;
  attempt_count: number;
  response_status_code: number | null;
  failure_reason: string | null;
  last_attempted_at: string | null;
  next_attempt_at: string | null;
  delivered_at: string | null;
};

export type DeveloperWebhookRetryRunRead = {
  organization_id: UUID;
  eligible_count: number;
  replayed_count: number;
  skipped_count: number;
  failed_count: number;
  delivery_ids: UUID[];
  statuses: Record<string, number>;
  max_attempts: number;
  include_recorded: boolean;
};

export type DeveloperApiScopeCatalogRead = {
  scope: string;
  category: string;
  description: string;
  recommended_for: string[];
};

export type DeveloperWebhookEventCatalogRead = {
  event_type: string;
  category: string;
  description: string;
  emission_status: string;
  payload_fields: string[];
  recommended_scopes: string[];
  example_payload: Record<string, unknown>;
};

export type DeveloperSdkCatalogRead = {
  language: string;
  package_name: string;
  install_command: string;
  status: string;
  entry_points: string[];
};

export type DeveloperQuickstartRead = {
  title: string;
  language: string;
  description: string;
  steps: string[];
  code_sample: string;
};

export type DeveloperIntegrationCatalogRead = {
  organization_id: UUID;
  api_base_path: string;
  auth_header: string;
  webhook_signature_header: string;
  scopes: DeveloperApiScopeCatalogRead[];
  webhook_events: DeveloperWebhookEventCatalogRead[];
  sdks: DeveloperSdkCatalogRead[];
  configured_event_types: string[];
};

export type DeveloperPublicDocsRead = {
  title: string;
  version: string;
  api_base_path: string;
  authentication: string;
  auth_header: string;
  webhook_signature_header: string;
  webhook_timestamp_header: string;
  quickstarts: DeveloperQuickstartRead[];
  scopes: DeveloperApiScopeCatalogRead[];
  webhook_events: DeveloperWebhookEventCatalogRead[];
  sdks: DeveloperSdkCatalogRead[];
  marketplace_categories: string[];
  security_requirements: string[];
};

export type DeveloperMarketplaceListingRead = {
  id: UUID;
  organization_id: UUID;
  application_id: UUID | null;
  name: string;
  category: string;
  summary: string;
  install_url: string | null;
  support_url: string | null;
  pricing_model: string;
  version: string;
  visibility: string;
  review_status: string;
  install_count: number;
};

export type DeveloperPortalSummaryRead = {
  organization_id: UUID;
  application_count: number;
  active_application_count: number;
  api_key_count: number;
  active_api_key_count: number;
  webhook_subscription_count: number;
  live_webhook_count: number;
  marketplace_listing_count: number;
  approved_marketplace_listing_count: number;
  install_count: number;
  recommended_next_steps: string[];
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

export type BackgroundCheckRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID;
  requested_by_person_id: UUID | null;
  reviewed_by_person_id: UUID | null;
  provider: string;
  check_type: string;
  status: BackgroundCheckStatus;
  risk_level: string;
  requested_at: string;
  completed_at: string | null;
  expires_at: string | null;
  external_reference: string | null;
  result_summary: string | null;
  notes: string | null;
  created_at: string;
};

export type ComplianceCredentialRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID;
  verified_by_person_id: UUID | null;
  credential_type: ComplianceCredentialType;
  status: ComplianceCredentialStatus;
  title: string;
  issuing_body: string | null;
  credential_number: string | null;
  issued_at: string | null;
  expires_at: string | null;
  renewal_due_at: string | null;
  verification_url: string | null;
  evidence_object_key: string | null;
  notes: string | null;
  created_at: string;
};

export type ComplianceQueueItemRead = {
  source: string;
  id: UUID;
  person_id: UUID | null;
  person_name: string | null;
  title: string;
  status: string;
  due_on: string | null;
  severity: string;
  reason: string;
};

export type ComplianceSummaryRead = {
  organization_id: UUID;
  generated_at: string;
  overall_compliance_percent: number;
  total_background_checks: number;
  clear_background_checks: number;
  review_background_checks: number;
  expired_background_checks: number;
  total_credentials: number;
  verified_credentials: number;
  expiring_credentials: number;
  expired_credentials: number;
  revoked_credentials: number;
  open_incidents: number;
  critical_incidents: number;
  regulatory_incidents: number;
  blockers: ComplianceQueueItemRead[];
  renewals_due: ComplianceQueueItemRead[];
  investigation_queue: ComplianceQueueItemRead[];
};

export type ComplianceReconciliationRead = {
  organization_id: UUID;
  reconciled_at: string;
  background_checks_expired: number;
  credentials_expired: number;
  credentials_expiring_soon: number;
};

export type IncidentReportPackageRead = {
  id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  prepared_by_person_id: UUID | null;
  submitted_by_person_id: UUID | null;
  agency_name: string;
  jurisdiction: string;
  status: IncidentReportPackageStatus;
  due_at: string | null;
  submitted_at: string | null;
  accepted_at: string | null;
  external_reference: string | null;
  narrative: string;
  checklist_json: string | null;
  submission_payload: string | null;
  notes: string | null;
  created_at: string;
};

export type IncidentInsuranceClaimRead = {
  id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  claimant_person_id: UUID | null;
  prepared_by_person_id: UUID | null;
  submitted_by_person_id: UUID | null;
  claim_type: InsuranceClaimType;
  status: InsuranceClaimStatus;
  provider_name: string;
  policy_number: string | null;
  claim_number: string | null;
  coverage_verified_at: string | null;
  submitted_at: string | null;
  closed_at: string | null;
  claimed_amount_cents: number;
  approved_amount_cents: number;
  paid_amount_cents: number;
  currency: string;
  reserve_amount_cents: number;
  tracking_url: string | null;
  documentation_checklist_json: string | null;
  submission_payload: string | null;
  communication_log: string | null;
  notes: string | null;
  created_at: string;
};

export type IncidentMedicalClearanceRead = {
  id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  athlete_person_id: UUID;
  reviewed_by_person_id: UUID | null;
  status: MedicalClearanceStatus;
  clearance_type: string;
  assessed_at: string | null;
  valid_from: string | null;
  valid_until: string | null;
  restrictions: string | null;
  return_to_play_stage: string | null;
  provider_name: string | null;
  documentation_object_key: string | null;
  notes: string | null;
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

export type AgentWorkerCallbackRead = {
  accepted: boolean;
  duplicate: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  run_record_id: UUID | null;
  message: string;
  task: AgentTaskRead;
};

export type AgentModelRegistryRead = {
  id: UUID;
  organization_id: UUID;
  model_policy: string;
  provider: string;
  model_family: string | null;
  version: string | null;
  use_case: string;
  risk_tier: "low" | "medium" | "high" | "critical";
  review_status: "draft" | "in_review" | "approved" | "retired" | "blocked";
  documentation_url: string | null;
  evaluation_summary: string | null;
  limitations: string | null;
  bias_notes: string | null;
  data_residency: string | null;
  owner_person_id: UUID | null;
  approved_by_person_id: UUID | null;
  approved_at: string | null;
};

export type AgentBiasAuditRead = {
  id: UUID;
  organization_id: UUID;
  model_registry_id: UUID;
  model_policy: string;
  audit_dimension: string;
  population_slice: string;
  sample_size: number;
  disparity_score: number;
  status: string;
  severity: string;
  findings: string;
  recommendation: string;
  mitigation_status: string;
  audited_by_person_id: UUID | null;
  audited_at: string;
};

export type AgentDecisionAppealRead = {
  id: UUID;
  organization_id: UUID;
  agent_id: UUID;
  task_id: UUID;
  model_policy: string;
  status: string;
  reason: string;
  question: string;
  simple_explanation: string;
  technical_explanation: string;
  data_summary: string;
  alternative_options: string;
  supporting_evidence_ref: string | null;
  submitted_by_person_id: UUID | null;
  resolved_by_person_id: UUID | null;
  resolution_notes: string | null;
  due_at: string;
  resolved_at: string | null;
};

export type AgentFamilyTaskRead = {
  id: UUID;
  organization_id: UUID;
  agent_id: UUID;
  agent_name: string;
  agent_kind: AgentKind;
  task_type: string;
  title: string;
  status: AgentTaskStatus;
  input_ref: string | null;
  output_ref: string | null;
  review_notes: string | null;
  athlete_name: string | null;
  appeal_status: string | null;
  simple_explanation: string;
  data_summary: string;
  alternative_options: string;
  governance_note: string;
};

export type AgentDecisionAppealFormRead = {
  organization_id: UUID;
  task_id: UUID;
  generated_at: string;
  download_filename: string;
  content_type: string;
  content: string;
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

export type AgentModelTransparencyItemRead = {
  model_policy: string;
  agent_count: number;
  run_count: number;
  completed_runs: number;
  failed_runs: number;
  human_review_runs: number;
  execution_modes: string[];
  latest_run_at: string | null;
  risk_band: string;
  registry_status: string | null;
  registered_risk_tier: string | null;
  documentation_url: string | null;
  transparency_notes: string;
};

export type AgentModelTransparencyReportRead = {
  organization_id: UUID;
  generated_at: string;
  total_models: number;
  total_runs: number;
  human_review_required: number;
  local_model_count: number;
  webhook_model_count: number;
  ledger_valid: boolean;
  latest_record_hash: string | null;
  credential_boundary: string;
  recommendations: string[];
  models: AgentModelTransparencyItemRead[];
};

export type AgentEthicalScorecardRead = {
  organization_id: UUID;
  generated_at: string;
  score: number;
  grade: string;
  total_models: number;
  approved_models: number;
  blocked_models: number;
  undocumented_models: number;
  bias_audits: number;
  passing_bias_audits: number;
  failing_bias_audits: number;
  open_mitigations: number;
  pending_appeals: number;
  resolved_appeals: number;
  human_review_required: number;
  ledger_valid: boolean;
  public_summary: string;
  improvement_actions: string[];
};

export type AgentScorecardCommentRead = {
  id: UUID;
  organization_id: UUID;
  display_name: string;
  affiliation: string | null;
  comment: string;
  status: string;
  consent_to_publish: boolean;
  submitted_at: string;
};

export type AgentScorecardCommentModerationRead = AgentScorecardCommentRead & {
  contact_email: string | null;
  abuse_score: number;
  abuse_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type AgentScorecardPublicationRead = {
  id: UUID;
  organization_id: UUID;
  period_label: string;
  status: string;
  score: number;
  grade: string;
  total_models: number;
  approved_models: number;
  bias_audits: number;
  pending_appeals: number;
  ledger_valid: boolean;
  public_summary: string;
  improvement_actions: string[];
  published_comment_count: number;
  flagged_comment_count: number;
  snapshot_hash: string;
  published_by_person_id: UUID | null;
  published_at: string;
};

export type AgentScorecardPublicationArtifactRead = {
  publication_id: UUID;
  organization_id: UUID;
  period_label: string;
  artifact_format: string;
  generated_at: string;
  download_filename: string;
  content_type: string;
  content: string;
  content_base64: string | null;
  checksum: string;
  size_bytes: number;
  storage_url: string;
  storage_key: string;
};

export type AgentScorecardPublicationArtifactLinkRead = {
  publication_id: UUID;
  organization_id: UUID;
  period_label: string;
  artifact_format: string;
  storage_url: string;
  signed_url: string;
  expires_at: string;
  content_type: string;
  filename: string;
  checksum: string;
  size_bytes: number;
};

export type AgentScorecardArtifactAccessRead = {
  id: UUID;
  organization_id: UUID;
  publication_id: UUID;
  event_type: string;
  artifact_format: string;
  filename: string;
  content_type: string;
  checksum: string;
  size_bytes: number;
  signed_url: string | null;
  expires_at: string | null;
  request_ip: string | null;
  user_agent: string | null;
  request_source: string | null;
  accessed_at: string;
};

export type AgentScorecardArtifactAccessBucketRead = {
  label: string;
  count: number;
};

export type AgentScorecardArtifactAccessTrendRead = {
  date: string;
  link_created_count: number;
  artifact_opened_count: number;
  total_count: number;
};

export type AgentScorecardArtifactAccessAnomalyRead = {
  severity: string;
  code: string;
  title: string;
  evidence: string;
  recommended_action: string;
};

export type AgentScorecardArtifactAccessSummaryRead = {
  organization_id: UUID;
  total_events: number;
  link_created_count: number;
  artifact_opened_count: number;
  pdf_count: number;
  markdown_count: number;
  unique_requester_count: number;
  last_accessed_at: string | null;
  by_source: AgentScorecardArtifactAccessBucketRead[];
  daily_trend: AgentScorecardArtifactAccessTrendRead[];
  anomalies: AgentScorecardArtifactAccessAnomalyRead[];
};

export type AgentScorecardArtifactAnomalyAlertRead = {
  organization_id: UUID;
  channel: CommunicationChannel;
  anomaly_count: number;
  message_id: UUID | null;
  message_status: string | null;
  recipient_count: number;
  recipient_person_ids: UUID[];
  subject: string;
  body: string;
  delivered: boolean;
  failure_reason: string | null;
};

export type AgentScorecardArtifactAnomalyAlertRunRead = {
  organization_id: UUID;
  channel: CommunicationChannel;
  anomaly_count: number;
  evaluated: boolean;
  sent: boolean;
  skipped_reason: string | null;
  recipient_count: number;
  message_id: UUID | null;
  alert: AgentScorecardArtifactAnomalyAlertRead | null;
};

export type AgentScorecardPublicationReminderRead = {
  organization_id: UUID;
  period_label: string;
  channel: CommunicationChannel;
  readiness_status: string;
  message_id: UUID | null;
  message_status: string | null;
  recipient_count: number;
  recipient_person_ids: UUID[];
  subject: string;
  body: string;
  scheduled_for: string | null;
  delivered: boolean;
  failure_reason: string | null;
};

export type AgentScorecardPublicationReminderRunRead = {
  organization_id: UUID;
  due_by: string;
  period_label: string;
  due: boolean;
  current_period_published: boolean;
  readiness_status: string;
  sent: boolean;
  skipped_reason: string | null;
  recipient_count: number;
  message_id: UUID | null;
  reminder: AgentScorecardPublicationReminderRead | null;
};

export type AgentScorecardAutomationOrganizationRunRead = {
  organization_id: UUID;
  organization_name: string;
  publication_reminder: AgentScorecardPublicationReminderRunRead | null;
  artifact_alert_run: AgentScorecardArtifactAnomalyAlertRunRead | null;
  sent_count: number;
  message_count: number;
  skipped_reason: string | null;
};

export type AgentScorecardAutomationRunRead = {
  channel: CommunicationChannel;
  evaluated_count: number;
  skipped_count: number;
  sent_count: number;
  message_count: number;
  runs: AgentScorecardAutomationOrganizationRunRead[];
};

export type AgentScorecardPublicationReadinessRead = {
  organization_id: UUID;
  current_period_label: string;
  current_period_published: boolean;
  next_publication_due_at: string;
  days_until_due: number;
  latest_period_label: string | null;
  latest_published_at: string | null;
  flagged_comment_count: number;
  pending_appeal_count: number;
  score: number;
  grade: string;
  readiness_status: string;
  recommended_action: string;
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
  perceived_exertion: number | null;
  effort_rating: number | null;
  summary: string | null;
  recommendations: string | null;
  review_assigned_to_person_id: UUID | null;
  review_due_at: string | null;
  review_priority: "low" | "normal" | "high" | "urgent";
  review_notes: string | null;
  reviewed_by_person_id: UUID | null;
  reviewed_at: string | null;
  review_last_escalated_at: string | null;
  review_escalation_count: number;
  review_escalation_message_id: UUID | null;
  verification_status: MetricVerificationStatus;
};

export type AthleteAssessmentReviewQueueItemRead = {
  assessment: AthleteAssessmentRead;
  athlete_person_id: UUID;
  athlete_name: string;
  review_assigned_to_name: string | null;
  review_sla_state: "unscheduled" | "overdue" | "due_soon" | "on_track";
  review_age_hours: number;
};

export type AssessmentReviewLoadRead = {
  reviewer_person_id: UUID | null;
  reviewer_name: string;
  open_count: number;
  overdue_count: number;
  urgent_count: number;
  escalated_count: number;
  oldest_age_hours: number;
};

export type AssessmentReviewQueueSummaryRead = {
  organization_id: UUID;
  open_count: number;
  unassigned_count: number;
  assigned_count: number;
  overdue_count: number;
  due_soon_count: number;
  on_track_count: number;
  unscheduled_count: number;
  urgent_count: number;
  escalated_count: number;
  average_age_hours: number;
  oldest_age_hours: number;
  priority_counts: Record<string, number>;
  reviewer_loads: AssessmentReviewLoadRead[];
};

export type AthletePerformanceSummaryRead = {
  athlete_profile_id: UUID;
  latest_overall_score: number | null;
  observation_count: number;
  assessment_count: number;
  latest_assessment_id: UUID | null;
  rating: string | null;
};

export type PerformanceMetricBenchmarkRead = {
  metric_definition_id: UUID;
  metric_code: string;
  metric_name: string;
  sport: string | null;
  category: MetricCategory;
  unit: string | null;
  higher_is_better: boolean;
  cohort_scope: string;
  cohort_label: string;
  sample_size: number;
  athlete_value: number | null;
  cohort_average: number | null;
  cohort_min: number | null;
  cohort_max: number | null;
  delta_to_average: number | null;
  percentile_rank: number | null;
  cohort_rank: number | null;
  benchmark_band: string;
  recommendation: string;
};

export type PerformanceCohortComparisonRead = {
  cohort_scope: string;
  cohort_label: string;
  metric_count: number;
  sample_size_total: number;
  average_percentile: number | null;
  watch_count: number;
  top_metric_name: string | null;
  top_percentile: number | null;
  recommendation: string;
  benchmarks: PerformanceMetricBenchmarkRead[];
};

export type PerformanceMetricTrendRead = {
  metric_definition_id: UUID;
  metric_code: string;
  metric_name: string;
  sport: string | null;
  category: MetricCategory;
  unit: string | null;
  higher_is_better: boolean;
  sample_size: number;
  first_value: number | null;
  previous_value: number | null;
  latest_value: number | null;
  best_value: number | null;
  average_value: number | null;
  change_from_previous: number | null;
  change_from_first: number | null;
  consistency_index: number | null;
  forecast_next_value: number | null;
  trend_direction: string;
  recommendation: string;
};

export type PerformanceMetricTrendPointRead = {
  observation_id: UUID;
  observed_at: string;
  value: number;
  normalized_value: number;
  source: MetricSource;
  verification_status: MetricVerificationStatus;
};

export type PerformanceMetricTrendSeriesRead = {
  metric_definition_id: UUID;
  metric_code: string;
  metric_name: string;
  sport: string | null;
  category: MetricCategory;
  unit: string | null;
  higher_is_better: boolean;
  sample_size: number;
  latest_value: number | null;
  forecast_next_value: number | null;
  trend_direction: string;
  recommendation: string;
  points: PerformanceMetricTrendPointRead[];
};

export type PerformanceForecastScenarioRead = {
  metric_definition_id: UUID;
  metric_code: string;
  metric_name: string;
  sport: string | null;
  category: MetricCategory;
  unit: string | null;
  higher_is_better: boolean;
  sample_size: number;
  latest_value: number | null;
  forecast_next_value: number | null;
  forecast_low: number | null;
  forecast_high: number | null;
  confidence: number;
  data_quality: string;
  risk_level: string;
  trend_direction: string;
  model_policy: string;
  projected_points: number[];
  recommendation: string;
};

export type PerformanceForecastWhatIfRead = PerformanceForecastScenarioRead & {
  scenario_label: string;
  training_adjustment_percent: number;
  readiness_score: number;
  horizon: number;
};

export type PerformanceGoalRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  metric_definition_id: UUID;
  title: string;
  target_value: number;
  baseline_value: number | null;
  current_value: number | null;
  direction: string;
  starts_at: string;
  due_at: string | null;
  status: string;
  reward_badge: string | null;
  notes: string | null;
};

export type PerformanceAchievementAwardRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  goal_id: UUID | null;
  metric_definition_id: UUID | null;
  title: string;
  badge_code: string;
  achievement_type: string;
  achieved_value: number | null;
  threshold_value: number | null;
  awarded_at: string;
  source_summary: string | null;
};

export type PerformanceAchievementRunRead = {
  organization_id: UUID;
  athlete_profile_id: UUID;
  evaluated_goals: number;
  awarded_count: number;
  updated_goals: number;
  awards: PerformanceAchievementAwardRead[];
};

export type PerformanceAssessmentReviewEscalationRunRead = {
  organization_id: UUID | null;
  eligible_count: number;
  escalated_count: number;
  skipped_count: number;
  failed_count: number;
  overdue_count: number;
  due_soon_count: number;
  assessment_ids: UUID[];
  message_ids: UUID[];
  dry_run: boolean;
};

export type PlayerPerformanceProfileRead = {
  organization_id: UUID;
  athlete_profile_id: UUID;
  athlete_person_id: UUID;
  athlete_name: string;
  latest_overall_score: number | null;
  observation_count: number;
  assessment_count: number;
  latest_assessment_id: UUID | null;
  latest_assessment: AthleteAssessmentRead | null;
  rating: string | null;
  active_goal_count: number;
  achieved_goal_count: number;
  award_count: number;
  observations: PerformanceObservationRead[];
  goals: PerformanceGoalRead[];
  awards: PerformanceAchievementAwardRead[];
  trends: PerformanceMetricTrendRead[];
  trend_series: PerformanceMetricTrendSeriesRead[];
  forecast_scenarios: PerformanceForecastScenarioRead[];
  benchmarks: PerformanceMetricBenchmarkRead[];
  cohort_comparisons: PerformanceCohortComparisonRead[];
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

export type CommunicationEscalationRunRead = {
  original_message_id: UUID;
  escalation_message_id: UUID | null;
  channel: CommunicationChannel;
  escalation_level: number;
  target_count: number;
  skipped_count: number;
  recipient_count: number;
  subject: string;
  message: string;
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
