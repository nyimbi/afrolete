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
import type { InfrastructureComponent, InfrastructureProbeSummary, InfrastructureStatus } from "@/types/platform";
import type {
  AgentAssignmentRead,
  AgentBiasAuditRead,
  AgentDecisionAppealRead,
  AgentEthicalScorecardRead,
  AgentGovernanceSummaryRead,
  AgentKind,
  AgentModelRegistryRead,
  AgentModelTransparencyReportRead,
  AgentRead,
  AgentRunLedgerVerificationRead,
  AgentRunRecordRead,
  AgentScorecardAutomationRunRead,
  AgentScorecardArtifactAnomalyAlertRead,
  AgentScorecardArtifactAnomalyAlertRunRead,
  AgentScorecardArtifactAccessRead,
  AgentScorecardArtifactAccessSummaryRead,
  AgentScorecardCommentModerationRead,
  AgentScorecardPublicationArtifactLinkRead,
  AgentScorecardPublicationArtifactRead,
  AgentScorecardPublicationRead,
  AgentScorecardPublicationReadinessRead,
  AgentScorecardPublicationReminderRead,
  AgentScorecardPublicationReminderRunRead,
  AgentTaskRead,
  AgentTaskStatus,
  AgentWorkerCallbackRead,
  AccountingExportRead,
  AccountingSyncRead,
  AssessmentReviewQueueSummaryRead,
  AssetCondition,
  AssetSummaryRead,
  AssetUtilizationRecommendationRead,
  AthleteAssessmentRead,
  AthleteAssessmentReviewQueueItemRead,
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
  CommunicationEscalationRunRead,
  CommunicationInboxItemRead,
  CommercialSummaryRead,
  CommercialTaxFilingRead,
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
  CommercialStatus,
  ConsentCaptureChannel,
  ConsentRequestRead,
  DonationRead,
  DeveloperApiKeyProvisionedRead,
  DeveloperApiKeyRead,
  DeveloperOAuthAuthorizationRead,
  DeveloperApplicationProvisionedRead,
  DeveloperApplicationRead,
  DeveloperIntegrationCatalogRead,
  DeveloperMarketplaceListingRead,
  DeveloperPortalSummaryRead,
  DeveloperWebhookDeliveryRead,
  DeveloperWebhookRetryRunRead,
  DeveloperWebhookSubscriptionProvisionedRead,
  DeveloperWebhookSubscriptionRead,
  EventRead,
  EventTravelApprovalRead,
  EventTravelApprovalRoutingRead,
  EventTravelBackupDriverDispatchRead,
  EventTravelBackupDriverRead,
  EventTravelCarpoolAutoMatchRead,
  EventTravelCarpoolRideRead,
  EventTravelChecklistEvidenceUploadRead,
  EventTravelChecklistItemRead,
  EventTravelConsentBatchRead,
  EventTravelConsentReminderRead,
  EventTravelConsentReminderRunRead,
  EventTravelDeviceRead,
  EventTravelDeviceSecretRead,
  EventTravelDeviceFleetInventoryRead,
  EventTravelDriverMarketplaceRead,
  EventTravelDriverRatingRead,
  EventTravelDriverRatingSummaryRead,
  EventTravelExpensePayoutCallbackRead,
  EventTravelExpensePayoutRead,
  EventTravelExpenseRead,
  EventTravelFeeCheckoutBatchRead,
  EventTravelFeeInvoiceBatchRead,
  EventTravelFeeReconciliationRead,
  EventTravelFeeReconciliationResolutionRead,
  EventTravelGeofenceCheckRead,
  EventTravelGeofenceZoneRead,
  EventTravelLocationUpdateRead,
  EventTravelMapRead,
  EventTravelTelemetryStreamRead,
  EventTravelManifestExportRead,
  EventTravelManifestRead,
  EventTravelManifestOfflineLinkRead,
  EventTravelPlanRead,
  EventTravelReadinessRead,
  EventTravelReceiptUploadRead,
  EventTravelRouteOptimizationRead,
  EventWeatherAlertRead,
  EventWeatherAutomationRunRead,
  EventWeatherAssessmentRead,
  EventType,
  EmergencyActivationAlertRead,
  EmergencyActionPlanRead,
  EmergencyActionPlanStatus,
  EmergencyPlanActivationRead,
  EmergencyActivationStatus,
  EmergencyType,
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
  BackgroundCheckRead,
  BackgroundCheckStatus,
  GuardianRelationshipRead,
  IncidentInsuranceClaimRead,
  IncidentMedicalClearanceRead,
  IncidentReportPackageRead,
  IncidentReportPackageStatus,
  InsightSeverity,
  InsightStatus,
  IntelligenceInsightRead,
  InsuranceClaimStatus,
  InsuranceClaimType,
  LocalIdentity,
  MatchEventType,
  MedicalClearanceStatus,
  MessageDeliveryStatus,
  MessageRecipientRead,
  MembershipRead,
  MetricCategory,
  MetricDefinitionRead,
  MetricVerificationStatus,
  MetricSource,
  OfficialRole,
  OrganizationRead,
  OrganizationType,
  ParticipationClearanceRead,
  PaymentSettlementRead,
  CommercialSettlementPayoutRead,
  CommercialSettlementPayoutCallbackRead,
  PerformanceAchievementAwardRead,
  PerformanceAchievementRunRead,
  PerformanceAssessmentReviewEscalationRunRead,
  PerformanceCohortComparisonRead,
  PerformanceForecastScenarioRead,
  PerformanceForecastValidationAlertRead,
  PerformanceForecastValidationRunRead,
  PerformanceForecastWhatIfRead,
  PerformanceGoalRead,
  PerformanceInjuryRiskAlertRead,
  PerformanceInjuryRiskAlertRunRead,
  PerformanceInjuryRiskRead,
  PerformanceIngestionRead,
  PerformanceMetricBenchmarkRead,
  PerformanceModelExtractionBenchmarkDatasetRead,
  PerformanceModelExtractionBenchmarkRunRead,
  PerformanceMetricTrendRead,
  PerformanceMetricTrendSeriesRead,
  PerformanceObservationRead,
  PerformanceWearableConnectionRead,
  PerformanceWearableOAuthCallbackRead,
  PerformanceWearableOAuthStartRead,
  PerformanceWearableSyncRunRead,
  PerformanceWearableTokenRefreshRead,
  PerformanceWearableWebhookRead,
  PerformanceWearableWebhookRegistrationRead,
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
  RegistrationInquiryConversionRead,
  RegistrationInquiryFollowUpRead,
  RegistrationInquiryRead,
  RenderedReportRead,
  ReportVerificationRead,
  ReportingBenchmarkRead,
  ReportingSummaryRead,
  SaaSInvoiceRead,
  SaaSPaymentRead,
  SafeguardingIncidentRead,
  SafeguardingIncidentSeverity,
  SafeguardingIncidentStatus,
  SafeguardingIncidentType,
  ComplianceCredentialRead,
  ComplianceCredentialStatus,
  ComplianceCredentialType,
  ComplianceReconciliationRead,
  ComplianceSummaryRead,
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
  TravelPlanStatus,
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

const performanceRiskAlertChannelOptions: CommunicationChannel[] = ["in_app", "push", "sms", "whatsapp"];
const metricCategoryOptions: MetricCategory[] = [
  "physical",
  "technical",
  "tactical",
  "mental",
  "wellness",
  "competition"
];

function wearableWebhookPayload(provider: string): Record<string, unknown> {
  if (provider === "garmin") {
    return {
      provider: "garmin",
      summaryType: "daily",
      calendarDate: "2026-06-05",
      wellnessData: {
        restingHeartRate: 92,
        averageStressLevel: 74,
        bodyBatteryMostRecentValue: 42
      }
    };
  }
  if (provider === "apple_health") {
    return {
      provider: "apple_health",
      samples: [
        { type: "HKQuantityTypeIdentifierHeartRateVariabilitySDNN", value: 38, unit: "ms", startDate: "2026-06-05T06:00:00Z" },
        { type: "HKQuantityTypeIdentifierRestingHeartRate", value: 91, unit: "count/min", startDate: "2026-06-05T06:00:00Z" }
      ]
    };
  }
  if (provider === "fitbit") {
    return {
      provider: "fitbit",
      summary: { restingHeartRate: 88 },
      sleep: { summary: { totalMinutesAsleep: 325, efficiency: 71 } },
      dateOfSleep: "2026-06-05"
    };
  }
  if (provider === "polar") {
    return {
      provider: "polar",
      date: "2026-06-05",
      heart_rate: { resting: 83, average: 144 },
      hrv: { rmssd: 46 },
      sleep: { duration_minutes: 411, score: 79 }
    };
  }
  if (provider === "oura") {
    return {
      provider: "oura",
      day: "2026-06-05",
      readiness: { score: 82, average_hrv: 48, resting_heart_rate: 58, temperature_deviation: 0.2 },
      sleep: { score: 86, total_sleep_duration: 25620 }
    };
  }
  if (["catapult", "statsports", "playertek"].includes(provider)) {
    return {
      provider,
      session_start: "2026-06-05T16:00:00Z",
      metrics: {
        player_load: 384,
        total_distance_m: 6820,
        max_velocity: 8.4,
        high_speed_distance: 721,
        accelerations: 43,
        decelerations: 38,
        average_heart_rate: 151
      }
    };
  }
  return {
    provider: "whoop",
    recovery: {
      score: 44,
      hrv_rmssd_milli: 33,
      resting_heart_rate: 99
    },
    strain: { score: 17.4 },
    created_at: "2026-06-05T06:15:00Z"
  };
}

type TravelManifestLegacyOfflineCache = EventTravelManifestRead & {
  cached_at: string;
  cache_version: number;
  expires_at?: string;
  encrypted?: false;
};

type TravelManifestEncryptedOfflineCache = {
  event_id: string;
  travel_plan_id: string;
  destination: string;
  participant_count: number;
  cached_at: string;
  expires_at: string;
  cache_version: 2;
  encrypted: true;
  encryption: "AES-GCM/PBKDF2-SHA-256";
  iv_base64: string;
  payload_base64: string;
  payload_sha256_base64: string;
};

type TravelManifestOfflineCache = TravelManifestEncryptedOfflineCache | TravelManifestLegacyOfflineCache;

const travelManifestCacheKey = (travelPlanId: string) => `afrolete:travel-manifest:${travelPlanId}`;
const travelManifestCacheTtlMs = 7 * 24 * 60 * 60 * 1000;
const travelManifestCacheSalt = "afrolete-travel-manifest-cache-v2";

const base64FromArrayBuffer = (buffer: ArrayBuffer | Uint8Array) => {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary);
};

const arrayBufferFromBase64 = (value: string) => {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes.buffer;
};

const getTravelManifestCacheCrypto = () => {
  if (typeof window === "undefined" || !window.crypto?.subtle) {
    throw new Error("Encrypted offline manifest cache requires browser Web Crypto support");
  }
  return window.crypto;
};

const deriveTravelManifestCacheKey = async (identity: LocalIdentity, travelPlanId: string) => {
  const webCrypto = getTravelManifestCacheCrypto();
  const encoder = new TextEncoder();
  const identityMaterial = [identity.sub, identity.email, identity.name, travelPlanId].join(":");
  const keyMaterial = await webCrypto.subtle.importKey(
    "raw",
    encoder.encode(identityMaterial),
    "PBKDF2",
    false,
    ["deriveKey"]
  );
  return webCrypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: encoder.encode(`${travelManifestCacheSalt}:${travelPlanId}`),
      iterations: 100_000,
      hash: "SHA-256"
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
};

const encryptTravelManifestOfflineCache = async (
  manifest: EventTravelManifestRead,
  identity: LocalIdentity
): Promise<TravelManifestEncryptedOfflineCache> => {
  const webCrypto = getTravelManifestCacheCrypto();
  const encoder = new TextEncoder();
  const cachedAt = new Date();
  const expiresAt = new Date(cachedAt.getTime() + travelManifestCacheTtlMs);
  const payload = encoder.encode(JSON.stringify(manifest));
  const iv = webCrypto.getRandomValues(new Uint8Array(12));
  const key = await deriveTravelManifestCacheKey(identity, manifest.travel_plan_id);
  const encryptedPayload = await webCrypto.subtle.encrypt({ name: "AES-GCM", iv }, key, payload);
  const payloadDigest = await webCrypto.subtle.digest("SHA-256", payload);

  return {
    event_id: manifest.event_id,
    travel_plan_id: manifest.travel_plan_id,
    destination: manifest.destination,
    participant_count: manifest.participant_count,
    cached_at: cachedAt.toISOString(),
    expires_at: expiresAt.toISOString(),
    cache_version: 2,
    encrypted: true,
    encryption: "AES-GCM/PBKDF2-SHA-256",
    iv_base64: base64FromArrayBuffer(iv),
    payload_base64: base64FromArrayBuffer(encryptedPayload),
    payload_sha256_base64: base64FromArrayBuffer(payloadDigest)
  };
};

const isTravelManifestEncryptedOfflineCache = (
  cache: TravelManifestOfflineCache
): cache is TravelManifestEncryptedOfflineCache => cache.encrypted === true;

const getTravelManifestOfflineCacheExpiry = (cache: TravelManifestOfflineCache) =>
  isTravelManifestEncryptedOfflineCache(cache)
    ? cache.expires_at
    : cache.expires_at ?? new Date(new Date(cache.cached_at).getTime() + travelManifestCacheTtlMs).toISOString();

const decryptTravelManifestOfflineCache = async (
  cache: TravelManifestEncryptedOfflineCache,
  identity: LocalIdentity
) => {
  const webCrypto = getTravelManifestCacheCrypto();
  const decoder = new TextDecoder();
  const key = await deriveTravelManifestCacheKey(identity, cache.travel_plan_id);
  const decryptedPayload = await webCrypto.subtle.decrypt(
    { name: "AES-GCM", iv: arrayBufferFromBase64(cache.iv_base64) },
    key,
    arrayBufferFromBase64(cache.payload_base64)
  );
  const payloadDigest = await webCrypto.subtle.digest("SHA-256", decryptedPayload);
  if (base64FromArrayBuffer(payloadDigest) !== cache.payload_sha256_base64) {
    throw new Error("Offline manifest cache checksum did not match");
  }
  return JSON.parse(decoder.decode(decryptedPayload)) as EventTravelManifestRead;
};

const parseGeofencePolygon = (value: string) => {
  const points = value
    .split(";")
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((entry) => {
      const [latitude, longitude] = entry.split(",").map((part) => Number(part.trim()));
      return Number.isFinite(latitude) && Number.isFinite(longitude)
        ? { latitude: String(latitude), longitude: String(longitude) }
        : null;
    })
    .filter((point): point is { latitude: string; longitude: string } => point !== null);
  return points.length >= 3 ? points : null;
};

const parseCommaList = (value: string) =>
  value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);

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

type InquiryReviewForm = {
  status: string;
  review_notes: string;
  follow_up_at: string;
};

type AssessmentReviewQueueFilters = {
  assignment: "all" | "mine" | "unassigned" | "assigned";
  sla: "all" | "overdue" | "due_soon" | "on_track";
  priority: "all" | "low" | "normal" | "high" | "urgent";
};

const chartColors = ["var(--teal)", "var(--blue)", "var(--amber)", "var(--red)", "var(--violet)"];
type BenchmarkCohortScope =
  | "tenant"
  | "age_group"
  | "position"
  | "region"
  | "local_association"
  | "regional_association";

function infrastructureTone(component: InfrastructureComponent) {
  if (component.configured || component.status === "local") {
    return "ready";
  }
  if (component.status === "standby") {
    return "standby";
  }
  return "attention";
}

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

function toDateTimeLocalValue(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
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

function ArtifactAccessTrendCard({ summary }: { summary: AgentScorecardArtifactAccessSummaryRead }) {
  const buckets = [...summary.daily_trend].reverse();
  const max = Math.max(...buckets.map((bucket) => bucket.total_count), 1);
  if (buckets.length === 0) {
    return null;
  }

  return (
    <article className="task-card chart-card">
      <div>
        <strong>Artifact access trend · {buckets.length} days</strong>
        <span>Daily signed scorecard link creation and artifact opens</span>
      </div>
      <div className="chart-bars artifact-trend-bars">
        {buckets.map((bucket) => {
          const width = Math.max(4, Math.round((bucket.total_count / max) * 100));
          const linkShare = bucket.total_count > 0
            ? Math.round((bucket.link_created_count / bucket.total_count) * 100)
            : 0;
          const openShare = bucket.total_count > 0
            ? Math.max(0, 100 - linkShare)
            : 0;
          return (
            <div className="chart-bar-row artifact-trend-row" key={bucket.date}>
              <span>{bucket.date.slice(5)}</span>
              <div className="chart-track artifact-trend-track">
                <div className="artifact-trend-stack" style={{ width: `${width}%` }}>
                  {bucket.link_created_count > 0 ? (
                    <i
                      className="artifact-trend-link"
                      style={{ width: `${Math.max(8, linkShare)}%` }}
                    />
                  ) : null}
                  {bucket.artifact_opened_count > 0 ? (
                    <i
                      className="artifact-trend-open"
                      style={{ width: `${Math.max(8, openShare)}%` }}
                    />
                  ) : null}
                </div>
              </div>
              <strong>{bucket.total_count}</strong>
            </div>
          );
        })}
      </div>
      <div className="chart-legend artifact-trend-legend">
        <span><i className="artifact-trend-link" />Links</span>
        <span><i className="artifact-trend-open" />Opens</span>
      </div>
    </article>
  );
}

function performanceValueLabel(value: number | null | undefined, unit?: string | null) {
  if (typeof value !== "number") {
    return "n/a";
  }
  const rounded = Number.isInteger(value) ? value.toString() : value.toFixed(1);
  return unit ? `${rounded} ${unit}` : rounded;
}

function PerformanceVisualDashboard({
  summary,
  assessments,
  trends,
  benchmarks
}: {
  summary: AthletePerformanceSummaryRead | null;
  assessments: AthleteAssessmentRead[];
  trends: PerformanceMetricTrendRead[];
  benchmarks: PerformanceMetricBenchmarkRead[];
}) {
  const latestAssessment = assessments.find((assessment) => assessment.id === summary?.latest_assessment_id)
    ?? assessments.find((assessment) => assessment.verification_status === "verified")
    ?? assessments[0]
    ?? null;
  const composition = latestAssessment
    ? [
        ["Physical", latestAssessment.physical_score, "var(--teal)"],
        ["Technical", latestAssessment.technical_score, "var(--blue)"],
        ["Tactical", latestAssessment.tactical_score, "var(--amber)"],
        ["Mental", latestAssessment.mental_score, "var(--violet)"]
      ]
    : [];
  const trendMax = Math.max(
    1,
    ...trends.slice(0, 4).flatMap((trend) => [
      Math.abs(trend.latest_value ?? 0),
      Math.abs(trend.forecast_next_value ?? 0),
      Math.abs(trend.best_value ?? 0)
    ])
  );

  return (
    <div className="task-list">
      <article className="task-card chart-card">
        <div>
          <strong>ALS composition · {summary?.latest_overall_score ?? "—"}</strong>
          <span>{summary?.rating ?? "No verified assessment"} · {summary?.assessment_count ?? 0} assessments</span>
        </div>
        <div className="chart-bars">
          {composition.length ? composition.map(([label, value, color]) => {
            const score = Number(value);
            return (
              <div className="chart-bar-row" key={label}>
                <span>{label}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{ width: `${Math.max(4, Math.min(100, score))}%`, backgroundColor: String(color) }}
                  />
                </div>
                <strong>{score}</strong>
              </div>
            );
          }) : (
            <div className="chart-bar-row">
              <span>No scores</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--muted)" }} />
              </div>
              <strong>0</strong>
            </div>
          )}
        </div>
      </article>

      <article className="task-card chart-card">
        <div>
          <strong>Trend runway · {trends.length} metrics</strong>
          <span>Latest values compared with the next simple forecast</span>
        </div>
        <div className="chart-bars">
          {trends.slice(0, 4).map((trend, index) => {
            const latestWidth = Math.max(4, Math.round((Math.abs(trend.latest_value ?? 0) / trendMax) * 100));
            const forecastWidth = Math.max(4, Math.round((Math.abs(trend.forecast_next_value ?? 0) / trendMax) * 100));
            return (
              <div className="chart-bar-row" key={`${trend.metric_definition_id}-visual`}>
                <span>{trend.metric_name}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{
                      width: `${Math.max(latestWidth, forecastWidth)}%`,
                      backgroundColor: chartColors[index % chartColors.length]
                    }}
                  />
                </div>
                <strong>{performanceValueLabel(trend.forecast_next_value ?? trend.latest_value, trend.unit)}</strong>
              </div>
            );
          })}
          {trends.length === 0 ? (
            <div className="chart-bar-row">
              <span>No trend data</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--muted)" }} />
              </div>
              <strong>n/a</strong>
            </div>
          ) : null}
        </div>
      </article>

      <article className="task-card chart-card">
        <div>
          <strong>Cohort standing · {benchmarks.length} benchmarks</strong>
          <span>
            {benchmarks[0]?.cohort_label ?? "All athletes"} · {(benchmarks[0]?.cohort_scope ?? "tenant").replaceAll("_", " ")}
          </span>
        </div>
        <div className="chart-bars">
          {benchmarks.slice(0, 4).map((benchmark, index) => {
            const percentile = benchmark.percentile_rank ?? 0;
            return (
              <div className="chart-bar-row" key={`${benchmark.metric_definition_id}-benchmark-visual`}>
                <span>{benchmark.metric_name}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{
                      width: `${Math.max(4, Math.min(100, percentile))}%`,
                      backgroundColor: chartColors[(index + 1) % chartColors.length]
                    }}
                  />
                </div>
                <strong>{benchmark.percentile_rank === null ? "n/a" : `${benchmark.percentile_rank}%`}</strong>
              </div>
            );
          })}
          {benchmarks.length === 0 ? (
            <div className="chart-bar-row">
              <span>No benchmark</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--muted)" }} />
              </div>
              <strong>n/a</strong>
            </div>
          ) : null}
        </div>
      </article>
    </div>
  );
}

function PerformanceTrendSeriesDashboard({ series }: { series: PerformanceMetricTrendSeriesRead[] }) {
  const visibleSeries = series
    .filter((item) => item.points.length > 0)
    .slice(0, 4);

  return (
    <div className="trend-series-grid">
      {visibleSeries.map((item, index) => (
        <article className="task-card trend-series-card" key={`${item.metric_definition_id}-series`}>
          <div>
            <strong>{item.metric_name} · {item.trend_direction.replaceAll("_", " ")}</strong>
            <span>
              {item.sample_size} points · latest {performanceValueLabel(item.latest_value, item.unit)} · forecast{" "}
              {performanceValueLabel(item.forecast_next_value, item.unit)}
            </span>
          </div>
          <div className="spark-bars" aria-label={`${item.metric_name} time series`}>
            {item.points.map((point) => (
              <i
                key={point.observation_id}
                title={`${new Date(point.observed_at).toLocaleDateString()} · ${performanceValueLabel(point.value, item.unit)}`}
                style={{
                  height: `${Math.max(8, point.normalized_value)}%`,
                  backgroundColor: chartColors[index % chartColors.length]
                }}
              />
            ))}
          </div>
          <small>{item.recommendation}</small>
        </article>
      ))}
      {visibleSeries.length === 0 ? (
        <article className="task-card trend-series-card">
          <div>
            <strong>Metric history</strong>
            <span>Accepted observations will render as compact time-series bars.</span>
          </div>
          <div className="spark-bars empty">
            <i />
            <i />
            <i />
          </div>
          <small>No accepted performance observations are available yet.</small>
        </article>
      ) : null}
    </div>
  );
}

function PerformanceCohortComparisonDashboard({ comparisons }: { comparisons: PerformanceCohortComparisonRead[] }) {
  const visibleComparisons = comparisons.slice(0, 4);

  return (
    <div className="trend-series-grid">
      {visibleComparisons.map((comparison, index) => {
        const percentile = comparison.average_percentile ?? 0;
        return (
          <article className="task-card chart-card" key={`${comparison.cohort_scope}-comparison`}>
            <div>
              <strong>{comparison.cohort_label} · {comparison.cohort_scope.replaceAll("_", " ")}</strong>
              <span>
                {comparison.metric_count} metrics · {comparison.sample_size_total} samples · {comparison.watch_count} watch
              </span>
            </div>
            <div className="chart-bars">
              <div className="chart-bar-row">
                <span>Average</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{ width: `${Math.max(4, Math.min(100, percentile))}%`, backgroundColor: chartColors[index % chartColors.length] }}
                  />
                </div>
                <strong>{comparison.average_percentile === null ? "n/a" : `${comparison.average_percentile}%`}</strong>
              </div>
              <div className="chart-bar-row">
                <span>{comparison.top_metric_name ?? "Top metric"}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{
                      width: `${Math.max(4, Math.min(100, comparison.top_percentile ?? 0))}%`,
                      backgroundColor: chartColors[(index + 1) % chartColors.length]
                    }}
                  />
                </div>
                <strong>{comparison.top_percentile === null ? "n/a" : `${comparison.top_percentile}%`}</strong>
              </div>
            </div>
            <small>{comparison.recommendation}</small>
          </article>
        );
      })}
      {visibleComparisons.length === 0 ? (
        <article className="task-card chart-card">
          <div>
            <strong>Cohort comparison</strong>
            <span>Benchmark scopes will appear after accepted observations are recorded.</span>
          </div>
          <small>No cohort comparison data is available yet.</small>
        </article>
      ) : null}
    </div>
  );
}

function PerformanceForecastScenarioDashboard({ scenarios }: { scenarios: PerformanceForecastScenarioRead[] }) {
  const visibleScenarios = scenarios
    .filter((scenario) => scenario.sample_size > 0)
    .slice(0, 4);
  const maxProjection = Math.max(
    1,
    ...visibleScenarios.flatMap((scenario) => [
      Math.abs(scenario.latest_value ?? 0),
      Math.abs(scenario.forecast_next_value ?? 0),
      ...scenario.projected_points.map((point) => Math.abs(point))
    ])
  );

  return (
    <div className="trend-series-grid">
      {visibleScenarios.map((scenario, index) => (
        <article className="task-card trend-series-card" key={`${scenario.metric_definition_id}-forecast-scenario`}>
          <div>
            <strong>{scenario.metric_name} · {scenario.risk_level.replaceAll("_", " ")}</strong>
            <span>
              {scenario.data_quality.replaceAll("_", " ")} · {Math.round(scenario.confidence * 100)}% confidence ·{" "}
              {scenario.model_policy.replaceAll("_", " ")}
            </span>
          </div>
          <div className="spark-bars" aria-label={`${scenario.metric_name} forecast scenario`}>
            {scenario.projected_points.length ? scenario.projected_points.map((point, pointIndex) => (
              <i
                key={`${scenario.metric_definition_id}-projection-${pointIndex}`}
                title={`Scenario ${pointIndex + 1} · ${performanceValueLabel(point, scenario.unit)}`}
                style={{
                  height: `${Math.max(8, Math.min(100, (Math.abs(point) / maxProjection) * 100))}%`,
                  backgroundColor: chartColors[(index + pointIndex) % chartColors.length]
                }}
              />
            )) : (
              <i style={{ height: "12%", backgroundColor: "var(--muted)" }} />
            )}
          </div>
          <small>
            Next {performanceValueLabel(scenario.forecast_next_value, scenario.unit)} · range{" "}
            {performanceValueLabel(scenario.forecast_low, scenario.unit)} to {performanceValueLabel(scenario.forecast_high, scenario.unit)}
          </small>
          <small>{scenario.recommendation}</small>
        </article>
      ))}
      {visibleScenarios.length === 0 ? (
        <article className="task-card trend-series-card">
          <div>
            <strong>Forecast scenarios</strong>
            <span>Accepted observations will generate deterministic training runway scenarios.</span>
          </div>
          <div className="spark-bars empty">
            <i />
            <i />
            <i />
          </div>
          <small>No forecast-ready performance history is available yet.</small>
        </article>
      ) : null}
    </div>
  );
}

function PerformanceWhatIfScenarioDashboard({ scenarios }: { scenarios: PerformanceForecastWhatIfRead[] }) {
  const visibleScenarios = scenarios.filter((scenario) => scenario.sample_size > 0).slice(0, 4);
  const maxProjection = Math.max(
    1,
    ...visibleScenarios.flatMap((scenario) => [
      Math.abs(scenario.latest_value ?? 0),
      Math.abs(scenario.forecast_next_value ?? 0),
      ...scenario.projected_points.map((point) => Math.abs(point))
    ])
  );

  return (
    <div className="trend-series-grid">
      {visibleScenarios.map((scenario, index) => (
        <article className="task-card trend-series-card" key={`${scenario.metric_definition_id}-what-if-scenario`}>
          <div>
            <strong>{scenario.metric_name} · {scenario.scenario_label}</strong>
            <span>
              {scenario.risk_level.replaceAll("_", " ")} · horizon {scenario.horizon} ·{" "}
              {Math.round(scenario.confidence * 100)}% confidence · {scenario.model_policy.replaceAll("_", " ")}
            </span>
          </div>
          <div className="spark-bars" aria-label={`${scenario.metric_name} what-if forecast`}>
            {scenario.projected_points.map((point, pointIndex) => (
              <i
                key={`${scenario.metric_definition_id}-what-if-${pointIndex}`}
                title={`What-if ${pointIndex + 1} · ${performanceValueLabel(point, scenario.unit)}`}
                style={{
                  height: `${Math.max(8, Math.min(100, (Math.abs(point) / maxProjection) * 100))}%`,
                  backgroundColor: chartColors[(index + pointIndex + 2) % chartColors.length]
                }}
              />
            ))}
          </div>
          <small>
            Next {performanceValueLabel(scenario.forecast_next_value, scenario.unit)} · range{" "}
            {performanceValueLabel(scenario.forecast_low, scenario.unit)} to {performanceValueLabel(scenario.forecast_high, scenario.unit)}
          </small>
          <small>{scenario.recommendation}</small>
        </article>
      ))}
      {visibleScenarios.length === 0 ? (
        <article className="task-card trend-series-card">
          <div>
            <strong>What-if scenarios</strong>
            <span>Coach adjustments will appear once accepted observations exist.</span>
          </div>
          <div className="spark-bars empty">
            <i />
            <i />
            <i />
          </div>
          <small>No what-if forecast can be calculated yet.</small>
        </article>
      ) : null}
    </div>
  );
}

function PerformanceInjuryRiskCard({
  risk,
  alert,
  onSendAlert,
  disabled
}: {
  risk: PerformanceInjuryRiskRead | null;
  alert: PerformanceInjuryRiskAlertRead | null;
  onSendAlert: () => void;
  disabled: boolean;
}) {
  const score = risk?.score ?? 0;
  const riskColor =
    risk?.risk_band === "critical" ? "var(--red)" :
    risk?.risk_band === "high" ? "var(--orange)" :
    risk?.risk_band === "watch" ? "var(--amber)" :
    "var(--green)";

  return (
    <article className="task-card chart-card">
      <div>
        <strong>Injury risk · {risk?.risk_band ?? "no data"}</strong>
        <span>
          {risk ? `${Math.round(risk.confidence * 100)}% confidence · ${risk.model_policy.replaceAll("_", " ")}` : "Training feedback drives risk prediction"}
        </span>
      </div>
      <div className="chart-bars">
        <div className="chart-bar-row">
          <span>Risk score</span>
          <div className="chart-track">
            <div className="chart-fill" style={{ width: `${Math.max(4, Math.min(100, score))}%`, backgroundColor: riskColor }} />
          </div>
          <strong>{risk?.score ?? "n/a"}</strong>
        </div>
        <div className="chart-bar-row">
          <span>Readiness</span>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{
                width: `${Math.max(4, Math.min(100, risk?.latest_readiness_score ?? 0))}%`,
                backgroundColor: "var(--teal)"
              }}
            />
          </div>
          <strong>{risk?.latest_readiness_score ?? "n/a"}</strong>
        </div>
        <div className="chart-bar-row">
          <span>ACWR</span>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{
                width: `${Math.max(4, Math.min(100, (risk?.acute_chronic_ratio ?? 0) * 50))}%`,
                backgroundColor: "var(--violet)"
              }}
            />
          </div>
          <strong>{risk?.acute_chronic_ratio ?? "n/a"}</strong>
        </div>
        <div className="chart-bar-row">
          <span>Weather</span>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{
                width: `${Math.max(4, Math.min(100, (risk?.weather_alert_count ?? 0) * 34))}%`,
                backgroundColor: "var(--blue)"
              }}
            />
          </div>
          <strong>{risk?.latest_weather_alert_level ?? "n/a"}</strong>
        </div>
        <div className="chart-bar-row">
          <span>Surface</span>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{
                width: `${Math.max(4, Math.min(100, (risk?.hazardous_surface_count ?? 0) * 50))}%`,
                backgroundColor: "var(--orange)"
              }}
            />
          </div>
          <strong>{risk?.hazardous_surface_count ?? "n/a"}</strong>
        </div>
        <div className="chart-bar-row">
          <span>Biomarkers</span>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{
                width: `${Math.max(4, Math.min(100, (risk?.biomarker_risk_count ?? 0) * 25))}%`,
                backgroundColor: "var(--red)"
              }}
            />
          </div>
          <strong>{risk?.biomarker_risk_count ?? "n/a"}</strong>
        </div>
        <div className="chart-bar-row">
          <span>Movement</span>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{
                width: `${Math.max(4, Math.min(100, (risk?.biomechanical_risk_count ?? 0) * 34))}%`,
                backgroundColor: "var(--amber)"
              }}
            />
          </div>
          <strong>{risk?.biomechanical_risk_count ?? "n/a"}</strong>
        </div>
        <div className="chart-bar-row">
          <span>Recovery</span>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{
                width: `${Math.max(4, Math.min(100, risk?.latest_recovery_score ?? risk?.latest_hydration_score ?? 0))}%`,
                backgroundColor: "var(--green)"
              }}
            />
          </div>
          <strong>{risk?.latest_recovery_score ?? risk?.latest_hydration_score ?? "n/a"}</strong>
        </div>
      </div>
      <small>{risk?.drivers[0] ?? "Record athlete-specific readiness and session feedback to generate risk drivers."}</small>
      {risk?.video_risk_labels.length ? <small>Video: {risk.video_risk_labels.join(", ")}</small> : null}
      <small>{risk?.recommendation ?? "No risk recommendation is available yet."}</small>
      <span>
        <button type="button" onClick={onSendAlert} disabled={disabled || !risk}>Send risk alert</button>
      </span>
      {alert ? (
        <small>
          {alert.sent
            ? `Alert sent as ${alert.message_ids.length} message(s) across ${alert.channels.join(", ")} to ${alert.recipient_count} delivery target(s).`
            : alert.skipped_reason ?? `Dry run: ${alert.recipient_count} recipient(s) would be alerted.`}
        </small>
      ) : null}
    </article>
  );
}

function downloadTextArtifact(content: string, contentType: string, filename: string) {
  const blob = new Blob([content], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function downloadBase64Artifact(contentBase64: string, contentType: string, filename: string) {
  const raw = window.atob(contentBase64);
  const bytes = new Uint8Array(raw.length);
  for (let index = 0; index < raw.length; index += 1) {
    bytes[index] = raw.charCodeAt(index);
  }
  const blob = new Blob([bytes], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
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
  const [weatherAssessments, setWeatherAssessments] = useState<EventWeatherAssessmentRead[]>([]);
  const [weatherAlert, setWeatherAlert] = useState<EventWeatherAlertRead | null>(null);
  const [weatherAutomation, setWeatherAutomation] = useState<EventWeatherAutomationRunRead | null>(null);
  const [travelPlans, setTravelPlans] = useState<EventTravelPlanRead[]>([]);
  const [travelConsentBatch, setTravelConsentBatch] = useState<EventTravelConsentBatchRead | null>(null);
  const [travelConsentReminder, setTravelConsentReminder] = useState<EventTravelConsentReminderRead | null>(null);
  const [travelConsentReminderRun, setTravelConsentReminderRun] =
    useState<EventTravelConsentReminderRunRead | null>(null);
  const [travelManifest, setTravelManifest] = useState<EventTravelManifestRead | null>(null);
  const [travelOfflineManifestCache, setTravelOfflineManifestCache] = useState<TravelManifestOfflineCache | null>(null);
  const [travelManifestExport, setTravelManifestExport] = useState<EventTravelManifestExportRead | null>(null);
  const [travelManifestOfflineLink, setTravelManifestOfflineLink] =
    useState<EventTravelManifestOfflineLinkRead | null>(null);
  const [travelFeeBatch, setTravelFeeBatch] = useState<EventTravelFeeInvoiceBatchRead | null>(null);
  const [travelFeeCheckoutBatch, setTravelFeeCheckoutBatch] = useState<EventTravelFeeCheckoutBatchRead | null>(null);
  const [travelFeeReconciliation, setTravelFeeReconciliation] =
    useState<EventTravelFeeReconciliationRead | null>(null);
  const [travelApprovals, setTravelApprovals] = useState<EventTravelApprovalRead[]>([]);
  const [travelApprovalRouting, setTravelApprovalRouting] = useState<EventTravelApprovalRoutingRead | null>(null);
  const [travelChecklistItems, setTravelChecklistItems] = useState<EventTravelChecklistItemRead[]>([]);
  const [selectedTravelChecklistFile, setSelectedTravelChecklistFile] = useState<File | null>(null);
  const [travelLocationUpdates, setTravelLocationUpdates] = useState<EventTravelLocationUpdateRead[]>([]);
  const [travelTelemetryStream, setTravelTelemetryStream] = useState<EventTravelTelemetryStreamRead | null>(null);
  const [travelDevices, setTravelDevices] = useState<EventTravelDeviceRead[]>([]);
  const [travelDeviceSecret, setTravelDeviceSecret] = useState<EventTravelDeviceSecretRead | null>(null);
  const [travelDeviceFleetInventory, setTravelDeviceFleetInventory] =
    useState<EventTravelDeviceFleetInventoryRead | null>(null);
  const [travelBackupDrivers, setTravelBackupDrivers] = useState<EventTravelBackupDriverRead[]>([]);
  const [travelBackupDriverDispatch, setTravelBackupDriverDispatch] =
    useState<EventTravelBackupDriverDispatchRead | null>(null);
  const [travelDriverMarketplace, setTravelDriverMarketplace] = useState<EventTravelDriverMarketplaceRead | null>(null);
  const [travelDriverRatings, setTravelDriverRatings] = useState<EventTravelDriverRatingRead[]>([]);
  const [travelDriverRatingSummary, setTravelDriverRatingSummary] = useState<EventTravelDriverRatingSummaryRead | null>(null);
  const [travelExpenses, setTravelExpenses] = useState<EventTravelExpenseRead[]>([]);
  const [travelExpensePayout, setTravelExpensePayout] = useState<EventTravelExpensePayoutRead | null>(null);
  const [selectedTravelReceiptFile, setSelectedTravelReceiptFile] = useState<File | null>(null);
  const [travelCarpoolRides, setTravelCarpoolRides] = useState<EventTravelCarpoolRideRead[]>([]);
  const [travelCarpoolAutoMatch, setTravelCarpoolAutoMatch] = useState<EventTravelCarpoolAutoMatchRead | null>(null);
  const [travelReadiness, setTravelReadiness] = useState<EventTravelReadinessRead | null>(null);
  const [travelRouteOptimization, setTravelRouteOptimization] = useState<EventTravelRouteOptimizationRead | null>(null);
  const [travelRouteMap, setTravelRouteMap] = useState<EventTravelMapRead | null>(null);
  const [travelGeofenceCheck, setTravelGeofenceCheck] = useState<EventTravelGeofenceCheckRead | null>(null);
  const [travelGeofenceZones, setTravelGeofenceZones] = useState<EventTravelGeofenceZoneRead[]>([]);
  const [agents, setAgents] = useState<AgentRead[]>([]);
  const [agentTasks, setAgentTasks] = useState<AgentTaskRead[]>([]);
  const [agentRuns, setAgentRuns] = useState<AgentRunRecordRead[]>([]);
  const [agentLedgerVerification, setAgentLedgerVerification] =
    useState<AgentRunLedgerVerificationRead | null>(null);
  const [agentGovernance, setAgentGovernance] = useState<AgentGovernanceSummaryRead | null>(null);
  const [agentTransparency, setAgentTransparency] = useState<AgentModelTransparencyReportRead | null>(null);
  const [agentModelRegistry, setAgentModelRegistry] = useState<AgentModelRegistryRead[]>([]);
  const [agentBiasAudits, setAgentBiasAudits] = useState<AgentBiasAuditRead[]>([]);
  const [agentDecisionAppeals, setAgentDecisionAppeals] = useState<AgentDecisionAppealRead[]>([]);
  const [agentEthicalScorecard, setAgentEthicalScorecard] = useState<AgentEthicalScorecardRead | null>(null);
  const [agentScorecardComments, setAgentScorecardComments] = useState<AgentScorecardCommentModerationRead[]>([]);
  const [agentScorecardPublications, setAgentScorecardPublications] = useState<AgentScorecardPublicationRead[]>([]);
  const [agentScorecardReadiness, setAgentScorecardReadiness] = useState<AgentScorecardPublicationReadinessRead | null>(null);
  const [agentScorecardReminder, setAgentScorecardReminder] = useState<AgentScorecardPublicationReminderRead | null>(null);
  const [agentScorecardReminderRun, setAgentScorecardReminderRun] =
    useState<AgentScorecardPublicationReminderRunRead | null>(null);
  const [agentScorecardAutomationRun, setAgentScorecardAutomationRun] =
    useState<AgentScorecardAutomationRunRead | null>(null);
  const [agentScorecardArtifactLink, setAgentScorecardArtifactLink] =
    useState<AgentScorecardPublicationArtifactLinkRead | null>(null);
  const [agentScorecardArtifactAccesses, setAgentScorecardArtifactAccesses] =
    useState<AgentScorecardArtifactAccessRead[]>([]);
  const [agentScorecardArtifactAccessSummary, setAgentScorecardArtifactAccessSummary] =
    useState<AgentScorecardArtifactAccessSummaryRead | null>(null);
  const [agentScorecardArtifactAnomalyAlert, setAgentScorecardArtifactAnomalyAlert] =
    useState<AgentScorecardArtifactAnomalyAlertRead | null>(null);
  const [agentScorecardArtifactAnomalyAlertRun, setAgentScorecardArtifactAnomalyAlertRun] =
    useState<AgentScorecardArtifactAnomalyAlertRunRead | null>(null);
  const [metricDefinitions, setMetricDefinitions] = useState<MetricDefinitionRead[]>([]);
  const [observations, setObservations] = useState<PerformanceObservationRead[]>([]);
  const [performanceIngestion, setPerformanceIngestion] = useState<PerformanceIngestionRead | null>(null);
  const [performanceModelBenchmark, setPerformanceModelBenchmark] =
    useState<PerformanceModelExtractionBenchmarkRunRead | null>(null);
  const [performanceModelBenchmarkDatasets, setPerformanceModelBenchmarkDatasets] =
    useState<PerformanceModelExtractionBenchmarkDatasetRead[]>([]);
  const [performanceWebhookIngest, setPerformanceWebhookIngest] = useState<PerformanceWearableWebhookRead | null>(null);
  const [wearableConnections, setWearableConnections] = useState<PerformanceWearableConnectionRead[]>([]);
  const [wearableSyncRun, setWearableSyncRun] = useState<PerformanceWearableSyncRunRead | null>(null);
  const [wearableOAuthStart, setWearableOAuthStart] = useState<PerformanceWearableOAuthStartRead | null>(null);
  const [wearableOAuthCallback, setWearableOAuthCallback] = useState<PerformanceWearableOAuthCallbackRead | null>(null);
  const [wearableTokenRefresh, setWearableTokenRefresh] = useState<PerformanceWearableTokenRefreshRead | null>(null);
  const [wearableWebhookRegistration, setWearableWebhookRegistration] =
    useState<PerformanceWearableWebhookRegistrationRead | null>(null);
  const [performanceBenchmarks, setPerformanceBenchmarks] = useState<PerformanceMetricBenchmarkRead[]>([]);
  const [performanceBenchmarkScope, setPerformanceBenchmarkScope] = useState<BenchmarkCohortScope>("tenant");
  const [performanceCohortComparisons, setPerformanceCohortComparisons] = useState<PerformanceCohortComparisonRead[]>([]);
  const [performanceTrends, setPerformanceTrends] = useState<PerformanceMetricTrendRead[]>([]);
  const [performanceTrendSeries, setPerformanceTrendSeries] = useState<PerformanceMetricTrendSeriesRead[]>([]);
  const [performanceTrendPeriodStart, setPerformanceTrendPeriodStart] = useState("");
  const [performanceTrendPeriodEnd, setPerformanceTrendPeriodEnd] = useState("");
  const [performanceTrendCategory, setPerformanceTrendCategory] = useState<MetricCategory | "all">("all");
  const [performanceTrendMetricCode, setPerformanceTrendMetricCode] = useState("");
  const [performanceForecastScenarios, setPerformanceForecastScenarios] = useState<PerformanceForecastScenarioRead[]>([]);
  const [performanceWhatIfScenarios, setPerformanceWhatIfScenarios] = useState<PerformanceForecastWhatIfRead[]>([]);
  const [performanceForecastValidationRun, setPerformanceForecastValidationRun] =
    useState<PerformanceForecastValidationRunRead | null>(null);
  const [performanceForecastValidationRuns, setPerformanceForecastValidationRuns] =
    useState<PerformanceForecastValidationRunRead[]>([]);
  const [performanceForecastValidationAlert, setPerformanceForecastValidationAlert] =
    useState<PerformanceForecastValidationAlertRead | null>(null);
  const [performanceWhatIfAdjustment, setPerformanceWhatIfAdjustment] = useState(15);
  const [performanceWhatIfReadiness, setPerformanceWhatIfReadiness] = useState(70);
  const [performanceRiskAlertChannels, setPerformanceRiskAlertChannels] =
    useState<CommunicationChannel[]>(["in_app", "push", "sms", "whatsapp"]);
  const [performanceInjuryRisk, setPerformanceInjuryRisk] = useState<PerformanceInjuryRiskRead | null>(null);
  const [performanceInjuryRiskAlert, setPerformanceInjuryRiskAlert] = useState<PerformanceInjuryRiskAlertRead | null>(null);
  const [performanceInjuryRiskAlertRun, setPerformanceInjuryRiskAlertRun] =
    useState<PerformanceInjuryRiskAlertRunRead | null>(null);
  const [performanceGoals, setPerformanceGoals] = useState<PerformanceGoalRead[]>([]);
  const [performanceAwards, setPerformanceAwards] = useState<PerformanceAchievementAwardRead[]>([]);
  const [performanceAchievementRun, setPerformanceAchievementRun] =
    useState<PerformanceAchievementRunRead | null>(null);
  const [performanceReviewEscalationRun, setPerformanceReviewEscalationRun] =
    useState<PerformanceAssessmentReviewEscalationRunRead | null>(null);
  const [assessments, setAssessments] = useState<AthleteAssessmentRead[]>([]);
  const [assessmentReviewQueue, setAssessmentReviewQueue] = useState<AthleteAssessmentReviewQueueItemRead[]>([]);
  const [assessmentReviewSummary, setAssessmentReviewSummary] =
    useState<AssessmentReviewQueueSummaryRead | null>(null);
  const [assessmentReviewQueueFilters, setAssessmentReviewQueueFilters] =
    useState<AssessmentReviewQueueFilters>({ assignment: "all", sla: "all", priority: "all" });
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
  const [escalationRun, setEscalationRun] = useState<CommunicationEscalationRunRead | null>(null);
  const [notificationPreference, setNotificationPreference] = useState<NotificationPreferenceRead | null>(null);
  const [facilities, setFacilities] = useState<FacilityRead[]>([]);
  const [emergencyPlans, setEmergencyPlans] = useState<EmergencyActionPlanRead[]>([]);
  const [emergencyActivations, setEmergencyActivations] = useState<EmergencyPlanActivationRead[]>([]);
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
  const [commercialTaxFiling, setCommercialTaxFiling] = useState<CommercialTaxFilingRead | null>(null);
  const [paymentSettlement, setPaymentSettlement] = useState<PaymentSettlementRead | null>(null);
  const [commercialPayout, setCommercialPayout] = useState<CommercialSettlementPayoutRead | null>(null);
  const [commercialPayouts, setCommercialPayouts] = useState<CommercialSettlementPayoutRead[]>([]);
  const [accountingExport, setAccountingExport] = useState<AccountingExportRead | null>(null);
  const [accountingSync, setAccountingSync] = useState<AccountingSyncRead | null>(null);
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
  const [developerApplications, setDeveloperApplications] = useState<DeveloperApplicationRead[]>([]);
  const [developerApiKeys, setDeveloperApiKeys] = useState<DeveloperApiKeyRead[]>([]);
  const [developerOAuthAuthorizations, setDeveloperOAuthAuthorizations] = useState<DeveloperOAuthAuthorizationRead[]>([]);
  const [developerOAuthGrant, setDeveloperOAuthGrant] = useState<DeveloperOAuthAuthorizationRead | null>(null);
  const [developerWebhooks, setDeveloperWebhooks] = useState<DeveloperWebhookSubscriptionRead[]>([]);
  const [developerWebhookDeliveries, setDeveloperWebhookDeliveries] = useState<DeveloperWebhookDeliveryRead[]>([]);
  const [developerWebhookRetryRun, setDeveloperWebhookRetryRun] = useState<DeveloperWebhookRetryRunRead | null>(null);
  const [developerListings, setDeveloperListings] = useState<DeveloperMarketplaceListingRead[]>([]);
  const [developerCatalog, setDeveloperCatalog] = useState<DeveloperIntegrationCatalogRead | null>(null);
  const [developerSummary, setDeveloperSummary] = useState<DeveloperPortalSummaryRead | null>(null);
  const [developerApplicationSecret, setDeveloperApplicationSecret] =
    useState<DeveloperApplicationProvisionedRead | null>(null);
  const [developerApiKeySecret, setDeveloperApiKeySecret] =
    useState<DeveloperApiKeyProvisionedRead | null>(null);
  const [developerWebhookSecret, setDeveloperWebhookSecret] =
    useState<DeveloperWebhookSubscriptionProvisionedRead | null>(null);
  const [registrationInquiries, setRegistrationInquiries] = useState<RegistrationInquiryRead[]>([]);
  const [inquiryReviewForms, setInquiryReviewForms] = useState<Record<string, InquiryReviewForm>>({});
  const [athletes, setAthletes] = useState<AthleteEntry[]>([]);
  const [guardians, setGuardians] = useState<GuardianRelationshipRead[]>([]);
  const [consentRequest, setConsentRequest] = useState<ConsentRequestRead | null>(null);
  const [clearance, setClearance] = useState<ParticipationClearanceRead | null>(null);
  const [safeguardingIncidents, setSafeguardingIncidents] = useState<SafeguardingIncidentRead[]>([]);
  const [backgroundChecks, setBackgroundChecks] = useState<BackgroundCheckRead[]>([]);
  const [complianceCredentials, setComplianceCredentials] = useState<ComplianceCredentialRead[]>([]);
  const [complianceSummary, setComplianceSummary] = useState<ComplianceSummaryRead | null>(null);
  const [incidentReportPackages, setIncidentReportPackages] = useState<IncidentReportPackageRead[]>([]);
  const [incidentInsuranceClaims, setIncidentInsuranceClaims] = useState<IncidentInsuranceClaimRead[]>([]);
  const [incidentMedicalClearances, setIncidentMedicalClearances] = useState<IncidentMedicalClearanceRead[]>([]);
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
  const [emergencyAlert, setEmergencyAlert] = useState<EmergencyActivationAlertRead | null>(null);
  const [selectedEquipmentFile, setSelectedEquipmentFile] = useState<File | null>(null);
  const [infrastructureStatus, setInfrastructureStatus] = useState<InfrastructureStatus | null>(null);
  const [infrastructureProbes, setInfrastructureProbes] = useState<InfrastructureProbeSummary | null>(null);
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
    country_code: "KE",
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
  const [weatherForm, setWeatherForm] = useState({
    source: "manual venue check",
    observed_at: "2026-05-28T08:30",
    temperature_c: 29,
    heat_index_c: 31,
    wbgt_c: 28.5,
    humidity_percent: 72,
    aqi: 82,
    lightning_distance_km: 30,
    wind_speed_kph: 18,
    wind_gust_kph: 30,
    precipitation_mm_per_hr: 0,
    alert_channel: "push" as CommunicationChannel,
    notes: "Pre-match venue and weather safety check."
  });
  const [travelForm, setTravelForm] = useState({
    destination: "City Sports Complex",
    travel_mode: "Club minibus",
    departure_at: "2026-05-28T07:45",
    return_at: "2026-05-28T13:30",
    route_summary: "Meet at main field parking, route via A104, rest stop at Riverside services.",
    vehicle_details: "Minibus #3, seatbelts, first-aid kit, insurance current.",
    driver_details: "James Wilson, defensive driving and first aid verified.",
    staff_manifest: "Coach Maria Garcia; assistant David Chen; medic Amina Yusuf.",
    passenger_manifest: "U16 match squad and substitutes.",
    lodging_details: "",
    meal_plan: "Packed snacks, water, and post-match lunch.",
    equipment_manifest: "2 kit bags, medical kit, match balls, hydration cooler.",
    emergency_contacts: "Coach Maria +254700111111; Safety Officer +254700222222.",
    medical_access_plan: "Nearest hospital: City Clinic, 8 km from destination. Athlete medical notes accessible to staff.",
    route_weather_risk: "low",
    driver_certification_status: "verified",
    vehicle_inspection_status: "passed",
    consent_required: true,
    consent_due_at: "2026-05-27T18:00",
    estimated_cost: 450,
    cost_per_participant: 15,
    consent_channel: "email" as ConsentCaptureChannel,
    reminder_channel: "email" as CommunicationChannel,
    approval_level: "school",
    checklist_type: "pre_trip_inspection",
    tracking_phase: "departed",
    tracking_source: "manual GPS",
    latitude: -1.2921,
    longitude: 36.8219,
    speed_kph: 45,
    heading_degrees: 90,
    tracking_channel: "push" as CommunicationChannel,
    device_provider: "hardware-gps",
    device_id: "bus-3-gps",
    device_label: "Minibus #3 tracker",
    device_status: "active" as EventTravelDeviceRead["status"],
    device_vehicle: "Minibus #3",
    backup_driver_name: "Grace Njeri",
    backup_driver_phone: "+254700333333",
    backup_driver_vehicle: "Reserve van #2",
    backup_driver_capacity: 12,
    backup_driver_license_status: "verified",
    backup_driver_background_status: "cleared",
    backup_driver_availability: "standby" as EventTravelBackupDriverRead["availability_status"],
    backup_driver_response_minutes: 25,
    backup_driver_priority: 1,
    backup_driver_notes: "On call during away fixtures and cleared for minor transport.",
    backup_dispatch_reason: "Primary driver reported a vehicle issue.",
    backup_dispatch_minimum_capacity: 8,
    backup_dispatch_require_verified: true,
    backup_dispatch_channel: "sms" as CommunicationChannel,
    driver_rating_name: "James Wilson",
    driver_rating_vehicle: "Minibus #3",
    driver_rating_overall: 5,
    driver_rating_safety: 5,
    driver_rating_punctuality: 4,
    driver_rating_communication: 5,
    driver_rating_vehicle_condition: 4,
    driver_rating_would_use_again: true,
    driver_rating_incident_reported: false,
    driver_rating_notes: "Safe driving, clear communication, and punctual arrival.",
    geofence_label: "planned route corridor",
    geofence_latitude: -1.2921,
    geofence_longitude: 36.8219,
    geofence_radius_km: 5,
    geofence_polygon: "-1.292100,36.821900; -1.291400,36.824000; -1.294000,36.824200; -1.294200,36.821400",
    geofence_provider: "manual_polygon",
    geofence_provider_zone_id: "route-corridor-001",
    geofence_provider_revision: "v1",
    geofence_channel: "push" as CommunicationChannel,
    expense_category: "fuel",
    expense_vendor: "Riverside Fuel",
    expense_amount: 75,
    expense_receipt_url: "https://receipts.example/travel-fuel.jpg",
    expense_notes: "Fuel and tolls for away match transport.",
    payout_provider: "mobile_money_gateway",
    payout_destination: "mpesa:+254700000000",
    payout_adapter_mode: "mobile_money",
    carpool_type: "request",
    carpool_pickup_location: "123 Main St",
    carpool_pickup_latitude: -1.2921,
    carpool_pickup_longitude: 36.8219,
    carpool_dropoff_location: "City Sports Complex",
    carpool_dropoff_latitude: -1.3021,
    carpool_dropoff_longitude: 36.8236,
    carpool_seats_requested: 1,
    carpool_seats_available: 3,
    carpool_window_start: "2026-05-28T07:00",
    carpool_window_end: "2026-05-28T07:30",
    carpool_notes: "Match families near the west side pickup zone.",
    route_strategy: "balanced",
    notes: "Away match travel plan."
  });
  const [guardianForm, setGuardianForm] = useState({
    guardian_display_name: "Parent Example",
    guardian_email: "parent@example.com",
    guardian_phone: "+254700000000"
  });
  const [incidentForm, setIncidentForm] = useState({
    title: "Matchday injury report",
    incident_type: "injury" as SafeguardingIncidentType,
    severity: "medium" as SafeguardingIncidentSeverity,
    occurred_at: "2026-05-28T10:15",
    location: "Main field",
    description: "Athlete reported ankle pain after a challenge.",
    immediate_action: "Removed from play, first aid applied, guardian notified.",
    medical_follow_up_required: "yes",
    regulatory_report_required: false
  });
  const [backgroundCheckForm, setBackgroundCheckForm] = useState({
    provider: "Manual verification",
    check_type: "Safeguarding background",
    requested_at: "2026-05-28T09:00",
    expires_at: "2027-05-28",
    external_reference: "BG-2026-001",
    notes: "Initial safeguarding screen for athlete-facing role."
  });
  const [credentialForm, setCredentialForm] = useState({
    title: "Safeguarding essentials",
    credential_type: "safeguarding_training" as ComplianceCredentialType,
    issuing_body: "AfroLete Academy",
    credential_number: "SAFE-2026-001",
    issued_at: "2026-05-28",
    expires_at: "2027-05-28",
    renewal_due_at: "2027-04-28",
    verification_url: "",
    notes: "Required before unsupervised athlete activities."
  });
  const [reportPackageForm, setReportPackageForm] = useState({
    agency_name: "County safeguarding office",
    jurisdiction: "Local",
    due_at: "2026-06-04",
    external_reference: "",
    notes: "Package prepared for statutory or league reporting."
  });
  const [insuranceClaimForm, setInsuranceClaimForm] = useState({
    provider_name: "Athletic Health Insurers",
    policy_number: "POL-2026-001",
    claim_type: "injury_medical" as InsuranceClaimType,
    claimed_amount: "3800",
    reserve_amount: "5000",
    currency: "USD",
    tracking_url: "",
    notes: "Claim package prepared from incident documentation."
  });
  const [medicalClearanceForm, setMedicalClearanceForm] = useState({
    clearance_type: "return_to_play",
    valid_from: "2026-05-28",
    valid_until: "2026-06-28",
    return_to_play_stage: "graduated_return_stage_1",
    provider_name: "Club medical officer",
    restrictions: "No contact drills until reviewed.",
    notes: "Medical review required before full competition clearance."
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
    source_provider: "",
    evidence_ref: "video://matchday/clip-001",
    evidence_text: "Clip analysis: first touch quality 8.4, pressure scan before receiving.",
    confidence: 0.9,
    notes: "Improved under pressure."
  });
  const [performanceGoalForm, setPerformanceGoalForm] = useState({
    title: "Reach first-touch score 9",
    target_value: 9,
    starts_at: "2026-05-28",
    due_at: "2026-06-28",
    reward_badge: "First Touch Builder",
    notes: "Goal set from performance trend review."
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
  const [emergencyPlanForm, setEmergencyPlanForm] = useState({
    title: "Main field medical emergency plan",
    emergency_type: "medical" as EmergencyType,
    effective_from: "2026-05-28",
    review_due_on: "2026-08-28",
    emergency_contacts: "Safety Officer x123; Medical lead x456; Emergency services 911",
    evacuation_routes: "Primary: north gate. Secondary: east service gate. Accessible route: clubhouse ramp.",
    medical_protocols: "Clear area, call medical lead, retrieve AED from clubhouse, begin first aid, log incident.",
    weather_protocols: "Lightning shelter: gym. Extreme heat: cooling station at clubhouse.",
    communication_protocols: "PA announcement, staff radio channel 3, mobile alert to staff and guardians.",
    incident_command_roles: "Incident commander: Safety Officer. Medical lead: Club medic. Communications: Team manager.",
    escalation_matrix: "Level 1: staff push. Level 2: guardians and venue operations. Level 3: emergency services and association leadership.",
    external_agency_contacts: "Emergency services 911; Venue security x789; County health duty desk.",
    equipment_locations: "AED: clubhouse lobby. First aid: equipment room. Stretcher: tunnel entrance.",
    assembly_points: "North car park and clubhouse lawn.",
    special_needs_plan: "Assign accessibility marshal to ramp route and medical transport point.",
    activation_location: "Section B, main touchline",
    responders: "Safety Officer; Club medic; Security lead",
    alert_channel: "push" as CommunicationChannel,
    alert_body: "",
    notes: "Reviewed before all tournament fixtures."
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
    method: "card",
    tax_jurisdiction: "KE",
    tax_rate: 16,
    tax_period_start: "2026-06-01",
    tax_period_end: "2026-06-30"
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
  const [developerForm, setDeveloperForm] = useState({
    app_name: "Matchday Sync",
    app_type: "server_to_server",
    app_scopes: "read:organization,write:events",
    redirect_uris: "https://sync.example/callback",
    contact_email: "integrations@example.com",
    api_key_name: "Sandbox SDK Key",
    api_key_environment: "sandbox",
    api_key_rate_limit: 120,
    oauth_code_challenge: "",
    oauth_code_challenge_method: "S256",
    webhook_name: "Event Updates",
    webhook_url: "https://sync.example/webhooks/afrolete",
    webhook_events: "events.created,events.updated",
    webhook_delivery_mode: "webhook",
    listing_name: "Matchday Sync Connector",
    listing_category: "operations",
    listing_summary: "Synchronizes fixtures, attendance, and matchday logistics.",
    listing_install_url: "https://sync.example/install",
    listing_support_url: "https://sync.example/support"
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
  const assessmentReviewQueueSummary = useMemo(() => ({
    total: assessmentReviewQueue.length,
    overdue: assessmentReviewQueue.filter((item) => item.review_sla_state === "overdue").length,
    dueSoon: assessmentReviewQueue.filter((item) => item.review_sla_state === "due_soon").length,
    urgent: assessmentReviewQueue.filter((item) => item.assessment.review_priority === "urgent").length
  }), [assessmentReviewQueue]);
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
  const infrastructureReadyCount =
    infrastructureStatus?.components.filter((component) => infrastructureTone(component) === "ready").length ?? 0;
  const infrastructureAttentionCount =
    infrastructureStatus?.components.filter((component) => infrastructureTone(component) === "attention").length ?? 0;
  const infrastructureStandbyCount =
    infrastructureStatus?.components.filter((component) => infrastructureTone(component) === "standby").length ?? 0;
  const infrastructureProbeFailures =
    infrastructureProbes?.results.filter((result) => result.reachable === false).length ?? 0;
  const infrastructureProbeByKey = useMemo(
    () => new Map((infrastructureProbes?.results ?? []).map((result) => [result.key, result])),
    [infrastructureProbes]
  );

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

  const loadRegistrationInquiries = useCallback(
    async (organizationId: string) => {
      const data = await apiRequest<RegistrationInquiryRead[]>(
        `/organizations/${organizationId}/registration-inquiries`,
        { identity }
      );
      setRegistrationInquiries(data);
    },
    [identity]
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

  const loadWeatherAssessments = useCallback(async (eventId: string) => {
    const data = await apiRequest<EventWeatherAssessmentRead[]>(`/events/${eventId}/weather-assessments`);
    setWeatherAssessments(data);
  }, []);

  const loadTravelPlans = useCallback(async (eventId: string) => {
    const data = await apiRequest<EventTravelPlanRead[]>(`/events/${eventId}/travel-plans`);
    setTravelPlans(data);
  }, []);

  const loadSafeguardingIncidents = useCallback(async (organizationId: string) => {
    const data = await apiRequest<SafeguardingIncidentRead[]>(
      `/safeguarding/incidents?organization_id=${organizationId}`,
      { identity }
    );
    setSafeguardingIncidents(data);
  }, [identity]);

  const loadBackgroundChecks = useCallback(async (organizationId: string) => {
    const data = await apiRequest<BackgroundCheckRead[]>(
      `/safeguarding/background-checks?organization_id=${organizationId}`,
      { identity }
    );
    setBackgroundChecks(data);
  }, [identity]);

  const loadComplianceCredentials = useCallback(async (organizationId: string) => {
    const data = await apiRequest<ComplianceCredentialRead[]>(
      `/safeguarding/credentials?organization_id=${organizationId}`,
      { identity }
    );
    setComplianceCredentials(data);
  }, [identity]);

  const loadComplianceSummary = useCallback(async (organizationId: string) => {
    const data = await apiRequest<ComplianceSummaryRead>(
      `/safeguarding/compliance-summary?organization_id=${organizationId}`,
      { identity }
    );
    setComplianceSummary(data);
  }, [identity]);

  const loadIncidentReportPackages = useCallback(async (organizationId: string) => {
    const data = await apiRequest<IncidentReportPackageRead[]>(
      `/safeguarding/incident-report-packages?organization_id=${organizationId}`,
      { identity }
    );
    setIncidentReportPackages(data);
  }, [identity]);

  const loadIncidentInsuranceClaims = useCallback(async (organizationId: string) => {
    const data = await apiRequest<IncidentInsuranceClaimRead[]>(
      `/safeguarding/insurance-claims?organization_id=${organizationId}`,
      { identity }
    );
    setIncidentInsuranceClaims(data);
  }, [identity]);

  const loadIncidentMedicalClearances = useCallback(async (organizationId: string) => {
    const data = await apiRequest<IncidentMedicalClearanceRead[]>(
      `/safeguarding/medical-clearances?organization_id=${organizationId}`,
      { identity }
    );
    setIncidentMedicalClearances(data);
  }, [identity]);

  const loadAgents = useCallback(async (organizationId: string) => {
    const data = await apiRequest<AgentRead[]>(`/agents?organization_id=${organizationId}`);
    setAgents(data);
    setSelectedAgentId((current) =>
      data.some((agent) => agent.id === current) ? current : data[0]?.id ?? ""
    );
  }, []);

  const loadAgentTasks = useCallback(async (organizationId: string, agentId?: string) => {
    const query = agentId ? `&agent_id=${agentId}` : "";
    const [tasks, runs, governance, ledgerVerification, transparency, registry, biasAudits, appeals, scorecard, comments, publications, readiness, artifactAccesses, artifactAccessSummary] = await Promise.all([
      apiRequest<AgentTaskRead[]>(`/agents/tasks?organization_id=${organizationId}${query}`),
      apiRequest<AgentRunRecordRead[]>(`/agents/runs?organization_id=${organizationId}`),
      apiRequest<AgentGovernanceSummaryRead>(`/agents/governance?organization_id=${organizationId}`),
      apiRequest<AgentRunLedgerVerificationRead>(`/agents/runs/verify?organization_id=${organizationId}`),
      apiRequest<AgentModelTransparencyReportRead>(`/agents/model-transparency?organization_id=${organizationId}`),
      apiRequest<AgentModelRegistryRead[]>(`/agents/model-registry?organization_id=${organizationId}`),
      apiRequest<AgentBiasAuditRead[]>(`/agents/bias-audits?organization_id=${organizationId}`),
      apiRequest<AgentDecisionAppealRead[]>(`/agents/appeals?organization_id=${organizationId}`),
      apiRequest<AgentEthicalScorecardRead>(`/agents/ethical-scorecard?organization_id=${organizationId}`),
      apiRequest<AgentScorecardCommentModerationRead[]>(
        `/agents/ethical-scorecard/comments/moderation?organization_id=${organizationId}`,
        { identity }
      ),
      apiRequest<AgentScorecardPublicationRead[]>(
        `/agents/ethical-scorecard/publications?organization_id=${organizationId}`
      ),
      apiRequest<AgentScorecardPublicationReadinessRead>(
        `/agents/ethical-scorecard/publications/readiness?organization_id=${organizationId}`
      ),
      apiRequest<AgentScorecardArtifactAccessRead[]>(
        `/agents/ethical-scorecard/artifact-accesses?organization_id=${organizationId}`,
        { identity }
      ),
      apiRequest<AgentScorecardArtifactAccessSummaryRead>(
        `/agents/ethical-scorecard/artifact-accesses/summary?organization_id=${organizationId}`,
        { identity }
      )
    ]);
    setAgentTasks(tasks);
    setAgentRuns(runs);
    setAgentGovernance(governance);
    setAgentLedgerVerification(ledgerVerification);
    setAgentTransparency(transparency);
    setAgentModelRegistry(registry);
    setAgentBiasAudits(biasAudits);
    setAgentDecisionAppeals(appeals);
    setAgentEthicalScorecard(scorecard);
    setAgentScorecardComments(comments);
    setAgentScorecardPublications(publications);
    setAgentScorecardReadiness(readiness);
    setAgentScorecardArtifactAccesses(artifactAccesses);
    setAgentScorecardArtifactAccessSummary(artifactAccessSummary);
  }, [identity]);

  const loadMetricDefinitions = useCallback(async (organizationId: string) => {
    const data = await apiRequest<MetricDefinitionRead[]>(
      `/performance/metrics?organization_id=${organizationId}`
    );
    setMetricDefinitions(data);
  }, []);

  const loadAssessmentReviewQueue = useCallback(async (
    organizationId: string,
    filters: AssessmentReviewQueueFilters
  ) => {
    const params = new URLSearchParams({ organization_id: organizationId });
    if (filters.assignment !== "all") {
      params.set("assignment", filters.assignment);
    }
    if (filters.sla !== "all") {
      params.set("sla", filters.sla);
    }
    if (filters.priority !== "all") {
      params.set("priority", filters.priority);
    }
    const data = await apiRequest<AthleteAssessmentReviewQueueItemRead[]>(
      `/performance/assessments/review-queue?${params.toString()}`,
      { identity }
    );
    setAssessmentReviewQueue(data);
  }, [identity]);

  const loadAssessmentReviewSummary = useCallback(async (organizationId: string) => {
    const data = await apiRequest<AssessmentReviewQueueSummaryRead>(
      `/performance/assessments/review-summary?organization_id=${organizationId}`,
      { identity }
    );
    setAssessmentReviewSummary(data);
  }, [identity]);

  const loadPerformanceBenchmarkDatasets = useCallback(async (organizationId: string) => {
    const data = await apiRequest<PerformanceModelExtractionBenchmarkDatasetRead[]>(
      `/performance/model-extraction/benchmark-datasets?organization_id=${organizationId}`,
      { identity }
    );
    setPerformanceModelBenchmarkDatasets(data);
  }, [identity]);

  const loadPerformanceForecastValidationRuns = useCallback(async (organizationId: string, athleteProfileId?: string) => {
    const params = new URLSearchParams({ organization_id: organizationId, limit: "5" });
    if (athleteProfileId) {
      params.set("athlete_profile_id", athleteProfileId);
    }
    const data = await apiRequest<PerformanceForecastValidationRunRead[]>(
      `/performance/forecast-validation-runs?${params.toString()}`,
      { identity }
    );
    setPerformanceForecastValidationRuns(data);
    setPerformanceForecastValidationRun((current) =>
      current && data.some((run) => run.id === current.id) ? current : data[0] ?? null
    );
  }, [identity]);

  const loadAthletePerformance = useCallback(
    async (organizationId: string, athleteProfileId: string) => {
      const trendParams = new URLSearchParams({ organization_id: organizationId });
      if (performanceTrendPeriodStart) {
        trendParams.set("period_start", performanceTrendPeriodStart);
      }
      if (performanceTrendPeriodEnd) {
        trendParams.set("period_end", performanceTrendPeriodEnd);
      }
      if (performanceTrendCategory !== "all") {
        trendParams.set("category", performanceTrendCategory);
      }
      if (performanceTrendMetricCode.trim()) {
        trendParams.set("metric_code", performanceTrendMetricCode.trim().toLowerCase());
      }
      const [
        observationData,
        assessmentData,
        summaryData,
        benchmarkData,
        cohortComparisonData,
        trendData,
        trendSeriesData,
        forecastScenarioData,
        whatIfScenarioData,
        forecastValidationData,
        injuryRiskData,
        goalData,
        awardData,
        wearableConnectionData
      ] = await Promise.all([
        apiRequest<PerformanceObservationRead[]>(
          `/performance/athletes/${athleteProfileId}/observations?organization_id=${organizationId}`
        ),
        apiRequest<AthleteAssessmentRead[]>(
          `/performance/athletes/${athleteProfileId}/assessments?organization_id=${organizationId}`
        ),
        apiRequest<AthletePerformanceSummaryRead>(
          `/performance/athletes/${athleteProfileId}/summary?organization_id=${organizationId}`
        ),
        apiRequest<PerformanceMetricBenchmarkRead[]>(
          `/performance/athletes/${athleteProfileId}/benchmarks?organization_id=${organizationId}&cohort_scope=${performanceBenchmarkScope}`
        ),
        apiRequest<PerformanceCohortComparisonRead[]>(
          `/performance/athletes/${athleteProfileId}/cohort-comparisons?organization_id=${organizationId}`
        ),
        apiRequest<PerformanceMetricTrendRead[]>(
          `/performance/athletes/${athleteProfileId}/trends?${trendParams.toString()}`
        ),
        apiRequest<PerformanceMetricTrendSeriesRead[]>(
          `/performance/athletes/${athleteProfileId}/trend-series?${trendParams.toString()}`
        ),
        apiRequest<PerformanceForecastScenarioRead[]>(
          `/performance/athletes/${athleteProfileId}/forecast-scenarios?organization_id=${organizationId}`
        ),
        apiRequest<PerformanceForecastWhatIfRead[]>(
          `/performance/athletes/${athleteProfileId}/forecast-scenarios/what-if?organization_id=${organizationId}&training_adjustment_percent=${performanceWhatIfAdjustment}&readiness_score=${performanceWhatIfReadiness}`
        ),
        apiRequest<PerformanceForecastValidationRunRead[]>(
          `/performance/forecast-validation-runs?organization_id=${organizationId}&athlete_profile_id=${athleteProfileId}&limit=5`,
          { identity }
        ),
        apiRequest<PerformanceInjuryRiskRead>(
          `/performance/athletes/${athleteProfileId}/injury-risk?organization_id=${organizationId}`
        ),
        apiRequest<PerformanceGoalRead[]>(
          `/performance/athletes/${athleteProfileId}/goals?organization_id=${organizationId}`
        ),
        apiRequest<PerformanceAchievementAwardRead[]>(
          `/performance/athletes/${athleteProfileId}/awards?organization_id=${organizationId}`
        ),
        apiRequest<PerformanceWearableConnectionRead[]>(
          `/performance/wearable-connections?organization_id=${organizationId}&athlete_profile_id=${athleteProfileId}`,
          { identity }
        )
      ]);
      setObservations(observationData);
      setAssessments(assessmentData);
      setPerformanceSummary(summaryData);
      setPerformanceBenchmarks(benchmarkData);
      setPerformanceCohortComparisons(cohortComparisonData);
      setPerformanceTrends(trendData);
      setPerformanceTrendSeries(trendSeriesData);
      setPerformanceForecastScenarios(forecastScenarioData);
      setPerformanceWhatIfScenarios(whatIfScenarioData);
      setPerformanceForecastValidationRuns(forecastValidationData);
      setPerformanceForecastValidationRun(forecastValidationData[0] ?? null);
      setPerformanceInjuryRisk(injuryRiskData);
      setPerformanceGoals(goalData);
      setPerformanceAwards(awardData);
      setWearableConnections(wearableConnectionData);
      setSelectedObservationId((current) =>
        observationData.some((observation) => observation.id === current)
          ? current
          : observationData[0]?.id ?? ""
      );
    },
    [
      identity,
      performanceBenchmarkScope,
      performanceTrendCategory,
      performanceTrendMetricCode,
      performanceTrendPeriodEnd,
      performanceTrendPeriodStart,
      performanceWhatIfAdjustment,
      performanceWhatIfReadiness
    ]
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
      leaseScheduleData,
      emergencyPlanData,
      emergencyActivationData
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
      apiRequest<EquipmentLeaseScheduleRead[]>(`/assets/lease-schedules?organization_id=${organizationId}`),
      apiRequest<EmergencyActionPlanRead[]>(`/assets/emergency-plans?organization_id=${organizationId}`),
      apiRequest<EmergencyPlanActivationRead[]>(
        `/assets/emergency-activations?organization_id=${organizationId}`
      )
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
    setEmergencyPlans(emergencyPlanData);
    setEmergencyActivations(emergencyActivationData);
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
      dashboardData,
      payoutData
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
      ),
      apiRequest<CommercialSettlementPayoutRead[]>(`/commercial/settlements/payouts?organization_id=${organizationId}`)
    ]);
    setSponsors(sponsorData);
    setSponsorships(sponsorshipData);
    setCampaigns(campaignData);
    setTicketProducts(ticketProductData);
    setTickets(ticketData);
    setInvoices(invoiceData);
    setCommercialSummary(summaryData);
    setSponsorshipDashboard(dashboardData);
    setCommercialPayouts(payoutData);
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

  const loadDevelopers = useCallback(async (organizationId: string) => {
    const [applications, apiKeys, oauthAuthorizations, webhooks, deliveries, listings, catalog, summary] = await Promise.all([
      apiRequest<DeveloperApplicationRead[]>(`/developers/applications?organization_id=${organizationId}`, {
        identity
      }),
      apiRequest<DeveloperApiKeyRead[]>(`/developers/api-keys?organization_id=${organizationId}`, { identity }),
      apiRequest<DeveloperOAuthAuthorizationRead[]>(`/developers/oauth/authorizations?organization_id=${organizationId}`, {
        identity
      }),
      apiRequest<DeveloperWebhookSubscriptionRead[]>(
        `/developers/webhook-subscriptions?organization_id=${organizationId}`,
        { identity }
      ),
      apiRequest<DeveloperWebhookDeliveryRead[]>(
        `/developers/webhook-deliveries?organization_id=${organizationId}`,
        { identity }
      ),
      apiRequest<DeveloperMarketplaceListingRead[]>(
        `/developers/marketplace-listings?organization_id=${organizationId}`,
        { identity }
      ),
      apiRequest<DeveloperIntegrationCatalogRead>(`/developers/catalog?organization_id=${organizationId}`, {
        identity
      }),
      apiRequest<DeveloperPortalSummaryRead>(`/developers/summary?organization_id=${organizationId}`, {
        identity
      })
    ]);
    setDeveloperApplications(applications);
    setDeveloperApiKeys(apiKeys);
    setDeveloperOAuthAuthorizations(oauthAuthorizations);
    setDeveloperWebhooks(webhooks);
    setDeveloperWebhookDeliveries(deliveries);
    setDeveloperListings(listings);
    setDeveloperCatalog(catalog);
    setDeveloperSummary(summary);
  }, [identity]);

  const loadInfrastructure = useCallback(async () => {
    const [status, probes] = await Promise.all([
      apiRequest<InfrastructureStatus>("/infrastructure"),
      apiRequest<InfrastructureProbeSummary>("/infrastructure/probes")
    ]);
    setInfrastructureStatus(status);
    setInfrastructureProbes(probes);
    return { status, probes };
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
    runAction("load-infrastructure", loadInfrastructure, ({ status, probes }) => {
      const attentionCount = status.components.filter((component) => infrastructureTone(component) === "attention").length;
      const probeFailures = probes.results.filter((result) => result.reachable === false).length;
      addLog(
        attentionCount > 0 || probeFailures > 0
          ? `${attentionCount} configured dependency issue(s), ${probeFailures} live probe failure(s)`
          : "Infrastructure readiness synchronized",
        attentionCount > 0 || probeFailures > 0 ? "bad" : "good"
      );
    });
  }, [loadInfrastructure, runAction, addLog]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      setTeams([]);
      setEvents([]);
      setWeatherAssessments([]);
      setWeatherAlert(null);
      setWeatherAutomation(null);
      setTravelPlans([]);
      setTravelConsentBatch(null);
      setTravelConsentReminder(null);
      setTravelConsentReminderRun(null);
      setTravelManifest(null);
      setTravelOfflineManifestCache(null);
      setTravelManifestExport(null);
      setTravelManifestOfflineLink(null);
      setTravelFeeBatch(null);
      setTravelFeeCheckoutBatch(null);
      setTravelFeeReconciliation(null);
      setTravelApprovals([]);
      setTravelApprovalRouting(null);
      setTravelChecklistItems([]);
      setTravelLocationUpdates([]);
      setTravelTelemetryStream(null);
      setTravelDevices([]);
      setTravelDeviceSecret(null);
      setTravelDeviceFleetInventory(null);
      setTravelBackupDrivers([]);
      setTravelBackupDriverDispatch(null);
      setTravelDriverMarketplace(null);
      setTravelDriverRatings([]);
      setTravelDriverRatingSummary(null);
      setTravelExpenses([]);
      setTravelExpensePayout(null);
      setTravelCarpoolRides([]);
      setTravelCarpoolAutoMatch(null);
      setTravelReadiness(null);
      setTravelRouteOptimization(null);
      setTravelRouteMap(null);
      setTravelGeofenceCheck(null);
      setTravelGeofenceZones([]);
      setAgents([]);
      setAgentTasks([]);
      setAgentRuns([]);
      setAgentLedgerVerification(null);
      setAgentGovernance(null);
      setAgentTransparency(null);
      setAgentModelRegistry([]);
      setAgentBiasAudits([]);
      setAgentDecisionAppeals([]);
      setAgentEthicalScorecard(null);
      setAgentScorecardComments([]);
      setAgentScorecardPublications([]);
      setAgentScorecardReadiness(null);
      setAgentScorecardReminder(null);
      setAgentScorecardReminderRun(null);
      setAgentScorecardAutomationRun(null);
      setAgentScorecardArtifactLink(null);
      setAgentScorecardArtifactAccesses([]);
      setAgentScorecardArtifactAccessSummary(null);
      setAgentScorecardArtifactAnomalyAlert(null);
      setAgentScorecardArtifactAnomalyAlertRun(null);
      setMetricDefinitions([]);
      setObservations([]);
      setPerformanceIngestion(null);
      setPerformanceModelBenchmark(null);
      setPerformanceModelBenchmarkDatasets([]);
      setPerformanceForecastValidationRun(null);
      setPerformanceForecastValidationRuns([]);
      setPerformanceForecastValidationAlert(null);
      setPerformanceWebhookIngest(null);
      setWearableConnections([]);
      setWearableSyncRun(null);
      setWearableOAuthStart(null);
      setWearableOAuthCallback(null);
      setWearableTokenRefresh(null);
      setWearableWebhookRegistration(null);
      setAssessments([]);
      setAssessmentReviewQueue([]);
      setAssessmentReviewSummary(null);
      setPerformanceReviewEscalationRun(null);
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
      setRegistrationInquiries([]);
      setSafeguardingIncidents([]);
      setBackgroundChecks([]);
      setComplianceCredentials([]);
      setComplianceSummary(null);
      setIncidentReportPackages([]);
      setIncidentInsuranceClaims([]);
      setIncidentMedicalClearances([]);
      setCommunicationTemplates([]);
      setCommunicationMessages([]);
      setMessageRecipients([]);
      setInboxItems([]);
      setDigestSummary(null);
      setDigestRun(null);
      setDraftPreview(null);
      setEscalationRun(null);
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
      setCommercialTaxFiling(null);
      setPaymentSettlement(null);
      setCommercialPayout(null);
      setCommercialPayouts([]);
      setAccountingExport(null);
      setAccountingSync(null);
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
      setDeveloperApplications([]);
      setDeveloperApiKeys([]);
      setDeveloperOAuthAuthorizations([]);
      setDeveloperOAuthGrant(null);
      setDeveloperWebhooks([]);
      setDeveloperWebhookDeliveries([]);
      setDeveloperWebhookRetryRun(null);
      setDeveloperListings([]);
      setDeveloperCatalog(null);
      setDeveloperSummary(null);
      setDeveloperApplicationSecret(null);
      setDeveloperApiKeySecret(null);
      setDeveloperWebhookSecret(null);
      return;
    }
    runAction("load-tenant-data", async () => {
      await loadTeams(selectedOrganizationId);
      await loadRegistrationInquiries(selectedOrganizationId);
      await loadEvents(selectedOrganizationId);
      await loadSafeguardingIncidents(selectedOrganizationId);
      await loadBackgroundChecks(selectedOrganizationId);
      await loadComplianceCredentials(selectedOrganizationId);
      await loadComplianceSummary(selectedOrganizationId);
      await loadIncidentReportPackages(selectedOrganizationId);
      await loadIncidentInsuranceClaims(selectedOrganizationId);
      await loadIncidentMedicalClearances(selectedOrganizationId);
      await loadAgents(selectedOrganizationId);
      await loadAgentTasks(selectedOrganizationId);
      await loadMetricDefinitions(selectedOrganizationId);
      await loadPerformanceBenchmarkDatasets(selectedOrganizationId);
      await loadTraining(selectedOrganizationId);
      await loadCompetitions(selectedOrganizationId);
      await loadCommunications(selectedOrganizationId);
      await loadAssets(selectedOrganizationId);
      await loadCommercial(selectedOrganizationId);
      await loadReporting(selectedOrganizationId);
      await loadBilling(selectedOrganizationId);
      await loadDevelopers(selectedOrganizationId);
    }, () => addLog("Organization workspace loaded", "good"));
  }, [
    selectedOrganizationId,
    loadTeams,
    loadRegistrationInquiries,
    loadEvents,
    loadSafeguardingIncidents,
    loadBackgroundChecks,
    loadComplianceCredentials,
    loadComplianceSummary,
    loadIncidentReportPackages,
    loadIncidentInsuranceClaims,
    loadIncidentMedicalClearances,
    loadAgents,
    loadAgentTasks,
    loadMetricDefinitions,
    loadPerformanceBenchmarkDatasets,
    loadTraining,
    loadCompetitions,
    loadCommunications,
    loadAssets,
    loadCommercial,
    loadReporting,
    loadBilling,
    loadDevelopers,
    runAction,
    addLog
  ]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "load-assessment-review-queue",
      async () => {
        await loadAssessmentReviewQueue(selectedOrganizationId, assessmentReviewQueueFilters);
        await loadAssessmentReviewSummary(selectedOrganizationId);
      },
      () => undefined
    );
  }, [
    selectedOrganizationId,
    assessmentReviewQueueFilters,
    loadAssessmentReviewQueue,
    loadAssessmentReviewSummary,
    runAction
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
      setWeatherAssessments([]);
      setWeatherAlert(null);
      setWeatherAutomation(null);
      setTravelPlans([]);
      setTravelConsentBatch(null);
      setTravelConsentReminder(null);
      setTravelConsentReminderRun(null);
      setTravelManifest(null);
      setTravelOfflineManifestCache(null);
      setTravelManifestExport(null);
      setTravelManifestOfflineLink(null);
      setTravelFeeBatch(null);
      setTravelFeeCheckoutBatch(null);
      setTravelFeeReconciliation(null);
      setTravelApprovals([]);
      setTravelApprovalRouting(null);
      setTravelChecklistItems([]);
      setTravelLocationUpdates([]);
      setTravelTelemetryStream(null);
      setTravelDevices([]);
      setTravelDeviceSecret(null);
      setTravelDeviceFleetInventory(null);
      setTravelBackupDrivers([]);
      setTravelBackupDriverDispatch(null);
      setTravelDriverMarketplace(null);
      setTravelDriverRatings([]);
      setTravelDriverRatingSummary(null);
      setTravelExpenses([]);
      setTravelExpensePayout(null);
      setTravelCarpoolRides([]);
      setTravelCarpoolAutoMatch(null);
      setTravelReadiness(null);
      setTravelRouteOptimization(null);
      setTravelRouteMap(null);
      setTravelGeofenceCheck(null);
      setTravelGeofenceZones([]);
      return;
    }
    runAction(
      "load-event-readiness",
      async () => {
        await loadAttendance(selectedEventId);
        await loadWeatherAssessments(selectedEventId);
        await loadTravelPlans(selectedEventId);
      },
      () => undefined
    );
  }, [selectedEventId, loadAttendance, loadTravelPlans, loadWeatherAssessments, runAction]);

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
      setPerformanceBenchmarks([]);
      setPerformanceCohortComparisons([]);
      setPerformanceTrends([]);
      setPerformanceTrendSeries([]);
      setPerformanceForecastScenarios([]);
      setPerformanceWhatIfScenarios([]);
      setPerformanceForecastValidationRun(null);
      setPerformanceForecastValidationRuns([]);
      setPerformanceForecastValidationAlert(null);
      setPerformanceInjuryRisk(null);
      setPerformanceInjuryRiskAlert(null);
      setPerformanceInjuryRiskAlertRun(null);
      setPerformanceGoals([]);
      setPerformanceAwards([]);
      setPerformanceAchievementRun(null);
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
            country_code: athleteForm.country_code,
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

  const updateInquiryReviewForm = (
    inquiry: RegistrationInquiryRead,
    field: keyof InquiryReviewForm,
    value: string
  ) => {
    setInquiryReviewForms((current) => {
      const existing = current[inquiry.id] ?? {
        status: inquiry.status,
        review_notes: inquiry.review_notes ?? "",
        follow_up_at: toDateTimeLocalValue(inquiry.follow_up_at)
      };
      return {
        ...current,
        [inquiry.id]: {
          ...existing,
          [field]: value
        }
      };
    });
  };

  const updateRegistrationInquiryReview = (inquiry: RegistrationInquiryRead, statusOverride?: string) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const form = inquiryReviewForms[inquiry.id];
    const nextStatus = statusOverride ?? form?.status ?? inquiry.status;
    const followUpValue = form ? form.follow_up_at : toDateTimeLocalValue(inquiry.follow_up_at);
    const body: {
      status?: string;
      review_notes: string | null;
      follow_up_at: string | null;
    } = {
      review_notes: form ? form.review_notes || null : inquiry.review_notes,
      follow_up_at: followUpValue ? new Date(followUpValue).toISOString() : null
    };
    if (nextStatus !== "converted") {
      body.status = nextStatus;
    }
    runAction(
      `review-registration-inquiry-${inquiry.id}`,
      () =>
        apiRequest<RegistrationInquiryRead>(
          `/organizations/${selectedOrganizationId}/registration-inquiries/${inquiry.id}`,
          {
            method: "PATCH",
            identity,
            body
          }
        ),
      (updated) => {
        setRegistrationInquiries((current) =>
          current.map((item) => (item.id === updated.id ? updated : item))
        );
        setInquiryReviewForms((current) => ({
          ...current,
          [updated.id]: {
            status: updated.status,
            review_notes: updated.review_notes ?? "",
            follow_up_at: toDateTimeLocalValue(updated.follow_up_at)
          }
        }));
        addLog(`${updated.athlete_name} inquiry moved to ${updated.status}`, "good");
      }
    );
  };

  const sendRegistrationInquiryFollowUp = (inquiry: RegistrationInquiryRead) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const form = inquiryReviewForms[inquiry.id];
    const notes = form?.review_notes || inquiry.review_notes || "";
    const subject = `Registration follow-up for ${inquiry.athlete_name}`;
    const body = [
      `Hello ${inquiry.guardian_name || inquiry.athlete_name},`,
      "",
      `Thank you for your interest in ${selectedOrganization?.public_name || selectedOrganization?.name || "our program"}.`,
      inquiry.sport_interest ? `Sport/program: ${inquiry.sport_interest}.` : null,
      inquiry.age_group ? `Age group: ${inquiry.age_group}.` : null,
      notes ? `Notes from our team: ${notes}` : null,
      "",
      "Please reply with any availability, medical, or registration questions so we can complete the intake."
    ].filter(Boolean).join("\n");
    runAction(
      `follow-up-registration-inquiry-${inquiry.id}`,
      () =>
        apiRequest<RegistrationInquiryFollowUpRead>(
          `/organizations/${selectedOrganizationId}/registration-inquiries/${inquiry.id}/follow-up`,
          {
            method: "POST",
            identity,
            body: {
              channel: "email",
              subject,
              body,
              urgent: false,
              quiet_hours_override: false
            }
          }
        ),
      (result) => {
        setRegistrationInquiries((current) =>
          current.map((item) => (item.id === result.inquiry.id ? result.inquiry : item))
        );
        setInquiryReviewForms((current) => ({
          ...current,
          [result.inquiry.id]: {
            status: result.inquiry.status,
            review_notes: result.inquiry.review_notes ?? "",
            follow_up_at: toDateTimeLocalValue(result.inquiry.follow_up_at)
          }
        }));
        setCommunicationMessages((current) => [
          result.message,
          ...current.filter((item) => item.id !== result.message.id)
        ]);
        setSelectedMessageId(result.message.id);
        addLog(`Follow-up queued for ${result.inquiry.athlete_name}`, "good");
      }
    );
  };

  const convertRegistrationInquiry = (inquiry: RegistrationInquiryRead) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `convert-registration-inquiry-${inquiry.id}`,
      () =>
        apiRequest<RegistrationInquiryConversionRead>(
          `/organizations/${selectedOrganizationId}/registration-inquiries/${inquiry.id}/convert`,
          {
            method: "POST",
            identity,
            body: {
              team_id: inquiry.team_id || selectedTeamId || null,
              role: "player",
              create_guardian: true
            }
          }
        ),
      (conversion) => {
        setRegistrationInquiries((current) =>
          current.map((item) => (item.id === conversion.inquiry.id ? conversion.inquiry : item))
        );
        setInquiryReviewForms((current) => ({
          ...current,
          [conversion.inquiry.id]: {
            status: conversion.inquiry.status,
            review_notes: conversion.inquiry.review_notes ?? "",
            follow_up_at: toDateTimeLocalValue(conversion.inquiry.follow_up_at)
          }
        }));
        setAthletes((current) => [
          {
            personId: conversion.athlete_person_id,
            athleteProfileId: conversion.athlete_profile_id,
            name: conversion.inquiry.athlete_name,
            email: conversion.inquiry.email,
            rosterEntryId: conversion.roster_entry_id ?? undefined
          },
          ...current.filter((item) => item.personId !== conversion.athlete_person_id)
        ]);
        setSelectedAthleteId(conversion.athlete_person_id);
        addLog(`${conversion.inquiry.athlete_name} converted from inquiry`, "good");
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

  const assessEventWeather = () => {
    if (!selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      "assess-event-weather",
      () =>
        apiRequest<EventWeatherAssessmentRead>(`/events/${selectedEventId}/weather-assessments`, {
          method: "POST",
          identity,
          body: {
            source: weatherForm.source,
            observed_at: new Date(weatherForm.observed_at).toISOString(),
            temperature_c: weatherForm.temperature_c,
            heat_index_c: weatherForm.heat_index_c,
            wbgt_c: weatherForm.wbgt_c,
            humidity_percent: weatherForm.humidity_percent,
            aqi: weatherForm.aqi,
            lightning_distance_km: weatherForm.lightning_distance_km,
            wind_speed_kph: weatherForm.wind_speed_kph,
            wind_gust_kph: weatherForm.wind_gust_kph,
            precipitation_mm_per_hr: weatherForm.precipitation_mm_per_hr,
            notes: weatherForm.notes || null
          }
        }),
      (assessment) => {
        setWeatherAssessments((current) => [
          assessment,
          ...current.filter((item) => item.id !== assessment.id)
        ]);
        addLog(
          `Weather ${assessment.alert_level}: ${assessment.decision}`,
          assessment.alert_level === "critical" || assessment.alert_level === "warning" ? "bad" : "good"
        );
      }
    );
  };

  const dispatchWeatherAlert = (assessment: EventWeatherAssessmentRead) => {
    runAction(
      `weather-alert-${assessment.id}`,
      () =>
        apiRequest<EventWeatherAlertRead>(
          `/events/${assessment.event_id}/weather-assessments/${assessment.id}/alerts`,
          {
            method: "POST",
            identity,
            body: {
              channel: weatherForm.alert_channel,
              copy_guardians_for_minors: true
            }
          }
        ),
      (alert) => {
        setWeatherAlert(alert);
        setSelectedMessageId(alert.message_id);
        addLog(`Weather alert sent to ${alert.recipient_count} recipients`, "bad");
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
      }
    );
  };

  const runWeatherAutomation = () => {
    if (!selectedEventId) {
      addLog("Select an event before running weather automation", "bad");
      return;
    }
    runAction(
      `weather-automation-${selectedEventId}`,
      () =>
        apiRequest<EventWeatherAutomationRunRead>(`/events/${selectedEventId}/weather-automation/run`, {
          method: "POST",
          identity,
          body: {
            channel: weatherForm.alert_channel,
            minimum_alert_level: "warning",
            copy_guardians_for_minors: true,
            include_existing_alerts: false,
            dry_run: false
          }
        }),
      (automation) => {
        setWeatherAutomation(automation);
        addLog(
          `Weather automation dispatched ${automation.dispatched_count}, skipped ${automation.skipped_count}`,
          automation.dispatched_count > 0 ? "bad" : "neutral"
        );
        if (selectedOrganizationId && automation.dispatched_count > 0) {
          void loadCommunications(selectedOrganizationId);
        }
      }
    );
  };

  const createTravelPlan = () => {
    if (!selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      "create-travel-plan",
      () =>
        apiRequest<EventTravelPlanRead>(`/events/${selectedEventId}/travel-plans`, {
          method: "POST",
          identity,
          body: {
            destination: travelForm.destination,
            travel_mode: travelForm.travel_mode,
            departure_at: travelForm.departure_at ? new Date(travelForm.departure_at).toISOString() : null,
            return_at: travelForm.return_at ? new Date(travelForm.return_at).toISOString() : null,
            route_summary: travelForm.route_summary || null,
            vehicle_details: travelForm.vehicle_details || null,
            driver_details: travelForm.driver_details || null,
            staff_manifest: travelForm.staff_manifest || null,
            passenger_manifest: travelForm.passenger_manifest || null,
            lodging_details: travelForm.lodging_details || null,
            meal_plan: travelForm.meal_plan || null,
            equipment_manifest: travelForm.equipment_manifest || null,
            emergency_contacts: travelForm.emergency_contacts || null,
            medical_access_plan: travelForm.medical_access_plan || null,
            route_weather_risk: travelForm.route_weather_risk || null,
            driver_certification_status: travelForm.driver_certification_status || null,
            vehicle_inspection_status: travelForm.vehicle_inspection_status || null,
            consent_required: travelForm.consent_required,
            consent_due_at: travelForm.consent_due_at ? new Date(travelForm.consent_due_at).toISOString() : null,
            estimated_cost: travelForm.estimated_cost,
            cost_per_participant: travelForm.cost_per_participant,
            notes: travelForm.notes || null
          }
        }),
      (plan) => {
        setTravelPlans((current) => [plan, ...current.filter((item) => item.id !== plan.id)]);
        addLog(`Travel plan ${plan.risk_level} risk`, plan.risk_level === "critical" || plan.risk_level === "high" ? "bad" : "good");
      }
    );
  };

  const updateTravelPlan = (plan: EventTravelPlanRead, statusValue: TravelPlanStatus) => {
    runAction(
      `travel-plan-${plan.id}-${statusValue}`,
      () =>
        apiRequest<EventTravelPlanRead>(`/events/travel-plans/${plan.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            route_weather_risk: travelForm.route_weather_risk || null,
            driver_certification_status: travelForm.driver_certification_status || null,
            vehicle_inspection_status: travelForm.vehicle_inspection_status || null,
            notes: `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setTravelPlans((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`Travel plan moved to ${updated.status} with ${updated.risk_level} risk`, "good");
      }
    );
  };

  const checkTravelReadiness = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-readiness-${plan.id}`,
      () =>
        apiRequest<EventTravelReadinessRead>(`/events/travel-plans/${plan.id}/readiness`, {
          identity
        }),
      (readiness) => {
        setTravelReadiness(readiness);
        addLog(
          readiness.ready
            ? `${plan.destination} is ready for departure`
            : `${readiness.blockers.length} departure blocker(s) found`,
          readiness.ready ? "good" : "bad"
        );
      }
    );
  };

  const optimizeTravelRoute = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-route-optimization-${plan.id}`,
      () =>
        apiRequest<EventTravelRouteOptimizationRead>(`/events/travel-plans/${plan.id}/route-optimization`, {
          method: "POST",
          identity,
          body: {
            strategy: travelForm.route_strategy,
            include_carpools: true,
            avoid_weather_risk: true
          }
        }),
      (optimization) => {
        setTravelRouteOptimization(optimization);
        addLog(
          optimization.reroute_required
            ? `Reroute advised: ${optimization.recommended_strategy}, ${optimization.estimated_duration_minutes} min`
            : `Route optimized: ${optimization.stop_count} stops, ${optimization.estimated_duration_minutes} min`,
          optimization.reroute_required || optimization.risk_level === "high" || optimization.risk_level === "critical" ? "bad" : "good"
        );
      }
    );
  };

  const loadTravelRouteMap = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-route-map-${plan.id}`,
      () =>
        apiRequest<EventTravelMapRead>(`/events/travel-plans/${plan.id}/route-map`, {
          identity
        }),
      (routeMap) => {
        setTravelRouteMap(routeMap);
        addLog(
          `Route map loaded: ${routeMap.path.length} points, ${routeMap.markers.length} markers`,
          routeMap.path.length ? "good" : "neutral"
        );
      }
    );
  };

  const requestTravelConsents = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-consents-${plan.id}`,
      () =>
        apiRequest<EventTravelConsentBatchRead>(`/events/travel-plans/${plan.id}/consent-requests`, {
          method: "POST",
          identity,
          body: {
            channel: travelForm.consent_channel,
            expires_at: travelForm.consent_due_at ? new Date(travelForm.consent_due_at).toISOString() : null,
            include_unknown_age: true,
            notes: null
          }
        }),
      (batch) => {
        setTravelConsentBatch(batch);
        addLog(
          `Travel consents: ${batch.created} created, ${batch.existing} existing`,
          batch.skipped_no_guardian > 0 ? "bad" : "good"
        );
      }
    );
  };

  const remindTravelConsents = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-consent-reminders-${plan.id}`,
      () =>
        apiRequest<EventTravelConsentReminderRead>(`/events/travel-plans/${plan.id}/consent-reminders`, {
          method: "POST",
          identity,
          body: {
            channel: travelForm.reminder_channel,
            subject: null,
            body: null
          }
        }),
      (reminder) => {
        setTravelConsentReminder(reminder);
        setSelectedMessageId(reminder.message_id);
        addLog(
          `Travel consent reminder sent to ${reminder.recipient_count} guardians`,
          reminder.recipient_count > 0 ? "good" : "bad"
        );
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
      }
    );
  };

  const runTravelConsentReminderAutomation = () => {
    if (!selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      `travel-consent-reminder-run-${selectedEventId}`,
      () =>
        apiRequest<EventTravelConsentReminderRunRead>(`/events/${selectedEventId}/travel-consent-reminder-run`, {
          method: "POST",
          identity,
          body: {
            channel: travelForm.reminder_channel,
            due_within_hours: 48,
            send_reminders: true,
            subject: null,
            body: null
          }
        }),
      (run) => {
        setTravelConsentReminderRun(run);
        if (run.message_id) {
          setSelectedMessageId(run.message_id);
        }
        addLog(
          `Travel reminder run: ${run.due_plan_count} due plans, ${run.recipient_count} recipients`,
          run.recipient_count > 0 ? "good" : "neutral"
        );
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
      }
    );
  };

  const loadTravelManifest = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-manifest-${plan.id}`,
      () =>
        apiRequest<EventTravelManifestRead>(`/events/travel-plans/${plan.id}/manifest`, {
          identity
        }),
      (manifest) => {
        setTravelManifest(manifest);
        addLog(`Travel manifest loaded for ${manifest.participant_count} participants`, "good");
      }
    );
  };

  const writeTravelManifestOfflineCache = async (manifest: EventTravelManifestRead) => {
    const cache = await encryptTravelManifestOfflineCache(manifest, identity);
    localStorage.setItem(travelManifestCacheKey(manifest.travel_plan_id), JSON.stringify(cache));
    setTravelManifest(manifest);
    setTravelOfflineManifestCache(cache);
    return cache;
  };

  const cacheTravelManifestOffline = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-manifest-offline-cache-${plan.id}`,
      async () => {
        const manifest = await apiRequest<EventTravelManifestRead>(`/events/travel-plans/${plan.id}/manifest`, {
          identity
        });
        return writeTravelManifestOfflineCache(manifest);
      },
      (cache) => {
        addLog(
          `Encrypted travel manifest cache saved for ${cache.participant_count} participants until ${new Date(cache.expires_at).toLocaleDateString()}`,
          "good"
        );
      }
    );
  };

  const restoreTravelManifestOffline = (plan: EventTravelPlanRead) => {
    const cached = localStorage.getItem(travelManifestCacheKey(plan.id));
    if (!cached) {
      setTravelOfflineManifestCache(null);
      addLog(`No offline manifest cache found for ${plan.destination}`, "neutral");
      return;
    }
    try {
      const parsed = JSON.parse(cached) as TravelManifestOfflineCache;
      const expiresAt = getTravelManifestOfflineCacheExpiry(parsed);
      if (new Date(expiresAt).getTime() <= Date.now()) {
        localStorage.removeItem(travelManifestCacheKey(plan.id));
        setTravelOfflineManifestCache(null);
        addLog(`Offline manifest cache for ${plan.destination} expired and has been cleared`, "neutral");
        return;
      }
      runAction(
        `travel-manifest-offline-restore-${plan.id}`,
        () =>
          isTravelManifestEncryptedOfflineCache(parsed)
            ? decryptTravelManifestOfflineCache(parsed, identity)
            : Promise.resolve(parsed),
        (manifest) => {
          setTravelManifest(manifest);
          setTravelOfflineManifestCache(parsed);
          addLog(
            `Offline manifest restored from ${new Date(parsed.cached_at).toLocaleString()} with cache expiry ${new Date(expiresAt).toLocaleDateString()}`,
            "good"
          );
        }
      );
    } catch {
      localStorage.removeItem(travelManifestCacheKey(plan.id));
      setTravelOfflineManifestCache(null);
      addLog(`Offline manifest cache for ${plan.destination} was invalid and has been cleared`, "bad");
    }
  };

  const exportTravelManifest = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-manifest-export-${plan.id}`,
      () =>
        apiRequest<EventTravelManifestExportRead>(`/events/travel-plans/${plan.id}/manifest/export`, {
          method: "POST",
          identity,
          body: {
            format: "csv"
          }
        }),
      (manifestExport) => {
        setTravelManifestExport(manifestExport);
        addLog(`Travel manifest export ready: ${manifestExport.filename}`, "good");
      }
    );
  };

  const createTravelManifestOfflineLink = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-manifest-offline-link-${plan.id}`,
      () =>
        apiRequest<EventTravelManifestOfflineLinkRead>(`/events/travel-plans/${plan.id}/manifest/offline-link`, {
          method: "POST",
          identity,
          body: {
            format: "pdf",
            ttl_seconds: 3600
          }
        }),
      (link) => {
        setTravelManifestOfflineLink(link);
        addLog(`Travel manifest PDF link ready until ${new Date(link.expires_at).toLocaleTimeString()}`, "good");
      }
    );
  };

  const generateTravelFeeInvoices = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-fee-invoices-${plan.id}`,
      () =>
        apiRequest<EventTravelFeeInvoiceBatchRead>(`/events/travel-plans/${plan.id}/fee-invoices`, {
          method: "POST",
          identity,
          body: {
            amount_per_participant: String(travelForm.cost_per_participant),
            currency: "USD",
            due_on: travelForm.consent_due_at ? travelForm.consent_due_at.slice(0, 10) : null,
            bill_guardians_for_minors: true,
            memo: null
          }
        }),
      (batch) => {
        setTravelFeeBatch(batch);
        setInvoices((current) => [
          ...current,
          ...batch.invoices
            .filter((invoice) => !current.some((item) => item.id === invoice.invoice_id))
            .map((invoice) => ({
              id: invoice.invoice_id,
              organization_id: selectedOrganizationId,
              person_id: invoice.billed_person_id,
              team_id: selectedTeamId || null,
              sponsor_id: null,
              invoice_number: invoice.invoice_number,
              title: `Travel fee: ${selectedEvent?.title ?? "event"}`,
              amount_due: invoice.amount_due,
              amount_paid: "0.00",
              currency: "USD",
              due_on: travelForm.consent_due_at ? travelForm.consent_due_at.slice(0, 10) : null,
              status: invoice.status as CommercialStatus,
              memo: `Travel fee for ${plan.destination}`
            }))
        ]);
        addLog(
          `Travel fees: ${batch.created} invoices created, ${batch.existing} existing`,
          batch.skipped_no_payer > 0 ? "bad" : "good"
        );
        if (selectedOrganizationId) {
          void loadCommercial(selectedOrganizationId);
        }
      }
    );
  };

  const createTravelFeeCheckouts = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-fee-checkouts-${plan.id}`,
      () =>
        apiRequest<EventTravelFeeCheckoutBatchRead>(`/events/travel-plans/${plan.id}/fee-checkouts`, {
          method: "POST",
          identity,
          body: {
            provider: "manual_gateway",
            checkout_base_url: "/pay/invoices",
            session_base_url: "/pay/sessions",
            success_url: "/pay/travel/success",
            cancel_url: "/pay/travel/cancelled",
            expires_at: travelForm.consent_due_at ? new Date(travelForm.consent_due_at).toISOString() : null
          }
        }),
      (batch) => {
        setTravelFeeCheckoutBatch(batch);
        addLog(`Travel payment links ready: ${batch.checkout_count}`, batch.checkout_count > 0 ? "good" : "bad");
      }
    );
  };

  const reconcileTravelFeePayments = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-fee-reconciliation-${plan.id}`,
      () =>
        apiRequest<EventTravelFeeReconciliationRead>(
          `/events/travel-plans/${plan.id}/fee-reconciliation?provider=manual_gateway`,
          { identity }
        ),
      (reconciliation) => {
        setTravelFeeReconciliation(reconciliation);
        addLog(
          `Travel fee reconciliation: ${reconciliation.paid_count} paid, ${reconciliation.exception_count} exceptions`,
          reconciliation.exception_count > 0 ? "bad" : Number(reconciliation.total_open) > 0 ? "neutral" : "good"
        );
      }
    );
  };

  const resolveTravelFeeException = (travelPlanId: string) => {
    if (!travelFeeReconciliation?.exceptions.length) {
      addLog("No travel fee reconciliation exceptions to resolve", "neutral");
      return;
    }
    const exception = travelFeeReconciliation.exceptions[0];
    const item =
      travelFeeReconciliation.items.find((entry) => entry.invoice_id === exception.invoice_id) ??
      (exception.code === "ledger_total_mismatch"
        ? travelFeeReconciliation.items.find((entry) => {
            const paymentTotal = entry.payments.reduce((total, payment) => total + Number(payment.amount), 0);
            return paymentTotal.toFixed(2) !== Number(entry.amount_paid).toFixed(2);
          })
        : undefined);
    if (!item) {
      addLog("Select a travel fee invoice exception first", "bad");
      return;
    }
    const unresolvedPayment = item.payments.find((payment) => !payment.external_reference);
    const currencyMismatchPayment = item.payments.find((payment) => payment.currency !== item.currency);
    const action =
      exception.code === "missing_provider_reference"
        ? "attach_payment_reference"
        : exception.code === "payment_currency_mismatch"
          ? "rebook_payment_currency"
          : exception.code === "paid_without_payment_row"
            ? "rebuild_missing_payment"
            : exception.code === "overpaid_invoice"
              ? "refund_overpayment"
              : exception.code === "overdue_open_balance"
                ? "apply_waiver"
                : exception.code === "invoice_payment_total_mismatch" || exception.code === "ledger_total_mismatch"
                  ? "sync_invoice_paid_total"
                  : "";
    if (!action) {
      addLog(`${exception.code} requires finance review before automatic resolution`, "neutral");
      return;
    }
    if (action === "attach_payment_reference" && !unresolvedPayment) {
      addLog("No payment row needs a provider reference", "neutral");
      return;
    }
    if (action === "rebook_payment_currency" && !currencyMismatchPayment) {
      addLog("No payment row needs currency rebooking", "neutral");
      return;
    }
    runAction(
      `travel-fee-resolve-${travelPlanId}`,
      () =>
        apiRequest<EventTravelFeeReconciliationResolutionRead>(
          `/events/travel-plans/${travelPlanId}/fee-reconciliation/resolve?provider=${travelFeeReconciliation.provider}`,
          {
            method: "POST",
            identity,
            body: {
              invoice_id: item.invoice_id,
              action,
              payment_id:
                action === "attach_payment_reference"
                  ? unresolvedPayment?.payment_id ?? null
                  : action === "rebook_payment_currency"
                    ? currencyMismatchPayment?.payment_id ?? null
                    : null,
              amount: action === "apply_waiver" ? item.open_amount : null,
              external_reference: `TRAVEL-RES-${Date.now()}`,
              notes: `Resolved ${exception.code} from operations console.`
            }
          }
        ),
      (resolution) => {
        setTravelFeeReconciliation(resolution.reconciliation);
        addLog(resolution.message, resolution.reconciliation.exception_count > 0 ? "neutral" : "good");
      }
    );
  };

  const loadTravelApprovals = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-approvals-${plan.id}`,
      () => apiRequest<EventTravelApprovalRead[]>(`/events/travel-plans/${plan.id}/approvals`, { identity }),
      (approvals) => {
        setTravelApprovals(approvals);
        addLog(`Travel approvals loaded: ${approvals.length}`, "good");
      }
    );
  };

  const createTravelApproval = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-approval-create-${plan.id}`,
      () =>
        apiRequest<EventTravelApprovalRead>(`/events/travel-plans/${plan.id}/approvals`, {
          method: "POST",
          identity,
          body: {
            approval_level: travelForm.approval_level,
            approver_person_id: null,
            notes: `Approval required before ${plan.destination} travel.`
          }
        }),
      (approval) => {
        setTravelApprovals((current) => [
          approval,
          ...current.filter((item) => item.id !== approval.id)
        ]);
        addLog(`${approval.approval_level} travel approval opened`, "good");
      }
    );
  };

  const routeTravelApprovals = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-approval-routing-${plan.id}`,
      () =>
        apiRequest<EventTravelApprovalRoutingRead>(`/events/travel-plans/${plan.id}/approval-routing`, {
          method: "POST",
          identity,
          body: {
            include_school: true,
            include_association: true,
            include_operations: true,
            include_medical: true,
            include_finance: true,
            notes: `Routed from the operations console for ${plan.destination}.`
          }
        }),
      (routing) => {
        setTravelApprovalRouting(routing);
        setTravelApprovals(routing.approvals);
        addLog(
          `Travel approvals routed: ${routing.created} created, ${routing.existing} existing`,
          routing.created > 0 ? "good" : "neutral"
        );
      }
    );
  };

  const decideTravelApproval = (approval: EventTravelApprovalRead, statusValue: "approved" | "rejected") => {
    runAction(
      `travel-approval-${approval.id}-${statusValue}`,
      () =>
        apiRequest<EventTravelApprovalRead>(`/events/travel-approvals/${approval.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            notes: `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setTravelApprovals((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.approval_level} approval ${updated.status}`, updated.status === "approved" ? "good" : "bad");
      }
    );
  };

  const loadTravelChecklist = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-checklist-${plan.id}`,
      () => apiRequest<EventTravelChecklistItemRead[]>(`/events/travel-plans/${plan.id}/checklist`, { identity }),
      (items) => {
        setTravelChecklistItems(items);
        addLog(`Travel checklist loaded: ${items.length} items`, "good");
      }
    );
  };

  const seedTravelChecklist = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-checklist-seed-${plan.id}`,
      () =>
        apiRequest<EventTravelChecklistItemRead[]>(`/events/travel-plans/${plan.id}/checklist`, {
          method: "POST",
          identity,
          body: {
            checklist_type: travelForm.checklist_type,
            items: null
          }
        }),
      (items) => {
        setTravelChecklistItems(items);
        addLog(`Travel checklist ready: ${items.length} items`, "good");
      }
    );
  };

  const updateTravelChecklistItem = (
    item: EventTravelChecklistItemRead,
    statusValue: "completed" | "blocked" | "pending"
  ) => {
    runAction(
      `travel-checklist-item-${item.id}-${statusValue}`,
      () =>
        apiRequest<EventTravelChecklistItemRead>(`/events/travel-checklist-items/${item.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            evidence_url: item.evidence_url,
            notes: statusValue === "blocked" ? "Blocked from operations console." : item.notes
          }
        }),
      (updated) => {
        setTravelChecklistItems((current) => [
          updated,
          ...current.filter((entry) => entry.id !== updated.id)
        ]);
        addLog(`${updated.item_label}: ${updated.status}`, updated.status === "completed" ? "good" : "bad");
      }
    );
  };

  const uploadTravelChecklistEvidence = (item: EventTravelChecklistItemRead) => {
    if (!selectedTravelChecklistFile) {
      addLog("Choose a checklist evidence file first", "bad");
      return;
    }
    runAction(
      `travel-checklist-evidence-${item.id}`,
      async () => {
        const contentBase64 = await fileToBase64(selectedTravelChecklistFile);
        return apiRequest<EventTravelChecklistEvidenceUploadRead>(`/events/travel-checklist-items/${item.id}/evidence`, {
          method: "POST",
          identity,
          body: {
            filename: selectedTravelChecklistFile.name,
            content_type: selectedTravelChecklistFile.type || "application/octet-stream",
            content_base64: contentBase64,
            status: "completed",
            notes: item.notes ?? `Evidence uploaded for ${item.item_label}.`
          }
        });
      },
      (upload) => {
        setTravelChecklistItems((current) => [
          upload.checklist_item,
          ...current.filter((entry) => entry.id !== upload.checklist_item.id)
        ]);
        setSelectedTravelChecklistFile(null);
        addLog(`${upload.filename} checklist evidence stored (${upload.size_bytes} bytes)`, "good");
      }
    );
  };

  const loadTravelLocationUpdates = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-location-updates-${plan.id}`,
      () => apiRequest<EventTravelLocationUpdateRead[]>(`/events/travel-plans/${plan.id}/location-updates`, { identity }),
      (updates) => {
        setTravelLocationUpdates(updates);
        addLog(`Travel tracking loaded: ${updates.length} updates`, "good");
      }
    );
  };

  const loadTravelTelemetryStream = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-telemetry-stream-${plan.id}`,
      () =>
        apiRequest<EventTravelTelemetryStreamRead>(`/events/travel-plans/${plan.id}/location-stream-info`, {
          identity
        }),
      (stream) => {
        setTravelTelemetryStream(stream);
        addLog(`Telemetry stream ready: ${stream.update_count} replay rows`, stream.update_count ? "good" : "neutral");
      }
    );
  };

  const recordTravelLocationUpdate = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-location-update-${plan.id}`,
      () =>
        apiRequest<EventTravelLocationUpdateRead>(`/events/travel-plans/${plan.id}/location-updates`, {
          method: "POST",
          identity,
          body: {
            phase: travelForm.tracking_phase,
            source: travelForm.tracking_source,
            recorded_at: new Date().toISOString(),
            latitude: String(travelForm.latitude),
            longitude: String(travelForm.longitude),
            speed_kph: String(travelForm.speed_kph),
            heading_degrees: String(travelForm.heading_degrees),
            notify_guardians: true,
            channel: travelForm.tracking_channel,
            notes: `Travel ${travelForm.tracking_phase} update for ${plan.destination}.`
          }
        }),
      (update) => {
        setTravelLocationUpdates((current) => [
          update,
          ...current.filter((item) => item.id !== update.id)
        ]);
        addLog(
          `Travel ${update.phase} at ${update.latitude}, ${update.longitude}`,
          update.notification_recipient_count > 0 ? "good" : "neutral"
        );
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
        if (selectedEventId) {
          void loadTravelPlans(selectedEventId);
        }
      }
    );
  };

  const loadTravelDevices = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-devices-${plan.id}`,
      () =>
        apiRequest<EventTravelDeviceRead[]>(`/events/travel-plans/${plan.id}/devices`, {
          method: "GET",
          identity
        }),
      (devices) => {
        setTravelDevices(devices);
        addLog(`${devices.length} travel devices loaded for ${plan.destination}`, "neutral");
      }
    );
  };

  const loadTravelDeviceFleetInventory = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `travel-device-fleet-${selectedOrganizationId}`,
      () =>
        apiRequest<EventTravelDeviceFleetInventoryRead>(
          `/events/travel-devices/fleet-inventory?organization_id=${selectedOrganizationId}`,
          { identity }
        ),
      (inventory) => {
        setTravelDeviceFleetInventory(inventory);
        addLog(
          `Travel GPS fleet: ${inventory.total_devices} devices, ${inventory.stale_devices} stale`,
          inventory.stale_devices > 0 || inventory.low_battery_devices > 0 ? "bad" : "good"
        );
      }
    );
  };

  const createTravelDevice = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-device-create-${plan.id}`,
      () =>
        apiRequest<EventTravelDeviceRead>(`/events/travel-plans/${plan.id}/devices`, {
          method: "POST",
          identity,
          body: {
            provider: travelForm.device_provider,
            device_id: travelForm.device_id,
            label: travelForm.device_label,
            status: travelForm.device_status,
            assigned_vehicle: travelForm.device_vehicle || null,
            installed_at: new Date().toISOString(),
            notes: `Provisioned from operations console for ${plan.destination}.`
          }
        }),
      (device) => {
        setTravelDevices((current) => [
          device,
          ...current.filter((item) => item.id !== device.id)
        ]);
        addLog(`Travel device provisioned: ${device.label}`, "good");
      }
    );
  };

  const setTravelDeviceStatus = (device: EventTravelDeviceRead, status: EventTravelDeviceRead["status"]) => {
    runAction(
      `travel-device-status-${device.id}-${status}`,
      () =>
        apiRequest<EventTravelDeviceRead>(`/events/travel-devices/${device.id}`, {
          method: "PATCH",
          identity,
          body: { status }
        }),
      (updatedDevice) => {
        setTravelDevices((current) => current.map((item) => (item.id === updatedDevice.id ? updatedDevice : item)));
        addLog(`${updatedDevice.label} marked ${updatedDevice.status}`, updatedDevice.status === "active" ? "good" : "neutral");
      }
    );
  };

  const rotateTravelDeviceSecret = (device: EventTravelDeviceRead) => {
    runAction(
      `travel-device-secret-${device.id}`,
      () =>
        apiRequest<EventTravelDeviceSecretRead>(`/events/travel-devices/${device.id}/rotate-secret`, {
          method: "POST",
          identity
        }),
      (secret) => {
        setTravelDeviceSecret(secret);
        setTravelDevices((current) =>
          current.map((item) =>
            item.id === secret.id
              ? {
                  ...item,
                  secret_configured: true,
                  secret_storage_mode: secret.secret_storage_mode,
                  secret_vault_provider: secret.secret_vault_provider,
                  secret_vault_reference: secret.secret_vault_reference,
                  secret_rotated_at: secret.secret_rotated_at
                }
              : item
          )
        );
        addLog(`Rotated ingest secret for ${secret.label}`, "good");
      }
    );
  };

  const loadTravelBackupDrivers = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-backup-drivers-${plan.id}`,
      () => apiRequest<EventTravelBackupDriverRead[]>(`/events/travel-plans/${plan.id}/backup-drivers`, { identity }),
      (drivers) => {
        setTravelBackupDrivers(drivers);
        addLog(`Backup drivers loaded: ${drivers.length}`, "neutral");
      }
    );
  };

  const createTravelBackupDriver = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-backup-driver-create-${plan.id}`,
      () =>
        apiRequest<EventTravelBackupDriverRead>(`/events/travel-plans/${plan.id}/backup-drivers`, {
          method: "POST",
          identity,
          body: {
            driver_name: travelForm.backup_driver_name,
            driver_person_id: null,
            phone: travelForm.backup_driver_phone || null,
            vehicle_label: travelForm.backup_driver_vehicle || null,
            capacity: travelForm.backup_driver_capacity,
            license_status: travelForm.backup_driver_license_status,
            background_check_status: travelForm.backup_driver_background_status,
            availability_status: travelForm.backup_driver_availability,
            response_minutes: travelForm.backup_driver_response_minutes,
            priority: travelForm.backup_driver_priority,
            notes: travelForm.backup_driver_notes || null
          }
        }),
      (driver) => {
        setTravelBackupDrivers((current) => [
          driver,
          ...current.filter((item) => item.id !== driver.id)
        ]);
        addLog(`Backup driver added: ${driver.driver_name}`, "good");
      }
    );
  };

  const setTravelBackupDriverAvailability = (
    driver: EventTravelBackupDriverRead,
    availabilityStatus: EventTravelBackupDriverRead["availability_status"]
  ) => {
    runAction(
      `travel-backup-driver-${driver.id}-${availabilityStatus}`,
      () =>
        apiRequest<EventTravelBackupDriverRead>(`/events/travel-backup-drivers/${driver.id}`, {
          method: "PATCH",
          identity,
          body: {
            availability_status: availabilityStatus,
            notes: driver.notes
          }
        }),
      (updatedDriver) => {
        setTravelBackupDrivers((current) =>
          current.map((item) => (item.id === updatedDriver.id ? updatedDriver : item))
        );
        addLog(
          `${updatedDriver.driver_name} ${updatedDriver.availability_status}`,
          updatedDriver.availability_status === "available" ? "good" : "neutral"
        );
      }
    );
  };

  const dispatchTravelBackupDriver = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-backup-driver-dispatch-${plan.id}`,
      () =>
        apiRequest<EventTravelBackupDriverDispatchRead>(`/events/travel-plans/${plan.id}/backup-drivers/dispatch`, {
          method: "POST",
          identity,
          body: {
            minimum_capacity: travelForm.backup_dispatch_minimum_capacity,
            require_verified: travelForm.backup_dispatch_require_verified,
            channel: travelForm.backup_dispatch_channel,
            reason: travelForm.backup_dispatch_reason,
            notify_driver: true
          }
        }),
      (dispatch) => {
        setTravelBackupDriverDispatch(dispatch);
        setTravelBackupDrivers((current) => [
          dispatch.driver,
          ...current.filter((item) => item.id !== dispatch.driver.id)
        ]);
        if (dispatch.message_id) {
          setSelectedMessageId(dispatch.message_id);
        }
        addLog(
          `Backup driver dispatched: ${dispatch.driver.driver_name}`,
          dispatch.recipient_count > 0 || !dispatch.driver.driver_person_id ? "good" : "neutral"
        );
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
      }
    );
  };

  const loadTravelDriverMarketplace = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-driver-marketplace-${plan.id}`,
      () =>
        apiRequest<EventTravelDriverMarketplaceRead>(`/events/travel-plans/${plan.id}/driver-marketplace`, {
          identity
        }),
      (marketplace) => {
        setTravelDriverMarketplace(marketplace);
        addLog(
          `Driver marketplace: ${marketplace.verified_candidate_count}/${marketplace.candidate_count} verified`,
          marketplace.verified_candidate_count ? "good" : "neutral"
        );
      }
    );
  };

  const loadTravelDriverRatings = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-driver-ratings-${plan.id}`,
      async () => {
        const [ratings, summary] = await Promise.all([
          apiRequest<EventTravelDriverRatingRead[]>(`/events/travel-plans/${plan.id}/driver-ratings`, { identity }),
          apiRequest<EventTravelDriverRatingSummaryRead>(`/events/travel-plans/${plan.id}/driver-rating-summary`, {
            identity
          })
        ]);
        return { ratings, summary };
      },
      ({ ratings, summary }) => {
        setTravelDriverRatings(ratings);
        setTravelDriverRatingSummary(summary);
        addLog(`Driver ratings loaded: ${summary.rating_count}`, "neutral");
      }
    );
  };

  const createTravelDriverRating = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-driver-rating-create-${plan.id}`,
      () =>
        apiRequest<EventTravelDriverRatingRead>(`/events/travel-plans/${plan.id}/driver-ratings`, {
          method: "POST",
          identity,
          body: {
            driver_name: travelForm.driver_rating_name,
            driver_person_id: null,
            vehicle_label: travelForm.driver_rating_vehicle || null,
            overall_score: travelForm.driver_rating_overall,
            safety_score: travelForm.driver_rating_safety,
            punctuality_score: travelForm.driver_rating_punctuality,
            communication_score: travelForm.driver_rating_communication,
            vehicle_condition_score: travelForm.driver_rating_vehicle_condition,
            would_use_again: travelForm.driver_rating_would_use_again,
            incident_reported: travelForm.driver_rating_incident_reported,
            reviewer_person_id: null,
            reviewed_at: new Date().toISOString(),
            notes: travelForm.driver_rating_notes || null
          }
        }),
      (rating) => {
        setTravelDriverRatings((current) => [
          rating,
          ...current.filter((item) => item.id !== rating.id)
        ]);
        void loadTravelDriverRatings(plan);
        addLog(`Driver ${rating.driver_name} rated ${rating.overall_score}/5`, rating.incident_reported ? "bad" : "good");
      }
    );
  };

  const checkTravelGeofence = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-geofence-${plan.id}`,
      () =>
        apiRequest<EventTravelGeofenceCheckRead>(`/events/travel-plans/${plan.id}/geofence-check`, {
          method: "POST",
          identity,
          body: {
            center_latitude: String(travelForm.geofence_latitude),
            center_longitude: String(travelForm.geofence_longitude),
            radius_km: String(travelForm.geofence_radius_km),
            label: travelForm.geofence_label,
            polygon_coordinates: parseGeofencePolygon(travelForm.geofence_polygon),
            alert_on_breach: true,
            channel: travelForm.geofence_channel
          }
        }),
      (check) => {
        setTravelGeofenceCheck(check);
        addLog(
          check.breached
            ? `Geofence breached by latest ${plan.destination} update`
            : `${plan.destination} is inside geofence`,
          check.breached ? "bad" : "good"
        );
        if (check.message_id) {
          setSelectedMessageId(check.message_id);
        }
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
      }
    );
  };

  const loadTravelExpenses = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-expenses-${plan.id}`,
      () => apiRequest<EventTravelExpenseRead[]>(`/events/travel-plans/${plan.id}/expenses`, { identity }),
      (expenses) => {
        setTravelExpenses(expenses);
        addLog(`Travel expenses loaded: ${expenses.length}`, "good");
      }
    );
  };

  const loadTravelGeofenceZones = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-geofence-zones-${plan.id}`,
      () =>
        apiRequest<EventTravelGeofenceZoneRead[]>(`/events/travel-plans/${plan.id}/geofence-zones`, {
          method: "GET",
          identity
        }),
      (zones) => {
        setTravelGeofenceZones(zones);
        addLog(`${zones.length} travel geofence zones loaded for ${plan.destination}`, "neutral");
      }
    );
  };

  const createTravelGeofenceZone = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-geofence-zone-create-${plan.id}`,
      () =>
        apiRequest<EventTravelGeofenceZoneRead>(`/events/travel-plans/${plan.id}/geofence-zones`, {
          method: "POST",
          identity,
          body: {
            center_latitude: String(travelForm.geofence_latitude),
            center_longitude: String(travelForm.geofence_longitude),
            radius_km: String(travelForm.geofence_radius_km),
            label: travelForm.geofence_label,
            polygon_coordinates: parseGeofencePolygon(travelForm.geofence_polygon),
            provider: travelForm.geofence_provider || null,
            provider_zone_id: travelForm.geofence_provider_zone_id || null,
            provider_revision: travelForm.geofence_provider_revision || null,
            alert_on_breach: true,
            channel: travelForm.geofence_channel,
            active: true,
            notes: `Saved from operations console for ${plan.destination}.`
          }
        }),
      (zone) => {
        setTravelGeofenceZones((current) => [
          zone,
          ...current.filter((item) => item.id !== zone.id)
        ]);
        addLog(`Travel geofence zone saved: ${zone.label}`, "good");
      }
    );
  };

  const checkTravelGeofenceZone = (zone: EventTravelGeofenceZoneRead) => {
    runAction(
      `travel-geofence-zone-check-${zone.id}`,
      () =>
        apiRequest<EventTravelGeofenceCheckRead>(`/events/travel-geofence-zones/${zone.id}/check`, {
          method: "POST",
          identity
        }),
      (check) => {
        setTravelGeofenceCheck(check);
        addLog(
          check.breached
            ? `Saved zone breached: ${check.label}`
            : `Latest update is inside saved zone: ${check.label}`,
          check.breached ? "bad" : "good"
        );
        if (check.message_id) {
          setSelectedMessageId(check.message_id);
        }
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
      }
    );
  };

  const editTravelGeofenceZone = (zone: EventTravelGeofenceZoneRead) => {
    setTravelForm((current) => ({
      ...current,
      geofence_label: zone.label,
      geofence_latitude: Number(zone.center_latitude),
      geofence_longitude: Number(zone.center_longitude),
      geofence_radius_km: Number(zone.radius_km),
      geofence_polygon: zone.polygon_coordinates?.map((point) => `${point.latitude},${point.longitude}`).join("; ") ?? "",
      geofence_provider: zone.provider ?? "",
      geofence_provider_zone_id: zone.provider_zone_id ?? "",
      geofence_provider_revision: zone.provider_revision ?? "",
      geofence_channel: zone.channel
    }));
    addLog(`Loaded ${zone.label} into the geofence form`, "neutral");
  };

  const updateTravelGeofenceZone = (zone: EventTravelGeofenceZoneRead) => {
    runAction(
      `travel-geofence-zone-update-${zone.id}`,
      () =>
        apiRequest<EventTravelGeofenceZoneRead>(`/events/travel-geofence-zones/${zone.id}`, {
          method: "PATCH",
          identity,
          body: {
            center_latitude: String(travelForm.geofence_latitude),
            center_longitude: String(travelForm.geofence_longitude),
            radius_km: String(travelForm.geofence_radius_km),
            label: travelForm.geofence_label,
            polygon_coordinates: parseGeofencePolygon(travelForm.geofence_polygon),
            provider: travelForm.geofence_provider || null,
            provider_zone_id: travelForm.geofence_provider_zone_id || null,
            provider_revision: travelForm.geofence_provider_revision || null,
            alert_on_breach: true,
            channel: travelForm.geofence_channel,
            active: zone.active,
            notes: `Updated from operations console for ${zone.label}.`
          }
        }),
      (updatedZone) => {
        setTravelGeofenceZones((current) => current.map((item) => (item.id === updatedZone.id ? updatedZone : item)));
        addLog(`${updatedZone.label} ${updatedZone.active ? "updated" : "deactivated"}`, updatedZone.active ? "good" : "neutral");
      }
    );
  };

  const setTravelGeofenceZoneActive = (zone: EventTravelGeofenceZoneRead, active: boolean) => {
    runAction(
      `travel-geofence-zone-active-${zone.id}-${active ? "active" : "inactive"}`,
      () =>
        apiRequest<EventTravelGeofenceZoneRead>(`/events/travel-geofence-zones/${zone.id}`, {
          method: "PATCH",
          identity,
          body: { active }
        }),
      (updatedZone) => {
        setTravelGeofenceZones((current) => current.map((item) => (item.id === updatedZone.id ? updatedZone : item)));
        addLog(`${updatedZone.label} ${updatedZone.active ? "activated" : "deactivated"}`, updatedZone.active ? "good" : "neutral");
      }
    );
  };

  const createTravelExpense = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-expense-create-${plan.id}`,
      () =>
        apiRequest<EventTravelExpenseRead>(`/events/travel-plans/${plan.id}/expenses`, {
          method: "POST",
          identity,
          body: {
            category: travelForm.expense_category,
            vendor: travelForm.expense_vendor || null,
            amount: String(travelForm.expense_amount),
            currency: "USD",
            incurred_at: new Date().toISOString(),
            paid_by_person_id: null,
            receipt_url: travelForm.expense_receipt_url || null,
            notes: travelForm.expense_notes || null
          }
        }),
      (expense) => {
        setTravelExpenses((current) => [
          expense,
          ...current.filter((item) => item.id !== expense.id)
        ]);
        addLog(`${expense.category} expense submitted for ${expense.amount} ${expense.currency}`, "good");
      }
    );
  };

  const updateTravelExpenseStatus = (
    expense: EventTravelExpenseRead,
    statusValue: "approved" | "reimbursed" | "rejected"
  ) => {
    runAction(
      `travel-expense-${expense.id}-${statusValue}`,
      () =>
        apiRequest<EventTravelExpenseRead>(`/events/travel-expenses/${expense.id}`, {
          method: "PATCH",
          identity,
          body: {
            reimbursement_status: statusValue,
            receipt_url: expense.receipt_url,
            notes: expense.notes ?? `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setTravelExpenses((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(
          `${updated.category} expense ${updated.reimbursement_status}`,
          updated.reimbursement_status === "rejected" ? "bad" : "good"
        );
      }
    );
  };

  const executeTravelExpensePayout = (expense: EventTravelExpenseRead) => {
    runAction(
      `travel-expense-payout-${expense.id}`,
      () =>
        apiRequest<EventTravelExpensePayoutRead>(`/events/travel-expenses/${expense.id}/payout`, {
          method: "POST",
          identity,
          body: {
            provider: travelForm.payout_provider,
            external_reference: null,
            destination: travelForm.payout_destination || null,
            adapter_mode: travelForm.payout_adapter_mode || null,
            idempotency_key: null,
            mark_reimbursed: true,
            notes: `Payout executed from the operations console for ${expense.category}.`
          }
        }),
      (payout) => {
        setTravelExpensePayout(payout);
        setTravelExpenses((current) => [
          payout.expense,
          ...current.filter((item) => item.id !== payout.expense.id)
        ]);
        addLog(`Payout ${payout.payout_reference} ${payout.payout_status} via ${payout.adapter_mode}`, "good");
      }
    );
  };

  const reconcileTravelExpensePayoutCallback = (expense: EventTravelExpenseRead, statusValue: "paid" | "failed") => {
    if (!expense.payout_reference && !expense.payout_idempotency_key) {
      addLog("Execute or queue the payout before reconciling a callback", "neutral");
      return;
    }
    runAction(
      `travel-expense-payout-callback-${expense.id}-${statusValue}`,
      () =>
        apiRequest<EventTravelExpensePayoutCallbackRead>("/events/travel-expense-payout-callbacks", {
          method: "POST",
          body: {
            provider: expense.payout_provider ?? travelForm.payout_provider,
            payout_reference: expense.payout_reference,
            idempotency_key: expense.payout_idempotency_key,
            status: statusValue,
            provider_status_code: statusValue === "paid" ? 200 : 422,
            external_event_id: `travel-payout-${statusValue}-${Date.now()}`,
            raw_payload: {
              source: "operations_console",
              expense_id: expense.id,
              callback_status: statusValue
            },
            notes: `Payout callback reconciled from operations console as ${statusValue}.`
          }
        }),
      (callback) => {
        setTravelExpenses((current) => [
          callback.expense,
          ...current.filter((item) => item.id !== callback.expense.id)
        ]);
        addLog(callback.message, callback.payout_status === "paid" ? "good" : "bad");
      }
    );
  };

  const uploadTravelReceipt = (expense: EventTravelExpenseRead) => {
    if (!selectedTravelReceiptFile) {
      addLog("Choose a receipt file first", "bad");
      return;
    }
    runAction(
      `travel-receipt-${expense.id}`,
      async () => {
        const contentBase64 = await fileToBase64(selectedTravelReceiptFile);
        return apiRequest<EventTravelReceiptUploadRead>(`/events/travel-expenses/${expense.id}/receipt`, {
          method: "POST",
          identity,
          body: {
            filename: selectedTravelReceiptFile.name,
            content_type: selectedTravelReceiptFile.type || "application/octet-stream",
            content_base64: contentBase64,
            notes: travelForm.expense_notes || expense.notes
          }
        });
      },
      (upload) => {
        setTravelExpenses((current) => [
          upload.expense,
          ...current.filter((item) => item.id !== upload.expense.id)
        ]);
        setSelectedTravelReceiptFile(null);
        addLog(`${upload.filename} receipt stored (${upload.size_bytes} bytes)`, "good");
      }
    );
  };

  const loadTravelCarpools = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-carpools-${plan.id}`,
      () => apiRequest<EventTravelCarpoolRideRead[]>(`/events/travel-plans/${plan.id}/carpools`, { identity }),
      (rides) => {
        setTravelCarpoolRides(rides);
        addLog(`Travel carpools loaded: ${rides.length}`, "good");
      }
    );
  };

  const createTravelCarpool = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-carpool-create-${plan.id}`,
      () =>
        apiRequest<EventTravelCarpoolRideRead>(`/events/travel-plans/${plan.id}/carpools`, {
          method: "POST",
          identity,
          body: {
            ride_type: travelForm.carpool_type,
            rider_person_id: travelForm.carpool_type === "request" ? selectedAthleteId || null : null,
            driver_person_id: null,
            pickup_location: travelForm.carpool_pickup_location,
            pickup_latitude: String(travelForm.carpool_pickup_latitude),
            pickup_longitude: String(travelForm.carpool_pickup_longitude),
            dropoff_location: travelForm.carpool_dropoff_location || null,
            dropoff_latitude: travelForm.carpool_dropoff_location ? String(travelForm.carpool_dropoff_latitude) : null,
            dropoff_longitude: travelForm.carpool_dropoff_location ? String(travelForm.carpool_dropoff_longitude) : null,
            seats_requested: travelForm.carpool_seats_requested,
            seats_available: travelForm.carpool_type === "offer" ? travelForm.carpool_seats_available : 0,
            departure_window_start: travelForm.carpool_window_start
              ? new Date(travelForm.carpool_window_start).toISOString()
              : null,
            departure_window_end: travelForm.carpool_window_end
              ? new Date(travelForm.carpool_window_end).toISOString()
              : null,
            notes: travelForm.carpool_notes || null
          }
        }),
      (ride) => {
        setTravelCarpoolRides((current) => [
          ride,
          ...current.filter((item) => item.id !== ride.id)
        ]);
        addLog(`${ride.ride_type} carpool opened for ${ride.pickup_location}`, "good");
      }
    );
  };

  const autoMatchTravelCarpools = (plan: EventTravelPlanRead) => {
    runAction(
      `travel-carpool-auto-match-${plan.id}`,
      () =>
        apiRequest<EventTravelCarpoolAutoMatchRead>(`/events/travel-plans/${plan.id}/carpools/auto-match`, {
          method: "POST",
          identity,
          body: {
            minimum_score: "55.00",
            confirm_matches: false
          }
        }),
      (result) => {
        setTravelCarpoolAutoMatch(result);
        setTravelCarpoolRides(result.rides);
        addLog(
          `Carpool auto-match: ${result.matched_count}/${result.request_count} requests matched`,
          result.matched_count > 0 ? "good" : "neutral"
        );
      }
    );
  };

  const updateTravelCarpoolStatus = (
    ride: EventTravelCarpoolRideRead,
    statusValue: "matched" | "confirmed" | "cancelled"
  ) => {
    runAction(
      `travel-carpool-${ride.id}-${statusValue}`,
      () =>
        apiRequest<EventTravelCarpoolRideRead>(`/events/travel-carpools/${ride.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            rider_person_id: ride.rider_person_id,
            driver_person_id: ride.driver_person_id,
            match_score: statusValue === "matched" ? "87.50" : ride.match_score,
            notes: ride.notes ?? `Carpool ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setTravelCarpoolRides((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.ride_type} carpool ${updated.status}`, updated.status === "cancelled" ? "bad" : "good");
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

  const createSafeguardingIncident = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-safeguarding-incident",
      () =>
        apiRequest<SafeguardingIncidentRead>("/safeguarding/incidents", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            event_id: selectedEventId || null,
            team_id: selectedTeamId || null,
            athlete_person_id: selectedAthleteId || null,
            incident_type: incidentForm.incident_type,
            severity: incidentForm.severity,
            occurred_at: new Date(incidentForm.occurred_at).toISOString(),
            location: incidentForm.location || null,
            title: incidentForm.title,
            description: incidentForm.description,
            immediate_action: incidentForm.immediate_action || null,
            parent_notified_at: null,
            medical_follow_up_required: incidentForm.medical_follow_up_required,
            regulatory_report_required: incidentForm.regulatory_report_required
          }
        }),
      (incident) => {
        setSafeguardingIncidents((current) => [
          incident,
          ...current.filter((item) => item.id !== incident.id)
        ]);
        addLog(`${incident.title} incident logged`, incident.severity === "critical" ? "bad" : "good");
        refreshSafeguardingCompliance();
      }
    );
  };

  const updateSafeguardingIncident = (
    incident: SafeguardingIncidentRead,
    statusValue: SafeguardingIncidentStatus
  ) => {
    runAction(
      `safeguarding-incident-${incident.id}-${statusValue}`,
      () =>
        apiRequest<SafeguardingIncidentRead>(`/safeguarding/incidents/${incident.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            resolution_notes:
              statusValue === "resolved" || statusValue === "closed"
                ? `Marked ${statusValue} from the operations console.`
                : null
          }
        }),
      (updated) => {
        setSafeguardingIncidents((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.title} moved to ${updated.status}`, "good");
        refreshSafeguardingCompliance();
      }
    );
  };

  const createBackgroundCheck = () => {
    if (!selectedOrganizationId || !selectedAthleteId) {
      addLog("Select an organization and athlete first", "bad");
      return;
    }
    runAction(
      "create-background-check",
      () =>
        apiRequest<BackgroundCheckRead>("/safeguarding/background-checks", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            person_id: selectedAthleteId,
            provider: backgroundCheckForm.provider,
            check_type: backgroundCheckForm.check_type,
            requested_at: new Date(backgroundCheckForm.requested_at).toISOString(),
            expires_at: backgroundCheckForm.expires_at || null,
            external_reference: backgroundCheckForm.external_reference || null,
            notes: backgroundCheckForm.notes || null
          }
        }),
      (check) => {
        setBackgroundChecks((current) => [
          check,
          ...current.filter((item) => item.id !== check.id)
        ]);
        addLog(`${check.check_type} background check requested`, "good");
        refreshSafeguardingCompliance();
      }
    );
  };

  const updateBackgroundCheck = (check: BackgroundCheckRead, statusValue: BackgroundCheckStatus) => {
    runAction(
      `background-check-${check.id}-${statusValue}`,
      () =>
        apiRequest<BackgroundCheckRead>(`/safeguarding/background-checks/${check.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            completed_at: statusValue === "clear" || statusValue === "failed"
              ? new Date().toISOString()
              : null,
            result_summary: `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setBackgroundChecks((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.check_type} moved to ${updated.status}`, "good");
        refreshSafeguardingCompliance();
      }
    );
  };

  const createComplianceCredential = () => {
    if (!selectedOrganizationId || !selectedAthleteId) {
      addLog("Select an organization and athlete first", "bad");
      return;
    }
    runAction(
      "create-compliance-credential",
      () =>
        apiRequest<ComplianceCredentialRead>("/safeguarding/credentials", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            person_id: selectedAthleteId,
            credential_type: credentialForm.credential_type,
            title: credentialForm.title,
            issuing_body: credentialForm.issuing_body || null,
            credential_number: credentialForm.credential_number || null,
            issued_at: credentialForm.issued_at || null,
            expires_at: credentialForm.expires_at || null,
            renewal_due_at: credentialForm.renewal_due_at || null,
            verification_url: credentialForm.verification_url || null,
            notes: credentialForm.notes || null
          }
        }),
      (credential) => {
        setComplianceCredentials((current) => [
          credential,
          ...current.filter((item) => item.id !== credential.id)
        ]);
        addLog(`${credential.title} credential tracked`, "good");
        refreshSafeguardingCompliance();
      }
    );
  };

  const updateComplianceCredential = (
    credential: ComplianceCredentialRead,
    statusValue: ComplianceCredentialStatus
  ) => {
    runAction(
      `compliance-credential-${credential.id}-${statusValue}`,
      () =>
        apiRequest<ComplianceCredentialRead>(`/safeguarding/credentials/${credential.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            notes: `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setComplianceCredentials((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.title} credential moved to ${updated.status}`, "good");
        refreshSafeguardingCompliance();
      }
    );
  };

  const createIncidentReportPackage = (incident: SafeguardingIncidentRead) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `create-incident-report-package-${incident.id}`,
      () =>
        apiRequest<IncidentReportPackageRead>("/safeguarding/incident-report-packages", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            incident_id: incident.id,
            agency_name: reportPackageForm.agency_name,
            jurisdiction: reportPackageForm.jurisdiction,
            due_at: reportPackageForm.due_at || null,
            external_reference: reportPackageForm.external_reference || null,
            checklist_json: JSON.stringify({
              incident_report: true,
              guardian_notification: incident.parent_notified_at !== null,
              medical_follow_up: incident.medical_follow_up_required,
              regulatory_report_required: true
            }),
            submission_payload: JSON.stringify({
              incident_id: incident.id,
              incident_type: incident.incident_type,
              severity: incident.severity,
              occurred_at: incident.occurred_at,
              title: incident.title
            }),
            notes: reportPackageForm.notes || null
          }
        }),
      (reportPackage) => {
        setIncidentReportPackages((current) => [
          reportPackage,
          ...current.filter((item) => item.id !== reportPackage.id)
        ]);
        refreshSafeguardingCompliance();
        addLog(`${reportPackage.agency_name} report package drafted`, "good");
      }
    );
  };

  const updateIncidentReportPackage = (
    reportPackage: IncidentReportPackageRead,
    statusValue: IncidentReportPackageStatus
  ) => {
    runAction(
      `incident-report-package-${reportPackage.id}-${statusValue}`,
      () =>
        apiRequest<IncidentReportPackageRead>(
          `/safeguarding/incident-report-packages/${reportPackage.id}`,
          {
            method: "PATCH",
            identity,
            body: {
              status: statusValue,
              external_reference: reportPackage.external_reference || reportPackageForm.external_reference || null,
              notes: `Marked ${statusValue} from the operations console.`
            }
          }
        ),
      (updated) => {
        setIncidentReportPackages((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        refreshSafeguardingCompliance();
        addLog(`${updated.agency_name} report package moved to ${updated.status}`, "good");
      }
    );
  };

  const claimAmountCents = (value: string) => Math.round((Number(value) || 0) * 100);

  const createIncidentInsuranceClaim = (incident: SafeguardingIncidentRead) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `create-insurance-claim-${incident.id}`,
      () =>
        apiRequest<IncidentInsuranceClaimRead>("/safeguarding/insurance-claims", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            incident_id: incident.id,
            claimant_person_id: incident.athlete_person_id,
            claim_type: insuranceClaimForm.claim_type,
            provider_name: insuranceClaimForm.provider_name,
            policy_number: insuranceClaimForm.policy_number || null,
            claimed_amount_cents: claimAmountCents(insuranceClaimForm.claimed_amount),
            currency: insuranceClaimForm.currency,
            reserve_amount_cents: claimAmountCents(insuranceClaimForm.reserve_amount),
            tracking_url: insuranceClaimForm.tracking_url || null,
            documentation_checklist_json: JSON.stringify({
              incident_documentation: true,
              medical_follow_up: incident.medical_follow_up_required,
              regulatory_report: incident.regulatory_report_required,
              guardian_notification: incident.parent_notified_at !== null
            }),
            submission_payload: JSON.stringify({
              incident_id: incident.id,
              title: incident.title,
              incident_type: incident.incident_type,
              severity: incident.severity,
              occurred_at: incident.occurred_at,
              claimed_amount: insuranceClaimForm.claimed_amount,
              currency: insuranceClaimForm.currency
            }),
            notes: insuranceClaimForm.notes || null
          }
        }),
      (claim) => {
        setIncidentInsuranceClaims((current) => [
          claim,
          ...current.filter((item) => item.id !== claim.id)
        ]);
        addLog(`${claim.provider_name} claim drafted`, "good");
      }
    );
  };

  const updateIncidentInsuranceClaim = (
    claim: IncidentInsuranceClaimRead,
    statusValue: InsuranceClaimStatus
  ) => {
    runAction(
      `incident-insurance-claim-${claim.id}-${statusValue}`,
      () =>
        apiRequest<IncidentInsuranceClaimRead>(`/safeguarding/insurance-claims/${claim.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            coverage_verified_at: statusValue === "ready" ? new Date().toISOString() : null,
            claim_number: claim.claim_number || insuranceClaimForm.policy_number || null,
            approved_amount_cents:
              statusValue === "approved" || statusValue === "paid"
                ? claim.claimed_amount_cents
                : null,
            paid_amount_cents: statusValue === "paid" ? claim.claimed_amount_cents : null,
            communication_log: `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setIncidentInsuranceClaims((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.provider_name} claim moved to ${updated.status}`, "good");
      }
    );
  };

  const createIncidentMedicalClearance = (incident: SafeguardingIncidentRead) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `create-medical-clearance-${incident.id}`,
      () =>
        apiRequest<IncidentMedicalClearanceRead>("/safeguarding/medical-clearances", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            incident_id: incident.id,
            athlete_person_id: incident.athlete_person_id,
            clearance_type: medicalClearanceForm.clearance_type,
            valid_from: medicalClearanceForm.valid_from || null,
            valid_until: medicalClearanceForm.valid_until || null,
            restrictions: medicalClearanceForm.restrictions || null,
            return_to_play_stage: medicalClearanceForm.return_to_play_stage || null,
            provider_name: medicalClearanceForm.provider_name || null,
            notes: medicalClearanceForm.notes || null
          }
        }),
      (clearance) => {
        setIncidentMedicalClearances((current) => [
          clearance,
          ...current.filter((item) => item.id !== clearance.id)
        ]);
        addLog(`${clearance.clearance_type} clearance opened`, "good");
      }
    );
  };

  const updateIncidentMedicalClearance = (
    clearance: IncidentMedicalClearanceRead,
    statusValue: MedicalClearanceStatus
  ) => {
    runAction(
      `incident-medical-clearance-${clearance.id}-${statusValue}`,
      () =>
        apiRequest<IncidentMedicalClearanceRead>(`/safeguarding/medical-clearances/${clearance.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            assessed_at: new Date().toISOString(),
            restrictions:
              statusValue === "cleared"
                ? "Cleared for full participation."
                : medicalClearanceForm.restrictions || null,
            return_to_play_stage:
              statusValue === "cleared"
                ? "full_return"
                : medicalClearanceForm.return_to_play_stage || null,
            notes: `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setIncidentMedicalClearances((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.clearance_type} moved to ${updated.status}`, "good");
      }
    );
  };

  const refreshSafeguardingCompliance = () => {
    if (!selectedOrganizationId) {
      return;
    }
    void Promise.all([
      loadBackgroundChecks(selectedOrganizationId),
      loadComplianceCredentials(selectedOrganizationId),
      loadSafeguardingIncidents(selectedOrganizationId),
      loadComplianceSummary(selectedOrganizationId),
      loadIncidentReportPackages(selectedOrganizationId),
      loadIncidentInsuranceClaims(selectedOrganizationId),
      loadIncidentMedicalClearances(selectedOrganizationId)
    ]);
  };

  const reconcileCompliance = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "reconcile-compliance",
      () =>
        apiRequest<ComplianceReconciliationRead>(
          `/safeguarding/compliance-reconcile?organization_id=${selectedOrganizationId}`,
          {
            method: "POST",
            identity
          }
        ),
      (result) => {
        refreshSafeguardingCompliance();
        addLog(
          `Compliance reconciled: ${result.background_checks_expired} checks expired, ${result.credentials_expired} credentials expired, ${result.credentials_expiring_soon} renewals flagged`,
          "good"
        );
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

  const registerAgentModel = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const modelPolicy =
      agentForm.model_policy ||
      selectedAgent?.model_policy ||
      agentGovernance?.credential_status.default_model ||
      "afrolete-local-planner";
    const provider = modelPolicy.toLowerCase().includes("gpt")
      ? "openai-compatible"
      : modelPolicy.toLowerCase().includes("webhook")
        ? "external-worker"
        : "local";
    runAction(
      `register-agent-model-${modelPolicy}`,
      () =>
        apiRequest<AgentModelRegistryRead>("/agents/model-registry", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            model_policy: modelPolicy,
            provider,
            model_family: selectedAgent?.kind ?? agentForm.kind,
            version: "v1",
            use_case: selectedAgent?.purpose ?? agentForm.purpose,
            risk_tier: ["safeguarding", "analytics"].includes(selectedAgent?.kind ?? agentForm.kind)
              ? "high"
              : "medium",
            review_status: "in_review",
            evaluation_summary: "Registered from the operations console for governed evaluation tracking.",
            limitations: "Human review required before recommendations create side effects.",
            bias_notes: "Monitor model outputs for age, gender, region, school, and club bias.",
            data_residency: agentGovernance?.credential_status.credential_boundary ?? "local"
          }
        }),
      (registry) => {
        setAgentModelRegistry((current) => [
          registry,
          ...current.filter((item) => item.id !== registry.id)
        ]);
        addLog(`${registry.model_policy} registered for ${registry.review_status}`, "good");
        void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
      }
    );
  };

  const updateAgentModelRegistryStatus = (
    registry: AgentModelRegistryRead,
    reviewStatus: AgentModelRegistryRead["review_status"]
  ) => {
    runAction(
      `agent-model-registry-${registry.id}-${reviewStatus}`,
      () =>
        apiRequest<AgentModelRegistryRead>(`/agents/model-registry/${registry.id}`, {
          method: "PATCH",
          identity,
          body: {
            review_status: reviewStatus,
            evaluation_summary:
              reviewStatus === "approved"
                ? "Approved from the operations console after governance review."
                : `Marked ${reviewStatus} from the operations console.`
          }
        }),
      (updatedRegistry) => {
        setAgentModelRegistry((current) => [
          updatedRegistry,
          ...current.filter((item) => item.id !== updatedRegistry.id)
        ]);
        addLog(`${updatedRegistry.model_policy} is ${updatedRegistry.review_status}`, "good");
        if (selectedOrganizationId) {
          void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
        }
      }
    );
  };

  const runAgentBiasAudit = (registry: AgentModelRegistryRead) => {
    runAction(
      `agent-bias-audit-${registry.id}`,
      () =>
        apiRequest<AgentBiasAuditRead>(`/agents/model-registry/${registry.id}/bias-audits`, {
          method: "POST",
          identity,
          body: {
            audit_dimension: "age_gender_region_club_school",
            population_slice: "all-participants"
          }
        }),
      (audit) => {
        setAgentBiasAudits((current) => [
          audit,
          ...current.filter((item) => item.id !== audit.id)
        ]);
        addLog(`${audit.model_policy} bias audit is ${audit.status}`, audit.status === "fail" ? "bad" : "good");
        if (selectedOrganizationId) {
          void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
        }
      }
    );
  };

  const submitAgentDecisionAppeal = (task: AgentTaskRead) => {
    runAction(
      `agent-decision-appeal-${task.id}`,
      () =>
        apiRequest<AgentDecisionAppealRead>(`/agents/tasks/${task.id}/appeals`, {
          method: "POST",
          identity,
          body: {
            reason: "human_review",
            question: `Please explain and review the recommendation for ${task.title}.`,
            supporting_evidence_ref: task.output_ref ?? task.input_ref ?? undefined
          }
        }),
      (appeal) => {
        setAgentDecisionAppeals((current) => [
          appeal,
          ...current.filter((item) => item.id !== appeal.id)
        ]);
        addLog(`Appeal opened for ${appeal.model_policy}`, "good");
        if (selectedOrganizationId) {
          void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
        }
      }
    );
  };

  const resolveAgentDecisionAppeal = (
    appeal: AgentDecisionAppealRead,
    statusValue: "upheld" | "modified" | "overturned"
  ) => {
    runAction(
      `agent-decision-appeal-${appeal.id}-${statusValue}`,
      () =>
        apiRequest<AgentDecisionAppealRead>(`/agents/appeals/${appeal.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            resolution_notes: `Human reviewer ${statusValue} the appeal from the operations console.`
          }
        }),
      (updatedAppeal) => {
        setAgentDecisionAppeals((current) => [
          updatedAppeal,
          ...current.filter((item) => item.id !== updatedAppeal.id)
        ]);
        addLog(`Appeal ${updatedAppeal.status}`, "good");
      }
    );
  };

  const moderateAgentScorecardComment = (
    comment: AgentScorecardCommentModerationRead,
    statusValue: "published" | "hidden" | "flagged" | "private_feedback"
  ) => {
    runAction(
      `scorecard-comment-${comment.id}-${statusValue}`,
      () =>
        apiRequest<AgentScorecardCommentModerationRead>(`/agents/ethical-scorecard/comments/${comment.id}`, {
          method: "PATCH",
          identity,
          body: { status: statusValue }
        }),
      (updatedComment) => {
        setAgentScorecardComments((current) => [
          updatedComment,
          ...current.filter((item) => item.id !== updatedComment.id)
        ]);
        addLog(`Scorecard comment ${updatedComment.status}`, updatedComment.status === "published" ? "good" : "neutral");
      }
    );
  };

  const publishAgentScorecardSnapshot = () => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "agent-scorecard-publication",
      () =>
        apiRequest<AgentScorecardPublicationRead>("/agents/ethical-scorecard/publications", {
          method: "POST",
          identity,
          body: { organization_id: selectedOrganizationId }
        }),
      (publication) => {
        setAgentScorecardPublications((current) => [
          publication,
          ...current.filter((item) => item.id !== publication.id)
        ]);
        if (selectedOrganizationId) {
          void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
        }
        addLog(`Published ${publication.period_label} AI scorecard`, "good");
      }
    );
  };

  const downloadAgentScorecardPublication = (
    publication: AgentScorecardPublicationRead,
    artifactFormat: "markdown" | "pdf"
  ) => {
    runAction(
      `agent-scorecard-artifact-${artifactFormat}-${publication.id}`,
      () =>
        apiRequest<AgentScorecardPublicationArtifactRead>(
          `/agents/ethical-scorecard/publications/${publication.id}/artifact?artifact_format=${artifactFormat}`
        ),
      (artifact) => {
        if (artifact.content_base64) {
          downloadBase64Artifact(artifact.content_base64, artifact.content_type, artifact.download_filename);
        } else {
          downloadTextArtifact(artifact.content, artifact.content_type, artifact.download_filename);
        }
        addLog(
          `Downloaded ${artifact.period_label} ${artifact.artifact_format} scorecard artifact`,
          "good"
        );
      }
    );
  };

  const shareAgentScorecardPublication = (
    publication: AgentScorecardPublicationRead,
    artifactFormat: "markdown" | "pdf"
  ) => {
    runAction(
      `agent-scorecard-artifact-link-${artifactFormat}-${publication.id}`,
      () =>
        apiRequest<AgentScorecardPublicationArtifactLinkRead>(
          `/agents/ethical-scorecard/publications/${publication.id}/artifact-link?artifact_format=${artifactFormat}`
        ),
      (link) => {
        setAgentScorecardArtifactLink(link);
        if (selectedOrganizationId) {
          void loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined);
        }
        addLog(
          `Created ${link.period_label} ${link.artifact_format} scorecard link`,
          "good"
        );
      }
    );
  };

  const deliverAgentScorecardReminder = () => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "agent-scorecard-reminder",
      () =>
        apiRequest<AgentScorecardPublicationReminderRead>("/agents/ethical-scorecard/publications/reminder", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            channel: "email" as CommunicationChannel,
            send_to_managers: true
          }
        }),
      (reminder) => {
        setAgentScorecardReminder(reminder);
        addLog(
          reminder.delivered
            ? `Sent ${reminder.period_label} scorecard reminder to ${reminder.recipient_count} people`
            : `Prepared ${reminder.period_label} scorecard reminder without recipients`,
          reminder.delivered ? "good" : "neutral"
        );
      }
    );
  };

  const deliverAgentScorecardArtifactAnomalyAlert = () => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "agent-scorecard-artifact-anomaly-alert",
      () =>
        apiRequest<AgentScorecardArtifactAnomalyAlertRead>(
          "/agents/ethical-scorecard/artifact-accesses/anomaly-alert",
          {
            method: "POST",
            identity,
            body: {
              organization_id: selectedOrganizationId,
              channel: "email" as CommunicationChannel,
              send_to_managers: true
            }
          }
        ),
      (alert) => {
        setAgentScorecardArtifactAnomalyAlert(alert);
        if (alert.message_id) {
          setSelectedMessageId(alert.message_id);
        }
        addLog(
          alert.delivered
            ? `Sent ${alert.anomaly_count} artifact anomaly alerts to ${alert.recipient_count} people`
            : alert.failure_reason ?? "No scorecard artifact anomaly alert was sent",
          alert.delivered ? "bad" : "neutral"
        );
      }
    );
  };

  const runAgentScorecardArtifactAnomalyAlertAutomation = () => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "agent-scorecard-artifact-anomaly-alert-run",
      () =>
        apiRequest<AgentScorecardArtifactAnomalyAlertRunRead>(
          "/agents/ethical-scorecard/artifact-accesses/anomaly-alert-run",
          {
            method: "POST",
            identity,
            body: {
              organization_id: selectedOrganizationId,
              channel: "email" as CommunicationChannel,
              send_alerts: true
            }
          }
        ),
      (run) => {
        setAgentScorecardArtifactAnomalyAlertRun(run);
        if (run.alert) {
          setAgentScorecardArtifactAnomalyAlert(run.alert);
        }
        if (run.message_id) {
          setSelectedMessageId(run.message_id);
        }
        addLog(
          run.sent
            ? `Artifact anomaly run sent ${run.recipient_count} alerts`
            : run.skipped_reason ?? "Artifact anomaly run completed without sending",
          run.sent ? "bad" : "neutral"
        );
      }
    );
  };

  const runAgentScorecardReminderAutomation = () => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "agent-scorecard-reminder-run",
      () =>
        apiRequest<AgentScorecardPublicationReminderRunRead>("/agents/ethical-scorecard/publications/reminder-run", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            channel: "email" as CommunicationChannel,
            due_within_days: 14,
            send_reminders: true
          }
        }),
      (run) => {
        setAgentScorecardReminderRun(run);
        if (run.reminder) {
          setAgentScorecardReminder(run.reminder);
        }
        addLog(
          run.sent
            ? `AI scorecard reminder run sent ${run.recipient_count} reminders`
            : `AI scorecard reminder run skipped ${run.period_label}`,
          run.sent ? "good" : "neutral"
        );
      }
    );
  };

  const runAgentScorecardAutomation = () => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "agent-scorecard-automation-run",
      () =>
        apiRequest<AgentScorecardAutomationRunRead>("/agents/ethical-scorecard/automation/run", {
          method: "POST",
          identity,
          body: {
            organization_ids: [selectedOrganizationId],
            channel: "email" as CommunicationChannel,
            due_within_days: 14,
            send_messages: true,
            run_publication_reminders: true,
            run_artifact_alerts: true
          }
        }),
      (run) => {
        setAgentScorecardAutomationRun(run);
        const firstRun = run.runs[0];
        if (firstRun?.publication_reminder) {
          setAgentScorecardReminderRun(firstRun.publication_reminder);
          if (firstRun.publication_reminder.reminder) {
            setAgentScorecardReminder(firstRun.publication_reminder.reminder);
          }
        }
        if (firstRun?.artifact_alert_run) {
          setAgentScorecardArtifactAnomalyAlertRun(firstRun.artifact_alert_run);
          if (firstRun.artifact_alert_run.alert) {
            setAgentScorecardArtifactAnomalyAlert(firstRun.artifact_alert_run.alert);
          }
        }
        addLog(
          `AI scorecard automation evaluated ${run.evaluated_count} orgs and sent ${run.sent_count} lanes`,
          run.sent_count > 0 ? "good" : "neutral"
        );
      }
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

  const applyAgentWorkerCallback = (task: AgentTaskRead) => {
    runAction(
      `agent-worker-callback-${task.id}`,
      () =>
        apiRequest<AgentWorkerCallbackRead>("/agents/worker-callbacks", {
          method: "POST",
          body: {
            task_id: task.id,
            status: "waiting_for_review",
            output_ref: `agent://tasks/${task.id}/outputs/worker-callback`,
            review_notes: `External worker callback returned a governed draft for ${task.title}.`,
            idempotency_key: `console-worker-callback-${task.id}`,
            external_event_id: `console-${Date.now()}`,
            raw_payload: {
              source: "operations_console",
              task_type: task.task_type
            }
          }
        }),
      (callback) => {
        setAgentTasks((current) => [
          callback.task,
          ...current.filter((item) => item.id !== callback.task.id)
        ]);
        addLog(callback.message, callback.duplicate ? "neutral" : "good");
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
            source_provider: observationForm.source_provider || undefined,
            evidence_ref: observationForm.evidence_ref,
            evidence_text: observationForm.evidence_text,
            extracted_value:
              observationForm.source === "manual" || observationForm.source === "coach_evaluation"
                ? observationForm.value
                : undefined,
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

  const runPerformanceModelBenchmark = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization before running model extraction benchmarks", "bad");
      return;
    }
    const dataset = performanceModelBenchmarkDatasets[0] ?? null;
    runAction(
      "performance-model-benchmark",
      () =>
        apiRequest<PerformanceModelExtractionBenchmarkRunRead>("/performance/model-extraction/benchmarks", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...(dataset ? { dataset_id: dataset.id } : {})
          }
        }),
      (benchmark) => {
        setPerformanceModelBenchmark(benchmark);
        if (dataset) {
          void loadPerformanceBenchmarkDatasets(selectedOrganizationId);
        }
        addLog(
          `${dataset ? dataset.name : benchmark.model_policy} benchmark ${benchmark.passed_count}/${benchmark.case_count} passed`,
          benchmark.failed_count ? "neutral" : "good"
        );
      }
    );
  };

  const runPerformanceForecastValidation = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization before running forecast validation", "bad");
      return;
    }
    runAction(
      "performance-forecast-validation",
      () =>
        apiRequest<PerformanceForecastValidationRunRead>("/performance/forecast-validation-runs", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...(selectedAthlete?.athleteProfileId ? { athlete_profile_id: selectedAthlete.athleteProfileId } : {})
          }
        }),
      (run) => {
        setPerformanceForecastValidationRun(run);
        setPerformanceForecastValidationRuns((current) => [
          run,
          ...current.filter((item) => item.id !== run.id)
        ]);
        addLog(
          `Forecast QA ${run.drift_level.replaceAll("_", " ")} · ${run.passed_count}/${run.evaluated_count} backtests passed`,
          run.drift_level === "stable" ? "good" : "neutral"
        );
        void loadPerformanceForecastValidationRuns(
          selectedOrganizationId,
          selectedAthlete?.athleteProfileId
        );
      }
    );
  };

  const sendPerformanceForecastValidationAlert = () => {
    if (!performanceForecastValidationRun) {
      addLog("Run Forecast QA before sending a drift alert", "bad");
      return;
    }
    const channelQuery = riskAlertChannelQuery();
    runAction(
      "performance-forecast-validation-alert",
      () =>
        apiRequest<PerformanceForecastValidationAlertRead>(
          `/performance/forecast-validation-runs/${performanceForecastValidationRun.id}/alerts?${channelQuery}`,
          {
            method: "POST",
            identity
          }
        ),
      (alert) => {
        setPerformanceForecastValidationAlert(alert);
        setPerformanceForecastValidationRun(alert.validation_run);
        addLog(
          alert.sent
            ? `Forecast drift alert sent across ${alert.channel_count} channel(s)`
            : alert.skipped_reason ?? "Forecast drift alert was not sent",
          alert.sent ? "good" : "neutral"
        );
      }
    );
  };

  const createPerformanceModelBenchmarkDataset = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization before creating a benchmark dataset", "bad");
      return;
    }
    runAction(
      "performance-model-benchmark-dataset",
      () =>
        apiRequest<PerformanceModelExtractionBenchmarkDatasetRead>("/performance/model-extraction/benchmark-datasets", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            name: "Narrative extraction baseline",
            slug: `narrative-extraction-${Date.now()}`,
            description: "Reusable parser and model-assisted extraction quality gate for coach, video, and agent narratives.",
            cases: [
              {
                case_id: "sleep-duration-number-word",
                metric_code: "sleep_minutes",
                metric_name: "Sleep Minutes",
                category: "wellness",
                unit: "minutes",
                min_value: 0,
                max_value: 900,
                source: "audio_narration",
                evidence_ref: "benchmark://audio/recovery-sleep-word",
                evidence_text: "Recovery note: sleep duration was seven hours after travel.",
                expected_value: 420,
                tolerance: 0.01
              },
              {
                case_id: "video-first-touch-specific-number",
                metric_code: "first_touch",
                metric_name: "First Touch",
                category: "technical",
                unit: "score",
                min_value: 0,
                max_value: 10,
                source: "video_analysis",
                evidence_ref: "benchmark://video/first-touch",
                evidence_text: "Video analysis marked first touch quality at 8.4 during the first phase.",
                expected_value: 8.4,
                tolerance: 0.01
              },
              {
                case_id: "agent-recovery-score",
                metric_code: "recovery_score",
                metric_name: "Recovery Score",
                category: "wellness",
                unit: "score",
                min_value: 0,
                max_value: 100,
                source: "agent_extracted",
                evidence_ref: "benchmark://agent/recovery-score",
                evidence_text: "Agent review says the recovery score came out at 74 after combining sleep and HRV.",
                expected_value: 74,
                tolerance: 0.01
              }
            ]
          }
        }),
      (dataset) => {
        setPerformanceModelBenchmarkDatasets((current) => [
          dataset,
          ...current.filter((item) => item.id !== dataset.id)
        ]);
        addLog(`${dataset.name} saved with ${dataset.case_count} benchmark cases`, "good");
      }
    );
  };

  const ingestPerformanceWearableWebhook = () => {
    const provider = observationForm.source_provider || "whoop";
    const metrics = metricDefinitions.filter((metric) =>
      [
        "hrv",
        "resting_heart_rate",
        "recovery_score",
        "hydration_score",
        "sleep_quality",
        "sleep_minutes",
        "stress",
        "strain",
        "temperature"
      ].includes(metric.code)
    );
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId || metrics.length === 0) {
      addLog("Select an athlete and create wearable metric definitions first", "bad");
      return;
    }
    runAction(
      "wearable-webhook-ingest",
      () =>
        apiRequest<PerformanceWearableWebhookRead>("/performance/webhooks/wearables", {
          method: "POST",
          body: {
            organization_id: selectedOrganizationId,
            athlete_profile_id: selectedAthlete.athleteProfileId,
            source_provider: provider,
            external_event_id: `${provider}-console-${Date.now()}`,
            event_id: selectedEventId || null,
            metric_definition_ids: metrics.map((metric) => metric.id),
            payload: wearableWebhookPayload(provider)
          }
        }),
      (ingest) => {
        setPerformanceWebhookIngest(ingest);
        addLog(`${ingest.source_provider} webhook accepted ${ingest.observation_count} observation(s)`, "good");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const createWearableConnection = () => {
    const provider = observationForm.source_provider || "whoop";
    const wearableMetricIds = metricDefinitions
      .filter((metric) =>
        ["hrv", "resting_heart_rate", "recovery_score", "sleep_quality", "stress", "strain"].includes(metric.code)
      )
      .map((metric) => metric.id);
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId) {
      addLog("Select an athlete before connecting a wearable provider", "bad");
      return;
    }
    runAction(
      "create-wearable-connection",
      () =>
        apiRequest<PerformanceWearableConnectionRead>("/performance/wearable-connections", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_profile_id: selectedAthlete.athleteProfileId,
            provider,
            display_name: `${provider.replaceAll("_", " ")} wearable feed`,
            external_athlete_ref: `${provider}-${selectedAthlete.athleteProfileId.slice(0, 8)}`,
            scopes: ["read:profile", "read:recovery", "read:metrics"],
            access_token_secret_path: `secret/data/afrolete/wearables/${selectedOrganizationId}/${selectedAthlete.athleteProfileId}/${provider}`,
            webhook_secret_path: `secret/data/afrolete/wearables/${selectedOrganizationId}/${selectedAthlete.athleteProfileId}/${provider}-webhook`,
            provider_pull_url: `https://${provider}.connect.example/api/wearables/pull`,
            provider_webhook_registration_url: `https://${provider}.connect.example/api/webhooks`,
            provider_webhook_callback_url: `${window.location.origin}/api/v1/performance/webhooks/wearables`,
            provider_webhook_event_types: ["metrics.created", "recovery.updated", "sleep.updated"],
            default_metric_definition_ids: wearableMetricIds
          }
        }),
      (connection) => {
        setWearableConnections((current) => [
          connection,
          ...current.filter((item) => item.id !== connection.id)
        ]);
        addLog(`${connection.provider} wearable connection configured`, "good");
      }
    );
  };

  const runWearableConnectionSync = () => {
    const connection = wearableConnections[0];
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId || !connection) {
      addLog("Create a wearable connection before syncing", "bad");
      return;
    }
    runAction(
      "sync-wearable-connection",
      () =>
        apiRequest<PerformanceWearableSyncRunRead>(`/performance/wearable-connections/${connection.id}/sync-runs`, {
          method: "POST",
          identity,
          body: {
            external_event_id: `${connection.provider}-sync-${Date.now()}`,
            payload: wearableWebhookPayload(connection.provider),
            metric_definition_ids: connection.default_metric_definition_ids
          }
        }),
      (syncRun) => {
        setWearableSyncRun(syncRun);
        addLog(`${syncRun.provider} sync ${syncRun.status}: ${syncRun.observation_count} observation(s)`, "good");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const runWearableConnectionPull = () => {
    const connection = wearableConnections[0];
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId || !connection) {
      addLog("Create a wearable connection before pulling provider data", "bad");
      return;
    }
    runAction(
      "pull-wearable-connection",
      () =>
        apiRequest<PerformanceWearableSyncRunRead>(`/performance/wearable-connections/${connection.id}/sync-runs`, {
          method: "POST",
          identity,
          body: {
            metric_definition_ids: connection.default_metric_definition_ids,
            since: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            until: new Date().toISOString()
          }
        }),
      (syncRun) => {
        setWearableSyncRun(syncRun);
        addLog(`${syncRun.provider} provider pull ${syncRun.status}`, syncRun.status === "completed" ? "good" : "neutral");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const registerWearableWebhook = () => {
    const connection = wearableConnections[0];
    if (!connection) {
      addLog("Create a wearable connection before registering provider webhooks", "bad");
      return;
    }
    runAction(
      "register-wearable-webhook",
      () =>
        apiRequest<PerformanceWearableWebhookRegistrationRead>(
          `/performance/wearable-connections/${connection.id}/webhook-registration`,
          {
            method: "POST",
            identity,
            body: {
              callback_url: connection.provider_webhook_callback_url ?? `${window.location.origin}/api/v1/performance/webhooks/wearables`,
              registration_url: connection.provider_webhook_registration_url,
              event_types: connection.provider_webhook_event_types.length
                ? connection.provider_webhook_event_types
                : ["metrics.created", "recovery.updated", "sleep.updated"],
              signing_secret_path:
                `secret/data/afrolete/wearables/${connection.organization_id}/${connection.athlete_profile_id}/${connection.provider}-webhook`,
              provider_payload: {
                athlete_ref: connection.external_athlete_ref,
                replay_protection: "external_event_id"
              }
            }
          }
        ),
      (registration) => {
        setWearableWebhookRegistration(registration);
        setWearableConnections((current) => [
          registration.connection,
          ...current.filter((item) => item.id !== registration.connection.id)
        ]);
        addLog(`${registration.connection.provider} webhook registration ${registration.status}`, registration.registered ? "good" : "bad");
      }
    );
  };

  const startWearableOAuth = () => {
    const connection = wearableConnections[0];
    if (!connection) {
      addLog("Create a wearable connection before OAuth authorization", "bad");
      return;
    }
    runAction(
      "start-wearable-oauth",
      () =>
        apiRequest<PerformanceWearableOAuthStartRead>(`/performance/wearable-connections/${connection.id}/oauth/start`, {
          method: "POST",
          identity,
          body: {
            client_id: `${connection.provider}-client`,
            authorization_url: `https://${connection.provider}.connect.example/oauth/authorize`,
            token_url: `https://${connection.provider}.connect.example/oauth/token`,
            redirect_uri: `${window.location.origin}/performance/wearables/callback`,
            scopes: connection.scopes.length ? connection.scopes : ["read:profile", "read:metrics"]
          }
        }),
      (oauthStart) => {
        setWearableOAuthStart(oauthStart);
        addLog(`${oauthStart.provider} OAuth URL prepared`, "good");
      }
    );
  };

  const completeWearableOAuth = () => {
    const connection = wearableConnections[0];
    if (!connection || !wearableOAuthStart) {
      addLog("Start wearable OAuth before completing it", "bad");
      return;
    }
    runAction(
      "complete-wearable-oauth",
      () =>
        apiRequest<PerformanceWearableOAuthCallbackRead>(`/performance/wearable-connections/${connection.id}/oauth/callback`, {
          method: "POST",
          identity,
          body: {
            state: wearableOAuthStart.state,
            code: `${connection.provider}-authorization-code`,
            access_token_secret_path: `secret/data/afrolete/wearables/${connection.organization_id}/${connection.athlete_profile_id}/${connection.provider}/access-token`,
            refresh_token_secret_path: `secret/data/afrolete/wearables/${connection.organization_id}/${connection.athlete_profile_id}/${connection.provider}/refresh-token`,
            provider_token_response: {
              access_token: `${connection.provider}-access-token-sample`,
              refresh_token: `${connection.provider}-refresh-token-sample`,
              expires_in: 30 * 24 * 60 * 60,
              token_type: "Bearer",
              scope: connection.scopes.length ? connection.scopes : ["read:profile", "read:metrics"]
            }
          }
        }),
      (callback) => {
        setWearableOAuthCallback(callback);
        setWearableConnections((current) => [
          callback.connection,
          ...current.filter((item) => item.id !== callback.connection.id)
        ]);
        addLog(`${callback.connection.provider} OAuth callback accepted`, "good");
      }
    );
  };

  const refreshWearableToken = () => {
    const connection = wearableConnections[0];
    if (!connection) {
      addLog("Create and authorize a wearable connection before refreshing tokens", "bad");
      return;
    }
    runAction(
      "refresh-wearable-token",
      () =>
        apiRequest<PerformanceWearableTokenRefreshRead>(`/performance/wearable-connections/${connection.id}/oauth/refresh`, {
          method: "POST",
          identity,
          body: {
            provider_token_response: {
              access_token: `${connection.provider}-access-token-rotated`,
              refresh_token: `${connection.provider}-refresh-token-rotated-${Date.now()}`,
              expires_in: 45 * 24 * 60 * 60,
              token_type: "Bearer",
              scope: [...new Set([...(connection.scopes.length ? connection.scopes : ["read:profile", "read:metrics"]), "read:recovery"])]
            }
          }
        }),
      (refresh) => {
        setWearableTokenRefresh(refresh);
        setWearableConnections((current) => [
          refresh.connection,
          ...current.filter((item) => item.id !== refresh.connection.id)
        ]);
        addLog(`${refresh.connection.provider} token refresh recorded`, "good");
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

  const createPerformanceGoal = () => {
    const metric = metricDefinitions[0];
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId || !metric) {
      addLog("Select an athlete and metric first", "bad");
      return;
    }
    runAction(
      "create-performance-goal",
      () =>
        apiRequest<PerformanceGoalRead>(
          `/performance/athletes/${selectedAthlete.athleteProfileId}/goals`,
          {
            method: "POST",
            identity,
            body: {
              organization_id: selectedOrganizationId,
              metric_definition_id: metric.id,
              ...performanceGoalForm,
              direction: metric.higher_is_better ? "increase" : "decrease"
            }
          }
        ),
      (goal) => {
        setPerformanceGoals((current) => [goal, ...current.filter((item) => item.id !== goal.id)]);
        addLog(`Goal created: ${goal.title}`, "good");
        void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
      }
    );
  };

  const evaluatePerformanceAchievements = () => {
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId) {
      addLog("Select an athlete first", "bad");
      return;
    }
    runAction(
      "evaluate-performance-achievements",
      () =>
        apiRequest<PerformanceAchievementRunRead>(
          `/performance/athletes/${selectedAthlete.athleteProfileId}/achievements/evaluate?organization_id=${selectedOrganizationId}`,
          {
            method: "POST",
            identity
          }
        ),
      (run) => {
        setPerformanceAchievementRun(run);
        setPerformanceAwards((current) => [
          ...run.awards,
          ...current.filter((award) => !run.awards.some((item) => item.id === award.id))
        ]);
        addLog(`Achievement scan awarded ${run.awarded_count} badge(s)`, run.awarded_count ? "good" : "neutral");
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

  const reviewAssessment = (assessment: AthleteAssessmentRead, verificationStatus: MetricVerificationStatus) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `review-assessment-${verificationStatus}`,
      () =>
        apiRequest<AthleteAssessmentRead>(
          `/performance/assessments/${assessment.id}/review`,
          {
            method: "PATCH",
            identity,
            body: {
              verification_status: verificationStatus,
              recommendations:
                verificationStatus === "verified"
                  ? "Coach verified player self-assessment from console."
                  : "Coach rejected player self-assessment from console."
            }
          }
        ),
      (reviewed) => {
        setAssessments((current) => [
          reviewed,
          ...current.filter((item) => item.id !== reviewed.id)
        ]);
        setAssessmentReviewQueue((current) =>
          reviewed.verification_status === "pending_review"
            ? current.map((item) =>
                item.assessment.id === reviewed.id ? { ...item, assessment: reviewed } : item
              )
            : current.filter((item) => item.assessment.id !== reviewed.id)
        );
        addLog(`Assessment ${verificationStatus}: ALS ${reviewed.overall_score}`, verificationStatus === "verified" ? "good" : "neutral");
        void loadAssessmentReviewQueue(selectedOrganizationId, assessmentReviewQueueFilters);
        void loadAssessmentReviewSummary(selectedOrganizationId);
        if (selectedAthlete?.athleteProfileId === reviewed.athlete_profile_id) {
          void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
        }
      }
    );
  };

  const updateAssessmentQueueItem = (
    assessment: AthleteAssessmentRead,
    body: {
      assign_to_self?: boolean;
      clear_assignment?: boolean;
      review_due_at?: string | null;
      review_priority?: "low" | "normal" | "high" | "urgent";
      review_notes?: string | null;
    },
    label: string
  ) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `assessment-queue-${assessment.id}-${label}`,
      () =>
        apiRequest<AthleteAssessmentRead>(
          `/performance/assessments/${assessment.id}/review-assignment`,
          {
            method: "PATCH",
            identity,
            body
          }
        ),
      (updated) => {
        setAssessments((current) =>
          current.map((item) => (item.id === updated.id ? updated : item))
        );
        setAssessmentReviewQueue((current) =>
          current.map((item) =>
            item.assessment.id === updated.id ? { ...item, assessment: updated } : item
          )
        );
        addLog(`Assessment queue updated: ${label.replaceAll("-", " ")}`, "good");
        void loadAssessmentReviewQueue(selectedOrganizationId, assessmentReviewQueueFilters);
        void loadAssessmentReviewSummary(selectedOrganizationId);
      }
    );
  };

  const runAssessmentReviewEscalations = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "assessment-review-escalations",
      () =>
        apiRequest<PerformanceAssessmentReviewEscalationRunRead>(
          `/performance/assessments/review-escalations?organization_id=${selectedOrganizationId}`,
          {
            method: "POST",
            identity
          }
        ),
      (run) => {
        setPerformanceReviewEscalationRun(run);
        addLog(
          `Review escalation sent ${run.escalated_count}/${run.eligible_count} item(s)`,
          run.escalated_count ? "good" : "neutral"
        );
        void loadAssessmentReviewQueue(selectedOrganizationId, assessmentReviewQueueFilters);
        void loadAssessmentReviewSummary(selectedOrganizationId);
      }
    );
  };

  const riskAlertChannelQuery = () => {
    const params = new URLSearchParams();
    const selectedChannels = performanceRiskAlertChannels.length ? performanceRiskAlertChannels : ["in_app" as CommunicationChannel];
    selectedChannels.forEach((channel) => params.append("channels", channel));
    return params.toString();
  };

  const togglePerformanceRiskAlertChannel = (channel: CommunicationChannel) => {
    setPerformanceRiskAlertChannels((current) => {
      if (current.includes(channel)) {
        const next = current.filter((item) => item !== channel);
        return next.length ? next : ["in_app"];
      }
      return [...current, channel];
    });
  };

  const sendPerformanceInjuryRiskAlert = () => {
    if (!selectedOrganizationId || !selectedAthlete?.athleteProfileId) {
      addLog("Select an athlete first", "bad");
      return;
    }
    const channelQuery = riskAlertChannelQuery();
    runAction(
      "performance-injury-risk-alert",
      () =>
        apiRequest<PerformanceInjuryRiskAlertRead>(
          `/performance/athletes/${selectedAthlete.athleteProfileId}/injury-risk/alerts?organization_id=${selectedOrganizationId}&${channelQuery}`,
          {
            method: "POST",
            identity
          }
        ),
      (alert) => {
        setPerformanceInjuryRiskAlert(alert);
        setPerformanceInjuryRisk(alert.risk);
        addLog(
          alert.sent
            ? `Injury-risk alert sent across ${alert.channel_count} channel(s)`
            : alert.skipped_reason ?? "Injury-risk alert was not sent",
          alert.sent ? "good" : "neutral"
        );
      }
    );
  };

  const runPerformanceInjuryRiskAlertScan = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const channelQuery = riskAlertChannelQuery();
    runAction(
      "performance-injury-risk-alert-scan",
      () =>
        apiRequest<PerformanceInjuryRiskAlertRunRead>(
          `/performance/injury-risk/alert-scans?organization_id=${selectedOrganizationId}&${channelQuery}`,
          {
            method: "POST",
            identity
          }
        ),
      (run) => {
        setPerformanceInjuryRiskAlertRun(run);
        addLog(
          `Injury-risk scan alerted ${run.alerted_count}/${run.high_risk_count} high-risk athlete(s)`,
          run.alerted_count ? "good" : "neutral"
        );
        if (selectedAthlete?.athleteProfileId) {
          void loadAthletePerformance(selectedOrganizationId, selectedAthlete.athleteProfileId);
        }
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

  const escalateSelectedMessage = () => {
    if (!selectedMessageId) {
      addLog("Select an urgent communication first", "bad");
      return;
    }

    runAction(
      "escalate-communication",
      () =>
        apiRequest<CommunicationEscalationRunRead>(`/communications/messages/${selectedMessageId}/escalate`, {
          method: "POST",
          identity,
          body: {
            channel: messageForm.channel === "sms" ? "whatsapp" : "sms",
            escalation_level: 2,
            failed_only: false
          }
        }),
      (escalation) => {
        setEscalationRun(escalation);
        if (escalation.escalation_message_id) {
          setSelectedMessageId(escalation.escalation_message_id);
        }
        addLog(escalation.message, escalation.target_count > 0 ? "bad" : "neutral");
        if (selectedOrganizationId) {
          void loadCommunications(selectedOrganizationId);
        }
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

  const createEmergencyPlan = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-emergency-plan",
      () =>
        apiRequest<EmergencyActionPlanRead>("/assets/emergency-plans", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            facility_id: selectedFacilityId || null,
            title: emergencyPlanForm.title,
            emergency_type: emergencyPlanForm.emergency_type,
            effective_from: emergencyPlanForm.effective_from || null,
            review_due_on: emergencyPlanForm.review_due_on || null,
            emergency_contacts: emergencyPlanForm.emergency_contacts,
            evacuation_routes: emergencyPlanForm.evacuation_routes || null,
            medical_protocols: emergencyPlanForm.medical_protocols || null,
            weather_protocols: emergencyPlanForm.weather_protocols || null,
            communication_protocols: emergencyPlanForm.communication_protocols || null,
            incident_command_roles: emergencyPlanForm.incident_command_roles || null,
            escalation_matrix: emergencyPlanForm.escalation_matrix || null,
            external_agency_contacts: emergencyPlanForm.external_agency_contacts || null,
            equipment_locations: emergencyPlanForm.equipment_locations || null,
            assembly_points: emergencyPlanForm.assembly_points || null,
            special_needs_plan: emergencyPlanForm.special_needs_plan || null,
            notes: emergencyPlanForm.notes || null
          }
        }),
      (plan) => {
        setEmergencyPlans((current) => [plan, ...current.filter((item) => item.id !== plan.id)]);
        addLog(`${plan.title} emergency plan drafted`, "good");
      }
    );
  };

  const updateEmergencyPlan = (
    plan: EmergencyActionPlanRead,
    statusValue: EmergencyActionPlanStatus
  ) => {
    runAction(
      `emergency-plan-${plan.id}-${statusValue}`,
      () =>
        apiRequest<EmergencyActionPlanRead>(`/assets/emergency-plans/${plan.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            review_due_on: emergencyPlanForm.review_due_on || null,
            incident_command_roles: emergencyPlanForm.incident_command_roles || null,
            escalation_matrix: emergencyPlanForm.escalation_matrix || null,
            external_agency_contacts: emergencyPlanForm.external_agency_contacts || null,
            notes: `Marked ${statusValue} from the operations console.`
          }
        }),
      (updated) => {
        setEmergencyPlans((current) => [updated, ...current.filter((item) => item.id !== updated.id)]);
        addLog(`${updated.title} moved to ${updated.status}`, "good");
      }
    );
  };

  const activateEmergencyPlan = (plan: EmergencyActionPlanRead) => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      `activate-emergency-plan-${plan.id}`,
      () =>
        apiRequest<EmergencyPlanActivationRead>("/assets/emergency-activations", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            plan_id: plan.id,
            facility_id: plan.facility_id || selectedFacilityId || null,
            emergency_type: plan.emergency_type,
            location_detail: emergencyPlanForm.activation_location,
            escalation_level: 1,
            assigned_responders: emergencyPlanForm.responders || null,
            notes: "Emergency mode activated from the operations console."
          }
        }),
      (activation) => {
        setEmergencyActivations((current) => [
          activation,
          ...current.filter((item) => item.id !== activation.id)
        ]);
        addLog(`${activation.emergency_type} emergency activated`, "bad");
      }
    );
  };

  const updateEmergencyActivation = (
    activation: EmergencyPlanActivationRead,
    statusValue: EmergencyActivationStatus | null,
    escalationLevel = activation.escalation_level
  ) => {
    runAction(
      `emergency-activation-${activation.id}-${statusValue ?? `level-${escalationLevel}`}`,
      () =>
        apiRequest<EmergencyPlanActivationRead>(`/assets/emergency-activations/${activation.id}`, {
          method: "PATCH",
          identity,
          body: {
            status: statusValue,
            escalation_level: escalationLevel,
            outcome_summary:
              statusValue === "resolved" || statusValue === "reviewed"
                ? "Emergency response closed and queued for after-action review."
                : null,
            response_time_seconds: statusValue === "resolved" ? 180 : null,
            notes: statusValue
              ? `Marked ${statusValue} from the operations console.`
              : `Escalated to level ${escalationLevel} from the operations console.`
          }
        }),
      (updated) => {
        setEmergencyActivations((current) => [
          updated,
          ...current.filter((item) => item.id !== updated.id)
        ]);
        addLog(`${updated.emergency_type} activation is ${updated.status} at level ${updated.escalation_level}`, "good");
      }
    );
  };

  const dispatchEmergencyAlert = (activation: EmergencyPlanActivationRead) => {
    runAction(
      `emergency-alert-${activation.id}`,
      () =>
        apiRequest<EmergencyActivationAlertRead>(`/assets/emergency-activations/${activation.id}/alerts`, {
          method: "POST",
          identity,
          body: {
            channel: emergencyPlanForm.alert_channel,
            scope_type: "organization" as CommunicationScopeType,
            scope_id: selectedOrganizationId || activation.organization_id,
            body: emergencyPlanForm.alert_body || null,
            copy_guardians_for_minors: true
          }
        }),
      (alert) => {
        setEmergencyAlert(alert);
        setSelectedMessageId(alert.message_id);
        addLog(`Emergency alert sent to ${alert.recipient_count} recipients`, "bad");
        void loadCommunications(activation.organization_id);
      }
    );
  };

  const createEmergencyIncident = (activation: EmergencyPlanActivationRead) => {
    runAction(
      `emergency-incident-${activation.id}`,
      () =>
        apiRequest<SafeguardingIncidentRead>(`/assets/emergency-activations/${activation.id}/incident`, {
          method: "POST",
          identity,
          body: {
            severity: activation.escalation_level >= 4 ? "critical" : activation.escalation_level >= 2 ? "high" : "medium",
            medical_follow_up_required: activation.emergency_type === "medical" ? "yes" : "unknown",
            regulatory_report_required: activation.escalation_level >= 4
          }
        }),
      (incident) => {
        setSafeguardingIncidents((current) => [
          incident,
          ...current.filter((item) => item.id !== incident.id)
        ]);
        setEmergencyActivations((current) =>
          current.map((item) =>
            item.id === activation.id ? { ...item, incident_id: incident.id } : item
          )
        );
        addLog(`${incident.title} incident linked`, incident.severity === "critical" ? "bad" : "good");
        refreshSafeguardingCompliance();
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

  const downloadEquipmentFile = (fileRecord: EquipmentFileRead) => {
    runAction(
      `download-equipment-file-${fileRecord.id}`,
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
          `${apiBaseUrl}/api/v1/assets/equipment/files/${fileRecord.id}/download`,
          { headers }
        );
        if (!response.ok) {
          throw new Error(`Equipment file download failed: ${response.status}`);
        }
        const blob = await response.blob();
        const href = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = href;
        anchor.download = fileRecord.filename;
        document.body.append(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(href);
        return {
          filename: fileRecord.filename,
          checksum: response.headers.get("X-Afrolete-Equipment-Checksum") ?? fileRecord.checksum,
          size: blob.size
        };
      },
      (download) => {
        addLog(`${download.filename} downloaded (${download.size} bytes, ${download.checksum.slice(0, 8)})`, "good");
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
          `/commercial/tax-quote?organization_id=${selectedOrganizationId}&subtotal=${invoiceForm.amount_due}&tax_rate=${invoiceForm.tax_rate}&jurisdiction=${invoiceForm.tax_jurisdiction}`
        ),
      (quote) => {
        setTaxQuote(quote);
        addLog(`Tax quote total ${quote.total}`, "good");
      }
    );
  };

  const fileCommercialTax = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "commercial-tax-filing",
      () =>
        apiRequest<CommercialTaxFilingRead>(
          `/commercial/tax-filing/deliver?organization_id=${selectedOrganizationId}&period_start=${invoiceForm.tax_period_start}&period_end=${invoiceForm.tax_period_end}&jurisdiction=${invoiceForm.tax_jurisdiction}&tax_rate=${invoiceForm.tax_rate}`,
          {
            method: "POST",
            identity
          }
        ),
      (filing) => {
        setCommercialTaxFiling(filing);
        addLog(
          filing.delivered ? "Commercial tax filing delivered" : filing.failure_reason ?? "Commercial tax filing package prepared",
          filing.delivered ? "good" : "neutral"
        );
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

  const executeCommercialPayout = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "commercial-payout",
      () =>
        apiRequest<CommercialSettlementPayoutRead>(
          `/commercial/settlements/payout?organization_id=${selectedOrganizationId}&provider=manual_gateway&fee_rate=2.9&fixed_fee=0.3`,
          {
            method: "POST",
            identity
          }
        ),
      (payout) => {
        setCommercialPayout(payout);
        setCommercialPayouts((current) => [payout, ...current.filter((item) => item.id !== payout.id)]);
        addLog(
          payout.delivered
            ? `Payout delivered: ${payout.payout_batch_reference}`
            : `Payout prepared: ${payout.payout_batch_reference}`,
          payout.failure_reason ? "neutral" : "good"
        );
      }
    );
  };

  const reconcileCommercialPayout = (statusValue: "paid" | "failed" | "returned") => {
    const payout = commercialPayout ?? commercialPayouts[0];
    if (!payout) {
      addLog("Execute a payout before reconciling provider status", "neutral");
      return;
    }
    runAction(
      `commercial-payout-callback-${statusValue}`,
      () =>
        apiRequest<CommercialSettlementPayoutCallbackRead>("/commercial/settlements/payout-callbacks", {
          method: "POST",
          body: {
            provider: payout.provider,
            payout_batch_reference: payout.payout_batch_reference,
            idempotency_key: payout.idempotency_key,
            status: statusValue,
            provider_status_code: statusValue === "paid" ? 200 : 422,
            external_event_id: `commercial-payout-${statusValue}-${Date.now()}`,
            raw_payload: {
              source: "operations_console",
              payout_reference: payout.payout_reference
            }
          }
        }),
      (callback) => {
        setCommercialPayout(callback.payout);
        setCommercialPayouts((current) => [callback.payout, ...current.filter((item) => item.id !== callback.payout.id)]);
        addLog(callback.message, callback.payout_status === "paid" ? "good" : "neutral");
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

  const syncCommercialAccounting = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "commercial-accounting-sync",
      () =>
        apiRequest<AccountingSyncRead>(
          `/commercial/accounting-export/sync?organization_id=${selectedOrganizationId}&system=generic&basis=cash`,
          {
            method: "POST",
            identity
          }
        ),
      (sync) => {
        setAccountingSync(sync);
        addLog(
          sync.delivered
            ? `Accounting sync delivered: ${sync.sync_reference}`
            : `Accounting sync prepared: ${sync.sync_reference}`,
          sync.failure_reason ? "neutral" : "good"
        );
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

  const createDeveloperApplication = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-developer-application",
      () =>
        apiRequest<DeveloperApplicationProvisionedRead>("/developers/applications", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            name: developerForm.app_name,
            app_type: developerForm.app_type,
            redirect_uris: parseCommaList(developerForm.redirect_uris),
            scopes: parseCommaList(developerForm.app_scopes),
            contact_email: developerForm.contact_email || null,
            notes: "Created from AfroLete developer console."
          }
        }),
      (provisioned) => {
        setDeveloperApplicationSecret(provisioned);
        setDeveloperApplications((current) => [
          provisioned.application,
          ...current.filter((item) => item.id !== provisioned.application.id)
        ]);
        addLog(`${provisioned.application.name} developer app created`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const rotateDeveloperApplicationSecret = (applicationId: string) => {
    runAction(
      "rotate-developer-secret",
      () =>
        apiRequest<DeveloperApplicationProvisionedRead>(
          `/developers/applications/${applicationId}/rotate-secret`,
          { method: "POST", identity }
        ),
      (provisioned) => {
        setDeveloperApplicationSecret(provisioned);
        setDeveloperApplications((current) =>
          current.map((item) => (item.id === provisioned.application.id ? provisioned.application : item))
        );
        addLog(`${provisioned.application.name} secret rotated`, "good");
      }
    );
  };

  const createDeveloperApiKey = () => {
    if (!selectedOrganizationId || developerApplications.length === 0) {
      addLog("Create a developer application first", "bad");
      return;
    }
    runAction(
      "create-developer-api-key",
      () =>
        apiRequest<DeveloperApiKeyProvisionedRead>("/developers/api-keys", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            application_id: developerApplications[0].id,
            name: developerForm.api_key_name,
            scopes: parseCommaList(developerForm.app_scopes),
            environment: developerForm.api_key_environment,
            rate_limit_per_minute: developerForm.api_key_rate_limit,
            notes: "Created from AfroLete developer console."
          }
        }),
      (provisioned) => {
        setDeveloperApiKeySecret(provisioned);
        setDeveloperApiKeys((current) => [
          provisioned.api_key,
          ...current.filter((item) => item.id !== provisioned.api_key.id)
        ]);
        addLog(`${provisioned.api_key.name} API key issued`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const revokeDeveloperApiKey = (apiKeyId: string) => {
    runAction(
      "revoke-developer-api-key",
      () =>
        apiRequest<DeveloperApiKeyRead>(`/developers/api-keys/${apiKeyId}/revoke`, {
          method: "POST",
          identity
        }),
      (apiKey) => {
        setDeveloperApiKeys((current) => current.map((item) => (item.id === apiKey.id ? apiKey : item)));
        addLog(`${apiKey.name} revoked`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const createDeveloperOAuthAuthorization = () => {
    const application = developerApplications[0];
    if (!selectedOrganizationId || !application) {
      addLog("Create a developer application first", "bad");
      return;
    }
    const redirectUri = application.redirect_uris[0] ?? parseCommaList(developerForm.redirect_uris)[0];
    if (!redirectUri) {
      addLog("Register a redirect URI before OAuth consent", "bad");
      return;
    }
    runAction(
      "create-developer-oauth-authorization",
      () =>
        apiRequest<DeveloperOAuthAuthorizationRead>("/developers/oauth/authorizations", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            client_id: application.client_id,
            redirect_uri: redirectUri,
            scopes: parseCommaList(developerForm.app_scopes),
            state: `console-${Date.now()}`,
            code_challenge: developerForm.oauth_code_challenge || null,
            code_challenge_method: developerForm.oauth_code_challenge
              ? developerForm.oauth_code_challenge_method
              : null
          }
        }),
      (authorization) => {
        setDeveloperOAuthGrant(authorization);
        setDeveloperOAuthAuthorizations((current) => [
          authorization,
          ...current.filter((item) => item.id !== authorization.id)
        ]);
        addLog(`${authorization.application_name} OAuth consent granted`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const createDeveloperWebhook = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-developer-webhook",
      () =>
        apiRequest<DeveloperWebhookSubscriptionProvisionedRead>("/developers/webhook-subscriptions", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            application_id: developerApplications[0]?.id ?? null,
            name: developerForm.webhook_name,
            target_url: developerForm.webhook_url,
            event_types: parseCommaList(developerForm.webhook_events),
            delivery_mode: developerForm.webhook_delivery_mode
          }
        }),
      (provisioned) => {
        setDeveloperWebhookSecret(provisioned);
        setDeveloperWebhooks((current) => [
          provisioned.subscription,
          ...current.filter((item) => item.id !== provisioned.subscription.id)
        ]);
        addLog(`${provisioned.subscription.name} webhook created`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const createDeveloperListing = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-developer-listing",
      () =>
        apiRequest<DeveloperMarketplaceListingRead>("/developers/marketplace-listings", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            application_id: developerApplications[0]?.id ?? null,
            name: developerForm.listing_name,
            category: developerForm.listing_category,
            summary: developerForm.listing_summary,
            install_url: developerForm.listing_install_url || null,
            support_url: developerForm.listing_support_url || null
          }
        }),
      (listing) => {
        setDeveloperListings((current) => [listing, ...current.filter((item) => item.id !== listing.id)]);
        addLog(`${listing.name} listing drafted`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const approveDeveloperListing = (listingId: string) => {
    runAction(
      "approve-developer-listing",
      () =>
        apiRequest<DeveloperMarketplaceListingRead>(
          `/developers/marketplace-listings/${listingId}/review`,
          {
            method: "PATCH",
            identity,
            body: { review_status: "approved", visibility: "public" }
          }
        ),
      (listing) => {
        setDeveloperListings((current) => current.map((item) => (item.id === listing.id ? listing : item)));
        addLog(`${listing.name} approved for marketplace`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const recordDeveloperListingInstall = (listingId: string) => {
    runAction(
      "install-developer-listing",
      () =>
        apiRequest<DeveloperMarketplaceListingRead>(
          `/developers/marketplace-listings/${listingId}/install`,
          { method: "POST", identity }
        ),
      (listing) => {
        setDeveloperListings((current) => current.map((item) => (item.id === listing.id ? listing : item)));
        addLog(`${listing.name} install recorded`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const replayDeveloperWebhookDelivery = (deliveryId: string) => {
    runAction(
      "replay-developer-webhook",
      () =>
        apiRequest<DeveloperWebhookDeliveryRead>(
          `/developers/webhook-deliveries/${deliveryId}/replay`,
          { method: "POST", identity }
        ),
      (delivery) => {
        setDeveloperWebhookDeliveries((current) =>
          current.map((item) => (item.id === delivery.id ? delivery : item))
        );
        addLog(`${delivery.event_type} webhook replay ${delivery.status}`, "good");
        void loadDevelopers(selectedOrganizationId);
      }
    );
  };

  const retryDeveloperWebhookDeliveries = () => {
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "retry-developer-webhooks",
      () =>
        apiRequest<DeveloperWebhookRetryRunRead>(
          `/developers/webhook-deliveries/retry-due?organization_id=${selectedOrganizationId}&max_attempts=5&limit=25&include_recorded=true`,
          { method: "POST", identity }
        ),
      (run) => {
        setDeveloperWebhookRetryRun(run);
        addLog(`${run.replayed_count}/${run.eligible_count} webhook deliveries retried`, "good");
        void loadDevelopers(selectedOrganizationId);
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
          <a href="#developers">Developers</a>
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

        <section className="infrastructure-ribbon" aria-label="Infrastructure readiness">
          <div className="infra-summary">
            <p className="section-label">Infrastructure</p>
            <strong>
              {infrastructureStatus
                ? `${infrastructureReadyCount} active · ${infrastructureStandbyCount} standby`
                : "Checking runtime"}
            </strong>
            <span>
              {infrastructureStatus
                ? `${infrastructureStatus.environment} · ${infrastructureAttentionCount} attention · ${infrastructureProbeFailures} probe failures`
                : "Postgres, Keycloak, SpiceDB, OpenBao, object storage, Redis, Temporal"}
            </span>
          </div>
          <div className="infra-strip">
            {(infrastructureStatus?.components ?? []).map((component) => {
              const probe = infrastructureProbeByKey.get(component.key);
              const tone = probe?.reachable === false ? "attention" : infrastructureTone(component);
              return (
                <article className={`infra-chip ${tone}`} key={component.key}>
                  <div>
                    <strong>{component.name}</strong>
                    <span>
                      {component.mode} · {component.status}
                      {probe ? ` · ${probe.status}` : ""}
                    </span>
                  </div>
                  <small>
                    {probe?.latency_ms !== null && probe?.latency_ms !== undefined
                      ? `${probe.latency_ms}ms · ${probe.details[0] ?? component.endpoint ?? "checked"}`
                      : component.endpoint ?? component.details[0] ?? "not set"}
                  </small>
                </article>
              );
            })}
            {!infrastructureStatus ? (
              <article className="infra-chip standby">
                <div>
                  <strong>Runtime</strong>
                  <span>loading · configuration</span>
                </div>
                <small>{apiBaseUrl.replace("http://", "")}</small>
              </article>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() =>
              void runAction("load-infrastructure", loadInfrastructure, ({ status, probes }) => {
                const attentionCount = status.components.filter(
                  (component) => infrastructureTone(component) === "attention"
                ).length;
                const probeFailures = probes.results.filter((result) => result.reachable === false).length;
                addLog(
                  attentionCount > 0 || probeFailures > 0
                    ? `${attentionCount} configured dependency issue(s), ${probeFailures} live probe failure(s)`
                    : "Infrastructure readiness synchronized",
                  attentionCount > 0 || probeFailures > 0 ? "bad" : "good"
                );
              })
            }
            disabled={busyAction !== null}
          >
            Refresh
          </button>
        </section>

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
            <div className="task-list">
              {registrationInquiries.slice(0, 4).map((inquiry) => {
                const reviewForm = inquiryReviewForms[inquiry.id];
                const reviewStatus = reviewForm?.status ?? inquiry.status;
                const reviewNotes = reviewForm?.review_notes ?? inquiry.review_notes ?? "";
                const followUpAt = reviewForm?.follow_up_at ?? toDateTimeLocalValue(inquiry.follow_up_at);
                return (
                  <article key={inquiry.id} className="task-card inquiry-review-card">
                    <div>
                      <strong>{inquiry.athlete_name}</strong>
                      <span>{inquiry.email} · {inquiry.age_group ?? "age open"} · {inquiry.status}</span>
                      {inquiry.phone ? <small>{inquiry.phone}</small> : null}
                      {inquiry.message ? <small>{inquiry.message}</small> : null}
                    </div>
                    <div className="form-grid compact-form-grid">
                      <label>
                        Review
                        <select
                          value={reviewStatus}
                          onChange={(event) => updateInquiryReviewForm(inquiry, "status", event.target.value)}
                          disabled={inquiry.status === "converted"}
                        >
                          <option value="new">New</option>
                          <option value="reviewing">Reviewing</option>
                          <option value="contacted">Contacted</option>
                          <option value="waitlisted">Waitlisted</option>
                          <option value="rejected">Rejected</option>
                          {inquiry.status === "converted" ? <option value="converted">Converted</option> : null}
                        </select>
                      </label>
                      <label>
                        Follow-up
                        <input
                          type="datetime-local"
                          value={followUpAt}
                          onChange={(event) => updateInquiryReviewForm(inquiry, "follow_up_at", event.target.value)}
                        />
                      </label>
                    </div>
                    <label>
                      Notes
                      <textarea
                        value={reviewNotes}
                        onChange={(event) => updateInquiryReviewForm(inquiry, "review_notes", event.target.value)}
                        placeholder="Contact attempts, eligibility notes, waitlist reason"
                      />
                    </label>
                    <div className="event-toolbar">
                      <button
                        type="button"
                        onClick={() => updateRegistrationInquiryReview(inquiry)}
                        disabled={busyAction !== null}
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => updateRegistrationInquiryReview(inquiry, "contacted")}
                        disabled={busyAction !== null || inquiry.status === "converted"}
                      >
                        Contacted
                      </button>
                      <button
                        type="button"
                        onClick={() => updateRegistrationInquiryReview(inquiry, "waitlisted")}
                        disabled={busyAction !== null || inquiry.status === "converted"}
                      >
                        Waitlist
                      </button>
                      <button
                        type="button"
                        onClick={() => sendRegistrationInquiryFollowUp(inquiry)}
                        disabled={busyAction !== null || inquiry.status === "converted"}
                      >
                        Follow up
                      </button>
                      <button
                        type="button"
                        onClick={() => convertRegistrationInquiry(inquiry)}
                        disabled={busyAction !== null || inquiry.status === "converted"}
                      >
                        Convert
                      </button>
                    </div>
                  </article>
                );
              })}
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
                Country
                <input maxLength={2} value={athleteForm.country_code} onChange={(event) => setAthleteForm({ ...athleteForm, country_code: event.target.value.toUpperCase() })} />
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
              <button type="button" onClick={assessEventWeather} disabled={busyAction !== null}>Weather check</button>
              <button type="button" onClick={runWeatherAutomation} disabled={busyAction !== null}>Weather automation</button>
              <button type="button" onClick={createTravelPlan} disabled={busyAction !== null}>Travel plan</button>
              <button type="button" onClick={runTravelConsentReminderAutomation} disabled={busyAction !== null}>Auto reminders</button>
              <button type="button" onClick={loadTravelDeviceFleetInventory} disabled={busyAction !== null}>GPS fleet</button>
            </div>
            <div className="form-grid three">
              <label>
                Observed
                <input type="datetime-local" value={weatherForm.observed_at} onChange={(event) => setWeatherForm({ ...weatherForm, observed_at: event.target.value })} />
              </label>
              <label>
                WBGT C
                <input type="number" step="0.1" value={weatherForm.wbgt_c} onChange={(event) => setWeatherForm({ ...weatherForm, wbgt_c: Number(event.target.value) })} />
              </label>
              <label>
                Lightning km
                <input type="number" step="0.1" min="0" value={weatherForm.lightning_distance_km} onChange={(event) => setWeatherForm({ ...weatherForm, lightning_distance_km: Number(event.target.value) })} />
              </label>
              <label>
                AQI
                <input type="number" min="0" value={weatherForm.aqi} onChange={(event) => setWeatherForm({ ...weatherForm, aqi: Number(event.target.value) })} />
              </label>
              <label>
                Gust kph
                <input type="number" step="0.1" min="0" value={weatherForm.wind_gust_kph} onChange={(event) => setWeatherForm({ ...weatherForm, wind_gust_kph: Number(event.target.value) })} />
              </label>
              <label>
                Rain mm/hr
                <input type="number" step="0.1" min="0" value={weatherForm.precipitation_mm_per_hr} onChange={(event) => setWeatherForm({ ...weatherForm, precipitation_mm_per_hr: Number(event.target.value) })} />
              </label>
              <label>
                Alert channel
                <select value={weatherForm.alert_channel} onChange={(event) => setWeatherForm({ ...weatherForm, alert_channel: event.target.value as CommunicationChannel })}>
                  <option value="push">Push</option>
                  <option value="in_app">In app</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="email">Email</option>
                </select>
              </label>
            </div>
            <div className="task-list">
              {weatherAutomation ? (
                <article className="task-card">
                  <div>
                    <strong>Weather automation · {weatherAutomation.channel}</strong>
                    <span>{weatherAutomation.dispatched_count} dispatched · {weatherAutomation.skipped_count} skipped · threshold {weatherAutomation.minimum_alert_level}</span>
                    <span>{weatherAutomation.items[0]?.reason ?? "No assessments met the automation threshold"}</span>
                  </div>
                </article>
              ) : null}
              {weatherAlert ? (
                <article className="task-card">
                  <div>
                    <strong>{weatherAlert.subject}</strong>
                    <span>{weatherAlert.channel} · {weatherAlert.recipient_count} recipients</span>
                    <span>Message {weatherAlert.message_id}</span>
                  </div>
                </article>
              ) : null}
              {weatherAssessments.slice(0, 2).map((assessment) => (
                <article key={assessment.id} className="task-card">
                  <div>
                    <strong>{assessment.alert_level} · {assessment.decision}</strong>
                    <span>
                      WBGT {assessment.wbgt_c ?? assessment.heat_index_c ?? "n/a"}C · AQI {assessment.aqi ?? "n/a"} · lightning {assessment.lightning_distance_km ?? "n/a"} km
                    </span>
                    <span>{assessment.recommended_actions}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => dispatchWeatherAlert(assessment)}>Alert</button>
                  </div>
                </article>
              ))}
            </div>
            <div className="form-grid three">
              <label>
                Destination
                <input value={travelForm.destination} onChange={(event) => setTravelForm({ ...travelForm, destination: event.target.value })} />
              </label>
              <label>
                Mode
                <input value={travelForm.travel_mode} onChange={(event) => setTravelForm({ ...travelForm, travel_mode: event.target.value })} />
              </label>
              <label>
                Depart
                <input type="datetime-local" value={travelForm.departure_at} onChange={(event) => setTravelForm({ ...travelForm, departure_at: event.target.value })} />
              </label>
              <label>
                Return
                <input type="datetime-local" value={travelForm.return_at} onChange={(event) => setTravelForm({ ...travelForm, return_at: event.target.value })} />
              </label>
              <label>
                Weather risk
                <input value={travelForm.route_weather_risk} onChange={(event) => setTravelForm({ ...travelForm, route_weather_risk: event.target.value })} />
              </label>
              <label>
                Driver
                <input value={travelForm.driver_certification_status} onChange={(event) => setTravelForm({ ...travelForm, driver_certification_status: event.target.value })} />
              </label>
              <label>
                Vehicle
                <input value={travelForm.vehicle_inspection_status} onChange={(event) => setTravelForm({ ...travelForm, vehicle_inspection_status: event.target.value })} />
              </label>
              <label>
                Cost
                <input type="number" min="0" value={travelForm.estimated_cost} onChange={(event) => setTravelForm({ ...travelForm, estimated_cost: Number(event.target.value) })} />
              </label>
              <label>
                Per participant
                <input type="number" min="0" value={travelForm.cost_per_participant} onChange={(event) => setTravelForm({ ...travelForm, cost_per_participant: Number(event.target.value) })} />
              </label>
              <label>
                Consent due
                <input type="datetime-local" value={travelForm.consent_due_at} onChange={(event) => setTravelForm({ ...travelForm, consent_due_at: event.target.value })} />
              </label>
              <label>
                Consent channel
                <select value={travelForm.consent_channel} onChange={(event) => setTravelForm({ ...travelForm, consent_channel: event.target.value as ConsentCaptureChannel })}>
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="web_link">Web link</option>
                </select>
              </label>
              <label>
                Reminder channel
                <select value={travelForm.reminder_channel} onChange={(event) => setTravelForm({ ...travelForm, reminder_channel: event.target.value as CommunicationChannel })}>
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="push">Push</option>
                  <option value="in_app">In app</option>
                </select>
              </label>
              <label>
                Approval level
                <select value={travelForm.approval_level} onChange={(event) => setTravelForm({ ...travelForm, approval_level: event.target.value })}>
                  <option value="school">School</option>
                  <option value="association">Association</option>
                  <option value="operations">Operations</option>
                  <option value="medical">Medical</option>
                  <option value="finance">Finance</option>
                </select>
              </label>
              <label>
                Checklist
                <select value={travelForm.checklist_type} onChange={(event) => setTravelForm({ ...travelForm, checklist_type: event.target.value })}>
                  <option value="pre_trip_inspection">Pre-trip inspection</option>
                  <option value="departure">Departure</option>
                  <option value="arrival">Arrival</option>
                  <option value="emergency">Emergency</option>
                </select>
              </label>
              <label>
                Tracking phase
                <select value={travelForm.tracking_phase} onChange={(event) => setTravelForm({ ...travelForm, tracking_phase: event.target.value })}>
                  <option value="departed">Departed</option>
                  <option value="en_route">En route</option>
                  <option value="delayed">Delayed</option>
                  <option value="arrived">Arrived</option>
                  <option value="returned">Returned</option>
                </select>
              </label>
              <label>
                Tracking channel
                <select value={travelForm.tracking_channel} onChange={(event) => setTravelForm({ ...travelForm, tracking_channel: event.target.value as CommunicationChannel })}>
                  <option value="push">Push</option>
                  <option value="in_app">In app</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="email">Email</option>
                </select>
              </label>
              <label>
                Latitude
                <input type="number" step="0.000001" value={travelForm.latitude} onChange={(event) => setTravelForm({ ...travelForm, latitude: Number(event.target.value) })} />
              </label>
              <label>
                Longitude
                <input type="number" step="0.000001" value={travelForm.longitude} onChange={(event) => setTravelForm({ ...travelForm, longitude: Number(event.target.value) })} />
              </label>
              <label>
                Speed kph
                <input type="number" min="0" value={travelForm.speed_kph} onChange={(event) => setTravelForm({ ...travelForm, speed_kph: Number(event.target.value) })} />
              </label>
              <label>
                Device provider
                <input value={travelForm.device_provider} onChange={(event) => setTravelForm({ ...travelForm, device_provider: event.target.value })} />
              </label>
              <label>
                Device ID
                <input value={travelForm.device_id} onChange={(event) => setTravelForm({ ...travelForm, device_id: event.target.value })} />
              </label>
              <label>
                Device label
                <input value={travelForm.device_label} onChange={(event) => setTravelForm({ ...travelForm, device_label: event.target.value })} />
              </label>
              <label>
                Device status
                <select value={travelForm.device_status} onChange={(event) => setTravelForm({ ...travelForm, device_status: event.target.value as EventTravelDeviceRead["status"] })}>
                  <option value="active">Active</option>
                  <option value="standby">Standby</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="disabled">Disabled</option>
                  <option value="lost">Lost</option>
                </select>
              </label>
              <label>
                Device vehicle
                <input value={travelForm.device_vehicle} onChange={(event) => setTravelForm({ ...travelForm, device_vehicle: event.target.value })} />
              </label>
              <label>
                Backup driver
                <input value={travelForm.backup_driver_name} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_name: event.target.value })} />
              </label>
              <label>
                Backup phone
                <input value={travelForm.backup_driver_phone} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_phone: event.target.value })} />
              </label>
              <label>
                Backup vehicle
                <input value={travelForm.backup_driver_vehicle} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_vehicle: event.target.value })} />
              </label>
              <label>
                Backup capacity
                <input type="number" min="0" max="80" value={travelForm.backup_driver_capacity} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_capacity: Number(event.target.value) })} />
              </label>
              <label>
                Backup availability
                <select value={travelForm.backup_driver_availability} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_availability: event.target.value as EventTravelBackupDriverRead["availability_status"] })}>
                  <option value="standby">Standby</option>
                  <option value="available">Available</option>
                  <option value="dispatched">Dispatched</option>
                  <option value="unavailable">Unavailable</option>
                </select>
              </label>
              <label>
                Backup license
                <input value={travelForm.backup_driver_license_status} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_license_status: event.target.value })} />
              </label>
              <label>
                Backup screening
                <input value={travelForm.backup_driver_background_status} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_background_status: event.target.value })} />
              </label>
              <label>
                Backup response
                <input type="number" min="0" max="1440" value={travelForm.backup_driver_response_minutes} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_response_minutes: Number(event.target.value) })} />
              </label>
              <label>
                Backup priority
                <input type="number" min="1" max="20" value={travelForm.backup_driver_priority} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_priority: Number(event.target.value) })} />
              </label>
              <label>
                Dispatch seats
                <input type="number" min="0" max="80" value={travelForm.backup_dispatch_minimum_capacity} onChange={(event) => setTravelForm({ ...travelForm, backup_dispatch_minimum_capacity: Number(event.target.value) })} />
              </label>
              <label>
                Dispatch channel
                <select value={travelForm.backup_dispatch_channel} onChange={(event) => setTravelForm({ ...travelForm, backup_dispatch_channel: event.target.value as CommunicationChannel })}>
                  <option value="sms">SMS</option>
                  <option value="push">Push</option>
                  <option value="in_app">In app</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="email">Email</option>
                </select>
              </label>
              <label>
                Verified only
                <select value={travelForm.backup_dispatch_require_verified ? "yes" : "no"} onChange={(event) => setTravelForm({ ...travelForm, backup_dispatch_require_verified: event.target.value === "yes" })}>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
              <label>
                Driver rating
                <input value={travelForm.driver_rating_name} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_name: event.target.value })} />
              </label>
              <label>
                Rating vehicle
                <input value={travelForm.driver_rating_vehicle} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_vehicle: event.target.value })} />
              </label>
              <label>
                Overall score
                <input type="number" min="1" max="5" value={travelForm.driver_rating_overall} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_overall: Number(event.target.value) })} />
              </label>
              <label>
                Safety score
                <input type="number" min="1" max="5" value={travelForm.driver_rating_safety} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_safety: Number(event.target.value) })} />
              </label>
              <label>
                Punctuality
                <input type="number" min="1" max="5" value={travelForm.driver_rating_punctuality} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_punctuality: Number(event.target.value) })} />
              </label>
              <label>
                Communication
                <input type="number" min="1" max="5" value={travelForm.driver_rating_communication} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_communication: Number(event.target.value) })} />
              </label>
              <label>
                Vehicle condition
                <input type="number" min="1" max="5" value={travelForm.driver_rating_vehicle_condition} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_vehicle_condition: Number(event.target.value) })} />
              </label>
              <label>
                Driver outcome
                <select
                  value={travelForm.driver_rating_incident_reported ? "incident" : travelForm.driver_rating_would_use_again ? "use_again" : "avoid"}
                  onChange={(event) =>
                    setTravelForm({
                      ...travelForm,
                      driver_rating_would_use_again: event.target.value === "use_again",
                      driver_rating_incident_reported: event.target.value === "incident"
                    })
                  }
                >
                  <option value="use_again">Use again</option>
                  <option value="avoid">Avoid next trip</option>
                  <option value="incident">Incident reported</option>
                </select>
              </label>
              <label>
                Geofence label
                <input value={travelForm.geofence_label} onChange={(event) => setTravelForm({ ...travelForm, geofence_label: event.target.value })} />
              </label>
              <label>
                Geofence lat
                <input type="number" step="0.000001" value={travelForm.geofence_latitude} onChange={(event) => setTravelForm({ ...travelForm, geofence_latitude: Number(event.target.value) })} />
              </label>
              <label>
                Geofence lon
                <input type="number" step="0.000001" value={travelForm.geofence_longitude} onChange={(event) => setTravelForm({ ...travelForm, geofence_longitude: Number(event.target.value) })} />
              </label>
              <label>
                Radius km
                <input type="number" min="0.1" step="0.1" value={travelForm.geofence_radius_km} onChange={(event) => setTravelForm({ ...travelForm, geofence_radius_km: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Geofence polygon
                <input value={travelForm.geofence_polygon} onChange={(event) => setTravelForm({ ...travelForm, geofence_polygon: event.target.value })} />
              </label>
              <label>
                Map provider
                <input value={travelForm.geofence_provider} onChange={(event) => setTravelForm({ ...travelForm, geofence_provider: event.target.value })} />
              </label>
              <label>
                Provider zone
                <input value={travelForm.geofence_provider_zone_id} onChange={(event) => setTravelForm({ ...travelForm, geofence_provider_zone_id: event.target.value })} />
              </label>
              <label>
                Provider rev
                <input value={travelForm.geofence_provider_revision} onChange={(event) => setTravelForm({ ...travelForm, geofence_provider_revision: event.target.value })} />
              </label>
              <label>
                Geofence alert
                <select value={travelForm.geofence_channel} onChange={(event) => setTravelForm({ ...travelForm, geofence_channel: event.target.value as CommunicationChannel })}>
                  <option value="push">Push</option>
                  <option value="in_app">In app</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="email">Email</option>
                </select>
              </label>
              <label>
                Expense
                <select value={travelForm.expense_category} onChange={(event) => setTravelForm({ ...travelForm, expense_category: event.target.value })}>
                  <option value="fuel">Fuel</option>
                  <option value="tolls">Tolls</option>
                  <option value="meals">Meals</option>
                  <option value="lodging">Lodging</option>
                  <option value="parking">Parking</option>
                  <option value="driver">Driver</option>
                  <option value="emergency">Emergency</option>
                  <option value="other">Other</option>
                </select>
              </label>
              <label>
                Vendor
                <input value={travelForm.expense_vendor} onChange={(event) => setTravelForm({ ...travelForm, expense_vendor: event.target.value })} />
              </label>
              <label>
                Expense amount
                <input type="number" min="0" value={travelForm.expense_amount} onChange={(event) => setTravelForm({ ...travelForm, expense_amount: Number(event.target.value) })} />
              </label>
              <label>
                Payout provider
                <input value={travelForm.payout_provider} onChange={(event) => setTravelForm({ ...travelForm, payout_provider: event.target.value })} />
              </label>
              <label>
                Payout adapter
                <select value={travelForm.payout_adapter_mode} onChange={(event) => setTravelForm({ ...travelForm, payout_adapter_mode: event.target.value })}>
                  <option value="mobile_money">Mobile money</option>
                  <option value="bank_transfer">Bank transfer</option>
                  <option value="record_only">Record only</option>
                </select>
              </label>
              <label className="wide-field">
                Payout destination
                <input value={travelForm.payout_destination} onChange={(event) => setTravelForm({ ...travelForm, payout_destination: event.target.value })} />
              </label>
              <label>
                Carpool type
                <select value={travelForm.carpool_type} onChange={(event) => setTravelForm({ ...travelForm, carpool_type: event.target.value })}>
                  <option value="request">Request</option>
                  <option value="offer">Offer</option>
                </select>
              </label>
              <label>
                Pickup
                <input value={travelForm.carpool_pickup_location} onChange={(event) => setTravelForm({ ...travelForm, carpool_pickup_location: event.target.value })} />
              </label>
              <label>
                Pickup lat
                <input type="number" step="0.000001" value={travelForm.carpool_pickup_latitude} onChange={(event) => setTravelForm({ ...travelForm, carpool_pickup_latitude: Number(event.target.value) })} />
              </label>
              <label>
                Pickup lon
                <input type="number" step="0.000001" value={travelForm.carpool_pickup_longitude} onChange={(event) => setTravelForm({ ...travelForm, carpool_pickup_longitude: Number(event.target.value) })} />
              </label>
              <label>
                Carpool seats
                <input
                  type="number"
                  min="1"
                  value={travelForm.carpool_type === "offer" ? travelForm.carpool_seats_available : travelForm.carpool_seats_requested}
                  onChange={(event) =>
                    setTravelForm({
                      ...travelForm,
                      carpool_seats_requested: Number(event.target.value),
                      carpool_seats_available: Number(event.target.value)
                    })
                  }
                />
              </label>
              <label>
                Pickup start
                <input type="datetime-local" value={travelForm.carpool_window_start} onChange={(event) => setTravelForm({ ...travelForm, carpool_window_start: event.target.value })} />
              </label>
              <label>
                Pickup end
                <input type="datetime-local" value={travelForm.carpool_window_end} onChange={(event) => setTravelForm({ ...travelForm, carpool_window_end: event.target.value })} />
              </label>
              <label>
                Route strategy
                <select value={travelForm.route_strategy} onChange={(event) => setTravelForm({ ...travelForm, route_strategy: event.target.value })}>
                  <option value="balanced">Balanced</option>
                  <option value="fastest">Fastest</option>
                  <option value="safest">Safest</option>
                  <option value="carpool_dense">Carpool dense</option>
                </select>
              </label>
              <label className="wide-field">
                Route
                <input value={travelForm.route_summary} onChange={(event) => setTravelForm({ ...travelForm, route_summary: event.target.value })} />
              </label>
              <label className="wide-field">
                Carpool dropoff
                <input value={travelForm.carpool_dropoff_location} onChange={(event) => setTravelForm({ ...travelForm, carpool_dropoff_location: event.target.value })} />
              </label>
              <label>
                Dropoff lat
                <input type="number" step="0.000001" value={travelForm.carpool_dropoff_latitude} onChange={(event) => setTravelForm({ ...travelForm, carpool_dropoff_latitude: Number(event.target.value) })} />
              </label>
              <label>
                Dropoff lon
                <input type="number" step="0.000001" value={travelForm.carpool_dropoff_longitude} onChange={(event) => setTravelForm({ ...travelForm, carpool_dropoff_longitude: Number(event.target.value) })} />
              </label>
              <label className="wide-field">
                Driver notes
                <input value={travelForm.driver_rating_notes} onChange={(event) => setTravelForm({ ...travelForm, driver_rating_notes: event.target.value })} />
              </label>
              <label className="wide-field">
                Backup notes
                <input value={travelForm.backup_driver_notes} onChange={(event) => setTravelForm({ ...travelForm, backup_driver_notes: event.target.value })} />
              </label>
              <label className="wide-field">
                Dispatch reason
                <input value={travelForm.backup_dispatch_reason} onChange={(event) => setTravelForm({ ...travelForm, backup_dispatch_reason: event.target.value })} />
              </label>
              <label className="wide-field">
                Receipt URL
                <input value={travelForm.expense_receipt_url} onChange={(event) => setTravelForm({ ...travelForm, expense_receipt_url: event.target.value })} />
              </label>
              <label className="wide-field">
                Receipt file
                <input type="file" accept="image/*,.pdf" onChange={(event) => setSelectedTravelReceiptFile(event.target.files?.[0] ?? null)} />
              </label>
              <label className="wide-field">
                Checklist evidence
                <input type="file" accept="image/*,.pdf" onChange={(event) => setSelectedTravelChecklistFile(event.target.files?.[0] ?? null)} />
              </label>
              <label className="wide-field">
                Emergency and medical
                <input value={travelForm.medical_access_plan} onChange={(event) => setTravelForm({ ...travelForm, medical_access_plan: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {travelConsentBatch ? (
                <article className="task-card">
                  <div>
                    <strong>Travel consent requests</strong>
                    <span>
                      {travelConsentBatch.created} created · {travelConsentBatch.existing} existing · {travelConsentBatch.skipped_no_guardian} missing guardians
                    </span>
                    <span>
                      {travelConsentBatch.skipped_not_minor} not minors · {travelConsentBatch.requests[0]?.destination ?? "No new request destinations"}
                    </span>
                  </div>
                </article>
              ) : null}
              {travelConsentReminder ? (
                <article className="task-card">
                  <div>
                    <strong>Travel consent reminder</strong>
                    <span>{travelConsentReminder.recipient_count} recipients · {travelConsentReminder.pending_request_count} pending requests</span>
                    <span>Message {travelConsentReminder.message_id}</span>
                  </div>
                </article>
              ) : null}
              {travelConsentReminderRun ? (
                <article className="task-card">
                  <div>
                    <strong>Automated travel reminders · {travelConsentReminderRun.due_plan_count} due plans</strong>
                    <span>
                      {travelConsentReminderRun.pending_request_count} pending requests · {travelConsentReminderRun.recipient_count} recipients · due by {new Date(travelConsentReminderRun.due_by).toLocaleString()}
                    </span>
                    <span>{travelConsentReminderRun.plans[0]?.destination ?? "No travel consent reminders due"}</span>
                  </div>
                </article>
              ) : null}
              {travelManifest ? (
                <article className="task-card">
                  <div>
                    <strong>{travelManifest.destination} manifest</strong>
                    <span>{travelManifest.participant_count} participants · {travelManifest.medical_access_plan ?? "Medical access plan not set"}</span>
                    <span>{travelManifest.participants[0]?.display_name ?? "No participants loaded"}</span>
                  </div>
                </article>
              ) : null}
              {travelOfflineManifestCache ? (
                <article className="task-card">
                  <div>
                    <strong>Offline manifest cache</strong>
                    <span>{travelOfflineManifestCache.destination} · {travelOfflineManifestCache.participant_count} participants</span>
                    <span>
                      {travelOfflineManifestCache.encrypted ? "Encrypted" : "Legacy"} · cached{" "}
                      {new Date(travelOfflineManifestCache.cached_at).toLocaleString()} · expires{" "}
                      {new Date(getTravelManifestOfflineCacheExpiry(travelOfflineManifestCache)).toLocaleDateString()} ·
                      v{travelOfflineManifestCache.cache_version}
                    </span>
                  </div>
                </article>
              ) : null}
              {travelManifestExport ? (
                <article className="task-card">
                  <div>
                    <strong>{travelManifestExport.filename}</strong>
                    <span>{travelManifestExport.content_type} · {travelManifestExport.content.split("\n").length} lines</span>
                    <span>{travelManifestExport.content.split("\n")[0] ?? "Manifest export ready"}</span>
                  </div>
                </article>
              ) : null}
              {travelManifestOfflineLink ? (
                <article className="task-card">
                  <div>
                    <strong>{travelManifestOfflineLink.filename} offline link</strong>
                    <span>{travelManifestOfflineLink.size_bytes} bytes · expires {new Date(travelManifestOfflineLink.expires_at).toLocaleString()}</span>
                    <span>{travelManifestOfflineLink.checksum.slice(0, 12)} · signed manifest access</span>
                  </div>
                  <div className="event-toolbar">
                    <a className="button-link" href={`${apiBaseUrl}${travelManifestOfflineLink.signed_url}`} target="_blank" rel="noreferrer">
                      Open
                    </a>
                  </div>
                </article>
              ) : null}
              {travelReadiness ? (
                <article className="task-card">
                  <div>
                    <strong>{travelReadiness.ready ? "Departure ready" : "Departure blocked"} · {travelReadiness.risk_level}</strong>
                    <span>
                      {travelReadiness.pending_approval_count} approvals · {travelReadiness.pending_checklist_count} checklist · {travelReadiness.pending_consent_request_count} consents pending
                    </span>
                    <span>{travelReadiness.blockers[0] ?? travelReadiness.warnings[0] ?? "No readiness warnings"}</span>
                  </div>
                </article>
              ) : null}
              {travelRouteOptimization ? (
                <article className="task-card">
                  <div>
                    <strong>{travelRouteOptimization.recommended_strategy} route · {travelRouteOptimization.stop_count} stops</strong>
                    <span>
                      {travelRouteOptimization.estimated_duration_minutes} min · traffic +{travelRouteOptimization.traffic_delay_minutes} · weather +{travelRouteOptimization.weather_delay_minutes}
                    </span>
                    <span>Depart {travelRouteOptimization.recommended_departure_at ? new Date(travelRouteOptimization.recommended_departure_at).toLocaleString() : "not set"}</span>
                    <span>
                      {travelRouteOptimization.reroute_required ? `Reroute: ${travelRouteOptimization.reroute_reason ?? "weather/traffic risk"}` : "No reroute required"}
                      {travelRouteOptimization.latest_weather_alert_level ? ` · ${travelRouteOptimization.latest_weather_alert_level}/${travelRouteOptimization.latest_weather_decision}` : ""}
                    </span>
                    <span>{travelRouteOptimization.route_summary}</span>
                  </div>
                </article>
              ) : null}
              {travelRouteMap ? (
                <article className="task-card">
                  <div>
                    <strong>{travelRouteMap.destination} map · {travelRouteMap.path.length} points</strong>
                    <span>
                      {travelRouteMap.provider_hint} · {travelRouteMap.latest_phase ?? "no position"}
                      {travelRouteMap.latest_recorded_at ? ` · ${new Date(travelRouteMap.latest_recorded_at).toLocaleString()}` : ""}
                    </span>
                    <span>
                      Bounds {travelRouteMap.bounds.min_latitude ?? "n/a"}, {travelRouteMap.bounds.min_longitude ?? "n/a"} to {travelRouteMap.bounds.max_latitude ?? "n/a"}, {travelRouteMap.bounds.max_longitude ?? "n/a"}
                    </span>
                    <span>{travelRouteMap.markers.map((marker) => `${marker.label} (${marker.marker_type})`).slice(0, 3).join(" · ") || "No map markers yet"}</span>
                  </div>
                </article>
              ) : null}
              {travelTelemetryStream ? (
                <article className="task-card">
                  <div>
                    <strong>Telemetry stream · {travelTelemetryStream.update_count} replay rows</strong>
                    <span>{travelTelemetryStream.content_type} · {travelTelemetryStream.replay_window_seconds}s replay window</span>
                    <span>
                      {travelTelemetryStream.latest_recorded_at ? new Date(travelTelemetryStream.latest_recorded_at).toLocaleString() : "No telemetry yet"}
                      {` · ${travelTelemetryStream.stream_url}`}
                    </span>
                  </div>
                </article>
              ) : null}
              {travelGeofenceCheck ? (
                <article className="task-card">
                  <div>
                    <strong>{travelGeofenceCheck.breached ? "Geofence breached" : "Inside geofence"} · {travelGeofenceCheck.label}</strong>
                    <span>
                      {travelGeofenceCheck.boundary_type} · {travelGeofenceCheck.distance_km} km from center · {travelGeofenceCheck.radius_km} km radius · {travelGeofenceCheck.recipient_count} alerted
                    </span>
                    <span>{travelGeofenceCheck.polygon_vertices ? `${travelGeofenceCheck.polygon_vertices} polygon vertices` : "Circular boundary"}</span>
                    <span>{travelGeofenceCheck.recommendation}</span>
                  </div>
                </article>
              ) : null}
              {travelGeofenceZones.slice(0, 3).map((zone) => (
                <article className="task-card" key={zone.id}>
                  <div>
                    <strong>{zone.label} · {zone.active ? "active" : "inactive"}</strong>
                    <span>{zone.center_latitude}, {zone.center_longitude} · {zone.radius_km} km radius</span>
                    <span>
                      {zone.polygon_coordinates?.length ? `${zone.polygon_coordinates.length} polygon vertices` : "Circular boundary"}
                      {zone.provider ? ` · ${zone.provider}:${zone.provider_zone_id ?? "unlinked"}` : ""}
                    </span>
                    <span>{zone.channel} alerts · {zone.alert_on_breach ? "alerts on breach" : "monitor only"}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => checkTravelGeofenceZone(zone)}>Check zone</button>
                    <button type="button" onClick={() => editTravelGeofenceZone(zone)}>Edit</button>
                    <button type="button" onClick={() => updateTravelGeofenceZone(zone)}>Update</button>
                    <button type="button" onClick={() => setTravelGeofenceZoneActive(zone, !zone.active)}>
                      {zone.active ? "Deactivate" : "Activate"}
                    </button>
                  </div>
                </article>
              ))}
              {travelDevices.slice(0, 3).map((device) => (
                <article className="task-card" key={device.id}>
                  <div>
                    <strong>{device.label} · {device.status}</strong>
                    <span>{device.provider}:{device.device_id} · {device.assigned_vehicle ?? "No vehicle assigned"}</span>
                    <span>{device.secret_configured ? `Secret rotated ${device.secret_rotated_at ? new Date(device.secret_rotated_at).toLocaleString() : "recently"}` : "Using global ingest key fallback"}</span>
                    <span>
                      Secret custody: {device.secret_storage_mode}
                      {device.secret_vault_provider ? ` · ${device.secret_vault_provider}` : ""}
                    </span>
                    <span>
                      {device.last_seen_at ? `Last seen ${new Date(device.last_seen_at).toLocaleString()}` : "No device pings yet"}
                      {device.last_battery_percent ? ` · ${device.last_battery_percent}% battery` : ""}
                    </span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => setTravelDeviceStatus(device, "active")}>Activate</button>
                    <button type="button" onClick={() => setTravelDeviceStatus(device, "maintenance")}>Service</button>
                    <button type="button" onClick={() => setTravelDeviceStatus(device, "disabled")}>Disable</button>
                    <button type="button" onClick={() => rotateTravelDeviceSecret(device)}>Rotate secret</button>
                  </div>
                </article>
              ))}
              {travelDeviceSecret ? (
                <article className="task-card">
                  <div>
                    <strong>{travelDeviceSecret.label} ingest secret</strong>
                    <span>{travelDeviceSecret.provider}:{travelDeviceSecret.device_id} · rotated {new Date(travelDeviceSecret.secret_rotated_at).toLocaleString()}</span>
                    <span>{travelDeviceSecret.secret_vault_reference ?? `Secret custody: ${travelDeviceSecret.secret_storage_mode}`}</span>
                    <span>{travelDeviceSecret.ingest_secret}</span>
                  </div>
                </article>
              ) : null}
              {travelDeviceFleetInventory ? (
                <article className="task-card">
                  <div>
                    <strong>GPS fleet · {travelDeviceFleetInventory.total_devices} devices</strong>
                    <span>
                      {travelDeviceFleetInventory.active_devices} active · {travelDeviceFleetInventory.maintenance_devices} maintenance · {travelDeviceFleetInventory.disabled_devices} disabled
                    </span>
                    <span>
                      {travelDeviceFleetInventory.stale_devices} stale · {travelDeviceFleetInventory.low_battery_devices} low battery · {travelDeviceFleetInventory.devices[0]?.label ?? "No devices provisioned"}
                    </span>
                  </div>
                </article>
              ) : null}
              {travelBackupDrivers.slice(0, 3).map((driver) => (
                <article className="task-card" key={driver.id}>
                  <div>
                    <strong>{driver.driver_name} · {driver.availability_status}</strong>
                    <span>{driver.vehicle_label ?? "No vehicle"} · {driver.capacity} seats · priority {driver.priority}</span>
                    <span>
                      {driver.license_status} license · {driver.background_check_status} screening
                      {driver.response_minutes !== null ? ` · ${driver.response_minutes} min response` : ""}
                    </span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => setTravelBackupDriverAvailability(driver, "available")}>Available</button>
                    <button type="button" onClick={() => setTravelBackupDriverAvailability(driver, "dispatched")}>Dispatch</button>
                    <button type="button" onClick={() => setTravelBackupDriverAvailability(driver, "unavailable")}>Unavailable</button>
                  </div>
                </article>
              ))}
              {travelBackupDriverDispatch ? (
                <article className="task-card">
                  <div>
                    <strong>Dispatched backup · {travelBackupDriverDispatch.driver.driver_name}</strong>
                    <span>
                      {travelBackupDriverDispatch.eligible_driver_count} eligible · {travelBackupDriverDispatch.recipient_count} notified · {travelBackupDriverDispatch.driver.vehicle_label ?? "No vehicle"}
                    </span>
                    <span>{travelBackupDriverDispatch.rationale[0] ?? travelBackupDriverDispatch.driver.dispatch_reason ?? "Backup dispatch complete"}</span>
                  </div>
                </article>
              ) : null}
              {travelDriverMarketplace ? (
                <article className="task-card">
                  <div>
                    <strong>Driver marketplace · {travelDriverMarketplace.candidate_count} candidates</strong>
                    <span>
                      {travelDriverMarketplace.verified_candidate_count} verified · recommended {travelDriverMarketplace.candidates[0]?.driver.driver_name ?? "none"}
                    </span>
                    <span>
                      {travelDriverMarketplace.candidates[0]
                        ? `${travelDriverMarketplace.candidates[0].match_score}% · ${travelDriverMarketplace.candidates[0].marketplace_status} · ${travelDriverMarketplace.candidates[0].rationale[0] ?? "No rationale"}`
                        : "No available marketplace candidates"}
                    </span>
                  </div>
                </article>
              ) : null}
              {travelDriverRatingSummary ? (
                <article className="task-card">
                  <div>
                    <strong>Driver ratings · {travelDriverRatingSummary.rating_count}</strong>
                    <span>
                      {travelDriverRatingSummary.average_overall_score ?? "n/a"}/5 average · {travelDriverRatingSummary.would_use_again_count} use again
                    </span>
                    <span>{travelDriverRatingSummary.incident_reported_count} incident flag(s)</span>
                  </div>
                </article>
              ) : null}
              {travelDriverRatings.slice(0, 3).map((rating) => (
                <article className="task-card" key={rating.id}>
                  <div>
                    <strong>{rating.driver_name} · {rating.overall_score}/5</strong>
                    <span>
                      Safety {rating.safety_score ?? "n/a"} · punctuality {rating.punctuality_score ?? "n/a"} · communication {rating.communication_score ?? "n/a"}
                    </span>
                    <span>{rating.incident_reported ? "Incident reported" : rating.would_use_again ? "Use again" : "Avoid next trip"} · {rating.notes ?? "No driver notes"}</span>
                  </div>
                </article>
              ))}
              {travelFeeBatch ? (
                <article className="task-card">
                  <div>
                    <strong>Travel fee invoices</strong>
                    <span>{travelFeeBatch.created} created · {travelFeeBatch.existing} existing · {travelFeeBatch.skipped_no_payer} missing payers</span>
                    <span>{travelFeeBatch.total_amount_due} total · {travelFeeBatch.invoices[0]?.invoice_number ?? "No invoices"}</span>
                  </div>
                </article>
              ) : null}
              {travelFeeCheckoutBatch ? (
                <article className="task-card">
                  <div>
                    <strong>{travelFeeCheckoutBatch.checkout_count} travel payment sessions</strong>
                    <span>{travelFeeCheckoutBatch.total_open_amount} open · {travelFeeCheckoutBatch.provider}</span>
                    <span>
                      {travelFeeCheckoutBatch.checkouts[0]?.session_id ?? "No checkout sessions"}
                      {travelFeeCheckoutBatch.checkouts[0]?.session_status ? ` · ${travelFeeCheckoutBatch.checkouts[0].session_status}` : ""}
                    </span>
                    <span>{travelFeeCheckoutBatch.checkouts[0]?.session_url ?? travelFeeCheckoutBatch.checkouts[0]?.checkout_url ?? "No checkout URL"}</span>
                  </div>
                </article>
              ) : null}
              {travelFeeReconciliation ? (
                <article className="task-card">
                  <div>
                    <strong>Travel fee reconciliation · {travelFeeReconciliation.provider}</strong>
                    <span>
                      {travelFeeReconciliation.paid_count} paid · {travelFeeReconciliation.partial_count} partial · {travelFeeReconciliation.unpaid_count} unpaid
                    </span>
                    <span>
                      {travelFeeReconciliation.total_paid} paid · {travelFeeReconciliation.total_open} open · {travelFeeReconciliation.invoice_count} invoices
                    </span>
                    <span>
                      {travelFeeReconciliation.exception_count} exceptions · {travelFeeReconciliation.exceptions[0]?.recommended_action ?? "No payment reconciliation exceptions"}
                    </span>
                    <span>
                      {travelFeeReconciliation.items[0]?.last_payment_reference ?? travelFeeReconciliation.items[0]?.session_id ?? "No travel payments reconciled yet"}
                    </span>
                    <button type="button" onClick={() => resolveTravelFeeException(travelFeeReconciliation.travel_plan_id)}>
                      Resolve first exception
                    </button>
                  </div>
                </article>
              ) : null}
              {travelApprovalRouting ? (
                <article className="task-card">
                  <div>
                    <strong>Approval routing · {travelApprovalRouting.recommended_levels.join(", ") || "none"}</strong>
                    <span>{travelApprovalRouting.created} created · {travelApprovalRouting.existing} existing</span>
                    <span>{travelApprovalRouting.rationale[0] ?? "No approval route needed for this plan"}</span>
                  </div>
                </article>
              ) : null}
              {travelExpenses.slice(0, 3).map((expense) => (
                <article className="task-card" key={expense.id}>
                  <div>
                    <strong>{expense.category} · {expense.amount} {expense.currency}</strong>
                    <span>{expense.reimbursement_status} · {expense.vendor ?? "No vendor"} · {new Date(expense.incurred_at).toLocaleString()}</span>
                    <span>{expense.payout_adapter_mode ?? "No payout adapter"} · {expense.payout_destination ?? "No payout destination"}</span>
                    <span>{expense.payout_reference ?? expense.receipt_url ?? expense.notes ?? "No receipt evidence"}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => uploadTravelReceipt(expense)}>Receipt</button>
                    <button type="button" onClick={() => updateTravelExpenseStatus(expense, "approved")}>Approve</button>
                    <button type="button" onClick={() => executeTravelExpensePayout(expense)}>Payout</button>
                    <button type="button" onClick={() => reconcileTravelExpensePayoutCallback(expense, "paid")}>Callback paid</button>
                    <button type="button" onClick={() => reconcileTravelExpensePayoutCallback(expense, "failed")}>Callback fail</button>
                    <button type="button" onClick={() => updateTravelExpenseStatus(expense, "rejected")}>Reject</button>
                  </div>
                </article>
              ))}
              {travelExpensePayout ? (
                <article className="task-card">
                  <div>
                    <strong>{travelExpensePayout.payout_reference}</strong>
                    <span>{travelExpensePayout.amount} {travelExpensePayout.currency} · {travelExpensePayout.provider} · {travelExpensePayout.payout_status}</span>
                    <span>{travelExpensePayout.adapter_mode} · {travelExpensePayout.destination ?? "No destination"} · {travelExpensePayout.provider_status_code ?? "recorded"}</span>
                    <span>{travelExpensePayout.idempotency_key}</span>
                    <span>{new Date(travelExpensePayout.processed_at).toLocaleString()}</span>
                  </div>
                </article>
              ) : null}
              {travelCarpoolRides.slice(0, 3).map((ride) => (
                <article className="task-card" key={ride.id}>
                  <div>
                    <strong>{ride.ride_type} carpool · {ride.status}</strong>
                    <span>{ride.pickup_location} to {ride.dropoff_location ?? "destination"} · {ride.seats_available || ride.seats_requested} seats</span>
                    <span>
                      {ride.pickup_latitude && ride.pickup_longitude ? `${ride.pickup_latitude}, ${ride.pickup_longitude}` : "No pickup coordinates"}
                      {ride.dropoff_latitude && ride.dropoff_longitude ? ` · drop ${ride.dropoff_latitude}, ${ride.dropoff_longitude}` : ""}
                    </span>
                    <span>{ride.match_score ? `${ride.match_score}% match` : ride.notes ?? "No match score yet"}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => updateTravelCarpoolStatus(ride, "matched")}>Match</button>
                    <button type="button" onClick={() => updateTravelCarpoolStatus(ride, "confirmed")}>Confirm</button>
                    <button type="button" onClick={() => updateTravelCarpoolStatus(ride, "cancelled")}>Cancel</button>
                  </div>
                </article>
              ))}
              {travelCarpoolAutoMatch ? (
                <article className="task-card">
                  <div>
                    <strong>Carpool auto-match · {travelCarpoolAutoMatch.matched_count} matched</strong>
                    <span>{travelCarpoolAutoMatch.request_count} requests · {travelCarpoolAutoMatch.offer_count} offers</span>
                    <span>
                      {travelCarpoolAutoMatch.pairs[0]?.pickup_distance_km
                        ? `${travelCarpoolAutoMatch.pairs[0].pickup_distance_km} km pickup distance`
                        : travelCarpoolAutoMatch.pairs[0]?.pickup_match ?? "No automatic matches above threshold"}
                    </span>
                  </div>
                </article>
              ) : null}
              {travelApprovals.slice(0, 3).map((approval) => (
                <article className="task-card" key={approval.id}>
                  <div>
                    <strong>{approval.approval_level} approval</strong>
                    <span>{approval.status} · {approval.decided_at ? new Date(approval.decided_at).toLocaleString() : "awaiting decision"}</span>
                    <span>{approval.notes ?? "No approval notes"}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => decideTravelApproval(approval, "approved")}>Approve</button>
                    <button type="button" onClick={() => decideTravelApproval(approval, "rejected")}>Reject</button>
                  </div>
                </article>
              ))}
              {travelChecklistItems.slice(0, 4).map((item) => (
                <article className="task-card" key={item.id}>
                  <div>
                    <strong>{item.item_label}</strong>
                    <span>{item.checklist_type} · {item.status} · {item.completed_at ? new Date(item.completed_at).toLocaleString() : "open"}</span>
                    <span>{item.notes ?? item.evidence_url ?? "No evidence recorded"}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => uploadTravelChecklistEvidence(item)}>Evidence</button>
                    <button type="button" onClick={() => updateTravelChecklistItem(item, "completed")}>Done</button>
                    <button type="button" onClick={() => updateTravelChecklistItem(item, "blocked")}>Block</button>
                    <button type="button" onClick={() => updateTravelChecklistItem(item, "pending")}>Reset</button>
                  </div>
                </article>
              ))}
              {travelLocationUpdates.slice(0, 3).map((update) => (
                <article className="task-card" key={update.id}>
                  <div>
                    <strong>{update.phase} · {update.source}</strong>
                    <span>{update.latitude}, {update.longitude} · {update.speed_kph ?? "n/a"} kph</span>
                    <span>{update.notification_recipient_count} notified · {new Date(update.recorded_at).toLocaleString()}</span>
                  </div>
                </article>
              ))}
              {travelPlans.slice(0, 2).map((plan) => (
                <article key={plan.id} className="task-card">
                  <div>
                    <strong>{plan.destination} · {plan.risk_level}</strong>
                    <span>{plan.travel_mode} · {plan.status} · depart {plan.departure_at ? new Date(plan.departure_at).toLocaleString() : "not set"}</span>
                    <span>{plan.risk_assessment}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => requestTravelConsents(plan)}>Consent</button>
                    <button type="button" onClick={() => remindTravelConsents(plan)}>Remind</button>
                    <button type="button" onClick={() => loadTravelManifest(plan)}>Manifest</button>
                    <button type="button" onClick={() => cacheTravelManifestOffline(plan)}>Cache</button>
                    <button type="button" onClick={() => restoreTravelManifestOffline(plan)}>Offline</button>
                    <button type="button" onClick={() => exportTravelManifest(plan)}>Export</button>
                    <button type="button" onClick={() => createTravelManifestOfflineLink(plan)}>PDF link</button>
                    <button type="button" onClick={() => checkTravelReadiness(plan)}>Gate</button>
                    <button type="button" onClick={() => optimizeTravelRoute(plan)}>Optimize</button>
                    <button type="button" onClick={() => loadTravelRouteMap(plan)}>Map</button>
                    <button type="button" onClick={() => loadTravelTelemetryStream(plan)}>Stream</button>
                    <button type="button" onClick={() => generateTravelFeeInvoices(plan)}>Fees</button>
                    <button type="button" onClick={() => createTravelFeeCheckouts(plan)}>Pay links</button>
                    <button type="button" onClick={() => reconcileTravelFeePayments(plan)}>Payments</button>
                    <button type="button" onClick={() => routeTravelApprovals(plan)}>Route approvals</button>
                    <button type="button" onClick={() => createTravelApproval(plan)}>Require</button>
                    <button type="button" onClick={() => loadTravelApprovals(plan)}>Approvals</button>
                    <button type="button" onClick={() => seedTravelChecklist(plan)}>Inspect</button>
                    <button type="button" onClick={() => loadTravelChecklist(plan)}>Checklist</button>
                    <button type="button" onClick={() => recordTravelLocationUpdate(plan)}>Track</button>
                    <button type="button" onClick={() => createTravelDevice(plan)}>Device</button>
                    <button type="button" onClick={() => loadTravelDevices(plan)}>Devices</button>
                    <button type="button" onClick={() => createTravelBackupDriver(plan)}>Backup driver</button>
                    <button type="button" onClick={() => loadTravelBackupDrivers(plan)}>Backups</button>
                    <button type="button" onClick={() => dispatchTravelBackupDriver(plan)}>Dispatch backup</button>
                    <button type="button" onClick={() => loadTravelDriverMarketplace(plan)}>Marketplace</button>
                    <button type="button" onClick={() => createTravelDriverRating(plan)}>Rate driver</button>
                    <button type="button" onClick={() => loadTravelDriverRatings(plan)}>Ratings</button>
                    <button type="button" onClick={() => checkTravelGeofence(plan)}>Geofence</button>
                    <button type="button" onClick={() => createTravelGeofenceZone(plan)}>Save zone</button>
                    <button type="button" onClick={() => loadTravelGeofenceZones(plan)}>Zones</button>
                    <button type="button" onClick={() => loadTravelLocationUpdates(plan)}>Route</button>
                    <button type="button" onClick={() => createTravelExpense(plan)}>Expense</button>
                    <button type="button" onClick={() => loadTravelExpenses(plan)}>Expenses</button>
                    <button type="button" onClick={() => createTravelCarpool(plan)}>Carpool</button>
                    <button type="button" onClick={() => autoMatchTravelCarpools(plan)}>Auto match</button>
                    <button type="button" onClick={() => loadTravelCarpools(plan)}>Carpools</button>
                    <button type="button" onClick={() => updateTravelPlan(plan, "ready")}>Ready</button>
                    <button type="button" onClick={() => updateTravelPlan(plan, "in_progress")}>Depart</button>
                    <button type="button" onClick={() => updateTravelPlan(plan, "completed")}>Complete</button>
                    <button type="button" onClick={() => updateTravelPlan(plan, "cancelled")}>Cancel</button>
                  </div>
                </article>
              ))}
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
                  <small>
                    {record.medical_clearance_status
                      ? `${record.medical_clearance_status} · ${record.medical_clearance_reason ?? "medical review"}`
                      : record.clearance_status ?? "clearance pending"}
                  </small>
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
                <button type="button" onClick={createEmergencyPlan} disabled={busyAction !== null}>EAP</button>
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
            <div className="form-grid three">
              <label>
                EAP title
                <input value={emergencyPlanForm.title} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, title: event.target.value })} />
              </label>
              <label>
                Emergency type
                <select value={emergencyPlanForm.emergency_type} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, emergency_type: event.target.value as EmergencyType })}>
                  <option value="medical">Medical</option>
                  <option value="fire">Fire</option>
                  <option value="weather">Weather</option>
                  <option value="security">Security</option>
                  <option value="evacuation">Evacuation</option>
                  <option value="missing_person">Missing person</option>
                  <option value="other">Other</option>
                </select>
              </label>
              <label>
                Review due
                <input type="date" value={emergencyPlanForm.review_due_on} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, review_due_on: event.target.value })} />
              </label>
              <label className="wide-field">
                Contacts
                <input value={emergencyPlanForm.emergency_contacts} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, emergency_contacts: event.target.value })} />
              </label>
              <label className="wide-field">
                Medical protocol
                <input value={emergencyPlanForm.medical_protocols} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, medical_protocols: event.target.value })} />
              </label>
              <label className="wide-field">
                Communication
                <input value={emergencyPlanForm.communication_protocols} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, communication_protocols: event.target.value })} />
              </label>
              <label className="wide-field">
                Command roles
                <input value={emergencyPlanForm.incident_command_roles} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, incident_command_roles: event.target.value })} />
              </label>
              <label className="wide-field">
                Escalation matrix
                <input value={emergencyPlanForm.escalation_matrix} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, escalation_matrix: event.target.value })} />
              </label>
              <label className="wide-field">
                External agencies
                <input value={emergencyPlanForm.external_agency_contacts} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, external_agency_contacts: event.target.value })} />
              </label>
              <label>
                Activation location
                <input value={emergencyPlanForm.activation_location} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, activation_location: event.target.value })} />
              </label>
              <label>
                Responders
                <input value={emergencyPlanForm.responders} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, responders: event.target.value })} />
              </label>
              <label>
                Alert channel
                <select value={emergencyPlanForm.alert_channel} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, alert_channel: event.target.value as CommunicationChannel })}>
                  <option value="push">Push</option>
                  <option value="in_app">In app</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="email">Email</option>
                </select>
              </label>
              <label className="wide-field">
                Alert note
                <input value={emergencyPlanForm.alert_body} onChange={(event) => setEmergencyPlanForm({ ...emergencyPlanForm, alert_body: event.target.value })} />
              </label>
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
              {emergencyAlert ? (
                <article className="task-card">
                  <div>
                    <strong>{emergencyAlert.subject}</strong>
                    <span>{emergencyAlert.channel} alert · {emergencyAlert.recipient_count} recipients</span>
                    <span>Message {emergencyAlert.message_id}</span>
                  </div>
                </article>
              ) : null}
              {emergencyActivations.slice(0, 3).map((activation) => (
                <article key={activation.id} className="task-card">
                  <div>
                    <strong>{activation.emergency_type} emergency · {activation.status}</strong>
                    <span>{activation.location_detail} · level {activation.escalation_level} · {new Date(activation.activated_at).toLocaleString()}</span>
                    <span>{activation.outcome_summary ?? activation.guidance_steps ?? "Response in progress"}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => dispatchEmergencyAlert(activation)}>Alert</button>
                    <button type="button" onClick={() => updateEmergencyActivation(activation, null, Math.min(5, activation.escalation_level + 1))}>Escalate</button>
                    <button type="button" onClick={() => createEmergencyIncident(activation)}>{activation.incident_id ? "Incident" : "Log incident"}</button>
                    <button type="button" onClick={() => updateEmergencyActivation(activation, "resolved")}>Resolve</button>
                    <button type="button" onClick={() => updateEmergencyActivation(activation, "reviewed")}>Review</button>
                    <button type="button" onClick={() => updateEmergencyActivation(activation, "cancelled")}>Cancel</button>
                  </div>
                </article>
              ))}
              {emergencyPlans.slice(0, 4).map((plan) => (
                <article key={plan.id} className="task-card">
                  <div>
                    <strong>{plan.title}</strong>
                    <span>{plan.emergency_type} · {plan.status} · review {plan.review_due_on ?? "not set"}</span>
                    <span>{plan.escalation_matrix ?? plan.emergency_contacts}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => updateEmergencyPlan(plan, "active")}>Activate Plan</button>
                    <button type="button" onClick={() => activateEmergencyPlan(plan)}>Emergency</button>
                    <button type="button" onClick={() => updateEmergencyPlan(plan, "under_review")}>Review</button>
                    <button type="button" onClick={() => updateEmergencyPlan(plan, "retired")}>Retire</button>
                  </div>
                </article>
              ))}
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
                  <div className="event-toolbar">
                    <button type="button" onClick={() => downloadEquipmentFile(fileRecord)}>Download</button>
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
                <button type="button" onClick={fileCommercialTax} disabled={busyAction !== null}>File tax</button>
                <button type="button" onClick={settleCommercialPayments} disabled={busyAction !== null}>Settle</button>
                <button type="button" onClick={executeCommercialPayout} disabled={busyAction !== null}>Payout</button>
                <button type="button" onClick={() => reconcileCommercialPayout("paid")} disabled={busyAction !== null}>Paid</button>
                <button type="button" onClick={exportCommercialAccounting} disabled={busyAction !== null}>Export</button>
                <button type="button" onClick={syncCommercialAccounting} disabled={busyAction !== null}>Sync</button>
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
              <label>
                Tax country
                <input value={invoiceForm.tax_jurisdiction} onChange={(event) => setInvoiceForm({ ...invoiceForm, tax_jurisdiction: event.target.value.toUpperCase() })} />
              </label>
              <label>
                Tax rate
                <input type="number" min="0" value={invoiceForm.tax_rate} onChange={(event) => setInvoiceForm({ ...invoiceForm, tax_rate: Number(event.target.value) })} />
              </label>
              <label>
                Period start
                <input type="date" value={invoiceForm.tax_period_start} onChange={(event) => setInvoiceForm({ ...invoiceForm, tax_period_start: event.target.value })} />
              </label>
              <label>
                Period end
                <input type="date" value={invoiceForm.tax_period_end} onChange={(event) => setInvoiceForm({ ...invoiceForm, tax_period_end: event.target.value })} />
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
              {commercialTaxFiling ? (
                <article className="task-card">
                  <div>
                    <strong>{commercialTaxFiling.jurisdiction} filing · {commercialTaxFiling.tax_amount}</strong>
                    <span>
                      {commercialTaxFiling.invoice_count} invoices · {commercialTaxFiling.delivery_mode} ·{" "}
                      {commercialTaxFiling.delivered ? "delivered" : commercialTaxFiling.failure_reason ?? "prepared"}
                    </span>
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
              {commercialPayout ? (
                <article className="task-card">
                  <div>
                    <strong>{commercialPayout.delivered ? "Payout delivered" : "Payout prepared"}</strong>
                    <span>
                      {commercialPayout.net_amount} {commercialPayout.currency} · {commercialPayout.status} · {commercialPayout.delivery_mode}
                      {commercialPayout.provider_status_code ? ` · ${commercialPayout.provider_status_code}` : ""}
                    </span>
                    {commercialPayout.failure_reason ? <small>{commercialPayout.failure_reason}</small> : null}
                  </div>
                </article>
              ) : null}
              {commercialPayouts.slice(0, 3).map((payout) => (
                <button
                  type="button"
                  key={payout.id ?? payout.payout_batch_reference}
                  className={`task-card ${payout.id && payout.id === commercialPayout?.id ? "selected" : ""}`}
                  onClick={() => setCommercialPayout(payout)}
                >
                  <div>
                    <strong>{payout.status} · {payout.payout_batch_reference}</strong>
                    <span>{payout.net_amount} {payout.currency} · {payout.provider}</span>
                  </div>
                </button>
              ))}
              {accountingExport ? (
                <article className="task-card">
                  <div>
                    <strong>{accountingExport.system} export</strong>
                    <span>{accountingExport.rows.length} rows · debit {accountingExport.debit_total} · credit {accountingExport.credit_total}</span>
                  </div>
                </article>
              ) : null}
              {accountingSync ? (
                <article className="task-card">
                  <div>
                    <strong>{accountingSync.delivered ? "Accounting delivered" : "Accounting prepared"}</strong>
                    <span>
                      {accountingSync.row_count} rows · {accountingSync.mode}
                      {accountingSync.provider_status_code ? ` · ${accountingSync.provider_status_code}` : ""}
                    </span>
                    {accountingSync.failure_reason ? <small>{accountingSync.failure_reason}</small> : null}
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

        <section className="work-grid" id="developers">
          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Developer ecosystem</p>
                <h2>Apps and webhooks</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createDeveloperApplication} disabled={busyAction !== null}>App</button>
                <button type="button" onClick={createDeveloperApiKey} disabled={busyAction !== null}>Key</button>
                <button type="button" onClick={createDeveloperOAuthAuthorization} disabled={busyAction !== null}>OAuth</button>
                <button type="button" onClick={createDeveloperWebhook} disabled={busyAction !== null}>Webhook</button>
                <button type="button" onClick={() => window.open("/developers", "_blank", "noopener,noreferrer")}>Docs</button>
              </div>
            </div>
            <div className="consent-grid">
              <div>
                <span className="muted">Apps</span>
                <strong>{developerSummary?.application_count ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Active</span>
                <strong>{developerSummary?.active_application_count ?? 0}</strong>
              </div>
              <div>
                <span className="muted">API keys</span>
                <strong>{developerSummary?.api_key_count ?? 0}</strong>
              </div>
              <div>
                <span className="muted">Webhooks</span>
                <strong>{developerSummary?.webhook_subscription_count ?? 0}</strong>
              </div>
            </div>
            <div className="form-grid">
              <label>
                Application
                <input value={developerForm.app_name} onChange={(event) => setDeveloperForm({ ...developerForm, app_name: event.target.value })} />
              </label>
              <label>
                Type
                <input value={developerForm.app_type} onChange={(event) => setDeveloperForm({ ...developerForm, app_type: event.target.value })} />
              </label>
              <label>
                Scopes
                <input value={developerForm.app_scopes} onChange={(event) => setDeveloperForm({ ...developerForm, app_scopes: event.target.value })} />
              </label>
              <label>
                Redirects
                <input value={developerForm.redirect_uris} onChange={(event) => setDeveloperForm({ ...developerForm, redirect_uris: event.target.value })} />
              </label>
              <label>
                Contact
                <input value={developerForm.contact_email} onChange={(event) => setDeveloperForm({ ...developerForm, contact_email: event.target.value })} />
              </label>
              <label>
                API key
                <input value={developerForm.api_key_name} onChange={(event) => setDeveloperForm({ ...developerForm, api_key_name: event.target.value })} />
              </label>
              <label>
                Environment
                <select value={developerForm.api_key_environment} onChange={(event) => setDeveloperForm({ ...developerForm, api_key_environment: event.target.value })}>
                  <option value="sandbox">Sandbox</option>
                  <option value="production">Production</option>
                </select>
              </label>
              <label>
                Rate/min
                <input type="number" min="1" value={developerForm.api_key_rate_limit} onChange={(event) => setDeveloperForm({ ...developerForm, api_key_rate_limit: Number(event.target.value) })} />
              </label>
              <label>
                PKCE challenge
                <input value={developerForm.oauth_code_challenge} onChange={(event) => setDeveloperForm({ ...developerForm, oauth_code_challenge: event.target.value })} />
              </label>
              <label>
                PKCE method
                <select value={developerForm.oauth_code_challenge_method} onChange={(event) => setDeveloperForm({ ...developerForm, oauth_code_challenge_method: event.target.value })}>
                  <option value="S256">S256</option>
                  <option value="plain">Plain</option>
                </select>
              </label>
              <label>
                Webhook
                <input value={developerForm.webhook_name} onChange={(event) => setDeveloperForm({ ...developerForm, webhook_name: event.target.value })} />
              </label>
              <label>
                Endpoint
                <input value={developerForm.webhook_url} onChange={(event) => setDeveloperForm({ ...developerForm, webhook_url: event.target.value })} />
              </label>
              <label>
                Events
                <input value={developerForm.webhook_events} onChange={(event) => setDeveloperForm({ ...developerForm, webhook_events: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {developerApplicationSecret ? (
                <article className="task-card">
                  <div>
                    <strong>{developerApplicationSecret.application.name} client secret</strong>
                    <span>{developerApplicationSecret.client_secret}</span>
                  </div>
                </article>
              ) : null}
              {developerApiKeySecret ? (
                <article className="task-card">
                  <div>
                    <strong>{developerApiKeySecret.api_key.name} API key</strong>
                    <span>{developerApiKeySecret.key}</span>
                  </div>
                </article>
              ) : null}
              {developerWebhookSecret ? (
                <article className="task-card">
                  <div>
                    <strong>{developerWebhookSecret.subscription.name} signing secret</strong>
                    <span>{developerWebhookSecret.signing_secret}</span>
                  </div>
                </article>
              ) : null}
              {developerOAuthGrant ? (
                <article className="task-card">
                  <div>
                    <strong>{developerOAuthGrant.application_name} OAuth code</strong>
                    <span>{developerOAuthGrant.authorization_code} · {developerOAuthGrant.redirect_url}</span>
                  </div>
                </article>
              ) : null}
              {developerCatalog ? (
                <article className="task-card">
                  <div>
                    <strong>{developerCatalog.webhook_events.length} webhook events · {developerCatalog.scopes.length} scopes</strong>
                    <span>
                      {developerCatalog.api_base_path} · {developerCatalog.auth_header} · {developerCatalog.configured_event_types.length} configured
                    </span>
                  </div>
                </article>
              ) : null}
              {developerCatalog?.webhook_events.slice(0, 2).map((event) => (
                <article key={event.event_type} className="task-card">
                  <div>
                    <strong>{event.event_type}</strong>
                    <span>{event.emission_status} · {event.category} · {event.recommended_scopes.join(", ")}</span>
                  </div>
                </article>
              ))}
              {developerCatalog?.sdks.slice(0, 2).map((sdk) => (
                <article key={sdk.language} className="task-card">
                  <div>
                    <strong>{sdk.language} SDK · {sdk.status}</strong>
                    <span>{sdk.package_name} · {sdk.entry_points.slice(0, 2).join(", ")}</span>
                  </div>
                </article>
              ))}
              {developerApplications.slice(0, 3).map((application) => (
                <article key={application.id} className="task-card">
                  <div>
                    <strong>{application.name}</strong>
                    <span>{application.client_id} · {application.scopes.join(", ")}</span>
                  </div>
                  <button type="button" onClick={() => rotateDeveloperApplicationSecret(application.id)} disabled={busyAction !== null}>Rotate</button>
                </article>
              ))}
              {developerApiKeys.slice(0, 3).map((apiKey) => (
                <article key={apiKey.id} className="task-card">
                  <div>
                    <strong>{apiKey.name}</strong>
                    <span>
                      {apiKey.key_prefix} · {apiKey.environment} · {apiKey.status} · {apiKey.window_request_count}/{apiKey.rate_limit_per_minute}/min · {apiKey.usage_count} calls
                      {apiKey.refresh_expires_at ? ` · refresh ${new Date(apiKey.refresh_expires_at).toLocaleDateString()}` : ""}
                      {apiKey.refresh_reused_at ? ` · reuse ${new Date(apiKey.refresh_reused_at).toLocaleDateString()}` : ""}
                    </span>
                  </div>
                  <button type="button" onClick={() => revokeDeveloperApiKey(apiKey.id)} disabled={busyAction !== null || apiKey.status === "revoked"}>Revoke</button>
                </article>
              ))}
              {developerOAuthAuthorizations.slice(0, 3).map((authorization) => (
                <article key={authorization.id} className="task-card">
                  <div>
                    <strong>{authorization.application_name} OAuth · {authorization.status}</strong>
                    <span>
                      {authorization.public_client ? `PKCE ${authorization.code_challenge_method}` : "confidential"} · {authorization.granted_scopes.join(", ")} · expires {new Date(authorization.expires_at).toLocaleString()}
                    </span>
                  </div>
                </article>
              ))}
              {developerWebhooks.slice(0, 3).map((webhook) => (
                <article key={webhook.id} className="task-card">
                  <div>
                    <strong>{webhook.name}</strong>
                    <span>{webhook.status} · {webhook.delivery_mode} · {webhook.event_types.join(", ")}</span>
                  </div>
                </article>
              ))}
              <article className="task-card">
                <div>
                  <strong>Webhook retry run</strong>
                  <span>
                    {developerWebhookRetryRun
                      ? `${developerWebhookRetryRun.replayed_count}/${developerWebhookRetryRun.eligible_count} retried · ${developerWebhookRetryRun.failed_count} failed · ${developerWebhookRetryRun.skipped_count} skipped`
                      : "No retry run yet"}
                  </span>
                </div>
                <button type="button" onClick={retryDeveloperWebhookDeliveries} disabled={busyAction !== null}>Retry</button>
              </article>
              {developerWebhookDeliveries.slice(0, 3).map((delivery) => (
                <article key={delivery.id} className="task-card">
                  <div>
                    <strong>{delivery.event_type}</strong>
                    <span>
                      {delivery.status} · {delivery.delivery_mode} · {delivery.attempt_count} attempt{delivery.attempt_count === 1 ? "" : "s"}
                      {delivery.next_attempt_at ? ` · next ${new Date(delivery.next_attempt_at).toLocaleTimeString()}` : ""}
                    </span>
                  </div>
                  <button type="button" onClick={() => replayDeveloperWebhookDelivery(delivery.id)} disabled={busyAction !== null}>Replay</button>
                </article>
              ))}
            </div>
          </div>

          <div className="panel form-panel">
            <div className="panel-head">
              <div>
                <p className="section-label">Marketplace</p>
                <h2>Listings and installs</h2>
              </div>
              <div className="event-toolbar">
                <button type="button" onClick={createDeveloperListing} disabled={busyAction !== null}>Listing</button>
              </div>
            </div>
            <div className="score-summary">
              <strong>{developerSummary?.install_count ?? 0}</strong>
              <span>installs</span>
              <small>
                {developerSummary
                  ? `${developerSummary.approved_marketplace_listing_count}/${developerSummary.marketplace_listing_count} approved`
                  : "No marketplace summary"}
              </small>
            </div>
            <div className="form-grid">
              <label>
                Listing
                <input value={developerForm.listing_name} onChange={(event) => setDeveloperForm({ ...developerForm, listing_name: event.target.value })} />
              </label>
              <label>
                Category
                <input value={developerForm.listing_category} onChange={(event) => setDeveloperForm({ ...developerForm, listing_category: event.target.value })} />
              </label>
              <label>
                Install URL
                <input value={developerForm.listing_install_url} onChange={(event) => setDeveloperForm({ ...developerForm, listing_install_url: event.target.value })} />
              </label>
              <label>
                Support URL
                <input value={developerForm.listing_support_url} onChange={(event) => setDeveloperForm({ ...developerForm, listing_support_url: event.target.value })} />
              </label>
              <label className="wide-field">
                Summary
                <input value={developerForm.listing_summary} onChange={(event) => setDeveloperForm({ ...developerForm, listing_summary: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {developerSummary?.recommended_next_steps.slice(0, 2).map((step) => (
                <article key={step} className="task-card">
                  <div>
                    <strong>Next step</strong>
                    <span>{step}</span>
                  </div>
                </article>
              ))}
              {developerListings.slice(0, 4).map((listing) => (
                <article key={listing.id} className="task-card">
                  <div>
                    <strong>{listing.name}</strong>
                    <span>{listing.category} · {listing.review_status} · {listing.visibility} · {listing.install_count} installs</span>
                  </div>
                  <button type="button" onClick={() => approveDeveloperListing(listing.id)} disabled={busyAction !== null}>Approve</button>
                  <button type="button" onClick={() => recordDeveloperListingInstall(listing.id)} disabled={busyAction !== null}>Install</button>
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
                <button type="button" onClick={escalateSelectedMessage} disabled={busyAction !== null || !selectedMessageId}>Escalate</button>
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
              {escalationRun ? (
                <article className="task-card">
                  <div>
                    <strong>{escalationRun.subject}</strong>
                    <span>Level {escalationRun.escalation_level} · {escalationRun.channel} · {escalationRun.recipient_count} recipients</span>
                    <span>{escalationRun.message}</span>
                  </div>
                </article>
              ) : null}
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
                <button type="button" onClick={createPerformanceModelBenchmarkDataset} disabled={busyAction !== null}>Dataset</button>
                <button type="button" onClick={runPerformanceModelBenchmark} disabled={busyAction !== null}>Benchmark</button>
                <button type="button" onClick={runPerformanceForecastValidation} disabled={busyAction !== null}>Forecast QA</button>
                <button type="button" onClick={sendPerformanceForecastValidationAlert} disabled={busyAction !== null}>Drift alert</button>
                <button type="button" onClick={ingestPerformanceWearableWebhook} disabled={busyAction !== null}>Webhook</button>
                <button type="button" onClick={createWearableConnection} disabled={busyAction !== null}>Connect</button>
                <button type="button" onClick={runWearableConnectionSync} disabled={busyAction !== null}>Sync</button>
                <button type="button" onClick={runWearableConnectionPull} disabled={busyAction !== null}>Pull</button>
                <button type="button" onClick={registerWearableWebhook} disabled={busyAction !== null}>Register</button>
                <button type="button" onClick={startWearableOAuth} disabled={busyAction !== null}>OAuth</button>
                <button type="button" onClick={completeWearableOAuth} disabled={busyAction !== null}>Callback</button>
                <button type="button" onClick={refreshWearableToken} disabled={busyAction !== null}>Refresh</button>
                <button type="button" onClick={reviewSelectedObservation} disabled={busyAction !== null}>Review</button>
                <button type="button" onClick={createPerformanceGoal} disabled={busyAction !== null}>Goal</button>
                <button type="button" onClick={evaluatePerformanceAchievements} disabled={busyAction !== null}>Award</button>
                <button type="button" onClick={runPerformanceInjuryRiskAlertScan} disabled={busyAction !== null}>Risk scan</button>
                <button type="button" onClick={runAssessmentReviewEscalations} disabled={busyAction !== null}>Escalate</button>
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
              <label>
                Provider
                <select value={observationForm.source_provider} onChange={(event) => setObservationForm({ ...observationForm, source_provider: event.target.value })}>
                  <option value="">Infer</option>
                  <option value="whoop">WHOOP</option>
                  <option value="garmin">Garmin</option>
                  <option value="apple_health">Apple Health</option>
                  <option value="fitbit">Fitbit</option>
                  <option value="polar">Polar</option>
                  <option value="oura">Oura</option>
                  <option value="catapult">Catapult</option>
                  <option value="statsports">STATSports</option>
                  <option value="playertek">Playertek</option>
                  <option value="statsbomb">StatsBomb</option>
                  <option value="wyscout">Wyscout</option>
                </select>
              </label>
              <label className="wide-field">
                Evidence text
                <input value={observationForm.evidence_text} onChange={(event) => setObservationForm({ ...observationForm, evidence_text: event.target.value })} />
              </label>
              <label>
                Goal
                <input value={performanceGoalForm.title} onChange={(event) => setPerformanceGoalForm({ ...performanceGoalForm, title: event.target.value })} />
              </label>
              <label>
                Target
                <input type="number" value={performanceGoalForm.target_value} onChange={(event) => setPerformanceGoalForm({ ...performanceGoalForm, target_value: Number(event.target.value) })} />
              </label>
              <label>
                Due
                <input type="date" value={performanceGoalForm.due_at} onChange={(event) => setPerformanceGoalForm({ ...performanceGoalForm, due_at: event.target.value })} />
              </label>
              <label>
                Benchmark cohort
                <select
                  value={performanceBenchmarkScope}
                  onChange={(event) => setPerformanceBenchmarkScope(event.target.value as BenchmarkCohortScope)}
                >
                  <option value="tenant">All athletes</option>
                  <option value="age_group">Age group</option>
                  <option value="position">Position</option>
                  <option value="region">Country/region</option>
                  <option value="local_association">Local association</option>
                  <option value="regional_association">Regional association</option>
                </select>
              </label>
              <label>
                Trend start
                <input
                  type="date"
                  value={performanceTrendPeriodStart}
                  onChange={(event) => setPerformanceTrendPeriodStart(event.target.value)}
                />
              </label>
              <label>
                Trend end
                <input
                  type="date"
                  value={performanceTrendPeriodEnd}
                  onChange={(event) => setPerformanceTrendPeriodEnd(event.target.value)}
                />
              </label>
              <label>
                Trend domain
                <select
                  value={performanceTrendCategory}
                  onChange={(event) => setPerformanceTrendCategory(event.target.value as MetricCategory | "all")}
                >
                  <option value="all">All domains</option>
                  {metricCategoryOptions.map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </label>
              <label>
                Trend metric
                <input
                  value={performanceTrendMetricCode}
                  placeholder="metric code"
                  onChange={(event) => setPerformanceTrendMetricCode(event.target.value)}
                />
              </label>
              <label>
                What-if load
                <input
                  type="number"
                  min="-50"
                  max="50"
                  value={performanceWhatIfAdjustment}
                  onChange={(event) => setPerformanceWhatIfAdjustment(Number(event.target.value))}
                />
              </label>
              <label>
                Readiness
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={performanceWhatIfReadiness}
                  onChange={(event) => setPerformanceWhatIfReadiness(Number(event.target.value))}
                />
              </label>
              <label className="wide-field">
                Risk alert channels
                <span className="check-row">
                  {performanceRiskAlertChannelOptions.map((channel) => (
                    <label key={channel}>
                      <input
                        type="checkbox"
                        checked={performanceRiskAlertChannels.includes(channel)}
                        onChange={() => togglePerformanceRiskAlertChannel(channel)}
                      />
                      {channel.replaceAll("_", " ")}
                    </label>
                  ))}
                </span>
              </label>
            </div>
            <PerformanceVisualDashboard
              summary={performanceSummary}
              assessments={assessments}
              trends={performanceTrends}
              benchmarks={performanceBenchmarks}
            />
            <PerformanceInjuryRiskCard
              risk={performanceInjuryRisk}
              alert={performanceInjuryRiskAlert}
              onSendAlert={sendPerformanceInjuryRiskAlert}
              disabled={busyAction !== null}
            />
            <PerformanceForecastScenarioDashboard scenarios={performanceForecastScenarios} />
            <PerformanceWhatIfScenarioDashboard scenarios={performanceWhatIfScenarios} />
            <PerformanceCohortComparisonDashboard comparisons={performanceCohortComparisons} />
            <PerformanceTrendSeriesDashboard series={performanceTrendSeries} />
            <div className="form-grid">
              <label>
                Queue
                <select
                  value={assessmentReviewQueueFilters.assignment}
                  onChange={(event) =>
                    setAssessmentReviewQueueFilters({
                      ...assessmentReviewQueueFilters,
                      assignment: event.target.value as AssessmentReviewQueueFilters["assignment"]
                    })
                  }
                >
                  <option value="all">All</option>
                  <option value="mine">Mine</option>
                  <option value="unassigned">Unassigned</option>
                  <option value="assigned">Assigned</option>
                </select>
              </label>
              <label>
                SLA
                <select
                  value={assessmentReviewQueueFilters.sla}
                  onChange={(event) =>
                    setAssessmentReviewQueueFilters({
                      ...assessmentReviewQueueFilters,
                      sla: event.target.value as AssessmentReviewQueueFilters["sla"]
                    })
                  }
                >
                  <option value="all">All</option>
                  <option value="overdue">Overdue</option>
                  <option value="due_soon">Due soon</option>
                  <option value="on_track">On track</option>
                </select>
              </label>
              <label>
                Priority
                <select
                  value={assessmentReviewQueueFilters.priority}
                  onChange={(event) =>
                    setAssessmentReviewQueueFilters({
                      ...assessmentReviewQueueFilters,
                      priority: event.target.value as AssessmentReviewQueueFilters["priority"]
                    })
                  }
                >
                  <option value="all">All</option>
                  <option value="urgent">Urgent</option>
                  <option value="high">High</option>
                  <option value="normal">Normal</option>
                  <option value="low">Low</option>
                </select>
              </label>
              <label>
                Review load
                <input
                  readOnly
                  value={`${assessmentReviewQueueSummary.total} open · ${assessmentReviewQueueSummary.urgent} urgent · ${assessmentReviewQueueSummary.overdue} overdue · ${assessmentReviewQueueSummary.dueSoon} soon`}
                />
              </label>
            </div>
            {assessmentReviewSummary ? (
              <div className="task-list">
                <article className="task-card">
                  <div>
                    <strong>Review load · {assessmentReviewSummary.open_count} open</strong>
                    <span>
                      {assessmentReviewSummary.urgent_count} urgent · {assessmentReviewSummary.overdue_count} overdue ·{" "}
                      {assessmentReviewSummary.due_soon_count} due soon · {assessmentReviewSummary.unassigned_count} unassigned
                    </span>
                    <small>
                      Oldest {assessmentReviewSummary.oldest_age_hours}h · average {assessmentReviewSummary.average_age_hours}h ·{" "}
                      {assessmentReviewSummary.escalated_count} previously escalated
                    </small>
                  </div>
                </article>
                {assessmentReviewSummary.reviewer_loads.slice(0, 3).map((load) => (
                  <article key={load.reviewer_person_id ?? "unassigned"} className="task-card">
                    <div>
                      <strong>{load.reviewer_name} · {load.open_count} open</strong>
                      <span>{load.urgent_count} urgent · {load.overdue_count} overdue · {load.escalated_count} escalated</span>
                      <small>Oldest assigned item {load.oldest_age_hours}h.</small>
                    </div>
                  </article>
                ))}
              </div>
            ) : null}
            <div className="task-list">
              {assessmentReviewQueue.slice(0, 6).map((item) => (
                <article key={`review-${item.assessment.id}`} className="task-card">
                  <div>
                    <strong>{item.athlete_name} · ALS {item.assessment.overall_score} · {item.assessment.review_priority}</strong>
                    <span>
                      {item.review_sla_state.replaceAll("_", " ")} · {item.review_age_hours}h open ·{" "}
                      {item.review_assigned_to_name ? `assigned to ${item.review_assigned_to_name}` : "unassigned"}
                    </span>
                    <small>
                      RPE {item.assessment.perceived_exertion ?? "n/a"} · effort {item.assessment.effort_rating ?? "n/a"} ·{" "}
                      {item.assessment.review_due_at ? `due ${new Date(item.assessment.review_due_at).toLocaleString()}` : "no due date"} ·{" "}
                      {item.assessment.summary ?? "Player self-assessment awaiting review."}
                    </small>
                  </div>
                  <span>
                    <button type="button" onClick={() => updateAssessmentQueueItem(item.assessment, { assign_to_self: true }, "assign-me")} disabled={busyAction !== null}>Assign me</button>
                    <button type="button" onClick={() => updateAssessmentQueueItem(item.assessment, { review_due_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() }, "due-24h")} disabled={busyAction !== null}>Due 24h</button>
                    <button type="button" onClick={() => updateAssessmentQueueItem(item.assessment, { review_priority: "urgent" }, "urgent")} disabled={busyAction !== null}>Urgent</button>
                    <button type="button" onClick={() => reviewAssessment(item.assessment, "verified")} disabled={busyAction !== null}>Verify</button>
                    <button type="button" onClick={() => reviewAssessment(item.assessment, "rejected")} disabled={busyAction !== null}>Reject</button>
                  </span>
                </article>
              ))}
              {performanceReviewEscalationRun ? (
                <article className="task-card">
                  <div>
                    <strong>Review escalation · {performanceReviewEscalationRun.escalated_count} escalated</strong>
                    <span>
                      {performanceReviewEscalationRun.overdue_count} overdue · {performanceReviewEscalationRun.due_soon_count} due soon ·{" "}
                      {performanceReviewEscalationRun.message_ids.length} alert message(s)
                    </span>
                    <small>
                      {performanceReviewEscalationRun.dry_run ? "Dry run only." : "In-app alerts sent to performance reviewers and assigned coaches."}
                    </small>
                  </div>
                </article>
              ) : null}
              {performanceInjuryRiskAlertRun ? (
                <article className="task-card">
                  <div>
                    <strong>Injury-risk scan · {performanceInjuryRiskAlertRun.alerted_count} alerted</strong>
                    <span>
                      {performanceInjuryRiskAlertRun.scanned_count} scanned · {performanceInjuryRiskAlertRun.high_risk_count} high risk ·{" "}
                      {performanceInjuryRiskAlertRun.skipped_count} skipped · top score {performanceInjuryRiskAlertRun.highest_score ?? "n/a"}
                    </span>
                    <small>
                      {performanceInjuryRiskAlertRun.dry_run
                        ? "Dry run only."
                        : `${performanceInjuryRiskAlertRun.message_ids.length} urgent alert message(s) across ${performanceInjuryRiskAlertRun.channels.join(", ")} with ${performanceInjuryRiskAlertRun.repeat_after_hours}h duplicate suppression.`}
                    </small>
                  </div>
                </article>
              ) : null}
              {performanceAchievementRun ? (
                <article className="task-card">
                  <div>
                    <strong>Achievement scan · {performanceAchievementRun.awarded_count} awarded</strong>
                    <span>{performanceAchievementRun.evaluated_goals} goals evaluated · {performanceAchievementRun.updated_goals} updated</span>
                  </div>
                </article>
              ) : null}
              {performanceAwards.slice(0, 3).map((award) => (
                <article key={award.id} className="task-card">
                  <div>
                    <strong>{award.title}</strong>
                    <span>{award.achievement_type.replaceAll("_", " ")} · {award.badge_code}</span>
                    <small>{award.source_summary ?? "Awarded from performance history."}</small>
                  </div>
                </article>
              ))}
              {performanceGoals.slice(0, 3).map((goal) => (
                <article key={goal.id} className="task-card">
                  <div>
                    <strong>{goal.title} · {goal.status}</strong>
                    <span>
                      current {goal.current_value ?? "—"} / target {goal.target_value}
                      {goal.due_at ? ` · due ${goal.due_at}` : ""}
                    </span>
                    <small>{goal.reward_badge ?? "Performance goal"} · {goal.notes ?? "No notes"}</small>
                  </div>
                </article>
              ))}
              {performanceIngestion ? (
                <article className="task-card">
                  <div>
                    <strong>{performanceIngestion.extractor}</strong>
                    <span>{performanceIngestion.summary} · confidence {Math.round(performanceIngestion.confidence * 100)}%</span>
                    <small>
                      {(performanceIngestion.source_provider ?? "provider-neutral").replaceAll("_", " ")} ·{" "}
                      {performanceIngestion.parser_method.replaceAll("_", " ")} · {performanceIngestion.parser_confidence_reason}
                    </small>
                    {performanceIngestion.parser_warnings.length ? (
                      <small>{performanceIngestion.parser_warnings.join(" · ")}</small>
                    ) : null}
                    {performanceIngestion.model_policy ? (
                      <small>
                        {performanceIngestion.model_assisted ? "model applied" : "model evaluated"} ·{" "}
                        {performanceIngestion.model_policy} ·{" "}
                        {performanceIngestion.model_confidence !== null
                          ? `${Math.round(performanceIngestion.model_confidence * 100)}%`
                          : "no score"}
                      </small>
                    ) : null}
                  </div>
                </article>
              ) : null}
              {performanceModelBenchmark ? (
                <article className="task-card">
                  <div>
                    <strong>{performanceModelBenchmark.model_policy} benchmark</strong>
                    <span>
                      {performanceModelBenchmark.passed_count}/{performanceModelBenchmark.case_count} passed ·{" "}
                      {Math.round(performanceModelBenchmark.accuracy * 100)}% accuracy · MAE{" "}
                      {performanceModelBenchmark.mean_absolute_error}
                    </span>
                    <small>
                      {performanceModelBenchmark.cases.slice(0, 3).map((item) =>
                        `${item.case_id}: ${item.passed ? "pass" : "fail"} via ${item.parser_method.replaceAll("_", " ")}`
                      ).join(" · ")}
                    </small>
                  </div>
                </article>
              ) : null}
              {performanceForecastValidationRun ? (
                <article className="task-card">
                  <div>
                    <strong>
                      Forecast QA · {performanceForecastValidationRun.drift_level.replaceAll("_", " ")}
                    </strong>
                    <span>
                      {performanceForecastValidationRun.passed_count}/{performanceForecastValidationRun.evaluated_count} passed ·{" "}
                      {performanceForecastValidationRun.drift_count} drift · MAE{" "}
                      {performanceForecastValidationRun.mean_absolute_error} · MRE{" "}
                      {Math.round(performanceForecastValidationRun.mean_relative_error * 100)}%
                    </span>
                    <small>
                      {performanceForecastValidationRun.model_policy} ·{" "}
                      {new Date(performanceForecastValidationRun.created_at).toLocaleString()}
                    </small>
                    <small>{performanceForecastValidationRun.recommendation}</small>
                    {performanceForecastValidationRun.details.length ? (
                      <small>
                        {performanceForecastValidationRun.details.slice(0, 3).map((item) =>
                          `${item.metric_name}: ${item.passed ? "pass" : "review"} ` +
                          `${item.predicted_value ?? "n/a"} vs ${item.actual_value}`
                        ).join(" · ")}
                      </small>
                    ) : null}
                  </div>
                  <span>
                    <button type="button" onClick={sendPerformanceForecastValidationAlert} disabled={busyAction !== null}>Alert</button>
                  </span>
                </article>
              ) : null}
              {performanceForecastValidationAlert ? (
                <article className="task-card">
                  <div>
                    <strong>
                      Forecast drift alert · {performanceForecastValidationAlert.sent ? "sent" : "not sent"}
                    </strong>
                    <span>
                      {performanceForecastValidationAlert.drift_level.replaceAll("_", " ")} ·{" "}
                      {performanceForecastValidationAlert.channel_count} channel(s) ·{" "}
                      {performanceForecastValidationAlert.recipient_count} recipient destination(s)
                    </span>
                    <small>
                      {performanceForecastValidationAlert.sent
                        ? `${performanceForecastValidationAlert.message_ids.length} alert message(s) created.`
                        : performanceForecastValidationAlert.skipped_reason ?? "No alert created."}
                    </small>
                  </div>
                </article>
              ) : null}
              {performanceForecastValidationRuns
                .filter((run) => run.id !== performanceForecastValidationRun?.id)
                .slice(0, 2)
                .map((run) => (
                  <article key={run.id} className="task-card">
                    <div>
                      <strong>Previous forecast QA · {run.drift_level.replaceAll("_", " ")}</strong>
                      <span>
                        {run.passed_count}/{run.evaluated_count} passed · {Math.round(run.mean_relative_error * 100)}% MRE
                      </span>
                      <small>{new Date(run.created_at).toLocaleString()} · {run.model_policy}</small>
                    </div>
                  </article>
                ))}
              {performanceModelBenchmarkDatasets.slice(0, 3).map((dataset) => (
                <article key={dataset.id} className="task-card">
                  <div>
                    <strong>{dataset.name} · {dataset.case_count} case(s)</strong>
                    <span>
                      {dataset.last_accuracy === null
                        ? "not run yet"
                        : `${Math.round(dataset.last_accuracy * 100)}% latest accuracy`} ·{" "}
                      {dataset.model_policy ?? "default model policy"}
                    </span>
                    <small>
                      {dataset.last_run_at ? `last run ${new Date(dataset.last_run_at).toLocaleString()}` : dataset.description ?? dataset.slug}
                    </small>
                    {dataset.cases.length ? (
                      <small>
                        {dataset.cases.slice(0, 3).map((item) =>
                          `${item.case_id}: ${item.metric_code}=${item.expected_value}`
                        ).join(" · ")}
                      </small>
                    ) : null}
                  </div>
                </article>
              ))}
              {performanceWebhookIngest ? (
                <article className="task-card">
                  <div>
                    <strong>
                      {performanceWebhookIngest.source_provider} webhook ·{" "}
                      {performanceWebhookIngest.replayed ? "replayed" : "accepted"}
                    </strong>
                    <span>
                      {performanceWebhookIngest.observation_count} observation(s) ·{" "}
                      {performanceWebhookIngest.skipped_metric_count} skipped ·{" "}
                      {performanceWebhookIngest.signature_required
                        ? performanceWebhookIngest.signature_validated ? "signed" : "signature failed"
                        : "signature optional"}
                    </span>
                    <small>{performanceWebhookIngest.external_event_id} · {performanceWebhookIngest.payload_hash.slice(0, 12)}</small>
                  </div>
                </article>
              ) : null}
              {wearableSyncRun ? (
                <article className="task-card">
                  <div>
                    <strong>{wearableSyncRun.provider} sync · {wearableSyncRun.status}</strong>
                    <span>
                      {wearableSyncRun.observation_count} observation(s) · {wearableSyncRun.skipped_metric_count} skipped ·{" "}
                      {wearableSyncRun.provider_rate_limited
                        ? `rate limited${wearableSyncRun.provider_retry_after_seconds ? ` ${wearableSyncRun.provider_retry_after_seconds}s` : ""}`
                        : wearableSyncRun.replayed
                          ? "replayed"
                          : wearableSyncRun.provider_status_code
                            ? `HTTP ${wearableSyncRun.provider_status_code}`
                            : wearableSyncRun.sync_mode} · {wearableSyncRun.provider_page_count || 1} page(s)
                    </span>
                    <small>
                      {wearableSyncRun.message ?? wearableSyncRun.external_event_id ?? "Provider sync run recorded."}
                      {wearableSyncRun.provider_response_hash ? ` · ${wearableSyncRun.provider_response_hash.slice(0, 12)}` : ""}
                    </small>
                  </div>
                </article>
              ) : null}
              {wearableOAuthStart ? (
                <article className="task-card">
                  <div>
                    <strong>{wearableOAuthStart.provider} OAuth authorization</strong>
                    <span>{wearableOAuthStart.scopes.join(", ")} · expires {new Date(wearableOAuthStart.expires_at).toLocaleTimeString()}</span>
                    <small>{wearableOAuthStart.authorization_url}</small>
                  </div>
                </article>
              ) : null}
              {wearableOAuthCallback ? (
                <article className="task-card">
                  <div>
                    <strong>{wearableOAuthCallback.connection.provider} OAuth · {wearableOAuthCallback.status}</strong>
                    <span>{wearableOAuthCallback.connection.access_token_configured ? "access token path set" : "token path missing"} · {wearableOAuthCallback.authorization_code_ref}</span>
                    <small>{wearableOAuthCallback.message}</small>
                  </div>
                </article>
              ) : null}
              {wearableTokenRefresh ? (
                <article className="task-card">
                  <div>
                    <strong>{wearableTokenRefresh.connection.provider} token refresh · {wearableTokenRefresh.status}</strong>
                    <span>
                      {wearableTokenRefresh.refresh_token_rotated ? "refresh token rotated" : "refresh token retained"} ·{" "}
                      {wearableTokenRefresh.access_token_ref ?? "token ref unavailable"}
                    </span>
                    <small>{wearableTokenRefresh.message}</small>
                  </div>
                </article>
              ) : null}
              {wearableWebhookRegistration ? (
                <article className="task-card">
                  <div>
                    <strong>
                      {wearableWebhookRegistration.connection.provider} webhook registration · {wearableWebhookRegistration.status}
                    </strong>
                    <span>
                      {wearableWebhookRegistration.provider_status_code
                        ? `HTTP ${wearableWebhookRegistration.provider_status_code}`
                        : "provider-console payload"} ·{" "}
                      {wearableWebhookRegistration.registration_payload_hash.slice(0, 12)}
                    </span>
                    <small>{wearableWebhookRegistration.message}</small>
                  </div>
                </article>
              ) : null}
              {wearableConnections.slice(0, 3).map((connection) => (
                <article key={connection.id} className="task-card">
                  <div>
                    <strong>{connection.display_name} · {connection.status}</strong>
                    <span>
                      {connection.provider} · {connection.external_athlete_ref} ·{" "}
                      {connection.access_token_recorded ? "token fingerprint recorded" : connection.access_token_configured ? "token path configured" : "token missing"} ·{" "}
                      {connection.provider_pull_configured ? "pull configured" : "pull not configured"}
                    </span>
                    <small>
                      {connection.webhook_registered ? "webhook registered" : "webhook not registered"} ·{" "}
                      {connection.provider_webhook_registered_at ? `registered ${new Date(connection.provider_webhook_registered_at).toLocaleString()}` : connection.provider_webhook_registration_hash ? "registration prepared" : "registration pending"} ·{" "}
                      {connection.oauth_authorized_at ? `authorized ${new Date(connection.oauth_authorized_at).toLocaleString()}` : connection.oauth_state_pending ? "OAuth pending" : "OAuth not started"} ·{" "}
                      {connection.token_last_refreshed_at ? `token refreshed ${new Date(connection.token_last_refreshed_at).toLocaleString()}` : connection.last_sync_at ? `last sync ${new Date(connection.last_sync_at).toLocaleString()}` : "not synced"}
                    </small>
                  </div>
                </article>
              ))}
              {performanceBenchmarks.slice(0, 3).map((benchmark) => (
                <article key={benchmark.metric_definition_id} className="task-card">
                  <div>
                    <strong>{benchmark.metric_name} · {benchmark.benchmark_band.replaceAll("_", " ")}</strong>
                    <span>
                      {benchmark.percentile_rank === null ? "No athlete percentile" : `${benchmark.percentile_rank}th percentile`}
                      {" · "}
                      cohort avg {benchmark.cohort_average ?? "—"}{benchmark.unit ? ` ${benchmark.unit}` : ""}
                    </span>
                    <small>{benchmark.recommendation}</small>
                    <small>{benchmark.cohort_label} · {benchmark.cohort_scope.replaceAll("_", " ")}</small>
                  </div>
                </article>
              ))}
              {performanceTrends.slice(0, 3).map((trend) => (
                <article key={`${trend.metric_definition_id}-trend`} className="task-card">
                  <div>
                    <strong>{trend.metric_name} · {trend.trend_direction.replaceAll("_", " ")}</strong>
                    <span>
                      latest {trend.latest_value ?? "—"}{trend.unit ? ` ${trend.unit}` : ""}
                      {" · "}
                      forecast {trend.forecast_next_value ?? "—"}{trend.unit ? ` ${trend.unit}` : ""}
                    </span>
                    <small>
                      consistency {trend.consistency_index ?? "—"} · {trend.recommendation}
                    </small>
                  </div>
                </article>
              ))}
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
                    <strong>ALS {assessment.overall_score} · {assessment.verification_status}</strong>
                    <span>{assessment.summary ?? "Assessment recorded"}</span>
                    <small>
                      RPE {assessment.perceived_exertion ?? "n/a"} · effort {assessment.effort_rating ?? "n/a"}
                    </small>
                  </div>
                  {assessment.verification_status === "pending_review" ? (
                    <span>
                      <button type="button" onClick={() => reviewAssessment(assessment, "verified")} disabled={busyAction !== null}>Verify</button>
                      <button type="button" onClick={() => reviewAssessment(assessment, "rejected")} disabled={busyAction !== null}>Reject</button>
                    </span>
                  ) : null}
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
              <button type="button" onClick={registerAgentModel} disabled={busyAction !== null}>Register model</button>
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
              <div>
                <span className="muted">Ledger</span>
                <strong>{agentLedgerVerification?.valid ? "valid" : "check"}</strong>
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
                    {agentLedgerVerification ? (
                      <span>
                        Ledger {agentLedgerVerification.verified_records}/{agentLedgerVerification.total_records} · {agentLedgerVerification.latest_record_hash?.slice(0, 12) ?? "empty"}
                      </span>
                    ) : null}
                  </div>
                </article>
              ) : null}
              {agentTransparency ? (
                <article className="task-card">
                  <div>
                    <strong>Model transparency · {agentTransparency.total_models} policies · {agentTransparency.total_runs} runs</strong>
                    <span>
                      {agentTransparency.credential_boundary} · ledger {agentTransparency.ledger_valid ? "valid" : "broken"} · review {agentTransparency.human_review_required}
                    </span>
                    <span>{agentTransparency.recommendations[0] ?? "Transparency report ready"}</span>
                  </div>
                </article>
              ) : null}
              {agentEthicalScorecard ? (
                <article className="task-card">
                  <div>
                    <strong>Ethical AI scorecard · {agentEthicalScorecard.score}/100 · {agentEthicalScorecard.grade}</strong>
                    <span>{agentEthicalScorecard.approved_models}/{agentEthicalScorecard.total_models} models approved · {agentEthicalScorecard.bias_audits} audits · {agentEthicalScorecard.pending_appeals} appeals</span>
                    <span>{agentEthicalScorecard.public_summary}</span>
                    <span>{agentEthicalScorecard.improvement_actions[0] ?? "Publish-ready"}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={publishAgentScorecardSnapshot}>Publish snapshot</button>
                  </div>
                </article>
              ) : null}
              {agentScorecardReadiness ? (
                <article className="task-card">
                  <div>
                    <strong>{agentScorecardReadiness.current_period_label} publication · {agentScorecardReadiness.readiness_status}</strong>
                    <span>
                      Due {new Date(agentScorecardReadiness.next_publication_due_at).toLocaleDateString()} · {agentScorecardReadiness.days_until_due} days · score {agentScorecardReadiness.score}/100
                    </span>
                    <span>
                      {agentScorecardReadiness.flagged_comment_count} flagged comments · {agentScorecardReadiness.pending_appeal_count} pending appeals · current {agentScorecardReadiness.current_period_published ? "published" : "unpublished"}
                    </span>
                    <span>{agentScorecardReadiness.recommended_action}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={deliverAgentScorecardReminder}>Send reminder</button>
                    <button type="button" onClick={runAgentScorecardReminderAutomation}>Run due check</button>
                    <button type="button" onClick={runAgentScorecardAutomation}>Run automation</button>
                  </div>
                </article>
              ) : null}
              {agentScorecardAutomationRun ? (
                <article className="task-card">
                  <div>
                    <strong>
                      AI scorecard automation · {agentScorecardAutomationRun.sent_count} lanes sent
                    </strong>
                    <span>
                      {agentScorecardAutomationRun.evaluated_count} evaluated · {agentScorecardAutomationRun.skipped_count} skipped · {agentScorecardAutomationRun.message_count} messages
                    </span>
                    <span>
                      {agentScorecardAutomationRun.runs[0]?.skipped_reason ??
                        agentScorecardAutomationRun.runs[0]?.organization_name ??
                        "Automation run ready for scheduler execution"}
                    </span>
                  </div>
                </article>
              ) : null}
              {agentScorecardReminderRun ? (
                <article className="task-card">
                  <div>
                    <strong>{agentScorecardReminderRun.period_label} reminder run · {agentScorecardReminderRun.sent ? "sent" : "skipped"}</strong>
                    <span>
                      Due by {new Date(agentScorecardReminderRun.due_by).toLocaleDateString()} · {agentScorecardReminderRun.recipient_count} recipients · {agentScorecardReminderRun.readiness_status}
                    </span>
                    <span>{agentScorecardReminderRun.skipped_reason ?? "Due-window reminder was delivered."}</span>
                  </div>
                </article>
              ) : null}
              {agentScorecardReminder ? (
                <article className="task-card">
                  <div>
                    <strong>{agentScorecardReminder.period_label} reminder · {agentScorecardReminder.message_status ?? "not sent"}</strong>
                    <span>
                      {agentScorecardReminder.channel} · {agentScorecardReminder.recipient_count} recipients · {agentScorecardReminder.readiness_status}
                    </span>
                    <span>{agentScorecardReminder.failure_reason ?? agentScorecardReminder.subject}</span>
                    <span>{agentScorecardReminder.body.split("\n")[0]}</span>
                  </div>
                </article>
              ) : null}
              {agentScorecardArtifactLink ? (
                <article className="task-card">
                  <div>
                    <strong>{agentScorecardArtifactLink.period_label} artifact link · {agentScorecardArtifactLink.artifact_format}</strong>
                    <span>
                      Expires {new Date(agentScorecardArtifactLink.expires_at).toLocaleString()} · {agentScorecardArtifactLink.size_bytes} bytes
                    </span>
                    <span>{agentScorecardArtifactLink.checksum.slice(0, 16)} · {agentScorecardArtifactLink.content_type}</span>
                  </div>
                  <a
                    href={`${apiBaseUrl}${agentScorecardArtifactLink.signed_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open
                  </a>
                </article>
              ) : null}
              {agentScorecardArtifactAccessSummary ? (
                <article className="task-card">
                  <div>
                    <strong>Artifact access · {agentScorecardArtifactAccessSummary.total_events} events</strong>
                    <span>
                      {agentScorecardArtifactAccessSummary.link_created_count} links · {agentScorecardArtifactAccessSummary.artifact_opened_count} opens · {agentScorecardArtifactAccessSummary.unique_requester_count} requesters
                    </span>
                    <span>
                      {agentScorecardArtifactAccessSummary.pdf_count} PDF · {agentScorecardArtifactAccessSummary.markdown_count} Markdown · last {agentScorecardArtifactAccessSummary.last_accessed_at ? new Date(agentScorecardArtifactAccessSummary.last_accessed_at).toLocaleString() : "never"}
                    </span>
                    <span>
                      {agentScorecardArtifactAccessSummary.by_source.slice(0, 2).map((bucket) => `${bucket.label.replaceAll("_", " ")} ${bucket.count}`).join(" · ") || "No source activity"}
                    </span>
                    <span>
                      {agentScorecardArtifactAccessSummary.daily_trend.slice(0, 3).map((bucket) => `${bucket.date}: ${bucket.total_count}`).join(" · ") || "No daily access trend"}
                    </span>
                    <span>
                      {agentScorecardArtifactAccessSummary.anomalies[0]
                        ? `${agentScorecardArtifactAccessSummary.anomalies[0].severity}: ${agentScorecardArtifactAccessSummary.anomalies[0].title}`
                        : "No artifact access anomalies"}
                    </span>
                  </div>
                  <div className="event-toolbar">
                    <button
                      type="button"
                      onClick={deliverAgentScorecardArtifactAnomalyAlert}
                      disabled={
                        busyAction !== null ||
                        agentScorecardArtifactAccessSummary.anomalies.length === 0
                      }
                    >
                      Alert managers
                    </button>
                    <button
                      type="button"
                      onClick={runAgentScorecardArtifactAnomalyAlertAutomation}
                      disabled={busyAction !== null}
                    >
                      Run alert check
                    </button>
                  </div>
                </article>
              ) : null}
              {agentScorecardArtifactAccessSummary?.daily_trend.slice(0, 4).map((bucket) => (
                <article key={bucket.date} className="task-card">
                  <div>
                    <strong>{bucket.date} artifact activity · {bucket.total_count} events</strong>
                    <span>{bucket.link_created_count} links created · {bucket.artifact_opened_count} artifacts opened</span>
                  </div>
                </article>
              ))}
              {agentScorecardArtifactAccessSummary ? (
                <ArtifactAccessTrendCard summary={agentScorecardArtifactAccessSummary} />
              ) : null}
              {agentScorecardArtifactAnomalyAlertRun ? (
                <article className="task-card">
                  <div>
                    <strong>
                      Artifact anomaly run · {agentScorecardArtifactAnomalyAlertRun.sent ? "sent" : "skipped"}
                    </strong>
                    <span>
                      {agentScorecardArtifactAnomalyAlertRun.anomaly_count} anomalies · {agentScorecardArtifactAnomalyAlertRun.recipient_count} recipients · {agentScorecardArtifactAnomalyAlertRun.channel}
                    </span>
                    <span>{agentScorecardArtifactAnomalyAlertRun.skipped_reason ?? "Artifact anomaly alert run delivered messages."}</span>
                  </div>
                </article>
              ) : null}
              {agentScorecardArtifactAnomalyAlert ? (
                <article className="task-card">
                  <div>
                    <strong>
                      Artifact anomaly alert · {agentScorecardArtifactAnomalyAlert.delivered ? "sent" : "skipped"}
                    </strong>
                    <span>
                      {agentScorecardArtifactAnomalyAlert.channel} · {agentScorecardArtifactAnomalyAlert.anomaly_count} anomalies · {agentScorecardArtifactAnomalyAlert.recipient_count} recipients
                    </span>
                    <span>{agentScorecardArtifactAnomalyAlert.failure_reason ?? agentScorecardArtifactAnomalyAlert.subject}</span>
                    <span>{agentScorecardArtifactAnomalyAlert.body.split("\n")[0]}</span>
                  </div>
                </article>
              ) : null}
              {agentScorecardArtifactAccessSummary?.anomalies.slice(0, 2).map((anomaly) => (
                <article key={anomaly.code} className="task-card">
                  <div>
                    <strong>{anomaly.severity} · {anomaly.title}</strong>
                    <span>{anomaly.evidence}</span>
                    <span>{anomaly.recommended_action}</span>
                  </div>
                </article>
              ))}
              {agentScorecardArtifactAccesses.slice(0, 3).map((access) => (
                <article key={access.id} className="task-card">
                  <div>
                    <strong>{(access.request_source ?? access.event_type).replaceAll("_", " ")} · {access.artifact_format}</strong>
                    <span>{new Date(access.accessed_at).toLocaleString()} · {access.size_bytes} bytes · {access.content_type}</span>
                    <span>{access.request_ip ?? "unknown IP"} · {access.user_agent?.slice(0, 80) ?? "unknown client"}</span>
                    <span>{access.filename} · {access.checksum.slice(0, 16)}</span>
                  </div>
                </article>
              ))}
              {agentScorecardPublications.slice(0, 2).map((publication) => (
                <article key={publication.id} className="task-card">
                  <div>
                    <strong>{publication.period_label} publication · {publication.score}/100 · {publication.grade}</strong>
                    <span>{publication.published_comment_count} comments · {publication.flagged_comment_count} held · ledger {publication.ledger_valid ? "valid" : "review"}</span>
                    <span>{new Date(publication.published_at).toLocaleDateString()} · {publication.snapshot_hash.slice(0, 16)}</span>
                    <span>{publication.public_summary}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => downloadAgentScorecardPublication(publication, "markdown")}>Markdown</button>
                    <button type="button" onClick={() => downloadAgentScorecardPublication(publication, "pdf")}>PDF</button>
                    <button type="button" onClick={() => shareAgentScorecardPublication(publication, "pdf")}>Link</button>
                  </div>
                </article>
              ))}
              {agentScorecardComments.slice(0, 4).map((comment) => (
                <article key={comment.id} className="task-card">
                  <div>
                    <strong>Scorecard comment · {comment.status}</strong>
                    <span>{comment.display_name} · {comment.affiliation ?? "community"} · {comment.consent_to_publish ? "publish consent" : "private only"}</span>
                    <span>
                      {comment.contact_email ?? "no contact"} · abuse {comment.abuse_score}/100
                      {comment.abuse_reason ? ` · ${comment.abuse_reason}` : ""}
                    </span>
                    <span>{new Date(comment.submitted_at).toLocaleDateString()}</span>
                    <span>{comment.comment}</span>
                  </div>
                  <div className="event-toolbar">
                    <button
                      type="button"
                      onClick={() => moderateAgentScorecardComment(comment, "published")}
                      disabled={!comment.consent_to_publish}
                    >
                      Publish
                    </button>
                    <button type="button" onClick={() => moderateAgentScorecardComment(comment, "hidden")}>Hide</button>
                    <button type="button" onClick={() => moderateAgentScorecardComment(comment, "flagged")}>Flag</button>
                    <button type="button" onClick={() => moderateAgentScorecardComment(comment, "private_feedback")}>Private</button>
                  </div>
                </article>
              ))}
              {agentTransparency?.models.slice(0, 3).map((model) => (
                <article key={model.model_policy} className="task-card">
                  <div>
                    <strong>{model.model_policy} · {model.registry_status ?? model.risk_band}</strong>
                    <span>{model.agent_count} agents · {model.run_count} runs · {model.execution_modes.join(", ") || "not run"}</span>
                    <span>{model.registered_risk_tier ?? "unregistered"} · {model.documentation_url ?? "no registry docs"}</span>
                    <span>{model.transparency_notes}</span>
                  </div>
                </article>
              ))}
              {agentModelRegistry.slice(0, 3).map((registry) => (
                <article key={registry.id} className="task-card">
                  <div>
                    <strong>{registry.model_policy} · {registry.review_status}</strong>
                    <span>{registry.provider} · {registry.risk_tier} · {registry.data_residency ?? "residency unset"}</span>
                    <span>{registry.use_case}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => runAgentBiasAudit(registry)}>Bias audit</button>
                    <button type="button" onClick={() => updateAgentModelRegistryStatus(registry, "approved")}>Approve</button>
                    <button type="button" onClick={() => updateAgentModelRegistryStatus(registry, "blocked")}>Block</button>
                    <button type="button" onClick={() => updateAgentModelRegistryStatus(registry, "retired")}>Retire</button>
                  </div>
                </article>
              ))}
              {agentBiasAudits.slice(0, 3).map((audit) => (
                <article key={audit.id} className="task-card">
                  <div>
                    <strong>{audit.model_policy} · bias {audit.status}</strong>
                    <span>{audit.audit_dimension} · {audit.population_slice} · score {audit.disparity_score.toFixed(3)}</span>
                    <span>{audit.severity} · sample {audit.sample_size} · {audit.mitigation_status}</span>
                    <span>{audit.recommendation}</span>
                  </div>
                </article>
              ))}
              {agentDecisionAppeals.slice(0, 3).map((appeal) => (
                <article key={appeal.id} className="task-card">
                  <div>
                    <strong>{appeal.model_policy} · appeal {appeal.status}</strong>
                    <span>{appeal.reason} · due {new Date(appeal.due_at).toLocaleDateString()}</span>
                    <span>{appeal.simple_explanation}</span>
                    <span>{appeal.resolution_notes ?? appeal.alternative_options}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => resolveAgentDecisionAppeal(appeal, "upheld")}>Uphold</button>
                    <button type="button" onClick={() => resolveAgentDecisionAppeal(appeal, "modified")}>Modify</button>
                    <button type="button" onClick={() => resolveAgentDecisionAppeal(appeal, "overturned")}>Overturn</button>
                  </div>
                </article>
              ))}
              {agentRuns.slice(0, 3).map((run) => (
                <article key={run.id} className="task-card">
                  <div>
                    <strong>#{run.ledger_sequence} · {run.agent_name} · {run.event_type} · {run.status}</strong>
                    <span>{run.execution_mode} · {run.model_policy} · {run.governance_notes}</span>
                    <span>{run.record_hash.slice(0, 12)}{run.previous_record_hash ? ` <- ${run.previous_record_hash.slice(0, 12)}` : ""}</span>
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
                    <button type="button" onClick={() => applyAgentWorkerCallback(task)}>Callback</button>
                    <button type="button" onClick={() => submitAgentDecisionAppeal(task)}>Appeal</button>
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
              <h2>Consent, checks, credentials, and incidents</h2>
            </div>
            <div className="event-toolbar">
              <button type="button" onClick={createGuardian} disabled={busyAction !== null}>Link guardian</button>
              <button type="button" onClick={requestConsent} disabled={busyAction !== null}>Request consent</button>
              <button type="button" onClick={createBackgroundCheck} disabled={busyAction !== null}>Request check</button>
              <button type="button" onClick={createComplianceCredential} disabled={busyAction !== null}>Track credential</button>
              <button type="button" onClick={createSafeguardingIncident} disabled={busyAction !== null}>Log incident</button>
              <button type="button" onClick={reconcileCompliance} disabled={busyAction !== null}>Reconcile</button>
            </div>
          </div>
          <div className="consent-grid">
            <div>
              <span className="muted">Compliance</span>
              <strong>{complianceSummary ? `${complianceSummary.overall_compliance_percent}%` : "Pending"}</strong>
            </div>
            <div>
              <span className="muted">Checks</span>
              <strong>{complianceSummary ? `${complianceSummary.clear_background_checks}/${complianceSummary.total_background_checks}` : "0/0"}</strong>
            </div>
            <div>
              <span className="muted">Renewals</span>
              <strong>{complianceSummary?.expiring_credentials ?? 0}</strong>
            </div>
            <div>
              <span className="muted">Open incidents</span>
              <strong>{complianceSummary?.open_incidents ?? 0}</strong>
            </div>
            <div>
              <span className="muted">Critical</span>
              <strong>{complianceSummary?.critical_incidents ?? 0}</strong>
            </div>
            <div>
              <span className="muted">Regulatory</span>
              <strong>{complianceSummary?.regulatory_incidents ?? 0}</strong>
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
          <div className="form-grid three">
            <label>
              Incident
              <input value={incidentForm.title} onChange={(event) => setIncidentForm({ ...incidentForm, title: event.target.value })} />
            </label>
            <label>
              Type
              <select value={incidentForm.incident_type} onChange={(event) => setIncidentForm({ ...incidentForm, incident_type: event.target.value as SafeguardingIncidentType })}>
                <option value="injury">Injury</option>
                <option value="medical">Medical</option>
                <option value="safeguarding">Safeguarding</option>
                <option value="misconduct">Misconduct</option>
                <option value="facility">Facility</option>
                <option value="transport">Transport</option>
                <option value="weather">Weather</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>
              Severity
              <select value={incidentForm.severity} onChange={(event) => setIncidentForm({ ...incidentForm, severity: event.target.value as SafeguardingIncidentSeverity })}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label>
              Occurred
              <input type="datetime-local" value={incidentForm.occurred_at} onChange={(event) => setIncidentForm({ ...incidentForm, occurred_at: event.target.value })} />
            </label>
            <label>
              Location
              <input value={incidentForm.location} onChange={(event) => setIncidentForm({ ...incidentForm, location: event.target.value })} />
            </label>
            <label>
              Medical follow-up
              <select value={incidentForm.medical_follow_up_required} onChange={(event) => setIncidentForm({ ...incidentForm, medical_follow_up_required: event.target.value })}>
                <option value="unknown">Unknown</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
                <option value="urgent">Urgent</option>
              </select>
            </label>
            <label className="wide-field">
              Description
              <textarea value={incidentForm.description} onChange={(event) => setIncidentForm({ ...incidentForm, description: event.target.value })} />
            </label>
            <label className="wide-field">
              Immediate action
              <textarea value={incidentForm.immediate_action} onChange={(event) => setIncidentForm({ ...incidentForm, immediate_action: event.target.value })} />
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={incidentForm.regulatory_report_required} onChange={(event) => setIncidentForm({ ...incidentForm, regulatory_report_required: event.target.checked })} />
              Regulatory report
            </label>
          </div>
          <div className="form-grid three">
            <label>
              Check provider
              <input value={backgroundCheckForm.provider} onChange={(event) => setBackgroundCheckForm({ ...backgroundCheckForm, provider: event.target.value })} />
            </label>
            <label>
              Check type
              <input value={backgroundCheckForm.check_type} onChange={(event) => setBackgroundCheckForm({ ...backgroundCheckForm, check_type: event.target.value })} />
            </label>
            <label>
              Requested
              <input type="datetime-local" value={backgroundCheckForm.requested_at} onChange={(event) => setBackgroundCheckForm({ ...backgroundCheckForm, requested_at: event.target.value })} />
            </label>
            <label>
              Check expiry
              <input type="date" value={backgroundCheckForm.expires_at} onChange={(event) => setBackgroundCheckForm({ ...backgroundCheckForm, expires_at: event.target.value })} />
            </label>
            <label>
              Reference
              <input value={backgroundCheckForm.external_reference} onChange={(event) => setBackgroundCheckForm({ ...backgroundCheckForm, external_reference: event.target.value })} />
            </label>
            <label>
              Check notes
              <input value={backgroundCheckForm.notes} onChange={(event) => setBackgroundCheckForm({ ...backgroundCheckForm, notes: event.target.value })} />
            </label>
          </div>
          <div className="form-grid three">
            <label>
              Credential
              <input value={credentialForm.title} onChange={(event) => setCredentialForm({ ...credentialForm, title: event.target.value })} />
            </label>
            <label>
              Credential type
              <select value={credentialForm.credential_type} onChange={(event) => setCredentialForm({ ...credentialForm, credential_type: event.target.value as ComplianceCredentialType })}>
                <option value="safeguarding_training">Safeguarding training</option>
                <option value="first_aid">First aid</option>
                <option value="coaching_license">Coaching license</option>
                <option value="officiating_license">Officiating license</option>
                <option value="driver_certification">Driver certification</option>
                <option value="background_check">Background check</option>
                <option value="medical_license">Medical license</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>
              Issuer
              <input value={credentialForm.issuing_body} onChange={(event) => setCredentialForm({ ...credentialForm, issuing_body: event.target.value })} />
            </label>
            <label>
              Number
              <input value={credentialForm.credential_number} onChange={(event) => setCredentialForm({ ...credentialForm, credential_number: event.target.value })} />
            </label>
            <label>
              Issued
              <input type="date" value={credentialForm.issued_at} onChange={(event) => setCredentialForm({ ...credentialForm, issued_at: event.target.value })} />
            </label>
            <label>
              Expires
              <input type="date" value={credentialForm.expires_at} onChange={(event) => setCredentialForm({ ...credentialForm, expires_at: event.target.value })} />
            </label>
            <label>
              Renewal due
              <input type="date" value={credentialForm.renewal_due_at} onChange={(event) => setCredentialForm({ ...credentialForm, renewal_due_at: event.target.value })} />
            </label>
            <label>
              Verify URL
              <input value={credentialForm.verification_url} onChange={(event) => setCredentialForm({ ...credentialForm, verification_url: event.target.value })} />
            </label>
            <label>
              Credential notes
              <input value={credentialForm.notes} onChange={(event) => setCredentialForm({ ...credentialForm, notes: event.target.value })} />
            </label>
          </div>
          <div className="form-grid three">
            <label>
              Reporting agency
              <input value={reportPackageForm.agency_name} onChange={(event) => setReportPackageForm({ ...reportPackageForm, agency_name: event.target.value })} />
            </label>
            <label>
              Jurisdiction
              <input value={reportPackageForm.jurisdiction} onChange={(event) => setReportPackageForm({ ...reportPackageForm, jurisdiction: event.target.value })} />
            </label>
            <label>
              Report due
              <input type="date" value={reportPackageForm.due_at} onChange={(event) => setReportPackageForm({ ...reportPackageForm, due_at: event.target.value })} />
            </label>
            <label>
              External ref
              <input value={reportPackageForm.external_reference} onChange={(event) => setReportPackageForm({ ...reportPackageForm, external_reference: event.target.value })} />
            </label>
            <label className="wide-field">
              Package notes
              <input value={reportPackageForm.notes} onChange={(event) => setReportPackageForm({ ...reportPackageForm, notes: event.target.value })} />
            </label>
          </div>
          <div className="form-grid three">
            <label>
              Insurer
              <input value={insuranceClaimForm.provider_name} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, provider_name: event.target.value })} />
            </label>
            <label>
              Policy
              <input value={insuranceClaimForm.policy_number} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, policy_number: event.target.value })} />
            </label>
            <label>
              Claim type
              <select value={insuranceClaimForm.claim_type} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, claim_type: event.target.value as InsuranceClaimType })}>
                <option value="injury_medical">Injury medical</option>
                <option value="liability">Liability</option>
                <option value="equipment_damage">Equipment damage</option>
                <option value="property_damage">Property damage</option>
                <option value="travel">Travel</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>
              Claimed
              <input type="number" min="0" value={insuranceClaimForm.claimed_amount} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, claimed_amount: event.target.value })} />
            </label>
            <label>
              Reserve
              <input type="number" min="0" value={insuranceClaimForm.reserve_amount} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, reserve_amount: event.target.value })} />
            </label>
            <label>
              Currency
              <input value={insuranceClaimForm.currency} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, currency: event.target.value.toUpperCase().slice(0, 3) })} />
            </label>
            <label>
              Tracking URL
              <input value={insuranceClaimForm.tracking_url} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, tracking_url: event.target.value })} />
            </label>
            <label className="wide-field">
              Claim notes
              <input value={insuranceClaimForm.notes} onChange={(event) => setInsuranceClaimForm({ ...insuranceClaimForm, notes: event.target.value })} />
            </label>
          </div>
          <div className="form-grid three">
            <label>
              Clearance type
              <input value={medicalClearanceForm.clearance_type} onChange={(event) => setMedicalClearanceForm({ ...medicalClearanceForm, clearance_type: event.target.value })} />
            </label>
            <label>
              Valid from
              <input type="date" value={medicalClearanceForm.valid_from} onChange={(event) => setMedicalClearanceForm({ ...medicalClearanceForm, valid_from: event.target.value })} />
            </label>
            <label>
              Valid until
              <input type="date" value={medicalClearanceForm.valid_until} onChange={(event) => setMedicalClearanceForm({ ...medicalClearanceForm, valid_until: event.target.value })} />
            </label>
            <label>
              RTP stage
              <input value={medicalClearanceForm.return_to_play_stage} onChange={(event) => setMedicalClearanceForm({ ...medicalClearanceForm, return_to_play_stage: event.target.value })} />
            </label>
            <label>
              Provider
              <input value={medicalClearanceForm.provider_name} onChange={(event) => setMedicalClearanceForm({ ...medicalClearanceForm, provider_name: event.target.value })} />
            </label>
            <label className="wide-field">
              Restrictions
              <input value={medicalClearanceForm.restrictions} onChange={(event) => setMedicalClearanceForm({ ...medicalClearanceForm, restrictions: event.target.value })} />
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
          <div className="task-list">
            {complianceSummary?.blockers.slice(0, 4).map((item) => (
              <article key={`blocker-${item.source}-${item.id}`} className="task-card">
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.source} · {item.status} · {item.severity}</span>
                  <span>{item.person_name ?? "Unassigned person"} · due {item.due_on ?? "not set"}</span>
                  <span>{item.reason}</span>
                </div>
              </article>
            ))}
            {complianceSummary?.renewals_due.slice(0, 4).map((item) => (
              <article key={`renewal-${item.source}-${item.id}`} className="task-card">
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.status} · renewal due {item.due_on ?? "not set"}</span>
                  <span>{item.person_name ?? "Unassigned person"} · {item.reason}</span>
                </div>
              </article>
            ))}
            {complianceSummary?.investigation_queue.slice(0, 4).map((item) => (
              <article key={`investigation-${item.source}-${item.id}`} className="task-card">
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.status} · {item.severity} · occurred {item.due_on ?? "not set"}</span>
                  <span>{item.person_name ?? "No athlete linked"} · {item.reason}</span>
                </div>
              </article>
            ))}
            {incidentReportPackages.slice(0, 4).map((reportPackage) => (
              <article key={reportPackage.id} className="task-card">
                <div>
                  <strong>{reportPackage.agency_name}</strong>
                  <span>{reportPackage.jurisdiction} · {reportPackage.status} · due {reportPackage.due_at ?? "not set"}</span>
                  <span>{reportPackage.external_reference ?? "No external reference"} · incident {reportPackage.incident_id.slice(0, 8)}</span>
                  <span>{reportPackage.notes ?? reportPackage.narrative.slice(0, 160)}</span>
                </div>
                <div className="event-toolbar">
                  <button type="button" onClick={() => updateIncidentReportPackage(reportPackage, "ready")}>Ready</button>
                  <button type="button" onClick={() => updateIncidentReportPackage(reportPackage, "submitted")}>Submit</button>
                  <button type="button" onClick={() => updateIncidentReportPackage(reportPackage, "accepted")}>Accept</button>
                  <button type="button" onClick={() => updateIncidentReportPackage(reportPackage, "rejected")}>Reject</button>
                </div>
              </article>
            ))}
            {incidentInsuranceClaims.slice(0, 4).map((claim) => (
              <article key={claim.id} className="task-card">
                <div>
                  <strong>{claim.provider_name}</strong>
                  <span>{claim.claim_type} · {claim.status} · {claim.currency} {(claim.claimed_amount_cents / 100).toFixed(2)} claimed</span>
                  <span>{claim.policy_number ?? "No policy"} · {claim.claim_number ?? "No claim number"}</span>
                  <span>{claim.paid_amount_cents ? `${claim.currency} ${(claim.paid_amount_cents / 100).toFixed(2)} paid` : claim.notes ?? "Awaiting insurer update"}</span>
                </div>
                <div className="event-toolbar">
                  <button type="button" onClick={() => updateIncidentInsuranceClaim(claim, "ready")}>Verify</button>
                  <button type="button" onClick={() => updateIncidentInsuranceClaim(claim, "submitted")}>Submit</button>
                  <button type="button" onClick={() => updateIncidentInsuranceClaim(claim, "approved")}>Approve</button>
                  <button type="button" onClick={() => updateIncidentInsuranceClaim(claim, "paid")}>Paid</button>
                  <button type="button" onClick={() => updateIncidentInsuranceClaim(claim, "denied")}>Deny</button>
                </div>
              </article>
            ))}
            {incidentMedicalClearances.slice(0, 4).map((clearance) => (
              <article key={clearance.id} className="task-card">
                <div>
                  <strong>{clearance.clearance_type}</strong>
                  <span>{clearance.status} · {clearance.return_to_play_stage ?? "stage pending"} · valid {clearance.valid_until ?? "not set"}</span>
                  <span>{clearance.provider_name ?? "Provider pending"} · athlete {clearance.athlete_person_id.slice(0, 8)}</span>
                  <span>{clearance.restrictions ?? clearance.notes ?? "No restrictions recorded"}</span>
                </div>
                <div className="event-toolbar">
                  <button type="button" onClick={() => updateIncidentMedicalClearance(clearance, "restricted")}>Restrict</button>
                  <button type="button" onClick={() => updateIncidentMedicalClearance(clearance, "cleared")}>Clear</button>
                  <button type="button" onClick={() => updateIncidentMedicalClearance(clearance, "not_cleared")}>Hold</button>
                  <button type="button" onClick={() => updateIncidentMedicalClearance(clearance, "expired")}>Expire</button>
                </div>
              </article>
            ))}
            {backgroundChecks.slice(0, 4).map((check) => (
              <article key={check.id} className="task-card">
                <div>
                  <strong>{check.check_type}</strong>
                  <span>{check.provider} · {check.status} · risk {check.risk_level}</span>
                  <span>Expires {check.expires_at ?? "not set"} · {check.external_reference ?? "no reference"}</span>
                  {check.result_summary ? <span>{check.result_summary}</span> : null}
                </div>
                <div className="event-toolbar">
                  <button type="button" onClick={() => updateBackgroundCheck(check, "in_progress")}>Start</button>
                  <button type="button" onClick={() => updateBackgroundCheck(check, "clear")}>Clear</button>
                  <button type="button" onClick={() => updateBackgroundCheck(check, "review_required")}>Review</button>
                </div>
              </article>
            ))}
            {complianceCredentials.slice(0, 4).map((credential) => (
              <article key={credential.id} className="task-card">
                <div>
                  <strong>{credential.title}</strong>
                  <span>{credential.credential_type} · {credential.status} · {credential.issuing_body ?? "issuer pending"}</span>
                  <span>Renew {credential.renewal_due_at ?? "not set"} · expires {credential.expires_at ?? "not set"}</span>
                  {credential.notes ? <span>{credential.notes}</span> : null}
                </div>
                <div className="event-toolbar">
                  <button type="button" onClick={() => updateComplianceCredential(credential, "verified")}>Verify</button>
                  <button type="button" onClick={() => updateComplianceCredential(credential, "expiring_soon")}>Expiring</button>
                  <button type="button" onClick={() => updateComplianceCredential(credential, "expired")}>Expire</button>
                </div>
              </article>
            ))}
            {safeguardingIncidents.slice(0, 5).map((incident) => (
              <article key={incident.id} className="task-card">
                <div>
                  <strong>{incident.title}</strong>
                  <span>{incident.incident_type} · {incident.severity} · {incident.status} · {new Date(incident.occurred_at).toLocaleString()}</span>
                  <span>{incident.description}</span>
                  {incident.immediate_action ? <span>{incident.immediate_action}</span> : null}
                </div>
                <div className="event-toolbar">
                  <button type="button" onClick={() => updateSafeguardingIncident(incident, "triaged")}>Triage</button>
                  <button type="button" onClick={() => updateSafeguardingIncident(incident, "investigating")}>Investigate</button>
                  <button type="button" onClick={() => createIncidentReportPackage(incident)}>Package</button>
                  <button type="button" onClick={() => createIncidentInsuranceClaim(incident)}>Claim</button>
                  <button type="button" onClick={() => createIncidentMedicalClearance(incident)}>Clearance</button>
                  <button type="button" onClick={() => updateSafeguardingIncident(incident, "resolved")}>Resolve</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
