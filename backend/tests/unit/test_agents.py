from sqlalchemy import select

from app.models.agent import Agent, AgentRunRecord, AgentTask
from app.models.enums import AgentKind, AgentTaskStatus, GuardianRelationshipKind, OrganizationType
from app.models.organization import Organization
from app.models.identity import Person
from app.models.team import AthleteProfile, GuardianRelationship
from app.services.agents import get_my_agent_decision_appeal_form, run_agent_task_worker
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import authorization_service


def create_org_and_team(client, identity_headers, suffix: str = "one"):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": f"Agent Ready Club {suffix}",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": f"Agent Reviewed U17 {suffix}",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    return organization, team


def test_agent_assignment_and_task_review_workflow(client, identity_headers) -> None:
    organization, team = create_org_and_team(client, identity_headers)

    create_response = client.post(
        "/api/v1/agents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Safeguarding Watch",
            "kind": "safeguarding",
            "purpose": "Monitor consent gaps and flag risky participation decisions.",
            "model_policy": "review_required",
        },
    )

    assert create_response.status_code == 201
    agent = create_response.json()
    assert agent["status"] == "active"
    assert agent["kind"] == "safeguarding"
    assert any(
        relationship.resource_type == "agent"
        and relationship.resource_id == agent["id"]
        and relationship.relation == "owner"
        and relationship.subject_type == "user"
        for relationship in authorization_service.relationships
    )

    assignment_response = client.post(
        f"/api/v1/agents/{agent['id']}/assignments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "scope_type": "team",
            "scope_id": team["id"],
        },
    )

    assert assignment_response.status_code == 201
    assignment = assignment_response.json()
    assert assignment["scope_type"] == "team"
    assert assignment["scope_id"] == team["id"]
    assert any(
        relationship.resource_type == "team"
        and relationship.resource_id == team["id"]
        and relationship.relation == "assigned_agent"
        and relationship.subject_type == "agent"
        and relationship.subject_id == agent["id"]
        for relationship in authorization_service.relationships
    )

    task_response = client.post(
        f"/api/v1/agents/{agent['id']}/tasks",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "task_type": "consent_gap_review",
            "title": "Review missing U17 event consent",
            "input_ref": f"team:{team['id']}",
        },
    )

    assert task_response.status_code == 201
    task = task_response.json()
    assert task["status"] == "queued"
    assert task["requested_by_person_id"] is not None

    task_list = client.get(
        f"/api/v1/agents/tasks?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert [item["id"] for item in task_list] == [task["id"]]

    execution_response = client.post(
        f"/api/v1/agents/tasks/{task['id']}/execute",
        headers=identity_headers,
    )

    assert execution_response.status_code == 200
    executed = execution_response.json()
    assert executed["status"] == "waiting_for_review"
    assert executed["output_ref"] == f"agent://tasks/{task['id']}/outputs/deterministic"
    assert "deterministic draft" in executed["review_notes"]

    review_response = client.patch(
        f"/api/v1/agents/tasks/{task['id']}",
        headers=identity_headers,
        json={
            "status": "waiting_for_review",
            "output_ref": f"agent-output:{task['id']}",
            "review_notes": "Needs human review before messaging guardians.",
        },
    )

    assert review_response.status_code == 200
    reviewed = review_response.json()
    assert reviewed["status"] == "waiting_for_review"
    assert reviewed["output_ref"] == f"agent-output:{task['id']}"
    assert "human review" in reviewed["review_notes"]


def test_agent_task_multi_approval_routing(client, identity_headers) -> None:
    organization, team = create_org_and_team(client, identity_headers, "approval")
    agent = client.post(
        "/api/v1/agents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Approval Steward",
            "kind": "operations",
            "purpose": "Route sensitive AI recommendations through human approvals.",
            "model_policy": "two_person_review",
        },
    ).json()
    task = client.post(
        f"/api/v1/agents/{agent['id']}/tasks",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "task_type": "selection_recommendation",
            "title": "Approve matchday selection recommendation",
            "input_ref": f"team:{team['id']}",
        },
    ).json()
    executed = client.post(f"/api/v1/agents/tasks/{task['id']}/execute", headers=identity_headers).json()
    assert executed["status"] == "waiting_for_review"

    approval_response = client.post(
        f"/api/v1/agents/tasks/{task['id']}/approvals",
        headers=identity_headers,
        json={
            "required_count": 2,
            "request_notes": "Selection advice needs two humans before it can be accepted.",
        },
    )

    assert approval_response.status_code == 201
    approvals = approval_response.json()
    assert len(approvals) == 2
    assert {approval["status"] for approval in approvals} == {"pending"}

    blocked_completion = client.patch(
        f"/api/v1/agents/tasks/{task['id']}",
        headers=identity_headers,
        json={"status": "completed"},
    )
    assert blocked_completion.status_code == 409

    first_decision = client.patch(
        f"/api/v1/agents/approvals/{approvals[0]['id']}",
        headers=identity_headers,
        json={"status": "approved", "decision_notes": "Coach accepted the recommendation."},
    )
    assert first_decision.status_code == 200
    first = first_decision.json()
    assert first["status"] == "approved"

    task_after_first = client.get(
        f"/api/v1/agents/tasks?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()[0]
    assert task_after_first["approval_status"] == "pending"
    assert task_after_first["approval_approved_count"] == 1
    assert task_after_first["status"] == "waiting_for_review"

    second_decision = client.patch(
        f"/api/v1/agents/approvals/{approvals[1]['id']}",
        headers=identity_headers,
        json={"status": "approved", "decision_notes": "Manager accepted the recommendation."},
    )
    assert second_decision.status_code == 200

    task_after_second = client.get(
        f"/api/v1/agents/tasks?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()[0]
    assert task_after_second["approval_status"] == "approved"
    assert task_after_second["approval_approved_count"] == 2
    assert task_after_second["approval_pending_count"] == 0
    assert task_after_second["status"] == "completed"

    approvals_list = client.get(
        f"/api/v1/agents/tasks/{task['id']}/approvals",
        headers=identity_headers,
    ).json()
    assert [approval["status"] for approval in approvals_list] == ["approved", "approved"]

    governance = client.get(
        f"/api/v1/agents/governance?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert governance["approval_approved"] == 1
    assert governance["approval_pending"] == 0

    runs = client.get(
        f"/api/v1/agents/runs?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert "approval_requested" in [run["event_type"] for run in runs]
    assert "approval_decided" in [run["event_type"] for run in runs]


async def test_agent_task_worker_executes_queued_tasks(db_session) -> None:
    organization = Organization(
        name="Agent Worker Club",
        slug="agent-worker-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    agent = Agent(
        organization_id=organization.id,
        name="Worker Coach",
        kind=AgentKind.OPERATIONS,
        purpose="Execute background agent tasks for operations review.",
        model_policy="worker-local-model",
    )
    db_session.add(agent)
    await db_session.flush()
    task = AgentTask(
        agent_id=agent.id,
        organization_id=organization.id,
        task_type="schedule_review",
        title="Review next match logistics",
        input_ref="event:upcoming",
    )
    db_session.add(task)
    await db_session.commit()

    result = await run_agent_task_worker(db_session, organization_id=organization.id, limit=10)

    assert result.eligible_count == 1
    assert result.executed_count == 1
    assert result.skipped_count == 0
    assert result.statuses["waiting_for_review"] == 1
    await db_session.refresh(task)
    assert task.status == AgentTaskStatus.WAITING_FOR_REVIEW
    assert task.output_ref == f"agent://tasks/{task.id}/outputs/deterministic"
    records = list(
        (
            await db_session.scalars(
                select(AgentRunRecord).where(AgentRunRecord.task_id == task.id).order_by(AgentRunRecord.ledger_sequence)
            )
        ).all()
    )
    assert [record.event_type for record in records] == ["execution_started", "execution_finished"]
    assert records[0].record_hash
    assert records[1].previous_record_hash == records[0].record_hash


async def test_family_ai_appeal_form_renders_markdown_and_pdf(db_session) -> None:
    organization = Organization(
        name="Agent Appeal Club",
        slug="agent-appeal-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    athlete = Person(display_name="Appeal Athlete", primary_email="appeal-athlete@example.com")
    guardian = Person(display_name="Appeal Guardian", primary_email="appeal-guardian@example.com")
    db_session.add_all([organization, athlete, guardian])
    await db_session.flush()
    profile = AthleteProfile(
        organization_id=organization.id,
        person_id=athlete.id,
        athlete_code="AP-10",
    )
    relationship = GuardianRelationship(
        athlete_person_id=athlete.id,
        guardian_person_id=guardian.id,
        relationship_kind=GuardianRelationshipKind.PARENT,
        relationship="parent",
        can_sign_consent=True,
    )
    agent = Agent(
        organization_id=organization.id,
        name="Family Explainability Agent",
        kind=AgentKind.SAFEGUARDING,
        purpose="Explain AI recommendations to families before decisions are finalized.",
        model_policy="family_review_model",
    )
    db_session.add_all([profile, relationship, agent])
    await db_session.flush()
    task = AgentTask(
        organization_id=organization.id,
        agent_id=agent.id,
        task_type="family_recommendation_review",
        title="Review athlete workload recommendation",
        status=AgentTaskStatus.WAITING_FOR_REVIEW,
        input_ref=f"athlete_profile:{profile.id}",
        output_ref=f"agent://tasks/family/{profile.id}",
        review_notes="Recommend reducing load after soreness signal.",
    )
    db_session.add(task)
    await db_session.commit()
    identity = CurrentIdentity(
        user_id=guardian.id,
        person_id=guardian.id,
        keycloak_sub="kc-parent-appeal",
        email="appeal-guardian@example.com",
        display_name="Appeal Guardian",
    )

    markdown = await get_my_agent_decision_appeal_form(db_session, identity, organization.id, task.id)
    assert markdown["artifact_format"] == "markdown"
    assert markdown["download_filename"].endswith(".md")
    assert markdown["content_type"].startswith("text/markdown")
    assert "AfroLete AI Decision Appeal Form" in str(markdown["content"])
    assert markdown["content_base64"] is None
    assert markdown["checksum"]
    assert markdown["size_bytes"] > 100

    pdf = await get_my_agent_decision_appeal_form(db_session, identity, organization.id, task.id, "pdf")
    assert pdf["artifact_format"] == "pdf"
    assert pdf["download_filename"].endswith(".pdf")
    assert pdf["content_type"] == "application/pdf"
    assert pdf["content"] == ""
    assert isinstance(pdf["content_base64"], str)
    assert pdf["size_bytes"] > 500


def test_agent_assignment_rejects_cross_organization_scope(client, identity_headers) -> None:
    first_org, _ = create_org_and_team(client, identity_headers, "one")
    second_org, second_team = create_org_and_team(client, identity_headers, "two")
    agent = client.post(
        "/api/v1/agents",
        headers=identity_headers,
        json={
            "organization_id": first_org["id"],
            "name": "Event Operator",
            "kind": "operations",
            "purpose": "Coordinate scheduling and venue conflict work.",
        },
    ).json()

    response = client.post(
        f"/api/v1/agents/{agent['id']}/assignments",
        headers=identity_headers,
        json={
            "organization_id": first_org["id"],
            "scope_type": "team",
            "scope_id": second_team["id"],
        },
    )

    assert second_org["id"] != first_org["id"]
    assert response.status_code == 422
    assert response.json()["detail"] == "Assignment scope belongs to another organization"
