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
