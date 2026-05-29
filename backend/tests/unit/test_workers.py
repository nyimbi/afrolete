from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.models.agent import Agent, AgentRunRecord, AgentTask
from app.models.assets import EmergencyActionPlan, EmergencyPlanActivation
from app.models.billing import BillingPlan, SaaSInvoice, TenantSubscription
from app.models.communication import CommunicationMessage, MessageRecipient, NotificationPreference
from app.models.enums import (
    AgentKind,
    AgentTaskStatus,
    BackgroundCheckStatus,
    BillingCycle,
    BillingInvoiceStatus,
    ChannelPreference,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    ComplianceCredentialStatus,
    ComplianceCredentialType,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    EmergencyActionPlanStatus,
    EmergencyActivationStatus,
    EmergencyType,
    EventType,
    GuardianRelationshipKind,
    MemberSubjectType,
    MessageDeliveryStatus,
    MembershipRole,
    MetricCategory,
    MetricSource,
    NotificationFrequency,
    OrganizationType,
    SubscriptionStatus,
    TravelPlanStatus,
)
from app.models.event import BackgroundCheck, ComplianceCredential, ConsentRequest, Event, EventTravelPlan
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.performance import (
    AthletePerformanceObservation,
    PerformanceForecastValidationRun,
    PerformanceMetricDefinition,
    PerformanceWearableProviderConnection,
    PerformanceWearableProviderSyncRun,
)
from app.models.team import AthleteProfile, GuardianRelationship
from app.services import performance as performance_service
from app.workers.due import run_due_workers, selected_lanes


async def test_due_worker_runs_agent_lane_and_empty_webhooks(db_session) -> None:
    organization = Organization(
        name="Unified Worker Club",
        slug="unified-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    agent = Agent(
        organization_id=organization.id,
        name="Unified Worker Agent",
        kind=AgentKind.OPERATIONS,
        purpose="Run queued tasks from the unified due-worker command.",
        model_policy="unified-worker-local-model",
    )
    db_session.add(agent)
    await db_session.flush()
    task = AgentTask(
        agent_id=agent.id,
        organization_id=organization.id,
        task_type="operations_review",
        title="Review unified worker scheduling",
        input_ref="organization:worker",
    )
    db_session.add(task)
    await db_session.commit()

    result = await run_due_workers(db_session, organization_id=organization.id, lanes=("all",), limit=10)

    assert result["lanes"] == [
        "agent-tasks",
        "billing-dunning",
        "billing-late-fees",
        "billing-recurring-invoices",
        "communication-digests",
        "communication-escalations",
        "communication-scheduled-dispatch",
        "compliance-reconciliation",
        "developer-webhooks",
        "emergency-escalations",
        "event-travel-consent-reminders",
        "family-portal-invite-reminders",
        "performance-achievements",
        "performance-forecast-validations",
        "performance-injury-risk-alerts",
        "performance-review-escalations",
        "wearable-pull-retries",
    ]
    assert result["summary"]["eligible_count"] == 2
    assert result["summary"]["processed_count"] == 2
    assert result["results"]["billing_dunning"]["eligible_count"] == 0
    assert result["results"]["billing_late_fees"]["eligible_count"] == 0
    assert result["results"]["billing_recurring_invoices"]["eligible_count"] == 0
    assert result["results"]["communication_digests"]["eligible_count"] == 0
    assert result["results"]["communication_escalations"]["eligible_count"] == 0
    assert result["results"]["communication_scheduled_dispatch"]["eligible_count"] == 0
    assert result["results"]["compliance_reconciliation"]["eligible_count"] == 1
    assert result["results"]["compliance_reconciliation"]["executed_count"] == 1
    assert result["results"]["developer_webhooks"]["eligible_count"] == 0
    assert result["results"]["emergency_escalations"]["eligible_count"] == 0
    assert result["results"]["event_travel_consent_reminders"]["eligible_count"] == 0
    assert result["results"]["family_portal_invite_reminders"]["eligible_count"] == 0
    assert result["results"]["performance_achievements"]["eligible_count"] == 0
    assert result["results"]["performance_forecast_validations"]["eligible_count"] == 0
    assert result["results"]["performance_injury_risk_alerts"]["eligible_count"] == 0
    assert result["results"]["performance_review_escalations"]["eligible_count"] == 0
    assert result["results"]["wearable_pull_retries"]["eligible_count"] == 0
    await db_session.refresh(task)
    assert task.status == AgentTaskStatus.WAITING_FOR_REVIEW
    record_count = await db_session.scalar(
        select(func.count(AgentRunRecord.id)).where(AgentRunRecord.task_id == task.id)
    )
    assert record_count == 2


def test_selected_lanes_expands_all() -> None:
    assert selected_lanes(("all",)) == {
        "agent-tasks",
        "billing-dunning",
        "billing-late-fees",
        "billing-recurring-invoices",
        "communication-digests",
        "communication-escalations",
        "communication-scheduled-dispatch",
        "compliance-reconciliation",
        "developer-webhooks",
        "emergency-escalations",
        "event-travel-consent-reminders",
        "family-portal-invite-reminders",
        "performance-achievements",
        "performance-forecast-validations",
        "performance-injury-risk-alerts",
        "performance-review-escalations",
        "wearable-pull-retries",
    }
    assert selected_lanes(("agent-tasks",)) == {"agent-tasks"}


async def test_due_worker_sends_dunning_for_overdue_saas_invoice(db_session) -> None:
    organization = Organization(
        name="Dunning Worker Club",
        slug="dunning-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    plan = BillingPlan(
        code="dunning-growth",
        name="Dunning Growth",
        base_price=300,
        currency="USD",
        billing_cycle=BillingCycle.MONTHLY,
        included_athletes=100,
        included_teams=8,
        included_agent_tasks=500,
        included_storage_gb=50,
        per_athlete_price=0,
        per_agent_task_price=0,
    )
    db_session.add(plan)
    await db_session.flush()
    subscription = TenantSubscription(
        organization_id=organization.id,
        billing_plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
        billing_cycle=BillingCycle.MONTHLY,
        current_period_start=date(2026, 6, 1),
        current_period_end=date(2026, 6, 30),
        next_billing_on=date(2026, 6, 30),
        seats_purchased=100,
        negotiated_price=250,
    )
    db_session.add(subscription)
    await db_session.flush()
    invoice = SaaSInvoice(
        organization_id=organization.id,
        subscription_id=subscription.id,
        invoice_number="DUN-WORKER-1",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        subtotal=250,
        tax_amount=0,
        discount_amount=0,
        total=250,
        amount_paid=0,
        currency="USD",
        due_on=date(2026, 6, 1),
        status=BillingInvoiceStatus.OPEN,
        line_items="Monthly subscription",
    )
    db_session.add(invoice)
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("billing-dunning",),
        billing_dunning_overdue_as_of=date(2026, 6, 20),
        billing_dunning_repeat_after_days=7,
        limit=10,
    )

    assert result["results"]["billing_dunning"]["eligible_count"] == 1
    assert result["results"]["billing_dunning"]["notice_count"] == 1
    assert result["results"]["billing_dunning"]["record_only_count"] == 1
    assert result["summary"]["processed_count"] == 1
    await db_session.refresh(invoice)
    await db_session.refresh(subscription)
    assert invoice.dunning_count == 1
    assert invoice.dunning_last_severity == "urgent"
    assert invoice.dunning_last_sent_at is not None
    assert subscription.status == SubscriptionStatus.PAST_DUE


async def test_due_worker_applies_late_fee_for_overdue_saas_invoice(db_session) -> None:
    organization = Organization(
        name="Late Fee Worker Club",
        slug="late-fee-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    plan = BillingPlan(
        code="late-fee-growth",
        name="Late Fee Growth",
        base_price=300,
        currency="USD",
        billing_cycle=BillingCycle.MONTHLY,
        included_athletes=100,
        included_teams=8,
        included_agent_tasks=500,
        included_storage_gb=50,
        per_athlete_price=0,
        per_agent_task_price=0,
    )
    db_session.add(plan)
    await db_session.flush()
    subscription = TenantSubscription(
        organization_id=organization.id,
        billing_plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
        billing_cycle=BillingCycle.MONTHLY,
        current_period_start=date(2026, 6, 1),
        current_period_end=date(2026, 6, 30),
        next_billing_on=date(2026, 6, 30),
        seats_purchased=100,
        negotiated_price=250,
    )
    db_session.add(subscription)
    await db_session.flush()
    invoice = SaaSInvoice(
        organization_id=organization.id,
        subscription_id=subscription.id,
        invoice_number="FEE-WORKER-1",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        subtotal=250,
        tax_amount=0,
        discount_amount=0,
        total=250,
        amount_paid=0,
        currency="USD",
        due_on=date(2026, 6, 1),
        status=BillingInvoiceStatus.OPEN,
        line_items="Monthly subscription",
    )
    db_session.add(invoice)
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("billing-late-fees",),
        billing_late_fee_apply_on=date(2026, 6, 20),
        billing_late_fee_fixed_fee=Decimal("10.00"),
        billing_late_fee_percentage_rate=Decimal("5.00"),
        billing_late_fee_max_fee=Decimal("30.00"),
        limit=10,
    )

    assert result["results"]["billing_late_fees"]["eligible_count"] == 1
    assert result["results"]["billing_late_fees"]["fee_count"] == 1
    assert result["results"]["billing_late_fees"]["total_late_fees"] == "22.50"
    assert result["summary"]["processed_count"] == 1
    await db_session.refresh(invoice)
    await db_session.refresh(subscription)
    assert invoice.total == Decimal("272.50")
    assert invoice.late_fee_total == Decimal("22.50")
    assert invoice.late_fee_count == 1
    assert invoice.late_fee_last_applied_on == date(2026, 6, 20)
    assert subscription.status == SubscriptionStatus.PAST_DUE


async def test_due_worker_generates_recurring_subscription_invoice(db_session) -> None:
    organization = Organization(
        name="Recurring Billing Club",
        slug="recurring-billing-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    plan = BillingPlan(
        code="recurring-growth",
        name="Recurring Growth",
        base_price=250,
        currency="USD",
        billing_cycle=BillingCycle.MONTHLY,
        included_athletes=100,
        included_teams=8,
        included_agent_tasks=500,
        included_storage_gb=50,
        per_athlete_price=0,
        per_agent_task_price=0,
    )
    db_session.add(plan)
    await db_session.flush()
    subscription = TenantSubscription(
        organization_id=organization.id,
        billing_plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
        billing_cycle=BillingCycle.MONTHLY,
        current_period_start=date(2026, 6, 1),
        current_period_end=date(2026, 6, 30),
        next_billing_on=date(2026, 6, 30),
        seats_purchased=100,
        negotiated_price=199,
    )
    db_session.add(subscription)
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("billing-recurring-invoices",),
        billing_recurring_invoice_bill_on=date(2026, 6, 30),
        billing_recurring_invoice_due_in_days=10,
        billing_recurring_invoice_prefix="AUTO",
        limit=10,
    )

    assert result["results"]["billing_recurring_invoices"]["eligible_count"] == 1
    assert result["results"]["billing_recurring_invoices"]["invoiced_count"] == 1
    assert result["summary"]["processed_count"] == 1
    invoice = await db_session.scalar(
        select(SaaSInvoice).where(SaaSInvoice.subscription_id == subscription.id)
    )
    assert invoice is not None
    assert invoice.invoice_number.startswith("AUTO-")
    assert invoice.status == BillingInvoiceStatus.OPEN
    assert invoice.total == Decimal("199.00")
    assert invoice.due_on == date(2026, 7, 10)
    await db_session.refresh(subscription)
    assert subscription.current_period_start == date(2026, 7, 1)
    assert subscription.current_period_end == date(2026, 7, 31)
    assert subscription.next_billing_on == date(2026, 7, 31)


async def test_due_worker_escalates_overdue_emergency_activation(db_session) -> None:
    organization = Organization(
        name="Emergency Worker Club",
        slug="emergency-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    plan = EmergencyActionPlan(
        organization_id=organization.id,
        title="Worker emergency plan",
        emergency_type=EmergencyType.MEDICAL,
        status=EmergencyActionPlanStatus.ACTIVE,
        emergency_contacts="Safety lead and medic.",
        communication_protocols="Notify staff and guardians.",
        escalation_matrix="Escalate while unresolved.",
    )
    db_session.add(plan)
    await db_session.flush()
    activation = EmergencyPlanActivation(
        organization_id=organization.id,
        plan_id=plan.id,
        emergency_type=EmergencyType.MEDICAL,
        status=EmergencyActivationStatus.ACTIVE,
        location_detail="Main field",
        activated_at=datetime.now(UTC) - timedelta(hours=1),
        escalation_level=1,
        communication_log="Initial response opened.",
    )
    db_session.add(activation)
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("emergency-escalations",),
        emergency_escalation_unresolved_after_minutes=0,
        emergency_escalation_repeat_after_minutes=1,
        limit=10,
    )

    assert result["results"]["emergency_escalations"]["eligible_count"] == 1
    assert result["results"]["emergency_escalations"]["escalated_count"] == 1
    assert result["summary"]["processed_count"] == 1
    await db_session.refresh(activation)
    assert activation.escalation_level == 2
    assert "automated emergency escalation timer" in (activation.communication_log or "")


async def test_due_worker_dispatches_due_scheduled_messages(db_session) -> None:
    organization = Organization(
        name="Scheduled Dispatch Club",
        slug="scheduled-dispatch-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    person = Person(display_name="Scheduled Parent", primary_email="scheduled-parent@example.com")
    db_session.add_all([organization, person])
    await db_session.flush()
    message = CommunicationMessage(
        organization_id=organization.id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.REMINDER,
        channel=CommunicationChannel.IN_APP,
        scope_type=CommunicationScopeType.ORGANIZATION,
        scope_id=organization.id,
        subject="Tonight training",
        body="Training starts at 18:00.",
        scheduled_for=datetime.now(UTC) - timedelta(minutes=5),
        status="scheduled",
    )
    future_message = CommunicationMessage(
        organization_id=organization.id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.REMINDER,
        channel=CommunicationChannel.IN_APP,
        scope_type=CommunicationScopeType.ORGANIZATION,
        scope_id=organization.id,
        subject="Tomorrow training",
        body="Training starts tomorrow.",
        scheduled_for=datetime.now(UTC) + timedelta(hours=1),
        status="scheduled",
    )
    db_session.add_all([message, future_message])
    await db_session.flush()
    recipient = MessageRecipient(
        message_id=message.id,
        person_id=person.id,
        destination=str(person.id),
        delivery_status=MessageDeliveryStatus.QUEUED,
    )
    db_session.add(recipient)
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("communication-scheduled-dispatch",),
        communication_scheduled_dispatch_limit=10,
    )

    dispatch = result["results"]["communication_scheduled_dispatch"]
    assert dispatch["eligible_count"] == 1
    assert dispatch["executed_count"] == 1
    assert dispatch["dispatched_count"] == 1
    assert dispatch["message_ids"] == [str(message.id)]
    assert result["summary"]["processed_count"] == 1
    await db_session.refresh(message)
    await db_session.refresh(future_message)
    await db_session.refresh(recipient)
    assert message.status == "sent"
    assert message.sent_at is not None
    assert recipient.delivery_status == MessageDeliveryStatus.DELIVERED
    assert recipient.delivered_at is not None
    assert future_message.status == "scheduled"


async def test_due_worker_reconciles_compliance_expiry(db_session) -> None:
    organization = Organization(
        name="Compliance Worker Club",
        slug="compliance-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    person = Person(display_name="Compliance Coach", primary_email="compliance-coach@example.com")
    db_session.add_all([organization, person])
    await db_session.flush()
    check = BackgroundCheck(
        organization_id=organization.id,
        person_id=person.id,
        provider="Manual",
        check_type="Safeguarding screen",
        status=BackgroundCheckStatus.CLEAR,
        risk_level="low",
        requested_at=datetime(2025, 1, 1, tzinfo=UTC),
        expires_at=date(2026, 1, 1),
    )
    expired_credential = ComplianceCredential(
        organization_id=organization.id,
        person_id=person.id,
        credential_type=ComplianceCredentialType.SAFEGUARDING_TRAINING,
        status=ComplianceCredentialStatus.VERIFIED,
        title="Safeguarding training",
        expires_at=date(2026, 1, 1),
    )
    expiring_credential = ComplianceCredential(
        organization_id=organization.id,
        person_id=person.id,
        credential_type=ComplianceCredentialType.FIRST_AID,
        status=ComplianceCredentialStatus.VERIFIED,
        title="First aid",
        renewal_due_at=date(2026, 5, 1),
        expires_at=date(2026, 6, 20),
    )
    db_session.add_all([check, expired_credential, expiring_credential])
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("compliance-reconciliation",),
        limit=10,
    )

    reconciliation = result["results"]["compliance_reconciliation"]
    assert reconciliation["eligible_count"] == 1
    assert reconciliation["executed_count"] == 1
    assert reconciliation["background_checks_expired"] == 1
    assert reconciliation["credentials_expired"] == 1
    assert reconciliation["credentials_expiring_soon"] == 1
    await db_session.refresh(check)
    await db_session.refresh(expired_credential)
    await db_session.refresh(expiring_credential)
    assert check.status == BackgroundCheckStatus.EXPIRED
    assert expired_credential.status == ComplianceCredentialStatus.EXPIRED
    assert expiring_credential.status == ComplianceCredentialStatus.EXPIRING_SOON


async def test_due_worker_runs_communication_digest_lane(db_session) -> None:
    organization = Organization(
        name="Digest Worker Club",
        slug="digest-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    person = Person(display_name="Digest Parent", primary_email="digest-parent@example.com")
    db_session.add(person)
    await db_session.flush()
    db_session.add(
        NotificationPreference(
            organization_id=organization.id,
            person_id=person.id,
            frequency=NotificationFrequency.DAILY_DIGEST,
            channel_preference=ChannelPreference.APP,
        )
    )
    source_message = CommunicationMessage(
        organization_id=organization.id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.ANNOUNCEMENT,
        channel=CommunicationChannel.IN_APP,
        scope_type=CommunicationScopeType.ORGANIZATION,
        scope_id=organization.id,
        subject="Training update",
        body="Training moved to 5pm.",
        sent_at=datetime(2026, 1, 5, 12, tzinfo=UTC),
        status="sent",
    )
    db_session.add(source_message)
    await db_session.flush()
    db_session.add(
        MessageRecipient(
            message_id=source_message.id,
            person_id=person.id,
            destination=str(person.id),
            delivery_status=MessageDeliveryStatus.DELIVERED,
            delivered_at=datetime(2026, 1, 5, 12, tzinfo=UTC),
        )
    )
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("communication-digests",),
        communication_digest_frequency=NotificationFrequency.DAILY_DIGEST,
        communication_digest_limit=10,
    )

    digest = result["results"]["communication_digests"]
    assert digest["eligible_count"] == 1
    assert digest["executed_count"] == 1
    assert digest["created_count"] == 1
    assert digest["skipped_count"] == 0
    assert len(digest["digest_message_ids"]) == 1
    assert result["summary"]["processed_count"] == 1
    digest_message = await db_session.get(CommunicationMessage, digest["digest_message_ids"][0])
    assert digest_message is not None
    assert digest_message.subject == "Digest: daily digest"
    assert "Training update" in digest_message.body


async def test_due_worker_escalates_unresolved_urgent_messages_once(db_session) -> None:
    organization = Organization(
        name="Escalation Worker Club",
        slug="escalation-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    person = Person(display_name="Urgent Parent", primary_email="urgent-parent@example.com")
    db_session.add(person)
    await db_session.flush()
    message = CommunicationMessage(
        organization_id=organization.id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.ALERT,
        channel=CommunicationChannel.EMAIL,
        scope_type=CommunicationScopeType.ORGANIZATION,
        scope_id=organization.id,
        subject="Storm shelter now",
        body="Move to the indoor shelter and confirm attendance.",
        urgent=True,
        quiet_hours_override=True,
        sent_at=datetime(2026, 1, 5, 12, tzinfo=UTC),
        status="sent",
    )
    db_session.add(message)
    await db_session.flush()
    db_session.add(
        MessageRecipient(
            message_id=message.id,
            person_id=person.id,
            destination=person.primary_email,
            delivery_status=MessageDeliveryStatus.QUEUED,
            failure_reason="Provider queue has not delivered yet.",
        )
    )
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("communication-escalations",),
        communication_escalation_channel=CommunicationChannel.IN_APP,
        communication_escalation_unresolved_after_minutes=0,
        communication_escalation_repeat_after_minutes=60,
        communication_escalation_limit=10,
    )

    escalation = result["results"]["communication_escalations"]
    assert escalation["eligible_count"] == 1
    assert escalation["executed_count"] == 1
    assert escalation["escalated_count"] == 1
    assert escalation["skipped_count"] == 0
    assert len(escalation["escalation_message_ids"]) == 1
    escalation_message = await db_session.get(CommunicationMessage, escalation["escalation_message_ids"][0])
    assert escalation_message is not None
    assert escalation_message.escalates_message_id == message.id
    assert escalation_message.escalation_level == 2
    assert escalation_message.quiet_hours_override is True

    repeat = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("communication-escalations",),
        communication_escalation_channel=CommunicationChannel.IN_APP,
        communication_escalation_unresolved_after_minutes=0,
        communication_escalation_repeat_after_minutes=60,
        communication_escalation_limit=10,
    )
    repeat_escalation = repeat["results"]["communication_escalations"]
    assert repeat_escalation["eligible_count"] == 1
    assert repeat_escalation["escalated_count"] == 0
    assert repeat_escalation["skipped_count"] == 1


async def test_due_worker_sends_travel_consent_reminders_once(db_session) -> None:
    organization = Organization(
        name="Travel Reminder Worker Club",
        slug="travel-reminder-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    athlete = Person(display_name="Minor Traveler", primary_email="minor-traveler@example.com")
    guardian = Person(
        display_name="Travel Guardian",
        primary_email="travel-guardian@example.com",
        primary_phone="+15550124000",
    )
    db_session.add_all([athlete, guardian])
    await db_session.flush()
    event = Event(
        organization_id=organization.id,
        team_id=None,
        event_type=EventType.TOURNAMENT,
        title="Regional Finals",
        starts_at=datetime(2026, 3, 8, 9, tzinfo=UTC),
        ends_at=datetime(2026, 3, 8, 17, tzinfo=UTC),
        venue_name="Regional Stadium",
    )
    db_session.add(event)
    await db_session.flush()
    plan = EventTravelPlan(
        organization_id=organization.id,
        event_id=event.id,
        status=TravelPlanStatus.READY,
        destination="Regional Stadium",
        travel_mode="bus",
        departure_at=datetime(2026, 3, 8, 6, tzinfo=UTC),
        consent_required=True,
        consent_due_at=datetime.now(UTC) + timedelta(hours=12),
        risk_assessment="Standard supervised team travel.",
    )
    request = ConsentRequest(
        organization_id=organization.id,
        athlete_person_id=athlete.id,
        guardian_person_id=guardian.id,
        scope_type=ConsentScopeType.EVENT,
        scope_id=event.id,
        channel=ConsentCaptureChannel.EMAIL,
        destination="travel-guardian@example.com",
        token_hash="travel-reminder-worker-token",
        status=ConsentRequestStatus.PENDING,
        sent_at=datetime.now(UTC) - timedelta(hours=4),
        notes="Travel consent pending.",
    )
    db_session.add_all([plan, request])
    await db_session.commit()

    first = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("event-travel-consent-reminders",),
        event_travel_consent_reminder_channel=CommunicationChannel.IN_APP,
        event_travel_consent_reminder_due_within_hours=48,
        event_travel_consent_reminder_repeat_after_hours=24,
        event_travel_consent_reminder_limit=10,
    )

    reminder = first["results"]["event_travel_consent_reminders"]
    assert reminder["eligible_count"] == 1
    assert reminder["executed_count"] == 1
    assert reminder["reminded_count"] == 1
    assert reminder["skipped_count"] == 0
    assert reminder["due_plan_count"] == 1
    assert reminder["pending_request_count"] == 1
    assert reminder["recipient_count"] == 1
    assert len(reminder["message_ids"]) == 1
    message = await db_session.get(CommunicationMessage, reminder["message_ids"][0])
    assert message is not None
    assert message.subject == "Travel consent deadline approaching: Regional Finals"
    assert "Regional Stadium" in message.body
    assert first["summary"]["processed_count"] == 1

    second = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("event-travel-consent-reminders",),
        event_travel_consent_reminder_channel=CommunicationChannel.IN_APP,
        event_travel_consent_reminder_due_within_hours=48,
        event_travel_consent_reminder_repeat_after_hours=24,
        event_travel_consent_reminder_limit=10,
    )

    duplicate = second["results"]["event_travel_consent_reminders"]
    assert duplicate["eligible_count"] == 1
    assert duplicate["executed_count"] == 1
    assert duplicate["reminded_count"] == 0
    assert duplicate["skipped_count"] == 1
    assert duplicate["message_ids"] == []
    message_count = await db_session.scalar(
        select(func.count(CommunicationMessage.id)).where(
            CommunicationMessage.organization_id == organization.id,
            CommunicationMessage.subject == "Travel consent deadline approaching: Regional Finals",
        )
    )
    assert message_count == 1


async def test_due_worker_sends_family_portal_invite_reminders_once(db_session) -> None:
    organization = Organization(
        name="Family Reminder Worker Club",
        slug="family-reminder-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    athlete = Person(display_name="Portal Athlete", primary_email="portal-athlete@example.com")
    guardian = Person(display_name="Portal Guardian", primary_email="portal-guardian@example.com")
    db_session.add_all([athlete, guardian])
    await db_session.flush()
    profile = AthleteProfile(
        organization_id=organization.id,
        person_id=athlete.id,
        athlete_code="PORTAL-1",
    )
    relationship = GuardianRelationship(
        athlete_person_id=athlete.id,
        guardian_person_id=guardian.id,
        relationship_kind=GuardianRelationshipKind.PARENT,
        relationship="parent",
        can_sign_consent=True,
    )
    invite = CommunicationMessage(
        organization_id=organization.id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.REQUEST,
        channel=CommunicationChannel.EMAIL,
        scope_type=CommunicationScopeType.PERSON,
        scope_id=guardian.id,
        subject="Family portal invitation",
        body="Open the AfroLete family portal to complete onboarding.",
        sent_at=datetime.now(UTC) - timedelta(hours=30),
        status="sent",
    )
    db_session.add_all([profile, relationship, invite])
    await db_session.flush()
    db_session.add(
        MessageRecipient(
            message_id=invite.id,
            person_id=guardian.id,
            destination=guardian.primary_email,
            delivery_status=MessageDeliveryStatus.QUEUED,
        )
    )
    await db_session.commit()

    first = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("family-portal-invite-reminders",),
        family_portal_invite_reminder_channel=CommunicationChannel.IN_APP,
        family_portal_invite_reminder_invited_before_hours=24,
        family_portal_invite_reminder_repeat_after_hours=24,
        family_portal_invite_reminder_limit=10,
    )

    reminder = first["results"]["family_portal_invite_reminders"]
    assert reminder["eligible_count"] == 1
    assert reminder["executed_count"] == 1
    assert reminder["reminded_count"] == 1
    assert reminder["skipped_count"] == 0
    assert len(reminder["message_ids"]) == 1
    message = await db_session.get(CommunicationMessage, reminder["message_ids"][0])
    assert message is not None
    assert message.subject == "Family portal sign-in reminder"
    assert "Portal Guardian" in message.body
    assert "family portal" in message.body

    second = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("family-portal-invite-reminders",),
        family_portal_invite_reminder_channel=CommunicationChannel.IN_APP,
        family_portal_invite_reminder_invited_before_hours=24,
        family_portal_invite_reminder_repeat_after_hours=24,
        family_portal_invite_reminder_limit=10,
    )

    duplicate = second["results"]["family_portal_invite_reminders"]
    assert duplicate["eligible_count"] == 1
    assert duplicate["reminded_count"] == 0
    assert duplicate["skipped_count"] == 1


async def test_due_worker_runs_forecast_validation_lane(db_session) -> None:
    organization = Organization(
        name="Forecast Worker Club",
        slug="forecast-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    person = Person(display_name="Forecast Athlete", primary_email="forecast-athlete@example.com")
    db_session.add(person)
    await db_session.flush()
    athlete = AthleteProfile(organization_id=organization.id, person_id=person.id)
    metric = PerformanceMetricDefinition(
        organization_id=organization.id,
        sport="football",
        code="sprint_time",
        name="Sprint Time",
        category=MetricCategory.PHYSICAL,
        unit="seconds",
        higher_is_better=False,
    )
    db_session.add_all([athlete, metric])
    await db_session.flush()
    for index, value in enumerate([13.0, 12.5, 12.0, 11.6]):
        db_session.add(
            AthletePerformanceObservation(
                organization_id=organization.id,
                athlete_profile_id=athlete.id,
                metric_definition_id=metric.id,
                value=value,
                observed_at=datetime(2026, 1, 1 + index * 7, 10, tzinfo=UTC),
                source=MetricSource.COACH_EVALUATION,
            )
        )
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("performance-forecast-validations",),
        limit=10,
    )

    assert result["summary"]["eligible_count"] == 1
    assert result["summary"]["processed_count"] == 1
    validation = result["results"]["performance_forecast_validations"]
    assert validation["eligible_count"] == 1
    assert validation["executed_count"] == 1
    assert validation["evaluated_count"] == 1
    assert validation["drift_count"] == 0
    assert validation["watch_count"] == 0
    assert validation["high_count"] == 0
    assert len(validation["run_ids"]) == 1
    run_count = await db_session.scalar(
        select(func.count(PerformanceForecastValidationRun.id)).where(
            PerformanceForecastValidationRun.organization_id == organization.id,
            PerformanceForecastValidationRun.drift_level == "stable",
        )
    )
    assert run_count == 1


async def test_due_worker_auto_alerts_forecast_validation_drift(db_session) -> None:
    organization = Organization(
        name="Forecast Alert Worker Club",
        slug="forecast-alert-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    manager = Person(
        display_name="Forecast Manager",
        primary_email="forecast-manager@example.com",
        primary_phone="+15550123000",
    )
    athlete_person = Person(display_name="Drift Athlete", primary_email="drift-athlete@example.com")
    db_session.add_all([manager, athlete_person])
    await db_session.flush()
    db_session.add(
        Membership(
            organization_id=organization.id,
            subject_type=MemberSubjectType.PERSON,
            subject_id=manager.id,
            role=MembershipRole.COACH,
        )
    )
    athlete = AthleteProfile(organization_id=organization.id, person_id=athlete_person.id)
    metric = PerformanceMetricDefinition(
        organization_id=organization.id,
        sport="football",
        code="power_score",
        name="Power Score",
        category=MetricCategory.PHYSICAL,
        unit="points",
        higher_is_better=True,
    )
    db_session.add_all([athlete, metric])
    await db_session.flush()
    for index, value in enumerate([10.0, 10.0, 10.0, 30.0]):
        db_session.add(
            AthletePerformanceObservation(
                organization_id=organization.id,
                athlete_profile_id=athlete.id,
                metric_definition_id=metric.id,
                value=value,
                observed_at=datetime(2026, 2, 1 + index * 7, 10, tzinfo=UTC),
                source=MetricSource.COACH_EVALUATION,
            )
        )
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("performance-forecast-validations",),
        limit=10,
        auto_alert_performance_forecast_drift=True,
        performance_forecast_drift_channels=[CommunicationChannel.IN_APP, CommunicationChannel.SMS],
    )

    validation = result["results"]["performance_forecast_validations"]
    assert validation["executed_count"] == 1
    assert validation["high_count"] == 1
    assert validation["alerted_count"] == 1
    assert validation["alert_channel_count"] == 2
    assert validation["alert_skipped_count"] == 0
    assert validation["alert_failed_count"] == 0
    assert len(validation["alert_message_ids"]) == 2
    assert result["summary"]["processed_count"] == 1
    message_count = await db_session.scalar(
        select(func.count(CommunicationMessage.id)).where(
            CommunicationMessage.organization_id == organization.id,
            CommunicationMessage.subject.ilike("%forecast drift high%"),
        )
    )
    recipient_count = await db_session.scalar(select(func.count(MessageRecipient.id)))
    assert message_count == 2
    assert recipient_count == 2


async def test_due_worker_retries_rate_limited_wearable_pull(db_session, monkeypatch) -> None:
    organization = Organization(
        name="Wearable Retry Club",
        slug="wearable-retry-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    person = Person(display_name="Wearable Athlete", primary_email="wearable-athlete@example.com")
    db_session.add(person)
    await db_session.flush()
    athlete = AthleteProfile(organization_id=organization.id, person_id=person.id)
    db_session.add(athlete)
    await db_session.flush()
    connection = PerformanceWearableProviderConnection(
        organization_id=organization.id,
        athlete_profile_id=athlete.id,
        provider="whoop",
        display_name="WHOOP retry",
        external_athlete_ref="whoop-retry-athlete",
        access_token_secret_path="secret/data/afrolete/wearables/whoop/retry",
        provider_pull_url="https://whoop.example/v1/recovery",
    )
    db_session.add(connection)
    await db_session.flush()
    old_run = PerformanceWearableProviderSyncRun(
        organization_id=organization.id,
        connection_id=connection.id,
        athlete_profile_id=athlete.id,
        provider="whoop",
        status="rate_limited",
        sync_mode="pull",
        started_at=datetime.now(UTC) - timedelta(minutes=10),
        completed_at=datetime.now(UTC) - timedelta(minutes=10),
        provider_status_code=429,
        provider_response_hash="rate-limit-hash",
        provider_page_count=0,
        provider_rate_limited=True,
        provider_retry_after_seconds=60,
        message="Rate limited by provider.",
    )
    db_session.add(old_run)
    await db_session.commit()

    async def fake_execute(db, retry_connection, payload):
        retry_run = PerformanceWearableProviderSyncRun(
            organization_id=retry_connection.organization_id,
            connection_id=retry_connection.id,
            athlete_profile_id=retry_connection.athlete_profile_id,
            provider=retry_connection.provider,
            status="completed",
            sync_mode=payload.sync_mode,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            observation_count=2,
            skipped_metric_count=0,
            provider_status_code=200,
            provider_response_hash="retry-hash",
            provider_page_count=1,
            provider_rate_limited=False,
            message="Retry completed.",
        )
        db.add(retry_run)
        await db.commit()
        await db.refresh(retry_run)
        return retry_run

    monkeypatch.setattr(performance_service, "execute_wearable_provider_sync", fake_execute)

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("wearable-pull-retries",),
        wearable_pull_default_retry_after_seconds=60,
    )

    assert result["summary"]["eligible_count"] == 1
    assert result["summary"]["processed_count"] == 1
    retry_result = result["results"]["wearable_pull_retries"]
    assert retry_result["eligible_count"] == 1
    assert retry_result["retried_count"] == 1
    assert retry_result["rate_limited_count"] == 1
    retry_count = await db_session.scalar(
        select(func.count(PerformanceWearableProviderSyncRun.id)).where(
            PerformanceWearableProviderSyncRun.connection_id == connection.id,
            PerformanceWearableProviderSyncRun.status == "completed",
        )
    )
    assert retry_count == 1


async def test_due_worker_honors_provider_wearable_backoff_policy(db_session, monkeypatch) -> None:
    organization = Organization(
        name="Wearable Policy Club",
        slug="wearable-policy-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    person = Person(display_name="Policy Athlete", primary_email="policy-athlete@example.com")
    db_session.add(person)
    await db_session.flush()
    athlete = AthleteProfile(organization_id=organization.id, person_id=person.id)
    db_session.add(athlete)
    await db_session.flush()
    connection = PerformanceWearableProviderConnection(
        organization_id=organization.id,
        athlete_profile_id=athlete.id,
        provider="WHOOP",
        display_name="WHOOP policy",
        external_athlete_ref="policy-athlete",
        access_token_secret_path="secret/data/afrolete/wearables/whoop/policy",
        provider_pull_url="https://whoop.example/v1/recovery",
    )
    db_session.add(connection)
    await db_session.flush()
    old_run = PerformanceWearableProviderSyncRun(
        organization_id=organization.id,
        connection_id=connection.id,
        athlete_profile_id=athlete.id,
        provider="WHOOP",
        status="rate_limited",
        sync_mode="pull",
        started_at=datetime.now(UTC) - timedelta(minutes=2),
        completed_at=datetime.now(UTC) - timedelta(minutes=2),
        provider_status_code=429,
        provider_response_hash="policy-rate-limit-hash",
        provider_page_count=0,
        provider_rate_limited=True,
        provider_retry_after_seconds=None,
        message="Rate limited by provider without Retry-After.",
    )
    db_session.add(old_run)
    await db_session.commit()

    result = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("wearable-pull-retries",),
        wearable_pull_default_retry_after_seconds=60,
        wearable_pull_provider_retry_after_seconds={"whoop": 900},
    )

    assert result["summary"]["eligible_count"] == 0
    assert result["results"]["wearable_pull_retries"]["provider_retry_after_seconds"] == {"whoop": 900}

    old_run.completed_at = datetime.now(UTC) - timedelta(minutes=20)
    old_run.started_at = old_run.completed_at
    db_session.add(old_run)
    await db_session.commit()
    seen_max_pages: list[int] = []

    async def fake_execute(db, retry_connection, payload):
        seen_max_pages.append(payload.max_pages)
        retry_run = PerformanceWearableProviderSyncRun(
            organization_id=retry_connection.organization_id,
            connection_id=retry_connection.id,
            athlete_profile_id=retry_connection.athlete_profile_id,
            provider=retry_connection.provider,
            status="completed",
            sync_mode=payload.sync_mode,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            observation_count=1,
            provider_status_code=200,
            provider_response_hash="policy-retry-hash",
            provider_page_count=1,
            provider_rate_limited=False,
            message="Policy retry completed.",
        )
        db.add(retry_run)
        await db.commit()
        await db.refresh(retry_run)
        return retry_run

    monkeypatch.setattr(performance_service, "execute_wearable_provider_sync", fake_execute)

    retried = await run_due_workers(
        db_session,
        organization_id=organization.id,
        lanes=("wearable-pull-retries",),
        wearable_pull_provider_retry_after_seconds={"whoop": 900},
        wearable_pull_provider_max_pages={"whoop": 1},
    )

    retry_result = retried["results"]["wearable_pull_retries"]
    assert retry_result["retried_count"] == 1
    assert retry_result["provider_policy_matches"] == {"whoop": 1}
    assert retry_result["provider_max_pages"] == {"whoop": 1}
    assert seen_max_pages == [1]
