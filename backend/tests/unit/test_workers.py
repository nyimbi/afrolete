from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.models.agent import Agent, AgentRunRecord, AgentTask
from app.models.enums import AgentKind, AgentTaskStatus, OrganizationType
from app.models.identity import Person
from app.models.organization import Organization
from app.models.performance import PerformanceWearableProviderConnection, PerformanceWearableProviderSyncRun
from app.models.team import AthleteProfile
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
        "developer-webhooks",
        "performance-achievements",
        "performance-injury-risk-alerts",
        "performance-review-escalations",
        "wearable-pull-retries",
    ]
    assert result["summary"]["eligible_count"] == 1
    assert result["summary"]["processed_count"] == 1
    assert result["results"]["developer_webhooks"]["eligible_count"] == 0
    assert result["results"]["performance_achievements"]["eligible_count"] == 0
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
        "developer-webhooks",
        "performance-achievements",
        "performance-injury-risk-alerts",
        "performance-review-escalations",
        "wearable-pull-retries",
    }
    assert selected_lanes(("agent-tasks",)) == {"agent-tasks"}


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
