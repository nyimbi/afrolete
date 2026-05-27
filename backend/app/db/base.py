from app.models.base import Base

# Import all models so Alembic can discover metadata.
from app.models.agent import Agent, AgentAssignment, AgentTask  # noqa: F401,E402
from app.models.event import AttendanceRecord, Event  # noqa: F401,E402
from app.models.identity import AppUser, Person  # noqa: F401,E402
from app.models.organization import Membership, Organization  # noqa: F401,E402
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry  # noqa: F401,E402

__all__ = ["Base"]
