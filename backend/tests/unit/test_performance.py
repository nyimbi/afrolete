def test_performance_achievements_create_in_app_notification(client, identity_headers) -> None:
    organization, _, member, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "finishing",
            "name": "Finishing",
            "category": "technical",
            "unit": "score",
            "min_value": 0,
            "max_value": 10,
        },
    ).json()

    first_observation = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "value": 7,
        },
    )
    assert first_observation.status_code == 201

    goal_response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/goals",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "title": "Raise finishing score",
            "target_value": 9,
            "starts_at": "2026-01-01",
        },
    )
    assert goal_response.status_code == 201
    assert goal_response.json()["status"] == "active"

    improved_observation = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "value": 9,
        },
    )
    assert improved_observation.status_code == 201

    evaluation = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/achievements/evaluate"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert evaluation.status_code == 200
    result = evaluation.json()
    assert result["awarded_count"] == 2
    assert {award["achievement_type"] for award in result["awards"]} == {
        "goal_achieved",
        "personal_best",
    }

    messages = client.get(
        f"/api/v1/communications/messages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert len(messages) == 1
    assert messages[0]["message_type"] == "report"
    assert messages[0]["channel"] == "in_app"
    assert messages[0]["recipient_count"] == 1
    assert "2 performance achievements" in messages[0]["subject"]

    recipients = client.get(
        f"/api/v1/communications/messages/{messages[0]['id']}/recipients",
        headers=identity_headers,
    ).json()
    assert [recipient["person_id"] for recipient in recipients] == [member["subject_id"]]


def create_rostered_athlete(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Performance Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U15 Performance",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "performance-athlete@example.com",
            "display_name": "Performance Athlete",
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
            "primary_position": "Forward",
        },
    ).json()
    return organization, team, member, roster


def test_performance_metric_observation_assessment_and_summary(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)

    metric_response = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "first_touch",
            "name": "First Touch",
            "category": "technical",
            "unit": "score",
            "min_value": 0,
            "max_value": 10,
            "weight": 1.2,
            "description": "Coach rating for first touch quality.",
        },
    )

    assert metric_response.status_code == 201
    metric = metric_response.json()
    assert metric["category"] == "technical"

    observation_response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "value": 8,
            "raw_value": "8/10",
            "source": "coach_evaluation",
            "confidence": 0.91,
            "notes": "Improved under pressure.",
        },
    )

    assert observation_response.status_code == 201
    observation = observation_response.json()
    assert observation["value"] == 8
    assert observation["verification_status"] == "verified"

    assessment_response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/assessments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "physical_score": 70,
            "technical_score": 80,
            "tactical_score": 60,
            "mental_score": 90,
            "summary": "Strong technical day.",
            "recommendations": "Add weak-foot finishing block.",
        },
    )

    assert assessment_response.status_code == 201
    assessment = assessment_response.json()
    assert assessment["overall_score"] == 74.0

    summary = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/summary"
        f"?organization_id={organization['id']}",
    ).json()

    assert summary["latest_overall_score"] == 74.0
    assert summary["rating"] == "good"
    assert summary["observation_count"] == 1
    assert summary["assessment_count"] == 1
    assert summary["latest_assessment_id"] == assessment["id"]


def test_performance_observation_rejects_metric_from_other_organization(
    client, identity_headers
) -> None:
    first_org, _, _, roster = create_rostered_athlete(client, identity_headers)
    second_org = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Other Performance Club", "organization_type": "club"},
    ).json()
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": second_org["id"],
            "code": "pace",
            "name": "Pace",
            "category": "physical",
        },
    ).json()

    response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": first_org["id"],
            "metric_definition_id": metric["id"],
            "value": 7,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Metric not found"
