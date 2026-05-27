from enum import StrEnum


class OrganizationType(StrEnum):
    CLUB = "club"
    SCHOOL = "school"
    ACADEMY = "academy"
    ASSOCIATION = "association"
    FEDERATION = "federation"
    EVENT_OPERATOR = "event_operator"


class MembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    COACH = "coach"
    STAFF = "staff"
    ATHLETE = "athlete"
    GUARDIAN = "guardian"
    VIEWER = "viewer"
    AGENT = "agent"


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

