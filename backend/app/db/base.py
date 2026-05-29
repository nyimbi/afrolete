from app.models.base import Base

# Import all models so Alembic can discover metadata.
from app.models.agent import (  # noqa: F401,E402
    Agent,
    AgentAssignment,
    AgentGovernancePolicyHistorySnapshot,
    AgentGovernancePolicyRule,
    AgentScorecardArtifactAccess,
    AgentBiasAudit,
    AgentDecisionAppeal,
    AgentModelRegistry,
    AgentRunRecord,
    AgentScorecardComment,
    AgentScorecardPublication,
    AgentTask,
)
from app.models.assets import (  # noqa: F401,E402
    EmergencyActionPlan,
    EmergencyPlanActivation,
    EquipmentCheckout,
    EquipmentFile,
    EquipmentItem,
    EquipmentLeaseInstallment,
    EquipmentLeaseSchedule,
    EquipmentReader,
    EquipmentScanEvent,
    Facility,
    FacilityBooking,
    MaintenanceWorkOrder,
    SupplierOrder,
)
from app.models.billing import (  # noqa: F401,E402
    BillingEntitlement,
    BillingPlan,
    SaaSInvoice,
    SaaSPayment,
    TenantSubscription,
    UsageMeter,
    UsageRecord,
)
from app.models.commercial import (  # noqa: F401,E402
    Donation,
    FinanceInvoice,
    FinancePayment,
    FundraisingCampaign,
    Sponsor,
    SponsorshipAgreement,
    Ticket,
    TicketOrder,
    TicketProduct,
)
from app.models.developer import (  # noqa: F401,E402
    DeveloperApiKey,
    DeveloperApplication,
    DeveloperMarketplaceListing,
    DeveloperOAuthAuthorization,
    DeveloperWebhookDelivery,
    DeveloperWebhookSubscription,
)
from app.models.communication import (  # noqa: F401,E402
    CommunicationMessage,
    CommunicationTemplate,
    MessageRecipient,
    NotificationPreference,
)
from app.models.competition import (  # noqa: F401,E402
    Competition,
    CompetitionFixture,
    CompetitionParticipant,
    FixtureMatchEvent,
    FixtureOfficialAssignment,
)
from app.models.event import (  # noqa: F401,E402
    ActivityConsent,
    EventAttendancePolicy,
    AttendanceRecord,
    BackgroundCheck,
    BackgroundCheckEvidenceDocument,
    ComplianceCredential,
    ConsentRequest,
    Event,
    EventTravelApproval,
    EventTravelCarpoolRide,
    EventTravelChecklistItem,
    EventTravelDevice,
    EventTravelDeviceIngestEvent,
    EventTravelExpense,
    EventTravelGeofenceZone,
    EventTravelLocationUpdate,
    EventTravelPlan,
    EventWeatherAssessment,
    IncidentInsuranceClaim,
    IncidentMedicalClearance,
    IncidentReportPackage,
    SafeguardingEvidencePolicyRule,
    SafeguardingIncident,
    SafeguardingIncidentAccessGrant,
)
from app.models.identity import AppUser, Person  # noqa: F401,E402
from app.models.organization import (  # noqa: F401,E402
    Committee,
    CommitteeMembership,
    Membership,
    Organization,
    RegistrationInquiry,
)
from app.models.performance import (  # noqa: F401,E402
    AthleteAssessment,
    AthletePerformanceObservation,
    PerformanceAchievementAward,
    PerformanceGoal,
    PerformanceMetricDefinition,
    PerformanceForecastValidationRun,
    PerformanceMovementReferenceProfile,
    PerformanceModelExtractionBenchmarkCase,
    PerformanceModelExtractionBenchmarkDataset,
    PerformanceVideoAnnotation,
    PerformanceVideoAsset,
    PerformanceVideoPoseSample,
    PerformanceWearableIngestEvent,
    PerformanceWearableProviderConnection,
    PerformanceWearableProviderSyncRun,
)
from app.models.reporting import (  # noqa: F401,E402
    GeneratedReport,
    IntelligenceInsight,
    PredictiveRiskScore,
    ReportDefinition,
    ReportExportJob,
    ScheduledReport,
)
from app.models.team import (  # noqa: F401,E402
    AthleteProfile,
    GuardianRelationship,
    Team,
    TeamCommittee,
    TeamCommitteeMembership,
    TeamRosterEntry,
)
from app.models.training import (  # noqa: F401,E402
    TrainingDrill,
    TrainingPlan,
    TrainingPlanItem,
    TrainingSessionFeedback,
    TrainingSessionPlan,
)

__all__ = ["Base"]
