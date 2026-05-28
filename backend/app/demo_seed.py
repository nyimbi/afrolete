from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.agent import Agent, AgentTask
from app.models.communication import CommunicationMessage, MessageRecipient, NotificationPreference
from app.models.commercial import FinanceInvoice, Sponsor, SponsorshipAgreement
from app.models.enums import (
    AgentKind,
    ChannelPreference,
    CommercialStatus,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    EventType,
    GuardianRelationshipKind,
    MemberSubjectType,
    MembershipRole,
    MetricCategory,
    MetricSource,
    MetricVerificationStatus,
    NotificationFrequency,
    OrganizationType,
    RosterStatus,
    SportFormat,
    TeamRole,
    TravelPlanStatus,
)
from app.models.event import ConsentRequest, Event, EventTravelPlan
from app.models.identity import AppUser, Person
from app.models.organization import Membership, Organization
from app.models.performance import AthletePerformanceObservation, PerformanceMetricDefinition
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry


DEMO_SUB = "kc-owner-1"
DEMO_EMAIL = "owner@example.com"
DEMO_ORG_SLUG = "demo-city-fc"


async def main() -> None:
    async with SessionLocal() as db:
        existing = await db.scalar(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
        if existing is not None:
            print(f"AfroLete demo seed already present: {existing.name}")
            return

        owner = Person(
            display_name="Owner Example",
            given_name="Owner",
            family_name="Example",
            primary_email=DEMO_EMAIL,
            primary_phone="+15550101000",
            country_code="US",
        )
        coach = Person(
            display_name="Maya Coach",
            given_name="Maya",
            family_name="Coach",
            primary_email="coach@example.com",
            primary_phone="+15550101001",
            country_code="US",
        )
        athlete = Person(
            display_name="Amina Forward",
            given_name="Amina",
            family_name="Forward",
            primary_email="amina@example.com",
            date_of_birth=date(2012, 5, 14),
            country_code="US",
        )
        guardian = Person(
            display_name="Nia Guardian",
            given_name="Nia",
            family_name="Guardian",
            primary_email="guardian@example.com",
            primary_phone="+15550101002",
            country_code="US",
        )
        db.add_all([owner, coach, athlete, guardian])
        await db.flush()

        db.add(
            AppUser(
                keycloak_sub=DEMO_SUB,
                person_id=owner.id,
                email=DEMO_EMAIL,
                display_name="Owner Example",
            )
        )
        organization = Organization(
            name="Demo City FC",
            slug=DEMO_ORG_SLUG,
            organization_type=OrganizationType.CLUB,
            country_code="US",
            primary_sport="football",
            mission="A demo tenant showing operations, safeguarding, performance, and AI workflows.",
            public_name="Demo City FC",
            contact_email="hello@demo-city-fc.test",
            contact_phone="+15550101010",
            website_url="https://demo-city-fc.test",
            subdomain="demo-city-fc",
            logo_url="https://placehold.co/256x256?text=DCF",
            brand_primary_color="#0f766e",
            brand_secondary_color="#f59e0b",
        )
        db.add(organization)
        await db.flush()

        db.add_all(
            [
                Membership(
                    organization_id=organization.id,
                    subject_type=MemberSubjectType.PERSON,
                    subject_id=owner.id,
                    role=MembershipRole.OWNER,
                    title="Owner",
                ),
                Membership(
                    organization_id=organization.id,
                    subject_type=MemberSubjectType.PERSON,
                    subject_id=coach.id,
                    role=MembershipRole.COACH,
                    title="Head Coach",
                ),
            ]
        )

        team = Team(
            organization_id=organization.id,
            name="Demo City U15",
            sport="football",
            sport_format=SportFormat.TEAM,
            age_group="U15",
            gender_category="girls",
            season_label="2026 Spring",
        )
        profile = AthleteProfile(
            organization_id=organization.id,
            person_id=athlete.id,
            athlete_code="DCF-015",
            dominant_side="right",
            development_notes="Explosive forward with strong acceleration and leadership potential.",
        )
        db.add_all([team, profile])
        await db.flush()
        db.add_all(
            [
                TeamRosterEntry(
                    team_id=team.id,
                    athlete_profile_id=profile.id,
                    role=TeamRole.CAPTAIN,
                    jersey_number="9",
                    primary_position="Forward",
                    is_captain=True,
                    status=RosterStatus.ACTIVE,
                ),
                GuardianRelationship(
                    athlete_person_id=athlete.id,
                    guardian_person_id=guardian.id,
                    relationship_kind=GuardianRelationshipKind.PARENT,
                    relationship="Parent",
                    can_sign_consent=True,
                    can_view_medical=True,
                    emergency_contact=True,
                    is_primary=True,
                ),
            ]
        )

        starts_at = datetime.now(UTC) + timedelta(days=7)
        event = Event(
            organization_id=organization.id,
            team_id=team.id,
            event_type=EventType.TOURNAMENT,
            title="Regional Futures Showcase",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=6),
            timezone="America/New_York",
            venue_name="Riverside Sports Park",
            notes="Demo event with travel, consent, and performance workflows.",
        )
        db.add(event)
        await db.flush()
        plan = EventTravelPlan(
            organization_id=organization.id,
            event_id=event.id,
            status=TravelPlanStatus.READY,
            destination="Riverside Sports Park",
            travel_mode="coach bus",
            departure_at=starts_at - timedelta(hours=3),
            return_at=starts_at + timedelta(hours=9),
            route_summary="Clubhouse to Riverside via I-95.",
            emergency_contacts="Ops desk +15550101010; venue security +15550101999.",
            medical_access_plan="Nearest urgent care is Riverside Clinic, 1.2 miles from venue.",
            consent_required=True,
            consent_due_at=datetime.now(UTC) + timedelta(days=2),
            cost_per_participant=25,
            risk_assessment="Medium-risk youth travel with guardian consent and staff supervision required.",
        )
        token_hash = hashlib.sha256(f"demo-consent:{event.id}:{guardian.id}".encode()).hexdigest()
        consent = ConsentRequest(
            organization_id=organization.id,
            athlete_person_id=athlete.id,
            guardian_person_id=guardian.id,
            scope_type=ConsentScopeType.EVENT,
            scope_id=event.id,
            channel=ConsentCaptureChannel.EMAIL,
            destination=guardian.primary_email or "guardian@example.com",
            token_hash=token_hash,
            status=ConsentRequestStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=5),
            sent_at=datetime.now(UTC) - timedelta(hours=2),
            notes="Demo travel consent request.",
        )
        db.add_all([plan, consent])

        sponsor = Sponsor(
            organization_id=organization.id,
            name="Demo Bank Public",
            industry="Financial services",
            contact_name="Sponsor Example",
            contact_email="sponsor@example.com",
            website_url="https://demo-bank.example",
            brand_assets_url="https://placehold.co/512x256?text=Demo+Bank",
            notes="Seed sponsor for the public support showcase and sponsor portal.",
        )
        db.add(sponsor)
        await db.flush()
        db.add_all(
            [
                SponsorshipAgreement(
                    organization_id=organization.id,
                    sponsor_id=sponsor.id,
                    event_id=event.id,
                    name="Regional Showcase Partner",
                    tier="Gold",
                    value_amount=Decimal("3000.00"),
                    currency="USD",
                    deliverables="Shirt logo, match board, community clinic",
                    activation_notes="Public support campaign and family ticket bundle are live.",
                    roi_notes="Track public-site visits, ticket conversions, and clinic attendance.",
                ),
                FinanceInvoice(
                    organization_id=organization.id,
                    sponsor_id=sponsor.id,
                    invoice_number="SPONSOR-DEMO-1",
                    title="Regional Showcase Partner",
                    amount_due=Decimal("1500.00"),
                    amount_paid=Decimal("500.00"),
                    currency="USD",
                    due_on=date.today() + timedelta(days=14),
                    status=CommercialStatus.PARTIAL,
                    memo="Demo invoice visible in the sponsor portal.",
                ),
            ]
        )

        sprint = PerformanceMetricDefinition(
            organization_id=organization.id,
            sport="football",
            code="sprint_20m",
            name="20m Sprint",
            category=MetricCategory.PHYSICAL,
            unit="seconds",
            higher_is_better=False,
            description="Acceleration benchmark used in the demo performance dashboard.",
        )
        readiness = PerformanceMetricDefinition(
            organization_id=organization.id,
            sport="football",
            code="readiness_score",
            name="Readiness Score",
            category=MetricCategory.WELLNESS,
            unit="score",
            higher_is_better=True,
            description="Coach-entered readiness score for demo forecasting and safety cards.",
        )
        db.add_all([sprint, readiness])
        await db.flush()
        for index, value in enumerate([3.62, 3.55, 3.51, 3.47], start=1):
            db.add(
                AthletePerformanceObservation(
                    organization_id=organization.id,
                    athlete_profile_id=profile.id,
                    metric_definition_id=sprint.id,
                    value=value,
                    observed_at=(datetime.now(UTC) - timedelta(days=35 - index * 7)).replace(
                        tzinfo=None
                    ),
                    source=MetricSource.COACH_EVALUATION,
                    confidence=0.9,
                    verification_status=MetricVerificationStatus.VERIFIED,
                    notes="Demo sprint benchmark.",
                )
            )
        for index, value in enumerate([72, 76, 81, 79], start=1):
            db.add(
                AthletePerformanceObservation(
                    organization_id=organization.id,
                    athlete_profile_id=profile.id,
                    metric_definition_id=readiness.id,
                    value=value,
                    observed_at=(datetime.now(UTC) - timedelta(days=28 - index * 7)).replace(
                        tzinfo=None
                    ),
                    source=MetricSource.COACH_EVALUATION,
                    confidence=0.85,
                    verification_status=MetricVerificationStatus.VERIFIED,
                    notes="Demo readiness check.",
                )
            )

        agent = Agent(
            organization_id=organization.id,
            name="Demo Operations Agent",
            kind=AgentKind.OPERATIONS,
            purpose="Summarize overdue actions, consent gaps, and performance signals for the demo tenant.",
            model_policy="afrolete-demo-local-agent",
        )
        db.add(agent)
        await db.flush()
        db.add(
            AgentTask(
                agent_id=agent.id,
                organization_id=organization.id,
                task_type="demo_readiness_review",
                title="Review demo tenant readiness",
                requested_by_person_id=owner.id,
                input_ref=f"organization:{organization.id}",
                review_notes="Seeded task for showing AI agents as first-class operators.",
            )
        )

        db.add(
            NotificationPreference(
                organization_id=organization.id,
                person_id=owner.id,
                frequency=NotificationFrequency.DAILY_DIGEST,
                channel_preference=ChannelPreference.APP,
            )
        )
        message = CommunicationMessage(
            organization_id=organization.id,
            template_id=None,
            created_by_person_id=coach.id,
            message_type=CommunicationMessageType.ANNOUNCEMENT,
            channel=CommunicationChannel.IN_APP,
            scope_type=CommunicationScopeType.ORGANIZATION,
            scope_id=organization.id,
            subject="Demo kickoff: review travel consent and performance signals",
            body="Use this seeded message to demo inbox, digest, and due-worker behavior.",
            sent_at=datetime.now(UTC) - timedelta(hours=1),
            status="sent",
        )
        db.add(message)
        await db.flush()
        db.add(
            MessageRecipient(
                message_id=message.id,
                person_id=owner.id,
                destination=str(owner.id),
            )
        )

        await db.commit()
        print("Seeded AfroLete demo tenant: Demo City FC")


if __name__ == "__main__":
    asyncio.run(main())
