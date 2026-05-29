from app.core.config import Settings
from app.services import training as training_service


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

    calendar_artifact = client.get(
        (
            f"/api/v1/training/calendar-artifact?organization_id={organization['id']}"
            f"&team_id={team['id']}&starts_at=2026-06-01T00:00:00Z&ends_at=2026-06-30T00:00:00Z"
        ),
        headers=identity_headers,
    ).json()
    assert calendar_artifact["content_type"] == "text/calendar; charset=utf-8"
    assert calendar_artifact["download_filename"].endswith(".ics")
    assert calendar_artifact["session_count"] == 1
    assert calendar_artifact["checksum"]
    assert "BEGIN:VCALENDAR" in calendar_artifact["content"]
    assert "METHOD:PUBLISH" in calendar_artifact["content"]
    assert "SUMMARY:Awareness session" in calendar_artifact["content"]
    assert "DTSTART:20260603T150000Z" in calendar_artifact["content"]
    assert "DTEND:20260603T161500Z" in calendar_artifact["content"]
    assert "Target RPE: 7" in calendar_artifact["content"]

    invalid_range = client.get(
        (
            f"/api/v1/training/calendar-artifact?organization_id={organization['id']}"
            f"&starts_at=2026-06-30T00:00:00Z&ends_at=2026-06-01T00:00:00Z"
        ),
        headers=identity_headers,
    )
    assert invalid_range.status_code == 422
    assert invalid_range.json()["detail"] == "ends_at must be after starts_at"


def test_training_plan_generation_can_use_live_model_provider(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    organization, team, _, roster = create_training_context(client, identity_headers, "Provider Training Club")
    captured = {}

    async def fake_provider(settings, payload, team_context, assessments, observations, next_competition_at, source, load):
        captured["mode"] = settings.training_plan_generation_mode
        captured["model"] = settings.training_plan_generation_model
        captured["team_name"] = team_context.name
        captured["weekly_sessions"] = payload.weekly_sessions
        captured["source"] = source
        captured["load"] = load
        captured["assessment_count"] = len(assessments)
        captured["observation_count"] = len(observations)
        captured["next_competition_at"] = next_competition_at
        return {
            "provider": "webhook",
            "model_policy": "coach-model-v9",
            "status_code": 200,
            "provider_reference": "provider-plan-123",
            "notes": "Live model plan accepted.",
            "payload": {
                "title": "Provider match-week plan",
                "focus_area": "Pressing transitions",
                "source_summary": "Provider used team readiness and competition context.",
                "load_guidance": "Two tactical sessions, one low-load rehearsal.",
                "recovery_protocol": "Hydration, sleep check, and soreness review after every session.",
                "progress_checkpoints": "Review pressing triggers after session 2.",
                "items": [
                    {
                        "day_label": "Day 1",
                        "title": "Pressing trigger rehearsal",
                        "focus_area": "Pressing transitions",
                        "duration_minutes": 70,
                        "intensity": 7,
                        "notes": "Small-sided pressing waves with coach stop points.",
                    },
                    {
                        "day_label": "Day 3",
                        "title": "Recovery rondo",
                        "focus_area": "Load management",
                        "duration_minutes": 35,
                        "intensity": 3,
                        "notes": "Keep it conversational and monitor soreness.",
                    },
                ],
            },
        }

    monkeypatch.setattr(
        training_service,
        "get_settings",
        lambda: Settings(
            training_plan_generation_mode="webhook",
            training_plan_generation_model="coach-model-v9",
            training_plan_generation_webhook_url="https://model.example/training",
            training_plan_generation_webhook_key="secret",
        ),
    )
    monkeypatch.setattr(training_service, "request_training_plan_provider", fake_provider)

    response = client.post(
        "/api/v1/training/plans/generate",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "period_start": "2026-06-01",
            "period_end": "2026-06-07",
            "weekly_sessions": 2,
            "readiness_score": 68,
            "upcoming_competition_weight": 8,
        },
    )

    assert response.status_code == 201
    generated = response.json()
    assert captured["mode"] == "webhook"
    assert captured["team_name"] == "Provider Training Club U17"
    assert captured["weekly_sessions"] == 2
    assert generated["generation_provider"] == "webhook"
    assert generated["model_policy"] == "coach-model-v9"
    assert generated["provider_status_code"] == 200
    assert generated["provider_reference"] == "provider-plan-123"
    assert generated["plan"]["title"] == "Provider match-week plan"
    assert generated["plan"]["source_summary"] == "Provider used team readiness and competition context."
    assert generated["items"][0]["title"] == "Pressing trigger rehearsal"
    assert generated["items"][0]["duration_minutes"] == 70
    assert generated["items"][1]["intensity"] == 3


def test_training_plan_generation_webhook_signature_headers() -> None:
    body = training_service.training_plan_generation_body({"event": "afrolete.training.plan.generate"})
    headers = training_service.training_plan_generation_headers(
        Settings(training_plan_generation_webhook_key="secret"),
        body,
        "secret",
    )

    assert headers["User-Agent"] == "AfroLete-Training-Planner/1.0"
    assert headers["X-Afrolete-Training-Key-Source"] == "env"
    timestamp = headers["X-Afrolete-Training-Timestamp"]
    expected = training_service.training_plan_generation_signature("secret", timestamp, body)
    assert headers["X-Afrolete-Training-Signature"] == expected


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
