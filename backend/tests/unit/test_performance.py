from datetime import UTC, datetime, timedelta


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


def test_player_can_load_own_performance_profile(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "pace",
            "name": "Pace",
            "category": "physical",
            "unit": "seconds",
            "higher_is_better": False,
        },
    ).json()
    observation = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "value": 12.4,
        },
    )
    assert observation.status_code == 201
    assessment = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/assessments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "physical_score": 82,
            "technical_score": 76,
            "tactical_score": 72,
            "mental_score": 79,
        },
    )
    assert assessment.status_code == 201
    goal = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/goals",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "title": "Lower sprint time",
            "target_value": 12.0,
            "starts_at": "2026-01-01",
        },
    )
    assert goal.status_code == 201

    player_headers = {
        "X-Afrolete-Sub": "kc-athlete-1",
        "X-Afrolete-Email": "performance-athlete@example.com",
        "X-Afrolete-Name": "Performance Athlete",
    }
    response = client.get(
        f"/api/v1/performance/my-profiles?organization_id={organization['id']}",
        headers=player_headers,
    )

    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile["athlete_profile_id"] == roster["athlete_profile_id"]
    assert profile["athlete_name"] == "Performance Athlete"
    assert profile["latest_overall_score"] == 76.95
    assert profile["rating"] == "good"
    assert profile["observation_count"] == 1
    assert profile["assessment_count"] == 1
    assert profile["latest_assessment"]["physical_score"] == 82
    assert profile["latest_assessment"]["technical_score"] == 76
    assert profile["latest_assessment"]["tactical_score"] == 72
    assert profile["latest_assessment"]["mental_score"] == 79
    assert profile["active_goal_count"] == 1
    assert profile["award_count"] == 0
    assert profile["goals"][0]["title"] == "Lower sprint time"
    assert profile["observations"][0]["value"] == 12.4
    assert profile["trends"][0]["metric_name"] == "Pace"
    assert profile["trend_series"][0]["metric_name"] == "Pace"
    assert profile["trend_series"][0]["points"][0]["value"] == 12.4
    assert profile["benchmarks"][0]["metric_name"] == "Pace"


def test_performance_trend_series_returns_ordered_points(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "sprint_time",
            "name": "Sprint Time",
            "category": "physical",
            "unit": "seconds",
            "higher_is_better": False,
        },
    ).json()
    for value, observed_at, status in [
        (13.0, "2026-01-01T10:00:00Z", "verified"),
        (12.5, "2026-01-08T10:00:00Z", "verified"),
        (99.0, "2026-01-09T10:00:00Z", "rejected"),
        (12.0, "2026-01-15T10:00:00Z", "verified"),
    ]:
        response = client.post(
            f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": metric["id"],
                "value": value,
                "observed_at": observed_at,
                "verification_status": status,
            },
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/trend-series"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert response.status_code == 200
    series = response.json()[0]
    assert series["metric_name"] == "Sprint Time"
    assert series["sample_size"] == 3
    assert series["latest_value"] == 12.0
    assert series["forecast_next_value"] == 11.5
    assert series["trend_direction"] == "improving"
    assert [point["value"] for point in series["points"]] == [13.0, 12.5, 12.0]
    assert [point["normalized_value"] for point in series["points"]] == [0.0, 50.0, 100.0]


def test_player_can_submit_pending_self_assessment(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    player_headers = {
        "X-Afrolete-Sub": "kc-athlete-1",
        "X-Afrolete-Email": "performance-athlete@example.com",
        "X-Afrolete-Name": "Performance Athlete",
    }

    response = client.post(
        f"/api/v1/performance/my-profiles/{roster['athlete_profile_id']}/self-assessments",
        headers=player_headers,
        json={
            "organization_id": organization["id"],
            "physical_score": 72,
            "technical_score": 75,
            "tactical_score": 68,
            "mental_score": 81,
            "perceived_exertion": 6,
            "effort_rating": 9,
            "summary": "Felt sharp but tired late.",
        },
    )

    assert response.status_code == 201
    assessment = response.json()
    assert assessment["athlete_profile_id"] == roster["athlete_profile_id"]
    assert assessment["overall_score"] == 73.4
    assert assessment["perceived_exertion"] == 6
    assert assessment["effort_rating"] == 9
    assert assessment["verification_status"] == "pending_review"
    assert assessment["summary"] == "Felt sharp but tired late."

    summary = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/summary"
        f"?organization_id={organization['id']}",
    ).json()
    assert summary["latest_overall_score"] is None
    assert summary["assessment_count"] == 1


def test_coach_can_review_player_self_assessment(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    player_headers = {
        "X-Afrolete-Sub": "kc-athlete-1",
        "X-Afrolete-Email": "performance-athlete@example.com",
        "X-Afrolete-Name": "Performance Athlete",
    }
    pending = client.post(
        f"/api/v1/performance/my-profiles/{roster['athlete_profile_id']}/self-assessments",
        headers=player_headers,
        json={
            "organization_id": organization["id"],
            "physical_score": 72,
            "technical_score": 75,
            "tactical_score": 68,
            "mental_score": 81,
            "perceived_exertion": 6,
            "effort_rating": 9,
        },
    ).json()

    queue_response = client.get(
        f"/api/v1/performance/assessments/review-queue?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert len(queue) == 1
    assert queue[0]["athlete_name"] == "Performance Athlete"
    assert queue[0]["assessment"]["id"] == pending["id"]
    assert queue[0]["assessment"]["review_priority"] == "normal"
    assert queue[0]["assessment"]["review_due_at"] is not None
    assert queue[0]["review_sla_state"] in {"due_soon", "on_track"}

    due_at = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    assignment_response = client.patch(
        f"/api/v1/performance/assessments/{pending['id']}/review-assignment",
        headers=identity_headers,
        json={
            "assign_to_self": True,
            "review_due_at": due_at,
            "review_priority": "urgent",
            "review_notes": "Review before the next matchday squad is picked.",
        },
    )
    assert assignment_response.status_code == 200
    assigned = assignment_response.json()
    assert assigned["review_assigned_to_person_id"] is not None
    assert assigned["review_priority"] == "urgent"
    assert assigned["review_notes"] == "Review before the next matchday squad is picked."

    filtered_queue = client.get(
        f"/api/v1/performance/assessments/review-queue?organization_id={organization['id']}"
        "&assignment=mine&sla=overdue&priority=urgent",
        headers=identity_headers,
    ).json()
    assert len(filtered_queue) == 1
    assert filtered_queue[0]["review_assigned_to_name"] == "Owner Example"
    assert filtered_queue[0]["review_sla_state"] == "overdue"
    assert filtered_queue[0]["review_age_hours"] >= 0

    summary = client.get(
        f"/api/v1/performance/assessments/review-summary?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert summary.status_code == 200
    summary_data = summary.json()
    assert summary_data["open_count"] == 1
    assert summary_data["assigned_count"] == 1
    assert summary_data["unassigned_count"] == 0
    assert summary_data["overdue_count"] == 1
    assert summary_data["urgent_count"] == 1
    assert summary_data["priority_counts"]["urgent"] == 1
    assert summary_data["reviewer_loads"][0]["reviewer_name"] == "Owner Example"
    assert summary_data["reviewer_loads"][0]["open_count"] == 1

    unassigned_queue = client.get(
        f"/api/v1/performance/assessments/review-queue?organization_id={organization['id']}"
        "&assignment=unassigned",
        headers=identity_headers,
    ).json()
    assert unassigned_queue == []

    escalation_response = client.post(
        f"/api/v1/performance/assessments/review-escalations?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert escalation_response.status_code == 200
    escalation = escalation_response.json()
    assert escalation["eligible_count"] == 1
    assert escalation["escalated_count"] == 1
    assert escalation["overdue_count"] == 1
    assert escalation["message_ids"]

    messages = client.get(
        f"/api/v1/communications/messages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert any(message["id"] == escalation["message_ids"][0] for message in messages)

    queue_after_escalation = client.get(
        f"/api/v1/performance/assessments/review-queue?organization_id={organization['id']}"
        "&assignment=mine&sla=overdue&priority=urgent",
        headers=identity_headers,
    ).json()
    assert queue_after_escalation[0]["assessment"]["review_escalation_count"] == 1
    assert queue_after_escalation[0]["assessment"]["review_last_escalated_at"] is not None
    assert queue_after_escalation[0]["assessment"]["review_escalation_message_id"] == escalation["message_ids"][0]
    summary_after_escalation = client.get(
        f"/api/v1/performance/assessments/review-summary?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert summary_after_escalation["escalated_count"] == 1
    assert summary_after_escalation["reviewer_loads"][0]["escalated_count"] == 1

    response = client.patch(
        f"/api/v1/performance/assessments/{pending['id']}/review",
        headers=identity_headers,
        json={
            "verification_status": "verified",
            "physical_score": 74,
            "recommendations": "Keep the recovery block and review fatigue next session.",
        },
    )

    assert response.status_code == 200
    reviewed = response.json()
    assert reviewed["verification_status"] == "verified"
    assert reviewed["physical_score"] == 74
    assert reviewed["overall_score"] == 73.9
    assert reviewed["recommendations"] == "Keep the recovery block and review fatigue next session."
    assert reviewed["reviewed_by_person_id"] is not None
    assert reviewed["reviewed_at"] is not None

    summary = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/summary"
        f"?organization_id={organization['id']}",
    ).json()
    assert summary["latest_overall_score"] == 73.9

    queue_after_review = client.get(
        f"/api/v1/performance/assessments/review-queue?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert queue_after_review == []


def test_player_cannot_submit_self_assessment_for_another_athlete(
    client,
    identity_headers,
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    other_headers = {
        "X-Afrolete-Sub": "kc-athlete-2",
        "X-Afrolete-Email": "other-athlete@example.com",
        "X-Afrolete-Name": "Other Athlete",
    }

    response = client.post(
        f"/api/v1/performance/my-profiles/{roster['athlete_profile_id']}/self-assessments",
        headers=other_headers,
        json={
            "organization_id": organization["id"],
            "physical_score": 72,
            "technical_score": 75,
            "tactical_score": 68,
            "mental_score": 81,
            "perceived_exertion": 6,
            "effort_rating": 9,
        },
    )

    assert response.status_code == 403


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
