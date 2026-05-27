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
