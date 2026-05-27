from enum import StrEnum


class OrganizationType(StrEnum):
    CLUB = "club"
    SCHOOL = "school"
    ACADEMY = "academy"
    ASSOCIATION = "association"
    FEDERATION = "federation"
    EVENT_OPERATOR = "event_operator"


class AssociationLevel(StrEnum):
    NATIONAL = "national"
    REGIONAL = "regional"
    LOCAL = "local"
    SPECIAL = "special"


class MembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    COACH = "coach"
    STAFF = "staff"
    ATHLETE = "athlete"
    GUARDIAN = "guardian"
    VIEWER = "viewer"
    AGENT = "agent"


class CommitteeRole(StrEnum):
    CHAIR = "chair"
    VICE_CHAIR = "vice_chair"
    SECRETARY = "secretary"
    TREASURER = "treasurer"
    MEMBER = "member"
    ADVISOR = "advisor"
    EX_OFFICIO = "ex_officio"


class TeamRole(StrEnum):
    PLAYER = "player"
    CAPTAIN = "captain"
    VICE_CAPTAIN = "vice_captain"
    COACH = "coach"
    ASSISTANT_COACH = "assistant_coach"
    MANAGER = "manager"
    MEDIC = "medic"
    ANALYST = "analyst"
    SUBSTITUTE = "substitute"
    RESERVE = "reserve"
    BENCH = "bench"
    INDIVIDUAL_ATHLETE = "individual_athlete"


class SportFormat(StrEnum):
    TEAM = "team"
    INDIVIDUAL = "individual"
    MIXED = "mixed"


class RosterStatus(StrEnum):
    ACTIVE = "active"
    STARTER = "starter"
    BENCH = "bench"
    SUBSTITUTE = "substitute"
    RESERVE = "reserve"
    INJURED = "injured"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class GuardianRelationshipKind(StrEnum):
    PARENT = "parent"
    LEGAL_GUARDIAN = "legal_guardian"
    FOSTER_GUARDIAN = "foster_guardian"
    CAREGIVER = "caregiver"
    EMERGENCY_CONTACT = "emergency_contact"


class ConsentScopeType(StrEnum):
    ORGANIZATION = "organization"
    TEAM = "team"
    EVENT = "event"


class ConsentStatus(StrEnum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentCaptureChannel(StrEnum):
    WEB_LINK = "web_link"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    EMAIL = "email"
    MANUAL = "manual"


class ConsentRequestStatus(StrEnum):
    PENDING = "pending"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ParticipationClearanceStatus(StrEnum):
    CLEARED = "cleared"
    MINOR_REQUIRES_CONSENT = "minor_requires_consent"
    CONSENT_DENIED = "consent_denied"
    CONSENT_EXPIRED = "consent_expired"
    NO_GUARDIAN = "no_guardian"
    MEDICAL_CLEARANCE_REQUIRED = "medical_clearance_required"
    MEDICAL_NOT_CLEARED = "medical_not_cleared"
    MEDICAL_CLEARANCE_EXPIRED = "medical_clearance_expired"


class MemberSubjectType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    TEAM = "team"


class EventType(StrEnum):
    TRAINING = "training"
    MATCH = "match"
    MEETING = "meeting"
    TOURNAMENT = "tournament"
    ASSESSMENT = "assessment"
    COMMUNITY = "community"


class WeatherAlertLevel(StrEnum):
    INFORMATION = "information"
    ADVISORY = "advisory"
    WARNING = "warning"
    CRITICAL = "critical"


class WeatherDecision(StrEnum):
    PROCEED = "proceed"
    MONITOR = "monitor"
    MODIFY = "modify"
    DELAY = "delay"
    CANCEL = "cancel"
    EVACUATE = "evacuate"


class TravelPlanStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TravelRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttendanceStatus(StrEnum):
    INVITED = "invited"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class AgentKind(StrEnum):
    COACHING = "coaching"
    OPERATIONS = "operations"
    SAFEGUARDING = "safeguarding"
    ANALYTICS = "analytics"
    COMMUNICATIONS = "communications"
    SCOUTING = "scouting"


class AgentTaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_REVIEW = "waiting_for_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SafeguardingIncidentType(StrEnum):
    INJURY = "injury"
    MEDICAL = "medical"
    SAFEGUARDING = "safeguarding"
    MISCONDUCT = "misconduct"
    FACILITY = "facility"
    TRANSPORT = "transport"
    WEATHER = "weather"
    OTHER = "other"


class SafeguardingIncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafeguardingIncidentStatus(StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentReportPackageStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class InsuranceClaimType(StrEnum):
    INJURY_MEDICAL = "injury_medical"
    LIABILITY = "liability"
    EQUIPMENT_DAMAGE = "equipment_damage"
    PROPERTY_DAMAGE = "property_damage"
    TRAVEL = "travel"
    OTHER = "other"


class InsuranceClaimStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    DENIED = "denied"
    CLOSED = "closed"


class MedicalClearanceStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    RESTRICTED = "restricted"
    CLEARED = "cleared"
    NOT_CLEARED = "not_cleared"
    EXPIRED = "expired"


class BackgroundCheckStatus(StrEnum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    CLEAR = "clear"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"
    EXPIRED = "expired"


class ComplianceCredentialType(StrEnum):
    SAFEGUARDING_TRAINING = "safeguarding_training"
    FIRST_AID = "first_aid"
    COACHING_LICENSE = "coaching_license"
    OFFICIATING_LICENSE = "officiating_license"
    DRIVER_CERTIFICATION = "driver_certification"
    BACKGROUND_CHECK = "background_check"
    MEDICAL_LICENSE = "medical_license"
    OTHER = "other"


class ComplianceCredentialStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    REVOKED = "revoked"


class MetricCategory(StrEnum):
    PHYSICAL = "physical"
    TECHNICAL = "technical"
    TACTICAL = "tactical"
    MENTAL = "mental"
    WELLNESS = "wellness"
    COMPETITION = "competition"


class MetricSource(StrEnum):
    MANUAL = "manual"
    COACH_EVALUATION = "coach_evaluation"
    SELF_ASSESSMENT = "self_assessment"
    OFFICIAL_STATS = "official_stats"
    VIDEO_ANALYSIS = "video_analysis"
    AUDIO_NARRATION = "audio_narration"
    WEARABLE = "wearable"
    AGENT_EXTRACTED = "agent_extracted"


class MetricVerificationStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class TrainingPlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TrainingSessionStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CompetitionType(StrEnum):
    LEAGUE = "league"
    TOURNAMENT = "tournament"
    CUP = "cup"
    FRIENDLY_SERIES = "friendly_series"


class CompetitionFormat(StrEnum):
    ROUND_ROBIN = "round_robin"
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    GROUP_KNOCKOUT = "group_knockout"
    SWISS = "swiss"
    FRIENDLY = "friendly"


class CompetitionStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FixtureStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINAL = "final"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class OfficialRole(StrEnum):
    REFEREE = "referee"
    ASSISTANT_REFEREE = "assistant_referee"
    FOURTH_OFFICIAL = "fourth_official"
    SCORER = "scorer"
    TIMEKEEPER = "timekeeper"
    MATCH_COMMISSIONER = "match_commissioner"


class OfficialAssignmentStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CONFIRMED = "confirmed"


class MatchEventType(StrEnum):
    GOAL = "goal"
    OWN_GOAL = "own_goal"
    ASSIST = "assist"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    INJURY = "injury"
    NOTE = "note"


class CommunicationMessageType(StrEnum):
    ANNOUNCEMENT = "announcement"
    ALERT = "alert"
    REMINDER = "reminder"
    REQUEST = "request"
    REPORT = "report"


class CommunicationChannel(StrEnum):
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


class CommunicationScopeType(StrEnum):
    ORGANIZATION = "organization"
    TEAM = "team"
    EVENT = "event"
    PERSON = "person"


class MessageDeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class NotificationFrequency(StrEnum):
    IMMEDIATE = "immediate"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"


class ChannelPreference(StrEnum):
    APP = "app"
    EMAIL = "email"
    SMS = "sms"
    ALL = "all"


class FacilityType(StrEnum):
    FIELD = "field"
    COURT = "court"
    STADIUM = "stadium"
    GYM = "gym"
    POOL = "pool"
    CLUBHOUSE = "clubhouse"
    STORAGE = "storage"
    OTHER = "other"


class FacilityStatus(StrEnum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"
    RETIRED = "retired"


class AssetCondition(StrEnum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNUSABLE = "unusable"


class EquipmentStatus(StrEnum):
    AVAILABLE = "available"
    CHECKED_OUT = "checked_out"
    MAINTENANCE = "maintenance"
    LOST = "lost"
    RETIRED = "retired"


class CheckoutStatus(StrEnum):
    CHECKED_OUT = "checked_out"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"
    DAMAGED = "damaged"


class WorkOrderPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkOrderStatus(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FacilityBookingStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmergencyActionPlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    RETIRED = "retired"


class EmergencyActivationStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    REVIEWED = "reviewed"


class EmergencyType(StrEnum):
    MEDICAL = "medical"
    FIRE = "fire"
    WEATHER = "weather"
    SECURITY = "security"
    EVACUATION = "evacuation"
    MISSING_PERSON = "missing_person"
    OTHER = "other"


class CommercialStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PLEDGED = "pledged"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TicketStatus(StrEnum):
    ISSUED = "issued"
    CHECKED_IN = "checked_in"
    VOID = "void"
    REFUNDED = "refunded"


class ReportCategory(StrEnum):
    PERFORMANCE = "performance"
    ADMINISTRATIVE = "administrative"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    INTELLIGENCE = "intelligence"


class ReportFormat(StrEnum):
    ONLINE = "online"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    API = "api"


class ReportFrequency(StrEnum):
    ON_DEMAND = "on_demand"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ON_TRIGGER = "on_trigger"


class ReportRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


class InsightSeverity(StrEnum):
    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


class InsightStatus(StrEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class BillingInvoiceStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    PARTIAL = "partial"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class UsageUnit(StrEnum):
    ATHLETE = "athlete"
    TEAM = "team"
    AGENT_TASK = "agent_task"
    REPORT = "report"
    STORAGE_GB = "storage_gb"
    MESSAGE = "message"
