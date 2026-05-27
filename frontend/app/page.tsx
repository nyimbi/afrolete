"use client";

import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import {
  clearStoredAuthSession,
  completeKeycloakCallbackFromUrl,
  keycloakLogoutUrl,
  startKeycloakLogin,
  type AuthSession
} from "@/lib/auth";
import { afroleteAuthMode, apiBaseUrl, keycloakClientId, keycloakIssuer } from "@/lib/config";
import type {
  AgentAssignmentRead,
  AgentGovernanceSummaryRead,
  AgentKind,
  AgentRead,
  AgentRunRecordRead,
  AgentTaskRead,
  AgentTaskStatus,
  AccountingExportRead,
  AssetCondition,
  AssetSummaryRead,
  AssetUtilizationRecommendationRead,
  AthleteAssessmentRead,
  AthletePerformanceSummaryRead,
  AttendanceRecordRead,
  AttendanceSeedRead,
  AttendanceStatus,
  BillingCycle,
  BillingDunningDeliveryRead,
  BillingDunningNoticeRead,
  BillingEntitlementRead,
  BillingPaymentWebhookRead,
  BillingPlanChangeRead,
  BillingPlanRead,
  BillingProrationQuoteRead,
  BillingSummaryRead,
  BillingTaxFilingRead,
  BillingTaxQuoteRead,
  ChannelPreference,
  CommunicationDigestRead,
  CommunicationDigestRunRead,
  CommunicationDispatchSummary,
  CommunicationDraftRead,
  CommunicationInboxItemRead,
  CommercialSummaryRead,
  CommunicationChannel,
  CommunicationMessageRead,
  CommunicationMessageType,
  CommunicationScopeType,
  CommunicationTemplateRead,
  CommercialRefundRead,
  CompetitionAdvancementRead,
  CompetitionBracketRead,
  CompetitionBracketRoundRead,
  CompetitionBroadcastRead,
  CompetitionConflictRead,
  CompetitionFixtureRead,
  CompetitionFixtureGenerationRead,
  CompetitionFormat,
  CompetitionParticipantRead,
  CompetitionRead,
  CompetitionScheduleOptimizationRead,
  CompetitionStandingRead,
  CompetitionTicketingRead,
  CompetitionType,
  ConsentRequestRead,
  DonationRead,
  EventRead,
  EventType,
  EquipmentCheckoutRead,
  EquipmentFileRead,
  EquipmentItemRead,
  EquipmentLeaseInvoiceRead,
  EquipmentLeasePaymentRead,
  EquipmentLeaseQuoteRead,
  EquipmentLeaseScheduleRead,
  EquipmentReaderProvisionRead,
  EquipmentReaderRead,
  EquipmentScanEventRead,
  EquipmentScanRead,
  FacilityBookingRead,
  FacilityRead,
  FacilityType,
  FinanceInvoiceRead,
  FinancePaymentRead,
  FixtureMatchEventRead,
  FixtureOfficialAssignmentRead,
  FundraisingCampaignRead,
  GeneratedTrainingPlanRead,
  GeneratedReportRead,
  GuardianRelationshipRead,
  InsightSeverity,
  InsightStatus,
  IntelligenceInsightRead,
  LocalIdentity,
  MatchEventType,
  MessageDeliveryStatus,
  MessageRecipientRead,
  MembershipRead,
  MetricCategory,
  MetricDefinitionRead,
  MetricSource,
  OfficialRole,
  OrganizationRead,
  OrganizationType,
  ParticipationClearanceRead,
  PaymentSettlementRead,
  PerformanceIngestionRead,
  PerformanceObservationRead,
  NotificationFrequency,
  NotificationPreferenceRead,
  PredictiveRiskScoreRead,
  ProcurementRecommendationRead,
  ReportCategory,
  ReportArtifactAccessRead,
  ReportChartRead,
  ReportDefinitionRead,
  ReportExportJobRead,
  ReportFormat,
  ReportFrequency,
  RenderedReportRead,
  ReportVerificationRead,
  ReportingBenchmarkRead,
  ReportingSummaryRead,
  SaaSInvoiceRead,
  SaaSPaymentRead,
  ScheduledReportRead,
  SponsorRead,
  SponsorshipAgreementRead,
  SponsorshipDashboardRead,
  SupplierOrderRead,
  SupplierInvoiceSyncRead,
  SupplierOrderSubmissionRead,
  SupplierScoreRead,
  SportFormat,
  SubscriptionRead,
  TaxQuoteRead,
  TeamRead,
  TeamRosterEntryRead,
  TeamRole,
  TrainingAvailabilityRead,
  TrainingDrillRead,
  TrainingPlanItemRead,
  TrainingPlanRead,
  TrainingSessionFeedbackRead,
  TrainingSessionPlanRead,
  TicketOrderRead,
  TicketProductRead,
  TicketRead,
  UsageMeterRead,
  UsageRecordRead,
  UsageUnit,
  WorkOrderPriority,
  WorkOrderStatus,
  MaintenanceWorkOrderRead
} from "@/types/operations";

const defaultIdentity: LocalIdentity = {
  sub: "kc-owner-1",
  email: "owner@example.com",
  name: "Owner Example"
};

type LogEntry = {
  id: string;
  tone: "good" | "bad" | "neutral";
  message: string;
};

type AthleteEntry = {
  personId: string;
  athleteProfileId: string;
  name: string;
  email: string;
  rosterEntryId?: string;
};

const chartColors = ["var(--teal)", "var(--blue)", "var(--amber)", "var(--red)", "var(--violet)"];

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? "");
      resolve(result.includes(",") ? result.split(",", 2)[1] : result);
    };
    reader.onerror = () => reject(reader.error ?? new Error("File read failed"));
    reader.readAsDataURL(file);
  });
}

function ReportingChartCard({ chart }: { chart: ReportChartRead }) {
  const total = chart.values.reduce((sum, value) => sum + value, 0);
  const max = Math.max(...chart.values, 1);
  let cursor = 0;
  const donutSegments = chart.values.map((value, index) => {
    const size = total > 0 ? (value / total) * 360 : 0;
    const segment = `${chartColors[index % chartColors.length]} ${cursor}deg ${cursor + size}deg`;
    cursor += size;
    return segment;
  });
  const donutBackground = total > 0
    ? `conic-gradient(${donutSegments.join(", ")})`
    : "var(--wash-strong)";

  return (
    <article className="task-card chart-card">
      <div>
        <strong>{chart.title}</strong>
        <span>{chart.chart_type} · {chart.insight}</span>
      </div>
      {chart.chart_type === "donut" ? (
        <div className="chart-donut-row">
          <div
            className="chart-donut"
            style={{ background: donutBackground }}
          >
            <span>{Math.round(total)}</span>
          </div>
          <div className="chart-legend">
            {chart.labels.map((label, index) => (
              <span key={label}>
                <i style={{ backgroundColor: chartColors[index % chartColors.length] }} />
                {label}: {chart.values[index] ?? 0}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="chart-bars">
          {chart.labels.map((label, index) => {
            const value = chart.values[index] ?? 0;
            const width = Math.max(4, Math.round((value / max) * 100));
            return (
              <div className="chart-bar-row" key={label}>
                <span>{label}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{
                      width: `${width}%`,
                      backgroundColor: chartColors[index % chartColors.length]
                    }}
                  />
                </div>
                <strong>{value}</strong>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

function CompetitionBracketLane({ round }: { round: CompetitionBracketRoundRead }) {
  return (
    <article className="bracket-lane">
      <div className="bracket-lane-head">
        <strong>{round.round_label}</strong>
        <span>{round.stage_label}</span>
      </div>
      <div className="bracket-match-list">
        {round.matches.map((match) => (
          <div className="bracket-match" key={`${match.fixture_id ?? "projected"}-${match.slot}`}>
            <div className="bracket-slot">
              <span>{match.home_team_name ?? "TBD"}</span>
              <span>{match.away_team_name ?? "BYE"}</span>
            </div>
            <div className="bracket-result">
              <strong>{match.winner_team_name ?? "Pending"}</strong>
              <small>{match.status ?? "projected"} · slot {match.slot}</small>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

export default function HomePage() {
  const [identity, setIdentity] = useState<LocalIdentity>(defaultIdentity);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationRead[]>([]);
  const [teams, setTeams] = useState<TeamRead[]>([]);
  const [events, setEvents] = useState<EventRead[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecordRead[]>([]);
  const [agents, setAgents] = useState<AgentRead[]>([]);
  const [agentTasks, setAgentTasks] = useState<AgentTaskRead[]>([]);
  const [agentRuns, setAgentRuns] = useState<AgentRunRecordRead[]>([]);
  const [agentGovernance, setAgentGovernance] = useState<AgentGovernanceSummaryRead | null>(null);
  const [metricDefinitions, setMetricDefinitions] = useState<MetricDefinitionRead[]>([]);
  const [observations, setObservations] = useState<PerformanceObservationRead[]>([]);
  const [performanceIngestion, setPerformanceIngestion] = useState<PerformanceIngestionRead | null>(null);
  const [assessments, setAssessments] = useState<AthleteAssessmentRead[]>([]);
  const [performanceSummary, setPerformanceSummary] =
    useState<AthletePerformanceSummaryRead | null>(null);
  const [trainingDrills, setTrainingDrills] = useState<TrainingDrillRead[]>([]);
  const [trainingPlans, setTrainingPlans] = useState<TrainingPlanRead[]>([]);
  const [trainingPlanItems, setTrainingPlanItems] = useState<TrainingPlanItemRead[]>([]);
  const [trainingSessions, setTrainingSessions] = useState<TrainingSessionPlanRead[]>([]);
  const [trainingFeedback, setTrainingFeedback] = useState<TrainingSessionFeedbackRead[]>([]);
  const [trainingAvailability, setTrainingAvailability] = useState<TrainingAvailabilityRead | null>(null);
  const [generatedTrainingPlan, setGeneratedTrainingPlan] = useState<GeneratedTrainingPlanRead | null>(null);
  const [competitions, setCompetitions] = useState<CompetitionRead[]>([]);
  const [competitionParticipants, setCompetitionParticipants] = useState<CompetitionParticipantRead[]>([]);
  const [competitionFixtures, setCompetitionFixtures] = useState<CompetitionFixtureRead[]>([]);
  const [competitionStandings, setCompetitionStandings] = useState<CompetitionStandingRead[]>([]);
  const [fixtureGeneration, setFixtureGeneration] = useState<CompetitionFixtureGenerationRead | null>(null);
  const [competitionAdvancement, setCompetitionAdvancement] = useState<CompetitionAdvancementRead | null>(null);
  const [scheduleOptimization, setScheduleOptimization] =
    useState<CompetitionScheduleOptimizationRead | null>(null);
  const [competitionBroadcast, setCompetitionBroadcast] = useState<CompetitionBroadcastRead | null>(null);
  const [competitionTicketing, setCompetitionTicketing] = useState<CompetitionTicketingRead[]>([]);
  const [competitionBracket, setCompetitionBracket] = useState<CompetitionBracketRead | null>(null);
  const [competitionConflicts, setCompetitionConflicts] = useState<CompetitionConflictRead[]>([]);
  const [matchEvents, setMatchEvents] = useState<FixtureMatchEventRead[]>([]);
  const [officialAssignments, setOfficialAssignments] = useState<FixtureOfficialAssignmentRead[]>([]);
  const [communicationTemplates, setCommunicationTemplates] = useState<CommunicationTemplateRead[]>([]);
  const [communicationMessages, setCommunicationMessages] = useState<CommunicationMessageRead[]>([]);
  const [messageRecipients, setMessageRecipients] = useState<MessageRecipientRead[]>([]);
  const [inboxItems, setInboxItems] = useState<CommunicationInboxItemRead[]>([]);
  const [digestSummary, setDigestSummary] = useState<CommunicationDigestRead | null>(null);
  const [digestRun, setDigestRun] = useState<CommunicationDigestRunRead | null>(null);
  const [draftPreview, setDraftPreview] = useState<CommunicationDraftRead | null>(null);
  const [notificationPreference, setNotificationPreference] = useState<NotificationPreferenceRead | null>(null);
  const [facilities, setFacilities] = useState<FacilityRead[]>([]);
  const [equipmentItems, setEquipmentItems] = useState<EquipmentItemRead[]>([]);
  const [equipmentFiles, setEquipmentFiles] = useState<EquipmentFileRead[]>([]);
  const [equipmentScanEvents, setEquipmentScanEvents] = useState<EquipmentScanEventRead[]>([]);
  const [equipmentReaders, setEquipmentReaders] = useState<EquipmentReaderRead[]>([]);
  const [rfidProvision, setRfidProvision] = useState<EquipmentReaderProvisionRead | null>(null);
  const [equipmentCheckouts, setEquipmentCheckouts] = useState<EquipmentCheckoutRead[]>([]);
  const [workOrders, setWorkOrders] = useState<MaintenanceWorkOrderRead[]>([]);
  const [facilityBookings, setFacilityBookings] = useState<FacilityBookingRead[]>([]);
  const [assetSummary, setAssetSummary] = useState<AssetSummaryRead | null>(null);
  const [procurementRecommendations, setProcurementRecommendations] = useState<ProcurementRecommendationRead[]>([]);
  const [supplierOrders, setSupplierOrders] = useState<SupplierOrderRead[]>([]);
  const [supplierScores, setSupplierScores] = useState<SupplierScoreRead[]>([]);
  const [supplierSubmission, setSupplierSubmission] = useState<SupplierOrderSubmissionRead | null>(null);
  const [supplierInvoiceSync, setSupplierInvoiceSync] = useState<SupplierInvoiceSyncRead | null>(null);
  const [assetUtilization, setAssetUtilization] = useState<AssetUtilizationRecommendationRead[]>([]);
  const [leaseQuote, setLeaseQuote] = useState<EquipmentLeaseQuoteRead | null>(null);
  const [leaseInvoice, setLeaseInvoice] = useState<EquipmentLeaseInvoiceRead | null>(null);
  const [leaseSchedules, setLeaseSchedules] = useState<EquipmentLeaseScheduleRead[]>([]);
  const [leasePayment, setLeasePayment] = useState<EquipmentLeasePaymentRead | null>(null);
  const [sponsors, setSponsors] = useState<SponsorRead[]>([]);
  const [sponsorships, setSponsorships] = useState<SponsorshipAgreementRead[]>([]);
  const [campaigns, setCampaigns] = useState<FundraisingCampaignRead[]>([]);
  const [donations, setDonations] = useState<DonationRead[]>([]);
  const [ticketProducts, setTicketProducts] = useState<TicketProductRead[]>([]);
  const [ticketOrders, setTicketOrders] = useState<TicketOrderRead[]>([]);
  const [tickets, setTickets] = useState<TicketRead[]>([]);
  const [invoices, setInvoices] = useState<FinanceInvoiceRead[]>([]);
  const [payments, setPayments] = useState<FinancePaymentRead[]>([]);
  const [commercialSummary, setCommercialSummary] = useState<CommercialSummaryRead | null>(null);
  const [taxQuote, setTaxQuote] = useState<TaxQuoteRead | null>(null);
  const [paymentSettlement, setPaymentSettlement] = useState<PaymentSettlementRead | null>(null);
  const [accountingExport, setAccountingExport] = useState<AccountingExportRead | null>(null);
  const [commercialRefund, setCommercialRefund] = useState<CommercialRefundRead | null>(null);
  const [sponsorshipDashboard, setSponsorshipDashboard] = useState<SponsorshipDashboardRead[]>([]);
  const [reportDefinitions, setReportDefinitions] = useState<ReportDefinitionRead[]>([]);
  const [generatedReports, setGeneratedReports] = useState<GeneratedReportRead[]>([]);
  const [scheduledReports, setScheduledReports] = useState<ScheduledReportRead[]>([]);
  const [insights, setInsights] = useState<IntelligenceInsightRead[]>([]);
  const [riskScores, setRiskScores] = useState<PredictiveRiskScoreRead[]>([]);
  const [reportExports, setReportExports] = useState<ReportExportJobRead[]>([]);
  const [renderedReport, setRenderedReport] = useState<RenderedReportRead | null>(null);
  const [reportArtifactAccess, setReportArtifactAccess] = useState<ReportArtifactAccessRead | null>(null);
  const [reportVerification, setReportVerification] = useState<ReportVerificationRead | null>(null);
  const [reportCharts, setReportCharts] = useState<ReportChartRead[]>([]);
  const [reportingBenchmarks, setReportingBenchmarks] = useState<ReportingBenchmarkRead[]>([]);
  const [reportingSummary, setReportingSummary] = useState<ReportingSummaryRead | null>(null);
  const [billingPlans, setBillingPlans] = useState<BillingPlanRead[]>([]);
  const [subscriptions, setSubscriptions] = useState<SubscriptionRead[]>([]);
  const [usageMeters, setUsageMeters] = useState<UsageMeterRead[]>([]);
  const [usageRecords, setUsageRecords] = useState<UsageRecordRead[]>([]);
  const [saasInvoices, setSaasInvoices] = useState<SaaSInvoiceRead[]>([]);
  const [saasPayments, setSaasPayments] = useState<SaaSPaymentRead[]>([]);
  const [billingEntitlements, setBillingEntitlements] = useState<BillingEntitlementRead[]>([]);
  const [billingTaxQuote, setBillingTaxQuote] = useState<BillingTaxQuoteRead | null>(null);
  const [billingTaxFiling, setBillingTaxFiling] = useState<BillingTaxFilingRead | null>(null);
  const [billingProration, setBillingProration] = useState<BillingProrationQuoteRead | null>(null);
  const [billingPlanChange, setBillingPlanChange] = useState<BillingPlanChangeRead | null>(null);
  const [billingDunning, setBillingDunning] = useState<BillingDunningNoticeRead | null>(null);
  const [billingDunningDelivery, setBillingDunningDelivery] =
    useState<BillingDunningDeliveryRead | null>(null);
  const [billingWebhook, setBillingWebhook] = useState<BillingPaymentWebhookRead | null>(null);
  const [billingSummary, setBillingSummary] = useState<BillingSummaryRead | null>(null);
  const [athletes, setAthletes] = useState<AthleteEntry[]>([]);
  const [guardians, setGuardians] = useState<GuardianRelationshipRead[]>([]);
  const [consentRequest, setConsentRequest] = useState<ConsentRequestRead | null>(null);
  const [clearance, setClearance] = useState<ParticipationClearanceRead | null>(null);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState("");
  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [selectedEventId, setSelectedEventId] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [selectedAthleteId, setSelectedAthleteId] = useState("");
  const [selectedObservationId, setSelectedObservationId] = useState("");
  const [selectedTrainingPlanId, setSelectedTrainingPlanId] = useState("");
  const [selectedTrainingSessionId, setSelectedTrainingSessionId] = useState("");
  const [selectedCompetitionId, setSelectedCompetitionId] = useState("");
  const [selectedFixtureId, setSelectedFixtureId] = useState("");
  const [selectedMessageId, setSelectedMessageId] = useState("");
  const [selectedFacilityId, setSelectedFacilityId] = useState("");
  const [selectedEquipmentId, setSelectedEquipmentId] = useState("");
  const [selectedCheckoutId, setSelectedCheckoutId] = useState("");
  const [selectedWorkOrderId, setSelectedWorkOrderId] = useState("");
  const [selectedSupplierOrderId, setSelectedSupplierOrderId] = useState("");
  const [selectedSponsorId, setSelectedSponsorId] = useState("");
  const [selectedCampaignId, setSelectedCampaignId] = useState("");
  const [selectedTicketProductId, setSelectedTicketProductId] = useState("");
  const [selectedTicketId, setSelectedTicketId] = useState("");
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [selectedReportDefinitionId, setSelectedReportDefinitionId] = useState("");
  const [selectedGeneratedReportId, setSelectedGeneratedReportId] = useState("");
  const [selectedInsightId, setSelectedInsightId] = useState("");
  const [selectedBillingPlanId, setSelectedBillingPlanId] = useState("");
  const [selectedSubscriptionId, setSelectedSubscriptionId] = useState("");
  const [selectedUsageMeterId, setSelectedUsageMeterId] = useState("");
  const [selectedSaasInvoiceId, setSelectedSaasInvoiceId] = useState("");
  const [selectedEquipmentFile, setSelectedEquipmentFile] = useState<File | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const [organizationForm, setOrganizationForm] = useState({
    name: "Nairobi Rising FC",
    organization_type: "club" as OrganizationType,
    country_code: "KE",
    primary_sport: "football",
    public_name: "Nairobi Rising",
    subdomain: "nairobi-rising",
    brand_primary_color: "#0f766e",
    brand_secondary_color: "#f59e0b",
    contact_email: "hello@rising.example"
  });
  const [teamForm, setTeamForm] = useState({
    name: "U16 Rising",
    sport: "football",
    sport_format: "team" as SportFormat,
    age_group: "U16",
    gender_category: "open",
    season_label: "2026"
  });
  const [athleteForm, setAthleteForm] = useState({
    display_name: "Amani Otieno",
    email: "amani@example.com",
    role: "player" as TeamRole,
    primary_position: "Midfielder",
    jersey_number: "8",
    is_captain: false
  });
  const [eventForm, setEventForm] = useState({
    title: "U16 League Match",
    event_type: "match" as EventType,
    starts_at: "2026-05-28T09:00",
    duration_minutes: 90,
    timezone: "Africa/Nairobi",
    venue_name: "City Stadium",
    notes: "Matchday operations and consent clearance."
  });
  const [guardianForm, setGuardianForm] = useState({
    guardian_display_name: "Parent Example",
    guardian_email: "parent@example.com",
    guardian_phone: "+254700000000"
  });
  const [agentForm, setAgentForm] = useState({
    name: "Safeguarding Watch",
    kind: "safeguarding" as AgentKind,
    purpose: "Monitor consent gaps, unsafe participation, and review tasks before messages go out.",
    model_policy: "human_review_required"
  });
  const [taskForm, setTaskForm] = useState({
    task_type: "consent_gap_review",
    title: "Review missing consent before matchday",
    input_ref: "event-clearance"
  });
  const [metricForm, setMetricForm] = useState({
    code: "first_touch",
    name: "First Touch",
    category: "technical" as MetricCategory,
    unit: "score",
    min_value: 0,
    max_value: 10,
    weight: 1.2
  });
  const [observationForm, setObservationForm] = useState({
    value: 8,
    raw_value: "8/10",
    source: "coach_evaluation" as MetricSource,
    evidence_ref: "video://matchday/clip-001",
    evidence_text: "Clip analysis: first touch quality 8.4, pressure scan before receiving.",
    confidence: 0.9,
    notes: "Improved under pressure."
  });
  const [assessmentForm, setAssessmentForm] = useState({
    physical_score: 70,
    technical_score: 80,
    tactical_score: 66,
    mental_score: 86,
    summary: "Strong technical day with good decision speed.",
    recommendations: "Add weak-foot finishing and transition scanning."
  });
  const [drillForm, setDrillForm] = useState({
    name: "Scanning rondo",
    focus_area: "Awareness",
    category: "technical",
    description: "Possession drill requiring shoulder checks before receiving.",
    coaching_points: "Check both shoulders and open the body before the first touch.",
    default_duration_minutes: 18,
    default_intensity: 6
  });
  const [trainingPlanForm, setTrainingPlanForm] = useState({
    title: "Four-week awareness block",
    focus_area: "Scanning and first touch",
    period_start: "2026-06-01",
    period_end: "2026-06-28",
    readiness_score: 72,
    weekly_sessions: 3,
    load_guidance: "Keep acute load below 1.3x the four-week baseline.",
    recovery_protocol: "Mobility, hydration, and wellness check after high-intensity days.",
    progress_checkpoints: "Weekly coach review and first-touch score."
  });
  const [trainingItemForm, setTrainingItemForm] = useState({
    day_label: "Week 1 Day 1",
    title: "Scanning rondo block",
    duration_minutes: 18,
    intensity: 6,
    notes: "Progress from 4v2 to 5v2 if tempo stays high."
  });
  const [trainingSessionForm, setTrainingSessionForm] = useState({
    title: "Awareness session",
    scheduled_for: "2026-06-03T15:00",
    duration_minutes: 75,
    rpe_target: 7,
    objectives: "Improve scanning before receiving under pressure."
  });
  const [trainingFeedbackForm, setTrainingFeedbackForm] = useState({
    readiness_score: 76,
    soreness_score: 3,
    sleep_quality: 8,
    mood_score: 8,
    actual_rpe: 7,
    actual_duration_minutes: 72,
    completed: true,
    feedback: "Felt strong after warm-up; slight tightness near the end.",
    coach_notes: "Keep next session technical if soreness rises tomorrow."
  });
  const [competitionForm, setCompetitionForm] = useState({
    name: "U17 City League",
    sport: "football",
    competition_type: "league" as CompetitionType,
    format: "round_robin" as CompetitionFormat,
    season_label: "2026",
    starts_on: "2026-06-01",
    ends_on: "2026-08-31",
    tiebreakers: "Points, goal difference, goals for",
    rules_summary: "Standard league scoring with confirmed official results."
  });
  const [fixtureForm, setFixtureForm] = useState({
    round_label: "Round 1",
    stage_label: "League",
    scheduled_at: "2026-06-05T16:00",
    venue_name: "City Stadium",
    home_score: 2,
    away_score: 1,
    event_minute: 31,
    event_type: "goal" as MatchEventType,
    event_description: "Opening goal from a set piece."
  });
  const [officialForm, setOfficialForm] = useState({
    display_name: "Referee Example",
    email: "referee@example.com",
    role: "referee" as OfficialRole,
    certification_level: "Regional"
  });
  const [templateForm, setTemplateForm] = useState({
    name: "Match day reminder",
    message_type: "reminder" as CommunicationMessageType,
    channel: "email" as CommunicationChannel,
    subject_template: "Match day information for {team.name}",
    body_template: "Please confirm attendance and arrive 45 minutes before kick-off.",
    variables: "team.name,event.time,venue.name"
  });
  const [messageForm, setMessageForm] = useState({
    message_type: "reminder" as CommunicationMessageType,
    channel: "email" as CommunicationChannel,
    scope_type: "team" as CommunicationScopeType,
    subject: "Match day information",
    body: "Kick-off is at 09:00. Bring boots, ID, water, and travel consent if required.",
    urgent: false,
    quiet_hours_override: false
  });
  const [preferenceForm, setPreferenceForm] = useState({
    frequency: "immediate" as NotificationFrequency,
    channel_preference: "all" as ChannelPreference,
    language: "en",
    quiet_hours_start: "21:00",
    quiet_hours_end: "06:00",
    emergency_override: true
  });
  const [facilityForm, setFacilityForm] = useState({
    name: "Main Field",
    facility_type: "field" as FacilityType,
    surface: "Natural grass",
    capacity: 500,
    location: "Riverside campus",
    hourly_rate: 120,
    maintenance_budget: 15000,
    condition: "good" as AssetCondition,
    amenities: "Lights, changing rooms, scoreboard, secure storage",
    insurance_policy_ref: "LIAB-2026"
  });
  const [equipmentForm, setEquipmentForm] = useState({
    name: "Footballs Size 5",
    category: "training_equipment",
    subcategory: "balls",
    brand: "Nike",
    model: "Premier League Match Ball",
    tag_code: "BALL-SET-001",
    serial_number: "SER-BALL-001",
    quantity_total: 24,
    min_stock_level: 10,
    reorder_point: 8,
    unit_value: 50,
    depreciation_rate: 20,
    photo_url: "https://cdn.afrolete.local/assets/ball-set.jpg",
    storage_location: "Equipment Room A, Shelf 3",
    condition: "good" as AssetCondition
  });
  const [rfidForm, setRfidForm] = useState({
    reader_id: "reader-main-gate",
    reader_name: "Main gate RFID reader",
    reader_location: "Equipment Room A, Shelf 3",
    movement: "audit",
    source: "rfid_reader",
    api_key: "local-reader-key-0001",
    gateway_code: "BALL-SET-001"
  });
  const [checkoutForm, setCheckoutForm] = useState({
    quantity: 6,
    purpose: "Saturday match kit",
    due_at: "2026-06-11T12:00",
    condition_notes: "Two balls need inflation."
  });
  const [workOrderForm, setWorkOrderForm] = useState({
    title: "Inspect goal nets and ball pressure",
    priority: "high" as WorkOrderPriority,
    due_at: "2026-06-09T12:00",
    vendor: "Grounds Crew",
    estimated_cost: 150,
    safety_related: true,
    compliance_reference: "Monthly equipment inspection",
    notes: "Pre-match safety check."
  });
  const [bookingForm, setBookingForm] = useState({
    title: "U16 training block",
    starts_at: "2026-06-12T15:00",
    duration_hours: 2,
    requester_name: "Coach Example",
    requester_email: "coach@example.com",
    expected_attendees: 28,
    rate: 120,
    deposit_required: 50,
    insurance_certificate_ref: "CERT-2026",
    special_requirements: "Goals, corner flags, and first-aid kit."
  });
  const [sponsorForm, setSponsorForm] = useState({
    name: "Sportswear Co.",
    industry: "Sports apparel",
    contact_name: "Sponsor Lead",
    contact_email: "sponsor@example.com",
    agreement_name: "Season development partner",
    tier: "Gold",
    value_amount: 10000,
    deliverables: "Logo on kits, matchday signage, branded challenge, coupon code.",
    activation_notes: "Launch branded first-touch challenge for U17 athletes."
  });
  const [campaignForm, setCampaignForm] = useState({
    name: "New Training Facility",
    purpose: "Equipment upgrades and scholarship access",
    goal_amount: 15000,
    donor_name: "Community Donor",
    donor_email: "donor@example.com",
    donation_amount: 250,
    message: "Supporting the next generation."
  });
  const [ticketForm, setTicketForm] = useState({
    name: "General admission",
    price: 5,
    capacity: 500,
    access_zone: "Main gate",
    buyer_name: "Ticket Buyer",
    buyer_email: "buyer@example.com",
    quantity: 2,
    gate: "Gate A"
  });
  const [invoiceForm, setInvoiceForm] = useState({
    invoice_number: "INV-2026-001",
    title: "Season membership fees",
    amount_due: 500,
    due_on: "2026-06-30",
    memo: "Membership, facility, and program participation.",
    payment_amount: 250,
    method: "card"
  });
  const [reportForm, setReportForm] = useState({
    name: "Weekly intelligence brief",
    category: "intelligence" as ReportCategory,
    default_format: "online" as ReportFormat,
    description: "Performance, attendance, compliance, and commercial signals in one review.",
    title: "Weekly operating intelligence",
    period_start: "2026-06-01",
    period_end: "2026-06-07",
    frequency: "weekly" as ReportFrequency,
    delivery_channels: "in_app,email",
    recipients: "board@example.com,coach@example.com"
  });
  const [insightForm, setInsightForm] = useState({
    title: "Late-match performance drop",
    insight_type: "pattern_detection",
    severity: "warning" as InsightSeverity,
    confidence: 0.82,
    evidence: "Team output drops in final match phases and high-RPE sessions cluster before fixtures.",
    recommendation: "Reduce late-week load and add final-20-minute conditioning scenarios.",
    model_name: "afrolete-insight-fast"
  });
  const [riskForm, setRiskForm] = useState({
    model_name: "injury-risk-v1",
    score: 78,
    drivers: "High acute load, low recovery, match congestion.",
    recommendation: "Reduce session intensity and add wellness check before next match.",
    valid_for_date: "2026-06-08"
  });
  const [billingForm, setBillingForm] = useState({
    plan_code: "growth",
    plan_name: "Growth",
    base_price: 199,
    billing_cycle: "monthly" as BillingCycle,
    included_athletes: 150,
    included_teams: 10,
    included_agent_tasks: 500,
    included_storage_gb: 100,
    per_athlete_price: 1.5,
    per_agent_task_price: 0.05,
    features: "Operations console, AI agents, reports, communications, safeguarding.",
    period_start: "2026-06-01",
    period_end: "2026-06-30",
    seats_purchased: 150,
    negotiated_price: 179,
    meter_code: "agent_tasks",
    meter_name: "AI agent tasks",
    usage_unit: "agent_task" as UsageUnit,
    included_quantity: 500,
    overage_price: 0.05,
    usage_quantity: 650,
    invoice_number: "SAAS-2026-001",
    tax_amount: 0,
    tax_jurisdiction: "KE",
    discount_amount: 20,
    payment_amount: 159,
    prorated_price: 249,
    webhook_provider: "stripe",
    entitlement_feature: "ai_agents",
    entitlement_limit: 12
  });

  const selectedOrganization = useMemo(
    () => organizations.find((organization) => organization.id === selectedOrganizationId) ?? null,
    [organizations, selectedOrganizationId]
  );
  const selectedTeam = useMemo(
    () => teams.find((team) => team.id === selectedTeamId) ?? null,
    [teams, selectedTeamId]
  );
  const selectedEvent = useMemo(
    () => events.find((event) => event.id === selectedEventId) ?? null,
    [events, selectedEventId]
  );
  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) ?? null,
    [agents, selectedAgentId]
  );
  const selectedAthlete = useMemo(
    () => athletes.find((athlete) => athlete.personId === selectedAthleteId) ?? null,
    [athletes, selectedAthleteId]
  );
  const selectedInboxPersonId = selectedAthlete?.personId ?? athletes[0]?.personId ?? "";
  const selectedTrainingPlan = useMemo(
    () => trainingPlans.find((plan) => plan.id === selectedTrainingPlanId) ?? null,
    [trainingPlans, selectedTrainingPlanId]
  );
  const selectedTrainingSession = useMemo(
    () => trainingSessions.find((sessionPlan) => sessionPlan.id === selectedTrainingSessionId) ?? null,
    [trainingSessions, selectedTrainingSessionId]
  );
  const selectedCompetition = useMemo(
    () => competitions.find((competition) => competition.id === selectedCompetitionId) ?? null,
    [competitions, selectedCompetitionId]
  );
  const selectedFixture = useMemo(
    () => competitionFixtures.find((fixture) => fixture.id === selectedFixtureId) ?? null,
    [competitionFixtures, selectedFixtureId]
  );
  const selectedMessage = useMemo(
    () => communicationMessages.find((message) => message.id === selectedMessageId) ?? null,
    [communicationMessages, selectedMessageId]
  );
  const selectedFacility = useMemo(
    () => facilities.find((facility) => facility.id === selectedFacilityId) ?? null,
    [facilities, selectedFacilityId]
  );
  const selectedEquipment = useMemo(
    () => equipmentItems.find((item) => item.id === selectedEquipmentId) ?? null,
    [equipmentItems, selectedEquipmentId]
  );
  const keycloakEnabled = afroleteAuthMode === "keycloak";

  const addLog = useCallback((message: string, tone: LogEntry["tone"] = "neutral") => {
    setLogs((current) => [
      { id: crypto.randomUUID(), message, tone },
      ...current.slice(0, 7)
    ]);
  }, []);

  const runAction = useCallback(
    async <T,>(label: string, action: () => Promise<T>, success: (value: T) => void) => {
      setBusyAction(label);
      try {
        const value = await action();
        success(value);
      } catch (error) {
        addLog(error instanceof Error ? error.message : "Request failed", "bad");
      } finally {
        setBusyAction(null);
      }
    },
    [addLog]
  );

  const beginKeycloakLogin = useCallback(() => {
    setBusyAction("keycloak-login");
    void startKeycloakLogin().catch((error) => {
      setBusyAction(null);
      addLog(error instanceof Error ? error.message : "Keycloak sign-in failed", "bad");
    });
  }, [addLog]);

  const endKeycloakSession = useCallback(() => {
    const logoutUrl = keycloakEnabled ? keycloakLogoutUrl(authSession) : null;
    clearStoredAuthSession();
    setAuthSession(null);
    addLog("Keycloak session cleared", "neutral");
    if (logoutUrl) {
      window.location.assign(logoutUrl);
    }
  }, [addLog, authSession, keycloakEnabled]);

  const loadOrganizations = useCallback(async () => {
    const data = await apiRequest<OrganizationRead[]>("/organizations", { identity });
    setOrganizations(data);
    if (!selectedOrganizationId && data[0]) {
      setSelectedOrganizationId(data[0].id);
    }
  }, [identity, selectedOrganizationId]);

  const loadTeams = useCallback(
    async (organizationId: string) => {
      const data = await apiRequest<TeamRead[]>(`/teams/by-organization/${organizationId}`);
      setTeams(data);
      setSelectedTeamId((current) => (data.some((team) => team.id === current) ? current : data[0]?.id ?? ""));
    },
    []
  );

  const loadEvents = useCallback(async (organizationId: string, teamId?: string) => {
    const query = teamId ? `&team_id=${teamId}` : "";
    const data = await apiRequest<EventRead[]>(`/events?organization_id=${organizationId}${query}`);
    setEvents(data);
    setSelectedEventId((current) => (data.some((event) => event.id === current) ? current : data[0]?.id ?? ""));
  }, []);

  const loadAttendance = useCallback(async (eventId: string) => {
    const data = await apiRequest<AttendanceRecordRead[]>(`/events/${eventId}/attendance`);
    setAttendance(data);
  }, []);

  const loadAgents = useCallback(async (organizationId: string) => {
    const data = await apiRequest<AgentRead[]>(`/agents?organization_id=${organizationId}`);
    setAgents(data);
    setSelectedAgentId((current) =>
      data.some((agent) => agent.id === current) ? current : data[0]?.id ?? ""
    );
  }, []);

  const loadAgentTasks = useCallback(async (organizationId: string, agentId?: string) => {
    const query = agentId ? `&agent_id=${agentId}` : "";
    const [tasks, runs, governance] = await Promise.all([
      apiRequest<AgentTaskRead[]>(`/agents/tasks?organization_id=${organizationId}${query}`),
      apiRequest<AgentRunRecordRead[]>(`/agents/runs?organization_id=${organizationId}`),
      apiRequest<AgentGovernanceSummaryRead>(`/agents/governance?organization_id=${organizationId}`)
    ]);
    setAgentTasks(tasks);
    setAgentRuns(runs);
    setAgentGovernance(governance);
  }, []);

  const loadMetricDefinitions = useCallback(async (organizationId: string) => {
    const data = await apiRequest<MetricDefinitionRead[]>(
      `/performance/metrics?organization_id=${organizationId}`
    );
    setMetricDefinitions(data);
  }, []);

  const loadAthletePerformance = useCallback(
    async (organizationId: string, athleteProfileId: string) => {
      const [observationData, assessmentData, summaryData] = await Promise.all([
        apiRequest<PerformanceObservationRead[]>(
          `/performance/athletes/${athleteProfileId}/observations?organization_id=${organizationId}`
        ),
        apiRequest<AthleteAssessmentRead[]>(
          `/performance/athletes/${athleteProfileId}/assessments?organization_id=${organizationId}`
        ),
        apiRequest<AthletePerformanceSummaryRead>(
          `/performance/athletes/${athleteProfileId}/summary?organization_id=${organizationId}`
        )
      ]);
      setObservations(observationData);
      setAssessments(assessmentData);
      setPerformanceSummary(summaryData);
      setSelectedObservationId((current) =>
        observationData.some((observation) => observation.id === current)
          ? current
          : observationData[0]?.id ?? ""
      );
    },
    []
  );

  const loadTraining = useCallback(async (organizationId: string, teamId?: string) => {
    const teamQuery = teamId ? `&team_id=${teamId}` : "";
    const [drills, plans, sessions] = await Promise.all([
      apiRequest<TrainingDrillRead[]>(`/training/drills?organization_id=${organizationId}`),
      apiRequest<TrainingPlanRead[]>(`/training/plans?organization_id=${organizationId}${teamQuery}`),
      apiRequest<TrainingSessionPlanRead[]>(
        `/training/sessions?organization_id=${organizationId}${teamQuery}`
      )
    ]);
    setTrainingDrills(drills);
    setTrainingPlans(plans);
    setTrainingSessions(sessions);
    setSelectedTrainingPlanId((current) =>
      plans.some((plan) => plan.id === current) ? current : plans[0]?.id ?? ""
    );
    setSelectedTrainingSessionId((current) =>
      sessions.some((sessionPlan) => sessionPlan.id === current) ? current : sessions[0]?.id ?? ""
    );
  }, []);

  const loadTrainingPlanItems = useCallback(async (planId: string) => {
    const data = await apiRequest<TrainingPlanItemRead[]>(`/training/plans/${planId}/items`);
    setTrainingPlanItems(data);
  }, []);

  const loadTrainingFeedback = useCallback(async (sessionPlanId: string) => {
    const data = await apiRequest<TrainingSessionFeedbackRead[]>(
      `/training/sessions/${sessionPlanId}/feedback`
    );
    setTrainingFeedback(data);
  }, []);

  const loadCompetitions = useCallback(async (organizationId: string) => {
    const data = await apiRequest<CompetitionRead[]>(`/competitions?organization_id=${organizationId}`);
    setCompetitions(data);
    setSelectedCompetitionId((current) =>
      data.some((competition) => competition.id === current) ? current : data[0]?.id ?? ""
    );
  }, []);

  const loadCompetitionWorkspace = useCallback(async (competitionId: string) => {
    const [participants, fixtures, standings, bracket, conflicts, ticketing] = await Promise.all([
      apiRequest<CompetitionParticipantRead[]>(`/competitions/${competitionId}/participants`),
      apiRequest<CompetitionFixtureRead[]>(`/competitions/${competitionId}/fixtures`),
      apiRequest<CompetitionStandingRead[]>(`/competitions/${competitionId}/standings`),
      apiRequest<CompetitionBracketRead>(`/competitions/${competitionId}/bracket`),
      apiRequest<CompetitionConflictRead[]>(`/competitions/${competitionId}/conflicts`),
      apiRequest<CompetitionTicketingRead[]>(`/competitions/${competitionId}/ticketing`)
    ]);
    setCompetitionParticipants(participants);
    setCompetitionFixtures(fixtures);
    setCompetitionStandings(standings);
    setCompetitionBracket(bracket);
    setCompetitionConflicts(conflicts);
    setCompetitionTicketing(ticketing);
    setSelectedFixtureId((current) =>
      fixtures.some((fixture) => fixture.id === current) ? current : fixtures[0]?.id ?? ""
    );
  }, []);

  const loadFixtureEvents = useCallback(async (fixtureId: string) => {
    const data = await apiRequest<FixtureMatchEventRead[]>(`/competitions/fixtures/${fixtureId}/events`);
    setMatchEvents(data);
  }, []);

  const loadCommunications = useCallback(async (organizationId: string) => {
    const [templates, messages] = await Promise.all([
      apiRequest<CommunicationTemplateRead[]>(`/communications/templates?organization_id=${organizationId}`),
      apiRequest<CommunicationMessageRead[]>(`/communications/messages?organization_id=${organizationId}`)
    ]);
    setCommunicationTemplates(templates);
    setCommunicationMessages(messages);
    setSelectedMessageId((current) =>
      messages.some((message) => message.id === current) ? current : messages[0]?.id ?? ""
    );
  }, []);

  const loadMessageRecipients = useCallback(async (messageId: string) => {
    const data = await apiRequest<MessageRecipientRead[]>(
      `/communications/messages/${messageId}/recipients`
    );
    setMessageRecipients(data);
  }, []);

  const loadInbox = useCallback(async (organizationId: string, personId: string) => {
    const data = await apiRequest<CommunicationInboxItemRead[]>(
      `/communications/inbox?organization_id=${organizationId}&person_id=${personId}`,
      { identity }
    );
    setInboxItems(data);
  }, [identity]);

  const loadAssets = useCallback(async (organizationId: string, facilityId?: string) => {
    const facilityQuery = facilityId ? `&facility_id=${facilityId}` : "";
    const [
      facilityData,
      equipmentData,
      checkoutData,
      workOrderData,
      bookingData,
      summaryData,
      procurementData,
      supplierOrderData,
      supplierData,
      utilizationData,
      scanEventData,
      readerData,
      leaseScheduleData
    ] = await Promise.all([
      apiRequest<FacilityRead[]>(`/assets/facilities?organization_id=${organizationId}`),
      apiRequest<EquipmentItemRead[]>(`/assets/equipment?organization_id=${organizationId}${facilityQuery}`),
      apiRequest<EquipmentCheckoutRead[]>(`/assets/checkouts?organization_id=${organizationId}`),
      apiRequest<MaintenanceWorkOrderRead[]>(`/assets/work-orders?organization_id=${organizationId}`),
      apiRequest<FacilityBookingRead[]>(`/assets/bookings?organization_id=${organizationId}${facilityQuery}`),
      apiRequest<AssetSummaryRead>(`/assets/summary?organization_id=${organizationId}`),
      apiRequest<ProcurementRecommendationRead[]>(
        `/assets/procurement/recommendations?organization_id=${organizationId}`
      ),
      apiRequest<SupplierOrderRead[]>(`/assets/suppliers/orders?organization_id=${organizationId}`),
      apiRequest<SupplierScoreRead[]>(`/assets/suppliers/scorecard?organization_id=${organizationId}`),
      apiRequest<AssetUtilizationRecommendationRead[]>(
        `/assets/utilization/recommendations?organization_id=${organizationId}`
      ),
      apiRequest<EquipmentScanEventRead[]>(
        `/assets/equipment/rfid-scans?organization_id=${organizationId}`,
        { identity }
      ),
      apiRequest<EquipmentReaderRead[]>(
        `/assets/equipment/rfid-readers?organization_id=${organizationId}`,
        { identity }
      ),
      apiRequest<EquipmentLeaseScheduleRead[]>(`/assets/lease-schedules?organization_id=${organizationId}`)
    ]);
    setFacilities(facilityData);
    setEquipmentItems(equipmentData);
    setEquipmentCheckouts(checkoutData);
    setWorkOrders(workOrderData);
    setFacilityBookings(bookingData);
    setAssetSummary(summaryData);
    setProcurementRecommendations(procurementData);
    setSupplierOrders(supplierOrderData);
    setSupplierScores(supplierData);
    setAssetUtilization(utilizationData);
    setEquipmentScanEvents(scanEventData);
    setEquipmentReaders(readerData);
    setLeaseSchedules(leaseScheduleData);
    setSelectedFacilityId((current) =>
      facilityData.some((facility) => facility.id === current) ? current : facilityData[0]?.id ?? ""
    );
    setSelectedEquipmentId((current) =>
      equipmentData.some((item) => item.id === current) ? current : equipmentData[0]?.id ?? ""
    );
    setSelectedCheckoutId((current) =>
      checkoutData.some((checkout) => checkout.id === current) ? current : checkoutData[0]?.id ?? ""
    );
    setSelectedWorkOrderId((current) =>
      workOrderData.some((workOrder) => workOrder.id === current)
        ? current
        : workOrderData[0]?.id ?? ""
    );
    setSelectedSupplierOrderId((current) =>
      supplierOrderData.some((order) => order.id === current) ? current : supplierOrderData[0]?.id ?? ""
    );
  }, [identity]);

  const loadEquipmentFiles = useCallback(async (equipmentItemId: string) => {
    const data = await apiRequest<EquipmentFileRead[]>(`/assets/equipment/${equipmentItemId}/files`);
    setEquipmentFiles(data);
  }, []);

  const loadCommercial = useCallback(async (organizationId: string) => {
    const [
      sponsorData,
      sponsorshipData,
      campaignData,
      ticketProductData,
      ticketData,
      invoiceData,
      summaryData,
      dashboardData
    ] = await Promise.all([
      apiRequest<SponsorRead[]>(`/commercial/sponsors?organization_id=${organizationId}`),
      apiRequest<SponsorshipAgreementRead[]>(`/commercial/sponsorships?organization_id=${organizationId}`),
      apiRequest<FundraisingCampaignRead[]>(`/commercial/campaigns?organization_id=${organizationId}`),
      apiRequest<TicketProductRead[]>(`/commercial/tickets/products?organization_id=${organizationId}`),
      apiRequest<TicketRead[]>(`/commercial/tickets?organization_id=${organizationId}`),
      apiRequest<FinanceInvoiceRead[]>(`/commercial/invoices?organization_id=${organizationId}`),
      apiRequest<CommercialSummaryRead>(`/commercial/summary?organization_id=${organizationId}`),
      apiRequest<SponsorshipDashboardRead[]>(
        `/commercial/sponsorship-dashboard?organization_id=${organizationId}`
      )
    ]);
    setSponsors(sponsorData);
    setSponsorships(sponsorshipData);
    setCampaigns(campaignData);
    setTicketProducts(ticketProductData);
    setTickets(ticketData);
    setInvoices(invoiceData);
    setCommercialSummary(summaryData);
    setSponsorshipDashboard(dashboardData);
    setSelectedSponsorId((current) =>
      sponsorData.some((sponsor) => sponsor.id === current) ? current : sponsorData[0]?.id ?? ""
    );
    setSelectedCampaignId((current) =>
      campaignData.some((campaign) => campaign.id === current) ? current : campaignData[0]?.id ?? ""
    );
    setSelectedTicketProductId((current) =>
      ticketProductData.some((product) => product.id === current) ? current : ticketProductData[0]?.id ?? ""
    );
    setSelectedTicketId((current) =>
      ticketData.some((ticket) => ticket.id === current) ? current : ticketData[0]?.id ?? ""
    );
    setSelectedInvoiceId((current) =>
      invoiceData.some((invoice) => invoice.id === current) ? current : invoiceData[0]?.id ?? ""
    );
  }, []);

  const loadReporting = useCallback(async (organizationId: string) => {
    const [definitions, reports, schedules, insightData, riskData, exports, charts, benchmarks, summary] =
      await Promise.all([
        apiRequest<ReportDefinitionRead[]>(`/reporting/definitions?organization_id=${organizationId}`),
        apiRequest<GeneratedReportRead[]>(`/reporting/reports?organization_id=${organizationId}`),
        apiRequest<ScheduledReportRead[]>(`/reporting/schedules?organization_id=${organizationId}`),
        apiRequest<IntelligenceInsightRead[]>(`/reporting/insights?organization_id=${organizationId}`),
        apiRequest<PredictiveRiskScoreRead[]>(`/reporting/risk-scores?organization_id=${organizationId}`),
        apiRequest<ReportExportJobRead[]>(`/reporting/exports?organization_id=${organizationId}`),
        apiRequest<ReportChartRead[]>(`/reporting/charts?organization_id=${organizationId}`),
        apiRequest<ReportingBenchmarkRead[]>(`/reporting/benchmarks?organization_id=${organizationId}`),
        apiRequest<ReportingSummaryRead>(`/reporting/summary?organization_id=${organizationId}`)
      ]);
    setReportDefinitions(definitions);
    setGeneratedReports(reports);
    setScheduledReports(schedules);
    setInsights(insightData);
    setRiskScores(riskData);
    setReportExports(exports);
    setReportCharts(charts);
    setReportingBenchmarks(benchmarks);
    setReportingSummary(summary);
    setSelectedReportDefinitionId((current) =>
      definitions.some((definition) => definition.id === current)
        ? current
        : definitions[0]?.id ?? ""
    );
    setSelectedGeneratedReportId((current) =>
      reports.some((report) => report.id === current) ? current : reports[0]?.id ?? ""
    );
    setSelectedInsightId((current) =>
      insightData.some((insight) => insight.id === current) ? current : insightData[0]?.id ?? ""
    );
  }, []);

  const loadBilling = useCallback(async (organizationId: string) => {
    const [plans, subscriptionsData, meters, records, invoicesData, entitlements, summary] =
      await Promise.all([
        apiRequest<BillingPlanRead[]>("/billing/plans"),
        apiRequest<SubscriptionRead[]>(`/billing/subscriptions?organization_id=${organizationId}`),
        apiRequest<UsageMeterRead[]>("/billing/meters"),
        apiRequest<UsageRecordRead[]>(`/billing/usage?organization_id=${organizationId}`),
        apiRequest<SaaSInvoiceRead[]>(`/billing/invoices?organization_id=${organizationId}`),
        apiRequest<BillingEntitlementRead[]>(`/billing/entitlements?organization_id=${organizationId}`),
        apiRequest<BillingSummaryRead>(`/billing/summary?organization_id=${organizationId}`)
      ]);
    setBillingPlans(plans);
    setSubscriptions(subscriptionsData);
    setUsageMeters(meters);
    setUsageRecords(records);
    setSaasInvoices(invoicesData);
    setBillingEntitlements(entitlements);
    setBillingSummary(summary);
    setSelectedBillingPlanId((current) =>
      plans.some((plan) => plan.id === current) ? current : plans[0]?.id ?? ""
    );
    setSelectedSubscriptionId((current) =>
      subscriptionsData.some((subscription) => subscription.id === current)
        ? current
        : subscriptionsData[0]?.id ?? ""
    );
    setSelectedUsageMeterId((current) =>
      meters.some((meter) => meter.id === current) ? current : meters[0]?.id ?? ""
    );
    setSelectedSaasInvoiceId((current) =>
      invoicesData.some((invoice) => invoice.id === current) ? current : invoicesData[0]?.id ?? ""
    );
  }, []);

  useEffect(() => {
    const stored = window.localStorage.getItem("afrolete.localIdentity");
    if (stored) {
      setIdentity(JSON.parse(stored) as LocalIdentity);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("afrolete.localIdentity", JSON.stringify(identity));
  }, [identity]);

  useEffect(() => {
    if (!keycloakEnabled) {
      return;
    }

    const hadCallback = new URLSearchParams(window.location.search).has("code");
    let active = true;

    completeKeycloakCallbackFromUrl()
      .then((session) => {
        if (!active) {
          return;
        }
        setAuthSession(session);
        if (session && hadCallback) {
          addLog("Keycloak session established", "good");
        }
      })
      .catch((error) => {
        if (!active) {
          return;
        }
        setAuthSession(null);
        addLog(error instanceof Error ? error.message : "Keycloak sign-in failed", "bad");
      });

    return () => {
      active = false;
    };
  }, [addLog, keycloakEnabled]);

  useEffect(() => {
    if (!authSession) {
      return;
    }
    setIdentity((current) => ({
      sub: authSession.subject ?? current.sub,
      email: authSession.email ?? current.email,
      name: authSession.name ?? authSession.email ?? current.name
    }));
  }, [authSession]);

  useEffect(() => {
    if (keycloakEnabled && !authSession) {
      return;
    }
    runAction("load-organizations", loadOrganizations, () => addLog("Workspace synchronized", "good"));
  }, [authSession, keycloakEnabled, loadOrganizations, runAction, addLog]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      setTeams([]);
      setEvents([]);
      setAgents([]);
      setAgentTasks([]);
      setAgentRuns([]);
      setAgentGovernance(null);
      setMetricDefinitions([]);
      setObservations([]);
      setPerformanceIngestion(null);
      setAssessments([]);
      setPerformanceSummary(null);
      setTrainingDrills([]);
      setTrainingPlans([]);
      setTrainingSessions([]);
      setTrainingPlanItems([]);
      setTrainingFeedback([]);
      setTrainingAvailability(null);
      setGeneratedTrainingPlan(null);
      setCompetitions([]);
      setCompetitionParticipants([]);
      setCompetitionFixtures([]);
      setCompetitionStandings([]);
      setFixtureGeneration(null);
      setCompetitionAdvancement(null);
      setScheduleOptimization(null);
      setCompetitionBroadcast(null);
      setCompetitionTicketing([]);
      setCompetitionBracket(null);
      setCompetitionConflicts([]);
      setMatchEvents([]);
      setOfficialAssignments([]);
      setCommunicationTemplates([]);
      setCommunicationMessages([]);
      setMessageRecipients([]);
      setInboxItems([]);
      setDigestSummary(null);
      setDigestRun(null);
      setDraftPreview(null);
      setNotificationPreference(null);
      setFacilities([]);
      setEquipmentItems([]);
      setEquipmentFiles([]);
      setEquipmentScanEvents([]);
      setEquipmentReaders([]);
      setRfidProvision(null);
      setEquipmentCheckouts([]);
      setWorkOrders([]);
      setFacilityBookings([]);
      setAssetSummary(null);
      setProcurementRecommendations([]);
      setSupplierOrders([]);
      setSupplierScores([]);
      setSupplierSubmission(null);
      setSupplierInvoiceSync(null);
      setAssetUtilization([]);
      setLeaseQuote(null);
      setLeaseInvoice(null);
      setLeaseSchedules([]);
      setLeasePayment(null);
      setSponsors([]);
      setSponsorships([]);
      setCampaigns([]);
      setDonations([]);
      setTicketProducts([]);
      setTicketOrders([]);
      setTickets([]);
      setInvoices([]);
      setPayments([]);
      setCommercialSummary(null);
      setTaxQuote(null);
      setPaymentSettlement(null);
      setAccountingExport(null);
      setCommercialRefund(null);
      setSponsorshipDashboard([]);
      setReportDefinitions([]);
      setGeneratedReports([]);
      setScheduledReports([]);
      setInsights([]);
      setRiskScores([]);
      setReportExports([]);
      setRenderedReport(null);
      setReportArtifactAccess(null);
      setReportVerification(null);
      setReportCharts([]);
      setReportingBenchmarks([]);
      setReportingSummary(null);
      setBillingPlans([]);
      setSubscriptions([]);
      setUsageMeters([]);
      setUsageRecords([]);
      setSaasInvoices([]);
      setSaasPayments([]);
      setBillingEntitlements([]);
      setBillingTaxQuote(null);
      setBillingTaxFiling(null);
      setBillingProration(null);
      setBillingPlanChange(null);
      setBillingDunning(null);
      setBillingDunningDelivery(null);
      setBillingWebhook(null);
      setBillingSummary(null);
      return;
    }
    runAction("load-tenant-data", async () => {
      await loadTeams(selectedOrganizationId);
      await loadEvents(selectedOrganizationId);
      await loadAgents(selectedOrganizationId);
      await loadAgentTasks(selectedOrganizationId);
      await loadMetricDefinitions(selectedOrganizationId);
      await loadTraining(selectedOrganizationId);
      await loadCompetitions(selectedOrganizationId);
      await loadCommunications(selectedOrganizationId);
      await loadAssets(selectedOrganizationId);
      await loadCommercial(selectedOrganizationId);
      await loadReporting(selectedOrganizationId);
      await loadBilling(selectedOrganizationId);
    }, () => addLog("Organization workspace loaded", "good"));
  }, [
    selectedOrganizationId,
    loadTeams,
    loadEvents,
    loadAgents,
    loadAgentTasks,
    loadMetricDefinitions,
    loadTraining,
    loadCompetitions,
    loadCommunications,
    loadAssets,
    loadCommercial,
    loadReporting,
    loadBilling,
    runAction,
    addLog
  ]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "load-team-events",
      async () => {
        await loadEvents(selectedOrganizationId, selectedTeamId || undefined);
        await loadTraining(selectedOrganizationId, selectedTeamId || undefined);
      },
      () => addLog("Team lanes refreshed", "good")
    );
  }, [selectedTeamId, selectedOrganizationId, loadEvents, loadTraining, runAction, addLog]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "load-assets",
      () => loadAssets(selectedOrganizationId, selectedFacilityId || undefined),
      () => undefined
    );
  }, [selectedFacilityId, selectedOrganizationId, loadAssets, runAction]);

  useEffect(() => {
    if (!selectedEquipmentId) {
      setEquipmentFiles([]);
      return;
    }
    runAction(
      "load-equipment-files",
      () => loadEquipmentFiles(selectedEquipmentId),
      () => undefined
    );
  }, [selectedEquipmentId, loadEquipmentFiles, runAction]);

  useEffect(() => {
    if (!selectedEventId) {
      setAttendance([]);
      return;
    }
    runAction("load-attendance", () => loadAttendance(selectedEventId), () => undefined);
  }, [selectedEventId, loadAttendance, runAction]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "load-agent-tasks",
      () => loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined),
      () => undefined
    );
  }, [selectedAgentId, selectedOrganizationId, loadAgentTasks, runAction]);

  useEffect(() => {
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId) {
      setObservations([]);
      setAssessments([]);
      setPerformanceSummary(null);
      return;
    }
    runAction(
      "load-athlete-performance",
      () => loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId),
      () => undefined
    );
  }, [selectedAthlete, selectedOrganizationId, loadAthletePerformance, runAction]);

  useEffect(() => {
    if (!selectedTrainingPlanId) {
      setTrainingPlanItems([]);
      return;
    }
    runAction(
      "load-training-plan-items",
      () => loadTrainingPlanItems(selectedTrainingPlanId),
      () => undefined
    );
  }, [selectedTrainingPlanId, loadTrainingPlanItems, runAction]);

  useEffect(() => {
    if (!selectedTrainingSessionId) {
      setTrainingFeedback([]);
      return;
    }
    runAction(
      "load-training-feedback",
      () => loadTrainingFeedback(selectedTrainingSessionId),
      () => undefined
    );
  }, [selectedTrainingSessionId, loadTrainingFeedback, runAction]);

  useEffect(() => {
    if (!selectedCompetitionId) {
      setCompetitionParticipants([]);
      setCompetitionFixtures([]);
      setCompetitionStandings([]);
      setFixtureGeneration(null);
      setCompetitionAdvancement(null);
      setScheduleOptimization(null);
      setCompetitionBroadcast(null);
      setCompetitionTicketing([]);
      setCompetitionBracket(null);
      setCompetitionConflicts([]);
      setMatchEvents([]);
      setOfficialAssignments([]);
      return;
    }
    runAction(
      "load-competition-workspace",
      () => loadCompetitionWorkspace(selectedCompetitionId),
      () => undefined
    );
  }, [selectedCompetitionId, loadCompetitionWorkspace, runAction]);

  useEffect(() => {
    if (!selectedFixtureId) {
      setMatchEvents([]);
      setOfficialAssignments([]);
      return;
    }
    runAction("load-fixture-events", () => loadFixtureEvents(selectedFixtureId), () => undefined);
  }, [selectedFixtureId, loadFixtureEvents, runAction]);

  useEffect(() => {
    if (!selectedMessageId) {
      setMessageRecipients([]);
      return;
    }
    runAction(
      "load-message-recipients",
      () => loadMessageRecipients(selectedMessageId),
      () => undefined
    );
  }, [selectedMessageId, loadMessageRecipients, runAction]);

  useEffect(() => {
    if (!selectedOrganizationId || !selectedInboxPersonId) {
      setInboxItems([]);
      return;
    }
    runAction(
      "load-communication-inbox",
      () => loadInbox(selectedOrganizationId, selectedInboxPersonId),
      () => undefined
    );
  }, [selectedInboxPersonId, selectedOrganizationId, loadInbox, runAction]);

  const createOrganization = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    runAction(
      "create-organization",
      () =>
        apiRequest<OrganizationRead>("/organizations", {
          method: "POST",
          identity,
          body: {
            ...organizationForm,
            mission: "Build an accountable athlete development pathway."
          }
        }),
      (organization) => {
        setOrganizations((current) => [organization, ...current.filter((item) => item.id !== organization.id)]);
        setSelectedOrganizationId(organization.id);
        addLog(`${organization.name} is ready`, "good");
      }
    );
  };

  const createTeam = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId) {
      addLog("Create or select an organization first", "bad");
      return;
    }
    runAction(
      "create-team",
      () =>
        apiRequest<TeamRead>("/teams", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...teamForm
          }
        }),
      (team) => {
        setTeams((current) => [team, ...current.filter((item) => item.id !== team.id)]);
        setSelectedTeamId(team.id);
        addLog(`${team.name} roster lane opened`, "good");
      }
    );
  };

  const addAthlete = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId || !selectedTeamId) {
      addLog("Select an organization and team first", "bad");
      return;
    }

    runAction(
      "add-athlete",
      async () => {
        const member = await apiRequest<MembershipRead>(`/organizations/${selectedOrganizationId}/members`, {
          method: "POST",
          identity,
          body: {
            email: athleteForm.email,
            display_name: athleteForm.display_name,
            role: "athlete",
            title: athleteForm.primary_position
          }
        });
        const roster = await apiRequest<TeamRosterEntryRead>(`/teams/${selectedTeamId}/members`, {
          method: "POST",
          identity,
          body: {
            person_id: member.subject_id,
            role: athleteForm.role,
            status: athleteForm.role === "substitute" ? "substitute" : "active",
            primary_position: athleteForm.primary_position,
            jersey_number: athleteForm.jersey_number,
            is_captain: athleteForm.is_captain
          }
        });
        return { member, roster };
      },
      ({ member, roster }) => {
        const athlete = {
          personId: member.subject_id,
          athleteProfileId: roster.athlete_profile_id,
          name: athleteForm.display_name,
          email: athleteForm.email,
          rosterEntryId: roster.id
        };
        setAthletes((current) => [athlete, ...current.filter((item) => item.personId !== athlete.personId)]);
        setSelectedAthleteId(athlete.personId);
        addLog(`${athlete.name} joined ${selectedTeam?.name ?? "the team"}`, "good");
      }
    );
  };

  const createEvent = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const startsAt = new Date(eventForm.starts_at);
    const endsAt = new Date(startsAt.getTime() + eventForm.duration_minutes * 60_000);

    runAction(
      "create-event",
      () =>
        apiRequest<EventRead>("/events", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId || null,
            event_type: eventForm.event_type,
            title: eventForm.title,
            starts_at: startsAt.toISOString(),
            ends_at: endsAt.toISOString(),
            timezone: eventForm.timezone,
            venue_name: eventForm.venue_name,
            notes: eventForm.notes
          }
        }),
      (createdEvent) => {
        setEvents((current) => [createdEvent, ...current.filter((item) => item.id !== createdEvent.id)]);
        setSelectedEventId(createdEvent.id);
        addLog(`${createdEvent.title} scheduled`, "good");
      }
    );
  };

  const seedAttendance = () => {
    if (!selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      "seed-attendance",
      () =>
        apiRequest<AttendanceSeedRead>(`/events/${selectedEventId}/attendance/from-roster`, {
          method: "POST",
          identity
        }),
      (seed) => {
        addLog(`Attendance seeded: ${seed.created} created, ${seed.existing} existing`, "good");
        void loadAttendance(selectedEventId);
      }
    );
  };

  const recordAttendance = (personId: string, status: AttendanceStatus) => {
    if (!selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      `attendance-${personId}-${status}`,
      () =>
        apiRequest<AttendanceRecordRead>(`/events/${selectedEventId}/attendance`, {
          method: "POST",
          identity,
          body: {
            person_id: personId,
            status,
            note: `${status} from AfroLete console`
          }
        }),
      (record) => {
        setAttendance((current) => [record, ...current.filter((item) => item.person_id !== record.person_id)]);
        addLog(`Attendance recorded as ${record.status}`, "good");
      }
    );
  };

  const createGuardian = () => {
    if (!selectedOrganizationId || !selectedAthleteId) {
      addLog("Select an athlete first", "bad");
      return;
    }
    runAction(
      "create-guardian",
      () =>
        apiRequest<GuardianRelationshipRead>("/safeguarding/guardians", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_person_id: selectedAthleteId,
            guardian_email: guardianForm.guardian_email,
            guardian_phone: guardianForm.guardian_phone,
            guardian_display_name: guardianForm.guardian_display_name,
            relationship_kind: "parent",
            can_sign_consent: true,
            emergency_contact: true,
            is_primary: true
          }
        }),
      (guardian) => {
        setGuardians((current) => [guardian, ...current.filter((item) => item.id !== guardian.id)]);
        addLog(`${guardianForm.guardian_display_name} linked as guardian`, "good");
      }
    );
  };

  const requestConsent = () => {
    const guardian = guardians.find((item) => item.athlete_person_id === selectedAthleteId);
    if (!selectedOrganizationId || !selectedEventId || !selectedAthleteId || !guardian) {
      addLog("Select an athlete, event, and guardian first", "bad");
      return;
    }
    runAction(
      "request-consent",
      () =>
        apiRequest<ConsentRequestRead>("/safeguarding/consent-requests", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_person_id: selectedAthleteId,
            guardian_person_id: guardian.guardian_person_id,
            scope_type: "event",
            scope_id: selectedEventId,
            channel: "email",
            destination: guardianForm.guardian_email,
            notes: `Consent for ${selectedEvent?.title ?? "event"}`
          }
        }),
      (request) => {
        setConsentRequest(request);
        addLog("Consent request created", "good");
      }
    );
  };

  const checkClearance = () => {
    if (!selectedEventId || !selectedAthleteId) {
      addLog("Select an event and athlete first", "bad");
      return;
    }
    runAction(
      "check-clearance",
      () =>
        apiRequest<ParticipationClearanceRead>(
          `/safeguarding/events/${selectedEventId}/athletes/${selectedAthleteId}/clearance`
        ),
      (value) => {
        setClearance(value);
        addLog(`Clearance: ${value.status}`, value.status === "cleared" ? "good" : "neutral");
      }
    );
  };

  const createAgent = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-agent",
      () =>
        apiRequest<AgentRead>("/agents", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...agentForm
          }
        }),
      (agent) => {
        setAgents((current) => [agent, ...current.filter((item) => item.id !== agent.id)]);
        setSelectedAgentId(agent.id);
        addLog(`${agent.name} is active`, "good");
        void loadAgentTasks(selectedOrganizationId);
      }
    );
  };

  const assignAgent = (scopeType: "organization" | "team" | "event") => {
    if (!selectedOrganizationId || !selectedAgentId) {
      addLog("Select an organization and agent first", "bad");
      return;
    }
    const scopeId =
      scopeType === "organization"
        ? selectedOrganizationId
        : scopeType === "team"
          ? selectedTeamId
          : selectedEventId;
    if (!scopeId) {
      addLog(`Select a ${scopeType} first`, "bad");
      return;
    }
    runAction(
      `assign-agent-${scopeType}`,
      () =>
        apiRequest<AgentAssignmentRead>(`/agents/${selectedAgentId}/assignments`, {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            scope_type: scopeType,
            scope_id: scopeId
          }
        }),
      (assignment) => addLog(`Agent assigned to ${assignment.scope_type}`, "good")
    );
  };

  const queueAgentTask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId || !selectedAgentId) {
      addLog("Select an organization and agent first", "bad");
      return;
    }
    runAction(
      "queue-agent-task",
      () =>
        apiRequest<AgentTaskRead>(`/agents/${selectedAgentId}/tasks`, {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...taskForm,
            input_ref: selectedEventId ? `event:${selectedEventId}` : taskForm.input_ref
          }
        }),
      (task) => {
        setAgentTasks((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        addLog(`${selectedAgent?.name ?? "Agent"} task queued`, "good");
        void loadAgentTasks(selectedOrganizationId, selectedAgentId);
      }
    );
  };

  const updateAgentTask = (taskId: string, status: AgentTaskStatus) => {
    runAction(
      `agent-task-${taskId}-${status}`,
      () =>
        apiRequest<AgentTaskRead>(`/agents/tasks/${taskId}`, {
          method: "PATCH",
          identity,
          body: {
            status,
            output_ref: status === "completed" ? `reviewed:${taskId}` : undefined,
            review_notes:
              status === "waiting_for_review"
                ? "Agent output needs human review before action."
                : `Marked ${status} from the command console.`
          }
        }),
      (task) => {
        setAgentTasks((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        addLog(`Task moved to ${task.status}`, "good");
        if (selectedOrganizationId) {
          void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
        }
      }
    );
  };

  const executeAgentTask = (taskId: string) => {
    runAction(
      `agent-task-${taskId}-execute`,
      () =>
        apiRequest<AgentTaskRead>(`/agents/tasks/${taskId}/execute`, {
          method: "POST",
          identity
        }),
      (task) => {
        setAgentTasks((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        addLog(`Agent output is ${task.status}`, task.status === "failed" ? "bad" : "good");
        if (selectedOrganizationId) {
          void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
        }
      }
    );
  };

  const refreshAgentTelemetry = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "refresh-agent-telemetry",
      () => loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined),
      () => addLog("Agent governance telemetry refreshed", "good")
    );
  };

  const createMetricDefinition = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-metric",
      () =>
        apiRequest<MetricDefinitionRead>("/performance/metrics", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            sport: selectedTeam?.sport ?? organizationForm.primary_sport,
            ...metricForm,
            description: `${metricForm.name} tracked from the command console.`
          }
        }),
      (metric) => {
        setMetricDefinitions((current) => [
          metric,
          ...current.filter((item) => item.id !== metric.id)
        ]);
        addLog(`${metric.name} metric is available`, "good");
      }
    );
  };

  const recordObservation = () => {
    const metric = metricDefinitions[0];
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId || !metric) {
      addLog("Select an athlete and create a metric first", "bad");
      return;
    }
    runAction(
      "record-observation",
      () =>
        apiRequest<PerformanceObservationRead>(
          `/performance/athletes/${selectedAthlete.athleteProfileId}/observations`,
          {
            method: "POST",
            identity,
            body: {
              organization_id: selectedOrganizationId,
              metric_definition_id: metric.id,
              event_id: selectedEventId || null,
              value: observationForm.value,
              raw_value: observationForm.raw_value,
              source: observationForm.source,
              confidence: observationForm.confidence,
              notes: observationForm.notes
            }
          }
        ),
      (observation) => {
        setObservations((current) => [
          observation,
          ...current.filter((item) => item.id !== observation.id)
        ]);
        addLog(`Observation recorded: ${observation.value}`, "good");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const ingestPerformanceEvidence = () => {
    const metric = metricDefinitions[0];
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId || !metric) {
      addLog("Select an athlete and create a metric first", "bad");
      return;
    }
    runAction(
      "ingest-performance-evidence",
      () =>
        apiRequest<PerformanceIngestionRead>("/performance/ingest", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_profile_id: selectedAthlete.athleteProfileId,
            metric_definition_id: metric.id,
            event_id: selectedEventId || null,
            source: observationForm.source,
            evidence_ref: observationForm.evidence_ref,
            evidence_text: observationForm.evidence_text,
            extracted_value: observationForm.value,
            confidence: observationForm.confidence
          }
        }),
      (ingestion) => {
        setPerformanceIngestion(ingestion);
        setObservations((current) => [
          ingestion.observation,
          ...current.filter((item) => item.id !== ingestion.observation.id)
        ]);
        setSelectedObservationId(ingestion.observation.id);
        addLog(`${ingestion.extractor} queued observation review`, "good");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const reviewSelectedObservation = () => {
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId || !selectedObservationId) {
      addLog("Select an ingested observation first", "bad");
      return;
    }
    runAction(
      "review-performance-observation",
      () =>
        apiRequest<PerformanceObservationRead>(
          `/performance/observations/${selectedObservationId}/review`,
          {
            method: "PATCH",
            identity,
            body: {
              verification_status: "verified",
              value: observationForm.value,
              notes: `Human reviewed from console. ${observationForm.notes}`
            }
          }
        ),
      (observation) => {
        setObservations((current) => [
          observation,
          ...current.filter((item) => item.id !== observation.id)
        ]);
        addLog(`Observation verified: ${observation.value}`, "good");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const recordAssessment = () => {
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId) {
      addLog("Select an athlete first", "bad");
      return;
    }
    runAction(
      "record-assessment",
      () =>
        apiRequest<AthleteAssessmentRead>(
          `/performance/athletes/${selectedAthlete.athleteProfileId}/assessments`,
          {
            method: "POST",
            identity,
            body: {
              organization_id: selectedOrganizationId,
              event_id: selectedEventId || null,
              ...assessmentForm
            }
          }
        ),
      (assessment) => {
        setAssessments((current) => [
          assessment,
          ...current.filter((item) => item.id !== assessment.id)
        ]);
        addLog(`Assessment ALS ${assessment.overall_score}`, "good");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const createTrainingDrill = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-training-drill",
      () =>
        apiRequest<TrainingDrillRead>("/training/drills", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            sport: selectedTeam?.sport ?? organizationForm.primary_sport,
            ...drillForm
          }
        }),
      (drill) => {
        setTrainingDrills((current) => [
          drill,
          ...current.filter((item) => item.id !== drill.id)
        ]);
        addLog(`${drill.name} added to the drill library`, "good");
      }
    );
  };

  const createTrainingPlan = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const planPayload = {
      title: trainingPlanForm.title,
      focus_area: trainingPlanForm.focus_area,
      period_start: trainingPlanForm.period_start,
      period_end: trainingPlanForm.period_end,
      load_guidance: trainingPlanForm.load_guidance,
      recovery_protocol: trainingPlanForm.recovery_protocol,
      progress_checkpoints: trainingPlanForm.progress_checkpoints
    };
    runAction(
      "create-training-plan",
      () =>
        apiRequest<TrainingPlanRead>("/training/plans", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId || null,
            athlete_profile_id: selectedAthlete?.athleteProfileId ?? null,
            ai_generated: true,
            source_summary:
              typeof performanceSummary?.latest_overall_score === "number"
                ? `Latest ALS ${performanceSummary.latest_overall_score} informs this plan.`
                : "Plan created from coach inputs.",
            ...planPayload
          }
        }),
      (plan) => {
        setTrainingPlans((current) => [plan, ...current.filter((item) => item.id !== plan.id)]);
        setSelectedTrainingPlanId(plan.id);
        addLog(`${plan.title} opened for session planning`, "good");
      }
    );
  };

  const generateTrainingPlan = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "generate-training-plan",
      () =>
        apiRequest<GeneratedTrainingPlanRead>("/training/plans/generate", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId || null,
            athlete_profile_id: selectedAthlete?.athleteProfileId ?? null,
            title: `AI ${trainingPlanForm.focus_area} plan`,
            focus_area: trainingPlanForm.focus_area,
            period_start: trainingPlanForm.period_start,
            period_end: trainingPlanForm.period_end,
            weekly_sessions: trainingPlanForm.weekly_sessions,
            readiness_score: trainingPlanForm.readiness_score,
            upcoming_competition_weight: competitionFixtures.length ? 8 : 5
          }
        }),
      (generated) => {
        setGeneratedTrainingPlan(generated);
        setTrainingPlans((current) => [
          generated.plan,
          ...current.filter((item) => item.id !== generated.plan.id)
        ]);
        setTrainingPlanItems(generated.items);
        setSelectedTrainingPlanId(generated.plan.id);
        addLog(`AI generated ${generated.items.length} training sessions`, "good");
        void loadTraining(selectedOrganizationId, selectedTeamId || undefined);
      }
    );
  };

  const addTrainingPlanItem = () => {
    if (!selectedTrainingPlanId) {
      addLog("Create or select a training plan first", "bad");
      return;
    }
    const drill = trainingDrills[0];
    runAction(
      "add-training-plan-item",
      () =>
        apiRequest<TrainingPlanItemRead>(`/training/plans/${selectedTrainingPlanId}/items`, {
          method: "POST",
          identity,
          body: {
            drill_id: drill?.id ?? null,
            sequence: trainingPlanItems.length + 1,
            focus_area: drill?.focus_area ?? trainingPlanForm.focus_area,
            ...trainingItemForm
          }
        }),
      (item) => {
        setTrainingPlanItems((current) => [
          item,
          ...current.filter((planItem) => planItem.id !== item.id)
        ]);
        addLog(`${item.title} added to the weekly structure`, "good");
      }
    );
  };

  const createTrainingSession = () => {
    if (!selectedOrganizationId || !selectedTeamId) {
      addLog("Select an organization and team first", "bad");
      return;
    }
    const scheduledFor = new Date(trainingSessionForm.scheduled_for);
    runAction(
      "create-training-session",
      () =>
        apiRequest<TrainingSessionPlanRead>("/training/sessions", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId,
            plan_id: selectedTrainingPlanId || null,
            event_id: selectedEvent?.event_type === "training" ? selectedEvent.id : null,
            title: trainingSessionForm.title,
            scheduled_for: scheduledFor.toISOString(),
            duration_minutes: trainingSessionForm.duration_minutes,
            rpe_target: trainingSessionForm.rpe_target,
            objectives: trainingSessionForm.objectives
          }
        }),
      (sessionPlan) => {
        setTrainingSessions((current) => [
          sessionPlan,
          ...current.filter((item) => item.id !== sessionPlan.id)
        ]);
        setSelectedTrainingSessionId(sessionPlan.id);
        addLog(`Session load ${sessionPlan.load_score} planned`, "good");
      }
    );
  };

  const recordTrainingFeedback = () => {
    if (!selectedTrainingSessionId) {
      addLog("Select a training session first", "bad");
      return;
    }
    runAction(
      "record-training-feedback",
      () =>
        apiRequest<TrainingSessionFeedbackRead>(
          `/training/sessions/${selectedTrainingSessionId}/feedback`,
          {
            method: "POST",
            identity,
            body: {
              athlete_profile_id: selectedAthlete?.athleteProfileId ?? null,
              readiness_score: trainingFeedbackForm.readiness_score,
              soreness_score: trainingFeedbackForm.soreness_score,
              sleep_quality: trainingFeedbackForm.sleep_quality,
              mood_score: trainingFeedbackForm.mood_score,
              actual_rpe: trainingFeedbackForm.actual_rpe,
              actual_duration_minutes: trainingFeedbackForm.actual_duration_minutes,
              completed: trainingFeedbackForm.completed,
              feedback: trainingFeedbackForm.feedback,
              coach_notes: trainingFeedbackForm.coach_notes
            }
          }
        ),
      (feedback) => {
        setTrainingFeedback((current) => [
          feedback,
          ...current.filter((item) => item.id !== feedback.id)
        ]);
        addLog(`${feedback.readiness_band} readiness · ${feedback.recommendation}`, "good");
        if (selectedOrganizationId) {
          void loadTraining(selectedOrganizationId, selectedTeamId || undefined);
        }
      }
    );
  };

  const suggestTrainingAvailability = () => {
    if (!selectedOrganizationId || !selectedTeamId) {
      addLog("Select an organization and team first", "bad");
      return;
    }
    runAction(
      "suggest-training-availability",
      () =>
        apiRequest<TrainingAvailabilityRead>("/training/availability", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId,
            starts_at: new Date(trainingSessionForm.scheduled_for).toISOString(),
            days: 7,
            duration_minutes: trainingSessionForm.duration_minutes,
            earliest_hour: 6,
            latest_hour: 20
          }
        }),
      (availability) => {
        setTrainingAvailability(availability);
        const best = availability.slots[0];
        if (best) {
          const localDate = new Date(best.starts_at);
          setTrainingSessionForm((current) => ({
            ...current,
            scheduled_for: localDate.toISOString().slice(0, 16)
          }));
          addLog(`Best training slot scored ${best.score}`, "good");
        }
      }
    );
  };

  const createCompetition = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-competition",
      () =>
        apiRequest<CompetitionRead>("/competitions", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...competitionForm
          }
        }),
      (competition) => {
        setCompetitions((current) => [
          competition,
          ...current.filter((item) => item.id !== competition.id)
        ]);
        setSelectedCompetitionId(competition.id);
        addLog(`${competition.name} competition workspace created`, "good");
      }
    );
  };

  const registerCompetitionTeam = () => {
    if (!selectedCompetitionId || !selectedTeamId) {
      addLog("Select a competition and team first", "bad");
      return;
    }
    runAction(
      "register-competition-team",
      () =>
        apiRequest<CompetitionParticipantRead>(
          `/competitions/${selectedCompetitionId}/participants`,
          {
            method: "POST",
            identity,
            body: {
              team_id: selectedTeamId,
              seed: competitionParticipants.length + 1,
              group_label: "A"
            }
          }
        ),
      (participant) => {
        setCompetitionParticipants((current) => [
          participant,
          ...current.filter((item) => item.id !== participant.id)
        ]);
        addLog(`${participant.team_name} registered`, "good");
        void loadCompetitionWorkspace(selectedCompetitionId);
      }
    );
  };

  const createCompetitionFixture = () => {
    if (!selectedCompetitionId || competitionParticipants.length < 2) {
      addLog("Register at least two teams first", "bad");
      return;
    }
    const [home, away] = competitionParticipants;
    runAction(
      "create-competition-fixture",
      () =>
        apiRequest<CompetitionFixtureRead>(`/competitions/${selectedCompetitionId}/fixtures`, {
          method: "POST",
          identity,
          body: {
            home_team_id: home.team_id,
            away_team_id: away.team_id,
            round_label: fixtureForm.round_label,
            stage_label: fixtureForm.stage_label,
            scheduled_at: new Date(fixtureForm.scheduled_at).toISOString(),
            venue_name: fixtureForm.venue_name,
            notes: `Fixture in ${selectedCompetition?.name ?? "competition"}`
          }
        }),
      (fixture) => {
        setCompetitionFixtures((current) => [
          fixture,
          ...current.filter((item) => item.id !== fixture.id)
        ]);
        setSelectedFixtureId(fixture.id);
        addLog(`${fixture.home_team_name} vs ${fixture.away_team_name} scheduled`, "good");
      }
    );
  };

  const generateCompetitionFixtures = () => {
    if (!selectedCompetitionId || competitionParticipants.length < 2) {
      addLog("Register at least two teams first", "bad");
      return;
    }
    runAction(
      "generate-competition-fixtures",
      () =>
        apiRequest<CompetitionFixtureGenerationRead>(
          `/competitions/${selectedCompetitionId}/fixtures/generate`,
          {
            method: "POST",
            identity,
            body: {
              starts_at: new Date(fixtureForm.scheduled_at).toISOString(),
              interval_days: 7,
              match_spacing_minutes: 120,
              venue_name: fixtureForm.venue_name,
              stage_label: fixtureForm.stage_label || "Regular season",
              double_round_robin: selectedCompetition?.format === "round_robin"
            }
          }
        ),
      (generation) => {
        setFixtureGeneration(generation);
        addLog(`${generation.created} fixtures generated across ${generation.rounds} rounds`, "good");
        void loadCompetitionWorkspace(selectedCompetitionId);
      }
    );
  };

  const reviewCompetitionConflicts = () => {
    if (!selectedCompetitionId) {
      addLog("Select a competition first", "bad");
      return;
    }
    runAction(
      "review-competition-conflicts",
      () => loadCompetitionWorkspace(selectedCompetitionId),
      () => addLog("Competition conflicts refreshed", "good")
    );
  };

  const advanceCompetitionRound = () => {
    if (!selectedCompetitionId) {
      addLog("Select a competition first", "bad");
      return;
    }
    runAction(
      "advance-competition-round",
      () =>
        apiRequest<CompetitionAdvancementRead>(
          `/competitions/${selectedCompetitionId}/advance`,
          {
            method: "POST",
            identity,
            body: {
              source_stage_label: fixtureForm.stage_label,
              source_round_label: fixtureForm.round_label,
              next_stage_label: "Knockout",
              next_round_label: "Next round",
              scheduled_at: new Date(fixtureForm.scheduled_at).toISOString(),
              match_spacing_minutes: 120,
              venue_name: fixtureForm.venue_name
            }
          }
        ),
      (advancement) => {
        setCompetitionAdvancement(advancement);
        addLog(`${advancement.created} advancement fixtures created`, "good");
        void loadCompetitionWorkspace(selectedCompetitionId);
      }
    );
  };

  const optimizeCompetitionSchedule = () => {
    if (!selectedCompetitionId) {
      addLog("Select a competition first", "bad");
      return;
    }
    runAction(
      "optimize-competition-schedule",
      () =>
        apiRequest<CompetitionScheduleOptimizationRead>(
          `/competitions/${selectedCompetitionId}/schedule/optimize`,
          {
            method: "POST",
            identity,
            body: {
              starts_at: new Date(fixtureForm.scheduled_at).toISOString(),
              match_spacing_minutes: 120,
              team_rest_minutes: 240,
              venue_name: fixtureForm.venue_name,
              preserve_final_results: true
            }
          }
        ),
      (optimization) => {
        setScheduleOptimization(optimization);
        addLog(`${optimization.moved} fixtures optimized`, "good");
        void loadCompetitionWorkspace(selectedCompetitionId);
      }
    );
  };

  const broadcastCompetitionUpdate = () => {
    if (!selectedCompetitionId) {
      addLog("Select a competition first", "bad");
      return;
    }
    runAction(
      "broadcast-competition-update",
      () =>
        apiRequest<CompetitionBroadcastRead>(
          `/competitions/${selectedCompetitionId}/broadcast`,
          {
            method: "POST",
            identity,
            body: {
              channel: messageForm.channel,
              urgent: false,
              include_guardians: true
            }
          }
        ),
      (broadcast) => {
        setCompetitionBroadcast(broadcast);
        addLog(`${broadcast.subject} sent to ${broadcast.recipient_count} recipients`, "good");
        void loadCommunications(selectedOrganizationId);
      }
    );
  };

  const openCompetitionTicketing = () => {
    if (!selectedCompetitionId || !selectedFixtureId) {
      addLog("Select a competition fixture first", "bad");
      return;
    }
    runAction(
      "open-competition-ticketing",
      () =>
        apiRequest<CompetitionTicketingRead>(
          `/competitions/${selectedCompetitionId}/ticketing`,
          {
            method: "POST",
            identity,
            body: {
              fixture_id: selectedFixtureId,
              name: ticketForm.name,
              price: String(ticketForm.price),
              capacity: ticketForm.capacity,
              access_zone: ticketForm.access_zone
            }
          }
        ),
      (ticketing) => {
        setCompetitionTicketing((current) => [
          ticketing,
          ...current.filter((item) => item.ticket_product_id !== ticketing.ticket_product_id)
        ]);
        setSelectedTicketProductId(ticketing.ticket_product_id);
        addLog(`${ticketing.name} opened with ${ticketing.capacity} tickets`, "good");
        void loadCompetitionWorkspace(selectedCompetitionId);
        if (selectedOrganizationId) {
          void loadCommercial(selectedOrganizationId);
        }
      }
    );
  };

  const recordFixtureResult = () => {
    if (!selectedFixtureId || !selectedCompetitionId) {
      addLog("Select a fixture first", "bad");
      return;
    }
    runAction(
      "record-fixture-result",
      () =>
        apiRequest<CompetitionFixtureRead>(`/competitions/fixtures/${selectedFixtureId}/result`, {
          method: "PATCH",
          identity,
          body: {
            home_score: fixtureForm.home_score,
            away_score: fixtureForm.away_score,
            confirmed: true,
            notes: "Result confirmed from the operations console."
          }
        }),
      (fixture) => {
        setCompetitionFixtures((current) => [
          fixture,
          ...current.filter((item) => item.id !== fixture.id)
        ]);
        addLog(`Result confirmed: ${fixture.home_score}-${fixture.away_score}`, "good");
        void loadCompetitionWorkspace(selectedCompetitionId);
      }
    );
  };

  const assignFixtureOfficial = () => {
    if (!selectedOrganizationId || !selectedFixtureId) {
      addLog("Select a fixture first", "bad");
      return;
    }
    runAction(
      "assign-fixture-official",
      async () => {
        const member = await apiRequest<MembershipRead>(
          `/organizations/${selectedOrganizationId}/members`,
          {
            method: "POST",
            identity,
            body: {
              email: officialForm.email,
              display_name: officialForm.display_name,
              role: "staff",
              title: officialForm.certification_level
            }
          }
        );
        const assignment = await apiRequest<FixtureOfficialAssignmentRead>(
          `/competitions/fixtures/${selectedFixtureId}/officials`,
          {
            method: "POST",
            identity,
            body: {
              person_id: member.subject_id,
              role: officialForm.role,
              status: "confirmed",
              certification_level: officialForm.certification_level
            }
          }
        );
        return assignment;
      },
      (assignment) => {
        setOfficialAssignments((current) => [
          assignment,
          ...current.filter((item) => item.id !== assignment.id)
        ]);
        addLog(`${officialForm.display_name} assigned as ${assignment.role}`, "good");
      }
    );
  };

  const recordFixtureEvent = () => {
    if (!selectedFixture) {
      addLog("Select a fixture first", "bad");
      return;
    }
    runAction(
      "record-fixture-event",
      () =>
        apiRequest<FixtureMatchEventRead>(`/competitions/fixtures/${selectedFixture.id}/events`, {
          method: "POST",
          identity,
          body: {
            team_id: selectedFixture.home_team_id,
            minute: fixtureForm.event_minute,
            event_type: fixtureForm.event_type,
            description: fixtureForm.event_description
          }
        }),
      (matchEvent) => {
        setMatchEvents((current) => [
          matchEvent,
          ...current.filter((item) => item.id !== matchEvent.id)
        ]);
        addLog(`Match event logged at ${matchEvent.minute ?? 0}'`, "good");
      }
    );
  };

  const createCommunicationTemplate = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-communication-template",
      () =>
        apiRequest<CommunicationTemplateRead>("/communications/templates", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...templateForm
          }
        }),
      (template) => {
        setCommunicationTemplates((current) => [
          template,
          ...current.filter((item) => item.id !== template.id)
        ]);
        addLog(`${template.name} template is ready`, "good");
      }
    );
  };

  const communicationScopeId = () => {
    if (messageForm.scope_type === "organization") {
      return selectedOrganizationId;
    }
    if (messageForm.scope_type === "team") {
      return selectedTeamId;
    }
    if (messageForm.scope_type === "event") {
      return selectedEventId;
    }
    return selectedAthleteId;
  };

  const sendCommunicationMessage = () => {
    const scopeId = communicationScopeId();
    if (!selectedOrganizationId || !scopeId) {
      addLog("Select the communication scope first", "bad");
      return;
    }
    runAction(
      "send-communication-message",
      () =>
        apiRequest<CommunicationMessageRead>("/communications/messages", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            template_id: communicationTemplates[0]?.id ?? null,
            ...messageForm,
            scope_id: scopeId,
            quiet_hours_override: messageForm.urgent && messageForm.quiet_hours_override
          }
        }),
      (message) => {
        setCommunicationMessages((current) => [
          message,
          ...current.filter((item) => item.id !== message.id)
        ]);
        setSelectedMessageId(message.id);
        addLog(`${message.subject} sent to ${message.recipient_count} recipients`, "good");
      }
    );
  };

  const updateRecipientStatus = (recipientId: string, delivery_status: MessageDeliveryStatus) => {
    runAction(
      `message-recipient-${recipientId}-${delivery_status}`,
      () =>
        apiRequest<MessageRecipientRead>(`/communications/recipients/${recipientId}`, {
          method: "PATCH",
          identity,
          body: { delivery_status }
        }),
      (recipient) => {
        setMessageRecipients((current) => [
          recipient,
          ...current.filter((item) => item.id !== recipient.id)
        ]);
        setInboxItems((current) =>
          current.map((item) =>
            item.recipient_id === recipient.id
              ? {
                  ...item,
                  delivery_status: recipient.delivery_status,
                  delivered_at: recipient.delivered_at,
                  read_at: recipient.read_at,
                  failure_reason: recipient.failure_reason
                }
              : item
          )
        );
        addLog(`${recipient.person_name} marked ${recipient.delivery_status}`, "good");
      }
    );
  };

  const dispatchSelectedMessage = () => {
    if (!selectedMessageId) {
      addLog("Select a communication first", "bad");
      return;
    }

    runAction(
      "dispatch-communication",
      async () => {
        const summary = await apiRequest<CommunicationDispatchSummary>(
          `/communications/messages/${selectedMessageId}/dispatch`,
          { method: "POST", identity }
        );
        const recipients = await apiRequest<MessageRecipientRead[]>(
          `/communications/messages/${selectedMessageId}/recipients`
        );
        return { summary, recipients };
      },
      ({ summary, recipients }) => {
        setMessageRecipients(recipients);
        addLog(
          `Delivery ${summary.transport_mode}: ${summary.sent + summary.delivered} sent, ${summary.failed} failed, ${summary.queued} queued`,
          summary.failed > 0 ? "bad" : "good"
        );
      }
    );
  };

  const draftCommunicationMessage = () => {
    const scopeId = communicationScopeId();
    if (!selectedOrganizationId || !scopeId) {
      addLog("Select the communication scope first", "bad");
      return;
    }
    runAction(
      "draft-communication-message",
      () =>
        apiRequest<CommunicationDraftRead>("/communications/drafts", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            message_type: messageForm.message_type,
            channel: messageForm.channel,
            scope_type: messageForm.scope_type,
            scope_id: scopeId,
            intent: messageForm.body,
            tone: messageForm.urgent ? "urgent and direct" : "clear and supportive",
            audience: messageForm.scope_type === "person" ? "the selected family" : "members and guardians",
            include_guardian_context: true
          }
        }),
      (draft) => {
        setDraftPreview(draft);
        setMessageForm((current) => ({
          ...current,
          subject: draft.subject,
          body: draft.body
        }));
        addLog(`Draft prepared by ${draft.model_name}`, "good");
      }
    );
  };

  const createCommunicationDigest = () => {
    if (!selectedOrganizationId || !selectedInboxPersonId) {
      addLog("Select an inbox person first", "bad");
      return;
    }
    runAction(
      "create-communication-digest",
      async () => {
        const digest = await apiRequest<CommunicationDigestRead>("/communications/digests", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            person_id: selectedInboxPersonId,
            frequency: preferenceForm.frequency === "weekly_digest" ? "weekly_digest" : "daily_digest"
          }
        });
        const inbox = await apiRequest<CommunicationInboxItemRead[]>(
          `/communications/inbox?organization_id=${selectedOrganizationId}&person_id=${selectedInboxPersonId}`,
          { identity }
        );
        return { digest, inbox };
      },
      ({ digest, inbox }) => {
        setDigestSummary(digest);
        setDigestRun(null);
        setInboxItems(inbox);
        addLog(`${digest.subject} created with ${digest.item_count} items`, "good");
      }
    );
  };

  const runCommunicationDigestScheduler = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const frequency = preferenceForm.frequency === "weekly_digest" ? "weekly_digest" : "daily_digest";
    runAction(
      "run-communication-digests",
      () =>
        apiRequest<CommunicationDigestRunRead>("/communications/digests/run", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            frequency,
            limit: 50
          }
        }),
      (run) => {
        setDigestRun(run);
        setDigestSummary(run.digests[0] ?? null);
        addLog(`Digest run created ${run.created} and skipped ${run.skipped}`, "good");
      }
    );
  };

  const saveNotificationPreference = () => {
    if (!selectedOrganizationId || !selectedAthleteId) {
      addLog("Select an athlete first", "bad");
      return;
    }
    runAction(
      "save-notification-preference",
      () =>
        apiRequest<NotificationPreferenceRead>("/communications/preferences", {
          method: "PUT",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            person_id: selectedAthleteId,
            ...preferenceForm
          }
        }),
      (preference) => {
        setNotificationPreference(preference);
        addLog(`Preference saved for selected athlete`, "good");
      }
    );
  };

  const createFacility = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-facility",
      () =>
        apiRequest<FacilityRead>("/assets/facilities", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            sport: selectedTeam?.sport ?? organizationForm.primary_sport,
            ...facilityForm,
            hourly_rate: String(facilityForm.hourly_rate),
            maintenance_budget: String(facilityForm.maintenance_budget)
          }
        }),
      (facility) => {
        setFacilities((current) => [facility, ...current.filter((item) => item.id !== facility.id)]);
        setSelectedFacilityId(facility.id);
        addLog(`${facility.name} facility is available`, "good");
        void loadAssets(selectedOrganizationId, facility.id);
      }
    );
  };

  const createEquipmentItem = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-equipment",
      () =>
        apiRequest<EquipmentItemRead>("/assets/equipment", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            facility_id: selectedFacilityId || null,
            team_id: selectedTeamId || null,
            ...equipmentForm,
            quantity_available: equipmentForm.quantity_total,
            unit_value: String(equipmentForm.unit_value),
            depreciation_rate: String(equipmentForm.depreciation_rate)
          }
        }),
      (item) => {
        setEquipmentItems((current) => [item, ...current.filter((value) => value.id !== item.id)]);
        setSelectedEquipmentId(item.id);
        addLog(`${item.name} added to inventory`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const scanEquipmentItem = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const code = selectedEquipment?.tag_code ?? equipmentForm.tag_code;
    if (!code) {
      addLog("Enter or select a tag code first", "bad");
      return;
    }
    runAction(
      "scan-equipment",
      () =>
        apiRequest<EquipmentScanRead>(
          `/assets/equipment/scan?organization_id=${selectedOrganizationId}&code=${encodeURIComponent(code)}`,
          { identity }
        ),
      (scan) => {
        setEquipmentItems((current) => [
          scan.item,
          ...current.filter((item) => item.id !== scan.item.id)
        ]);
        setSelectedEquipmentId(scan.item.id);
        addLog(`${scan.match_type} scan matched ${scan.item.name}`, "good");
      }
    );
  };

  const recordRfidEquipmentScan = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const code = selectedEquipment?.tag_code ?? selectedEquipment?.serial_number ?? equipmentForm.tag_code;
    if (!code) {
      addLog("Enter or select a tag or serial code first", "bad");
      return;
    }
    runAction(
      "record-rfid-scan",
      () =>
        apiRequest<EquipmentScanEventRead>("/assets/equipment/rfid-scans", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            scanned_code: code,
            reader_id: rfidForm.reader_id,
            reader_location: rfidForm.reader_location || equipmentForm.storage_location,
            movement: rfidForm.movement,
            source: rfidForm.source,
            external_reference: `RFID-${Date.now()}`,
            notes: `Recorded from operations console for ${selectedEquipment?.name ?? equipmentForm.name}.`
          }
        }),
      (event) => {
        setEquipmentScanEvents((current) => [
          event,
          ...current.filter((item) => item.id !== event.id)
        ]);
        addLog(
          event.matched
            ? `${event.reader_id} matched ${event.item_name ?? event.scanned_code}`
            : `${event.reader_id} recorded unmatched code ${event.scanned_code}`,
          event.matched ? "good" : "neutral"
        );
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const provisionRfidReader = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "provision-rfid-reader",
      () =>
        apiRequest<EquipmentReaderProvisionRead>("/assets/equipment/rfid-readers", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            reader_id: rfidForm.reader_id,
            name: rfidForm.reader_name,
            location: rfidForm.reader_location,
            status: "active",
            api_key: rfidForm.api_key,
            notes: "Provisioned from the operations console."
          }
        }),
      (provision) => {
        setRfidProvision(provision);
        setEquipmentReaders((current) => [
          provision.reader,
          ...current.filter((reader) => reader.id !== provision.reader.id)
        ]);
        setRfidForm((current) => ({ ...current, api_key: provision.api_key }));
        addLog(`${provision.reader.name} provisioned`, "good");
      }
    );
  };

  const recordGatewayRfidScan = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const code = rfidForm.gateway_code || selectedEquipment?.tag_code || selectedEquipment?.serial_number;
    if (!code) {
      addLog("Enter a gateway scan code first", "bad");
      return;
    }
    runAction(
      "gateway-rfid-scan",
      () =>
        apiRequest<EquipmentScanEventRead>(
          `/assets/equipment/rfid-gateway/${selectedOrganizationId}/${encodeURIComponent(rfidForm.reader_id)}/scans`,
          {
            method: "POST",
            headers: { "X-Afrolete-RFID-Key": rfidProvision?.api_key ?? rfidForm.api_key },
            body: {
              scanned_code: code,
              movement: rfidForm.movement,
              external_reference: `GATEWAY-${Date.now()}`,
              notes: "Hardware-style gateway scan submitted from the operations console."
            }
          }
        ),
      (event) => {
        setEquipmentScanEvents((current) => [
          event,
          ...current.filter((item) => item.id !== event.id)
        ]);
        addLog(
          event.matched
            ? `${event.reader_id} gateway matched ${event.item_name ?? event.scanned_code}`
            : `${event.reader_id} gateway recorded unmatched ${event.scanned_code}`,
          event.matched ? "good" : "neutral"
        );
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const updateSelectedEquipmentPhoto = () => {
    if (!selectedEquipmentId) {
      addLog("Select equipment first", "bad");
      return;
    }
    runAction(
      "update-equipment-photo",
      () =>
        apiRequest<EquipmentItemRead>(`/assets/equipment/${selectedEquipmentId}/photo`, {
          method: "PATCH",
          identity,
          body: {
            photo_url: equipmentForm.photo_url,
            notes: `Photo metadata updated from console for ${equipmentForm.name}.`
          }
        }),
      (item) => {
        setEquipmentItems((current) => [item, ...current.filter((value) => value.id !== item.id)]);
        addLog(`${item.name} photo metadata saved`, "good");
      }
    );
  };

  const uploadSelectedEquipmentFile = () => {
    if (!selectedEquipmentId || !selectedEquipmentFile) {
      addLog("Select equipment and choose a file first", "bad");
      return;
    }
    runAction(
      "upload-equipment-file",
      async () => {
        const contentBase64 = await fileToBase64(selectedEquipmentFile);
        return apiRequest<EquipmentFileRead>(`/assets/equipment/${selectedEquipmentId}/files`, {
          method: "POST",
          identity,
          body: {
            filename: selectedEquipmentFile.name,
            content_type: selectedEquipmentFile.type || "application/octet-stream",
            content_base64: contentBase64,
            notes: `Uploaded from the operations console for ${selectedEquipment?.name ?? "equipment"}.`,
            mark_as_photo: selectedEquipmentFile.type.startsWith("image/")
          }
        });
      },
      (fileRecord) => {
        setEquipmentFiles((current) => [
          fileRecord,
          ...current.filter((item) => item.id !== fileRecord.id)
        ]);
        addLog(`${fileRecord.filename} uploaded (${fileRecord.size_bytes} bytes)`, "good");
        setSelectedEquipmentFile(null);
        if (selectedOrganizationId) {
          void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
        }
      }
    );
  };

  const quoteSelectedEquipmentLease = () => {
    if (!selectedOrganizationId || !selectedEquipmentId) {
      addLog("Select equipment first", "bad");
      return;
    }
    runAction(
      "equipment-lease-quote",
      () =>
        apiRequest<EquipmentLeaseQuoteRead>(
          `/assets/equipment/${selectedEquipmentId}/lease-quote?organization_id=${selectedOrganizationId}&quantity=${checkoutForm.quantity}&term_months=12`
        ),
      (quote) => {
        setLeaseQuote(quote);
        addLog(`${quote.item_name} lease quote: $${quote.monthly_amount}/month`, "good");
      }
    );
  };

  const billSelectedEquipmentLease = () => {
    if (!selectedOrganizationId || !selectedEquipmentId) {
      addLog("Select equipment first", "bad");
      return;
    }
    runAction(
      "equipment-lease-invoice",
      () =>
        apiRequest<EquipmentLeaseInvoiceRead>(`/assets/equipment/${selectedEquipmentId}/lease-invoice`, {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            quantity: checkoutForm.quantity,
            term_months: 12,
            person_id: selectedAthleteId || null,
            team_id: selectedTeamId || null,
            due_on: new Date().toISOString().slice(0, 10),
            memo: `Lease billing created from asset operations for ${selectedEquipment?.name ?? equipmentForm.name}.`
          }
        }),
      (leaseBilling) => {
        setLeaseInvoice(leaseBilling);
        setLeaseQuote(leaseBilling.lease_quote);
        setInvoices((current) => [
          leaseBilling.invoice,
          ...current.filter((invoice) => invoice.id !== leaseBilling.invoice.id)
        ]);
        setSelectedInvoiceId(leaseBilling.invoice.id);
        addLog(`${leaseBilling.invoice.invoice_number} opened for ${leaseBilling.lease_quote.item_name}`, "good");
      }
    );
  };

  const scheduleSelectedEquipmentLease = () => {
    if (!selectedOrganizationId || !selectedEquipmentId) {
      addLog("Select equipment first", "bad");
      return;
    }
    runAction(
      "equipment-lease-schedule",
      () =>
        apiRequest<EquipmentLeaseScheduleRead>(`/assets/equipment/${selectedEquipmentId}/lease-schedules`, {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            quantity: checkoutForm.quantity,
            term_months: 12,
            person_id: selectedAthleteId || null,
            team_id: selectedTeamId || null,
            starts_on: new Date().toISOString().slice(0, 10),
            notes: `Lease schedule created from asset operations for ${selectedEquipment?.name ?? equipmentForm.name}.`
          }
        }),
      (schedule) => {
        setLeaseSchedules((current) => [
          schedule,
          ...current.filter((item) => item.id !== schedule.id)
        ]);
        setLeaseQuote({
          equipment_item_id: schedule.equipment_item_id,
          item_name: schedule.invoice.title,
          quantity: schedule.quantity,
          term_months: schedule.term_months,
          monthly_amount: schedule.monthly_amount,
          total_amount: schedule.total_amount,
          residual_value: "0.00",
          rationale: "Scheduled lease billing from asset operations."
        });
        setInvoices((current) => [
          schedule.invoice,
          ...current.filter((invoice) => invoice.id !== schedule.invoice.id)
        ]);
        setSelectedInvoiceId(schedule.invoice.id);
        addLog(`${schedule.term_months} lease installments scheduled`, "good");
      }
    );
  };

  const reconcileNextLeaseInstallment = (scheduleId = leaseSchedules[0]?.id ?? "") => {
    if (!selectedOrganizationId || !scheduleId) {
      addLog("Create or select a lease schedule first", "bad");
      return;
    }
    const schedule = leaseSchedules.find((item) => item.id === scheduleId);
    const nextInstallment = schedule?.installments.find((item) => item.status !== "paid");
    runAction(
      "reconcile-lease-installment",
      () =>
        apiRequest<EquipmentLeasePaymentRead>(`/assets/lease-schedules/${scheduleId}/payments`, {
          method: "POST",
          identity,
          body: {
            amount: nextInstallment?.amount ?? schedule?.monthly_amount ?? String(invoiceForm.payment_amount),
            method: invoiceForm.method,
            external_reference: `LEASE-PAY-${Date.now()}`,
            notes: "Lease installment reconciled from the operations console."
          }
        }),
      (result) => {
        setLeasePayment(result);
        setLeaseSchedules((current) => [
          result.schedule,
          ...current.filter((item) => item.id !== result.schedule.id)
        ]);
        setPayments((current) => [
          result.payment,
          ...current.filter((payment) => payment.id !== result.payment.id)
        ]);
        setInvoices((current) => [
          result.schedule.invoice,
          ...current.filter((invoice) => invoice.id !== result.schedule.invoice.id)
        ]);
        addLog(
          `${result.installments_paid} paid, ${result.installments_partially_paid} partially paid`,
          "good"
        );
      }
    );
  };

  const checkoutEquipmentItem = () => {
    if (!selectedOrganizationId || !selectedEquipmentId) {
      addLog("Create or select equipment first", "bad");
      return;
    }
    runAction(
      "checkout-equipment",
      () =>
        apiRequest<EquipmentCheckoutRead>("/assets/checkouts", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            equipment_item_id: selectedEquipmentId,
            team_id: selectedTeamId || null,
            event_id: selectedEventId || null,
            borrower_person_id: selectedAthleteId || null,
            quantity: checkoutForm.quantity,
            purpose: checkoutForm.purpose,
            due_at: new Date(checkoutForm.due_at).toISOString(),
            condition_out: selectedEquipment?.condition ?? "good",
            condition_notes: checkoutForm.condition_notes
          }
        }),
      (checkout) => {
        setEquipmentCheckouts((current) => [
          checkout,
          ...current.filter((item) => item.id !== checkout.id)
        ]);
        setSelectedCheckoutId(checkout.id);
        addLog(`${checkout.quantity} item(s) checked out`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const returnSelectedCheckout = () => {
    if (!selectedOrganizationId || !selectedCheckoutId) {
      addLog("Select an open checkout first", "bad");
      return;
    }
    runAction(
      "return-equipment",
      () =>
        apiRequest<EquipmentCheckoutRead>(`/assets/checkouts/${selectedCheckoutId}/return`, {
          method: "PATCH",
          identity,
          body: {
            condition_in: "fair",
            late_fee: "0.00",
            damage_report: null
          }
        }),
      (checkout) => {
        setEquipmentCheckouts((current) => [
          checkout,
          ...current.filter((item) => item.id !== checkout.id)
        ]);
        addLog(`Checkout marked ${checkout.status}`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const createWorkOrder = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-work-order",
      () =>
        apiRequest<MaintenanceWorkOrderRead>("/assets/work-orders", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            facility_id: selectedFacilityId || null,
            equipment_item_id: selectedEquipmentId || null,
            assigned_to_person_id: selectedAthleteId || null,
            ...workOrderForm,
            due_at: new Date(workOrderForm.due_at).toISOString(),
            estimated_cost: String(workOrderForm.estimated_cost)
          }
        }),
      (workOrder) => {
        setWorkOrders((current) => [
          workOrder,
          ...current.filter((item) => item.id !== workOrder.id)
        ]);
        setSelectedWorkOrderId(workOrder.id);
        addLog(`${workOrder.title} work order opened`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const updateWorkOrderStatus = (workOrderId: string, status: WorkOrderStatus) => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      `work-order-${workOrderId}-${status}`,
      () =>
        apiRequest<MaintenanceWorkOrderRead>(`/assets/work-orders/${workOrderId}`, {
          method: "PATCH",
          identity,
          body: {
            status,
            actual_cost: status === "completed" ? "125.00" : null,
            notes: `Marked ${status} from the operations console.`
          }
        }),
      (workOrder) => {
        setWorkOrders((current) => [
          workOrder,
          ...current.filter((item) => item.id !== workOrder.id)
        ]);
        addLog(`Work order moved to ${workOrder.status}`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const createSupplierOrder = (recommendation?: ProcurementRecommendationRead) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const equipment = recommendation
      ? equipmentItems.find((item) => item.id === recommendation.equipment_item_id)
      : selectedEquipment;
    if (!equipment && !recommendation) {
      addLog("Select equipment or a recommendation first", "bad");
      return;
    }
    const quantity = recommendation?.recommended_quantity ?? Math.max(checkoutForm.quantity, 1);
    const unitCost = equipment?.unit_value ?? "0.00";
    runAction(
      "create-supplier-order",
      () =>
        apiRequest<SupplierOrderRead>("/assets/suppliers/orders", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            equipment_item_id: recommendation?.equipment_item_id ?? equipment?.id ?? null,
            supplier_name: recommendation?.supplier_hint ?? equipment?.brand ?? "Preferred supplier",
            item_name: recommendation?.item_name ?? equipment?.name ?? equipmentForm.name,
            quantity,
            unit_cost: String(unitCost),
            currency: "USD",
            external_reference: `PO-${Date.now()}`,
            expected_delivery_at: new Date(Date.now() + 7 * 24 * 60 * 60_000).toISOString(),
            notes: recommendation?.rationale ?? "Supplier order created from the operations console.",
            submit: true
          }
        }),
      (order) => {
        setSupplierOrders((current) => [order, ...current.filter((item) => item.id !== order.id)]);
        setSelectedSupplierOrderId(order.id);
        addLog(`${order.item_name} supplier order opened`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const receiveSupplierOrder = (supplierOrderId = selectedSupplierOrderId) => {
    if (!selectedOrganizationId || !supplierOrderId) {
      addLog("Select a supplier order first", "bad");
      return;
    }
    const order = supplierOrders.find((item) => item.id === supplierOrderId);
    runAction(
      "receive-supplier-order",
      () =>
        apiRequest<SupplierOrderRead>(`/assets/suppliers/orders/${supplierOrderId}/receive`, {
          method: "PATCH",
          identity,
          body: {
            quantity_received: order?.quantity ?? null,
            notes: "Received from the operations console and applied to inventory."
          }
        }),
      (received) => {
        setSupplierOrders((current) => [
          received,
          ...current.filter((item) => item.id !== received.id)
        ]);
        addLog(`${received.item_name} order marked ${received.status}`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId || undefined);
      }
    );
  };

  const submitSupplierOrder = (supplierOrderId = selectedSupplierOrderId) => {
    if (!selectedOrganizationId || !supplierOrderId) {
      addLog("Select a supplier order first", "bad");
      return;
    }
    runAction(
      "submit-supplier-order",
      () =>
        apiRequest<SupplierOrderSubmissionRead>(`/assets/suppliers/orders/${supplierOrderId}/submit`, {
          method: "POST",
          identity
        }),
      (submission) => {
        setSupplierSubmission(submission);
        setSupplierOrders((current) => [
          submission.order,
          ...current.filter((item) => item.id !== submission.order.id)
        ]);
        setSelectedSupplierOrderId(submission.order.id);
        addLog(
          submission.delivered
            ? `${submission.order.item_name} submitted to supplier`
            : `${submission.order.item_name} prepared for supplier submission`,
          submission.delivered ? "good" : "neutral"
        );
      }
    );
  };

  const syncSupplierInvoice = (supplierOrderId = selectedSupplierOrderId) => {
    if (!selectedOrganizationId || !supplierOrderId) {
      addLog("Select a supplier order first", "bad");
      return;
    }
    runAction(
      "sync-supplier-invoice",
      () =>
        apiRequest<SupplierInvoiceSyncRead>(`/assets/suppliers/orders/${supplierOrderId}/invoice-sync`, {
          method: "POST",
          identity
        }),
      (sync) => {
        setSupplierInvoiceSync(sync);
        setSupplierOrders((current) => [
          sync.order,
          ...current.filter((item) => item.id !== sync.order.id)
        ]);
        setSelectedSupplierOrderId(sync.order.id);
        addLog(
          sync.synced
            ? `${sync.order.item_name} supplier invoice synced`
            : `${sync.order.item_name} supplier invoice prepared`,
          sync.synced ? "good" : "neutral"
        );
      }
    );
  };

  const createFacilityBooking = () => {
    if (!selectedOrganizationId || !selectedFacilityId) {
      addLog("Create or select a facility first", "bad");
      return;
    }
    const startsAt = new Date(bookingForm.starts_at);
    const endsAt = new Date(startsAt.getTime() + bookingForm.duration_hours * 60 * 60_000);
    runAction(
      "create-facility-booking",
      () =>
        apiRequest<FacilityBookingRead>("/assets/bookings", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            facility_id: selectedFacilityId,
            team_id: selectedTeamId || null,
            event_id: selectedEventId || null,
            title: bookingForm.title,
            starts_at: startsAt.toISOString(),
            ends_at: endsAt.toISOString(),
            requester_name: bookingForm.requester_name,
            requester_email: bookingForm.requester_email,
            expected_attendees: bookingForm.expected_attendees,
            rate: String(bookingForm.rate),
            deposit_required: String(bookingForm.deposit_required),
            insurance_certificate_ref: bookingForm.insurance_certificate_ref,
            special_requirements: bookingForm.special_requirements,
            access_code: `${selectedFacility?.name.slice(0, 4).toUpperCase() ?? "SITE"}-${startsAt.getDate()}`
          }
        }),
      (booking) => {
        setFacilityBookings((current) => [
          booking,
          ...current.filter((item) => item.id !== booking.id)
        ]);
        addLog(`${booking.title} confirmed for ${selectedFacility?.name ?? "facility"}`, "good");
        void loadAssets(selectedOrganizationId, selectedFacilityId);
      }
    );
  };

  const createSponsorAndAgreement = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-sponsorship",
      async () => {
        const sponsor = await apiRequest<SponsorRead>("/commercial/sponsors", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            name: sponsorForm.name,
            industry: sponsorForm.industry,
            contact_name: sponsorForm.contact_name,
            contact_email: sponsorForm.contact_email
          }
        });
        const agreement = await apiRequest<SponsorshipAgreementRead>("/commercial/sponsorships", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            sponsor_id: sponsor.id,
            event_id: selectedEventId || null,
            name: sponsorForm.agreement_name,
            tier: sponsorForm.tier,
            value_amount: String(sponsorForm.value_amount),
            deliverables: sponsorForm.deliverables,
            activation_notes: sponsorForm.activation_notes,
            roi_notes: "Track reach, ticket conversion, athlete challenge completions, and coupon use."
          }
        });
        return { sponsor, agreement };
      },
      ({ sponsor, agreement }) => {
        setSponsors((current) => [sponsor, ...current.filter((item) => item.id !== sponsor.id)]);
        setSponsorships((current) => [
          agreement,
          ...current.filter((item) => item.id !== agreement.id)
        ]);
        setSelectedSponsorId(sponsor.id);
        addLog(`${sponsor.name} sponsorship activated`, "good");
        void loadCommercial(selectedOrganizationId);
      }
    );
  };

  const createCampaignAndDonation = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-campaign-donation",
      async () => {
        const campaign = await apiRequest<FundraisingCampaignRead>("/commercial/campaigns", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId || null,
            name: campaignForm.name,
            purpose: campaignForm.purpose,
            goal_amount: String(campaignForm.goal_amount),
            public_url: `https://${organizationForm.subdomain}.afrolete.local/fundraising`
          }
        });
        const donation = await apiRequest<DonationRead>("/commercial/donations", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            campaign_id: campaign.id,
            donor_name: campaignForm.donor_name,
            donor_email: campaignForm.donor_email,
            amount: String(campaignForm.donation_amount),
            external_reference: `DON-${Date.now()}`,
            message: campaignForm.message
          }
        });
        return { campaign, donation };
      },
      ({ campaign, donation }) => {
        setCampaigns((current) => [campaign, ...current.filter((item) => item.id !== campaign.id)]);
        setDonations((current) => [donation, ...current.filter((item) => item.id !== donation.id)]);
        setSelectedCampaignId(campaign.id);
        addLog(`${donation.donor_name} donated ${donation.amount}`, "good");
        void loadCommercial(selectedOrganizationId);
      }
    );
  };

  const createTicketSale = () => {
    if (!selectedOrganizationId || !selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      "create-ticket-sale",
      async () => {
        const product = await apiRequest<TicketProductRead>("/commercial/tickets/products", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            event_id: selectedEventId,
            name: ticketForm.name,
            price: String(ticketForm.price),
            capacity: ticketForm.capacity,
            access_zone: ticketForm.access_zone
          }
        });
        const order = await apiRequest<TicketOrderRead>("/commercial/tickets/orders", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ticket_product_id: product.id,
            buyer_name: ticketForm.buyer_name,
            buyer_email: ticketForm.buyer_email,
            quantity: ticketForm.quantity,
            external_payment_reference: `PAY-${Date.now()}`
          }
        });
        return { product, order };
      },
      ({ product, order }) => {
        setTicketProducts((current) => [product, ...current.filter((item) => item.id !== product.id)]);
        setTicketOrders((current) => [order, ...current.filter((item) => item.id !== order.id)]);
        setSelectedTicketProductId(product.id);
        addLog(`${order.quantity} ticket(s) sold`, "good");
        void loadCommercial(selectedOrganizationId);
      }
    );
  };

  const checkInSelectedTicket = () => {
    if (!selectedTicketId || !selectedOrganizationId) {
      addLog("Sell or select a ticket first", "bad");
      return;
    }
    runAction(
      "check-in-ticket",
      () =>
        apiRequest<TicketRead>(`/commercial/tickets/${selectedTicketId}/check-in`, {
          method: "PATCH",
          identity,
          body: { gate: ticketForm.gate }
        }),
      (ticket) => {
        setTickets((current) => [ticket, ...current.filter((item) => item.id !== ticket.id)]);
        addLog(`Ticket checked in at ${ticket.gate ?? "gate"}`, "good");
        void loadCommercial(selectedOrganizationId);
      }
    );
  };

  const createInvoiceAndPayment = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-invoice-payment",
      async () => {
        const invoice = await apiRequest<FinanceInvoiceRead>("/commercial/invoices", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId || null,
            sponsor_id: selectedSponsorId || null,
            invoice_number: invoiceForm.invoice_number,
            title: invoiceForm.title,
            amount_due: String(invoiceForm.amount_due),
            due_on: invoiceForm.due_on,
            memo: invoiceForm.memo
          }
        });
        const payment = await apiRequest<FinancePaymentRead>("/commercial/payments", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            invoice_id: invoice.id,
            amount: String(invoiceForm.payment_amount),
            method: invoiceForm.method,
            external_reference: `RCPT-${Date.now()}`,
            notes: "Recorded from the operations console."
          }
        });
        return { invoice, payment };
      },
      ({ invoice, payment }) => {
        setInvoices((current) => [invoice, ...current.filter((item) => item.id !== invoice.id)]);
        setPayments((current) => [payment, ...current.filter((item) => item.id !== payment.id)]);
        setSelectedInvoiceId(invoice.id);
        addLog(`Payment recorded: ${payment.amount}`, "good");
        void loadCommercial(selectedOrganizationId);
      }
    );
  };

  const quoteCommercialTax = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "commercial-tax-quote",
      () =>
        apiRequest<TaxQuoteRead>(
          `/commercial/tax-quote?organization_id=${selectedOrganizationId}&subtotal=${invoiceForm.amount_due}&tax_rate=16&jurisdiction=local`
        ),
      (quote) => {
        setTaxQuote(quote);
        addLog(`Tax quote total ${quote.total}`, "good");
      }
    );
  };

  const settleCommercialPayments = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "commercial-settlement",
      () =>
        apiRequest<PaymentSettlementRead>(
          `/commercial/settlements?organization_id=${selectedOrganizationId}&provider=manual_gateway&fee_rate=2.9&fixed_fee=0.3`
        ),
      (settlement) => {
        setPaymentSettlement(settlement);
        addLog(`Settlement ${settlement.payout_reference}: ${settlement.net_amount} net`, "good");
      }
    );
  };

  const exportCommercialAccounting = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "commercial-accounting-export",
      () =>
        apiRequest<AccountingExportRead>(
          `/commercial/accounting-export?organization_id=${selectedOrganizationId}&system=generic&basis=cash`
        ),
      (exportData) => {
        setAccountingExport(exportData);
        addLog(`${exportData.rows.length} accounting rows prepared`, "good");
      }
    );
  };

  const refundSelectedTicket = () => {
    if (!selectedOrganizationId || !selectedTicketId) {
      addLog("Select a ticket first", "bad");
      return;
    }
    runAction(
      "commercial-ticket-refund",
      () =>
        apiRequest<CommercialRefundRead>(`/commercial/tickets/${selectedTicketId}/refund`, {
          method: "POST",
          identity,
          body: {
            reason: "Console refund after buyer request.",
            external_reference: `REF-${Date.now()}`
          }
        }),
      (refund) => {
        setCommercialRefund(refund);
        addLog(`Ticket refund processed: ${refund.amount}`, "good");
        void loadCommercial(selectedOrganizationId);
      }
    );
  };

  const refundSelectedInvoice = () => {
    if (!selectedOrganizationId || !selectedInvoiceId) {
      addLog("Select an invoice first", "bad");
      return;
    }
    runAction(
      "commercial-invoice-refund",
      () =>
        apiRequest<CommercialRefundRead>(`/commercial/invoices/${selectedInvoiceId}/refund`, {
          method: "POST",
          identity,
          body: {
            amount: String(Math.min(invoiceForm.payment_amount, invoiceForm.amount_due)),
            reason: "Console credit note adjustment.",
            external_reference: `CREDIT-${Date.now()}`
          }
        }),
      (refund) => {
        setCommercialRefund(refund);
        addLog(`Invoice refund processed: ${refund.amount}`, "good");
        void loadCommercial(selectedOrganizationId);
      }
    );
  };

  const createReportDefinitionAndRun = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-report-run",
      async () => {
        const definition = await apiRequest<ReportDefinitionRead>("/reporting/definitions", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            name: reportForm.name,
            category: reportForm.category,
            description: reportForm.description,
            default_format: reportForm.default_format,
            parameter_schema: "date_range,team,athlete,competition,event",
            template: "summary,findings,recommendations,next_actions",
            ai_assisted: true
          }
        });
        const report = await apiRequest<GeneratedReportRead>("/reporting/reports", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            report_definition_id: definition.id,
            team_id: selectedTeamId || null,
            athlete_profile_id: selectedAthlete?.athleteProfileId ?? null,
            competition_id: selectedCompetitionId || null,
            event_id: selectedEventId || null,
            title: reportForm.title,
            output_format: reportForm.default_format,
            period_start: reportForm.period_start,
            period_end: reportForm.period_end,
            parameters: "scope=current_console_selection"
          }
        });
        return { definition, report };
      },
      ({ definition, report }) => {
        setReportDefinitions((current) => [
          definition,
          ...current.filter((item) => item.id !== definition.id)
        ]);
        setGeneratedReports((current) => [report, ...current.filter((item) => item.id !== report.id)]);
        setSelectedReportDefinitionId(definition.id);
        setSelectedGeneratedReportId(report.id);
        addLog(`${report.title} generated`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const createScheduledReport = () => {
    if (!selectedOrganizationId || !selectedReportDefinitionId) {
      addLog("Create or select a report definition first", "bad");
      return;
    }
    runAction(
      "create-report-schedule",
      () =>
        apiRequest<ScheduledReportRead>("/reporting/schedules", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            report_definition_id: selectedReportDefinitionId,
            name: `${reportForm.name} delivery`,
            frequency: reportForm.frequency,
            delivery_channels: reportForm.delivery_channels,
            recipients: reportForm.recipients,
            next_run_at: new Date("2026-06-08T08:00:00").toISOString()
          }
        }),
      (schedule) => {
        setScheduledReports((current) => [
          schedule,
          ...current.filter((item) => item.id !== schedule.id)
        ]);
        addLog(`${schedule.name} scheduled`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const createInsightAndRisk = () => {
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId) {
      addLog("Select an athlete first", "bad");
      return;
    }
    runAction(
      "create-insight-risk",
      async () => {
        const insight = await apiRequest<IntelligenceInsightRead>("/reporting/insights", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_profile_id: selectedAthlete.athleteProfileId,
            team_id: selectedTeamId || null,
            event_id: selectedEventId || null,
            agent_id: selectedAgentId || null,
            ...insightForm
          }
        });
        const risk = await apiRequest<PredictiveRiskScoreRead>("/reporting/risk-scores", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_profile_id: selectedAthlete.athleteProfileId,
            ...riskForm
          }
        });
        return { insight, risk };
      },
      ({ insight, risk }) => {
        setInsights((current) => [insight, ...current.filter((item) => item.id !== insight.id)]);
        setRiskScores((current) => [risk, ...current.filter((item) => item.id !== risk.id)]);
        setSelectedInsightId(insight.id);
        addLog(`Insight and risk score ${risk.score} recorded`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const updateInsight = (status: InsightStatus) => {
    if (!selectedInsightId || !selectedOrganizationId) {
      addLog("Select an insight first", "bad");
      return;
    }
    runAction(
      `insight-${status}`,
      () =>
        apiRequest<IntelligenceInsightRead>(`/reporting/insights/${selectedInsightId}`, {
          method: "PATCH",
          identity,
          body: { status }
        }),
      (insight) => {
        setInsights((current) => [insight, ...current.filter((item) => item.id !== insight.id)]);
        addLog(`Insight marked ${insight.status}`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const createReportExport = () => {
    if (!selectedOrganizationId || !selectedGeneratedReportId) {
      addLog("Generate or select a report first", "bad");
      return;
    }
    runAction(
      "create-report-export",
      () =>
        apiRequest<ReportExportJobRead>("/reporting/exports", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            generated_report_id: selectedGeneratedReportId,
            output_format: "pdf",
            destination: "board-packages/weekly-intelligence.pdf",
            webhook_url: "https://analytics.example.com/webhooks/report-ready"
          }
        }),
      (exportJob) => {
        setReportExports((current) => [
          exportJob,
          ...current.filter((item) => item.id !== exportJob.id)
        ]);
        addLog(`${exportJob.output_format} export ready`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const renderSelectedReport = () => {
    if (!selectedOrganizationId || !selectedGeneratedReportId) {
      addLog("Generate or select a report first", "bad");
      return;
    }
    runAction(
      "render-report",
      () =>
        apiRequest<RenderedReportRead>(
          `/reporting/reports/${selectedGeneratedReportId}/render?output_format=${reportForm.default_format}`,
          { method: "POST", identity }
        ),
      (artifact) => {
        setRenderedReport(artifact);
        addLog(`${artifact.output_format} artifact rendered: ${artifact.size_bytes} bytes`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const verifySelectedReport = () => {
    if (!selectedOrganizationId || !selectedGeneratedReportId) {
      addLog("Generate or select a report first", "bad");
      return;
    }
    runAction(
      "verify-report",
      () =>
        apiRequest<ReportVerificationRead>(
          `/reporting/reports/${selectedGeneratedReportId}/verify`,
          { method: "POST", identity }
        ),
      (verification) => {
        setReportVerification(verification);
        addLog(`Report verification ${verification.score}/100`, verification.passed ? "good" : "bad");
      }
    );
  };

  const downloadSelectedReport = () => {
    if (!selectedGeneratedReportId) {
      addLog("Generate or select a report first", "bad");
      return;
    }
    runAction(
      "download-report-artifact",
      async () => {
        const headers = new Headers({ Accept: "*/*" });
        if (authSession) {
          headers.set("Authorization", `Bearer ${authSession.accessToken}`);
        } else {
          headers.set("X-Afrolete-Sub", identity.sub);
          headers.set("X-Afrolete-Email", identity.email);
          headers.set("X-Afrolete-Name", identity.name);
        }
        const response = await fetch(
          `${apiBaseUrl}/api/v1/reporting/reports/${selectedGeneratedReportId}/download?output_format=${reportForm.default_format}`,
          { headers }
        );
        if (!response.ok) {
          throw new Error(`Report download failed: ${response.status}`);
        }
        const blob = await response.blob();
        const disposition = response.headers.get("Content-Disposition") ?? "";
        const filename = disposition.match(/filename=([^;]+)/)?.[1] ?? `afrolete-report.${reportForm.default_format}`;
        const href = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = href;
        anchor.download = filename.replaceAll("\"", "");
        document.body.append(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(href);
        return {
          filename,
          checksum: response.headers.get("X-Afrolete-Report-Checksum") ?? "no-checksum",
          size: blob.size
        };
      },
      (artifact) => {
        addLog(`${artifact.filename} ready (${artifact.size} bytes, ${artifact.checksum.slice(0, 8)})`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const shareSelectedReportArtifact = () => {
    if (!selectedGeneratedReportId) {
      addLog("Generate or select a report first", "bad");
      return;
    }
    runAction(
      "share-report-artifact",
      () =>
        apiRequest<ReportArtifactAccessRead>(
          `/reporting/reports/${selectedGeneratedReportId}/share-artifact?output_format=${reportForm.default_format}`,
          { method: "POST", identity }
        ),
      (access) => {
        setReportArtifactAccess(access);
        addLog(`${access.output_format} link expires ${new Date(access.expires_at).toLocaleString()}`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const generateReportingInsight = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "generate-reporting-insight",
      () =>
        apiRequest<IntelligenceInsightRead>(
          `/reporting/insights/generate?organization_id=${selectedOrganizationId}`,
          { method: "POST", identity }
        ),
      (insight) => {
        setInsights((current) => [insight, ...current.filter((item) => item.id !== insight.id)]);
        setSelectedInsightId(insight.id);
        addLog(`${insight.title} generated`, "good");
        void loadReporting(selectedOrganizationId);
      }
    );
  };

  const createBillingPlanAndSubscription = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-billing-plan-subscription",
      async () => {
        const plan = await apiRequest<BillingPlanRead>("/billing/plans", {
          method: "POST",
          body: {
            code: `${billingForm.plan_code}-${Date.now()}`,
            name: billingForm.plan_name,
            description: "Tiered SaaS plan for sports organizations.",
            base_price: String(billingForm.base_price),
            billing_cycle: billingForm.billing_cycle,
            included_athletes: billingForm.included_athletes,
            included_teams: billingForm.included_teams,
            included_agent_tasks: billingForm.included_agent_tasks,
            included_storage_gb: billingForm.included_storage_gb,
            per_athlete_price: String(billingForm.per_athlete_price),
            per_agent_task_price: String(billingForm.per_agent_task_price),
            features: billingForm.features
          }
        });
        const subscription = await apiRequest<SubscriptionRead>("/billing/subscriptions", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            billing_plan_id: plan.id,
            billing_cycle: billingForm.billing_cycle,
            current_period_start: billingForm.period_start,
            current_period_end: billingForm.period_end,
            trial_ends_on: null,
            next_billing_on: billingForm.period_end,
            seats_purchased: billingForm.seats_purchased,
            negotiated_price: String(billingForm.negotiated_price),
            discount_code: "EARLY",
            external_customer_id: `cus_${selectedOrganizationId.slice(0, 8)}`,
            external_subscription_id: `sub_${Date.now()}`,
            notes: "Created from AfroLete billing console."
          }
        });
        return { plan, subscription };
      },
      ({ plan, subscription }) => {
        setBillingPlans((current) => [plan, ...current.filter((item) => item.id !== plan.id)]);
        setSubscriptions((current) => [
          subscription,
          ...current.filter((item) => item.id !== subscription.id)
        ]);
        setSelectedBillingPlanId(plan.id);
        setSelectedSubscriptionId(subscription.id);
        addLog(`${selectedOrganization?.name ?? "Tenant"} subscribed to ${plan.name}`, "good");
        void loadBilling(selectedOrganizationId);
      }
    );
  };

  const createUsageMeterAndRecord = () => {
    if (!selectedOrganizationId || !selectedSubscriptionId) {
      addLog("Create or select a subscription first", "bad");
      return;
    }
    runAction(
      "create-usage-meter-record",
      async () => {
        const meter = await apiRequest<UsageMeterRead>("/billing/meters", {
          method: "POST",
          body: {
            code: `${billingForm.meter_code}-${Date.now()}`,
            name: billingForm.meter_name,
            unit: billingForm.usage_unit,
            included_quantity: billingForm.included_quantity,
            overage_price: String(billingForm.overage_price),
            aggregation: "sum"
          }
        });
        const record = await apiRequest<UsageRecordRead>("/billing/usage", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            subscription_id: selectedSubscriptionId,
            usage_meter_id: meter.id,
            quantity: billingForm.usage_quantity,
            source: "console",
            external_reference: `usage-${Date.now()}`,
            notes: "Usage recorded from local console."
          }
        });
        return { meter, record };
      },
      ({ meter, record }) => {
        setUsageMeters((current) => [meter, ...current.filter((item) => item.id !== meter.id)]);
        setUsageRecords((current) => [record, ...current.filter((item) => item.id !== record.id)]);
        setSelectedUsageMeterId(meter.id);
        addLog(`${record.quantity} ${meter.unit} recorded`, "good");
        void loadBilling(selectedOrganizationId);
      }
    );
  };

  const createSaaSInvoiceAndPayment = () => {
    if (!selectedOrganizationId || !selectedSubscriptionId) {
      addLog("Create or select a subscription first", "bad");
      return;
    }
    runAction(
      "create-saas-invoice-payment",
      async () => {
        const invoice = await apiRequest<SaaSInvoiceRead>("/billing/invoices", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            subscription_id: selectedSubscriptionId,
            invoice_number: `${billingForm.invoice_number}-${Date.now()}`,
            period_start: billingForm.period_start,
            period_end: billingForm.period_end,
            tax_amount: String(billingForm.tax_amount),
            discount_amount: String(billingForm.discount_amount),
            due_on: billingForm.period_end
          }
        });
        const payment = await apiRequest<SaaSPaymentRead>("/billing/payments", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            invoice_id: invoice.id,
            amount: String(billingForm.payment_amount),
            provider: "manual",
            external_payment_id: `pay_${Date.now()}`,
            notes: "SaaS payment captured from billing console."
          }
        });
        return { invoice, payment };
      },
      ({ invoice, payment }) => {
        setSaasInvoices((current) => [invoice, ...current.filter((item) => item.id !== invoice.id)]);
        setSaasPayments((current) => [payment, ...current.filter((item) => item.id !== payment.id)]);
        setSelectedSaasInvoiceId(invoice.id);
        addLog(`SaaS invoice ${invoice.invoice_number} paid ${payment.amount}`, "good");
        void loadBilling(selectedOrganizationId);
      }
    );
  };

  const createBillingEntitlement = () => {
    if (!selectedOrganizationId || !selectedSubscriptionId) {
      addLog("Create or select a subscription first", "bad");
      return;
    }
    runAction(
      "create-billing-entitlement",
      () =>
        apiRequest<BillingEntitlementRead>("/billing/entitlements", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            subscription_id: selectedSubscriptionId,
            feature_key: billingForm.entitlement_feature,
            limit_value: billingForm.entitlement_limit,
            used_value: agents.length,
            resets_on: billingForm.period_end
          }
        }),
      (entitlement) => {
        setBillingEntitlements((current) => [
          entitlement,
          ...current.filter((item) => item.id !== entitlement.id)
        ]);
        addLog(`${entitlement.feature_key} entitlement active`, "good");
        void loadBilling(selectedOrganizationId);
      }
    );
  };

  const quoteBillingTax = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "billing-tax-quote",
      () =>
        apiRequest<BillingTaxQuoteRead>(
          `/billing/tax-quote?organization_id=${selectedOrganizationId}&subtotal=${billingForm.negotiated_price}&jurisdiction=${billingForm.tax_jurisdiction}`
        ),
      (quote) => {
        setBillingTaxQuote(quote);
        setBillingForm((current) => ({ ...current, tax_amount: Number(quote.tax_amount) }));
        addLog(`${quote.jurisdiction} SaaS tax quote ${quote.tax_amount}`, "good");
      }
    );
  };

  const deliverBillingTaxFiling = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "billing-tax-filing",
      () =>
        apiRequest<BillingTaxFilingRead>(
          `/billing/tax-filing/deliver?organization_id=${selectedOrganizationId}&period_start=${billingForm.period_start}&period_end=${billingForm.period_end}&jurisdiction=${billingForm.tax_jurisdiction}`,
          { method: "POST", identity }
        ),
      (filing) => {
        setBillingTaxFiling(filing);
        addLog(
          filing.delivered ? "Tax filing delivered" : filing.failure_reason ?? "Tax filing package prepared",
          filing.delivered ? "good" : "neutral"
        );
      }
    );
  };

  const quoteBillingProration = () => {
    if (!selectedOrganizationId || !selectedSubscriptionId) {
      addLog("Create or select a subscription first", "bad");
      return;
    }
    runAction(
      "billing-proration",
      () =>
        apiRequest<BillingProrationQuoteRead>(
          `/billing/subscriptions/${selectedSubscriptionId}/proration?organization_id=${selectedOrganizationId}&new_price=${billingForm.prorated_price}&effective_on=${billingForm.period_start}`,
          { identity }
        ),
      (quote) => {
        setBillingProration(quote);
        addLog(`Proration net ${quote.net_amount}`, "good");
      }
    );
  };

  const applyBillingPlanChange = () => {
    if (!selectedOrganizationId || !selectedSubscriptionId) {
      addLog("Create or select a subscription first", "bad");
      return;
    }
    runAction(
      "billing-plan-change",
      () =>
        apiRequest<BillingPlanChangeRead>(
          `/billing/subscriptions/${selectedSubscriptionId}/plan-change`,
          {
            method: "POST",
            identity,
            body: {
              organization_id: selectedOrganizationId,
              new_price: String(billingForm.prorated_price),
              effective_on: billingForm.period_start,
              note: "Applied from AfroLete billing console."
            }
          }
        ),
      (change) => {
        setBillingPlanChange(change);
        setBillingProration(change);
        addLog(`Plan change applied at ${change.applied_price}`, "good");
        void loadBilling(selectedOrganizationId);
      }
    );
  };

  const prepareDunningNotice = () => {
    if (!selectedOrganizationId || !selectedSaasInvoiceId) {
      addLog("Create or select a SaaS invoice first", "bad");
      return;
    }
    runAction(
      "billing-dunning",
      () =>
        apiRequest<BillingDunningNoticeRead>(
          `/billing/invoices/${selectedSaasInvoiceId}/dunning?organization_id=${selectedOrganizationId}`,
          { method: "POST", identity }
        ),
      (notice) => {
        setBillingDunning(notice);
        setBillingDunningDelivery(null);
        addLog(`${notice.severity} dunning notice prepared`, "good");
      }
    );
  };

  const deliverBillingDunningNotice = () => {
    if (!selectedOrganizationId || !selectedSaasInvoiceId) {
      addLog("Create or select a SaaS invoice first", "bad");
      return;
    }
    runAction(
      "billing-dunning-delivery",
      () =>
        apiRequest<BillingDunningDeliveryRead>(
          `/billing/invoices/${selectedSaasInvoiceId}/dunning/deliver?organization_id=${selectedOrganizationId}`,
          { method: "POST", identity }
        ),
      (delivery) => {
        setBillingDunning(delivery);
        setBillingDunningDelivery(delivery);
        addLog(
          delivery.delivered ? "Dunning notice delivered" : delivery.failure_reason ?? "Dunning notice recorded",
          delivery.delivered ? "good" : "neutral"
        );
      }
    );
  };

  const ingestBillingWebhook = () => {
    if (!selectedOrganizationId || !selectedSaasInvoiceId) {
      addLog("Create or select a SaaS invoice first", "bad");
      return;
    }
    runAction(
      "billing-payment-webhook",
      () =>
        apiRequest<BillingPaymentWebhookRead>("/billing/webhooks/payments", {
          method: "POST",
          body: {
            organization_id: selectedOrganizationId,
            invoice_id: selectedSaasInvoiceId,
            provider: billingForm.webhook_provider,
            event_type: "payment.succeeded",
            status: "succeeded",
            amount: String(billingForm.payment_amount),
            external_payment_id: `webhook_${Date.now()}`,
            raw_reference: "Console simulated payment processor webhook."
          }
        }),
      (webhook) => {
        setBillingWebhook(webhook);
        addLog(webhook.message, webhook.accepted ? "good" : "neutral");
        void loadBilling(selectedOrganizationId);
      }
    );
  };

  const consentUrl = consentRequest?.one_time_token
    ? `${window.location.origin}/consent/${consentRequest.one_time_token}`
    : "";

  return (
    <main className="app-shell">
      <aside className="app-rail" aria-label="Primary">
        <div className="brand-lockup">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Operations</span>
          </div>
        </div>
        <nav>
          <a href="#command" className="active">Command</a>
          <a href="#tenant">Tenant</a>
          <a href="#roster">Roster</a>
          <a href="#events">Events</a>
          <a href="#assets">Assets</a>
          <a href="#commercial">Commerce</a>
          <a href="#reports">Reports</a>
          <a href="#billing">Billing</a>
          <a href="#competition">Competition</a>
          <a href="#communications">Comms</a>
          <a href="#performance">Performance</a>
          <a href="#training">Training</a>
          <a href="#agents">Agents</a>
          <a href="#safeguarding">Safeguarding</a>
        </nav>
        <div className="rail-status">
          <span>API</span>
          <strong>{apiBaseUrl.replace("http://", "")}</strong>
        </div>
      </aside>

      <section className="workspace" id="command">
        <header className="topbar">
          <div>
            <p className="eyebrow">Live command surface</p>
            <h1>{selectedOrganization?.public_name ?? selectedOrganization?.name ?? "Build an operating tenant"}</h1>
          </div>
          <div className="topbar-actions">
            {keycloakEnabled ? (
              authSession ? (
                <button type="button" onClick={endKeycloakSession}>
                  Sign out
                </button>
              ) : (
                <button type="button" onClick={beginKeycloakLogin} disabled={busyAction !== null}>
                  Sign in
                </button>
              )
            ) : null}
            <button
              type="button"
              onClick={() => void loadOrganizations()}
              disabled={busyAction !== null || (keycloakEnabled && !authSession)}
            >
              Sync
            </button>
          </div>
        </header>

        <section className="operator-grid" aria-label="Workspace summary">
          <form className="panel identity-panel" onSubmit={(event) => event.preventDefault()}>
            <p className="section-label">Operator</p>
            <div className="auth-mode-card">
              <span>{keycloakEnabled ? "Keycloak" : "Local"} auth</span>
              <strong>
                {keycloakEnabled
                  ? authSession?.email ?? authSession?.name ?? "No browser session"
                  : "Trusted local headers"}
              </strong>
              {keycloakEnabled ? (
                <small>
                  {keycloakClientId} at {keycloakIssuer}
                </small>
              ) : (
                <small>Development session</small>
              )}
              {keycloakEnabled ? (
                <div className="auth-actions">
                  {authSession ? (
                    <button type="button" onClick={endKeycloakSession}>
                      Sign out
                    </button>
                  ) : (
                    <button type="button" onClick={beginKeycloakLogin} disabled={busyAction !== null}>
                      Sign in with Keycloak
                    </button>
                  )}
                </div>
              ) : null}
            </div>
            <label>
              Name
              <input value={identity.name} onChange={(event) => setIdentity({ ...identity, name: event.target.value })} />
            </label>
            <label>
              Email
              <input value={identity.email} onChange={(event) => setIdentity({ ...identity, email: event.target.value })} />
            </label>
            <label>
              Subject
              <input value={identity.sub} onChange={(event) => setIdentity({ ...identity, sub: event.target.value })} />
            </label>
          </form>

          <div className="panel status-panel">
            <p className="section-label">State</p>
            <div className="stat-row">
              <span>Organizations</span>
              <strong>{organizations.length}</strong>
            </div>
            <div className="stat-row">
              <span>Teams</span>
              <strong>{teams.length}</strong>
            </div>
            <div className="stat-row">
              <span>Events</span>
              <strong>{events.length}</strong>
            </div>
            <div className="stat-row">
              <span>Competitions</span>
              <strong>{competitions.length}</strong>
            </div>
            <div className="stat-row">
              <span>Messages</span>
              <strong>{communicationMessages.length}</strong>
            </div>
            <div className="stat-row">
              <span>Assets</span>
              <strong>{assetSummary?.equipment_items ?? 0}</strong>
            </div>
            <div className="stat-row">
              <span>Revenue</span>
              <strong>{commercialSummary?.tickets_sold ?? 0}</strong>
            </div>
            <div className="stat-row">
              <span>Insights</span>
              <strong>{reportingSummary?.open_insights ?? 0}</strong>
            </div>
            <div className="stat-row">
              <span>MRR</span>
              <strong>{billingSummary?.monthly_recurring_revenue ?? "0"}</strong>
            </div>
            <div className="stat-row">
              <span>Attendance</span>
              <strong>{attendance.length}</strong>
            </div>
            <div className="stat-row">
              <span>Agents</span>
              <strong>{agents.length}</strong>
            </div>
            <div className="stat-row">
              <span>ALS</span>
              <strong>{performanceSummary?.latest_overall_score ?? "—"}</strong>
            </div>
            <div className="stat-row">
              <span>Training</span>
              <strong>{trainingPlans.length}</strong>
            </div>
          </div>

          <div className="panel log-panel">
            <p className="section-label">Activity</p>
            <div className="activity-list">
              {logs.length === 0 ? <span className="muted">No activity yet</span> : null}
              {logs.map((log) => (
                <p key={log.id} className={`log-line ${log.tone}`}>{log.message}</p>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid">
          <form className="panel form-panel" id="tenant" onSubmit={createOrganization}>
            <div className="panel-head">
              <div>
                <p className="section-label">Tenant</p>
                <h2>Organization workspace</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Create</button>
            </div>
            <div className="form-grid">
              <label>
                Name
                <input value={organizationForm.name} onChange={(event) => setOrganizationForm({ ...organizationForm, name: event.target.value })} />
              </label>
              <label>
                Type
                <select value={organizationForm.organization_type} onChange={(event) => setOrganizationForm({ ...organizationForm, organization_type: event.target.value as OrganizationType })}>
                  <option value="club">Club</option>
                  <option value="school">School</option>
                  <option value="academy">Academy</option>
                  <option value="association">Association</option>
                  <option value="federation">Federation</option>
                </select>
              </label>
              <label>
                Public name
                <input value={organizationForm.public_name} onChange={(event) => setOrganizationForm({ ...organizationForm, public_name: event.target.value })} />
              </label>
              <label>
                Subdomain
                <input value={organizationForm.subdomain} onChange={(event) => setOrganizationForm({ ...organizationForm, subdomain: event.target.value })} />
              </label>
              <label>
                Sport
                <input value={organizationForm.primary_sport} onChange={(event) => setOrganizationForm({ ...organizationForm, primary_sport: event.target.value })} />
              </label>
              <label>
                Contact
                <input value={organizationForm.contact_email} onChange={(event) => setOrganizationForm({ ...organizationForm, contact_email: event.target.value })} />
              </label>
            </div>
            <div className="selection-list">
              {organizations.map((organization) => (
                <button
                  type="button"
                  key={organization.id}
                  className={organization.id === selectedOrganizationId ? "selected" : ""}
                  onClick={() => setSelectedOrganizationId(organization.id)}
                >
                  <span>{organization.name}</span>
                  <small>{organization.organization_type} · {organization.my_roles.join(", ")}</small>
                </button>
              ))}
            </div>
          </form>

          <form className="panel form-panel" onSubmit={createTeam}>
            <div className="panel-head">
              <div>
                <p className="section-label">Team</p>
                <h2>Squad builder</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Create</button>
            </div>
            <div className="form-grid">
              <label>
                Name
                <input value={teamForm.name} onChange={(event) => setTeamForm({ ...teamForm, name: event.target.value })} />
              </label>
              <label>
                Format
                <select value={teamForm.sport_format} onChange={(event) => setTeamForm({ ...teamForm, sport_format: event.target.value as SportFormat })}>
                  <option value="team">Team sport</option>
                  <option value="individual">Individual sport</option>
                  <option value="mixed">Mixed program</option>
                </select>
              </label>
              <label>
                Sport
                <input value={teamForm.sport} onChange={(event) => setTeamForm({ ...teamForm, sport: event.target.value })} />
              </label>
              <label>
                Age
                <input value={teamForm.age_group} onChange={(event) => setTeamForm({ ...teamForm, age_group: event.target.value })} />
              </label>
              <label>
                Gender
                <input value={teamForm.gender_category} onChange={(event) => setTeamForm({ ...teamForm, gender_category: event.target.value })} />
              </label>
              <label>
                Season
                <input value={teamForm.season_label} onChange={(event) => setTeamForm({ ...teamForm, season_label: event.target.value })} />
              </label>
            </div>
            <div className="selection-list">
              {teams.map((team) => (
                <button
                  type="button"
                  key={team.id}
                  className={team.id === selectedTeamId ? "selected" : ""}
                  onClick={() => setSelectedTeamId(team.id)}
                >
                  <span>{team.name}</span>
                  <small>{team.sport} · {team.sport_format}</small>
                </button>
              ))}
            </div>
          </form>
        </section>

        <section className="work-grid">
          <form className="panel form-panel" id="roster" onSubmit={addAthlete}>
            <div className="panel-head">
              <div>
                <p className="section-label">Roster</p>
                <h2>Athlete intake</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Add</button>
            </div>
            <div className="form-grid">
              <label>
                Athlete
                <input value={athleteForm.display_name} onChange={(event) => setAthleteForm({ ...athleteForm, display_name: event.target.value })} />
              </label>
              <label>
                Email
                <input value={athleteForm.email} onChange={(event) => setAthleteForm({ ...athleteForm, email: event.target.value })} />
              </label>
              <label>
                Role
                <select value={athleteForm.role} onChange={(event) => setAthleteForm({ ...athleteForm, role: event.target.value as TeamRole })}>
                  <option value="player">Player</option>
                  <option value="captain">Captain</option>
                  <option value="substitute">Substitute</option>
                  <option value="bench">Bench</option>
                  <option value="individual_athlete">Individual athlete</option>
                </select>
              </label>
              <label>
                Position
                <input value={athleteForm.primary_position} onChange={(event) => setAthleteForm({ ...athleteForm, primary_position: event.target.value })} />
              </label>
              <label>
                Jersey
                <input value={athleteForm.jersey_number} onChange={(event) => setAthleteForm({ ...athleteForm, jersey_number: event.target.value })} />
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={athleteForm.is_captain} onChange={(event) => setAthleteForm({ ...athleteForm, is_captain: event.target.checked })} />
                Captain
              </label>
            </div>
            <div className="selection-list">
              {athletes.map((athlete) => (
                <button
                  type="button"
                  key={athlete.personId}
                  className={athlete.personId === selectedAthleteId ? "selected" : ""}
                  onClick={() => setSelectedAthleteId(athlete.personId)}
                >
                  <span>{athlete.name}</span>
                  <small>{athlete.email}</small>
                </button>
              ))}
            </div>
          </form>

          <form className="panel form-panel" id="events" onSubmit={createEvent}>
            <div className="panel-head">
              <div>
                <p className="section-label">Events</p>
                <h2>Schedule and check-in</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Schedule</button>
            </div>
            <div className="form-grid">
              <label>
                Title
                <input value={eventForm.title} onChange={(event) => setEventForm({ ...eventForm, title: event.target.value })} />
              </label>
              <label>
                Type
                <select value={eventForm.event_type} onChange={(event) => setEventForm({ ...eventForm, event_type: event.target.value as EventType })}>
                  <option value="match">Match</option>
                  <option value="training">Training</option>
                  <option value="tournament">Tournament</option>
                  <option value="assessment">Assessment</option>
                  <option value="meeting">Meeting</option>
                </select>
              </label>
              <label>
                Start
                <input type="datetime-local" value={eventForm.starts_at} onChange={(event) => setEventForm({ ...eventForm, starts_at: event.target.value })} />
              </label>
              <label>
                Minutes
                <input type="number" min="15" value={eventForm.duration_minutes} onChange={(event) => setEventForm({ ...eventForm, duration_minutes: Number(event.target.value) })} />
              </label>
              <label>
                Venue
                <input value={eventForm.venue_name} onChange={(event) => setEventForm({ ...eventForm, venue_name: event.target.value })} />
              </label>
              <label>
                Timezone
                <input value={eventForm.timezone} onChange={(event) => setEventForm({ ...eventForm, timezone: event.target.value })} />
              </label>
            </div>
            <div className="event-toolbar">
              <button type="button" onClick={seedAttendance} disabled={busyAction !== null}>Seed roster</button>
              <button type="button" onClick={checkClearance} disabled={busyAction !== null}>Clearance</button>
            </div>
            <div className="selection-list compact">
              {events.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={item.id === selectedEventId ? "selected" : ""}
                  onClick={() => setSelectedEventId(item.id)}
                >
                  <span>{item.title}</span>
                  <small>{item.event_type} · {new Date(item.starts_at).toLocaleString()}</small>
                </button>
              ))}
            </div>
            <div className="attendance-table">
              {attendance.map((record) => (
                <div key={record.id} className="attendance-row">
                  <span>{record.person_id.slice(0, 8)}</span>
                  <strong>{record.status}</strong>
                  <button type="button" onClick={() => recordAttendance(record.person_id, "present")}>
                    Present
                  </button>
                  <button type="button" onClick={() => recordAttendance(record.person_id, "confirmed")}>
                    Confirm
                  </button>
                </div>
              ))}
            </div>
          </form>
        </section>

        <section className="work-grid" id="assets">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Facilities</p>
                <h2>Assets, bookings, and inventory</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createFacility} disabled={busyAction !== null}>Facility</button>
                <button type="button" onClick={createFacilityBooking} disabled={busyAction !== null}>Book</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{assetSummary?.booked_hours ?? 0}</strong>
              <span>Booked hours</span>
              <small>{assetSummary ? `$${assetSummary.projected_booking_revenue} projected` : "No asset summary"}</small>
            </div>
            <div className="form-grid">
              <label>
                Facility
                <input value={facilityForm.name} onChange={(event) => setFacilityForm({ ...facilityForm, name: event.target.value })} />
              </label>
              <label>
                Type
                <select value={facilityForm.facility_type} onChange={(event) => setFacilityForm({ ...facilityForm, facility_type: event.target.value as FacilityType })}>
                  <option value="field">Field</option>
                  <option value="court">Court</option>
                  <option value="stadium">Stadium</option>
                  <option value="gym">Gym</option>
                  <option value="pool">Pool</option>
                  <option value="clubhouse">Clubhouse</option>
                  <option value="storage">Storage</option>
                </select>
              </label>
              <label>
                Surface
                <input value={facilityForm.surface} onChange={(event) => setFacilityForm({ ...facilityForm, surface: event.target.value })} />
              </label>
              <label>
                Capacity
                <input type="number" min="0" value={facilityForm.capacity} onChange={(event) => setFacilityForm({ ...facilityForm, capacity: Number(event.target.value) })} />
              </label>
              <label>
                Rate
                <input type="number" min="0" value={facilityForm.hourly_rate} onChange={(event) => setFacilityForm({ ...facilityForm, hourly_rate: Number(event.target.value) })} />
              </label>
              <label>
                Condition
                <select value={facilityForm.condition} onChange={(event) => setFacilityForm({ ...facilityForm, condition: event.target.value as AssetCondition })}>
                  <option value="new">New</option>
                  <option value="good">Good</option>
                  <option value="fair">Fair</option>
                  <option value="poor">Poor</option>
                  <option value="unusable">Unusable</option>
                </select>
              </label>
              <label className="wide-field">
                Amenities
                <input value={facilityForm.amenities} onChange={(event) => setFacilityForm({ ...facilityForm, amenities: event.target.value })} />
              </label>
            </div>
            <div className="selection-list compact">
              {facilities.map((facility) => (
                <button
                  type="button"
                  key={facility.id}
                  className={facility.id === selectedFacilityId ? "selected" : ""}
                  onClick={() => setSelectedFacilityId(facility.id)}
                >
                  <span>{facility.name}</span>
                  <small>{facility.facility_type} · {facility.status} · {facility.condition}</small>
                </button>
              ))}
            </div>
            <div className="form-grid">
              <label>
                Booking
                <input value={bookingForm.title} onChange={(event) => setBookingForm({ ...bookingForm, title: event.target.value })} />
              </label>
              <label>
                Starts
                <input type="datetime-local" value={bookingForm.starts_at} onChange={(event) => setBookingForm({ ...bookingForm, starts_at: event.target.value })} />
              </label>
              <label>
                Hours
                <input type="number" min="1" value={bookingForm.duration_hours} onChange={(event) => setBookingForm({ ...bookingForm, duration_hours: Number(event.target.value) })} />
              </label>
              <label>
                Attendees
                <input type="number" min="0" value={bookingForm.expected_attendees} onChange={(event) => setBookingForm({ ...bookingForm, expected_attendees: Number(event.target.value) })} />
              </label>
            </div>
            <div className="task-list">
              {facilityBookings.slice(0, 3).map((booking) => (
                <article key={booking.id} className="task-card">
                  <div>
                    <strong>{booking.title}</strong>
                    <span>{booking.status} · {new Date(booking.starts_at).toLocaleString()}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Inventory</p>
                <h2>Checkout and maintenance</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createEquipmentItem} disabled={busyAction !== null}>Item</button>
                <button type="button" onClick={scanEquipmentItem} disabled={busyAction !== null}>Scan</button>
                <button type="button" onClick={recordRfidEquipmentScan} disabled={busyAction !== null}>RFID</button>
                <button type="button" onClick={provisionRfidReader} disabled={busyAction !== null}>Reader</button>
                <button type="button" onClick={recordGatewayRfidScan} disabled={busyAction !== null}>Gateway</button>
                <button type="button" onClick={updateSelectedEquipmentPhoto} disabled={busyAction !== null}>Photo</button>
                <button type="button" onClick={uploadSelectedEquipmentFile} disabled={busyAction !== null}>Upload</button>
                <button type="button" onClick={quoteSelectedEquipmentLease} disabled={busyAction !== null}>Lease</button>
                <button type="button" onClick={billSelectedEquipmentLease} disabled={busyAction !== null}>Bill</button>
                <button type="button" onClick={scheduleSelectedEquipmentLease} disabled={busyAction !== null}>Schedule</button>
                <button type="button" onClick={() => reconcileNextLeaseInstallment()} disabled={busyAction !== null}>Reconcile</button>
                <button type="button" onClick={checkoutEquipmentItem} disabled={busyAction !== null}>Checkout</button>
                <button type="button" onClick={returnSelectedCheckout} disabled={busyAction !== null}>Return</button>
              </div>
            </div>
            <div className="consent-grid">
              <div>
                <span className="muted">Stock alerts</span>
                <strong>{assetSummary?.stock_alerts ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Open checkouts</span>
                <strong>{assetSummary?.open_checkouts ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Work orders</span>
                <strong>{assetSummary?.open_work_orders ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Safety</span>
                <strong>{assetSummary?.safety_work_orders ?? 0}</strong>
              </div>
              <div>
                <span className="muted">RFID scans</span>
                <strong>{equipmentScanEvents.length}</strong>
              </div>
              <div>
                <span className="muted">Readers</span>
                <strong>{equipmentReaders.length}</strong>
              </div>
              <div>
                <span className="muted">Leases</span>
                <strong>{leaseSchedules.length}</strong>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Item
                <input value={equipmentForm.name} onChange={(event) => setEquipmentForm({ ...equipmentForm, name: event.target.value })} />
              </label>
              <label>
                Category
                <input value={equipmentForm.category} onChange={(event) => setEquipmentForm({ ...equipmentForm, category: event.target.value })} />
              </label>
              <label>
                Quantity
                <input type="number" min="1" value={equipmentForm.quantity_total} onChange={(event) => setEquipmentForm({ ...equipmentForm, quantity_total: Number(event.target.value) })} />
              </label>
              <label>
                Reorder
                <input type="number" min="0" value={equipmentForm.reorder_point} onChange={(event) => setEquipmentForm({ ...equipmentForm, reorder_point: Number(event.target.value) })} />
              </label>
              <label>
                Tag
                <input value={equipmentForm.tag_code} onChange={(event) => setEquipmentForm({ ...equipmentForm, tag_code: event.target.value })} />
              </label>
              <label>
                Serial
                <input value={equipmentForm.serial_number} onChange={(event) => setEquipmentForm({ ...equipmentForm, serial_number: event.target.value })} />
              </label>
              <label>
                Photo URL
                <input value={equipmentForm.photo_url} onChange={(event) => setEquipmentForm({ ...equipmentForm, photo_url: event.target.value })} />
              </label>
              <label>
                Location
                <input value={equipmentForm.storage_location} onChange={(event) => setEquipmentForm({ ...equipmentForm, storage_location: event.target.value })} />
              </label>
              <label>
                Reader
                <input value={rfidForm.reader_id} onChange={(event) => setRfidForm({ ...rfidForm, reader_id: event.target.value })} />
              </label>
              <label>
                Reader name
                <input value={rfidForm.reader_name} onChange={(event) => setRfidForm({ ...rfidForm, reader_name: event.target.value })} />
              </label>
              <label>
                Reader location
                <input value={rfidForm.reader_location} onChange={(event) => setRfidForm({ ...rfidForm, reader_location: event.target.value })} />
              </label>
              <label>
                Reader key
                <input value={rfidForm.api_key} onChange={(event) => setRfidForm({ ...rfidForm, api_key: event.target.value })} />
              </label>
              <label>
                Gateway code
                <input value={rfidForm.gateway_code} onChange={(event) => setRfidForm({ ...rfidForm, gateway_code: event.target.value })} />
              </label>
              <label>
                Movement
                <select value={rfidForm.movement} onChange={(event) => setRfidForm({ ...rfidForm, movement: event.target.value })}>
                  <option value="audit">Audit</option>
                  <option value="in">In</option>
                  <option value="out">Out</option>
                  <option value="location">Location</option>
                </select>
              </label>
              <label className="wide-field">
                File
                <input type="file" onChange={(event) => setSelectedEquipmentFile(event.target.files?.[0] ?? null)} />
              </label>
            </div>
            <div className="selection-list compact">
              {equipmentItems.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={item.id === selectedEquipmentId ? "selected" : ""}
                  onClick={() => setSelectedEquipmentId(item.id)}
                >
                  <span>{item.name}</span>
                  <small>{item.quantity_available}/{item.quantity_total} · {item.status} · {item.storage_location ?? "No location"}</small>
                </button>
              ))}
            </div>
            <div className="form-grid">
              <label>
                Quantity out
                <input type="number" min="1" value={checkoutForm.quantity} onChange={(event) => setCheckoutForm({ ...checkoutForm, quantity: Number(event.target.value) })} />
              </label>
              <label>
                Due
                <input type="datetime-local" value={checkoutForm.due_at} onChange={(event) => setCheckoutForm({ ...checkoutForm, due_at: event.target.value })} />
              </label>
              <label className="wide-field">
                Purpose
                <input value={checkoutForm.purpose} onChange={(event) => setCheckoutForm({ ...checkoutForm, purpose: event.target.value })} />
              </label>
            </div>
            {leaseQuote ? (
              <div className="score-summary">
                <strong>{leaseQuote.monthly_amount}</strong>
                <span>{leaseQuote.item_name} lease estimate</span>
                <small>{leaseQuote.term_months} months · total ${leaseQuote.total_amount}</small>
              </div>
            ) : null}
            {leaseInvoice ? (
              <div className="score-summary">
                <strong>{leaseInvoice.invoice.amount_due}</strong>
                <span>{leaseInvoice.invoice.invoice_number}</span>
                <small>{leaseInvoice.invoice.title} · due {leaseInvoice.invoice.due_on ?? "now"}</small>
              </div>
            ) : null}
            <div className="task-list">
              {leasePayment ? (
                <article className="task-card">
                  <div>
                    <strong>{leasePayment.installments_paid} paid · {leasePayment.installments_partially_paid} partial</strong>
                    <span>{leasePayment.payment.method} · {leasePayment.amount_applied} applied · {leasePayment.remaining_balance} remaining</span>
                  </div>
                </article>
              ) : null}
              {leaseSchedules.slice(0, 2).map((schedule) => (
                <article key={schedule.id} className="task-card">
                  <div>
                    <strong>{schedule.invoice.title}</strong>
                    <span>
                      {schedule.term_months} x {schedule.currency} {schedule.monthly_amount} · paid {schedule.installments[0]?.amount_paid ?? "0.00"}/{schedule.installments[0]?.amount ?? schedule.monthly_amount} · next {schedule.installments[0]?.due_on ?? schedule.starts_on}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => reconcileNextLeaseInstallment(schedule.id)}
                    disabled={schedule.status === "paid"}
                  >
                    Pay
                  </button>
                </article>
              ))}
              {equipmentReaders.slice(0, 3).map((reader) => (
                <article key={reader.id} className="task-card">
                  <div>
                    <strong>{reader.name}</strong>
                    <span>{reader.reader_id} · {reader.status} · {reader.location ?? "No location"} · last {reader.last_scan_at ? new Date(reader.last_scan_at).toLocaleString() : "never"}</span>
                  </div>
                </article>
              ))}
              {equipmentScanEvents.slice(0, 3).map((scanEvent) => (
                <article key={scanEvent.id} className="task-card">
                  <div>
                    <strong>{scanEvent.matched ? scanEvent.item_name ?? scanEvent.scanned_code : `Unmatched ${scanEvent.scanned_code}`}</strong>
                    <span>{scanEvent.reader_id} · {scanEvent.movement} · {new Date(scanEvent.scanned_at).toLocaleString()}</span>
                  </div>
                </article>
              ))}
              {equipmentFiles.slice(0, 3).map((fileRecord) => (
                <article key={fileRecord.id} className="task-card">
                  <div>
                    <strong>{fileRecord.filename}</strong>
                    <span>{fileRecord.content_type} · {fileRecord.size_bytes} bytes · {fileRecord.checksum.slice(0, 8)}</span>
                  </div>
                </article>
              ))}
              {equipmentCheckouts.slice(0, 3).map((checkout) => (
                <button
                  type="button"
                  key={checkout.id}
                  className={`task-card ${checkout.id === selectedCheckoutId ? "selected" : ""}`}
                  onClick={() => setSelectedCheckoutId(checkout.id)}
                >
                  <div>
                    <strong>{checkout.quantity} out · {checkout.status}</strong>
                    <span>{checkout.purpose} · due {new Date(checkout.due_at).toLocaleString()}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Maintenance</p>
                <h2>Work orders and safety compliance</h2>
              </div>
              <button type="button" onClick={createWorkOrder} disabled={busyAction !== null}>Work order</button>
            </div>
            <div className="form-grid">
              <label>
                Title
                <input value={workOrderForm.title} onChange={(event) => setWorkOrderForm({ ...workOrderForm, title: event.target.value })} />
              </label>
              <label>
                Priority
                <select value={workOrderForm.priority} onChange={(event) => setWorkOrderForm({ ...workOrderForm, priority: event.target.value as WorkOrderPriority })}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </label>
              <label>
                Due
                <input type="datetime-local" value={workOrderForm.due_at} onChange={(event) => setWorkOrderForm({ ...workOrderForm, due_at: event.target.value })} />
              </label>
              <label>
                Cost
                <input type="number" min="0" value={workOrderForm.estimated_cost} onChange={(event) => setWorkOrderForm({ ...workOrderForm, estimated_cost: Number(event.target.value) })} />
              </label>
              <label>
                Compliance
                <input value={workOrderForm.compliance_reference} onChange={(event) => setWorkOrderForm({ ...workOrderForm, compliance_reference: event.target.value })} />
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={workOrderForm.safety_related} onChange={(event) => setWorkOrderForm({ ...workOrderForm, safety_related: event.target.checked })} />
                Safety related
              </label>
            </div>
            <div className="task-list">
              {workOrders.map((workOrder) => (
                <article
                  key={workOrder.id}
                  className={`task-card ${workOrder.id === selectedWorkOrderId ? "selected" : ""}`}
                  onClick={() => setSelectedWorkOrderId(workOrder.id)}
                >
                  <div>
                    <strong>{workOrder.title}</strong>
                    <span>{workOrder.priority} · {workOrder.status} · {workOrder.compliance_reference ?? "No standard"}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => updateWorkOrderStatus(workOrder.id, "completed")}
                    disabled={workOrder.status === "completed"}
                  >
                    Done
                  </button>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Asset readiness</p>
                <h2>Operational checks</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={() => createSupplierOrder()} disabled={busyAction !== null}>Order</button>
                <button type="button" onClick={() => submitSupplierOrder()} disabled={busyAction !== null}>Submit</button>
                <button type="button" onClick={() => receiveSupplierOrder()} disabled={busyAction !== null}>Receive</button>
                <button type="button" onClick={() => syncSupplierInvoice()} disabled={busyAction !== null}>Sync invoice</button>
              </div>
            </div>
            <div className="task-list">
              {supplierSubmission ? (
                <article className="task-card">
                  <div>
                    <strong>{supplierSubmission.delivered ? "Supplier delivered" : "Supplier prepared"}</strong>
                    <span>{supplierSubmission.submission_mode} · {supplierSubmission.provider_status_code ?? "no provider"} · {supplierSubmission.failure_reason ?? "accepted"}</span>
                  </div>
                </article>
              ) : null}
              {supplierInvoiceSync ? (
                <article className="task-card">
                  <div>
                    <strong>{supplierInvoiceSync.synced ? "Supplier invoice synced" : "Supplier invoice prepared"}</strong>
                    <span>{supplierInvoiceSync.sync_mode} · {supplierInvoiceSync.provider_status_code ?? "no provider"} · {supplierInvoiceSync.failure_reason ?? "accepted"}</span>
                  </div>
                </article>
              ) : null}
              {procurementRecommendations.slice(0, 3).map((recommendation) => (
                <article key={recommendation.equipment_item_id} className="task-card">
                  <div>
                    <strong>{recommendation.item_name}</strong>
                    <span>{recommendation.urgency} · buy {recommendation.recommended_quantity} · ${recommendation.estimated_cost}</span>
                  </div>
                  <button type="button" onClick={() => createSupplierOrder(recommendation)}>
                    Order
                  </button>
                </article>
              ))}
              {supplierOrders.slice(0, 3).map((order) => (
                <article
                  key={order.id}
                  className={`task-card ${order.id === selectedSupplierOrderId ? "selected" : ""}`}
                  onClick={() => setSelectedSupplierOrderId(order.id)}
                >
                  <div>
                    <strong>{order.item_name} · {order.status}</strong>
                    <span>{order.quantity} from {order.supplier_name} · {order.currency} {order.total_cost}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => submitSupplierOrder(order.id)}
                    disabled={order.status === "submitted" || order.status === "received"}
                  >
                    Submit
                  </button>
                  <button
                    type="button"
                    onClick={() => receiveSupplierOrder(order.id)}
                    disabled={order.status === "received"}
                  >
                    Receive
                  </button>
                  <button
                    type="button"
                    onClick={() => syncSupplierInvoice(order.id)}
                    disabled={order.status === "draft" || order.status === "invoice_synced"}
                  >
                    Sync
                  </button>
                </article>
              ))}
              {supplierScores.slice(0, 2).map((supplier) => (
                <article key={supplier.supplier_name} className="task-card">
                  <div>
                    <strong>{supplier.supplier_name}</strong>
                    <span>Score {supplier.score} · {supplier.recommendation}</span>
                  </div>
                </article>
              ))}
              {assetUtilization.slice(0, 3).map((recommendation) => (
                <article key={`${recommendation.target_type}-${recommendation.target_id}`} className="task-card">
                  <div>
                    <strong>{recommendation.title}</strong>
                    <span>{recommendation.severity} · {recommendation.expected_impact}</span>
                  </div>
                </article>
              ))}
              <article className="task-card">
                <div>
                  <strong>Inventory discipline</strong>
                  <span>Checkouts reduce available quantity and returns restore stock with condition capture.</span>
                </div>
              </article>
              <article className="task-card">
                <div>
                  <strong>Facility availability</strong>
                  <span>Bookings reject overlapping time windows for confirmed facility reservations.</span>
                </div>
              </article>
              <article className="task-card">
                <div>
                  <strong>Safety compliance</strong>
                  <span>Safety-related work orders stay visible until completed with cost and notes.</span>
                </div>
              </article>
            </div>
          </div>
        </section>

        <section className="work-grid" id="commercial">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Commercial</p>
                <h2>Sponsorship and fundraising</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createSponsorAndAgreement} disabled={busyAction !== null}>Sponsor</button>
                <button type="button" onClick={createCampaignAndDonation} disabled={busyAction !== null}>Donate</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{commercialSummary?.fundraising_raised ?? "0.00"}</strong>
              <span>Raised</span>
              <small>{commercialSummary ? `${commercialSummary.active_sponsors} sponsors · ${commercialSummary.sponsorship_value} committed` : "No commercial summary"}</small>
            </div>
            <div className="form-grid">
              <label>
                Sponsor
                <input value={sponsorForm.name} onChange={(event) => setSponsorForm({ ...sponsorForm, name: event.target.value })} />
              </label>
              <label>
                Tier
                <input value={sponsorForm.tier} onChange={(event) => setSponsorForm({ ...sponsorForm, tier: event.target.value })} />
              </label>
              <label>
                Value
                <input type="number" min="0" value={sponsorForm.value_amount} onChange={(event) => setSponsorForm({ ...sponsorForm, value_amount: Number(event.target.value) })} />
              </label>
              <label>
                Contact
                <input value={sponsorForm.contact_email} onChange={(event) => setSponsorForm({ ...sponsorForm, contact_email: event.target.value })} />
              </label>
              <label className="wide-field">
                Deliverables
                <input value={sponsorForm.deliverables} onChange={(event) => setSponsorForm({ ...sponsorForm, deliverables: event.target.value })} />
              </label>
              <label>
                Campaign
                <input value={campaignForm.name} onChange={(event) => setCampaignForm({ ...campaignForm, name: event.target.value })} />
              </label>
              <label>
                Goal
                <input type="number" min="0" value={campaignForm.goal_amount} onChange={(event) => setCampaignForm({ ...campaignForm, goal_amount: Number(event.target.value) })} />
              </label>
              <label>
                Donor
                <input value={campaignForm.donor_name} onChange={(event) => setCampaignForm({ ...campaignForm, donor_name: event.target.value })} />
              </label>
              <label>
                Amount
                <input type="number" min="1" value={campaignForm.donation_amount} onChange={(event) => setCampaignForm({ ...campaignForm, donation_amount: Number(event.target.value) })} />
              </label>
            </div>
            <div className="task-list">
              {sponsorshipDashboard.slice(0, 3).map((dashboard) => (
                <article key={dashboard.sponsor_id} className="task-card">
                  <div>
                    <strong>{dashboard.sponsor_name}</strong>
                    <span>ROI {dashboard.roi_score} · {dashboard.recommendation}</span>
                  </div>
                </article>
              ))}
              {sponsorships.slice(0, 3).map((agreement) => (
                <article key={agreement.id} className="task-card">
                  <div>
                    <strong>{agreement.name}</strong>
                    <span>{agreement.tier} · {agreement.value_amount} · {agreement.status}</span>
                  </div>
                </article>
              ))}
              {campaigns.slice(0, 3).map((campaign) => (
                <button
                  type="button"
                  key={campaign.id}
                  className={`task-card ${campaign.id === selectedCampaignId ? "selected" : ""}`}
                  onClick={() => setSelectedCampaignId(campaign.id)}
                >
                  <div>
                    <strong>{campaign.name}</strong>
                    <span>{campaign.raised_amount}/{campaign.goal_amount} · {campaign.status}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Ticketing and finance</p>
                <h2>Access, invoices, and payment</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createTicketSale} disabled={busyAction !== null}>Ticket</button>
                <button type="button" onClick={checkInSelectedTicket} disabled={busyAction !== null}>Scan</button>
                <button type="button" onClick={refundSelectedTicket} disabled={busyAction !== null}>Refund ticket</button>
                <button type="button" onClick={createInvoiceAndPayment} disabled={busyAction !== null}>Invoice</button>
                <button type="button" onClick={refundSelectedInvoice} disabled={busyAction !== null}>Refund invoice</button>
                <button type="button" onClick={quoteCommercialTax} disabled={busyAction !== null}>Tax</button>
                <button type="button" onClick={settleCommercialPayments} disabled={busyAction !== null}>Settle</button>
                <button type="button" onClick={exportCommercialAccounting} disabled={busyAction !== null}>Export</button>
              </div>
            </div>
            <div className="consent-grid">
              <div>
                <span className="muted">Ticket revenue</span>
                <strong>{commercialSummary?.ticket_revenue ?? "0.00"}</strong>
              </div>
              <div>
                <span className="muted">Sold</span>
                <strong>{commercialSummary?.tickets_sold ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Checked in</span>
                <strong>{commercialSummary?.tickets_checked_in ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Outstanding</span>
                <strong>{commercialSummary?.invoice_outstanding ?? "0.00"}</strong>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Ticket
                <input value={ticketForm.name} onChange={(event) => setTicketForm({ ...ticketForm, name: event.target.value })} />
              </label>
              <label>
                Price
                <input type="number" min="0" value={ticketForm.price} onChange={(event) => setTicketForm({ ...ticketForm, price: Number(event.target.value) })} />
              </label>
              <label>
                Capacity
                <input type="number" min="1" value={ticketForm.capacity} onChange={(event) => setTicketForm({ ...ticketForm, capacity: Number(event.target.value) })} />
              </label>
              <label>
                Buyer
                <input value={ticketForm.buyer_email} onChange={(event) => setTicketForm({ ...ticketForm, buyer_email: event.target.value })} />
              </label>
              <label>
                Quantity
                <input type="number" min="1" value={ticketForm.quantity} onChange={(event) => setTicketForm({ ...ticketForm, quantity: Number(event.target.value) })} />
              </label>
              <label>
                Gate
                <input value={ticketForm.gate} onChange={(event) => setTicketForm({ ...ticketForm, gate: event.target.value })} />
              </label>
              <label>
                Invoice
                <input value={invoiceForm.invoice_number} onChange={(event) => setInvoiceForm({ ...invoiceForm, invoice_number: event.target.value })} />
              </label>
              <label>
                Due
                <input type="number" min="0" value={invoiceForm.amount_due} onChange={(event) => setInvoiceForm({ ...invoiceForm, amount_due: Number(event.target.value) })} />
              </label>
              <label>
                Payment
                <input type="number" min="0" value={invoiceForm.payment_amount} onChange={(event) => setInvoiceForm({ ...invoiceForm, payment_amount: Number(event.target.value) })} />
              </label>
            </div>
            <div className="task-list">
              {taxQuote ? (
                <article className="task-card">
                  <div>
                    <strong>Tax {taxQuote.jurisdiction}: {taxQuote.tax_amount}</strong>
                    <span>{taxQuote.subtotal} subtotal · {taxQuote.total} total</span>
                  </div>
                </article>
              ) : null}
              {paymentSettlement ? (
                <article className="task-card">
                  <div>
                    <strong>{paymentSettlement.payout_reference}</strong>
                    <span>{paymentSettlement.gross_amount} gross · {paymentSettlement.net_amount} net</span>
                  </div>
                </article>
              ) : null}
              {accountingExport ? (
                <article className="task-card">
                  <div>
                    <strong>{accountingExport.system} export</strong>
                    <span>{accountingExport.rows.length} rows · debit {accountingExport.debit_total} · credit {accountingExport.credit_total}</span>
                  </div>
                </article>
              ) : null}
              {commercialRefund ? (
                <article className="task-card">
                  <div>
                    <strong>{commercialRefund.target_type} refund</strong>
                    <span>{commercialRefund.amount} · {commercialRefund.status} · {commercialRefund.reason}</span>
                  </div>
                </article>
              ) : null}
              {tickets.slice(0, 3).map((ticket) => (
                <button
                  type="button"
                  key={ticket.id}
                  className={`task-card ${ticket.id === selectedTicketId ? "selected" : ""}`}
                  onClick={() => setSelectedTicketId(ticket.id)}
                >
                  <div>
                    <strong>{ticket.status} · {ticket.qr_token.slice(0, 12)}</strong>
                    <span>{ticket.gate ?? "No gate"} · {ticket.checked_in_at ? new Date(ticket.checked_in_at).toLocaleString() : "Not scanned"}</span>
                  </div>
                </button>
              ))}
              {invoices.slice(0, 3).map((invoice) => (
                <button
                  type="button"
                  key={invoice.id}
                  className={`task-card ${invoice.id === selectedInvoiceId ? "selected" : ""}`}
                  onClick={() => setSelectedInvoiceId(invoice.id)}
                >
                  <div>
                    <strong>{invoice.invoice_number}</strong>
                    <span>{invoice.amount_paid}/{invoice.amount_due} · {invoice.status}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid" id="reports">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Reporting</p>
                <h2>Reports and scheduled delivery</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createReportDefinitionAndRun} disabled={busyAction !== null}>Generate</button>
                <button type="button" onClick={createScheduledReport} disabled={busyAction !== null}>Schedule</button>
                <button type="button" onClick={renderSelectedReport} disabled={busyAction !== null}>Render</button>
                <button type="button" onClick={verifySelectedReport} disabled={busyAction !== null}>Verify</button>
                <button type="button" onClick={downloadSelectedReport} disabled={busyAction !== null}>Download</button>
                <button type="button" onClick={shareSelectedReportArtifact} disabled={busyAction !== null}>Link</button>
                <button type="button" onClick={createReportExport} disabled={busyAction !== null}>Export</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{reportingSummary?.generated_reports ?? 0}</strong>
              <span>Reports generated</span>
              <small>{reportingSummary ? `${reportingSummary.scheduled_reports} scheduled · ${reportingSummary.export_jobs} exports` : "No reporting summary"}</small>
            </div>
            <div className="form-grid">
              <label>
                Report
                <input value={reportForm.name} onChange={(event) => setReportForm({ ...reportForm, name: event.target.value })} />
              </label>
              <label>
                Category
                <select value={reportForm.category} onChange={(event) => setReportForm({ ...reportForm, category: event.target.value as ReportCategory })}>
                  <option value="performance">Performance</option>
                  <option value="administrative">Administrative</option>
                  <option value="operational">Operational</option>
                  <option value="financial">Financial</option>
                  <option value="compliance">Compliance</option>
                  <option value="intelligence">Intelligence</option>
                </select>
              </label>
              <label>
                Format
                <select value={reportForm.default_format} onChange={(event) => setReportForm({ ...reportForm, default_format: event.target.value as ReportFormat })}>
                  <option value="online">Online</option>
                  <option value="pdf">PDF</option>
                  <option value="excel">Excel</option>
                  <option value="csv">CSV</option>
                  <option value="api">API</option>
                </select>
              </label>
              <label>
                Frequency
                <select value={reportForm.frequency} onChange={(event) => setReportForm({ ...reportForm, frequency: event.target.value as ReportFrequency })}>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="on_trigger">On trigger</option>
                </select>
              </label>
              <label>
                Starts
                <input type="date" value={reportForm.period_start} onChange={(event) => setReportForm({ ...reportForm, period_start: event.target.value })} />
              </label>
              <label>
                Ends
                <input type="date" value={reportForm.period_end} onChange={(event) => setReportForm({ ...reportForm, period_end: event.target.value })} />
              </label>
              <label className="wide-field">
                Recipients
                <input value={reportForm.recipients} onChange={(event) => setReportForm({ ...reportForm, recipients: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {renderedReport ? (
                <article className="task-card">
                  <div>
                    <strong>{renderedReport.output_format} artifact · {renderedReport.size_bytes} bytes</strong>
                    <span>{renderedReport.artifact_url} · {renderedReport.content_type}</span>
                  </div>
                </article>
              ) : null}
              {reportVerification ? (
                <article className="task-card">
                  <div>
                    <strong>Verification {reportVerification.score}/100 · {reportVerification.passed ? "passed" : "needs work"}</strong>
                    <span>{reportVerification.findings[0]} · {reportVerification.recommendation}</span>
                  </div>
                </article>
              ) : null}
              {reportArtifactAccess ? (
                <article className="task-card">
                  <div>
                    <strong>{reportArtifactAccess.output_format} signed link · {reportArtifactAccess.size_bytes} bytes</strong>
                    <span>
                      Expires {new Date(reportArtifactAccess.expires_at).toLocaleString()} · {reportArtifactAccess.content_type}
                    </span>
                  </div>
                  <a
                    href={`${apiBaseUrl}${reportArtifactAccess.signed_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open
                  </a>
                </article>
              ) : null}
              {generatedReports.slice(0, 3).map((report) => (
                <button
                  type="button"
                  key={report.id}
                  className={`task-card ${report.id === selectedGeneratedReportId ? "selected" : ""}`}
                  onClick={() => {
                    setSelectedGeneratedReportId(report.id);
                    setReportArtifactAccess(null);
                  }}
                >
                  <div>
                    <strong>{report.title}</strong>
                    <span>{report.status} · {report.output_format} · {report.summary}</span>
                  </div>
                </button>
              ))}
              {scheduledReports.slice(0, 2).map((schedule) => (
                <article key={schedule.id} className="task-card">
                  <div>
                    <strong>{schedule.name}</strong>
                    <span>{schedule.frequency} · {schedule.delivery_channels}</span>
                  </div>
                </article>
              ))}
              {reportCharts.slice(0, 3).map((chart) => <ReportingChartCard key={chart.chart_key} chart={chart} />)}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Intelligence</p>
                <h2>AI insights and predictive risk</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createInsightAndRisk} disabled={busyAction !== null}>Insight</button>
                <button type="button" onClick={generateReportingInsight} disabled={busyAction !== null}>AI Review</button>
                <button type="button" onClick={() => updateInsight("actioned")} disabled={busyAction !== null}>Action</button>
              </div>
            </div>
            <div className="consent-grid">
              <div>
                <span className="muted">Open insights</span>
                <strong>{reportingSummary?.open_insights ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Warnings</span>
                <strong>{reportingSummary?.critical_insights ?? 0}</strong>
              </div>
              <div>
                <span className="muted">High risk</span>
                <strong>{reportingSummary?.high_risk_scores ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Definitions</span>
                <strong>{reportingSummary?.definitions ?? 0}</strong>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Insight
                <input value={insightForm.title} onChange={(event) => setInsightForm({ ...insightForm, title: event.target.value })} />
              </label>
              <label>
                Severity
                <select value={insightForm.severity} onChange={(event) => setInsightForm({ ...insightForm, severity: event.target.value as InsightSeverity })}>
                  <option value="info">Info</option>
                  <option value="watch">Watch</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                </select>
              </label>
              <label>
                Confidence
                <input type="number" min="0" max="1" step="0.01" value={insightForm.confidence} onChange={(event) => setInsightForm({ ...insightForm, confidence: Number(event.target.value) })} />
              </label>
              <label>
                Risk score
                <input type="number" min="0" max="100" value={riskForm.score} onChange={(event) => setRiskForm({ ...riskForm, score: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Evidence
                <input value={insightForm.evidence} onChange={(event) => setInsightForm({ ...insightForm, evidence: event.target.value })} />
              </label>
              <label className="wide-field">
                Recommendation
                <input value={riskForm.recommendation} onChange={(event) => setRiskForm({ ...riskForm, recommendation: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {insights.slice(0, 3).map((insight) => (
                <button
                  type="button"
                  key={insight.id}
                  className={`task-card ${insight.id === selectedInsightId ? "selected" : ""}`}
                  onClick={() => setSelectedInsightId(insight.id)}
                >
                  <div>
                    <strong>{insight.title}</strong>
                    <span>{insight.severity} · {insight.status} · {Math.round(insight.confidence * 100)}%</span>
                  </div>
                </button>
              ))}
              {riskScores.slice(0, 3).map((risk) => (
                <article key={risk.id} className="task-card">
                  <div>
                    <strong>{risk.score} · {risk.risk_band}</strong>
                    <span>{risk.model_name} · {risk.recommendation}</span>
                  </div>
                </article>
              ))}
              {reportingBenchmarks.slice(0, 3).map((benchmark) => (
                <article key={benchmark.model_name} className="task-card">
                  <div>
                    <strong>{benchmark.model_name} · {benchmark.average_score}</strong>
                    <span>{benchmark.sample_size} samples · {benchmark.high_risk_count} high risk · {benchmark.recommendation}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid" id="billing">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">SaaS billing</p>
                <h2>Plans and subscriptions</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createBillingPlanAndSubscription} disabled={busyAction !== null}>Subscribe</button>
                <button type="button" onClick={quoteBillingTax} disabled={busyAction !== null}>Tax</button>
                <button type="button" onClick={deliverBillingTaxFiling} disabled={busyAction !== null}>File Tax</button>
                <button type="button" onClick={quoteBillingProration} disabled={busyAction !== null}>Prorate</button>
                <button type="button" onClick={applyBillingPlanChange} disabled={busyAction !== null}>Apply</button>
                <button type="button" onClick={createBillingEntitlement} disabled={busyAction !== null}>Entitle</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{billingSummary?.monthly_recurring_revenue ?? "0.00"}</strong>
              <span>MRR</span>
              <small>{billingSummary ? `${billingSummary.active_subscriptions} active · ${billingSummary.entitlements} entitlements` : "No billing summary"}</small>
            </div>
            <div className="form-grid">
              <label>
                Plan
                <input value={billingForm.plan_name} onChange={(event) => setBillingForm({ ...billingForm, plan_name: event.target.value })} />
              </label>
              <label>
                Cycle
                <select value={billingForm.billing_cycle} onChange={(event) => setBillingForm({ ...billingForm, billing_cycle: event.target.value as BillingCycle })}>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="annual">Annual</option>
                </select>
              </label>
              <label>
                Base price
                <input type="number" min="0" value={billingForm.base_price} onChange={(event) => setBillingForm({ ...billingForm, base_price: Number(event.target.value) })} />
              </label>
              <label>
                Negotiated
                <input type="number" min="0" value={billingForm.negotiated_price} onChange={(event) => setBillingForm({ ...billingForm, negotiated_price: Number(event.target.value) })} />
              </label>
              <label>
                Tax country
                <input value={billingForm.tax_jurisdiction} onChange={(event) => setBillingForm({ ...billingForm, tax_jurisdiction: event.target.value.toUpperCase() })} />
              </label>
              <label>
                New price
                <input type="number" min="0" value={billingForm.prorated_price} onChange={(event) => setBillingForm({ ...billingForm, prorated_price: Number(event.target.value) })} />
              </label>
              <label>
                Athletes
                <input type="number" min="0" value={billingForm.included_athletes} onChange={(event) => setBillingForm({ ...billingForm, included_athletes: Number(event.target.value) })} />
              </label>
              <label>
                Agent tasks
                <input type="number" min="0" value={billingForm.included_agent_tasks} onChange={(event) => setBillingForm({ ...billingForm, included_agent_tasks: Number(event.target.value) })} />
              </label>
              <label>
                Period start
                <input type="date" value={billingForm.period_start} onChange={(event) => setBillingForm({ ...billingForm, period_start: event.target.value })} />
              </label>
              <label>
                Period end
                <input type="date" value={billingForm.period_end} onChange={(event) => setBillingForm({ ...billingForm, period_end: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {billingTaxQuote ? (
                <article className="task-card">
                  <div>
                    <strong>{billingTaxQuote.jurisdiction} tax · {billingTaxQuote.tax_amount}</strong>
                    <span>{billingTaxQuote.tax_rate}% · total {billingTaxQuote.total} · {billingTaxQuote.filing_hint}</span>
                  </div>
                </article>
              ) : null}
              {billingTaxFiling ? (
                <article className="task-card">
                  <div>
                    <strong>{billingTaxFiling.jurisdiction} filing · {billingTaxFiling.tax_amount}</strong>
                    <span>{billingTaxFiling.invoice_count} invoices · {billingTaxFiling.delivery_mode} · {billingTaxFiling.delivered ? "delivered" : billingTaxFiling.failure_reason ?? "prepared"}</span>
                  </div>
                </article>
              ) : null}
              {billingProration ? (
                <article className="task-card">
                  <div>
                    <strong>Proration net {billingProration.net_amount}</strong>
                    <span>{billingProration.remaining_days}/{billingProration.total_days} days · {billingProration.recommendation}</span>
                  </div>
                </article>
              ) : null}
              {billingPlanChange ? (
                <article className="task-card">
                  <div>
                    <strong>Plan change · {billingPlanChange.subscription_status}</strong>
                    <span>{billingPlanChange.previous_price} to {billingPlanChange.applied_price} · net {billingPlanChange.net_amount}</span>
                  </div>
                </article>
              ) : null}
              {subscriptions.slice(0, 3).map((subscription) => (
                <button
                  type="button"
                  key={subscription.id}
                  className={`task-card ${subscription.id === selectedSubscriptionId ? "selected" : ""}`}
                  onClick={() => setSelectedSubscriptionId(subscription.id)}
                >
                  <div>
                    <strong>{subscription.status} · {subscription.billing_cycle}</strong>
                    <span>{subscription.current_period_start} to {subscription.current_period_end}</span>
                  </div>
                </button>
              ))}
              {billingEntitlements.slice(0, 3).map((entitlement) => (
                <article key={entitlement.id} className="task-card">
                  <div>
                    <strong>{entitlement.feature_key}</strong>
                    <span>{entitlement.used_value}/{entitlement.limit_value ?? "unlimited"} · {entitlement.status}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Usage and invoices</p>
                <h2>Metering and collection</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createUsageMeterAndRecord} disabled={busyAction !== null}>Usage</button>
                <button type="button" onClick={createSaaSInvoiceAndPayment} disabled={busyAction !== null}>Invoice</button>
                <button type="button" onClick={prepareDunningNotice} disabled={busyAction !== null}>Dunning</button>
                <button type="button" onClick={deliverBillingDunningNotice} disabled={busyAction !== null}>Deliver</button>
                <button type="button" onClick={ingestBillingWebhook} disabled={busyAction !== null}>Webhook</button>
              </div>
            </div>
            <div className="consent-grid">
              <div>
                <span className="muted">Meters</span>
                <strong>{billingSummary?.usage_meters ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Usage</span>
                <strong>{billingSummary?.usage_records ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Open invoices</span>
                <strong>{billingSummary?.open_invoices ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Outstanding</span>
                <strong>{billingSummary?.invoice_outstanding ?? "0.00"}</strong>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Meter
                <input value={billingForm.meter_name} onChange={(event) => setBillingForm({ ...billingForm, meter_name: event.target.value })} />
              </label>
              <label>
                Unit
                <select value={billingForm.usage_unit} onChange={(event) => setBillingForm({ ...billingForm, usage_unit: event.target.value as UsageUnit })}>
                  <option value="athlete">Athlete</option>
                  <option value="team">Team</option>
                  <option value="agent_task">Agent task</option>
                  <option value="report">Report</option>
                  <option value="storage_gb">Storage GB</option>
                  <option value="message">Message</option>
                </select>
              </label>
              <label>
                Included
                <input type="number" min="0" value={billingForm.included_quantity} onChange={(event) => setBillingForm({ ...billingForm, included_quantity: Number(event.target.value) })} />
              </label>
              <label>
                Used
                <input type="number" min="0" value={billingForm.usage_quantity} onChange={(event) => setBillingForm({ ...billingForm, usage_quantity: Number(event.target.value) })} />
              </label>
              <label>
                Invoice
                <input value={billingForm.invoice_number} onChange={(event) => setBillingForm({ ...billingForm, invoice_number: event.target.value })} />
              </label>
              <label>
                Discount
                <input type="number" min="0" value={billingForm.discount_amount} onChange={(event) => setBillingForm({ ...billingForm, discount_amount: Number(event.target.value) })} />
              </label>
              <label>
                Payment
                <input type="number" min="0" value={billingForm.payment_amount} onChange={(event) => setBillingForm({ ...billingForm, payment_amount: Number(event.target.value) })} />
              </label>
              <label>
                Provider
                <input value={billingForm.webhook_provider} onChange={(event) => setBillingForm({ ...billingForm, webhook_provider: event.target.value })} />
              </label>
              <label>
                Entitlement
                <input value={billingForm.entitlement_feature} onChange={(event) => setBillingForm({ ...billingForm, entitlement_feature: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {billingDunning ? (
                <article className="task-card">
                  <div>
                    <strong>{billingDunning.severity} · {billingDunning.amount_due}</strong>
                    <span>{billingDunning.days_overdue} days overdue · {billingDunning.next_action}</span>
                  </div>
                </article>
              ) : null}
              {billingDunningDelivery ? (
                <article className="task-card">
                  <div>
                    <strong>{billingDunningDelivery.delivery_mode} delivery · {billingDunningDelivery.delivered ? "delivered" : "pending"}</strong>
                    <span>
                      {billingDunningDelivery.destination ?? "No external destination"} · {billingDunningDelivery.failure_reason ?? `status ${billingDunningDelivery.provider_status_code ?? "recorded"}`}
                    </span>
                  </div>
                </article>
              ) : null}
              {billingWebhook ? (
                <article className="task-card">
                  <div>
                    <strong>{billingWebhook.provider} webhook · {billingWebhook.invoice_status}</strong>
                    <span>
                      {billingWebhook.amount_paid} paid · {billingWebhook.message} · signature {billingWebhook.signature_validated ? "validated" : billingWebhook.signature_required ? "required" : "not configured"}
                    </span>
                  </div>
                </article>
              ) : null}
              {saasInvoices.slice(0, 3).map((invoice) => (
                <button
                  type="button"
                  key={invoice.id}
                  className={`task-card ${invoice.id === selectedSaasInvoiceId ? "selected" : ""}`}
                  onClick={() => setSelectedSaasInvoiceId(invoice.id)}
                >
                  <div>
                    <strong>{invoice.invoice_number}</strong>
                    <span>{invoice.amount_paid}/{invoice.total} · {invoice.status}</span>
                  </div>
                </button>
              ))}
              {usageRecords.slice(0, 3).map((record) => (
                <article key={record.id} className="task-card">
                  <div>
                    <strong>{record.quantity} units</strong>
                    <span>{record.source} · {new Date(record.recorded_at).toLocaleString()}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid" id="competition">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Competition</p>
                <h2>League and tournament control</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createCompetition} disabled={busyAction !== null}>Create</button>
                <button type="button" onClick={registerCompetitionTeam} disabled={busyAction !== null}>Register team</button>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Competition
                <input value={competitionForm.name} onChange={(event) => setCompetitionForm({ ...competitionForm, name: event.target.value })} />
              </label>
              <label>
                Type
                <select value={competitionForm.competition_type} onChange={(event) => setCompetitionForm({ ...competitionForm, competition_type: event.target.value as CompetitionType })}>
                  <option value="league">League</option>
                  <option value="tournament">Tournament</option>
                  <option value="cup">Cup</option>
                  <option value="friendly_series">Friendly series</option>
                </select>
              </label>
              <label>
                Format
                <select value={competitionForm.format} onChange={(event) => setCompetitionForm({ ...competitionForm, format: event.target.value as CompetitionFormat })}>
                  <option value="round_robin">Round robin</option>
                  <option value="single_elimination">Single elimination</option>
                  <option value="double_elimination">Double elimination</option>
                  <option value="group_knockout">Group + knockout</option>
                  <option value="swiss">Swiss</option>
                  <option value="friendly">Friendly</option>
                </select>
              </label>
              <label>
                Sport
                <input value={competitionForm.sport} onChange={(event) => setCompetitionForm({ ...competitionForm, sport: event.target.value })} />
              </label>
              <label>
                Starts
                <input type="date" value={competitionForm.starts_on} onChange={(event) => setCompetitionForm({ ...competitionForm, starts_on: event.target.value })} />
              </label>
              <label>
                Ends
                <input type="date" value={competitionForm.ends_on} onChange={(event) => setCompetitionForm({ ...competitionForm, ends_on: event.target.value })} />
              </label>
              <label className="wide-field">
                Tiebreakers
                <input value={competitionForm.tiebreakers} onChange={(event) => setCompetitionForm({ ...competitionForm, tiebreakers: event.target.value })} />
              </label>
            </div>
            <div className="selection-list compact">
              {competitions.map((competition) => (
                <button
                  type="button"
                  key={competition.id}
                  className={competition.id === selectedCompetitionId ? "selected" : ""}
                  onClick={() => setSelectedCompetitionId(competition.id)}
                >
                  <span>{competition.name}</span>
                  <small>{competition.competition_type} · {competition.format} · {competition.status}</small>
                </button>
              ))}
            </div>
            <div className="task-list">
              {competitionParticipants.map((participant) => (
                <article key={participant.id} className="task-card">
                  <div>
                    <strong>{participant.team_name}</strong>
                    <span>Seed {participant.seed ?? "—"} · Group {participant.group_label ?? "—"}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Fixtures</p>
                <h2>Match day and standings</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createCompetitionFixture} disabled={busyAction !== null}>Fixture</button>
                <button type="button" onClick={generateCompetitionFixtures} disabled={busyAction !== null}>Auto fixtures</button>
                <button type="button" onClick={advanceCompetitionRound} disabled={busyAction !== null}>Advance</button>
                <button type="button" onClick={optimizeCompetitionSchedule} disabled={busyAction !== null}>Optimize</button>
                <button type="button" onClick={recordFixtureResult} disabled={busyAction !== null}>Result</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{competitionStandings[0]?.points ?? 0}</strong>
              <span>{competitionStandings[0]?.team_name ?? "No leader"}</span>
              <small>{selectedCompetition?.name ?? "No competition selected"}</small>
            </div>
            <div className="form-grid">
              <label>
                Round
                <input value={fixtureForm.round_label} onChange={(event) => setFixtureForm({ ...fixtureForm, round_label: event.target.value })} />
              </label>
              <label>
                Stage
                <input value={fixtureForm.stage_label} onChange={(event) => setFixtureForm({ ...fixtureForm, stage_label: event.target.value })} />
              </label>
              <label>
                Kick-off
                <input type="datetime-local" value={fixtureForm.scheduled_at} onChange={(event) => setFixtureForm({ ...fixtureForm, scheduled_at: event.target.value })} />
              </label>
              <label>
                Venue
                <input value={fixtureForm.venue_name} onChange={(event) => setFixtureForm({ ...fixtureForm, venue_name: event.target.value })} />
              </label>
              <label>
                Home score
                <input type="number" min="0" value={fixtureForm.home_score} onChange={(event) => setFixtureForm({ ...fixtureForm, home_score: Number(event.target.value) })} />
              </label>
              <label>
                Away score
                <input type="number" min="0" value={fixtureForm.away_score} onChange={(event) => setFixtureForm({ ...fixtureForm, away_score: Number(event.target.value) })} />
              </label>
            </div>
            <div className="selection-list compact">
              {fixtureGeneration ? (
                <article className="task-card">
                  <div>
                    <strong>{fixtureGeneration.created} generated · {fixtureGeneration.rounds} rounds</strong>
                    <span>{fixtureGeneration.existing} existing fixtures skipped by the planner.</span>
                  </div>
                </article>
              ) : null}
              {competitionAdvancement ? (
                <article className="task-card">
                  <div>
                    <strong>{competitionAdvancement.created} advanced · {competitionAdvancement.next_round_label}</strong>
                    <span>{competitionAdvancement.winners.join(", ")}{competitionAdvancement.byes.length ? ` · byes: ${competitionAdvancement.byes.join(", ")}` : ""}</span>
                  </div>
                </article>
              ) : null}
              {scheduleOptimization ? (
                <article className="task-card">
                  <div>
                    <strong>{scheduleOptimization.moved} moved · {scheduleOptimization.protected_finals} finals protected</strong>
                    <span>{scheduleOptimization.team_rest_minutes} min rest · {scheduleOptimization.unchanged} unchanged</span>
                  </div>
                </article>
              ) : null}
              {competitionFixtures.map((fixture) => (
                <button
                  type="button"
                  key={fixture.id}
                  className={fixture.id === selectedFixtureId ? "selected" : ""}
                  onClick={() => setSelectedFixtureId(fixture.id)}
                >
                  <span>{fixture.home_team_name} vs {fixture.away_team_name}</span>
                  <small>{fixture.status} · {fixture.home_score ?? "—"}-{fixture.away_score ?? "—"} · {new Date(fixture.scheduled_at).toLocaleString()}</small>
                </button>
              ))}
            </div>
            <div className="standings-table">
              {competitionStandings.map((row) => (
                <div key={row.team_id} className="attendance-row">
                  <span>{row.team_name}</span>
                  <strong>{row.points} pts</strong>
                  <small>{row.played}P {row.wins}W {row.draws}D {row.losses}L GD {row.goal_difference}</small>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Officials</p>
                <h2>Assignments and live log</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={assignFixtureOfficial} disabled={busyAction !== null}>Assign</button>
                <button type="button" onClick={recordFixtureEvent} disabled={busyAction !== null}>Log event</button>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Official
                <input value={officialForm.display_name} onChange={(event) => setOfficialForm({ ...officialForm, display_name: event.target.value })} />
              </label>
              <label>
                Email
                <input value={officialForm.email} onChange={(event) => setOfficialForm({ ...officialForm, email: event.target.value })} />
              </label>
              <label>
                Role
                <select value={officialForm.role} onChange={(event) => setOfficialForm({ ...officialForm, role: event.target.value as OfficialRole })}>
                  <option value="referee">Referee</option>
                  <option value="assistant_referee">Assistant referee</option>
                  <option value="fourth_official">Fourth official</option>
                  <option value="scorer">Scorer</option>
                  <option value="timekeeper">Timekeeper</option>
                  <option value="match_commissioner">Match commissioner</option>
                </select>
              </label>
              <label>
                Certification
                <input value={officialForm.certification_level} onChange={(event) => setOfficialForm({ ...officialForm, certification_level: event.target.value })} />
              </label>
              <label>
                Minute
                <input type="number" min="0" max="200" value={fixtureForm.event_minute} onChange={(event) => setFixtureForm({ ...fixtureForm, event_minute: Number(event.target.value) })} />
              </label>
              <label>
                Event
                <select value={fixtureForm.event_type} onChange={(event) => setFixtureForm({ ...fixtureForm, event_type: event.target.value as MatchEventType })}>
                  <option value="goal">Goal</option>
                  <option value="own_goal">Own goal</option>
                  <option value="assist">Assist</option>
                  <option value="yellow_card">Yellow card</option>
                  <option value="red_card">Red card</option>
                  <option value="substitution">Substitution</option>
                  <option value="injury">Injury</option>
                  <option value="note">Note</option>
                </select>
              </label>
              <label className="wide-field">
                Event note
                <input value={fixtureForm.event_description} onChange={(event) => setFixtureForm({ ...fixtureForm, event_description: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {officialAssignments.map((assignment) => (
                <article key={assignment.id} className="task-card">
                  <div>
                    <strong>{assignment.role}</strong>
                    <span>{assignment.status} · {assignment.certification_level ?? "Uncertified"}</span>
                  </div>
                </article>
              ))}
              {matchEvents.slice(0, 4).map((matchEvent) => (
                <article key={matchEvent.id} className="task-card">
                  <div>
                    <strong>{matchEvent.minute ?? 0}' {matchEvent.event_type}</strong>
                    <span>{matchEvent.description ?? "Match event recorded"}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Competition readiness</p>
                <h2>Operational checks</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={reviewCompetitionConflicts} disabled={busyAction !== null}>Conflicts</button>
                <button type="button" onClick={broadcastCompetitionUpdate} disabled={busyAction !== null}>Broadcast</button>
                <button type="button" onClick={openCompetitionTicketing} disabled={busyAction !== null}>Ticketing</button>
              </div>
            </div>
            <div className="consent-grid">
              <div>
                <span className="muted">Participants</span>
                <strong>{competitionParticipants.length}</strong>
              </div>
              <div>
                <span className="muted">Fixtures</span>
                <strong>{competitionFixtures.length}</strong>
              </div>
              <div>
                <span className="muted">Results</span>
                <strong>{competitionFixtures.filter((fixture) => fixture.status === "final").length}</strong>
              </div>
              <div>
                <span className="muted">Officials</span>
                <strong>{officialAssignments.length}</strong>
              </div>
              <div>
                <span className="muted">Conflicts</span>
                <strong>{competitionConflicts.length}</strong>
              </div>
              <div>
                <span className="muted">Ticketed</span>
                <strong>{competitionTicketing.length}</strong>
              </div>
            </div>
            <div className="task-list">
              {competitionBracket ? (
                <div className="bracket-lanes">
                  {competitionBracket.rounds.map((round) => (
                    <CompetitionBracketLane
                      key={`${round.stage_label}-${round.round_label}`}
                      round={round}
                    />
                  ))}
                </div>
              ) : null}
              {competitionConflicts.slice(0, 3).map((conflict) => (
                <article key={`${conflict.conflict_key}-${conflict.fixture_id ?? "competition"}`} className="task-card">
                  <div>
                    <strong>{conflict.severity} · {conflict.title}</strong>
                    <span>{conflict.description} · {conflict.recommendation}</span>
                  </div>
                </article>
              ))}
              {competitionBroadcast ? (
                <article className="task-card">
                  <div>
                    <strong>{competitionBroadcast.channel} broadcast · {competitionBroadcast.delivered} delivered</strong>
                    <span>{competitionBroadcast.recipient_count} recipients · {competitionBroadcast.queued} queued · {competitionBroadcast.suppressed} suppressed</span>
                  </div>
                </article>
              ) : null}
              {competitionTicketing.slice(0, 3).map((ticketing) => (
                <article key={ticketing.ticket_product_id} className="task-card">
                  <div>
                    <strong>{ticketing.name} · {ticketing.sold_count}/{ticketing.capacity} sold</strong>
                    <span>{ticketing.currency} {ticketing.price} · {ticketing.venue_name ?? ticketing.access_zone ?? "No venue"} · {new Date(ticketing.scheduled_at).toLocaleString()}</span>
                  </div>
                </article>
              ))}
              <article className="task-card">
                <div>
                  <strong>Fixture integrity</strong>
                  <span>Teams must be registered participants before matches can be scheduled.</span>
                </div>
              </article>
              <article className="task-card">
                <div>
                  <strong>Table updates</strong>
                  <span>Confirmed final scores immediately recalculate points and goal difference.</span>
                </div>
              </article>
            </div>
          </div>
        </section>

        <section className="work-grid" id="communications">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Communications</p>
                <h2>Templates and broadcast</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createCommunicationTemplate} disabled={busyAction !== null}>Template</button>
                <button type="button" onClick={draftCommunicationMessage} disabled={busyAction !== null}>Draft</button>
                <button type="button" onClick={sendCommunicationMessage} disabled={busyAction !== null}>Send</button>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Template
                <input value={templateForm.name} onChange={(event) => setTemplateForm({ ...templateForm, name: event.target.value })} />
              </label>
              <label>
                Message type
                <select value={templateForm.message_type} onChange={(event) => setTemplateForm({ ...templateForm, message_type: event.target.value as CommunicationMessageType })}>
                  <option value="announcement">Announcement</option>
                  <option value="alert">Alert</option>
                  <option value="reminder">Reminder</option>
                  <option value="request">Request</option>
                  <option value="report">Report</option>
                </select>
              </label>
              <label>
                Channel
                <select value={templateForm.channel} onChange={(event) => {
                  const channel = event.target.value as CommunicationChannel;
                  setTemplateForm({ ...templateForm, channel });
                  setMessageForm({ ...messageForm, channel });
                }}>
                  <option value="in_app">In-app</option>
                  <option value="push">Push</option>
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                </select>
              </label>
              <label>
                Scope
                <select value={messageForm.scope_type} onChange={(event) => setMessageForm({ ...messageForm, scope_type: event.target.value as CommunicationScopeType })}>
                  <option value="organization">Organization</option>
                  <option value="team">Team</option>
                  <option value="event">Event</option>
                  <option value="person">Selected athlete</option>
                </select>
              </label>
              <label className="wide-field">
                Subject
                <input value={messageForm.subject} onChange={(event) => setMessageForm({ ...messageForm, subject: event.target.value })} />
              </label>
              <label className="wide-field">
                Body
                <textarea value={messageForm.body} onChange={(event) => setMessageForm({ ...messageForm, body: event.target.value })} />
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={messageForm.urgent} onChange={(event) => setMessageForm({ ...messageForm, urgent: event.target.checked })} />
                Urgent
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={messageForm.quiet_hours_override} onChange={(event) => setMessageForm({ ...messageForm, quiet_hours_override: event.target.checked })} />
                Override quiet hours
              </label>
            </div>
            {draftPreview ? (
              <div className="score-summary">
                <strong>AI</strong>
                <span>{draftPreview.subject}</span>
                <small>{draftPreview.model_name} · review required</small>
              </div>
            ) : null}
            <div className="selection-list compact">
              {communicationMessages.map((message) => (
                <button
                  type="button"
                  key={message.id}
                  className={message.id === selectedMessageId ? "selected" : ""}
                  onClick={() => setSelectedMessageId(message.id)}
                >
                  <span>{message.subject}</span>
                  <small>{message.message_type} · {message.channel} · {message.recipient_count} recipients</small>
                </button>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Delivery</p>
                <h2>Read receipts and preferences</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createCommunicationDigest} disabled={busyAction !== null || !selectedInboxPersonId}>Digest</button>
                <button type="button" onClick={runCommunicationDigestScheduler} disabled={busyAction !== null || !selectedOrganizationId}>Run digests</button>
                <button type="button" onClick={dispatchSelectedMessage} disabled={busyAction !== null || !selectedMessageId}>Dispatch</button>
                <button type="button" onClick={saveNotificationPreference} disabled={busyAction !== null}>Preference</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{inboxItems.length}</strong>
              <span>{selectedMessage?.subject ?? "No message selected"}</span>
              <small>{messageRecipients.length} recipients · {notificationPreference?.frequency ?? "no preference"}</small>
            </div>
            <div className="form-grid">
              <label>
                Frequency
                <select value={preferenceForm.frequency} onChange={(event) => setPreferenceForm({ ...preferenceForm, frequency: event.target.value as NotificationFrequency })}>
                  <option value="immediate">Immediate</option>
                  <option value="daily_digest">Daily digest</option>
                  <option value="weekly_digest">Weekly digest</option>
                </select>
              </label>
              <label>
                Channel preference
                <select value={preferenceForm.channel_preference} onChange={(event) => setPreferenceForm({ ...preferenceForm, channel_preference: event.target.value as ChannelPreference })}>
                  <option value="all">All</option>
                  <option value="app">App</option>
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                </select>
              </label>
              <label>
                Quiet start
                <input value={preferenceForm.quiet_hours_start} onChange={(event) => setPreferenceForm({ ...preferenceForm, quiet_hours_start: event.target.value })} />
              </label>
              <label>
                Quiet end
                <input value={preferenceForm.quiet_hours_end} onChange={(event) => setPreferenceForm({ ...preferenceForm, quiet_hours_end: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {digestRun ? (
                <article className="task-card">
                  <div>
                    <strong>Digest run</strong>
                    <span>{digestRun.created} created · {digestRun.skipped} skipped · {digestRun.considered} checked</span>
                  </div>
                </article>
              ) : null}
              {digestSummary ? (
                <article className="task-card">
                  <div>
                    <strong>{digestSummary.subject}</strong>
                    <span>{digestSummary.item_count} items · {digestSummary.channel}</span>
                  </div>
                </article>
              ) : null}
              {inboxItems.slice(0, 4).map((item) => (
                <article key={item.recipient_id} className="task-card">
                  <div>
                    <strong>{item.subject}</strong>
                    <span>{item.channel} · {item.delivery_status}{item.urgent ? " · urgent" : ""}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => updateRecipientStatus(item.recipient_id, "read")}>Read</button>
                  </div>
                </article>
              ))}
              {messageRecipients.map((recipient) => (
                <article key={recipient.id} className="task-card">
                  <div>
                    <strong>{recipient.person_name}</strong>
                    <span>{recipient.destination ?? "no destination"} · {recipient.delivery_status}</span>
                    {recipient.failure_reason ? <span>{recipient.failure_reason}</span> : null}
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => updateRecipientStatus(recipient.id, "delivered")}>Delivered</button>
                    <button type="button" onClick={() => updateRecipientStatus(recipient.id, "read")}>Read</button>
                  </div>
                </article>
              ))}
              {communicationTemplates.slice(0, 3).map((template) => (
                <article key={template.id} className="task-card">
                  <div>
                    <strong>{template.name}</strong>
                    <span>{template.message_type} · {template.channel}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid">
          <div className="panel form-panel" id="performance">
            <div className="panel-head">
              <div>
                <p className="section-label">Performance</p>
                <h2>Metric library and observations</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createMetricDefinition} disabled={busyAction !== null}>Metric</button>
                <button type="button" onClick={recordObservation} disabled={busyAction !== null}>Observe</button>
                <button type="button" onClick={ingestPerformanceEvidence} disabled={busyAction !== null}>Ingest</button>
                <button type="button" onClick={reviewSelectedObservation} disabled={busyAction !== null}>Review</button>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Code
                <input value={metricForm.code} onChange={(event) => setMetricForm({ ...metricForm, code: event.target.value })} />
              </label>
              <label>
                Metric
                <input value={metricForm.name} onChange={(event) => setMetricForm({ ...metricForm, name: event.target.value })} />
              </label>
              <label>
                Category
                <select value={metricForm.category} onChange={(event) => setMetricForm({ ...metricForm, category: event.target.value as MetricCategory })}>
                  <option value="physical">Physical</option>
                  <option value="technical">Technical</option>
                  <option value="tactical">Tactical</option>
                  <option value="mental">Mental</option>
                  <option value="wellness">Wellness</option>
                  <option value="competition">Competition</option>
                </select>
              </label>
              <label>
                Value
                <input type="number" value={observationForm.value} onChange={(event) => setObservationForm({ ...observationForm, value: Number(event.target.value) })} />
              </label>
              <label>
                Raw value
                <input value={observationForm.raw_value} onChange={(event) => setObservationForm({ ...observationForm, raw_value: event.target.value })} />
              </label>
              <label>
                Source
                <select value={observationForm.source} onChange={(event) => setObservationForm({ ...observationForm, source: event.target.value as MetricSource })}>
                  <option value="coach_evaluation">Coach evaluation</option>
                  <option value="manual">Manual</option>
                  <option value="self_assessment">Self assessment</option>
                  <option value="official_stats">Official stats</option>
                  <option value="video_analysis">Video analysis</option>
                  <option value="audio_narration">Audio narration</option>
                  <option value="wearable">Wearable</option>
                  <option value="agent_extracted">Agent extracted</option>
                </select>
              </label>
              <label className="wide-field">
                Evidence ref
                <input value={observationForm.evidence_ref} onChange={(event) => setObservationForm({ ...observationForm, evidence_ref: event.target.value })} />
              </label>
              <label className="wide-field">
                Evidence text
                <input value={observationForm.evidence_text} onChange={(event) => setObservationForm({ ...observationForm, evidence_text: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {performanceIngestion ? (
                <article className="task-card">
                  <div>
                    <strong>{performanceIngestion.extractor}</strong>
                    <span>{performanceIngestion.summary} · confidence {Math.round(performanceIngestion.confidence * 100)}%</span>
                  </div>
                </article>
              ) : null}
              {observations.slice(0, 4).map((observation) => (
                <button
                  type="button"
                  key={observation.id}
                  className={`task-card ${observation.id === selectedObservationId ? "selected" : ""}`}
                  onClick={() => setSelectedObservationId(observation.id)}
                >
                  <div>
                    <strong>{observation.source} · {observation.value}</strong>
                    <span>{observation.verification_status} · {observation.notes ?? "Observation recorded"}</span>
                  </div>
                </button>
              ))}
              {metricDefinitions.slice(0, 4).map((metric) => (
                <article key={metric.id} className="task-card">
                  <div>
                    <strong>{metric.name}</strong>
                    <span>{metric.category} · {metric.unit ?? "unitless"} · weight {metric.weight}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Assessment</p>
                <h2>AfroLete score</h2>
              </div>
              <button type="button" onClick={recordAssessment} disabled={busyAction !== null}>Record</button>
            </div>
            <div className="score-summary">
              <strong>{performanceSummary?.latest_overall_score ?? "—"}</strong>
              <span>{performanceSummary?.rating ?? "No assessment"}</span>
              <small>{performanceSummary?.observation_count ?? 0} observations · {performanceSummary?.assessment_count ?? 0} assessments</small>
            </div>
            <div className="form-grid">
              <label>
                Physical
                <input type="number" min="0" max="100" value={assessmentForm.physical_score} onChange={(event) => setAssessmentForm({ ...assessmentForm, physical_score: Number(event.target.value) })} />
              </label>
              <label>
                Technical
                <input type="number" min="0" max="100" value={assessmentForm.technical_score} onChange={(event) => setAssessmentForm({ ...assessmentForm, technical_score: Number(event.target.value) })} />
              </label>
              <label>
                Tactical
                <input type="number" min="0" max="100" value={assessmentForm.tactical_score} onChange={(event) => setAssessmentForm({ ...assessmentForm, tactical_score: Number(event.target.value) })} />
              </label>
              <label>
                Mental
                <input type="number" min="0" max="100" value={assessmentForm.mental_score} onChange={(event) => setAssessmentForm({ ...assessmentForm, mental_score: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Summary
                <input value={assessmentForm.summary} onChange={(event) => setAssessmentForm({ ...assessmentForm, summary: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {assessments.slice(0, 3).map((assessment) => (
                <article key={assessment.id} className="task-card">
                  <div>
                    <strong>ALS {assessment.overall_score}</strong>
                    <span>{assessment.summary ?? "Assessment recorded"}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid" id="training">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Training</p>
                <h2>Drill library and plan builder</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createTrainingDrill} disabled={busyAction !== null}>Drill</button>
                <button type="button" onClick={createTrainingPlan} disabled={busyAction !== null}>Plan</button>
                <button type="button" onClick={generateTrainingPlan} disabled={busyAction !== null}>AI Plan</button>
                <button type="button" onClick={addTrainingPlanItem} disabled={busyAction !== null}>Block</button>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Drill
                <input value={drillForm.name} onChange={(event) => setDrillForm({ ...drillForm, name: event.target.value })} />
              </label>
              <label>
                Focus
                <input value={drillForm.focus_area} onChange={(event) => setDrillForm({ ...drillForm, focus_area: event.target.value })} />
              </label>
              <label>
                Category
                <input value={drillForm.category} onChange={(event) => setDrillForm({ ...drillForm, category: event.target.value })} />
              </label>
              <label>
                Minutes
                <input type="number" min="1" max="240" value={drillForm.default_duration_minutes} onChange={(event) => setDrillForm({ ...drillForm, default_duration_minutes: Number(event.target.value) })} />
              </label>
              <label>
                Intensity
                <input type="number" min="1" max="10" value={drillForm.default_intensity} onChange={(event) => setDrillForm({ ...drillForm, default_intensity: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Coaching points
                <input value={drillForm.coaching_points} onChange={(event) => setDrillForm({ ...drillForm, coaching_points: event.target.value })} />
              </label>
              <label>
                Plan
                <input value={trainingPlanForm.title} onChange={(event) => setTrainingPlanForm({ ...trainingPlanForm, title: event.target.value })} />
              </label>
              <label>
                Plan focus
                <input value={trainingPlanForm.focus_area} onChange={(event) => setTrainingPlanForm({ ...trainingPlanForm, focus_area: event.target.value })} />
              </label>
              <label>
                Starts
                <input type="date" value={trainingPlanForm.period_start} onChange={(event) => setTrainingPlanForm({ ...trainingPlanForm, period_start: event.target.value })} />
              </label>
              <label>
                Ends
                <input type="date" value={trainingPlanForm.period_end} onChange={(event) => setTrainingPlanForm({ ...trainingPlanForm, period_end: event.target.value })} />
              </label>
              <label>
                Readiness
                <input type="number" min="0" max="100" value={trainingPlanForm.readiness_score} onChange={(event) => setTrainingPlanForm({ ...trainingPlanForm, readiness_score: Number(event.target.value) })} />
              </label>
              <label>
                Sessions
                <input type="number" min="1" max="7" value={trainingPlanForm.weekly_sessions} onChange={(event) => setTrainingPlanForm({ ...trainingPlanForm, weekly_sessions: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Load guidance
                <input value={trainingPlanForm.load_guidance} onChange={(event) => setTrainingPlanForm({ ...trainingPlanForm, load_guidance: event.target.value })} />
              </label>
            </div>
            <div className="selection-list compact">
              {trainingPlans.map((plan) => (
                <button
                  type="button"
                  key={plan.id}
                  className={plan.id === selectedTrainingPlanId ? "selected" : ""}
                  onClick={() => setSelectedTrainingPlanId(plan.id)}
                >
                  <span>{plan.title}</span>
                  <small>{plan.focus_area} · {plan.period_start} to {plan.period_end}</small>
                </button>
              ))}
            </div>
            <div className="task-list">
              {generatedTrainingPlan ? (
                <article className="task-card">
                  <div>
                    <strong>AI readiness {generatedTrainingPlan.readiness_score}</strong>
                    <span>{generatedTrainingPlan.load_balance} · {generatedTrainingPlan.rationale}</span>
                  </div>
                </article>
              ) : null}
              {trainingPlanItems.slice(0, 4).map((item) => (
                <article key={item.id} className="task-card">
                  <div>
                    <strong>{item.day_label}: {item.title}</strong>
                    <span>{item.focus_area} · {item.duration_minutes} min · RPE {item.intensity}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Load management</p>
                <h2>Session planner</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createTrainingSession} disabled={busyAction !== null}>Session</button>
                <button type="button" onClick={suggestTrainingAvailability} disabled={busyAction !== null}>Availability</button>
                <button type="button" onClick={recordTrainingFeedback} disabled={busyAction !== null}>Feedback</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{trainingFeedback[0]?.readiness_score ?? trainingSessionForm.duration_minutes * trainingSessionForm.rpe_target}</strong>
              <span>{trainingFeedback[0] ? `${trainingFeedback[0].readiness_band} readiness` : "Target load"}</span>
              <small>{selectedTrainingSession?.title ?? selectedTrainingPlan?.title ?? "No session selected"}</small>
            </div>
            <div className="form-grid">
              <label>
                Session
                <input value={trainingSessionForm.title} onChange={(event) => setTrainingSessionForm({ ...trainingSessionForm, title: event.target.value })} />
              </label>
              <label>
                Scheduled
                <input type="datetime-local" value={trainingSessionForm.scheduled_for} onChange={(event) => setTrainingSessionForm({ ...trainingSessionForm, scheduled_for: event.target.value })} />
              </label>
              <label>
                Minutes
                <input type="number" min="1" max="360" value={trainingSessionForm.duration_minutes} onChange={(event) => setTrainingSessionForm({ ...trainingSessionForm, duration_minutes: Number(event.target.value) })} />
              </label>
              <label>
                RPE
                <input type="number" min="1" max="10" value={trainingSessionForm.rpe_target} onChange={(event) => setTrainingSessionForm({ ...trainingSessionForm, rpe_target: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Objectives
                <input value={trainingSessionForm.objectives} onChange={(event) => setTrainingSessionForm({ ...trainingSessionForm, objectives: event.target.value })} />
              </label>
              <label>
                Readiness
                <input type="number" min="0" max="100" value={trainingFeedbackForm.readiness_score} onChange={(event) => setTrainingFeedbackForm({ ...trainingFeedbackForm, readiness_score: Number(event.target.value) })} />
              </label>
              <label>
                Soreness
                <input type="number" min="0" max="10" value={trainingFeedbackForm.soreness_score} onChange={(event) => setTrainingFeedbackForm({ ...trainingFeedbackForm, soreness_score: Number(event.target.value) })} />
              </label>
              <label>
                Sleep
                <input type="number" min="0" max="10" value={trainingFeedbackForm.sleep_quality} onChange={(event) => setTrainingFeedbackForm({ ...trainingFeedbackForm, sleep_quality: Number(event.target.value) })} />
              </label>
              <label>
                Actual RPE
                <input type="number" min="1" max="10" value={trainingFeedbackForm.actual_rpe} onChange={(event) => setTrainingFeedbackForm({ ...trainingFeedbackForm, actual_rpe: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Feedback
                <input value={trainingFeedbackForm.feedback} onChange={(event) => setTrainingFeedbackForm({ ...trainingFeedbackForm, feedback: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {trainingAvailability?.slots.slice(0, 3).map((slot) => (
                <article key={slot.starts_at} className="task-card">
                  <div>
                    <strong>Slot score {slot.score} · {new Date(slot.starts_at).toLocaleString()}</strong>
                    <span>{slot.recommendation}{slot.conflicts.length ? ` · ${slot.conflicts.join(", ")}` : ""}</span>
                  </div>
                </article>
              ))}
              {trainingSessions.slice(0, 4).map((sessionPlan) => (
                <article
                  key={sessionPlan.id}
                  className={`task-card ${sessionPlan.id === selectedTrainingSessionId ? "selected" : ""}`}
                  onClick={() => setSelectedTrainingSessionId(sessionPlan.id)}
                >
                  <div>
                    <strong>{sessionPlan.title}</strong>
                    <span>{sessionPlan.status} · {new Date(sessionPlan.scheduled_for).toLocaleString()} · load {sessionPlan.load_score}</span>
                  </div>
                </article>
              ))}
              {trainingFeedback.slice(0, 3).map((feedback) => (
                <article key={feedback.id} className="task-card">
                  <div>
                    <strong>{feedback.readiness_band} readiness · RPE {feedback.actual_rpe ?? "pending"}</strong>
                    <span>{feedback.recommendation}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid">
          <form className="panel form-panel" id="agents" onSubmit={createAgent}>
            <div className="panel-head">
              <div>
                <p className="section-label">Agents</p>
                <h2>Agent identity and scope</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Create</button>
            </div>
            <div className="form-grid">
              <label>
                Agent
                <input value={agentForm.name} onChange={(event) => setAgentForm({ ...agentForm, name: event.target.value })} />
              </label>
              <label>
                Kind
                <select value={agentForm.kind} onChange={(event) => setAgentForm({ ...agentForm, kind: event.target.value as AgentKind })}>
                  <option value="safeguarding">Safeguarding</option>
                  <option value="coaching">Coaching</option>
                  <option value="operations">Operations</option>
                  <option value="analytics">Analytics</option>
                  <option value="communications">Communications</option>
                  <option value="scouting">Scouting</option>
                </select>
              </label>
              <label>
                Model policy
                <input value={agentForm.model_policy} onChange={(event) => setAgentForm({ ...agentForm, model_policy: event.target.value })} />
              </label>
              <label>
                Purpose
                <textarea value={agentForm.purpose} onChange={(event) => setAgentForm({ ...agentForm, purpose: event.target.value })} />
              </label>
            </div>
            <div className="event-toolbar">
              <button type="button" onClick={() => assignAgent("organization")} disabled={busyAction !== null}>Assign org</button>
              <button type="button" onClick={() => assignAgent("team")} disabled={busyAction !== null}>Assign team</button>
              <button type="button" onClick={() => assignAgent("event")} disabled={busyAction !== null}>Assign event</button>
            </div>
            <div className="selection-list compact">
              {agents.map((agent) => (
                <button
                  type="button"
                  key={agent.id}
                  className={agent.id === selectedAgentId ? "selected" : ""}
                  onClick={() => setSelectedAgentId(agent.id)}
                >
                  <span>{agent.name}</span>
                  <small>{agent.kind} · {agent.model_policy ?? "default policy"}</small>
                </button>
              ))}
            </div>
          </form>

          <form className="panel form-panel" onSubmit={queueAgentTask}>
            <div className="panel-head">
              <div>
                <p className="section-label">Task inbox</p>
                <h2>Human-reviewed agent work</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={refreshAgentTelemetry} disabled={busyAction !== null}>Telemetry</button>
                <button type="submit" disabled={busyAction !== null}>Queue</button>
              </div>
            </div>
            <div className="consent-grid">
              <div>
                <span className="muted">Queued</span>
                <strong>{agentGovernance?.queued_tasks ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Review</span>
                <strong>{agentGovernance?.waiting_for_review ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Failed</span>
                <strong>{agentGovernance?.failed_tasks ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Boundary</span>
                <strong>{agentGovernance?.credential_status.credential_boundary ?? "local"}</strong>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Task type
                <input value={taskForm.task_type} onChange={(event) => setTaskForm({ ...taskForm, task_type: event.target.value })} />
              </label>
              <label>
                Input
                <input value={taskForm.input_ref} onChange={(event) => setTaskForm({ ...taskForm, input_ref: event.target.value })} />
              </label>
              <label className="wide-field">
                Title
                <input value={taskForm.title} onChange={(event) => setTaskForm({ ...taskForm, title: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {agentGovernance ? (
                <article className="task-card">
                  <div>
                    <strong>{agentGovernance.credential_status.execution_mode} · {agentGovernance.credential_status.default_model}</strong>
                    <span>{agentGovernance.credential_status.recommendation}</span>
                  </div>
                </article>
              ) : null}
              {agentRuns.slice(0, 3).map((run) => (
                <article key={run.task_id} className="task-card">
                  <div>
                    <strong>{run.agent_name} · {run.status}</strong>
                    <span>{run.model_policy} · {run.governance_notes}</span>
                  </div>
                </article>
              ))}
              {agentTasks.map((task) => (
                <article key={task.id} className="task-card">
                  <div>
                    <strong>{task.title}</strong>
                    <span>{task.task_type} · {task.status}</span>
                    {task.output_ref ? <span>{task.output_ref}</span> : null}
                    {task.review_notes ? <span>{task.review_notes}</span> : null}
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => executeAgentTask(task.id)}>Run</button>
                    <button type="button" onClick={() => updateAgentTask(task.id, "waiting_for_review")}>Review</button>
                    <button type="button" onClick={() => updateAgentTask(task.id, "completed")}>Done</button>
                  </div>
                </article>
              ))}
            </div>
          </form>
        </section>

        <section className="panel safeguarding-panel" id="safeguarding">
          <div className="panel-head">
            <div>
              <p className="section-label">Safeguarding</p>
              <h2>Guardian consent and event clearance</h2>
            </div>
            <div className="event-toolbar">
              <button type="button" onClick={createGuardian} disabled={busyAction !== null}>Link guardian</button>
              <button type="button" onClick={requestConsent} disabled={busyAction !== null}>Request consent</button>
            </div>
          </div>
          <div className="form-grid three">
            <label>
              Guardian
              <input value={guardianForm.guardian_display_name} onChange={(event) => setGuardianForm({ ...guardianForm, guardian_display_name: event.target.value })} />
            </label>
            <label>
              Email
              <input value={guardianForm.guardian_email} onChange={(event) => setGuardianForm({ ...guardianForm, guardian_email: event.target.value })} />
            </label>
            <label>
              Phone
              <input value={guardianForm.guardian_phone} onChange={(event) => setGuardianForm({ ...guardianForm, guardian_phone: event.target.value })} />
            </label>
          </div>
          <div className="consent-grid">
            <div>
              <span className="muted">Athlete</span>
              <strong>{selectedAthlete?.name ?? "None selected"}</strong>
            </div>
            <div>
              <span className="muted">Event</span>
              <strong>{selectedEvent?.title ?? "None selected"}</strong>
            </div>
            <div>
              <span className="muted">Clearance</span>
              <strong>{clearance?.status ?? "Unchecked"}</strong>
            </div>
            <div>
              <span className="muted">Guardian link</span>
              {consentUrl ? <a href={consentUrl}>{consentUrl}</a> : <strong>Not issued</strong>}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
