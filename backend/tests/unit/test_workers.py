from sqlalchemy import func, select

from app.models.agent import Agent, AgentRunRecord, AgentTask
from app.models.enums import AgentKind, AgentTaskStatus, OrganizationType
from app.models.organization import Organization
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

    assert result["lanes"] == ["agent-tasks", "developer-webhooks"]
    assert result["summary"]["eligible_count"] == 1
    assert result["summary"]["processed_count"] == 1
    assert result["results"]["developer_webhooks"]["eligible_count"] == 0
    await db_session.refresh(task)
    assert task.status == AgentTaskStatus.WAITING_FOR_REVIEW
    record_count = await db_session.scalar(
        select(func.count(AgentRunRecord.id)).where(AgentRunRecord.task_id == task.id)
    )
    assert record_count == 2


def test_selected_lanes_expands_all() -> None:
    assert selected_lanes(("all",)) == {"agent-tasks", "developer-webhooks"}
    assert selected_lanes(("agent-tasks",)) == {"agent-tasks"}
