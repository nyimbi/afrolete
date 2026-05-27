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
