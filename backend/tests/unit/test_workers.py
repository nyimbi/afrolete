from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.models.agent import Agent, AgentRunRecord, AgentTask
from app.models.enums import AgentKind, AgentTaskStatus, MetricCategory, MetricSource, OrganizationType
from app.models.identity import Person
from app.models.organization import Organization
from app.models.performance import (
    AthletePerformanceObservation,
    PerformanceForecastValidationRun,
    PerformanceMetricDefinition,
    PerformanceWearableProviderConnection,
    PerformanceWearableProviderSyncRun,
)
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
        "performance-forecast-validations",
        "performance-injury-risk-alerts",
        "performance-review-escalations",
        "wearable-pull-retries",
    ]
    assert result["summary"]["eligible_count"] == 1
    assert result["summary"]["processed_count"] == 1
    assert result["results"]["developer_webhooks"]["eligible_count"] == 0
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
        "developer-webhooks",
        "performance-achievements",
        "performance-forecast-validations",
        "performance-injury-risk-alerts",
        "performance-review-escalations",
        "wearable-pull-retries",
    }
    assert selected_lanes(("agent-tasks",)) == {"agent-tasks"}


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
