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
    assert profile["forecast_scenarios"][0]["metric_name"] == "Pace"
    assert profile["forecast_scenarios"][0]["model_policy"] == "deterministic_forecast_v1"
    assert profile["forecast_scenarios"][0]["data_quality"] == "thin_history"
    assert profile["benchmarks"][0]["cohort_scope"] == "tenant"
    assert profile["benchmarks"][0]["cohort_label"] == "All athletes"
    assert profile["benchmarks"][0]["metric_name"] == "Pace"
    assert len(profile["cohort_comparisons"]) == 4
    assert profile["cohort_comparisons"][0]["cohort_scope"] == "tenant"


def test_performance_benchmarks_can_scope_to_position_cohort(client, identity_headers) -> None:
    organization, team, _, roster = create_rostered_athlete(client, identity_headers)
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
    cohort_entries = [
        ("Forward Peer", "forward-peer@example.com", "Forward", 13.0),
        ("Midfield Peer", "midfield-peer@example.com", "Midfielder", 9.0),
    ]
    for display_name, email, position, value in cohort_entries:
        member = client.post(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=identity_headers,
            json={
                "email": email,
                "display_name": display_name,
                "role": "athlete",
            },
        ).json()
        peer_roster = client.post(
            f"/api/v1/teams/{team['id']}/members",
            headers=identity_headers,
            json={
                "person_id": member["subject_id"],
                "role": "player",
                "status": "active",
                "primary_position": position,
            },
        ).json()
        response = client.post(
            f"/api/v1/performance/athletes/{peer_roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": metric["id"],
                "value": value,
            },
        )
        assert response.status_code == 201
    target = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "value": 12.4,
        },
    )
    assert target.status_code == 201

    response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/benchmarks"
        f"?organization_id={organization['id']}&cohort_scope=position",
        headers=identity_headers,
    )

    assert response.status_code == 200
    benchmark = response.json()[0]
    assert benchmark["cohort_scope"] == "position"
    assert benchmark["cohort_label"] == "Forward"
    assert benchmark["sample_size"] == 2
    assert benchmark["cohort_average"] == 12.7
    assert benchmark["cohort_min"] == 12.4
    assert benchmark["cohort_max"] == 13.0
    assert benchmark["percentile_rank"] == 100.0


def test_performance_benchmarks_can_scope_to_region_cohort(client, identity_headers) -> None:
    organization, team, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "vertical_jump",
            "name": "Vertical Jump",
            "category": "physical",
            "unit": "cm",
            "higher_is_better": True,
        },
    ).json()
    cohort_entries = [
        ("Kenya Peer", "kenya-peer@example.com", "KE", 61),
        ("Uganda Peer", "uganda-peer@example.com", "UG", 80),
    ]
    for display_name, email, country_code, value in cohort_entries:
        member = client.post(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=identity_headers,
            json={
                "email": email,
                "display_name": display_name,
                "country_code": country_code,
                "role": "athlete",
            },
        ).json()
        peer_roster = client.post(
            f"/api/v1/teams/{team['id']}/members",
            headers=identity_headers,
            json={
                "person_id": member["subject_id"],
                "role": "player",
                "status": "active",
                "primary_position": "Forward",
            },
        ).json()
        response = client.post(
            f"/api/v1/performance/athletes/{peer_roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": metric["id"],
                "value": value,
            },
        )
        assert response.status_code == 201
    target = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "value": 62,
        },
    )
    assert target.status_code == 201

    response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/benchmarks"
        f"?organization_id={organization['id']}&cohort_scope=region",
        headers=identity_headers,
    )

    assert response.status_code == 200
    benchmark = response.json()[0]
    assert benchmark["cohort_scope"] == "region"
    assert benchmark["cohort_label"] == "KE"
    assert benchmark["sample_size"] == 2
    assert benchmark["cohort_average"] == 61.5
    assert benchmark["cohort_max"] == 62.0
    assert benchmark["percentile_rank"] == 100.0

    comparison_response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/cohort-comparisons"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert comparison_response.status_code == 200
    comparisons = comparison_response.json()
    assert [comparison["cohort_scope"] for comparison in comparisons] == [
        "tenant",
        "age_group",
        "position",
        "region",
    ]
    region = next(comparison for comparison in comparisons if comparison["cohort_scope"] == "region")
    assert region["cohort_label"] == "KE"
    assert region["metric_count"] == 1
    assert region["sample_size_total"] == 2
    assert region["average_percentile"] == 100.0
    assert region["watch_count"] == 0
    assert region["top_metric_name"] == "Vertical Jump"
    assert region["benchmarks"][0]["cohort_label"] == "KE"


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


def test_performance_forecast_scenarios_project_training_runway(client, identity_headers) -> None:
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
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/forecast-scenarios"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert response.status_code == 200
    scenario = response.json()[0]
    assert scenario["metric_name"] == "Sprint Time"
    assert scenario["sample_size"] == 3
    assert scenario["latest_value"] == 12.0
    assert scenario["forecast_next_value"] == 11.5
    assert scenario["forecast_low"] == 11.0
    assert scenario["forecast_high"] == 12.0
    assert scenario["confidence"] == 0.72
    assert scenario["data_quality"] == "usable_history"
    assert scenario["risk_level"] == "opportunity"
    assert scenario["model_policy"] == "deterministic_forecast_v1"
    assert scenario["projected_points"] == [11.5, 11.0, 10.5, 10.0]
    assert "improving scenario" in scenario["recommendation"]


def test_performance_what_if_forecast_adjusts_training_runway(client, identity_headers) -> None:
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
    for value, observed_at in [
        (13.0, "2026-01-01T10:00:00Z"),
        (12.5, "2026-01-08T10:00:00Z"),
        (12.0, "2026-01-15T10:00:00Z"),
    ]:
        response = client.post(
            f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": metric["id"],
                "value": value,
                "observed_at": observed_at,
            },
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/forecast-scenarios/what-if"
        f"?organization_id={organization['id']}&training_adjustment_percent=20&readiness_score=70&horizon=3",
        headers=identity_headers,
    )

    assert response.status_code == 200
    scenario = response.json()[0]
    assert scenario["scenario_label"] == "+20% load, readiness 70"
    assert scenario["model_policy"] == "deterministic_what_if_forecast_v1"
    assert scenario["training_adjustment_percent"] == 20.0
    assert scenario["readiness_score"] == 70
    assert scenario["horizon"] == 3
    assert scenario["forecast_next_value"] == 11.4
    assert scenario["forecast_low"] == 10.9
    assert scenario["forecast_high"] == 11.9
    assert scenario["projected_points"] == [11.4, 10.8, 10.2]
    assert scenario["risk_level"] == "opportunity"
    assert "20% training adjustment" in scenario["recommendation"]


def test_performance_injury_risk_combines_workload_readiness_and_incidents(
    client,
    identity_headers,
) -> None:
    organization, team, member, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "jump_power",
            "name": "Jump Power",
            "category": "physical",
            "unit": "cm",
            "higher_is_better": True,
        },
    ).json()
    for value in [50, 44]:
        response = client.post(
            f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": metric["id"],
                "value": value,
            },
        )
        assert response.status_code == 201

    session = client.post(
        "/api/v1/training/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "title": "High load conditioning",
            "scheduled_for": "2026-06-03T15:00:00Z",
            "duration_minutes": 75,
            "rpe_target": 7,
        },
    )
    assert session.status_code == 201
    feedback = client.post(
        f"/api/v1/training/sessions/{session.json()['id']}/feedback",
        headers=identity_headers,
        json={
            "athlete_profile_id": roster["athlete_profile_id"],
            "readiness_score": 42,
            "soreness_score": 8,
            "sleep_quality": 4,
            "mood_score": 5,
            "actual_rpe": 10,
            "actual_duration_minutes": 95,
            "completed": True,
        },
    )
    assert feedback.status_code == 201
    incident = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "athlete_person_id": member["subject_id"],
            "incident_type": "injury",
            "severity": "high",
            "occurred_at": "2026-06-04T12:00:00Z",
            "title": "Hamstring tightness",
            "description": "Athlete reported hamstring tightness after conditioning.",
            "medical_follow_up_required": "required",
        },
    )
    assert incident.status_code == 201

    response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/injury-risk"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert response.status_code == 200
    risk = response.json()
    assert risk["model_policy"] == "deterministic_injury_risk_v1"
    assert risk["score"] == 100
    assert risk["risk_band"] == "critical"
    assert risk["latest_readiness_score"] == 42
    assert risk["average_soreness_score"] == 8.0
    assert risk["average_sleep_quality"] == 4.0
    assert risk["latest_load"] == 950.0
    assert risk["open_incident_count"] == 1
    assert risk["declining_metric_count"] == 1
    assert any("open injury" in driver for driver in risk["drivers"])
    assert "medical or safeguarding review" in risk["recommendation"]


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
            "country_code": "KE",
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
