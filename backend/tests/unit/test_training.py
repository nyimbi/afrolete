def create_training_context(client, identity_headers, name="Training Club"):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": name,
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": f"{name} U17",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": f"{name.lower().replace(' ', '-')}-athlete@example.com",
            "display_name": f"{name} Athlete",
            "role": "athlete",
        },
    ).json()
    roster = client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": member["subject_id"],
            "role": "player",
            "status": "active",
            "primary_position": "Midfielder",
        },
    ).json()
    return organization, team, member, roster


def test_training_drill_plan_item_and_session_workflow(client, identity_headers) -> None:
    organization, team, _, roster = create_training_context(client, identity_headers)

    drill_response = client.post(
        "/api/v1/training/drills",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "name": "Scanning rondo",
            "focus_area": "Awareness",
            "category": "technical",
            "min_age": 12,
            "max_age": 18,
            "equipment": "Cones, bibs, 4 balls",
            "description": "Possession drill requiring shoulder checks before receiving.",
            "coaching_points": "Check both shoulders and open the body before the first touch.",
            "default_duration_minutes": 18,
            "default_intensity": 6,
        },
    )

    assert drill_response.status_code == 201
    drill = drill_response.json()
    assert drill["focus_area"] == "Awareness"

    plan_response = client.post(
        "/api/v1/training/plans",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "title": "Preseason awareness block",
            "focus_area": "Scanning and first touch",
            "period_start": "2026-06-01",
            "period_end": "2026-06-28",
            "ai_generated": True,
            "source_summary": "Based on technical assessment and upcoming tournament.",
            "load_guidance": "Keep acute load below 1.3x the four-week baseline.",
            "recovery_protocol": "Mobility and hydration check after high-intensity sessions.",
            "progress_checkpoints": "Weekly first-touch score and coach review.",
        },
    )

    assert plan_response.status_code == 201
    plan = plan_response.json()
    assert plan["status"] == "draft"
    assert plan["created_by_person_id"] is not None

    item_response = client.post(
        f"/api/v1/training/plans/{plan['id']}/items",
        headers=identity_headers,
        json={
            "drill_id": drill["id"],
            "sequence": 1,
            "day_label": "Week 1 Day 1",
            "title": "Scanning rondo block",
            "focus_area": "Awareness",
            "duration_minutes": 18,
            "intensity": 6,
            "notes": "Progress from 4v2 to 5v2 if tempo stays high.",
        },
    )

    assert item_response.status_code == 201
    item = item_response.json()
    assert item["plan_id"] == plan["id"]
    assert item["drill_id"] == drill["id"]

    session_response = client.post(
        "/api/v1/training/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "plan_id": plan["id"],
            "title": "Awareness session",
            "scheduled_for": "2026-06-03T15:00:00Z",
            "duration_minutes": 75,
            "rpe_target": 7,
            "objectives": "Improve scanning before receiving under pressure.",
        },
    )

    assert session_response.status_code == 201
    session_plan = session_response.json()
    assert session_plan["load_score"] == 525.0
    assert session_plan["status"] == "planned"

    plan_items = client.get(f"/api/v1/training/plans/{plan['id']}/items").json()
    assert [plan_item["id"] for plan_item in plan_items] == [item["id"]]

    sessions = client.get(
        f"/api/v1/training/sessions?organization_id={organization['id']}&team_id={team['id']}"
    ).json()
    assert [session["id"] for session in sessions] == [session_plan["id"]]


def test_training_plan_rejects_team_from_other_organization(client, identity_headers) -> None:
    organization, _, _, roster = create_training_context(client, identity_headers, "First Club")
    _, other_team, _, _ = create_training_context(client, identity_headers, "Other Club")

    response = client.post(
        "/api/v1/training/plans",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": other_team["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "title": "Invalid cross-org plan",
            "focus_area": "Speed",
            "period_start": "2026-06-01",
            "period_end": "2026-06-07",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"


def test_training_session_rejects_event_from_other_organization(client, identity_headers) -> None:
    organization, team, _, _ = create_training_context(client, identity_headers, "Session Club")
    other_organization, other_team, _, _ = create_training_context(
        client,
        identity_headers,
        "Event Club",
    )
    other_event = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": other_organization["id"],
            "team_id": other_team["id"],
            "event_type": "training",
            "title": "Other org training",
            "starts_at": "2026-06-04T15:00:00Z",
        },
    ).json()

    response = client.post(
        "/api/v1/training/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_id": other_event["id"],
            "title": "Invalid event session",
            "scheduled_for": "2026-06-04T15:00:00Z",
            "duration_minutes": 60,
            "rpe_target": 5,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"
