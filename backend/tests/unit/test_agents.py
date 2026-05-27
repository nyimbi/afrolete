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
