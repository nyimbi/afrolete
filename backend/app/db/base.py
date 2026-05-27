from app.models.base import Base

# Import all models so Alembic can discover metadata.
from app.models.agent import Agent, AgentAssignment, AgentTask  # noqa: F401,E402
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
from app.models.event import ActivityConsent, AttendanceRecord, ConsentRequest, Event  # noqa: F401,E402
from app.models.identity import AppUser, Person  # noqa: F401,E402
from app.models.organization import Committee, CommitteeMembership, Membership, Organization  # noqa: F401,E402
from app.models.performance import (  # noqa: F401,E402
    AthleteAssessment,
    AthletePerformanceObservation,
    PerformanceMetricDefinition,
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
    TrainingSessionPlan,
)

__all__ = ["Base"]
