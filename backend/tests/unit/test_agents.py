from sqlalchemy import select

from app.models.agent import Agent, AgentRunRecord, AgentTask
from app.models.enums import AgentKind, AgentTaskStatus, GuardianRelationshipKind, OrganizationType
from app.models.identity import Person
from app.models.organization import Organization
from app.models.team import AthleteProfile, GuardianRelationship
from app.schemas.agent import AgentWorkerCallbackCreate
from app.services.agents import (
    apply_agent_worker_callback,
    get_my_agent_decision_appeal_form,
    run_agent_task_worker,
    verify_agent_run_ledger,
)
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


def test_agent_governance_policy_requires_approvals_and_blocks_tasks(client, identity_headers) -> None:
    organization, team = create_org_and_team(client, identity_headers, "policy")
    agent = client.post(
        "/api/v1/agents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Policy Steward",
            "kind": "safeguarding",
            "purpose": "Apply tenant AI governance rules before sensitive recommendations run.",
            "model_policy": "sensitive-athlete-model",
        },
    ).json()

    policy_response = client.post(
        "/api/v1/agents/governance-policy-rules",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "rule_code": "safeguarding.selection.review",
            "title": "Selection advice requires two approvals",
            "agent_kind": "safeguarding",
            "task_type_contains": "selection",
            "model_policy_contains": "sensitive",
            "decision": "require_approval",
            "required_approval_count": 2,
            "risk_level": "critical",
            "rationale": "Athlete selection advice can materially affect minors and must be human-governed.",
        },
    )

    assert policy_response.status_code == 201
    policy = policy_response.json()
    assert policy["decision"] == "require_approval"

    simulation_response = client.post(
        "/api/v1/agents/governance-policy-rules/simulate",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "agent_id": agent["id"],
            "task_type": "selection_recommendation",
            "title": "Preview tournament squad recommendation",
            "input_ref": f"team:{team['id']}",
        },
    )
    assert simulation_response.status_code == 200
    simulation = simulation_response.json()
    assert simulation["matched"] is True
    assert simulation["matched_rule"]["rule_code"] == "safeguarding.selection.review"
    assert simulation["decision"] == "require_approval"
    assert simulation["would_require_approval"] is True
    assert simulation["required_approval_count"] == 2

    task_response = client.post(
        f"/api/v1/agents/{agent['id']}/tasks",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "task_type": "selection_recommendation",
            "title": "Recommend tournament squad",
            "input_ref": f"team:{team['id']}",
        },
    )

    assert task_response.status_code == 201
    task = task_response.json()
    assert task["governance_policy_code"] == "safeguarding.selection.review"
    assert task["governance_policy_decision"] == "require_approval"
    assert task["governance_policy_risk_level"] == "critical"
    assert task["approval_status"] == "pending"
    assert task["approval_required_count"] == 2
    assert task["approval_pending_count"] == 2

    approvals = client.get(
        f"/api/v1/agents/tasks/{task['id']}/approvals",
        headers=identity_headers,
    ).json()
    assert len(approvals) == 2
    assert all(approval["request_notes"].startswith("Required by AI governance policy") for approval in approvals)

    runs = client.get(
        f"/api/v1/agents/runs?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert runs[0]["event_type"] == "queued"
    assert "safeguarding.selection.review" in runs[0]["governance_notes"]

    block_response = client.post(
        "/api/v1/agents/governance-policy-rules",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "rule_code": "medical.autoapply.block",
            "title": "Medical auto-apply is blocked",
            "task_type_contains": "medical_auto_apply",
            "decision": "block",
            "required_approval_count": 1,
            "risk_level": "critical",
            "rationale": "Medical clearance side effects must not be automated by an AI agent.",
        },
    )
    assert block_response.status_code == 201

    blocked_simulation = client.post(
        "/api/v1/agents/governance-policy-rules/simulate",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "agent_id": agent["id"],
            "task_type": "medical_auto_apply",
            "title": "Preview auto-apply return-to-play clearance",
            "input_ref": "incident:medical",
        },
    ).json()
    assert blocked_simulation["matched_rule"]["rule_code"] == "medical.autoapply.block"
    assert blocked_simulation["would_block"] is True
    assert blocked_simulation["decision"] == "block"

    blocked_task = client.post(
        f"/api/v1/agents/{agent['id']}/tasks",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "task_type": "medical_auto_apply",
            "title": "Auto-apply return-to-play clearance",
            "input_ref": "incident:medical",
        },
    )
    assert blocked_task.status_code == 409
    assert "medical.autoapply.block" in blocked_task.json()["detail"]

    report = client.get(
        f"/api/v1/agents/governance-policy-rules/report?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert report["active_rule_count"] == 2
    assert report["approval_rule_count"] == 1
    assert report["blocking_rule_count"] == 1
    assert report["governed_task_count"] == 1
    assert report["recent_policy_codes"] == ["safeguarding.selection.review"]

    history = client.get(
        f"/api/v1/agents/governance-policy-rules/history?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert history["governed_task_count"] == 1
    assert history["approval_required_count"] == 1
    assert history["policy_count"] == 1
    assert history["latest_policy_code"] == "safeguarding.selection.review"
    assert history["timeline"][0]["task_count"] == 1
    assert history["policies"][0]["policy_code"] == "safeguarding.selection.review"
    assert history["policies"][0]["latest_task_title"] == "Recommend tournament squad"

    csv_export = client.get(
        f"/api/v1/agents/governance-policy-rules/history/export?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert csv_export["artifact_format"] == "csv"
    assert csv_export["content_type"].startswith("text/csv")
    assert csv_export["download_filename"].endswith(".csv")
    assert csv_export["governed_task_count"] == 1
    assert "safeguarding.selection.review" in csv_export["content"]
    assert csv_export["checksum"]
    assert csv_export["size_bytes"] == len(csv_export["content"].encode())

    markdown_export = client.get(
        f"/api/v1/agents/governance-policy-rules/history/export?organization_id={organization['id']}&artifact_format=markdown",
        headers=identity_headers,
    ).json()
    assert markdown_export["artifact_format"] == "markdown"
    assert markdown_export["download_filename"].endswith(".md")
    assert "AfroLete AI Governance Policy History" in markdown_export["content"]
    assert "Recommend tournament squad" in markdown_export["content"]

    snapshot_response = client.post(
        "/api/v1/agents/governance-policy-rules/history/snapshots",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "artifact_format": "markdown",
            "snapshot_label": "Board review policy history",
            "limit": 120,
        },
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()
    assert snapshot["snapshot_label"] == "Board review policy history"
    assert snapshot["artifact_format"] == "markdown"
    assert snapshot["governed_task_count"] == 1
    assert snapshot["policy_count"] == 1
    assert snapshot["latest_policy_code"] == "safeguarding.selection.review"
    assert snapshot["generated_by_person_id"] is not None
    assert snapshot["checksum"]

    snapshots = client.get(
        f"/api/v1/agents/governance-policy-rules/history/snapshots?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert [item["id"] for item in snapshots] == [snapshot["id"]]
    assert "Recommend tournament squad" in snapshots[0]["content"]


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


async def test_agent_worker_callback_external_event_replay_is_ignored(db_session) -> None:
    organization = Organization(
        name="Agent Callback Club",
        slug="agent-callback-club",
        organization_type=OrganizationType.CLUB,
        primary_sport="football",
    )
    db_session.add(organization)
    await db_session.flush()
    agent = Agent(
        organization_id=organization.id,
        name="Provider Worker",
        kind=AgentKind.OPERATIONS,
        purpose="Execute live provider worker callbacks for governed tasks.",
        model_policy="provider-model",
    )
    db_session.add(agent)
    await db_session.flush()
    task = AgentTask(
        agent_id=agent.id,
        organization_id=organization.id,
        task_type="provider_review",
        title="Review callback replay handling",
        input_ref="provider:event",
    )
    db_session.add(task)
    await db_session.commit()

    first_payload = AgentWorkerCallbackCreate(
        task_id=task.id,
        status=AgentTaskStatus.WAITING_FOR_REVIEW,
        output_ref="agent://provider/output/1",
        review_notes="Provider completed the review.",
        idempotency_key="provider-callback-1",
        external_event_id="provider-event-123",
        raw_payload={"provider": "demo-ai", "sequence": 1},
    )
    accepted_task, duplicate, message, run_record_id = await apply_agent_worker_callback(db_session, first_payload)

    assert accepted_task.id == task.id
    assert duplicate is False
    assert message == "Agent worker callback accepted."
    assert run_record_id is not None
    await db_session.refresh(task)
    assert task.output_ref == "agent://provider/output/1"

    replay_payload = AgentWorkerCallbackCreate(
        task_id=task.id,
        status=AgentTaskStatus.COMPLETED,
        output_ref="agent://provider/output/replayed",
        review_notes="This replay should not mutate the task.",
        idempotency_key="provider-callback-replay-different-key",
        external_event_id="provider-event-123",
        raw_payload={"provider": "demo-ai", "sequence": 2},
    )
    replay_task, replay_duplicate, replay_message, replay_run_record_id = await apply_agent_worker_callback(
        db_session,
        replay_payload,
    )

    assert replay_task.id == task.id
    assert replay_duplicate is True
    assert replay_message == "Duplicate external agent worker event ignored."
    assert replay_run_record_id == run_record_id
    await db_session.refresh(task)
    assert task.status == AgentTaskStatus.WAITING_FOR_REVIEW
    assert task.output_ref == "agent://provider/output/1"

    records = list(
        (
            await db_session.scalars(
                select(AgentRunRecord).where(AgentRunRecord.task_id == task.id).order_by(AgentRunRecord.ledger_sequence)
            )
        ).all()
    )
    assert len(records) == 1
    assert records[0].external_event_id == "provider-event-123"
    assert records[0].callback_payload_hash
    assert records[0].callback_received_at is not None
    assert "provider-event-123" in records[0].governance_notes

    ledger = await verify_agent_run_ledger(db_session, organization.id)
    assert ledger["valid"] is True


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


def test_agent_bias_audit_mitigation_lifecycle_updates_scorecard(client, identity_headers) -> None:
    organization, _ = create_org_and_team(client, identity_headers, "bias-mitigation")
    registry_response = client.post(
        "/api/v1/agents/model-registry",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "model_policy": "selection-recommendation-bias-v1",
            "provider": "local",
            "model_family": "deterministic-governance",
            "version": "2026-05",
            "use_case": "Selection recommendations with age, gender, regional, club, and school bias review.",
            "risk_tier": "high",
            "review_status": "blocked",
            "documentation_url": "https://docs.example.test/selection-bias",
            "evaluation_summary": "Initial model card requires bias mitigation evidence.",
            "bias_notes": "Audit all participant cohorts before release.",
            "data_residency": "tenant-region",
        },
    )
    assert registry_response.status_code == 201
    registry = registry_response.json()

    audit_response = client.post(
        f"/api/v1/agents/model-registry/{registry['id']}/bias-audits",
        headers=identity_headers,
        json={
            "audit_dimension": "age_gender_region_club_school",
            "population_slice": "all-participants",
        },
    )
    assert audit_response.status_code == 201
    audit = audit_response.json()
    assert audit["mitigation_status"] == "open"
    assert audit["mitigation_action"] is None
    assert audit["mitigated_at"] is None

    scorecard_with_open_audit = client.get(
        f"/api/v1/agents/ethical-scorecard?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert scorecard_with_open_audit["open_mitigations"] == 1

    in_progress_response = client.patch(
        f"/api/v1/agents/bias-audits/{audit['id']}/mitigation",
        headers=identity_headers,
        json={
            "mitigation_status": "in_progress",
            "mitigation_action": "Review cohort outcomes and pause recommendations until reviewer approval.",
            "mitigation_evidence_ref": "risk-register:selection-recommendation-bias-v1",
        },
    )
    assert in_progress_response.status_code == 200
    in_progress = in_progress_response.json()
    assert in_progress["mitigation_status"] == "in_progress"
    assert in_progress["mitigated_by_person_id"] is None
    assert in_progress["mitigated_at"] is None

    mitigated_response = client.patch(
        f"/api/v1/agents/bias-audits/{audit['id']}/mitigation",
        headers=identity_headers,
        json={
            "mitigation_status": "mitigated",
            "mitigation_action": "Balanced cohort sampling and required human review for high-impact outputs.",
            "mitigation_evidence_ref": "risk-register:selection-recommendation-bias-v1#mitigated",
        },
    )
    assert mitigated_response.status_code == 200
    mitigated = mitigated_response.json()
    assert mitigated["mitigation_status"] == "mitigated"
    assert mitigated["mitigation_action"].startswith("Balanced cohort sampling")
    assert mitigated["mitigation_evidence_ref"].endswith("#mitigated")
    assert mitigated["mitigated_by_person_id"] is not None
    assert mitigated["mitigated_at"] is not None

    scorecard_after_mitigation = client.get(
        f"/api/v1/agents/ethical-scorecard?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert scorecard_after_mitigation["open_mitigations"] == 0

    registry_after_mitigation = client.get(
        f"/api/v1/agents/model-registry?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()[0]
    assert registry_after_mitigation["review_status"] == "in_review"
