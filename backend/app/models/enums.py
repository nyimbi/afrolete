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
