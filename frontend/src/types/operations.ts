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
  | "volunteer"
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
  registration_open: boolean;
  registration_fee_amount: string | null;
  registration_fee_currency: string | null;
  registration_payment_instructions: string | null;
  registration_required_documents: string[];
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

export type PublicSiteSponsorRead = {
  sponsor_id: UUID;
  name: string;
  industry: string | null;
  website_url: string | null;
  brand_assets_url: string | null;
  tier: string | null;
  active_value: string;
  currency: string | null;
  deliverables: string[];
  activation_note: string | null;
};

export type PublicSiteFundraisingCampaignRead = {
  id: UUID;
  name: string;
  purpose: string;
  goal_amount: string;
  raised_amount: string;
  currency: string;
  public_url: string | null;
  status: string;
};

export type PublicSiteTicketProductRead = {
  id: UUID;
  event_id: UUID;
  event_title: string | null;
  event_starts_at: string | null;
  venue_name: string | null;
  name: string;
  price: string;
  currency: string;
  capacity: number;
  sold_count: number;
  available_count: number;
  access_zone: string | null;
  status: string;
};

export type PublicSiteSupporterTierRead = {
  id: UUID;
  name: string;
  slug: string;
  monthly_price: string;
  currency: string;
  benefits: string;
  voting_weight: number;
  trial_days: number;
};

export type PublicSiteFanChallengeRead = {
  id: UUID;
  title: string;
  description: string;
  challenge_type: string;
  target_activity_type: string;
  target_count: number;
  points_reward: number;
  badge_name: string | null;
  starts_at: string;
  ends_at: string | null;
  completion_count: number;
};

export type PublicSiteFanLeaderboardEntryRead = {
  rank: number;
  supporter_profile_id: UUID;
  supporter_name: string;
  tier_name: string | null;
  engagement_points: number;
  completed_challenge_count: number;
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
  registration_open: boolean;
  registration_fee_amount: string | null;
  registration_fee_currency: string | null;
  registration_payment_instructions: string | null;
  registration_required_documents: string[];
  teams: PublicSiteTeamRead[];
  upcoming_events: PublicSiteEventRead[];
  sponsors: PublicSiteSponsorRead[];
  fundraising_campaigns: PublicSiteFundraisingCampaignRead[];
  ticket_products: PublicSiteTicketProductRead[];
  supporter_tiers: PublicSiteSupporterTierRead[];
  fan_challenges: PublicSiteFanChallengeRead[];
  fan_leaderboard: PublicSiteFanLeaderboardEntryRead[];
};

export type PublicSupporterSignupRead = {
  supporter_profile_id: UUID;
  organization_id: UUID;
  display_name: string;
  email: string;
  tier_id: UUID | null;
  tier_name: string | null;
  engagement_points: number;
  status: string;
  signup_status: string;
  points_awarded: number;
  next_actions: string[];
};

export type PublicSupporterChallengeProgressRead = {
  supporter_profile_id: UUID;
  supporter_name: string;
  challenge_id: UUID;
  challenge_title: string;
  progress_count: number;
  target_count: number;
  points_awarded: number;
  status: string;
  completed_at: string | null;
};

export type OrganizationDirectoryRead = {
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
  public_site_path: string;
  team_count: number;
  upcoming_event_count: number;
};

export type OrganizationOnboardingRead = {
  organization: OrganizationRead;
  starter_team: TeamRead | null;
  concierge_task: AgentTaskRead | null;
  launch_center: RegistrationLaunchCommandCenterRead | null;
  public_site_path: string;
  registration_page_path: string;
  admissions_path: string;
  family_portal_path: string;
  dashboard_path: string;
  owner_email: string;
  owner_display_name: string;
  checklist: string[];
};

export type RegistrationLaunchLinkRead = {
  key: string;
  label: string;
  url: string;
  qr_payload: string;
  description: string;
};

export type RegistrationLaunchCopyRead = {
  channel: string;
  label: string;
  subject: string | null;
  body: string;
  share_url: string;
  character_count: number;
};

export type RegistrationLaunchMetricRead = {
  key: string;
  label: string;
  value: number;
  detail: string;
  status: string;
};

export type RegistrationLaunchReadinessCheckRead = {
  key: string;
  label: string;
  status: string;
  detail: string;
  action_label: string | null;
  href: string | null;
};

export type RegistrationLaunchCommandCenterRead = {
  organization_id: UUID;
  organization_name: string;
  organization_type: OrganizationType;
  public_name: string | null;
  launch_status: string;
  readiness_score: number;
  public_site_path: string;
  registration_page_path: string;
  admissions_path: string;
  family_portal_path: string;
  dashboard_path: string;
  launch_links: RegistrationLaunchLinkRead[];
  channel_copies: RegistrationLaunchCopyRead[];
  metrics: RegistrationLaunchMetricRead[];
  readiness_checks: RegistrationLaunchReadinessCheckRead[];
  staff_actions: string[];
  agent_task: AgentTaskRead | null;
};

export type RegistrationOnboardingPresetRead = {
  key: string;
  label: string;
  organization_type: OrganizationType;
  audience: string;
  description: string;
  primary_sport: string;
  launch_goal: string;
  starter_team_name: string;
  starter_team_sport_format: SportFormat;
  starter_team_age_group: string | null;
  starter_team_gender_category: string | null;
  starter_team_season_label: string | null;
  registration_required_documents: string[];
  registration_fee_currency: string;
  registration_payment_instructions: string;
  checklist: string[];
};

export type RegistrationReadinessStepRead = {
  key: string;
  label: string;
  status: string;
  detail: string;
  action_label: string | null;
  href: string | null;
};

export type RegistrationReadinessOrganizationRead = {
  id: UUID;
  name: string;
  public_name: string | null;
  organization_type: OrganizationType;
  registration_open: boolean;
  public_site_path: string;
  registration_page_path: string;
  admissions_path: string;
};

export type RegistrationReadinessFamilyInquiryRead = {
  id: UUID;
  organization_id: UUID;
  organization_public_name: string | null;
  athlete_name: string;
  packet_complete: boolean;
  payment_status: string;
  next_steps: string[];
  public_site_path: string;
};

export type RegistrationOnboardingMissionRead = {
  key: string;
  audience: string;
  title: string;
  status: string;
  progress_percent: number;
  xp: number;
  detail: string;
  action_label: string;
  href: string;
};

export type RegistrationLearningPathCreate = {
  role: string;
  primary_goal: string;
  skill_level: string;
  learning_style: string;
  accessibility_mode?: string | null;
};

export type RegistrationLearningModuleRead = {
  key: string;
  title: string;
  duration_minutes: number;
  format: string;
  objective: string;
  practice_task: string;
  completion_badge: string;
};

export type RegistrationLearningPathRead = {
  role: string;
  primary_goal: string;
  skill_level: string;
  learning_style: string;
  path_title: string;
  estimated_minutes: number;
  difficulty: string;
  first_action: string;
  modules: RegistrationLearningModuleRead[];
  accessibility_supports: string[];
};

export type RegistrationReadinessRead = {
  auth_mode: string;
  identity_email: string;
  identity_display_name: string;
  managed_organization_count: number;
  registration_open_count: number;
  public_directory_count: number;
  admissions_inquiry_count: number;
  admissions_ready_count: number;
  family_registration_count: number;
  family_packet_complete_count: number;
  steps: RegistrationReadinessStepRead[];
  missions: RegistrationOnboardingMissionRead[];
  organizations: RegistrationReadinessOrganizationRead[];
  family_registrations: RegistrationReadinessFamilyInquiryRead[];
};

export type OrganizationHandleAvailabilityRead = {
  desired_slug: string;
  slug_available: boolean;
  slug_suggestions: string[];
  desired_subdomain: string | null;
  subdomain_available: boolean | null;
  subdomain_suggestions: string[];
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
  guardian_person_id: UUID | null;
  guardian_contact_status: string;
  date_of_birth: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  medical_notes: string | null;
  consent_signer_name: string | null;
  guardian_consent_acknowledged_at: string | null;
  privacy_acknowledged_at: string | null;
  payment_amount: string | null;
  payment_currency: string | null;
  payment_method: string | null;
  payment_reference: string | null;
  payment_status: string;
  verification_status: string;
  packet_submitted_at: string | null;
  missing_documents: string[];
  packet_complete: boolean;
  next_steps: string[];
  created_at: string;
};

export type RegistrationInquiryImportRowErrorRead = {
  row_number: number;
  message: string;
  row: Record<string, string | null>;
};

export type RegistrationInquiryImportTemplateRead = {
  organization_id: UUID;
  filename: string;
  columns: string[];
  csv_text: string;
};

export type RegistrationInquiryImportPreviewRowRead = {
  row_number: number;
  athlete_name: string;
  guardian_name: string | null;
  email: string;
  phone: string | null;
  age_group: string | null;
  sport_interest: string | null;
  team_id: UUID | null;
  team_name: string | null;
  payment_status: string;
  required_documents: string[];
};

export type RegistrationInquiryImportRead = {
  organization_id: UUID;
  dry_run: boolean;
  created_count: number;
  preview_count: number;
  error_count: number;
  inquiries: RegistrationInquiryRead[];
  preview_rows: RegistrationInquiryImportPreviewRowRead[];
  errors: RegistrationInquiryImportRowErrorRead[];
};

export type RegistrationInquiryAccountReadinessRead = {
  inquiry_id: UUID;
  guardian_person_id: UUID | null;
  guardian_email: string | null;
  guardian_contact_status: string;
  account_status: string;
  can_create_account: boolean;
  can_sign_in: boolean;
  recommended_action: string;
};

export type FamilyRegistrationInquiryRead = {
  id: UUID;
  organization_id: UUID;
  organization_name: string;
  organization_public_name: string | null;
  organization_slug: string;
  public_site_path: string;
  athlete_name: string;
  guardian_name: string | null;
  email: string;
  status: string;
  verification_status: string;
  guardian_contact_status: string;
  account_status: string;
  payment_status: string;
  packet_complete: boolean;
  missing_documents: string[];
  next_steps: string[];
  created_at: string;
  packet_submitted_at: string | null;
};

export type RegistrationDocumentSubmission = {
  document_type: string;
  filename: string;
  storage_url: string | null;
  checksum: string | null;
  content_type: string | null;
  size_bytes: number | null;
  notes: string | null;
};

export type RegistrationPacketRead = {
  inquiry: RegistrationInquiryRead;
  required_documents: string[];
  submitted_documents: RegistrationDocumentSubmission[];
  missing_documents: string[];
  consent_complete: boolean;
  medical_complete: boolean;
  emergency_contact_complete: boolean;
  payment_complete: boolean;
  packet_complete: boolean;
  next_steps: string[];
};

export type RegistrationPaymentHostedCheckoutRead = {
  inquiry_id: UUID;
  organization_id: UUID;
  athlete_name: string;
  guardian_name: string | null;
  guardian_email: string;
  registration_reference: string;
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
  public_registration_path: string;
  family_portal_path: string;
};

export type RegistrationPaymentSessionRead = {
  inquiry: RegistrationInquiryRead;
  session_id: string;
  checkout_url: string;
  provider: string;
  hosted_checkout: RegistrationPaymentHostedCheckoutRead;
};

export type RegistrationPaymentSettlementRead = {
  inquiry_id: UUID;
  provider: string;
  accepted: boolean;
  payment_reference: string | null;
  payment_status: string;
  amount_paid: string;
  open_amount: string;
  session_status: string;
  message: string;
};

export type RegistrationInquiryConversionRead = {
  inquiry: RegistrationInquiryRead;
  athlete_person_id: UUID;
  athlete_profile_id: UUID;
  roster_entry_id: UUID | null;
  guardian_person_id: UUID | null;
  guardian_invite_message_id: UUID | null;
  guardian_invite_portal_url: string | null;
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

export type VolunteerProfileRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID;
  person_name: string;
  person_email: string | null;
  volunteer_type: string;
  certification_level: string | null;
  availability: string[];
  skills: string[];
  background_check_status: string;
  background_check_expires_on: string | null;
  training_status: string;
  onboarding_status: string;
  reliability_score: number;
  emergency_contact: string | null;
  notes: string | null;
  status: string;
};

export type VolunteerOpportunityRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  event_id: UUID | null;
  title: string;
  role_type: string;
  description: string | null;
  required_skills: string[];
  starts_at: string;
  ends_at: string | null;
  location: string | null;
  slots_required: number;
  assigned_count: number;
  open_slots: number;
  min_age: number | null;
  background_check_required: boolean;
  training_required: boolean;
  public_signup: boolean;
  priority: string;
  status: string;
};

export type VolunteerNeedRequestRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  event_id: UUID | null;
  requested_by_person_id: UUID | null;
  title: string;
  role_type: string;
  needed_count: number;
  required_skills: string[];
  needed_by: string | null;
  priority: string;
  status: string;
  notes: string | null;
  opportunity_id: UUID | null;
};

export type PublicVolunteerSignupRead = {
  organization_id: UUID;
  opportunity_id: UUID;
  opportunity_title: string;
  volunteer_profile_id: UUID;
  assignment_id: UUID;
  person_id: UUID;
  person_name: string;
  person_email: string | null;
  status: string;
  match_score: number;
  onboarding_status: string;
  message: string | null;
};

export type VolunteerGroupApplicationRead = {
  id: UUID;
  organization_id: UUID;
  opportunity_id: UUID;
  opportunity_title: string;
  company_name: string;
  coordinator_name: string;
  coordinator_email: string;
  coordinator_phone: string | null;
  group_size: number;
  requested_slots: number;
  approved_slots: number;
  skills: string[];
  availability: string[];
  message: string | null;
  source_url: string | null;
  status: string;
  reviewed_by_person_id: UUID | null;
  reviewed_at: string | null;
  review_notes: string | null;
};

export type VolunteerAssignmentRead = {
  id: UUID;
  organization_id: UUID;
  opportunity_id: UUID;
  volunteer_profile_id: UUID;
  person_id: UUID;
  person_name: string;
  opportunity_title: string;
  role_type: string;
  status: string;
  match_score: number;
  confirmed_at: string | null;
  checked_in_at: string | null;
  checked_out_at: string | null;
  hours_logged: number;
  notes: string | null;
};

export type VolunteerTrainingRecordRead = {
  id: UUID;
  organization_id: UUID;
  volunteer_profile_id: UUID;
  module_name: string;
  role_type: string | null;
  required: boolean;
  status: string;
  assigned_at: string;
  completed_at: string | null;
  expires_on: string | null;
  score: number | null;
  certificate_url: string | null;
};

export type VolunteerObligationRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID;
  person_name: string;
  person_email: string | null;
  team_id: UUID | null;
  season_label: string;
  category: string;
  required_hours: number;
  completed_hours: number;
  waived_hours: number;
  remaining_hours: number;
  due_on: string | null;
  status: string;
  notes: string | null;
};

export type VolunteerRecognitionRead = {
  id: UUID;
  organization_id: UUID;
  volunteer_profile_id: UUID;
  recognition_type: string;
  badge_code: string;
  title: string;
  points: number;
  awarded_on: string;
  source_summary: string | null;
};

export type VolunteerSummaryRead = {
  organization_id: UUID;
  active_volunteers: number;
  open_opportunities: number;
  open_slots: number;
  assigned_shifts: number;
  confirmed_shifts: number;
  pending_group_applications: number;
  approved_group_slots: number;
  open_need_requests: number;
  obligation_deficit_hours: number;
  completed_hours: number;
  training_compliance_percent: number;
  coverage_percent: number;
  top_skills: string[];
  shortage_roles: string[];
};

export type VolunteerReminderRunRead = {
  organization_id: UUID;
  eligible_count: number;
  reminded_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  coverage_gap_count: number;
  obligation_count: number;
  training_count: number;
  recipient_count: number;
  message_ids: UUID[];
};

export type VolunteerCoordinationMessageRead = {
  organization_id: UUID;
  opportunity_id: UUID;
  opportunity_title: string;
  channel: CommunicationChannel;
  subject: string;
  body: string;
  urgent: boolean;
  eligible_assignment_count: number;
  recipient_count: number;
  assignment_ids: UUID[];
  recipient_person_ids: UUID[];
  message_id: UUID | null;
  skipped_reasons: string[];
};

export type VolunteerSubstitutePoolMemberRead = {
  id: UUID;
  organization_id: UUID;
  volunteer_profile_id: UUID;
  person_id: UUID;
  person_name: string;
  person_email: string | null;
  team_id: UUID | null;
  role_type: string;
  availability: string[];
  priority: number;
  max_dispatches_per_month: number;
  status: string;
  last_contacted_at: string | null;
  notes: string | null;
};

export type VolunteerSubstituteDispatchRead = {
  organization_id: UUID;
  opportunity_id: UUID;
  opportunity_title: string;
  open_slots_before: number;
  candidate_count: number;
  dispatched_count: number;
  assignment_ids: UUID[];
  message_id: UUID | null;
  recipient_count: number;
  skipped_reasons: string[];
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
  organization_id: UUID;
  organization_name: string;
  organization_contact_email: string | null;
  organization_contact_phone: string | null;
  organization_logo_url: string | null;
  brand_primary_color: string | null;
  brand_secondary_color: string | null;
  event_title: string;
  event_starts_at: string;
  venue_name: string | null;
  destination: string;
  travel_mode: string;
  departure_at: string | null;
  return_at: string | null;
  route_summary: string | null;
  vehicle_details: string | null;
  driver_details: string | null;
  consent_required: boolean;
  risk_level: TravelRiskLevel;
  risk_assessment: string;
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

export type CommercialInvoiceHostedCheckoutRead = {
  invoice_id: UUID;
  invoice_number: string;
  organization_id: UUID;
  sponsor_id: UUID;
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

export type CommercialInvoiceProviderCheckoutRead = {
  id: UUID | null;
  invoice_id: UUID;
  organization_id: UUID;
  sponsor_id: UUID;
  provider: string;
  mode: string;
  status: string;
  provider_session_id: string;
  local_session_id: string;
  client_reference: string;
  amount: string;
  currency: string;
  redirect_url: string;
  success_url: string | null;
  cancel_url: string | null;
  customer_email: string | null;
  payment_method: string;
  provider_status_code: number | null;
  provider_response: string | null;
  failure_reason: string | null;
  webhook_configured: boolean;
  created_at: string;
  updated_at: string | null;
};

export type CommercialInvoiceCheckoutSettlementRead = {
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
  attendance_policy_code: string | null;
  attendance_policy_decision: string | null;
  attendance_policy_warnings: string[];
};

export type EventAttendancePolicyRead = {
  id: UUID | null;
  organization_id: UUID;
  event_id: UUID;
  policy_code: string;
  title: string;
  active: boolean;
  participation_statuses: AttendanceStatus[];
  require_minor_consent: boolean;
  require_medical_clearance: boolean;
  minor_consent_action: string;
  no_guardian_action: string;
  denied_consent_action: string;
  expired_consent_action: string;
  missing_medical_action: string;
  not_cleared_medical_action: string;
  expired_medical_action: string;
  restricted_medical_action: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
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

export type GuardianAccountReadinessRead = {
  relationship_id: UUID;
  athlete_person_id: UUID;
  athlete_name: string;
  guardian_person_id: UUID;
  guardian_name: string;
  guardian_email: string | null;
  guardian_phone: string | null;
  account_status: string;
  linked_app_user_id: UUID | null;
  keycloak_sub: string | null;
  email_matches_app_user: boolean;
  can_receive_invite: boolean;
  last_invite_message_id: UUID | null;
  last_invite_channel: CommunicationChannel | null;
  last_invite_destination: string | null;
  last_invite_delivery_status: string | null;
  last_invite_created_at: string | null;
  last_invite_sent_at: string | null;
  recommended_action: string;
};

export type GuardianPortalInviteRead = {
  relationship_id: UUID;
  organization_id: UUID;
  guardian_person_id: UUID;
  guardian_name: string;
  athlete_person_id: UUID;
  athlete_name: string;
  account_status: string;
  channel: CommunicationChannel;
  destination: string | null;
  portal_url: string;
  message_id: UUID;
  recipient_id: UUID | null;
  delivery_status: string | null;
  dispatch_attempted: number;
  dispatch_sent: number;
  dispatch_delivered: number;
  dispatch_failed: number;
  dispatch_suppressed: number;
  dispatch_queued: number;
  recommended_action: string;
};

export type GuardianPortalInviteBatchRead = {
  organization_id: UUID;
  channel: CommunicationChannel;
  considered: number;
  invited: number;
  skipped_recent: number;
  skipped_no_destination: number;
  skipped_not_ready: number;
  skipped_linked: number;
  dispatch_attempted: number;
  dispatch_delivered: number;
  dispatch_queued: number;
  dispatch_failed: number;
  invites: GuardianPortalInviteRead[];
  skipped: string[];
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

export type FamilyMatchGuidanceRead = {
  athlete_person_id: UUID;
  athlete_name: string;
  relationship: string;
  tracking_run_id: UUID;
  video_asset_id: UUID;
  guidance_message_id: UUID;
  guidance_recipient_id: UUID;
  guidance_published_at: string;
  guidance_delivery_status: string;
  guidance_recipient_count: number;
  opponent_name: string;
  match_label: string | null;
  tracked_at: string;
  track_id: string;
  team_label: string | null;
  player_label: string | null;
  jersey_number: string | null;
  readiness_level: string;
  tracking_quality_score: number;
  distance_m: number;
  high_speed_distance_m: number;
  max_speed_mps: number;
  sprint_count: number;
  work_rate_m_per_min: number;
  dominant_zone: string;
  pressure_applied_count: number;
  off_ball_run_count: number;
  pass_accuracy_percent: number;
  shot_count: number;
  expected_goals: number;
  coaching_flags: string[];
  player_guidance: string[];
  action_plan: Record<string, unknown>[];
  tactical_context: string[];
  quality_warnings: string[];
};

export type FamilyDashboardActionRead = {
  priority: string;
  action_type: string;
  title: string;
  detail: string;
  athlete_person_id: UUID | null;
  event_id: UUID | null;
  consent_request_id: UUID | null;
  due_at: string | null;
};

export type FamilyCoordinationRowRead = {
  key: string;
  athlete_person_id: UUID | null;
  athlete_name: string;
  relationship: string;
  registration_count: number;
  missing_document_count: number;
  pending_consent_count: number;
  rsvp_needed_count: number;
  clearance_blocked_count: number;
  active_goal_count: number;
  ai_recommendation_count: number;
  next_action_label: string;
  next_action_detail: string;
  action_href: string | null;
  urgency_score: number;
};

export type FamilyCoordinationDigestCreate = {
  organization_id: UUID;
  channel: CommunicationChannel;
  portal_url: string;
  dispatch_now?: boolean;
  max_rows?: number;
};

export type FamilyCoordinationDigestRead = {
  organization_id: UUID;
  guardian_person_id: UUID;
  channel: CommunicationChannel;
  message_id: UUID;
  recipient_id: UUID | null;
  delivery_status: string | null;
  action_count: number;
  top_urgency_score: number;
  subject: string;
  body: string;
  dispatch_attempted: number;
  dispatch_sent: number;
  dispatch_delivered: number;
  dispatch_failed: number;
  dispatch_suppressed: number;
  dispatch_queued: number;
};

export type FamilyScheduleConflictRead = {
  starts_at: string;
  ends_at: string;
  athlete_names: string[];
  event_titles: string[];
  event_ids: UUID[];
  recommendation: string;
};

export type FamilyDashboardRead = {
  organization_id: UUID;
  guardian_person_id: UUID;
  generated_at: string;
  child_count: number;
  pending_consent_count: number;
  unread_message_count: number;
  urgent_unread_count: number;
  upcoming_event_count: number;
  rsvp_needed_count: number;
  clearance_blocked_count: number;
  schedule_conflict_count: number;
  active_goal_count: number;
  award_count: number;
  ai_recommendation_count: number;
  open_ai_appeal_count: number;
  next_event_at: string | null;
  next_action_label: string;
  action_items: FamilyDashboardActionRead[];
  schedule_conflicts: FamilyScheduleConflictRead[];
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

export type FacilityBookingRuleRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  min_booking_minutes: number;
  max_booking_minutes: number;
  buffer_minutes: number;
  advance_booking_days: number;
  requires_approval: boolean;
  allow_public_booking: boolean;
  cancellation_notice_hours: number;
  peak_hour_rate_multiplier: string | null;
  public_booking_note: string | null;
  status: string;
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

export type EmergencyEscalationTimerRunRead = {
  organization_id: UUID | null;
  eligible_count: number;
  executed_count: number;
  escalated_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  activation_ids: UUID[];
  max_level_count: number;
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
  adapter_profile: string;
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
  adapter_profile: string;
  sync_attempted: boolean;
  synced: boolean;
  destination: string | null;
  provider_status_code: number | null;
  synced_at: string;
  failure_reason: string | null;
};

export type AssetAccountingExportRow = {
  row_type: string;
  source_id: UUID;
  source_label: string;
  account_code: string;
  memo: string;
  debit: string;
  credit: string;
  currency: string;
  external_reference: string | null;
};

export type AssetAccountingExportRead = {
  organization_id: UUID;
  basis: string;
  system: string;
  rows: AssetAccountingExportRow[];
  debit_total: string;
  credit_total: string;
  supplier_order_count: number;
  lease_schedule_count: number;
  payment_count: number;
};

export type AssetAccountingSyncRead = {
  organization_id: UUID;
  basis: string;
  system: string;
  mode: string;
  delivered: boolean;
  row_count: number;
  debit_total: string;
  credit_total: string;
  sync_reference: string;
  provider_status_code: number | null;
  failure_reason: string | null;
  webhook_configured: boolean;
  synced_at: string;
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
  facility_maintenance_schedule_id: UUID | null;
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

export type FacilityMaintenanceScheduleRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  equipment_item_id: UUID | null;
  assigned_to_person_id: UUID | null;
  title: string;
  category: string;
  frequency: "daily" | "weekly" | "monthly" | "quarterly" | "annual" | "custom";
  interval_days: number;
  next_due_at: string;
  last_generated_at: string | null;
  last_completed_at: string | null;
  vendor: string | null;
  estimated_cost: string | null;
  safety_related: boolean;
  compliance_reference: string | null;
  condition_metric: string | null;
  condition_threshold: string | null;
  warranty_expires_on: string | null;
  status: "active" | "paused" | "retired";
  notes: string | null;
};

export type FacilityMaintenanceScheduleRunRead = {
  schedule: FacilityMaintenanceScheduleRead;
  work_order: MaintenanceWorkOrderRead;
  next_due_at: string;
};

export type FacilityMaintenanceCostRead = {
  facility_id: UUID;
  facility_name: string;
  maintenance_budget: string | null;
  actual_cost: string;
  estimated_open_cost: string;
  net_budget_remaining: string | null;
};

export type FacilityMaintenanceDashboardRead = {
  organization_id: UUID;
  due_count: number;
  overdue_count: number;
  safety_due_count: number;
  maintenance_cost_ytd: string;
  estimated_open_cost: string;
  budget_remaining: string | null;
  upcoming_schedules: FacilityMaintenanceScheduleRead[];
  recent_work_orders: MaintenanceWorkOrderRead[];
  cost_by_facility: FacilityMaintenanceCostRead[];
  recommendation: string;
};

export type FacilityLeaseAgreementRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  finance_invoice_id: UUID | null;
  lessor_name: string;
  lessee_name: string;
  lessee_contact_name: string | null;
  lessee_contact_email: string | null;
  usage_terms: string;
  included_services: string | null;
  extra_charges: string | null;
  starts_on: string;
  ends_on: string;
  monthly_rent: string;
  security_deposit: string | null;
  deposit_status: "not_required" | "due" | "held" | "returned" | "forfeited";
  next_invoice_on: string | null;
  auto_renew: boolean;
  renewal_notice_on: string | null;
  status: "draft" | "active" | "invoicing" | "completed" | "terminated" | "disputed";
  compliance_status: "pending" | "compliant" | "review_required" | "breach" | "waived";
  compliance_notes: string | null;
  document_url: string | null;
  signed_at: string | null;
  terminated_at: string | null;
  version: number;
  notes: string | null;
};

export type FacilityLeaseInvoiceRead = {
  lease: FacilityLeaseAgreementRead;
  invoice: FinanceInvoiceRead;
  period_label: string;
};

export type FacilityAccessCredentialRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  booking_id: UUID | null;
  lease_agreement_id: UUID | null;
  person_id: UUID | null;
  guest_name: string | null;
  guest_email: string | null;
  credential_type: "qr_code" | "mobile_key" | "rfid" | "pin" | "biometric";
  access_code: string;
  access_level: string;
  zones: string | null;
  valid_from: string;
  valid_until: string;
  status: "active" | "paused" | "revoked" | "expired";
  max_uses: number | null;
  uses_count: number;
  last_used_at: string | null;
  issued_by_person_id: UUID | null;
  notes: string | null;
};

export type FacilityAccessEventRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  credential_id: UUID | null;
  booking_id: UUID | null;
  lease_agreement_id: UUID | null;
  access_code: string | null;
  reader_id: string;
  reader_location: string | null;
  subject_summary: string | null;
  decision: "granted" | "denied";
  reason: string;
  occurred_at: string;
  notes: string | null;
};

export type FacilityAccessDashboardRead = {
  organization_id: UUID;
  facility_id: UUID | null;
  active_credentials: number;
  guest_credentials: number;
  grants_last_24h: number;
  denials_last_24h: number;
  recent_events: FacilityAccessEventRead[];
  expiring_credentials: FacilityAccessCredentialRead[];
  recommendation: string;
};

export type FacilityAccessDeviceRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  device_id: string;
  name: string;
  location: string | null;
  device_type: string;
  unlock_method: string;
  status: "active" | "paused" | "maintenance" | "retired";
  last_seen_at: string | null;
  last_scan_at: string | null;
  last_health_at: string | null;
  battery_percent: number | null;
  firmware_version: string | null;
  network_status: string | null;
  notes: string | null;
};

export type FacilityAccessDeviceProvisionRead = {
  device: FacilityAccessDeviceRead;
  api_key: string;
};

export type FacilityAccessCommandRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  access_device_id: UUID;
  access_event_id: UUID | null;
  credential_id: UUID | null;
  command_type: "unlock" | "deny" | string;
  command_payload: string;
  command_signature: string;
  status: "issued" | "acknowledged" | "expired" | string;
  issued_at: string;
  valid_until: string;
  acknowledged_at: string | null;
  requested_by_person_id: UUID | null;
  notes: string | null;
};

export type FacilityAccessGatewayScanRead = {
  device: FacilityAccessDeviceRead;
  event: FacilityAccessEventRead;
  command: FacilityAccessCommandRead | null;
  signature_validated: boolean;
};

export type FacilityAccessDeviceHealthRead = {
  device: FacilityAccessDeviceRead;
  signature_validated: boolean;
  recommendation: string;
};

export type FacilityAccessLockdownRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  mode: "lockdown" | "unlock_all";
  status: "active" | "resolved" | "cancelled";
  reason: string;
  command_count: number;
  activated_at: string;
  resolved_at: string | null;
  issued_by_person_id: UUID | null;
  notes: string | null;
};

export type FacilityAccessLockdownResultRead = {
  lockdown: FacilityAccessLockdownRead;
  commands: FacilityAccessCommandRead[];
  devices_targeted: number;
  recommendation: string;
};

export type FacilityAccessLockdownDashboardRead = {
  organization_id: UUID;
  facility_id: UUID | null;
  active_lockdown_count: number;
  active_device_count: number;
  command_count_last_24h: number;
  recent_lockdowns: FacilityAccessLockdownRead[];
  recent_commands: FacilityAccessCommandRead[];
  recommendation: string;
};

export type FacilityUtilityMeterRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  meter_id: string;
  name: string;
  utility_type: "electricity" | "water" | "gas" | "solar" | "waste" | "other";
  unit: string;
  location: string | null;
  provider: string | null;
  account_reference: string | null;
  status: "active" | "paused" | "maintenance" | "retired";
  cost_per_unit: string | null;
  target_daily_usage: string | null;
  last_reading_at: string | null;
  last_value: string | null;
  last_cost_estimate: string | null;
  notes: string | null;
};

export type FacilityUtilityMeterProvisionRead = {
  meter: FacilityUtilityMeterRead;
  api_key: string;
};

export type FacilityUtilityReadingRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  utility_meter_id: UUID;
  meter_id: string;
  reading_value: string;
  usage_delta: string | null;
  unit: string;
  cost_estimate: string | null;
  reading_at: string;
  source: string;
  anomaly_level: "normal" | "warning" | "critical" | string;
  external_reference: string | null;
  notes: string | null;
};

export type FacilityUtilityAlertRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  utility_meter_id: UUID;
  utility_reading_id: UUID | null;
  alert_type: string;
  severity: "warning" | "critical" | string;
  status: "open" | "acknowledged" | "resolved" | "dismissed";
  message: string;
  recommended_action: string | null;
  triggered_at: string;
  resolved_at: string | null;
  notes: string | null;
};

export type FacilityUtilityReadingResultRead = {
  meter: FacilityUtilityMeterRead;
  reading: FacilityUtilityReadingRead;
  alert: FacilityUtilityAlertRead | null;
  signature_validated: boolean;
};

export type FacilityUtilityDashboardRead = {
  organization_id: UUID;
  facility_id: UUID | null;
  meter_count: number;
  open_alert_count: number;
  total_usage_last_30d: string;
  total_cost_last_30d: string;
  usage_by_type: Record<string, string>;
  recent_readings: FacilityUtilityReadingRead[];
  open_alerts: FacilityUtilityAlertRead[];
  recommendation: string;
};

export type ClubhouseAmenityRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  name: string;
  amenity_type: string;
  location: string | null;
  capacity: number | null;
  reservation_required: boolean;
  hourly_rate: string | null;
  status: "active" | "maintenance" | "closed" | "retired";
  notes: string | null;
};

export type ClubhouseVisitRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  person_id: UUID | null;
  access_event_id: UUID | null;
  guest_name: string | null;
  guest_email: string | null;
  check_in_at: string;
  check_out_at: string | null;
  status: "checked_in" | "checked_out" | "cancelled";
  party_size: number;
  purpose: string | null;
  notes: string | null;
};

export type ClubhouseAmenityReservationRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  amenity_id: UUID;
  person_id: UUID | null;
  guest_name: string | null;
  starts_at: string;
  ends_at: string;
  status: "reserved" | "checked_in" | "completed" | "cancelled" | "no_show";
  party_size: number;
  expected_fee: string | null;
  notes: string | null;
};

export type ClubhouseDashboardRead = {
  organization_id: UUID;
  facility_id: UUID | null;
  current_occupancy: number;
  capacity: number | null;
  capacity_remaining: number | null;
  active_member_visits: number;
  active_guest_visits: number;
  amenity_count: number;
  reservations_today: number;
  expected_revenue_today: string;
  active_visits: ClubhouseVisitRead[];
  upcoming_reservations: ClubhouseAmenityReservationRead[];
  popular_amenities: string[];
  recommendation: string;
};

export type ClubhouseMenuItemRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  name: string;
  category: string;
  description: string | null;
  unit_price: string;
  unit_cost: string | null;
  stock_quantity: number | null;
  reorder_point: number;
  nutrition_summary: string | null;
  dietary_tags: string | null;
  taxable: boolean;
  status: "active" | "sold_out" | "paused" | "retired";
  notes: string | null;
};

export type ClubhousePOSOrderLineRead = {
  id: UUID;
  organization_id: UUID;
  order_id: UUID;
  menu_item_id: UUID;
  item_name: string;
  quantity: number;
  unit_price: string;
  line_total: string;
  notes: string | null;
};

export type ClubhousePOSOrderRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  visit_id: UUID | null;
  reservation_id: UUID | null;
  person_id: UUID | null;
  guest_name: string | null;
  guest_email: string | null;
  order_type: "counter" | "mobile" | "table" | "delivery";
  table_label: string | null;
  pickup_location: string | null;
  status: "placed" | "preparing" | "ready" | "completed" | "paid" | "cancelled";
  subtotal: string;
  tax_total: string;
  total: string;
  currency: string;
  payment_method: string;
  ordered_at: string;
  fulfilled_at: string | null;
  paid_at: string | null;
  finance_invoice_id: UUID | null;
  finance_payment_id: UUID | null;
  notes: string | null;
  lines: ClubhousePOSOrderLineRead[];
};

export type ClubhousePOSDashboardRead = {
  organization_id: UUID;
  facility_id: UUID | null;
  open_order_count: number;
  ready_order_count: number;
  completed_order_count_today: number;
  revenue_today: string;
  low_stock_count: number;
  popular_items: string[];
  open_orders: ClubhousePOSOrderRead[];
  low_stock_items: ClubhouseMenuItemRead[];
  recommendation: string;
};

export type ClubhouseOperationsChecklistItemRead = {
  id: UUID;
  organization_id: UUID;
  checklist_id: UUID;
  label: string;
  area: string | null;
  category: string;
  priority: "low" | "medium" | "high" | "critical" | string;
  status: "pending" | "done" | "issue" | "blocked" | "skipped" | string;
  due_at: string | null;
  completed_at: string | null;
  assigned_to_person_id: UUID | null;
  work_order_id: UUID | null;
  evidence_url: string | null;
  notes: string | null;
};

export type ClubhouseOperationsChecklistRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  checklist_type: "opening" | "midday" | "closing" | "cleaning" | "safety" | "custom" | string;
  title: string;
  scheduled_for: string;
  status: "open" | "in_progress" | "completed" | "blocked" | "cancelled" | string;
  assigned_to_person_id: UUID | null;
  completed_at: string | null;
  score: number | null;
  notes: string | null;
  items: ClubhouseOperationsChecklistItemRead[];
};

export type ClubhouseOperationsDashboardRead = {
  organization_id: UUID;
  facility_id: UUID | null;
  open_checklist_count: number;
  blocked_item_count: number;
  issue_item_count: number;
  completed_today: number;
  average_score: number | null;
  open_checklists: ClubhouseOperationsChecklistRead[];
  blocked_items: ClubhouseOperationsChecklistItemRead[];
  recommendation: string;
};

export type ClubhouseEventGuestRead = {
  id: UUID;
  organization_id: UUID;
  clubhouse_event_id: UUID;
  person_id: UUID | null;
  guest_name: string;
  guest_email: string | null;
  party_size: number;
  rsvp_status: "invited" | "confirmed" | "declined" | "checked_in" | "no_show" | string;
  checked_in_at: string | null;
  notes: string | null;
};

export type ClubhouseEventRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  amenity_id: UUID | null;
  title: string;
  event_type: string;
  starts_at: string;
  ends_at: string;
  expected_attendees: number;
  status: "planning" | "tentative" | "confirmed" | "active" | "completed" | "cancelled" | string;
  budget_amount: string | null;
  revenue_target: string | null;
  actual_revenue: string;
  vendor_notes: string | null;
  catering_notes: string | null;
  staffing_notes: string | null;
  run_sheet: string | null;
  post_event_summary: string | null;
  notes: string | null;
  guests: ClubhouseEventGuestRead[];
};

export type ClubhouseServiceOfferingRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  name: string;
  service_type: string;
  description: string | null;
  price: string;
  billing_period: "once" | "visit" | "monthly" | "season" | "annual" | string;
  capacity_per_slot: number | null;
  status: "active" | "paused" | "retired" | string;
  notes: string | null;
};

export type ClubhouseServiceBookingRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  service_id: UUID;
  person_id: UUID | null;
  guest_name: string | null;
  starts_at: string | null;
  ends_at: string | null;
  status: "booked" | "active" | "completed" | "cancelled" | "no_show" | string;
  amount: string;
  finance_invoice_id: UUID | null;
  notes: string | null;
};

export type ClubhouseFeedbackRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  amenity_id: UUID | null;
  person_id: UUID | null;
  guest_name: string | null;
  category: string;
  rating: number;
  subject: string;
  message: string;
  status: "open" | "reviewing" | "resolved" | "dismissed" | string;
  response: string | null;
  submitted_at: string;
  resolved_at: string | null;
};

export type ClubhouseBusinessDashboardRead = {
  organization_id: UUID;
  facility_id: UUID | null;
  event_count: number;
  confirmed_event_count: number;
  service_booking_count: number;
  open_feedback_count: number;
  average_feedback_rating: string | null;
  projected_event_revenue: string;
  actual_event_revenue: string;
  service_revenue: string;
  pos_revenue: string;
  total_revenue: string;
  upcoming_events: ClubhouseEventRead[];
  open_feedback: ClubhouseFeedbackRead[];
  recommendation: string;
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
  finance_invoice_id: UUID | null;
  insurance_certificate_ref: string | null;
  special_requirements: string | null;
  access_code: string | null;
  public_visible: boolean;
  recurrence_group_id: string | null;
  occurrence_index: number | null;
  booking_source: string;
  public_booking_reference: string | null;
  payment_status: string;
  payment_checkout_url: string | null;
  access_starts_at: string | null;
  access_ends_at: string | null;
  conflict_note: string | null;
};

export type FacilityAvailabilitySlotRead = {
  starts_at: string;
  ends_at: string;
  status: string;
  booking_id: UUID | null;
  title: string | null;
  conflict_note: string | null;
};

export type FacilityAvailabilityRead = {
  organization_id: UUID;
  facility_id: UUID;
  starts_at: string;
  ends_at: string;
  rule: FacilityBookingRuleRead | null;
  slots: FacilityAvailabilitySlotRead[];
  conflict_count: number;
};

export type FacilityUtilizationRead = {
  organization_id: UUID;
  facility_id: UUID;
  starts_at: string;
  ends_at: string;
  available_hours: number;
  booked_hours: number;
  utilization_percent: number;
  booking_count: number;
  projected_revenue: string;
  average_attendance: number | null;
  recommendation: string;
};

export type FacilityPublicListingRead = FacilityRead & {
  rule: FacilityBookingRuleRead;
  availability: FacilityAvailabilityRead;
  public_rate: string;
  rate_summary: string;
  next_available_slot: string | null;
};

export type FacilityBookingCheckoutRead = {
  booking: FacilityBookingRead;
  invoice: FinanceInvoiceRead;
  checkout_url: string;
  session_id: string;
  access_window_summary: string;
};

export type FacilityBookingWaitlistRead = {
  id: UUID;
  organization_id: UUID;
  facility_id: UUID;
  offered_booking_id: UUID | null;
  activity_type: string;
  title: string;
  desired_starts_at: string;
  desired_ends_at: string;
  requester_name: string;
  requester_email: string;
  requester_phone: string | null;
  expected_attendees: number | null;
  insurance_certificate_ref: string | null;
  special_requirements: string | null;
  add_ons: string | null;
  notes: string | null;
  status: "pending" | "offered" | "converted" | "declined" | "cancelled";
  priority_score: number;
  notified_at: string | null;
  expires_at: string | null;
};

export type FacilityHireHostedCheckoutRead = {
  invoice_id: UUID;
  booking_id: UUID;
  invoice_number: string;
  organization_id: UUID;
  facility_id: UUID;
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

export type FacilityHireCheckoutSettlementRead = {
  booking_id: UUID;
  invoice_id: UUID;
  payment_id: UUID | null;
  provider: string;
  amount_paid: string;
  open_amount: string;
  currency: string;
  invoice_status: string;
  booking_status: FacilityBookingStatus;
  payment_status: string;
  session_status: string;
  access_code: string | null;
  access_starts_at: string | null;
  access_ends_at: string | null;
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

export type SponsorshipDeliverableMilestoneRead = {
  id: UUID;
  organization_id: UUID;
  sponsor_id: UUID;
  sponsorship_agreement_id: UUID;
  title: string;
  deliverable_type: string;
  due_on: string | null;
  completed_on: string | null;
  status: string;
  owner_name: string | null;
  evidence_url: string | null;
  notes: string | null;
  sponsor_name: string | null;
  agreement_name: string | null;
};

export type SponsorInteractionRead = {
  id: UUID;
  organization_id: UUID;
  sponsor_id: UUID;
  sponsorship_agreement_id: UUID | null;
  sponsor_name: string | null;
  agreement_name: string | null;
  contact_name: string;
  contact_email: string | null;
  interaction_type: string;
  subject: string;
  summary: string;
  sentiment: string;
  follow_up_on: string | null;
  occurred_at: string;
};

export type SponsorRenewalForecastRead = {
  sponsor_id: UUID;
  sponsor_name: string;
  active_value: string;
  renewal_score: number;
  renewal_signal: string;
  milestone_count: number;
  completed_milestone_count: number;
  overdue_milestone_count: number;
  upcoming_milestone_count: number;
  interaction_count: number;
  last_interaction_at: string | null;
  next_best_action: string;
};

export type SponsorStewardshipDashboardRead = {
  organization_id: UUID;
  sponsor_count: number;
  milestone_count: number;
  overdue_milestone_count: number;
  interaction_count: number;
  follow_up_due_count: number;
  forecasts: SponsorRenewalForecastRead[];
  recommendations: string[];
};

export type SponsorActivationCampaignRead = {
  id: UUID;
  organization_id: UUID;
  sponsor_id: UUID;
  sponsorship_agreement_id: UUID | null;
  fan_challenge_id: UUID | null;
  title: string;
  objective: string;
  offer_summary: string;
  coupon_code: string;
  discount_type: string;
  discount_value: string;
  target_url: string | null;
  starts_at: string | null;
  ends_at: string | null;
  status: CommercialStatus;
  sponsor_name: string | null;
  challenge_title: string | null;
  impression_count: number;
  signup_count: number;
  redemption_count: number;
  conversion_value: string;
};

export type SponsorCouponRedemptionRead = {
  id: UUID;
  organization_id: UUID;
  activation_campaign_id: UUID;
  coupon_code: string;
  sponsor_name: string | null;
  supporter_profile_id: UUID | null;
  redeemer_name: string;
  redeemer_email: string;
  source: string;
  order_reference: string | null;
  discount_amount: string;
  purchase_amount: string;
  status: CommercialStatus;
  redeemed_at: string;
};

export type SponsorActivationDashboardRead = {
  organization_id: UUID;
  campaign_count: number;
  active_campaign_count: number;
  total_impressions: number;
  total_signups: number;
  total_redemptions: number;
  conversion_value: string;
  top_coupon_code: string | null;
  roi_signal: string;
  recommendations: string[];
};

export type SponsorContentAssetRead = {
  id: UUID;
  organization_id: UUID;
  sponsor_id: UUID;
  sponsorship_agreement_id: UUID | null;
  title: string;
  asset_type: string;
  channel: string;
  format: string;
  asset_url: string;
  thumbnail_url: string | null;
  usage_guidelines: string | null;
  rights_summary: string | null;
  player_rights_required: boolean;
  expires_at: string | null;
  version: number;
  sponsor_name: string | null;
  approval_status: string;
  approved_at: string | null;
  approved_by_name: string | null;
  usage_count: number;
  impression_count: number;
  engagement_count: number;
};

export type SponsorContentApprovalRead = {
  id: UUID;
  organization_id: UUID;
  content_asset_id: UUID;
  reviewer_name: string;
  reviewer_email: string | null;
  decision: string;
  notes: string | null;
  content_title: string | null;
  decided_at: string;
};

export type SponsorActivationPlacementRead = {
  id: UUID;
  organization_id: UUID;
  sponsor_id: UUID;
  content_asset_id: UUID | null;
  activation_campaign_id: UUID | null;
  event_id: UUID | null;
  placement_name: string;
  placement_type: string;
  channel: string;
  scheduled_at: string | null;
  location_name: string | null;
  staff_requirements: string | null;
  inventory_checklist: string | null;
  weather_contingency: string | null;
  expected_impressions: number;
  notes: string | null;
  sponsor_name: string | null;
  content_title: string | null;
  campaign_title: string | null;
  event_title: string | null;
  status: string;
  actual_impressions: number;
  actual_engagements: number;
};

export type SponsorDigitalSignagePlaylistItemRead = {
  slot_index: number;
  duration_seconds: number;
  placement_id: UUID;
  sponsor_id: UUID;
  sponsor_name: string | null;
  content_asset_id: UUID | null;
  content_title: string;
  asset_url: string | null;
  thumbnail_url: string | null;
  format: string;
  placement_name: string;
  placement_type: string;
  channel: string;
  location_name: string | null;
  event_id: UUID | null;
  event_title: string | null;
  scheduled_at: string | null;
  campaign_title: string | null;
  coupon_code: string | null;
  target_url: string | null;
  rights_status: string;
  expected_impressions: number;
  warnings: string[];
};

export type SponsorDigitalSignagePlaylistRead = {
  organization_id: UUID;
  screen_name: string;
  location_name: string | null;
  event_id: UUID | null;
  generated_at: string;
  slot_count: number;
  total_duration_seconds: number;
  approved_slot_count: number;
  review_required_count: number;
  rotation_policy: string;
  items: SponsorDigitalSignagePlaylistItemRead[];
  warnings: string[];
};

export type SponsorDigitalSignagePlaybackRead = {
  organization_id: UUID;
  placement: SponsorActivationPlacementRead;
  content_asset: SponsorContentAssetRead | null;
  activation_campaign: SponsorActivationCampaignRead | null;
  screen_name: string;
  device_id: string | null;
  slot_index: number;
  played_at: string;
  duration_seconds: number;
  estimated_impressions: number;
  engagements: number;
  playback_status: string;
  evidence_ref: string | null;
  message: string;
};

export type SponsorContentDashboardRead = {
  organization_id: UUID;
  asset_count: number;
  approved_asset_count: number;
  pending_asset_count: number;
  expiring_asset_count: number;
  placement_count: number;
  planned_placement_count: number;
  total_expected_impressions: number;
  total_actual_impressions: number;
  recommendations: string[];
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

export type GrantOpportunityRead = {
  id: UUID;
  organization_id: UUID;
  funder_name: string;
  program_name: string;
  category: string;
  impact_area: string;
  award_ceiling: string;
  matching_required: string;
  currency: string;
  opens_on: string | null;
  due_on: string | null;
  eligibility_summary: string | null;
  requirements: string | null;
  source_url: string | null;
  status: string;
};

export type GrantApplicationRead = {
  id: UUID;
  organization_id: UUID;
  grant_opportunity_id: UUID;
  project_title: string;
  requested_amount: string;
  awarded_amount: string;
  currency: string;
  status: string;
  submitted_on: string | null;
  decision_on: string | null;
  reporting_due_on: string | null;
  lead_person_id: UUID | null;
  narrative: string | null;
  budget_summary: string | null;
  impact_metrics: string | null;
  external_reference: string | null;
  funder_name: string | null;
  program_name: string | null;
};

export type GrantReportRead = {
  id: UUID;
  organization_id: UUID;
  grant_application_id: UUID;
  report_type: string;
  due_on: string;
  submitted_on: string | null;
  status: string;
  narrative: string | null;
  metrics_summary: string | null;
  artifact_url: string | null;
  external_reference: string | null;
  project_title: string | null;
};

export type GrantDashboardRead = {
  organization_id: UUID;
  opportunity_count: number;
  active_opportunity_count: number;
  application_count: number;
  submitted_application_count: number;
  awarded_application_count: number;
  report_count: number;
  due_soon_count: number;
  overdue_report_count: number;
  requested_amount: string;
  awarded_amount: string;
  match_required_amount: string;
  readiness_score: number;
  pipeline_status: string;
  recommendations: string[];
  next_deadline_on: string | null;
};

export type MerchandiseProductRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  name: string;
  sku: string;
  category: string;
  description: string | null;
  price: string;
  cost: string;
  currency: string;
  inventory_count: number;
  reorder_point: number;
  personalization_enabled: boolean;
  variants: string | null;
  image_url: string | null;
  status: CommercialStatus;
};

export type MerchandiseOrderLineRead = {
  id: UUID;
  organization_id: UUID;
  merchandise_order_id: UUID;
  merchandise_product_id: UUID;
  product_name: string | null;
  sku: string | null;
  quantity: number;
  unit_price: string;
  line_total: string;
  size: string | null;
  color: string | null;
  personalization_name: string | null;
  personalization_number: string | null;
  fulfillment_status: string;
};

export type MerchandiseOrderRead = {
  id: UUID;
  organization_id: UUID;
  buyer_person_id: UUID | null;
  buyer_name: string;
  buyer_email: string;
  delivery_method: string;
  delivery_address: string | null;
  total_amount: string;
  currency: string;
  external_payment_reference: string | null;
  status: CommercialStatus;
  fulfillment_status: string;
  fulfilled_at: string | null;
  notes: string | null;
  lines: MerchandiseOrderLineRead[];
};

export type MerchandiseStoreDashboardRead = {
  organization_id: UUID;
  product_count: number;
  active_product_count: number;
  low_stock_count: number;
  order_count: number;
  queued_order_count: number;
  fulfilled_order_count: number;
  units_sold: number;
  gross_revenue: string;
  estimated_margin: string;
  recommendations: string[];
};

export type CommunityPostRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  author_person_id: UUID | null;
  title: string;
  body: string;
  post_type: string;
  visibility: string;
  media_url: string | null;
  pinned: boolean;
  status: string;
  published_at: string;
  comment_count: number;
  reaction_count: number;
  poll_count: number;
};

export type CommunityCommentRead = {
  id: UUID;
  organization_id: UUID;
  post_id: UUID;
  author_person_id: UUID | null;
  body: string;
  status: string;
  created_at: string;
};

export type CommunityModerationItemRead = {
  id: UUID;
  item_type: string;
  organization_id: UUID;
  post_id: UUID | null;
  title: string | null;
  body: string;
  status: string;
  risk_score: number;
  risk_reasons: string[];
  created_at: string;
};

export type CommunityModerationQueueRead = {
  organization_id: UUID;
  review_count: number;
  hidden_count: number;
  rejected_count: number;
  items: CommunityModerationItemRead[];
};

export type CommunitySocialShareChannelRead = {
  channel: string;
  text: string;
  url: string;
  character_count: number;
  hashtags: string[];
};

export type CommunitySocialSharePackageRead = {
  post_id: UUID;
  organization_id: UUID;
  title: string;
  status: string;
  public_url: string;
  risk_score: number;
  risk_reasons: string[];
  channels: CommunitySocialShareChannelRead[];
};

export type CommunityReactionRead = {
  id: UUID;
  organization_id: UUID;
  post_id: UUID;
  person_id: UUID;
  reaction_type: string;
  created_at: string;
};

export type FanPollOptionRead = {
  id: UUID;
  poll_id: UUID;
  label: string;
  sequence: number;
  vote_count: number;
};

export type FanPollRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  post_id: UUID | null;
  question: string;
  audience: string;
  status: string;
  closes_at: string | null;
  total_votes: number;
  options: FanPollOptionRead[];
};

export type FanPollVoteRead = {
  id: UUID;
  organization_id: UUID;
  poll_id: UUID;
  option_id: UUID;
  person_id: UUID;
  created_at: string;
};

export type CommunityEngagementSummaryRead = {
  organization_id: UUID;
  post_count: number;
  pinned_post_count: number;
  comment_count: number;
  reaction_count: number;
  poll_count: number;
  open_poll_count: number;
  vote_count: number;
  engagement_score: number;
  recommendations: string[];
};

export type SupporterMembershipTierRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  slug: string;
  monthly_price: string;
  currency: string;
  benefits: string;
  voting_weight: number;
  trial_days: number;
  status: string;
};

export type SupporterProfileRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID | null;
  tier_id: UUID | null;
  display_name: string;
  email: string;
  lifetime_value: string;
  notes: string | null;
  engagement_points: number;
  status: string;
  joined_at: string;
  last_engagement_at: string | null;
  tier_name: string | null;
  tier_voting_weight: number | null;
};

export type SupporterEngagementActivityRead = {
  id: UUID;
  organization_id: UUID;
  supporter_profile_id: UUID;
  activity_type: string;
  source: string;
  description: string;
  points: number;
  value_amount: string;
  occurred_at: string;
};

export type SupporterRewardRead = {
  id: UUID;
  organization_id: UUID;
  supporter_profile_id: UUID;
  title: string;
  reward_type: string;
  threshold_points: number;
  status: string;
  redeemed_at: string | null;
};

export type FanEngagementChallengeRead = {
  id: UUID;
  organization_id: UUID;
  title: string;
  description: string;
  challenge_type: string;
  target_activity_type: string;
  target_count: number;
  points_reward: number;
  badge_name: string | null;
  starts_at: string | null;
  ends_at: string | null;
  status: string;
  completion_count: number;
};

export type FanChallengeProgressRead = {
  id: UUID;
  organization_id: UUID;
  challenge_id: UUID;
  supporter_profile_id: UUID;
  supporter_name: string | null;
  progress_count: number;
  points_awarded: number;
  status: string;
  completed_at: string | null;
};

export type FanLeaderboardEntryRead = {
  rank: number;
  supporter_profile_id: UUID;
  supporter_name: string;
  tier_name: string | null;
  engagement_points: number;
  lifetime_value: string;
  reward_count: number;
  completed_challenge_count: number;
};

export type SupporterDashboardRead = {
  organization_id: UUID;
  tier_count: number;
  supporter_count: number;
  active_supporter_count: number;
  total_points: number;
  total_lifetime_value: string;
  reward_count: number;
  challenge_count: number;
  completed_challenge_count: number;
  top_supporter_name: string | null;
  recommendations: string[];
};

export type AlumniProfileRead = {
  id: UUID;
  organization_id: UUID;
  person_id: UUID | null;
  display_name: string;
  email: string;
  graduation_year: number | null;
  sports_history: string;
  career_industry: string | null;
  current_company: string | null;
  current_role: string | null;
  linkedin_url: string | null;
  engagement_level: string;
  lifetime_donations: string;
  privacy_status: string;
  last_engagement_at: string | null;
  notes: string | null;
};

export type MentorshipProgramRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  goals: string;
  industry_focus: string | null;
  capacity: number;
  starts_on: string | null;
  ends_on: string | null;
  status: string;
  match_count: number;
};

export type MentorshipMatchRead = {
  id: UUID;
  organization_id: UUID;
  program_id: UUID;
  alumni_profile_id: UUID;
  alumni_name: string | null;
  mentee_person_id: UUID | null;
  mentee_name: string;
  mentee_interest: string;
  match_score: number;
  goals: string;
  status: string;
  next_meeting_at: string | null;
  feedback_notes: string | null;
};

export type AlumniDashboardRead = {
  organization_id: UUID;
  alumni_count: number;
  active_alumni_count: number;
  mentorship_program_count: number;
  mentorship_match_count: number;
  lifetime_donations: string;
  mentor_capacity: number;
  recommendations: string[];
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

export type TicketBundleOfferRead = {
  id: UUID;
  organization_id: UUID;
  event_id: UUID;
  ticket_product_id: UUID;
  merchandise_product_id: UUID | null;
  name: string;
  package_type: string;
  ticket_quantity: number;
  price: string;
  currency: string;
  channel: string;
  sales_limit: number | null;
  starts_at: string | null;
  ends_at: string | null;
  ticket_product_name: string | null;
  merchandise_product_name: string | null;
  sold_count: number;
  status: CommercialStatus;
};

export type TicketSeatAssignmentRead = {
  id: UUID;
  organization_id: UUID;
  ticket_id: UUID;
  event_id: UUID;
  section: string;
  row: string | null;
  seat: string | null;
  access_zone: string | null;
  accessible: boolean;
  companion_seat: boolean;
  holder_name: string | null;
  ticket_status: TicketStatus | null;
  assigned_at: string;
};

export type TicketResaleListingRead = {
  id: UUID;
  organization_id: UUID;
  event_id: UUID;
  ticket_id: UUID;
  seller_name: string;
  seller_email: string;
  resale_price: string;
  currency: string;
  status: string;
  buyer_name: string | null;
  buyer_email: string | null;
  listed_at: string;
  sold_at: string | null;
  notes: string | null;
};

export type TicketAccessDashboardRead = {
  organization_id: UUID;
  ticket_product_count: number;
  ticket_count: number;
  checked_in_count: number;
  complimentary_count: number;
  assigned_seat_count: number;
  accessible_seat_count: number;
  resale_listing_count: number;
  resale_sold_count: number;
  package_offer_count: number;
  recommendations: string[];
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

export type CommercialTaxFilingRead = {
  organization_id: UUID;
  jurisdiction: string;
  period_start: string;
  period_end: string;
  invoice_count: number;
  taxable_subtotal: string;
  tax_rate: string;
  tax_amount: string;
  gross_total: string;
  outstanding_total: string;
  currency: string;
  reverse_charge: boolean;
  filing_reference: string;
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  destination: string | null;
  provider_status_code: number | null;
  failure_reason: string | null;
  filed_at: string;
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

export type CommercialSettlementPayoutRead = {
  id: UUID | null;
  organization_id: UUID;
  provider: string;
  currency: string;
  status: string;
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  payout_reference: string;
  payout_batch_reference: string;
  idempotency_key: string;
  gross_amount: string;
  fee_amount: string;
  net_amount: string;
  line_count: number;
  destination: string | null;
  provider_status_code: number | null;
  provider_response: string | null;
  failure_reason: string | null;
  processed_by_person_id: UUID | null;
  executed_at: string;
  reconciled_at: string | null;
  external_event_id: string | null;
};

export type CommercialSettlementPayoutCallbackRead = {
  accepted: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  matched_by: string;
  payout_reference: string;
  payout_batch_reference: string;
  payout_status: string;
  message: string;
  payout: CommercialSettlementPayoutRead;
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

export type AccountingSyncRead = {
  organization_id: UUID;
  basis: string;
  system: string;
  mode: string;
  delivered: boolean;
  row_count: number;
  debit_total: string;
  credit_total: string;
  sync_reference: string;
  provider_status_code: number | null;
  failure_reason: string | null;
  webhook_configured: boolean;
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

export type SponsorPortalSponsorRead = {
  id: UUID;
  organization_id: UUID;
  organization_name: string;
  organization_slug: string;
  sponsor_name: string;
  industry: string | null;
  contact_name: string | null;
  contact_email: string | null;
  website_url: string | null;
  brand_assets_url: string | null;
  public_site_path: string;
};

export type SponsorPortalAgreementRead = {
  id: UUID;
  organization_id: UUID;
  organization_name: string;
  sponsor_id: UUID;
  sponsor_name: string;
  event_id: UUID | null;
  event_title: string | null;
  event_starts_at: string | null;
  event_venue_name: string | null;
  name: string;
  tier: string;
  value_amount: string;
  currency: string;
  starts_on: string | null;
  ends_on: string | null;
  deliverables: string[];
  activation_notes: string | null;
  roi_notes: string | null;
  status: CommercialStatus;
};

export type SponsorPortalInvoiceRead = {
  id: UUID;
  organization_id: UUID;
  organization_name: string;
  sponsor_id: UUID;
  invoice_number: string;
  title: string;
  amount_due: string;
  amount_paid: string;
  outstanding_amount: string;
  currency: string;
  due_on: string | null;
  status: CommercialStatus;
  memo: string | null;
  payment_session_id: string | null;
  payment_session_url: string | null;
  payment_session_status: string | null;
};

export type SponsorPortalSummaryRead = {
  sponsor_count: number;
  agreement_count: number;
  active_value: string;
  outstanding_invoice_amount: string;
  deliverable_count: number;
  activation_count: number;
  upcoming_event_count: number;
  recommendation: string;
};

export type SponsorPortalRead = {
  identity_email: string;
  sponsors: SponsorPortalSponsorRead[];
  agreements: SponsorPortalAgreementRead[];
  invoices: SponsorPortalInvoiceRead[];
  summary: SponsorPortalSummaryRead;
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
  dunning_count: number;
  dunning_last_sent_at: string | null;
  dunning_last_severity: string | null;
  late_fee_total: string;
  late_fee_count: number;
  late_fee_last_applied_on: string | null;
  payment_retry_count: number;
  payment_retry_last_attempted_at: string | null;
  payment_retry_next_attempt_at: string | null;
  payment_retry_last_status: string | null;
  payment_retry_last_failure_reason: string | null;
  payment_retry_last_provider_reference: string | null;
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

export type SaaSInvoiceHostedCheckoutRead = {
  invoice_id: UUID;
  invoice_number: string;
  organization_id: UUID;
  subscription_id: UUID;
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

export type SaaSInvoiceCheckoutLinkRead = {
  invoice_id: UUID;
  provider: string;
  session_id: string;
  checkout_url: string;
  hosted_checkout: SaaSInvoiceHostedCheckoutRead;
};

export type SaaSInvoiceCheckoutSettlementRead = {
  invoice_id: UUID;
  provider: string;
  accepted: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  payment_id: UUID | null;
  invoice_status: BillingInvoiceStatus;
  amount_paid: string;
  open_amount: string;
  session_status: string;
  message: string;
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

export type BillingSubscriptionLifecycleRead = {
  organization_id: UUID;
  subscription_id: UUID;
  action: string;
  previous_status: SubscriptionStatus;
  status: SubscriptionStatus;
  cancel_at_period_end: boolean;
  effective_on: string;
  message: string;
  subscription: SubscriptionRead;
};

export type BillingEntitlementEnforcementItemRead = {
  entitlement_id: UUID;
  subscription_id: UUID;
  feature_key: string;
  previous_status: string;
  status: string;
  limit_value: number | null;
  used_value: number;
  remaining_value: number | null;
  subscription_status: SubscriptionStatus;
  action: string;
  reason: string;
  changed: boolean;
};

export type BillingEntitlementEnforcementRead = {
  organization_id: UUID;
  subscription_id: UUID | null;
  as_of: string;
  dry_run: boolean;
  checked_count: number;
  would_update_count: number;
  updated_count: number;
  blocked_count: number;
  over_limit_count: number;
  active_count: number;
  items: BillingEntitlementEnforcementItemRead[];
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

export type BillingDunningRunRead = {
  organization_id: UUID | null;
  overdue_as_of: string;
  eligible_count: number;
  executed_count: number;
  notice_count: number;
  delivered_count: number;
  record_only_count: number;
  past_due_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  invoice_ids: UUID[];
  subscription_ids: UUID[];
  total_outstanding: string;
  severity_counts: Record<string, number>;
};

export type BillingLateFeeRunRead = {
  organization_id: UUID | null;
  apply_on: string;
  eligible_count: number;
  executed_count: number;
  fee_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  invoice_ids: UUID[];
  subscription_ids: UUID[];
  total_late_fees: string;
};

export type BillingPaymentRetryRunRead = {
  organization_id: UUID | null;
  retry_at: string;
  eligible_count: number;
  executed_count: number;
  retry_count: number;
  succeeded_count: number;
  submitted_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  delivery_mode: string;
  invoice_ids: UUID[];
  subscription_ids: UUID[];
  total_attempted: string;
  total_collected: string;
  status_counts: Record<string, number>;
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

export type BillingRecurringInvoiceRunRead = {
  organization_id: UUID | null;
  bill_on: string;
  eligible_count: number;
  executed_count: number;
  invoiced_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  invoice_ids: UUID[];
  subscription_ids: UUID[];
  total_invoiced: string;
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

export type DeveloperOAuthAuthorizationCreate = {
  organization_id: UUID;
  client_id: string;
  redirect_uri: string;
  scopes: string[];
  state?: string | null;
  code_challenge?: string | null;
  code_challenge_method?: string | null;
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

export type DeveloperSdkEndpointCatalogRead = {
  method: string;
  path: string;
  category: string;
  summary: string;
  required_scopes: string[];
  typescript_entry_point: string | null;
  python_entry_point: string | null;
  webhook_events: string[];
};

export type DeveloperProviderCallbackCatalogRead = {
  method: string;
  path: string;
  category: string;
  description: string;
  auth_headers: string[];
  replay_key_fields: string[];
  payload_fields: string[];
  example_payload: Record<string, unknown>;
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
  sdk_endpoints: DeveloperSdkEndpointCatalogRead[];
  provider_callbacks: DeveloperProviderCallbackCatalogRead[];
  configured_event_types: string[];
};

export type DeveloperPublicDocsRead = {
  title: string;
  version: string;
  search_query: string | null;
  search_result_count: number;
  api_base_path: string;
  authentication: string;
  auth_header: string;
  webhook_signature_header: string;
  webhook_timestamp_header: string;
  quickstarts: DeveloperQuickstartRead[];
  scopes: DeveloperApiScopeCatalogRead[];
  webhook_events: DeveloperWebhookEventCatalogRead[];
  sdks: DeveloperSdkCatalogRead[];
  sdk_endpoints: DeveloperSdkEndpointCatalogRead[];
  provider_callbacks: DeveloperProviderCallbackCatalogRead[];
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

export type SafeguardingIncidentInvestigationActionRead = {
  incident_id: UUID;
  organization_id: UUID;
  action_type: string;
  status: SafeguardingIncidentStatus;
  severity: SafeguardingIncidentSeverity;
  assigned_to_person_id: UUID | null;
  regulatory_report_required: boolean;
  medical_follow_up_required: string;
  action_summary: string;
  resolution_notes: string | null;
  actioned_at: string;
};

export type SafeguardingIncidentEvidenceUploadRead = {
  incident_id: UUID;
  organization_id: UUID;
  filename: string;
  content_type: string;
  evidence_type: string;
  review_status: string;
  size_bytes: number;
  checksum: string;
  evidence_url: string;
  storage_key: string;
  uploaded_at: string;
  incident: SafeguardingIncidentRead;
};

export type SafeguardingIncidentEvidenceLinkRead = {
  incident_id: UUID;
  organization_id: UUID;
  signed_url: string;
  expires_at: string;
  filename: string;
  content_type: string;
  checksum: string;
  size_bytes: number;
  evidence_url: string;
  storage_key: string;
};

export type SafeguardingIncidentEvidenceApprovalPolicyRead = {
  incident_id: UUID;
  organization_id: UUID;
  incident_title: string;
  incident_status: SafeguardingIncidentStatus;
  incident_severity: SafeguardingIncidentSeverity;
  filename: string;
  content_type: string;
  evidence_type: string;
  review_status: string;
  policy_risk_level: string;
  approval_required: boolean;
  approval_status: string;
  required_approval_levels: string[];
  missing_approval_levels: string[];
  recommended_review_status: string;
  acceptance_blocked_by_policy: boolean;
  policy_summary: string;
  rationale: string[];
  matched_rule_codes: string[];
};

export type SafeguardingEvidencePolicyRuleRead = {
  id: UUID;
  organization_id: UUID;
  rule_code: string;
  title: string;
  active: boolean;
  incident_type: SafeguardingIncidentType | null;
  minimum_severity: SafeguardingIncidentSeverity | null;
  evidence_type_contains: string | null;
  medical_follow_up_values: string | null;
  regulatory_required: boolean | null;
  athlete_linked_required: boolean | null;
  required_approval_level: string;
  risk_level: string;
  recommended_review_status: string;
  block_acceptance: boolean;
  rationale: string;
  created_at: string;
  updated_at: string;
};

export type SafeguardingIncidentEvidenceReviewItemRead = {
  incident_id: UUID;
  organization_id: UUID;
  incident_title: string;
  incident_status: SafeguardingIncidentStatus;
  incident_severity: SafeguardingIncidentSeverity;
  filename: string;
  content_type: string;
  evidence_type: string;
  review_status: string;
  size_bytes: number;
  checksum: string;
  evidence_url: string;
  storage_key: string;
  uploaded_at: string;
  latest_reviewed_at: string | null;
  latest_review_notes: string | null;
  approval_policy: SafeguardingIncidentEvidenceApprovalPolicyRead | null;
};

export type SafeguardingIncidentEvidenceReviewActionRead = {
  incident_id: UUID;
  organization_id: UUID;
  filename: string;
  review_status: string;
  reviewer_person_id: UUID | null;
  reviewed_at: string;
  checksum: string;
  size_bytes: number;
  storage_key: string;
  incident_status: SafeguardingIncidentStatus;
  incident_severity: SafeguardingIncidentSeverity;
  regulatory_report_required: boolean;
  action_summary: string;
  resolution_notes: string | null;
  approval_policy: SafeguardingIncidentEvidenceApprovalPolicyRead | null;
};

export type SafeguardingIncidentAccessControlRead = {
  incident_id: UUID;
  organization_id: UUID;
  relationship_count: number;
  touched_relationships: string[];
  can_manage_case: boolean;
  can_review_evidence: boolean;
  synced_at: string;
};

export type SafeguardingIncidentAccessGrantRead = {
  id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  person_id: UUID;
  relation: string;
  active: boolean;
  granted_by_person_id: UUID | null;
  revoked_by_person_id: UUID | null;
  granted_reason: string | null;
  revoked_reason: string | null;
  revoked_at: string | null;
  created_at: string;
  updated_at: string;
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

export type BackgroundCheckEvidenceDocumentRead = {
  id: UUID;
  organization_id: UUID;
  background_check_id: UUID;
  person_id: UUID;
  uploaded_by_person_id: UUID | null;
  reviewed_by_person_id: UUID | null;
  filename: string;
  content_type: string;
  document_type: string;
  review_status: string;
  size_bytes: number;
  checksum: string;
  storage_key: string;
  evidence_url: string;
  provider_reference: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  notes: string | null;
  background_check_status: BackgroundCheckStatus;
  background_check_risk_level: string;
  created_at: string;
  updated_at: string;
};

export type BackgroundCheckEvidenceDocumentLinkRead = {
  document_id: UUID;
  background_check_id: UUID;
  organization_id: UUID;
  signed_url: string;
  expires_at: string;
  filename: string;
  content_type: string;
  checksum: string;
  size_bytes: number;
  evidence_url: string;
  storage_key: string;
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

export type BackgroundCheckProviderResultRead = {
  accepted: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  organization_id: UUID;
  background_check_id: UUID;
  provider: string;
  external_reference: string | null;
  status: BackgroundCheckStatus;
  risk_level: string;
  message: string;
};

export type BackgroundCheckProviderSubmissionRead = {
  background_check_id: UUID;
  organization_id: UUID;
  person_id: UUID;
  provider: string;
  check_type: string;
  provider_profile: string;
  provider_schema_id: string;
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  provider_status_code: number | null;
  external_reference: string | null;
  check_status: BackgroundCheckStatus;
  provider_payload: Record<string, unknown>;
  failure_reason: string | null;
  submitted_at: string;
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

export type IncidentReportPackageArtifactRead = {
  id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  generated_at: string;
  download_filename: string;
  content_type: string;
  artifact_format: "markdown" | "pdf";
  content: string;
  content_base64: string | null;
  checksum: string;
  size_bytes: number;
  artifact_url: string;
  storage_key: string;
};

export type IncidentReportPackageArtifactLinkRead = {
  id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  generated_at: string;
  artifact_format: "markdown" | "pdf";
  signed_url: string;
  expires_at: string;
  content_type: string;
  filename: string;
  checksum: string;
  size_bytes: number;
  artifact_url: string;
  storage_key: string;
};

export type IncidentReportPackageProviderSubmissionRead = {
  package_id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  agency_name: string;
  jurisdiction: string;
  provider_profile: string;
  provider_schema_id: string;
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  provider_status_code: number | null;
  provider_reference: string | null;
  package_status: IncidentReportPackageStatus;
  artifact_url: string | null;
  storage_key: string | null;
  checksum: string | null;
  failure_reason: string | null;
  submitted_at: string;
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

export type IncidentInsuranceClaimProviderSyncRead = {
  claim_id: UUID;
  organization_id: UUID;
  action: string;
  provider_profile: string;
  provider_schema_id: string;
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  provider_status_code: number | null;
  provider_reference: string | null;
  tracking_url: string | null;
  claim_status: InsuranceClaimStatus;
  failure_reason: string | null;
  synced_at: string;
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

export type IncidentMedicalClearanceProviderSyncRead = {
  clearance_id: UUID;
  organization_id: UUID;
  incident_id: UUID;
  athlete_person_id: UUID;
  action: string;
  provider_profile: string;
  provider_schema_id: string;
  delivery_mode: string;
  delivery_attempted: boolean;
  delivered: boolean;
  provider_status_code: number | null;
  provider_reference: string | null;
  clearance_status: MedicalClearanceStatus;
  documentation_object_key: string | null;
  failure_reason: string | null;
  synced_at: string;
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
  review_assigned_to_person_id: UUID | null;
  review_due_at: string | null;
  review_priority: string;
  review_assignment_notes: string | null;
  approval_required_count: number;
  approval_approved_count: number;
  approval_rejected_count: number;
  approval_pending_count: number;
  approval_status: string;
  approval_last_decided_at: string | null;
  governance_policy_rule_id: UUID | null;
  governance_policy_code: string | null;
  governance_policy_decision: string | null;
  governance_policy_risk_level: string | null;
  governance_policy_rationale: string | null;
};

export type AgentGovernancePolicyRuleRead = {
  id: UUID;
  organization_id: UUID;
  rule_code: string;
  title: string;
  active: boolean;
  agent_kind: AgentKind | null;
  task_type_contains: string | null;
  model_policy_contains: string | null;
  input_ref_contains: string | null;
  decision: string;
  required_approval_count: number;
  risk_level: string;
  rationale: string;
  created_at: string;
  updated_at: string;
};

export type AgentGovernancePolicySimulationRead = {
  organization_id: UUID;
  agent_id: UUID;
  agent_name: string;
  agent_kind: AgentKind;
  model_policy: string;
  task_type: string;
  title: string;
  input_ref: string | null;
  matched: boolean;
  matched_rule: AgentGovernancePolicyRuleRead | null;
  decision: string;
  risk_level: string;
  required_approval_count: number;
  would_block: boolean;
  would_require_approval: boolean;
  rationale: string;
  recommendation: string;
};

export type AgentGovernancePolicyReportRead = {
  organization_id: UUID;
  active_rule_count: number;
  inactive_rule_count: number;
  blocking_rule_count: number;
  approval_rule_count: number;
  allow_rule_count: number;
  critical_rule_count: number;
  high_rule_count: number;
  medium_rule_count: number;
  low_rule_count: number;
  governed_task_count: number;
  ungoverned_task_count: number;
  recent_policy_codes: string[];
  recommendation: string;
};

export type AgentGovernancePolicyHistoryBucketRead = {
  label: string;
  task_count: number;
  approval_required_count: number;
  completed_count: number;
  waiting_for_review_count: number;
  failed_count: number;
};

export type AgentGovernancePolicyHistoryItemRead = {
  policy_code: string;
  decision: string;
  risk_level: string;
  task_count: number;
  approval_required_count: number;
  completed_count: number;
  waiting_for_review_count: number;
  latest_task_title: string | null;
  latest_task_at: string | null;
};

export type AgentGovernancePolicyHistoryRead = {
  organization_id: UUID;
  generated_at: string;
  governed_task_count: number;
  approval_required_count: number;
  completed_count: number;
  waiting_for_review_count: number;
  failed_count: number;
  policy_count: number;
  latest_policy_code: string | null;
  timeline: AgentGovernancePolicyHistoryBucketRead[];
  policies: AgentGovernancePolicyHistoryItemRead[];
  recommendation: string;
};

export type AgentGovernancePolicyHistoryExportRead = {
  organization_id: UUID;
  generated_at: string;
  artifact_format: string;
  content_type: string;
  download_filename: string;
  content: string;
  checksum: string;
  size_bytes: number;
  governed_task_count: number;
  policy_count: number;
};

export type AgentGovernancePolicyHistorySnapshotRead = {
  id: UUID;
  organization_id: UUID;
  snapshot_label: string;
  artifact_format: string;
  content_type: string;
  download_filename: string;
  content: string;
  checksum: string;
  size_bytes: number;
  governed_task_count: number;
  approval_required_count: number;
  completed_count: number;
  waiting_for_review_count: number;
  failed_count: number;
  policy_count: number;
  latest_policy_code: string | null;
  recommendation: string;
  generated_by_person_id: UUID | null;
  generated_at: string;
  created_at: string;
  updated_at: string;
};

export type AgentOutcomeCohortRead = {
  cohort_key: string;
  cohort_label: string;
  task_count: number;
  completed_count: number;
  waiting_for_review_count: number;
  failed_count: number;
  cancelled_count: number;
  approval_required_count: number;
  approval_rejected_count: number;
  appeal_count: number;
  completion_rate: number;
  failure_rate: number;
  review_rate: number;
  appeal_rate: number;
  average_age_hours: number;
  latest_task_at: string | null;
};

export type AgentOutcomeComparisonRead = {
  organization_id: UUID;
  generated_at: string;
  horizon_days: number;
  cohort_by: string;
  total_task_count: number;
  completed_count: number;
  failed_count: number;
  waiting_for_review_count: number;
  appeal_count: number;
  highest_risk_cohort: string | null;
  cohorts: AgentOutcomeCohortRead[];
  recommendation: string;
};

export type AgentTaskApprovalRead = {
  id: UUID;
  organization_id: UUID;
  task_id: UUID;
  reviewer_person_id: UUID | null;
  reviewer_label: string | null;
  requested_by_person_id: UUID | null;
  status: string;
  request_notes: string | null;
  decision_notes: string | null;
  decided_by_person_id: UUID | null;
  decided_at: string | null;
  sequence: number;
};

export type AgentTaskReviewQueueItemRead = {
  task: AgentTaskRead;
  agent_name: string;
  review_assigned_to_name: string | null;
  review_sla_state: string;
  review_age_hours: number;
  pending_approval_count: number;
};

export type AgentTaskReviewQueueSummaryRead = {
  organization_id: UUID;
  open_count: number;
  assigned_count: number;
  unassigned_count: number;
  overdue_count: number;
  due_soon_count: number;
  urgent_count: number;
  pending_approval_count: number;
};

export type AgentTaskReviewTrendBucketRead = {
  label: string;
  opened_count: number;
  completed_count: number;
  assigned_count: number;
  urgent_count: number;
  approval_pending_count: number;
};

export type AgentTaskReviewerWorkloadRead = {
  reviewer_person_id: UUID | null;
  reviewer_name: string;
  assigned_count: number;
  overdue_count: number;
  urgent_count: number;
  completed_count: number;
  average_age_hours: number;
};

export type AgentTaskReviewTrendRead = {
  organization_id: UUID;
  generated_at: string;
  horizon_days: number;
  open_count: number;
  completed_count: number;
  overdue_count: number;
  urgent_count: number;
  buckets: AgentTaskReviewTrendBucketRead[];
  reviewers: AgentTaskReviewerWorkloadRead[];
  recommendation: string;
};

export type AgentTaskWorkerRunRead = {
  organization_id: UUID | null;
  eligible_count: number;
  executed_count: number;
  skipped_count: number;
  failed_count: number;
  task_ids: UUID[];
  statuses: Record<string, number>;
  organization_count: number;
  execution_mode: string;
  limit: number;
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

export type AgentModelGovernanceEvidenceArtifactRead = {
  registry_id: UUID;
  organization_id: UUID;
  model_policy: string;
  generated_at: string;
  artifact_format: string;
  content_type: string;
  download_filename: string;
  content: string;
  checksum: string;
  size_bytes: number;
  total_runs: number;
  review_required_runs: number;
  failed_runs: number;
  bias_audit_count: number;
  failing_bias_audit_count: number;
  open_mitigation_count: number;
  appeal_count: number;
  pending_appeal_count: number;
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
  mitigation_action: string | null;
  mitigation_evidence_ref: string | null;
  mitigated_by_person_id: UUID | null;
  mitigated_at: string | null;
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
  artifact_format: "markdown" | "pdf";
  content: string;
  content_base64: string | null;
  checksum: string;
  size_bytes: number;
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
  approval_pending: number;
  approval_approved: number;
  approval_rejected: number;
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
  external_event_id: string | null;
  callback_payload_hash: string | null;
  callback_received_at: string | null;
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
  source_provider: string | null;
  extractor: string;
  confidence: number;
  review_required: boolean;
  summary: string;
  parser_method: string;
  parser_confidence_reason: string;
  parser_warnings: string[];
  parsed_fields: Record<string, string>;
  model_assisted: boolean;
  model_policy: string | null;
  model_confidence: number | null;
  model_summary: string | null;
  model_evaluation: Record<string, string>;
};

export type PerformanceModelExtractionBenchmarkCaseRead = {
  case_id: string;
  metric_code: string;
  source: MetricSource;
  expected_value: number;
  extracted_value: number;
  absolute_error: number;
  tolerance: number;
  passed: boolean;
  parser_method: string;
  model_assisted: boolean;
  model_policy: string | null;
  confidence: number;
  summary: string;
};

export type PerformanceModelExtractionReviewQueueItemRead = {
  observation: PerformanceObservationRead;
  metric_code: string;
  metric_name: string;
  metric_category: MetricCategory;
  unit: string | null;
  model_assisted: boolean;
  model_policy: string | null;
  evidence_ref: string | null;
  review_priority: string;
  confidence_label: string;
  recommended_action: string;
  review_reason: string;
  flags: string[];
  age_hours: number;
};

export type PerformanceModelExtractionReviewQueueRead = {
  organization_id: UUID;
  athlete_profile_id: UUID | null;
  pending_count: number;
  model_assisted_count: number;
  high_priority_count: number;
  average_confidence: number | null;
  recommendations: string[];
  items: PerformanceModelExtractionReviewQueueItemRead[];
};

export type PerformanceModelExtractionBulkReviewRead = {
  organization_id: UUID;
  reviewed_count: number;
  skipped_count: number;
  verification_status: MetricVerificationStatus;
  summary: string;
  recommendations: string[];
  observations: PerformanceObservationRead[];
};

export type PerformanceModelExtractionBenchmarkDatasetCaseRead = {
  id: UUID;
  dataset_id: UUID;
  case_id: string;
  metric_code: string;
  metric_name: string;
  category: MetricCategory;
  unit: string | null;
  source: MetricSource;
  source_provider: string | null;
  evidence_ref: string;
  expected_value: number;
  tolerance: number;
  status: string;
};

export type PerformanceModelExtractionBenchmarkDatasetRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  slug: string;
  description: string | null;
  model_policy: string | null;
  status: string;
  case_count: number;
  last_run_at: string | null;
  last_accuracy: number | null;
  last_mean_absolute_error: number | null;
  cases: PerformanceModelExtractionBenchmarkDatasetCaseRead[];
};

export type PerformanceModelExtractionBenchmarkRunRead = {
  organization_id: UUID;
  model_policy: string;
  case_count: number;
  passed_count: number;
  failed_count: number;
  accuracy: number;
  mean_absolute_error: number;
  cases: PerformanceModelExtractionBenchmarkCaseRead[];
};

export type PerformanceWearableWebhookRead = {
  ingest_event_id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  source_provider: string;
  external_event_id: string;
  replayed: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  observation_count: number;
  skipped_metric_count: number;
  observation_ids: UUID[];
  payload_hash: string;
  received_at: string;
};

export type PerformanceWearableConnectionRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  provider: string;
  display_name: string;
  external_athlete_ref: string;
  status: string;
  auth_type: string;
  scopes: string[];
  access_token_configured: boolean;
  refresh_token_configured: boolean;
  webhook_secret_configured: boolean;
  access_token_recorded: boolean;
  refresh_token_recorded: boolean;
  refresh_token_family_id: string | null;
  refresh_token_rotated_at: string | null;
  token_last_refreshed_at: string | null;
  token_type: string | null;
  token_scope: string[];
  token_expires_at: string | null;
  oauth_client_id: string | null;
  oauth_client_secret_configured: boolean;
  oauth_authorization_url: string | null;
  oauth_token_url: string | null;
  oauth_redirect_uri: string | null;
  oauth_state_pending: boolean;
  oauth_state_expires_at: string | null;
  oauth_authorized_at: string | null;
  provider_pull_url: string | null;
  provider_pull_cursor_param: string | null;
  provider_pull_since_param: string | null;
  provider_pull_until_param: string | null;
  provider_pull_configured: boolean;
  sync_cursor: string | null;
  last_sync_at: string | null;
  webhook_registered: boolean;
  provider_webhook_registration_url: string | null;
  provider_webhook_callback_url: string | null;
  provider_webhook_event_types: string[];
  provider_webhook_registration_status_code: number | null;
  provider_webhook_registration_hash: string | null;
  provider_webhook_registered_at: string | null;
  provider_webhook_registration_error: string | null;
  default_metric_definition_ids: UUID[];
};

export type PerformanceWearableSyncRunRead = {
  id: UUID;
  organization_id: UUID;
  connection_id: UUID;
  athlete_profile_id: UUID;
  provider: string;
  external_event_id: string | null;
  status: string;
  sync_mode: string;
  started_at: string;
  completed_at: string | null;
  observation_count: number;
  skipped_metric_count: number;
  replayed: boolean;
  provider_status_code: number | null;
  provider_response_hash: string | null;
  provider_page_count: number;
  provider_rate_limited: boolean;
  provider_retry_after_seconds: number | null;
  message: string | null;
};

export type PerformanceWearableWebhookRegistrationRead = {
  connection: PerformanceWearableConnectionRead;
  status: string;
  registered: boolean;
  provider_status_code: number | null;
  registration_payload_hash: string;
  message: string;
};

export type PerformanceWearableOAuthStartRead = {
  connection_id: UUID;
  provider: string;
  authorization_url: string;
  state: string;
  expires_at: string;
  scopes: string[];
};

export type PerformanceWearableOAuthCallbackRead = {
  connection: PerformanceWearableConnectionRead;
  status: string;
  message: string;
  authorization_code_ref: string;
};

export type PerformanceWearableTokenRefreshRead = {
  connection: PerformanceWearableConnectionRead;
  status: string;
  message: string;
  access_token_ref: string | null;
  refresh_token_rotated: boolean;
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

export type PerformanceVideoCoachingMetricRead = {
  metric_definition_id: UUID;
  metric_code: string;
  metric_name: string;
  category: MetricCategory;
  value: number;
  unit: string | null;
  confidence: number;
  coaching_cue: string;
  evidence_summary: string;
};

export type PerformanceVideoCoachingRead = {
  organization_id: UUID;
  athlete_profile_id: UUID;
  event_id: UUID | null;
  sport: string;
  video_uri: string;
  clip_label: string | null;
  model_policy: string;
  confidence: number;
  summary: string;
  coaching_plan: string;
  review_required: boolean;
  observations: PerformanceObservationRead[];
  assessment: AthleteAssessmentRead;
  metrics: PerformanceVideoCoachingMetricRead[];
  next_actions: string[];
};

export type PerformanceVideoAssetRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  event_id: UUID | null;
  uploaded_by_person_id: UUID | null;
  sport: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  checksum: string;
  storage_url: string;
  video_uri: string;
  clip_label: string | null;
  analysis_focus: string | null;
  duration_seconds: number | null;
  frame_rate: number | null;
  frame_width: number | null;
  frame_height: number | null;
  status: string;
  analysis_model_policy: string | null;
  analyzed_at: string | null;
  slow_motion_rates: number[];
  review_default_rate: number;
};

export type OppositionScoutingVideoAssetRead = {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  competition_id: UUID | null;
  event_id: UUID | null;
  uploaded_by_person_id: UUID | null;
  opponent_name: string;
  sport: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  checksum: string;
  storage_url: string;
  video_uri: string;
  clip_label: string | null;
  match_context: string | null;
  analysis_focus: string | null;
  status: string;
  analyzed_at: string | null;
};

export type OppositionScoutingFindingRead = {
  category: string;
  title: string;
  severity: string;
  evidence: string;
  recommendation: string;
};

export type OppositionScoutingReportRead = {
  id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  calibration_id: UUID | null;
  team_id: UUID | null;
  competition_id: UUID | null;
  event_id: UUID | null;
  created_by_person_id: UUID | null;
  opponent_name: string;
  sport: string;
  match_context: string | null;
  analysis_focus: string | null;
  model_policy: string;
  confidence: number;
  formation_detected: string | null;
  tactical_summary: string;
  weaknesses: OppositionScoutingFindingRead[];
  threats: OppositionScoutingFindingRead[];
  recommendations: OppositionScoutingFindingRead[];
  set_pieces: OppositionScoutingFindingRead[];
  tracking_evidence: OppositionScoutingFindingRead[];
  status: string;
  generated_at: string;
};

export type PerformancePitchCalibrationPoint = {
  label: string;
  image_x_percent: number;
  image_y_percent: number;
  pitch_x_meters: number;
  pitch_y_meters: number;
};

export type PerformanceMatchPitchCalibrationRead = {
  id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  created_by_person_id: UUID | null;
  name: string;
  calibration_method: string;
  pitch_length_m: number;
  pitch_width_m: number;
  quality_score: number;
  points: PerformancePitchCalibrationPoint[];
  transform: Record<string, number | string>;
  status: string;
  notes: string | null;
  created_at: string;
};

export type PerformanceMatchTrackingSampleRead = {
  id: UUID;
  organization_id: UUID;
  tracking_run_id: UUID;
  video_asset_id: UUID;
  track_id: string;
  person_id: UUID | null;
  team_label: string | null;
  player_label: string | null;
  jersey_number: string | null;
  frame_index: number | null;
  timestamp_seconds: number;
  x_percent: number;
  y_percent: number;
  x_meters: number;
  y_meters: number;
  speed_mps: number | null;
  confidence: number | null;
  source: string;
};

export type PerformanceMatchTrackingPlayerMetricRead = {
  track_id: string;
  player_label: string | null;
  team_label: string | null;
  jersey_number: string | null;
  sample_count: number;
  duration_seconds: number;
  distance_m: number;
  average_speed_mps: number;
  max_speed_mps: number;
  work_rate_m_per_min: number;
  high_speed_distance_m: number;
  sprint_count: number;
  explosive_effort_count: number;
  recovery_ratio: number;
  pressure_applied_count: number;
  pressure_received_count: number;
  average_nearest_opponent_m: number | null;
  off_ball_run_count: number;
  territorial_advance_count: number;
  pass_completed_count: number;
  pass_received_count: number;
  pass_attempt_count: number;
  pass_accuracy_percent: number;
  turnover_involved_count: number;
  interception_count: number;
  tackle_count: number;
  ball_carry_m: number;
  ball_possession_sample_count: number;
  shot_count: number;
  shot_on_target_count: number;
  expected_goals: number;
  key_pass_count: number;
  expected_assists: number;
  tracking_quality_score: number;
  coaching_flags: string[];
  dominant_zone: string;
  heatmap: Record<string, number>;
};

export type PerformanceMatchTrackingRunRead = {
  id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  calibration_id: UUID | null;
  team_id: UUID | null;
  event_id: UUID | null;
  created_by_person_id: UUID | null;
  source_provider: string;
  model_policy: string;
  status: string;
  pitch_length_m: number;
  pitch_width_m: number;
  sample_count: number;
  player_count: number;
  total_distance_m: number;
  max_speed_mps: number;
  high_speed_distance_m: number;
  sprint_count: number;
  tracking_quality_score: number;
  identity_continuity_score: number;
  calibration_quality_score: number;
  readiness_level: string;
  quality_warnings: string[];
  coaching_guidance: string[];
  tactical_guidance: string[];
  team_shape_metrics: Record<string, unknown>[];
  team_phase_metrics: Record<string, unknown>[];
  pressure_events: Record<string, unknown>[];
  match_phase_snapshots: Record<string, unknown>[];
  ball_tracking_metrics: Record<string, unknown>;
  possession_estimates: Record<string, unknown>[];
  ball_action_events: Record<string, unknown>[];
  recognized_action_events: Record<string, unknown>[];
  action_recognition_metrics: Record<string, unknown>;
  shot_events: Record<string, unknown>[];
  pass_network: Record<string, unknown>[];
  pass_type_metrics: Record<string, unknown>[];
  defensive_action_events: Record<string, unknown>[];
  chance_creation_metrics: Record<string, unknown>;
  formation_snapshots: Record<string, unknown>[];
  player_metrics: PerformanceMatchTrackingPlayerMetricRead[];
  samples: PerformanceMatchTrackingSampleRead[];
  calibration: PerformanceMatchPitchCalibrationRead | null;
  started_at: string;
  completed_at: string | null;
};

export type PerformanceMatchTrackingRunCreate = {
  organization_id: UUID;
  calibration_id?: UUID | null;
  source_provider?: string;
  model_policy?: string | null;
  pitch_length_m?: number;
  pitch_width_m?: number;
  replace_existing?: boolean;
  auto_track?: boolean;
  max_frames?: number;
  sample_every_seconds?: number;
  min_detection_confidence?: number;
  samples?: Record<string, unknown>[];
  provider_metadata?: Record<string, unknown>;
  quality_warnings?: string[];
};

export type PerformanceMatchTrackingProviderDetection = {
  track_id: string;
  object_type?: "player" | "ball";
  person_id?: UUID | null;
  team_label?: string | null;
  player_label?: string | null;
  jersey_number?: string | null;
  x_percent?: number | null;
  y_percent?: number | null;
  x_meters?: number | null;
  y_meters?: number | null;
  bbox_x_percent?: number | null;
  bbox_y_percent?: number | null;
  bbox_width_percent?: number | null;
  bbox_height_percent?: number | null;
  foot_x_percent?: number | null;
  foot_y_percent?: number | null;
  speed_mps?: number | null;
  confidence?: number | null;
  source?: string | null;
};

export type PerformanceMatchTrackingProviderFrame = {
  timestamp_seconds: number;
  frame_index?: number | null;
  detections: PerformanceMatchTrackingProviderDetection[];
};

export type PerformanceMatchTrackingProviderImportCreate = {
  organization_id: UUID;
  calibration_id?: UUID | null;
  source_provider?: string;
  model_policy?: string;
  pitch_length_m?: number;
  pitch_width_m?: number;
  replace_existing?: boolean;
  frames: PerformanceMatchTrackingProviderFrame[];
  provider_metadata?: Record<string, unknown>;
  quality_warnings?: string[];
};

export type PerformanceMatchTrackingProviderIngestEventRead = {
  id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  tracking_run_id: UUID | null;
  team_id: UUID | null;
  event_id: UUID | null;
  source_provider: string;
  external_event_id: string;
  payload_hash: string;
  received_at: string;
  signature_required: boolean;
  signature_validated: boolean;
  sample_count: number;
  player_count: number;
  status: string;
  payload_available: boolean;
  frame_count: number;
  created_at: string;
};

export type PerformanceMatchTrackingProviderIngestReprocessCreate = {
  calibration_id?: UUID | null;
  notes?: string | null;
};

export type PerformanceMatchTrackingProviderWebhookRead = {
  ingest_event_id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  tracking_run_id: UUID | null;
  source_provider: string;
  external_event_id: string;
  replayed: boolean;
  reprocessed: boolean;
  signature_required: boolean;
  signature_validated: boolean;
  sample_count: number;
  player_count: number;
  payload_hash: string;
  received_at: string;
  tracking_run: PerformanceMatchTrackingRunRead | null;
};

export type PerformanceMatchTrackingIdentityReviewRead = {
  id: UUID;
  organization_id: UUID;
  tracking_run_id: UUID;
  video_asset_id: UUID;
  track_id: string;
  reviewer_person_id: UUID | null;
  person_id: UUID | null;
  team_label: string | null;
  player_label: string | null;
  jersey_number: string | null;
  decision: string;
  sample_count: number;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  notes: string | null;
  reviewed_at: string;
  created_at: string;
};

export type PerformanceMatchTrackingIdentityReviewResultRead = {
  review: PerformanceMatchTrackingIdentityReviewRead;
  tracking_run: PerformanceMatchTrackingRunRead;
};

export type PerformanceMatchAnalysisReportRead = {
  id: UUID;
  organization_id: UUID;
  tracking_run_id: UUID;
  video_asset_id: UUID;
  created_by_person_id: UUID | null;
  title: string;
  audience: string;
  report_scope: string;
  status: string;
  model_policy: string;
  summary: Record<string, unknown>;
  player_cards: Record<string, unknown>[];
  team_shape: Record<string, unknown>[];
  recommendations: string[];
  artifact_format: string;
  content_type: string;
  storage_url: string;
  checksum: string;
  size_bytes: number;
  generated_at: string;
  created_at: string;
};

export type PerformanceMatchPlayerGuidanceReviewRead = {
  tracking_run_id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  publishable: boolean;
  guidance_status: string;
  readiness_level: string;
  tracking_quality_score: number;
  identity_continuity_score: number;
  calibration_quality_score: number;
  sample_count: number;
  player_count: number;
  reviewed_identity_count: number;
  unreviewed_track_count: number;
  player_card_count: number;
  required_actions: string[];
  review_notes: string[];
  coach_guidance: string[];
  player_guidance: Record<string, unknown>[];
  player_cards: Record<string, unknown>[];
  quality_warnings: string[];
  generated_at: string;
};

export type PerformanceMatchPlayerGuidancePublishMessageRead = {
  message_id: UUID;
  player_person_id: UUID;
  recipient_person_ids: UUID[];
  track_id: string;
  player_label: string;
  subject: string;
  channel: CommunicationChannel;
};

export type PerformanceMatchPlayerGuidancePublishAuditRead = {
  id: UUID;
  organization_id: UUID;
  tracking_run_id: UUID;
  video_asset_id: UUID;
  message_id: UUID;
  player_person_id: UUID;
  track_id: string;
  player_label: string;
  channel: CommunicationChannel;
  recipient_count: number;
  queued_count: number;
  sent_count: number;
  delivered_count: number;
  read_count: number;
  failed_count: number;
  suppressed_count: number;
  published_by_person_id: UUID | null;
  status: string;
  published_at: string;
  created_at: string;
};

export type PerformanceMatchPlayerGuidancePublishRead = {
  tracking_run_id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  publishable: boolean;
  guidance_status: string;
  message_count: number;
  recipient_count: number;
  player_count: number;
  skipped_track_count: number;
  skipped_tracks: string[];
  required_actions: string[];
  messages: PerformanceMatchPlayerGuidancePublishMessageRead[];
  audits: PerformanceMatchPlayerGuidancePublishAuditRead[];
  published_at: string;
};

export type PerformanceHardwareKitRead = {
  id: UUID;
  organization_id: UUID;
  name: string;
  kit_type: string;
  provider: string;
  sport: string;
  level: string;
  recommended_camera_count: number;
  recommended_gps_unit_count: number;
  supported_metrics: string[];
  setup_steps: string[];
  estimated_cost: number | null;
  currency: string;
  status: string;
  notes: string | null;
  created_at: string;
};

export type PerformanceHardwareDeviceRead = {
  id: UUID;
  organization_id: UUID;
  kit_id: UUID | null;
  team_id: UUID | null;
  facility_id: UUID | null;
  device_type: string;
  provider: string;
  device_label: string;
  external_device_id: string;
  firmware_version: string | null;
  status: string;
  api_key_configured: boolean;
  api_key_secret_path: string | null;
  custody_mode: string;
  metrics_supported: string[];
  calibration_id: UUID | null;
  last_seen_at: string | null;
  battery_percent: number | null;
  notes: string | null;
  created_at: string;
};

export type PerformanceHardwareSyncRunRead = {
  id: UUID;
  organization_id: UUID;
  device_id: UUID;
  video_asset_id: UUID | null;
  tracking_run_id: UUID | null;
  provider: string;
  sync_mode: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  metrics_ingested: number;
  sample_count: number;
  payload_hash: string | null;
  message: string | null;
  tracking_run: PerformanceMatchTrackingRunRead | null;
};

export type PerformanceHighlightClipRead = {
  title: string;
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
  category: string;
  player_label: string | null;
  team_label: string | null;
  jersey_number: string | null;
  confidence: number;
  evidence: string;
  coaching_note: string;
  tags: string[];
};

export type PerformanceHighlightReelRead = {
  id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  tracking_run_id: UUID | null;
  athlete_profile_id: UUID | null;
  created_by_person_id: UUID | null;
  title: string;
  audience: string;
  purpose: string;
  model_policy: string;
  status: string;
  clip_count: number;
  duration_seconds: number;
  clips: PerformanceHighlightClipRead[];
  tags: string[];
  distribution: Record<string, unknown>;
  branding: Record<string, unknown> | null;
  generated_at: string;
  created_at: string;
};

export type PerformanceHighlightReelExportRead = {
  id: UUID;
  organization_id: UUID;
  highlight_reel_id: UUID;
  video_asset_id: UUID;
  tracking_run_id: UUID | null;
  requested_by_person_id: UUID | null;
  export_format: string;
  status: string;
  renderer_policy: string;
  filename: string;
  content_type: string;
  storage_url: string;
  checksum: string;
  size_bytes: number;
  message: string | null;
  manifest: Record<string, unknown>;
  generated_at: string;
  created_at: string;
};

export type PerformanceVideoAnnotationRead = {
  id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  athlete_profile_id: UUID;
  event_id: UUID | null;
  author_person_id: UUID | null;
  timestamp_seconds: number;
  playback_rate: number;
  annotation_type: string;
  label: string;
  notes: string | null;
  body_region: string | null;
  x_percent: number | null;
  y_percent: number | null;
  width_percent: number | null;
  height_percent: number | null;
  tags: string[];
  created_at: string;
};

export type PerformancePoseKeypoint = {
  name: string;
  x_percent: number;
  y_percent: number;
  z: number | null;
  confidence: number | null;
};

export type PerformanceVideoPoseSampleRead = {
  id: UUID;
  organization_id: UUID;
  video_asset_id: UUID;
  athlete_profile_id: UUID;
  event_id: UUID | null;
  created_by_person_id: UUID | null;
  source_provider: string;
  frame_index: number | null;
  timestamp_seconds: number;
  phase: string | null;
  contact_foot: string | null;
  stride_index: number | null;
  sample_confidence: number | null;
  keypoints: PerformancePoseKeypoint[];
  created_at: string;
};

export type PerformanceVideoPoseSampleBatchRead = {
  video_asset: PerformanceVideoAssetRead;
  sample_count: number;
  source_providers: string[];
  samples: PerformanceVideoPoseSampleRead[];
};

export type PerformanceVideoPoseProcessingRead = {
  video_asset: PerformanceVideoAssetRead;
  model_policy: string;
  source_provider: string;
  processed_frame_count: number;
  decoded_frame_count: number;
  sample_count: number;
  warning_count: number;
  warnings: string[];
  pose_samples: PerformanceVideoPoseSampleBatchRead;
  analysis_summary: string | null;
  analysis_model_policy: string | null;
};

export type PerformanceMovementReferenceMetricTarget = {
  key: string;
  label: string;
  category: MetricCategory;
  unit: string;
  optimal_min: number;
  optimal_max: number;
  benchmark_label: string | null;
  coaching_cue: string | null;
};

export type PerformanceMovementReferenceProfileRead = {
  id: UUID;
  organization_id: UUID;
  created_by_person_id: UUID | null;
  sport: string;
  name: string;
  benchmark_profile: string;
  performer_name: string | null;
  source_label: string;
  competition_context: string | null;
  consent_basis: string | null;
  visibility: string;
  status: string;
  metric_targets: PerformanceMovementReferenceMetricTarget[];
  pose_samples: unknown[];
  notes: string | null;
  created_at: string;
};

export type PerformancePoseGaitMetricRead = {
  key: string;
  label: string;
  category: MetricCategory;
  observed_value: number;
  optimal_min: number;
  optimal_max: number;
  unit: string;
  score: number;
  delta_from_optimal: number;
  benchmark_label: string;
  coaching_cue: string;
  source: string;
};

export type PerformancePoseGaitPhaseRead = {
  phase: string;
  timestamp_seconds: number;
  playback_rate: number;
  focus: string;
  finding: string;
  benchmark_note: string;
};

export type PerformanceOptimalProjectionRead = {
  priority: string;
  current_score: number;
  projected_score: number;
  target_change: string;
  drill: string;
};

export type PerformancePoseGaitAnalysisRead = {
  video_asset: PerformanceVideoAssetRead;
  model_policy: string;
  benchmark_profile: string;
  reference_profile_id: UUID | null;
  reference_profile_name: string | null;
  reference_profile_source: string | null;
  confidence: number;
  pose_sample_count: number;
  pose_sample_source_providers: string[];
  summary: string;
  metrics: PerformancePoseGaitMetricRead[];
  phases: PerformancePoseGaitPhaseRead[];
  optimal_projections: PerformanceOptimalProjectionRead[];
  slow_motion_rates: number[];
  annotations: PerformanceVideoAnnotationRead[];
  coaching: PerformanceVideoCoachingRead | null;
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
  filter_category: MetricCategory | null;
  filter_metric_code: string | null;
  period_start: string | null;
  period_end: string | null;
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
  filter_category: MetricCategory | null;
  filter_metric_code: string | null;
  period_start: string | null;
  period_end: string | null;
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

export type AthletePathwayOptionRead = {
  pathway: string;
  score: number;
  readiness: string;
  timeline: string;
  rationale: string;
  next_actions: string[];
};

export type AthletePathwayMilestoneRead = {
  title: string;
  due_label: string;
  priority: string;
  owner: string;
  status: string;
  evidence: string;
};

export type AthletePathwayProjectionRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  athlete_name: string;
  created_by_person_id: UUID | null;
  sport: string;
  primary_position: string | null;
  age_years: number | null;
  academic_gpa: number | null;
  graduation_year: number | null;
  target_pathway: string;
  model_policy: string;
  confidence: number;
  readiness_score: number;
  projected_level: string;
  college_fit_score: number;
  semi_pro_fit_score: number;
  professional_fit_score: number;
  scholarship_fit_score: number;
  summary: string;
  pathway_options: AthletePathwayOptionRead[];
  milestones: AthletePathwayMilestoneRead[];
  scout_actions: string[];
  evidence: Record<string, unknown>;
  risk_flags: string[];
  status: string;
  generated_at: string;
  created_at: string;
};

export type AthleteWellnessCheckInRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  submitted_by_person_id: UUID | null;
  check_in_at: string;
  mood_score: number;
  stress_score: number;
  sleep_hours: number;
  energy_score: number;
  soreness_score: number;
  resilience_score: number | null;
  support_requested: boolean;
  risk_band: string;
  notes: string | null;
  created_at: string;
};

export type AthleteAcademicRecordRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  recorded_by_person_id: UUID | null;
  school_name: string | null;
  term_label: string;
  grade_level: string | null;
  gpa: number | null;
  attendance_rate: number | null;
  study_hours_weekly: number | null;
  missing_assignment_count: number;
  eligibility_status: string;
  risk_level: string;
  next_review_on: string | null;
  notes: string | null;
  created_at: string;
};

export type AthleteLifeSkillAssignmentRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  assigned_by_person_id: UUID | null;
  module_code: string;
  title: string;
  category: string;
  level: string;
  status: string;
  progress_percent: number;
  due_on: string | null;
  completed_at: string | null;
  evidence_notes: string | null;
  created_at: string;
};

export type AthleteScholarshipApplicationRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  created_by_person_id: UUID | null;
  program_name: string;
  scholarship_type: string;
  donor_or_fund: string | null;
  amount_requested: number;
  amount_awarded: number | null;
  currency: string;
  status: string;
  eligibility_score: number;
  committee_recommendation: string;
  deadline_on: string | null;
  submitted_on: string | null;
  decided_on: string | null;
  notes: string | null;
  created_at: string;
};

export type AthleteDevelopmentActionRead = {
  key: string;
  priority: string;
  title: string;
  detail: string;
  owner: string;
};

export type AthleteDevelopmentDashboardRead = {
  organization_id: UUID;
  athlete_profile_id: UUID;
  athlete_name: string;
  generated_at: string;
  development_score: number;
  wellness_risk_band: string;
  academic_eligibility_status: string;
  scholarship_readiness_score: number;
  life_skill_progress_percent: number;
  latest_wellness: AthleteWellnessCheckInRead | null;
  latest_academic: AthleteAcademicRecordRead | null;
  scholarship_applications: AthleteScholarshipApplicationRead[];
  life_skill_assignments: AthleteLifeSkillAssignmentRead[];
  actions: AthleteDevelopmentActionRead[];
};

export type AthleteNutritionProfileRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  recorded_by_person_id: UUID | null;
  dietary_pattern: string;
  allergies: string | null;
  medical_notes: string | null;
  hydration_target_liters: number;
  daily_calorie_target: number;
  protein_target_grams: number;
  carbohydrate_target_grams: number;
  fat_target_grams: number;
  supplement_policy: string | null;
  travel_food_risk: string;
  consent_to_share_with_caterers: boolean;
  status: string;
  created_at: string;
};

export type AthleteMealPlanRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  created_by_person_id: UUID | null;
  title: string;
  plan_type: string;
  period_start: string;
  period_end: string;
  daily_calorie_target: number;
  hydration_target_liters: number;
  menu_summary: string;
  shopping_list: string | null;
  caterer_notes: string | null;
  risk_flags: string | null;
  ai_generated: boolean;
  status: string;
  created_at: string;
};

export type AthleteMealLogRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  meal_plan_id: UUID | null;
  logged_by_person_id: UUID | null;
  logged_at: string;
  meal_type: string;
  calories: number;
  protein_grams: number;
  carbohydrate_grams: number;
  fat_grams: number;
  hydration_liters: number;
  perceived_energy_score: number;
  gut_comfort_score: number;
  compliance_status: string;
  notes: string | null;
  created_at: string;
};

export type NutritionEducationAssignmentRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  assigned_by_person_id: UUID | null;
  module_code: string;
  title: string;
  category: string;
  status: string;
  progress_percent: number;
  due_on: string | null;
  completed_at: string | null;
  evidence_notes: string | null;
  created_at: string;
};

export type AthleteNutritionActionRead = {
  key: string;
  priority: string;
  title: string;
  detail: string;
  owner: string;
};

export type AthleteNutritionDashboardRead = {
  organization_id: UUID;
  athlete_profile_id: UUID;
  athlete_name: string;
  generated_at: string;
  nutrition_score: number;
  risk_band: string;
  hydration_adherence_percent: number;
  fueling_adherence_percent: number;
  education_progress_percent: number;
  profile: AthleteNutritionProfileRead | null;
  active_plan: AthleteMealPlanRead | null;
  recent_logs: AthleteMealLogRead[];
  education_assignments: NutritionEducationAssignmentRead[];
  actions: AthleteNutritionActionRead[];
};

export type PerformanceForecastValidationMetricRead = {
  athlete_profile_id: UUID;
  metric_definition_id: UUID;
  metric_code: string;
  metric_name: string;
  sample_size: number;
  predicted_value: number | null;
  actual_value: number;
  absolute_error: number | null;
  relative_error: number | null;
  tolerance: number;
  passed: boolean;
  drifted: boolean;
};

export type PerformanceForecastValidationRunRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID | null;
  model_policy: string;
  forecast_mode: string;
  metric_count: number;
  evaluated_count: number;
  passed_count: number;
  drift_count: number;
  mean_absolute_error: number;
  mean_relative_error: number;
  max_absolute_error: number;
  drift_level: string;
  recommendation: string;
  details: PerformanceForecastValidationMetricRead[];
  created_at: string;
};

export type PerformanceForecastValidationAlertRead = {
  organization_id: UUID;
  validation_run_id: UUID;
  drift_level: string;
  sent: boolean;
  dry_run: boolean;
  channels: CommunicationChannel[];
  channel_count: number;
  recipient_count: number;
  message_ids: UUID[];
  skipped_reason: string | null;
  validation_run: PerformanceForecastValidationRunRead;
};

export type PerformanceInjuryRiskRead = {
  athlete_profile_id: UUID;
  generated_at: string;
  model_policy: string;
  score: number;
  risk_band: string;
  confidence: number;
  latest_readiness_score: number | null;
  average_readiness_score: number | null;
  average_soreness_score: number | null;
  average_sleep_quality: number | null;
  latest_load: number | null;
  average_load: number | null;
  acute_load: number | null;
  chronic_load: number | null;
  acute_chronic_ratio: number | null;
  load_delta: number | null;
  open_incident_count: number;
  declining_metric_count: number;
  latest_weather_alert_level: string | null;
  latest_weather_decision: string | null;
  weather_alert_count: number;
  hazardous_surface_count: number;
  environmental_risk_count: number;
  surface_risk_labels: string[];
  wearable_observation_count: number;
  biomarker_risk_count: number;
  latest_hrv: number | null;
  latest_resting_heart_rate: number | null;
  latest_recovery_score: number | null;
  latest_hydration_score: number | null;
  wearable_risk_labels: string[];
  biomechanical_observation_count: number;
  biomechanical_risk_count: number;
  latest_movement_quality_score: number | null;
  latest_asymmetry_score: number | null;
  video_risk_labels: string[];
  drivers: string[];
  recommendation: string;
};

export type PerformanceInjuryRiskAlertRead = {
  organization_id: UUID;
  athlete_profile_id: UUID;
  score: number;
  risk_band: string;
  threshold_score: number;
  sent: boolean;
  dry_run: boolean;
  channels: CommunicationChannel[];
  channel_count: number;
  recipient_count: number;
  message_id: UUID | null;
  message_ids: UUID[];
  skipped_reason: string | null;
  risk: PerformanceInjuryRiskRead;
};

export type PerformanceInjuryRiskAlertRunRead = {
  organization_id: UUID | null;
  threshold_score: number;
  repeat_after_hours: number;
  dry_run: boolean;
  channels: CommunicationChannel[];
  channel_count: number;
  eligible_count: number;
  scanned_count: number;
  alerted_count: number;
  skipped_count: number;
  failed_count: number;
  high_risk_count: number;
  highest_score: number | null;
  athlete_profile_ids: UUID[];
  message_ids: UUID[];
  skipped_reasons: Record<string, number>;
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

export type PlayerMatchGuidanceRead = {
  tracking_run_id: UUID;
  video_asset_id: UUID;
  guidance_message_id: UUID;
  guidance_published_at: string;
  guidance_delivery_status: string;
  guidance_recipient_count: number;
  opponent_name: string;
  match_label: string | null;
  tracked_at: string;
  track_id: string;
  team_label: string | null;
  player_label: string | null;
  jersey_number: string | null;
  readiness_level: string;
  tracking_quality_score: number;
  distance_m: number;
  high_speed_distance_m: number;
  max_speed_mps: number;
  sprint_count: number;
  work_rate_m_per_min: number;
  dominant_zone: string;
  pressure_applied_count: number;
  off_ball_run_count: number;
  pass_accuracy_percent: number;
  shot_count: number;
  expected_goals: number;
  coaching_flags: string[];
  player_guidance: string[];
  action_plan: {
    priority: string;
    focus: string;
    cue: string;
    drill_recommendation: string;
    evidence: string;
  }[];
  tactical_context: string[];
  quality_warnings: string[];
};

export type PlayerMatchTrainingFollowupRead = {
  organization_id: UUID;
  athlete_profile_id: UUID;
  tracking_run_id: UUID;
  track_id: string;
  plan_id: UUID;
  item_ids: UUID[];
  title: string;
  focus_area: string;
  period_start: string;
  period_end: string;
  item_count: number;
  action_plan: PlayerMatchGuidanceRead["action_plan"];
  agent_task_id: UUID | null;
  agent_task_status: string | null;
  agent_task_title: string | null;
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
  what_if_scenarios: PerformanceForecastWhatIfRead[];
  injury_risk: PerformanceInjuryRiskRead;
  benchmarks: PerformanceMetricBenchmarkRead[];
  cohort_comparisons: PerformanceCohortComparisonRead[];
  match_guidance: PlayerMatchGuidanceRead[];
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
  generation_provider: string;
  model_policy: string;
  provider_status_code: number | null;
  provider_reference: string | null;
  provider_notes: string | null;
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

export type TrainingCalendarArtifactRead = {
  organization_id: UUID;
  team_id: UUID | null;
  generated_at: string;
  starts_at: string;
  ends_at: string;
  session_count: number;
  content_type: string;
  download_filename: string;
  content: string;
  checksum: string;
  size_bytes: number;
};

export type TrainingCommandMetricRead = {
  key: string;
  label: string;
  value: number;
  detail: string;
  status: string;
};

export type TrainingCommandCheckRead = {
  key: string;
  label: string;
  status: string;
  detail: string;
  action_label: string | null;
};

export type TrainingCommandCenterRead = {
  organization_id: UUID;
  team_id: UUID | null;
  team_name: string | null;
  command_status: string;
  readiness_score: number;
  active_plan_id: UUID | null;
  active_plan_title: string | null;
  next_session_id: UUID | null;
  next_session_title: string | null;
  next_session_at: string | null;
  average_readiness_score: number | null;
  average_load_delta: number | null;
  high_risk_feedback_count: number;
  metrics: TrainingCommandMetricRead[];
  checks: TrainingCommandCheckRead[];
  coach_actions: string[];
  agent_task: AgentTaskRead | null;
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

export type AthleteTransferRead = {
  id: UUID;
  organization_id: UUID;
  athlete_profile_id: UUID;
  athlete_name: string;
  from_team_id: UUID | null;
  from_team_name: string | null;
  to_team_id: UUID;
  to_team_name: string;
  transfer_type: string;
  status: string;
  requested_on: string;
  effective_on: string | null;
  window_label: string | null;
  previous_registration_ref: string | null;
  clearance_reference: string | null;
  reviewed_by_person_id: UUID | null;
  decided_at: string | null;
  reason: string | null;
  notes: string | null;
};

export type CompetitionEligibilityCheckRead = {
  key: string;
  label: string;
  status: string;
  severity: string;
  detail: string;
  recommendation: string;
};

export type CompetitionEligibilityCertificateRead = {
  id: UUID;
  organization_id: UUID;
  competition_id: UUID;
  athlete_profile_id: UUID;
  athlete_name: string;
  team_id: UUID;
  team_name: string;
  transfer_record_id: UUID | null;
  status: string;
  certificate_number: string;
  valid_from: string | null;
  valid_until: string | null;
  blocker_count: number;
  warning_count: number;
  eligibility_summary: string;
  checks: CompetitionEligibilityCheckRead[];
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
  escalates_message_id: UUID | null;
  escalation_level: number;
  escalation_triggered_at: string | null;
  escalation_reason: string | null;
};

export type CommunicationScheduledDispatchWorkerRunRead = {
  organization_id: UUID | null;
  eligible_count: number;
  executed_count: number;
  dispatched_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  message_ids: UUID[];
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

export type ProviderDeliveryWebhookRead = {
  provider: string;
  provider_status: string;
  normalized_status: MessageDeliveryStatus;
  recipient: MessageRecipientRead;
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

export type CommunicationDeliveryChannelReadiness = {
  channel: CommunicationChannel;
  status: string;
  dispatch_ready: boolean;
  live_ready: boolean;
  webhook_configured: boolean;
  webhook_source: string;
  key_configured: boolean;
  key_source: string;
  details: string[];
};

export type CommunicationDeliveryReadinessRead = {
  delivery_mode: string;
  key_source: string;
  key_configured: boolean;
  key_failure_reason: string | null;
  dispatch_ready_count: number;
  live_ready_count: number;
  blocked_count: number;
  channels: CommunicationDeliveryChannelReadiness[];
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

export type CommunicationEscalationSchedulerRunRead = {
  organization_id: UUID;
  eligible_count: number;
  escalated_count: number;
  skipped_count: number;
  failed_count: number;
  dry_run: boolean;
  original_message_ids: UUID[];
  escalation_message_ids: UUID[];
  runs: CommunicationEscalationRunRead[];
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
