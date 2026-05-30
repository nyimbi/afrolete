import base64
import csv
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import io
import json
import time
from types import SimpleNamespace

import numpy as np

from app.services import performance as performance_service


def test_match_pitch_calibration_uses_perspective_homography_for_trapezoid() -> None:
    points = [
        {"label": "top left", "image_x_percent": 20, "image_y_percent": 10, "pitch_x_meters": 0, "pitch_y_meters": 0},
        {"label": "top right", "image_x_percent": 80, "image_y_percent": 10, "pitch_x_meters": 100, "pitch_y_meters": 0},
        {"label": "bottom right", "image_x_percent": 100, "image_y_percent": 90, "pitch_x_meters": 100, "pitch_y_meters": 50},
        {"label": "bottom left", "image_x_percent": 0, "image_y_percent": 90, "pitch_x_meters": 0, "pitch_y_meters": 50},
    ]

    transform = performance_service.match_pitch_calibration_transform(points, 100, 50)
    calibration = SimpleNamespace(
        transform_json=json.dumps(transform),
        pitch_length_m=100,
        pitch_width_m=50,
    )

    assert transform["method"] == "perspective_homography"
    assert transform["quality_score"] >= 0.9
    assert transform["mean_residual_m"] < 0.001
    assert tuple(round(value, 2) for value in performance_service.apply_match_pitch_calibration(calibration, 20, 10)) == (0.0, 0.0)
    assert tuple(round(value, 2) for value in performance_service.apply_match_pitch_calibration(calibration, 80, 10)) == (100.0, 0.0)
    assert tuple(round(value, 2) for value in performance_service.apply_match_pitch_calibration(calibration, 100, 90)) == (100.0, 50.0)
    assert tuple(round(value, 2) for value in performance_service.apply_match_pitch_calibration(calibration, 0, 90)) == (0.0, 50.0)
    x_meters, y_meters = performance_service.apply_match_pitch_calibration(calibration, 50, 50)
    assert round(x_meters, 2) == 50.0
    assert round(y_meters, 2) == 31.25


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
    organization, team, member, roster = create_rostered_athlete(client, identity_headers)
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
    assert profile["what_if_scenarios"][0]["metric_name"] == "Pace"
    assert profile["what_if_scenarios"][0]["scenario_label"] == "baseline load, readiness 70"
    assert profile["what_if_scenarios"][0]["model_policy"] == "deterministic_what_if_forecast_v1"
    assert (
        profile["injury_risk"]["model_policy"]
        == "deterministic_injury_risk_v4_biomarker_environmental_biomechanical"
    )
    assert profile["injury_risk"]["athlete_profile_id"] == roster["athlete_profile_id"]
    assert profile["injury_risk"]["risk_band"] in {"low", "watch", "high", "critical"}
    assert "No athlete-specific training feedback" in profile["injury_risk"]["drivers"][0]
    assert profile["benchmarks"][0]["cohort_scope"] == "tenant"
    assert profile["benchmarks"][0]["cohort_label"] == "All athletes"
    assert profile["benchmarks"][0]["metric_name"] == "Pace"
    assert len(profile["cohort_comparisons"]) == 4
    assert profile["cohort_comparisons"][0]["cohort_scope"] == "tenant"
    assert profile["match_guidance"] == []

    video = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Player Guidance FC",
            "sport": "football",
            "filename": "player-guidance-fc.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"player match tracking video").decode(),
            "clip_label": "Player guidance match",
            "match_context": "Coach-reviewed tracking for player portal guidance.",
            "analysis_focus": "player-facing match load guidance",
        },
    ).json()
    tracking = client.post(
        f"/api/v1/performance/scouting/videos/{video['id']}/tracking-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "source_provider": "coach_reviewed_tracking",
            "samples": [
                {
                    "track_id": "home-9",
                    "person_id": member["subject_id"],
                    "team_label": "Home",
                    "player_label": "Performance Athlete",
                    "jersey_number": "9",
                    "timestamp_seconds": 0,
                    "x_percent": 10,
                    "y_percent": 50,
                },
                {
                    "track_id": "home-9",
                    "person_id": member["subject_id"],
                    "team_label": "Home",
                    "player_label": "Performance Athlete",
                    "jersey_number": "9",
                    "timestamp_seconds": 1,
                    "x_percent": 19,
                    "y_percent": 50,
                },
                {
                    "track_id": "home-9",
                    "person_id": member["subject_id"],
                    "team_label": "Home",
                    "player_label": "Performance Athlete",
                    "jersey_number": "9",
                    "timestamp_seconds": 2,
                    "x_percent": 28,
                    "y_percent": 50,
                },
                {
                    "track_id": "away-4",
                    "team_label": "Away",
                    "player_label": "Defender",
                    "timestamp_seconds": 1,
                    "x_percent": 18,
                    "y_percent": 51,
                },
            ],
        },
    )
    assert tracking.status_code == 201

    unpublished_profile_response = client.get(
        f"/api/v1/performance/my-profiles?organization_id={organization['id']}",
        headers=player_headers,
    )
    assert unpublished_profile_response.status_code == 200
    assert unpublished_profile_response.json()[0]["match_guidance"] == []

    blocked_followup_response = client.post(
        f"/api/v1/performance/my-profiles/{roster['athlete_profile_id']}/match-guidance/training-followups",
        headers=player_headers,
        json={
            "organization_id": organization["id"],
            "tracking_run_id": tracking.json()["id"],
            "track_id": "home-9",
            "period_start": "2026-03-01",
            "period_end": "2026-03-14",
            "max_items": 2,
        },
    )
    assert blocked_followup_response.status_code == 404

    publish_response = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{tracking.json()['id']}/player-guidance-publish",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "in_app",
            "include_guardians": False,
            "require_publishable": False,
            "subject_prefix": "Published player match guidance",
        },
    )
    assert publish_response.status_code == 201
    published = publish_response.json()
    assert published["message_count"] == 1

    guided_profile_response = client.get(
        f"/api/v1/performance/my-profiles?organization_id={organization['id']}",
        headers=player_headers,
    )
    assert guided_profile_response.status_code == 200
    match_guidance = guided_profile_response.json()[0]["match_guidance"]
    assert len(match_guidance) == 1
    assert match_guidance[0]["tracking_run_id"] == tracking.json()["id"]
    assert match_guidance[0]["guidance_message_id"] == published["messages"][0]["message_id"]
    assert match_guidance[0]["guidance_delivery_status"] == "queued"
    assert match_guidance[0]["guidance_recipient_count"] == 1
    assert match_guidance[0]["opponent_name"] == "Player Guidance FC"
    assert match_guidance[0]["team_label"] == "Home"
    assert match_guidance[0]["jersey_number"] == "9"
    assert match_guidance[0]["distance_m"] > 0
    assert match_guidance[0]["max_speed_mps"] > 0
    assert match_guidance[0]["pressure_applied_count"] >= 1
    assert any("high-speed" in item or "High peak speed" in item for item in match_guidance[0]["player_guidance"])
    assert match_guidance[0]["action_plan"]
    assert {item["focus"] for item in match_guidance[0]["action_plan"]} & {
        "Sprint mechanics and deceleration",
        "Pressing angle and recovery cover",
    }
    assert all(item["drill_recommendation"] for item in match_guidance[0]["action_plan"])
    assert any("Home phase" in item for item in match_guidance[0]["tactical_context"])

    followup_response = client.post(
        f"/api/v1/performance/my-profiles/{roster['athlete_profile_id']}/match-guidance/training-followups",
        headers=player_headers,
        json={
            "organization_id": organization["id"],
            "tracking_run_id": tracking.json()["id"],
            "track_id": "home-9",
            "period_start": "2026-03-01",
            "period_end": "2026-03-14",
            "max_items": 2,
        },
    )
    assert followup_response.status_code == 201
    followup = followup_response.json()
    assert followup["athlete_profile_id"] == roster["athlete_profile_id"]
    assert followup["tracking_run_id"] == tracking.json()["id"]
    assert followup["track_id"] == "home-9"
    assert followup["item_count"] == 2
    assert followup["action_plan"][0]["drill_recommendation"]
    assert followup["agent_task_id"] is not None
    assert followup["agent_task_status"] == "queued"
    assert "Review player match follow-up" in followup["agent_task_title"]

    plan_response = client.get(
        f"/api/v1/training/plans?organization_id={organization['id']}&athlete_profile_id={roster['athlete_profile_id']}",
        headers=identity_headers,
    )
    assert plan_response.status_code == 200
    assert plan_response.json()[0]["id"] == followup["plan_id"]
    assert plan_response.json()[0]["ai_generated"] is True

    items_response = client.get(f"/api/v1/training/plans/{followup['plan_id']}/items", headers=identity_headers)
    assert items_response.status_code == 200
    assert len(items_response.json()) == 2
    assert "Cue:" in items_response.json()[0]["notes"]

    agent_tasks_response = client.get(
        f"/api/v1/agents/tasks?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert agent_tasks_response.status_code == 200
    agent_task = next(task for task in agent_tasks_response.json() if task["id"] == followup["agent_task_id"])
    assert agent_task["task_type"] == "player_match_training_followup_review"
    assert f"plan:{followup['plan_id']}" in agent_task["input_ref"]

    touch_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "first_touch",
            "name": "First Touch",
            "category": "technical",
            "unit": "score",
            "higher_is_better": True,
        },
    ).json()
    for value, observed_at in [
        (66.0, "2026-02-01T10:00:00Z"),
        (74.0, "2026-02-20T10:00:00Z"),
    ]:
        response = client.post(
            f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": touch_metric["id"],
                "value": value,
                "observed_at": observed_at,
                "verification_status": "verified",
            },
        )
        assert response.status_code == 201

    filtered_response = client.get(
        f"/api/v1/performance/my-profiles?organization_id={organization['id']}"
        "&trend_category=technical&trend_metric_code=FIRST_TOUCH"
        "&trend_period_start=2026-02-15&trend_period_end=2026-02-28"
        "&what_if_training_adjustment_percent=15&what_if_readiness_score=82&what_if_horizon=3",
        headers=player_headers,
    )
    assert filtered_response.status_code == 200
    filtered_profile = filtered_response.json()[0]
    assert [trend["metric_code"] for trend in filtered_profile["trends"]] == ["first_touch"]
    assert filtered_profile["trends"][0]["filter_category"] == "technical"
    assert filtered_profile["trends"][0]["filter_metric_code"] == "first_touch"
    assert filtered_profile["trends"][0]["period_start"] == "2026-02-15"
    assert filtered_profile["trends"][0]["sample_size"] == 1
    assert [series["metric_code"] for series in filtered_profile["trend_series"]] == ["first_touch"]
    assert [point["value"] for point in filtered_profile["trend_series"][0]["points"]] == [74.0]
    assert [scenario["metric_code"] for scenario in filtered_profile["what_if_scenarios"]] == ["first_touch"]
    assert filtered_profile["what_if_scenarios"][0]["scenario_label"] == "+15% load, readiness 82"
    assert filtered_profile["what_if_scenarios"][0]["horizon"] == 3


def test_family_portal_shows_only_guardian_copied_match_guidance(client, identity_headers) -> None:
    organization, team, member, _ = create_rostered_athlete(client, identity_headers)
    guardian_response = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": member["subject_id"],
            "guardian_email": "family-guidance-parent@example.com",
            "guardian_display_name": "Family Guidance Parent",
            "relationship_kind": "parent",
            "can_sign_consent": True,
            "emergency_contact": True,
        },
    )
    assert guardian_response.status_code == 201
    guardian = guardian_response.json()
    guardian_headers = {
        "X-Afrolete-Sub": "kc-family-guidance-parent",
        "X-Afrolete-Email": "family-guidance-parent@example.com",
        "X-Afrolete-Name": "Family Guidance Parent",
    }
    unrelated_guardian_headers = {
        "X-Afrolete-Sub": "kc-unrelated-family-guidance-parent",
        "X-Afrolete-Email": "unrelated-family-guidance-parent@example.com",
        "X-Afrolete-Name": "Unrelated Family Guidance Parent",
    }

    video_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Guardian Shared FC",
            "sport": "football",
            "filename": "guardian-shared-fc.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"guardian shared match video").decode(),
            "clip_label": "Guardian shared match",
            "match_context": "Coach-reviewed tracking for family-visible guidance.",
            "analysis_focus": "guardian match guidance visibility",
        },
    )
    assert video_response.status_code == 201
    video = video_response.json()
    tracking_response = client.post(
        f"/api/v1/performance/scouting/videos/{video['id']}/tracking-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "source_provider": "coach_reviewed_tracking",
            "samples": [
                {
                    "track_id": "home-11",
                    "person_id": member["subject_id"],
                    "team_label": "Home",
                    "player_label": "Performance Athlete",
                    "jersey_number": "11",
                    "timestamp_seconds": 0,
                    "x_percent": 10,
                    "y_percent": 50,
                },
                {
                    "track_id": "home-11",
                    "person_id": member["subject_id"],
                    "team_label": "Home",
                    "player_label": "Performance Athlete",
                    "jersey_number": "11",
                    "timestamp_seconds": 1,
                    "x_percent": 20,
                    "y_percent": 50,
                },
                {
                    "track_id": "home-11",
                    "person_id": member["subject_id"],
                    "team_label": "Home",
                    "player_label": "Performance Athlete",
                    "jersey_number": "11",
                    "timestamp_seconds": 2,
                    "x_percent": 30,
                    "y_percent": 50,
                },
            ],
        },
    )
    assert tracking_response.status_code == 201
    tracking = tracking_response.json()

    family_before_publish = client.get(
        f"/api/v1/safeguarding/my-family/match-guidance?organization_id={organization['id']}",
        headers=guardian_headers,
    )
    assert family_before_publish.status_code == 200
    assert family_before_publish.json() == []

    player_only_publish = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/player-guidance-publish",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "in_app",
            "include_guardians": False,
            "require_publishable": False,
            "subject_prefix": "Player-only guidance",
        },
    )
    assert player_only_publish.status_code == 201
    assert player_only_publish.json()["recipient_count"] == 1
    family_after_player_only_publish = client.get(
        f"/api/v1/safeguarding/my-family/match-guidance?organization_id={organization['id']}",
        headers=guardian_headers,
    )
    assert family_after_player_only_publish.status_code == 200
    assert family_after_player_only_publish.json() == []

    guardian_publish = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/player-guidance-publish",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "in_app",
            "include_guardians": True,
            "require_publishable": False,
            "subject_prefix": "Family-copied guidance",
        },
    )
    assert guardian_publish.status_code == 201
    published = guardian_publish.json()
    assert published["recipient_count"] == 2

    family_response = client.get(
        f"/api/v1/safeguarding/my-family/match-guidance?organization_id={organization['id']}",
        headers=guardian_headers,
    )
    assert family_response.status_code == 200
    guidance = family_response.json()
    assert len(guidance) == 1
    assert guidance[0]["athlete_person_id"] == member["subject_id"]
    assert guidance[0]["athlete_name"] == "Performance Athlete"
    assert guidance[0]["relationship"] == guardian["relationship"]
    assert guidance[0]["tracking_run_id"] == tracking["id"]
    assert guidance[0]["guidance_message_id"] == published["messages"][0]["message_id"]
    assert guidance[0]["guidance_recipient_id"]
    assert guidance[0]["guidance_delivery_status"] == "queued"
    assert guidance[0]["guidance_recipient_count"] == 2
    assert guidance[0]["opponent_name"] == "Guardian Shared FC"
    assert guidance[0]["jersey_number"] == "11"
    assert guidance[0]["distance_m"] > 0
    assert guidance[0]["player_guidance"]
    assert guidance[0]["action_plan"]

    read_response = client.post(
        f"/api/v1/communications/inbox/{guidance[0]['guidance_recipient_id']}/read",
        headers=guardian_headers,
    )
    assert read_response.status_code == 200
    assert read_response.json()["delivery_status"] == "read"
    family_after_read_response = client.get(
        f"/api/v1/safeguarding/my-family/match-guidance?organization_id={organization['id']}",
        headers=guardian_headers,
    )
    assert family_after_read_response.status_code == 200
    assert family_after_read_response.json()[0]["guidance_delivery_status"] == "read"

    unrelated_response = client.get(
        f"/api/v1/safeguarding/my-family/match-guidance?organization_id={organization['id']}",
        headers=unrelated_guardian_headers,
    )
    assert unrelated_response.status_code == 200
    assert unrelated_response.json() == []


def test_athlete_pathway_projection_builds_recruiting_roadmap(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metrics = [
        ("pace", "Pace", "physical", 88),
        ("first_touch", "First Touch", "technical", 84),
        ("decision_speed", "Decision Speed", "tactical", 79),
        ("composure", "Composure", "mental", 82),
    ]
    metric_ids = []
    for code, name, category, value in metrics:
        metric = client.post(
            "/api/v1/performance/metrics",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "sport": "football",
                "code": code,
                "name": name,
                "category": category,
                "unit": "score",
                "min_value": 0,
                "max_value": 100,
                "higher_is_better": True,
            },
        ).json()
        metric_ids.append(metric["id"])
        response = client.post(
            f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": metric["id"],
                "value": value,
                "observed_at": "2026-03-01T10:00:00Z",
                "verification_status": "verified",
            },
        )
        assert response.status_code == 201
    assessment = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/assessments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "physical_score": 88,
            "technical_score": 84,
            "tactical_score": 79,
            "mental_score": 82,
            "summary": "External pathway readiness baseline.",
        },
    )
    assert assessment.status_code == 201

    projection_response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/pathway-projections",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "primary_position": "Forward",
            "academic_gpa": 3.7,
            "graduation_year": 2028,
            "target_pathway": "college_scholarship",
            "preferred_regions": ["Kenya", "East Africa", "NCAA Division II"],
            "recruiting_profile_url": "https://profiles.afrolete.local/performance-athlete",
            "notes": "Prioritize verified scout sharing.",
            "share_with_guardians": True,
        },
    )

    assert projection_response.status_code == 201
    projection = projection_response.json()
    assert projection["athlete_name"] == "Performance Athlete"
    assert projection["model_policy"] == "deterministic_pathway_projection_v1"
    assert projection["primary_position"] == "Forward"
    assert projection["readiness_score"] >= 80
    assert projection["projected_level"] in {
        "college_recruit",
        "semi_pro_candidate",
        "professional_prospect",
    }
    assert projection["college_fit_score"] >= 80
    assert projection["pathway_options"][0]["pathway"] == "college_scholarship"
    assert projection["milestones"]
    assert any("highlight" in milestone["title"].lower() for milestone in projection["milestones"])
    assert any("consent" in action.lower() for action in projection["scout_actions"])
    assert projection["evidence"]["observation_count"] == len(metrics)
    assert projection["evidence"]["assessment_count"] == 1
    assert "Guardian-sharing requested" in " ".join(projection["risk_flags"])

    list_response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/pathway-projections"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert list_response.status_code == 200
    projections = list_response.json()
    assert projections[0]["id"] == projection["id"]
    assert projections[0]["pathway_options"][0]["next_actions"]
    assert len(metric_ids) == len(metrics)


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


def test_performance_benchmarks_can_scope_to_association_region_cohorts(
    client, identity_headers
) -> None:
    organization, target_team, _, target_roster = create_rostered_athlete(client, identity_headers)
    local_association = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Nairobi Central Youth League",
            "organization_type": "association",
            "association_level": "local",
            "country_code": "KE",
        },
    ).json()
    regional_association = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Greater Nairobi Football Region",
            "organization_type": "association",
            "association_level": "regional",
            "country_code": "KE",
        },
    ).json()
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "sprint_speed",
            "name": "Sprint Speed",
            "category": "physical",
            "unit": "km/h",
            "higher_is_better": True,
        },
    ).json()

    def create_peer(team_name: str, display_name: str, email: str, value: float):
        team = client.post(
            "/api/v1/teams",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "name": team_name,
                "sport": "football",
                "sport_format": "team",
            },
        ).json()
        member = client.post(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=identity_headers,
            json={
                "email": email,
                "display_name": display_name,
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
            },
        ).json()
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
        return team, roster

    local_peer_team, _ = create_peer(
        "Central Peer U15",
        "Central Peer",
        "central-peer@example.com",
        61,
    )
    regional_peer_team, _ = create_peer(
        "Regional Peer U15",
        "Regional Peer",
        "regional-peer@example.com",
        80,
    )
    create_peer("Outside Peer U15", "Outside Peer", "outside-peer@example.com", 90)
    target_observation = client.post(
        f"/api/v1/performance/athletes/{target_roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": metric["id"],
            "value": 65,
        },
    )
    assert target_observation.status_code == 201

    for association, team in [
        (local_association, target_team),
        (local_association, local_peer_team),
        (regional_association, target_team),
        (regional_association, local_peer_team),
        (regional_association, regional_peer_team),
    ]:
        add_response = client.post(
            f"/api/v1/organizations/{association['id']}/members",
            headers=identity_headers,
            json={
                "subject_type": "team",
                "subject_id": team["id"],
                "role": "viewer",
                "title": "Registered cohort team",
            },
        )
        assert add_response.status_code == 201

    local_response = client.get(
        f"/api/v1/performance/athletes/{target_roster['athlete_profile_id']}/benchmarks"
        f"?organization_id={organization['id']}&cohort_scope=local_association",
        headers=identity_headers,
    )
    regional_response = client.get(
        f"/api/v1/performance/athletes/{target_roster['athlete_profile_id']}/benchmarks"
        f"?organization_id={organization['id']}&cohort_scope=regional_association",
        headers=identity_headers,
    )
    comparisons_response = client.get(
        f"/api/v1/performance/athletes/{target_roster['athlete_profile_id']}/cohort-comparisons"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert local_response.status_code == 200
    local = local_response.json()[0]
    assert local["cohort_scope"] == "local_association"
    assert local["cohort_label"] == "Nairobi Central Youth League"
    assert local["sample_size"] == 2
    assert local["cohort_average"] == 63.0
    assert local["cohort_max"] == 65.0

    assert regional_response.status_code == 200
    regional = regional_response.json()[0]
    assert regional["cohort_scope"] == "regional_association"
    assert regional["cohort_label"] == "Greater Nairobi Football Region"
    assert regional["sample_size"] == 3
    assert regional["cohort_average"] == 68.67
    assert regional["cohort_max"] == 80.0

    assert comparisons_response.status_code == 200
    assert [comparison["cohort_scope"] for comparison in comparisons_response.json()] == [
        "tenant",
        "age_group",
        "position",
        "region",
        "local_association",
        "regional_association",
    ]


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
    passing_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "pass_accuracy",
            "name": "Pass Accuracy",
            "category": "technical",
            "unit": "percent",
            "higher_is_better": True,
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
    response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "metric_definition_id": passing_metric["id"],
            "value": 81.0,
            "observed_at": "2026-01-12T10:00:00Z",
            "verification_status": "verified",
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

    filtered_trend_response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/trends"
        f"?organization_id={organization['id']}&period_start=2026-01-08&period_end=2026-01-15",
        headers=identity_headers,
    )
    filtered_series_response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/trend-series"
        f"?organization_id={organization['id']}&period_end=2026-01-08",
        headers=identity_headers,
    )
    category_filtered_response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/trends"
        f"?organization_id={organization['id']}&category=technical",
        headers=identity_headers,
    )
    metric_filtered_response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/trend-series"
        f"?organization_id={organization['id']}&metric_code=SPRINT_TIME",
        headers=identity_headers,
    )
    invalid_period_response = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/trends"
        f"?organization_id={organization['id']}&period_start=2026-01-15&period_end=2026-01-08",
        headers=identity_headers,
    )

    assert filtered_trend_response.status_code == 200
    filtered_trend = filtered_trend_response.json()[0]
    assert filtered_trend["period_start"] == "2026-01-08"
    assert filtered_trend["period_end"] == "2026-01-15"
    assert filtered_trend["sample_size"] == 2
    assert filtered_trend["first_value"] == 12.5
    assert filtered_trend["latest_value"] == 12.0
    assert filtered_trend["trend_direction"] == "improving"

    assert filtered_series_response.status_code == 200
    filtered_series = filtered_series_response.json()[0]
    assert filtered_series["period_start"] is None
    assert filtered_series["period_end"] == "2026-01-08"
    assert filtered_series["sample_size"] == 2
    assert [point["value"] for point in filtered_series["points"]] == [13.0, 12.5]
    assert category_filtered_response.status_code == 200
    category_filtered = category_filtered_response.json()
    assert [trend["metric_code"] for trend in category_filtered] == ["pass_accuracy"]
    assert category_filtered[0]["filter_category"] == "technical"
    assert category_filtered[0]["filter_metric_code"] is None
    assert category_filtered[0]["sample_size"] == 1
    assert metric_filtered_response.status_code == 200
    metric_filtered = metric_filtered_response.json()
    assert [series["metric_code"] for series in metric_filtered] == ["sprint_time"]
    assert metric_filtered[0]["filter_category"] is None
    assert metric_filtered[0]["filter_metric_code"] == "sprint_time"
    assert [point["value"] for point in metric_filtered[0]["points"]] == [13.0, 12.5, 12.0]
    assert invalid_period_response.status_code == 422


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


def test_performance_forecast_scenarios_use_signed_model_webhook(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    performance_service.get_settings.cache_clear()
    monkeypatch.setenv("AFROLETE_PERFORMANCE_FORECAST_MODE", "webhook")
    monkeypatch.setenv("AFROLETE_PERFORMANCE_FORECAST_MODEL", "afrolete-live-forecaster-v2")
    monkeypatch.setenv("AFROLETE_PERFORMANCE_FORECAST_WEBHOOK_URL", "https://models.example/forecast")
    monkeypatch.setenv("AFROLETE_PERFORMANCE_FORECAST_WEBHOOK_KEY", "forecast-secret")
    performance_service.get_settings.cache_clear()
    calls: list[dict[str, object]] = []

    class FakeAsyncClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(
            self,
            url: str,
            content: bytes,
            headers: dict[str, str],
        ) -> performance_service.httpx.Response:
            calls.append({"url": url, "content": content, "headers": headers, "timeout": self.timeout})
            return performance_service.httpx.Response(
                200,
                request=performance_service.httpx.Request("POST", url),
                json={
                    "model": "provider-forecast-v7",
                    "forecast_next_value": 11.2,
                    "forecast_low": 10.8,
                    "forecast_high": 11.7,
                    "confidence": 0.88,
                    "data_quality": "model_assisted",
                    "risk_level": "high_upside",
                    "projected_points": [11.2, 10.9, 10.6],
                    "recommendation": "Provider model expects a sharper sprint-time improvement window.",
                },
            )

    monkeypatch.setattr(performance_service.httpx, "AsyncClient", FakeAsyncClient)
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
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/forecast-scenarios"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert response.status_code == 200
    scenario = response.json()[0]
    assert scenario["model_policy"] == "provider-forecast-v7"
    assert scenario["forecast_next_value"] == 11.2
    assert scenario["forecast_low"] == 10.8
    assert scenario["forecast_high"] == 11.7
    assert scenario["confidence"] == 0.88
    assert scenario["data_quality"] == "model_assisted"
    assert scenario["risk_level"] == "high_upside"
    assert scenario["projected_points"] == [11.2, 10.9, 10.6]
    assert "sharper sprint-time" in scenario["recommendation"]
    assert calls[0]["url"] == "https://models.example/forecast"
    headers = calls[0]["headers"]
    assert isinstance(headers, dict)
    assert headers["X-Afrolete-Performance-Forecast-Signature"].startswith("sha256=")
    payload = json.loads(calls[0]["content"])
    assert payload["event"] == "afrolete.performance.forecast"
    assert payload["metric"]["code"] == "sprint_time"
    assert payload["deterministic_baseline"]["forecast_next_value"] == 11.5
    performance_service.get_settings.cache_clear()


def test_performance_forecast_validation_persists_drift_run(client, identity_headers) -> None:
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
        (11.6, "2026-01-22T10:00:00Z"),
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

    response = client.post(
        "/api/v1/performance/forecast-validation-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
        },
    )

    assert response.status_code == 201
    run = response.json()
    assert run["model_policy"] == "deterministic_forecast_v1_backtest"
    assert run["forecast_mode"] == "off"
    assert run["metric_count"] == 1
    assert run["evaluated_count"] == 1
    assert run["passed_count"] == 1
    assert run["drift_count"] == 0
    assert run["drift_level"] == "stable"
    assert run["mean_absolute_error"] == 0.1
    assert run["details"][0]["metric_code"] == "sprint_time"
    assert run["details"][0]["sample_size"] == 3
    assert run["details"][0]["predicted_value"] == 11.5
    assert run["details"][0]["actual_value"] == 11.6
    assert run["details"][0]["passed"] is True
    assert run["details"][0]["drifted"] is False

    list_response = client.get(
        f"/api/v1/performance/forecast-validation-runs?organization_id={organization['id']}"
        f"&athlete_profile_id={roster['athlete_profile_id']}",
        headers=identity_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == run["id"]


def test_performance_forecast_validation_alerts_managers_on_drift(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "power_score",
            "name": "Power Score",
            "category": "physical",
            "unit": "score",
            "higher_is_better": True,
        },
    ).json()
    for value, observed_at in [
        (10.0, "2026-01-01T10:00:00Z"),
        (10.0, "2026-01-08T10:00:00Z"),
        (10.0, "2026-01-15T10:00:00Z"),
        (30.0, "2026-01-22T10:00:00Z"),
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

    run_response = client.post(
        "/api/v1/performance/forecast-validation-runs",
        headers=identity_headers,
        json={"organization_id": organization["id"]},
    )
    assert run_response.status_code == 201
    run = run_response.json()
    assert run["drift_level"] == "high"
    assert run["drift_count"] == 1

    alert_response = client.post(
        f"/api/v1/performance/forecast-validation-runs/{run['id']}/alerts"
        "?channels=in_app&channels=sms",
        headers=identity_headers,
    )

    assert alert_response.status_code == 200
    alert = alert_response.json()
    assert alert["sent"] is True
    assert alert["drift_level"] == "high"
    assert alert["channel_count"] == 2
    assert len(alert["message_ids"]) == 2
    assert alert["validation_run"]["id"] == run["id"]
    messages = client.get(
        f"/api/v1/communications/messages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    message = next(message for message in messages if message["id"] == alert["message_ids"][0])
    assert message["urgent"] is True
    assert "forecast drift high" in message["subject"]
    recipients = client.get(
        f"/api/v1/communications/messages/{alert['message_ids'][0]}/recipients",
        headers=identity_headers,
    ).json()
    assert recipients

    duplicate = client.post(
        f"/api/v1/performance/forecast-validation-runs/{run['id']}/alerts",
        headers=identity_headers,
    ).json()
    assert duplicate["sent"] is False
    assert "already sent" in duplicate["skipped_reason"]


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

    for code, name, unit, value in [
        ("hrv", "Heart Rate Variability", "ms", 32),
        ("resting_heart_rate", "Resting Heart Rate", "bpm", 102),
        ("recovery_score", "Wearable Recovery Score", "score", 42),
        ("hydration_score", "Hydration Score", "score", 64),
    ]:
        biomarker_metric = client.post(
            "/api/v1/performance/metrics",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "sport": "football",
                "code": code,
                "name": name,
                "category": "wellness",
                "unit": unit,
                "higher_is_better": code != "resting_heart_rate",
            },
        ).json()
        response = client.post(
            f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": biomarker_metric["id"],
                "value": value,
                "source": "wearable",
                "observed_at": "2026-06-03T09:00:00Z",
            },
        )
        assert response.status_code == 201

    for code, name, unit, value, higher_is_better in [
        ("movement_asymmetry", "Movement Asymmetry", "percent", 18, False),
        ("landing_quality", "Landing Mechanics Quality", "score", 42, True),
    ]:
        video_metric = client.post(
            "/api/v1/performance/metrics",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "sport": "football",
                "code": code,
                "name": name,
                "category": "physical",
                "unit": unit,
                "higher_is_better": higher_is_better,
            },
        ).json()
        response = client.post(
            f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "metric_definition_id": video_metric["id"],
                "value": value,
                "source": "video_analysis",
                "observed_at": "2026-06-03T10:00:00Z",
            },
        )
        assert response.status_code == 201

    facility = client.post(
        "/api/v1/assets/facilities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Main Field",
            "facility_type": "field",
            "sport": "football",
            "surface": "wet uneven natural grass",
            "capacity": 500,
            "condition": "poor",
        },
    )
    assert facility.status_code == 201
    event = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_type": "training",
            "title": "Storm training block",
            "starts_at": "2026-06-03T15:00:00Z",
            "ends_at": "2026-06-03T16:30:00Z",
            "venue_name": "Main Field",
        },
    )
    assert event.status_code == 201
    weather = client.post(
        f"/api/v1/events/{event.json()['id']}/weather-assessments",
        headers=identity_headers,
        json={
            "source": "manual",
            "observed_at": "2026-06-03T14:30:00Z",
            "wbgt_c": 33,
            "lightning_distance_km": 9,
            "precipitation_mm_per_hr": 18,
            "notes": "Storm cell and wet pitch before conditioning.",
        },
    )
    assert weather.status_code == 201
    session = client.post(
        "/api/v1/training/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_id": event.json()["id"],
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
    assert risk["model_policy"] == "deterministic_injury_risk_v4_biomarker_environmental_biomechanical"
    assert risk["score"] == 100
    assert risk["risk_band"] == "critical"
    assert risk["latest_readiness_score"] == 42
    assert risk["average_soreness_score"] == 8.0
    assert risk["average_sleep_quality"] == 4.0
    assert risk["latest_load"] == 950.0
    assert risk["open_incident_count"] == 1
    assert risk["declining_metric_count"] == 1
    assert risk["latest_weather_alert_level"] == "critical"
    assert risk["weather_alert_count"] == 1
    assert risk["hazardous_surface_count"] == 1
    assert risk["environmental_risk_count"] == 2
    assert risk["surface_risk_labels"] == ["uneven surface"]
    assert risk["wearable_observation_count"] == 4
    assert risk["biomarker_risk_count"] == 4
    assert risk["latest_hrv"] == 32.0
    assert risk["latest_resting_heart_rate"] == 102.0
    assert risk["latest_recovery_score"] == 42.0
    assert risk["latest_hydration_score"] == 64.0
    assert risk["biomechanical_observation_count"] == 2
    assert risk["biomechanical_risk_count"] == 2
    assert risk["latest_movement_quality_score"] == 42.0
    assert risk["latest_asymmetry_score"] == 18.0
    assert any("low HRV" in label for label in risk["wearable_risk_labels"])
    assert any("movement asymmetry" in label for label in risk["video_risk_labels"])
    assert any("landing mechanics" in label for label in risk["video_risk_labels"])
    assert any("open injury" in driver for driver in risk["drivers"])
    assert any("weather risk" in driver for driver in risk["drivers"])
    assert any("surface risk" in driver for driver in risk["drivers"])
    assert any("wearable biomarker" in driver for driver in risk["drivers"])
    assert any("biomechanical video" in driver for driver in risk["drivers"])
    assert "medical or safeguarding review" in risk["recommendation"]

    scan_response = client.post(
        f"/api/v1/performance/injury-risk/alert-scans"
        f"?organization_id={organization['id']}&channels=in_app&channels=sms&channels=whatsapp",
        headers=identity_headers,
    )

    assert scan_response.status_code == 200
    scan = scan_response.json()
    assert scan["eligible_count"] == 1
    assert scan["scanned_count"] == 1
    assert scan["high_risk_count"] == 1
    assert scan["alerted_count"] == 1
    assert scan["channels"] == ["in_app", "sms", "whatsapp"]
    assert scan["channel_count"] == 3
    assert scan["message_ids"]
    assert len(scan["message_ids"]) == 3
    messages = client.get(
        f"/api/v1/communications/messages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    message = next(message for message in messages if message["id"] == scan["message_ids"][0])
    assert message["urgent"] is True
    assert "injury risk" in message["subject"]
    recipients = client.get(
        f"/api/v1/communications/messages/{scan['message_ids'][0]}/recipients",
        headers=identity_headers,
    ).json()
    recipient_ids = {recipient["person_id"] for recipient in recipients}
    assert member["subject_id"] in recipient_ids

    alert_response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/injury-risk/alerts"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert alert_response.status_code == 200
    alert = alert_response.json()
    assert alert["sent"] is False
    assert alert["score"] == 100
    assert alert["risk_band"] == "critical"
    assert alert["recipient_count"] >= 2
    assert "already sent" in alert["skipped_reason"]


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


def test_performance_ingestion_parses_structured_wearable_payload(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "recovery_score",
            "name": "Recovery Score",
            "category": "wellness",
            "unit": "score",
            "min_value": 0,
            "max_value": 100,
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "wearable",
            "evidence_ref": "whoop://recovery/2026-06-03",
            "evidence_text": json.dumps(
                {
                    "provider": "whoop",
                    "athlete_id": "wearable-athlete-1",
                    "metrics": [
                        {"code": "resting_heart_rate", "value": 98, "unit": "bpm"},
                        {
                            "code": "recovery_score",
                            "value": 42,
                            "unit": "score",
                            "confidence": 0.91,
                            "observed_at": "2026-06-03T09:15:00Z",
                        },
                    ],
                }
            ),
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["observation"]["value"] == 42
    assert ingestion["observation"]["source"] == "wearable"
    assert ingestion["observation"]["verification_status"] == "pending_review"
    assert ingestion["observation"]["observed_at"].startswith("2026-06-03T09:15:00")
    assert ingestion["confidence"] == 0.91
    assert ingestion["parser_method"] == "structured_provider_payload"
    assert ingestion["parsed_fields"]["code"] == "recovery_score"
    assert ingestion["parser_warnings"] == []


def test_performance_ingestion_normalizes_whoop_recovery_schema(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "hrv",
            "name": "Heart Rate Variability",
            "category": "wellness",
            "unit": "ms",
            "min_value": 0,
            "max_value": 200,
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "wearable",
            "evidence_ref": "wearable://cycle/2026-06-04",
            "source_provider": "whoop",
            "evidence_text": json.dumps(
                {
                    "recovery": {
                        "score": 41,
                        "hrv_rmssd_milli": 32,
                        "resting_heart_rate": 101,
                    },
                    "strain": {"score": 17.4},
                    "created_at": "2026-06-04T06:30:00Z",
                }
            ),
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["source_provider"] == "whoop"
    assert ingestion["observation"]["value"] == 32
    assert ingestion["parser_method"] == "whoop_provider_schema"
    assert ingestion["parsed_fields"]["source_path"] == "recovery.hrv"
    assert ingestion["observation"]["observed_at"].startswith("2026-06-04T06:30:00")


def test_performance_ingestion_normalizes_garmin_wellness_schema(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "stress",
            "name": "Stress Score",
            "category": "wellness",
            "unit": "score",
            "min_value": 0,
            "max_value": 100,
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "wearable",
            "evidence_ref": "garmin://wellness/daily/2026-06-04",
            "evidence_text": json.dumps(
                {
                    "summaryType": "daily",
                    "calendarDate": "2026-06-04",
                    "wellnessData": {
                        "restingHeartRate": 92,
                        "averageStressLevel": 76,
                        "bodyBatteryMostRecentValue": 39,
                    },
                }
            ),
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["source_provider"] == "garmin"
    assert ingestion["observation"]["value"] == 76
    assert ingestion["parser_method"] == "garmin_provider_schema"
    assert ingestion["parser_confidence_reason"].startswith("Normalized a garmin")


def test_performance_ingestion_normalizes_polar_hrv_schema(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "hrv",
            "name": "Heart Rate Variability",
            "category": "wellness",
            "unit": "ms",
            "min_value": 0,
            "max_value": 200,
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "wearable",
            "evidence_ref": "polar://nightly-recharge/2026-06-05",
            "evidence_text": json.dumps(
                {
                    "provider": "polar",
                    "date": "2026-06-05",
                    "heart_rate": {"resting": 82, "average": 143},
                    "hrv": {"rmssd": 47},
                    "sleep": {"duration_minutes": 418, "score": 81},
                }
            ),
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["source_provider"] == "polar"
    assert ingestion["observation"]["value"] == 47
    assert ingestion["parser_method"] == "polar_provider_schema"
    assert ingestion["parsed_fields"]["source_path"] == "hrv.rmssd"


def test_performance_ingestion_normalizes_oura_sleep_schema(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "sleep_minutes",
            "name": "Sleep Minutes",
            "category": "wellness",
            "unit": "minutes",
            "min_value": 0,
            "max_value": 900,
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "wearable",
            "evidence_ref": "oura://daily-sleep/2026-06-05",
            "evidence_text": json.dumps(
                {
                    "provider": "oura",
                    "day": "2026-06-05",
                    "readiness": {"score": 82, "average_hrv": 49, "resting_heart_rate": 57},
                    "sleep": {"score": 86, "total_sleep_duration": 25200},
                }
            ),
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["source_provider"] == "oura"
    assert ingestion["observation"]["value"] == 420
    assert ingestion["parser_method"] == "oura_provider_schema"
    assert ingestion["parsed_fields"]["source_path"] == "sleep.total_sleep_duration"


def test_performance_ingestion_normalizes_catapult_workload_schema(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "player_load",
            "name": "Player Load",
            "category": "physical",
            "unit": "load",
            "min_value": 0,
            "max_value": 1000,
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "wearable",
            "evidence_ref": "catapult://session/2026-06-05",
            "evidence_text": json.dumps(
                {
                    "provider": "catapult",
                    "session_start": "2026-06-05T16:00:00Z",
                    "metrics": {
                        "player_load": 384,
                        "total_distance_m": 6820,
                        "max_velocity": 8.4,
                        "high_speed_distance": 721,
                    },
                }
            ),
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["source_provider"] == "catapult"
    assert ingestion["observation"]["value"] == 384
    assert ingestion["parser_method"] == "catapult_provider_schema"
    assert ingestion["parsed_fields"]["source_path"] == "metrics.player_load"


def test_performance_ingestion_uses_model_assist_for_narrative_number_words(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "sleep_minutes",
            "name": "Sleep Minutes",
            "category": "wellness",
            "unit": "minutes",
            "min_value": 0,
            "max_value": 900,
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "audio_narration",
            "evidence_ref": "audio://coach-notes/recovery-2026-06-05",
            "evidence_text": "Coach note: recovery looked better today. Sleep duration was seven hours after travel.",
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["observation"]["value"] == 420
    assert ingestion["parser_method"] == "model_assisted_extraction"
    assert ingestion["model_assisted"] is True
    assert ingestion["model_policy"] == "afrolete-performance-extractor-v1"
    assert ingestion["model_confidence"] >= 0.75
    assert ingestion["model_evaluation"]["status"] == "applied"
    assert "Model-assisted extraction requires human review before verification." in ingestion["parser_warnings"]


def test_model_extraction_review_queue_bulk_verifies_model_assisted_observations(
    client, identity_headers
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "sleep_minutes",
            "name": "Sleep Minutes",
            "category": "wellness",
            "unit": "minutes",
            "min_value": 0,
            "max_value": 900,
        },
    ).json()
    ingestion_response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "audio_narration",
            "evidence_ref": "audio://coach-notes/recovery-queue",
            "evidence_text": "Coach note: sleep duration was seven hours after travel.",
        },
    )
    assert ingestion_response.status_code == 201
    observation_id = ingestion_response.json()["observation"]["id"]

    queue_response = client.get(
        (
            "/api/v1/performance/model-extraction/review-queue"
            f"?organization_id={organization['id']}&athlete_profile_id={roster['athlete_profile_id']}"
        ),
        headers=identity_headers,
    )
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert queue["pending_count"] == 1
    assert queue["model_assisted_count"] == 1
    assert queue["high_priority_count"] == 1
    assert queue["items"][0]["observation"]["id"] == observation_id
    assert queue["items"][0]["metric_code"] == "sleep_minutes"
    assert queue["items"][0]["model_policy"] == "afrolete-performance-extractor-v1"
    assert queue["items"][0]["evidence_ref"] == "audio://coach-notes/recovery-queue"
    assert "player_safety_relevant" in queue["items"][0]["flags"]

    bulk_response = client.post(
        "/api/v1/performance/model-extraction/review-queue/bulk-review",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "observation_ids": [observation_id],
            "verification_status": "verified",
            "min_confidence": 0.7,
            "notes": "Coach checked the source audio and accepted the extracted sleep value.",
        },
    )
    assert bulk_response.status_code == 200
    bulk = bulk_response.json()
    assert bulk["reviewed_count"] == 1
    assert bulk["skipped_count"] == 0
    assert bulk["observations"][0]["verification_status"] == "verified"
    assert "Coach checked" in bulk["observations"][0]["notes"]

    empty_queue_response = client.get(
        (
            "/api/v1/performance/model-extraction/review-queue"
            f"?organization_id={organization['id']}&athlete_profile_id={roster['athlete_profile_id']}"
        ),
        headers=identity_headers,
    )
    assert empty_queue_response.status_code == 200
    assert empty_queue_response.json()["pending_count"] == 0


def test_performance_model_extraction_benchmark_reports_accuracy(client, identity_headers) -> None:
    organization, _, _, _ = create_rostered_athlete(client, identity_headers)

    response = client.post(
        "/api/v1/performance/model-extraction/benchmarks",
        headers=identity_headers,
        json={"organization_id": organization["id"]},
    )

    assert response.status_code == 200
    benchmark = response.json()
    assert benchmark["model_policy"] == "afrolete-performance-extractor-v1"
    assert benchmark["case_count"] == 3
    assert benchmark["passed_count"] == 3
    assert benchmark["failed_count"] == 0
    assert benchmark["accuracy"] == 1.0
    assert benchmark["mean_absolute_error"] == 0.0
    methods = {case["case_id"]: case["parser_method"] for case in benchmark["cases"]}
    assert methods["sleep-duration-number-word"] == "model_assisted_extraction"
    assert methods["video-first-touch-specific-number"] == "metric_specific_text"


def test_performance_model_extraction_benchmark_dataset_can_be_saved_and_run(
    client, identity_headers
) -> None:
    organization, _, _, _ = create_rostered_athlete(client, identity_headers)

    dataset_response = client.post(
        "/api/v1/performance/model-extraction/benchmark-datasets",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Narrative Extraction Baseline",
            "slug": "narrative-extraction-baseline",
            "description": "Reusable production quality gate for narrative extraction.",
            "cases": [
                {
                    "case_id": "sleep-duration-number-word",
                    "metric_code": "sleep_minutes",
                    "metric_name": "Sleep Minutes",
                    "unit": "minutes",
                    "min_value": 0,
                    "max_value": 900,
                    "source": "audio_narration",
                    "evidence_ref": "benchmark://performance/sleep-duration-number-word",
                    "evidence_text": "Recovery note: sleep duration was seven hours after travel.",
                    "expected_value": 420,
                    "tolerance": 0.01,
                },
                {
                    "case_id": "video-first-touch-specific-number",
                    "metric_code": "first_touch",
                    "metric_name": "First Touch",
                    "category": "technical",
                    "unit": "score",
                    "min_value": 0,
                    "max_value": 10,
                    "source": "video_analysis",
                    "evidence_ref": "benchmark://performance/video-first-touch-specific-number",
                    "evidence_text": "70th minute clip: first touch quality 8.4 under pressure after two scans.",
                    "expected_value": 8.4,
                    "tolerance": 0.01,
                },
                {
                    "case_id": "agent-recovery-score",
                    "metric_code": "recovery_score",
                    "metric_name": "Recovery Score",
                    "unit": "score",
                    "min_value": 0,
                    "max_value": 100,
                    "source": "agent_extracted",
                    "evidence_ref": "benchmark://performance/agent-recovery-score",
                    "evidence_text": (
                        "Agent summary: fatigue was high but readiness improved; "
                        "recovery score came out at 74."
                    ),
                    "expected_value": 74,
                    "tolerance": 0.01,
                },
            ],
        },
    )

    assert dataset_response.status_code == 201
    dataset = dataset_response.json()
    assert dataset["slug"] == "narrative-extraction-baseline"
    assert dataset["case_count"] == 3
    assert dataset["last_run_at"] is None
    assert {case["case_id"] for case in dataset["cases"]} == {
        "sleep-duration-number-word",
        "video-first-touch-specific-number",
        "agent-recovery-score",
    }

    list_response = client.get(
        f"/api/v1/performance/model-extraction/benchmark-datasets?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == dataset["id"]

    run_response = client.post(
        "/api/v1/performance/model-extraction/benchmarks",
        headers=identity_headers,
        json={"organization_id": organization["id"], "dataset_id": dataset["id"]},
    )

    assert run_response.status_code == 200
    benchmark = run_response.json()
    assert benchmark["case_count"] == 3
    assert benchmark["passed_count"] == 3
    assert benchmark["accuracy"] == 1.0
    assert benchmark["mean_absolute_error"] == 0.0

    updated_list_response = client.get(
        f"/api/v1/performance/model-extraction/benchmark-datasets?organization_id={organization['id']}",
        headers=identity_headers,
    )
    updated = updated_list_response.json()[0]
    assert updated["last_run_at"] is not None
    assert updated["last_accuracy"] == 1.0
    assert updated["last_mean_absolute_error"] == 0.0


def test_performance_wearable_webhook_creates_pending_observations_once(
    client, identity_headers
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    hrv_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "hrv",
            "name": "Heart Rate Variability",
            "category": "wellness",
            "unit": "ms",
        },
    ).json()
    resting_hr_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "resting_heart_rate",
            "name": "Resting Heart Rate",
            "category": "wellness",
            "unit": "bpm",
        },
    ).json()

    payload = {
        "organization_id": organization["id"],
        "athlete_profile_id": roster["athlete_profile_id"],
        "source_provider": "whoop",
        "external_event_id": "whoop-cycle-2026-06-05",
        "metric_definition_ids": [hrv_metric["id"], resting_hr_metric["id"]],
        "payload": {
            "recovery": {
                "score": 44,
                "hrv_rmssd_milli": 33,
                "resting_heart_rate": 99,
            },
            "created_at": "2026-06-05T06:15:00Z",
        },
    }

    response = client.post("/api/v1/performance/webhooks/wearables", json=payload)

    assert response.status_code == 202
    ingest = response.json()
    assert ingest["source_provider"] == "whoop"
    assert ingest["external_event_id"] == "whoop-cycle-2026-06-05"
    assert ingest["replayed"] is False
    assert ingest["signature_required"] is False
    assert ingest["observation_count"] == 2
    assert ingest["skipped_metric_count"] == 0
    assert len(ingest["observation_ids"]) == 2

    observations = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert {observation["value"] for observation in observations} == {33, 99}
    assert {observation["verification_status"] for observation in observations} == {"pending_review"}
    assert all("whoop:whoop-cycle-2026-06-05" in observation["notes"] for observation in observations)

    replay = client.post("/api/v1/performance/webhooks/wearables", json=payload)

    assert replay.status_code == 202
    replay_body = replay.json()
    assert replay_body["replayed"] is True
    assert replay_body["observation_count"] == 2
    assert replay_body["observation_ids"] == []

    observations_after_replay = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert len(observations_after_replay) == 2


def test_performance_wearable_connection_sync_run_ingests_provider_payload(
    client, identity_headers
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    hrv_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "hrv",
            "name": "Heart Rate Variability",
            "category": "wellness",
            "unit": "ms",
        },
    ).json()
    resting_hr_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "resting_heart_rate",
            "name": "Resting Heart Rate",
            "category": "wellness",
            "unit": "bpm",
        },
    ).json()
    connection_response = client.post(
        "/api/v1/performance/wearable-connections",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "provider": "WHOOP",
            "display_name": "WHOOP recovery strap",
            "external_athlete_ref": "whoop-athlete-1",
            "scopes": ["read:recovery", "read:cycles"],
            "access_token_secret_path": "secret/data/afrolete/wearables/whoop-athlete-1",
            "webhook_registered": True,
            "default_metric_definition_ids": [hrv_metric["id"], resting_hr_metric["id"]],
        },
    )

    assert connection_response.status_code == 201
    connection = connection_response.json()
    assert connection["provider"] == "whoop"
    assert connection["access_token_configured"] is True
    assert connection["webhook_registered"] is True
    assert set(connection["scopes"]) == {"read:recovery", "read:cycles"}

    sync_response = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/sync-runs",
        headers=identity_headers,
        json={
            "external_event_id": "whoop-sync-2026-06-06",
            "payload": {
                "recovery": {
                    "hrv_rmssd_milli": 36,
                    "resting_heart_rate": 94,
                },
                "created_at": "2026-06-06T06:20:00Z",
            },
        },
    )

    assert sync_response.status_code == 202
    sync_run = sync_response.json()
    assert sync_run["status"] == "completed"
    assert sync_run["observation_count"] == 2
    assert sync_run["skipped_metric_count"] == 0
    assert sync_run["replayed"] is False

    listed_connections = client.get(
        f"/api/v1/performance/wearable-connections?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert listed_connections[0]["last_sync_at"] is not None
    assert listed_connections[0]["sync_cursor"] == "whoop-sync-2026-06-06"

    sync_runs = client.get(
        f"/api/v1/performance/wearable-connections/{connection['id']}/sync-runs",
        headers=identity_headers,
    ).json()
    assert sync_runs[0]["id"] == sync_run["id"]


def test_performance_wearable_webhook_registration_posts_provider_payload(
    client, identity_headers, monkeypatch
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    connection = client.post(
        "/api/v1/performance/wearable-connections",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "provider": "whoop",
            "display_name": "WHOOP webhook registration",
            "external_athlete_ref": "whoop-webhook-athlete",
            "access_token_secret_path": "secret/data/afrolete/wearables/whoop/webhook",
            "provider_webhook_registration_url": "https://whoop.example/v1/webhooks",
            "provider_webhook_event_types": ["recovery.updated"],
        },
    ).json()

    async def fake_resolve(path: str, field_name: str) -> str:
        assert path == "secret/data/afrolete/wearables/whoop/webhook"
        assert field_name == "access_token"
        return "provider-access-token"

    class FakeResponse:
        status_code = 201

        def raise_for_status(self) -> None:
            return None

    class FakeAsyncClient:
        def __init__(self, *_, **__) -> None:
            return None

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, url: str, *, json: dict[str, object], headers: dict[str, str]) -> FakeResponse:
            assert url == "https://whoop.example/v1/webhooks"
            assert headers["Authorization"] == "Bearer provider-access-token"
            assert json["callback_url"] == "https://app.afrolete.local/api/v1/performance/webhooks/wearables"
            assert json["athlete_ref"] == "whoop-webhook-athlete"
            assert json["event_types"] == ["recovery.updated", "sleep.updated"]
            assert json["replay_protection"] == "external_event_id"
            assert json["signing_secret_path"] == "secret/data/afrolete/wearables/whoop/webhook-signing"
            return FakeResponse()

    monkeypatch.setattr(performance_service, "resolve_wearable_token_secret", fake_resolve)
    monkeypatch.setattr(performance_service.httpx, "AsyncClient", FakeAsyncClient)

    response = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/webhook-registration",
        headers=identity_headers,
        json={
            "callback_url": "https://app.afrolete.local/api/v1/performance/webhooks/wearables",
            "event_types": ["recovery.updated", "sleep.updated"],
            "signing_secret_path": "secret/data/afrolete/wearables/whoop/webhook-signing",
            "provider_payload": {"replay_protection": "external_event_id"},
        },
    )

    assert response.status_code == 200
    registration = response.json()
    assert registration["status"] == "registered"
    assert registration["registered"] is True
    assert registration["provider_status_code"] == 201
    assert registration["registration_payload_hash"]
    assert registration["connection"]["webhook_registered"] is True
    assert registration["connection"]["provider_webhook_registered_at"] is not None
    assert registration["connection"]["provider_webhook_event_types"] == ["recovery.updated", "sleep.updated"]
    assert "provider-access-token" not in response.text


def test_performance_wearable_connection_live_pull_adapter_ingests_provider_response(
    client, identity_headers, monkeypatch
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    hrv_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "hrv",
            "name": "Heart Rate Variability",
            "category": "wellness",
            "unit": "ms",
        },
    ).json()
    recovery_metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "recovery_score",
            "name": "Recovery Score",
            "category": "wellness",
            "unit": "%",
        },
    ).json()
    connection = client.post(
        "/api/v1/performance/wearable-connections",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "provider": "whoop",
            "display_name": "WHOOP live pull",
            "external_athlete_ref": "whoop-live-athlete-1",
            "scopes": ["read:recovery"],
            "access_token_secret_path": "secret/data/afrolete/wearables/whoop/access",
            "provider_pull_url": "https://whoop.example/v1/recovery",
            "default_metric_definition_ids": [hrv_metric["id"], recovery_metric["id"]],
        },
    ).json()

    async def fake_resolve(path: str, field_name: str) -> str:
        assert path == "secret/data/afrolete/wearables/whoop/access"
        assert field_name == "access_token"
        return "provider-access-token"

    class FakeResponse:
        def __init__(self, payload: dict[str, object]) -> None:
            self.status_code = 200
            self.headers: dict[str, str] = {}
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._payload

    class FakeAsyncClient:
        def __init__(self, *_, **__) -> None:
            self.calls = 0

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def get(self, url: str, *, params: dict[str, str], headers: dict[str, str]) -> FakeResponse:
            self.calls += 1
            assert url == "https://whoop.example/v1/recovery"
            assert headers["Authorization"] == "Bearer provider-access-token"
            assert headers["X-AfroLete-Athlete-Ref"] == "whoop-live-athlete-1"
            assert params["athlete_ref"] == "whoop-live-athlete-1"
            if self.calls == 1:
                assert "cursor" not in params
                return FakeResponse(
                    {
                        "external_event_id": "whoop-live-2026-06-07-page-1",
                        "next_cursor": "cursor-2",
                        "recovery": {
                            "hrv_rmssd_milli": 42,
                        },
                        "created_at": "2026-06-07T06:20:00Z",
                    }
                )
            assert params["cursor"] == "cursor-2"
            return FakeResponse(
                {
                    "external_event_id": "whoop-live-2026-06-07-page-2",
                    "recovery": {
                        "score": 71,
                    },
                    "created_at": "2026-06-07T06:30:00Z",
                }
            )

    monkeypatch.setattr(performance_service, "resolve_wearable_token_secret", fake_resolve)
    monkeypatch.setattr(performance_service.httpx, "AsyncClient", FakeAsyncClient)

    sync_response = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/sync-runs",
        headers=identity_headers,
        json={
            "since": "2026-06-07T00:00:00Z",
            "until": "2026-06-07T23:59:59Z",
            "max_pages": 2,
        },
    )

    assert sync_response.status_code == 202
    sync_run = sync_response.json()
    assert sync_run["status"] == "completed"
    assert sync_run["observation_count"] == 2
    assert sync_run["provider_status_code"] == 200
    assert sync_run["provider_response_hash"]
    assert sync_run["provider_page_count"] == 2
    assert sync_run["provider_rate_limited"] is False
    assert sync_run["external_event_id"].startswith("pull-whoop-")

    observations = client.get(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/observations"
        f"?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert {observation["value"] for observation in observations} == {42.0, 71.0}

    listed_connections = client.get(
        f"/api/v1/performance/wearable-connections?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert listed_connections[0]["provider_pull_configured"] is True
    assert listed_connections[0]["sync_cursor"].startswith("pull-whoop-")


def test_performance_wearable_connection_pull_records_rate_limit(
    client, identity_headers, monkeypatch
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
        "/api/v1/performance/metrics",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "code": "hrv",
            "name": "Heart Rate Variability",
            "category": "wellness",
            "unit": "ms",
        },
    ).json()
    connection = client.post(
        "/api/v1/performance/wearable-connections",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "provider": "whoop",
            "display_name": "WHOOP rate limit",
            "external_athlete_ref": "whoop-rate-limit-athlete",
            "access_token_secret_path": "secret/data/afrolete/wearables/whoop/rate-limit",
            "provider_pull_url": "https://whoop.example/v1/recovery",
            "default_metric_definition_ids": [metric["id"]],
        },
    ).json()

    async def fake_resolve(path: str, field_name: str) -> str:
        assert path == "secret/data/afrolete/wearables/whoop/rate-limit"
        assert field_name == "access_token"
        return "provider-access-token"

    class RateLimitedResponse:
        status_code = 429
        headers = {"Retry-After": "90"}

        def json(self) -> dict[str, object]:
            return {"error": "rate_limited"}

    class FakeAsyncClient:
        def __init__(self, *_, **__) -> None:
            return None

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def get(self, *_: object, **__: object) -> RateLimitedResponse:
            return RateLimitedResponse()

    monkeypatch.setattr(performance_service, "resolve_wearable_token_secret", fake_resolve)
    monkeypatch.setattr(performance_service.httpx, "AsyncClient", FakeAsyncClient)

    sync_response = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/sync-runs",
        headers=identity_headers,
        json={"max_pages": 2},
    )

    assert sync_response.status_code == 202
    sync_run = sync_response.json()
    assert sync_run["status"] == "rate_limited"
    assert sync_run["provider_status_code"] == 429
    assert sync_run["provider_page_count"] == 0
    assert sync_run["provider_rate_limited"] is True
    assert sync_run["provider_retry_after_seconds"] == 90
    assert sync_run["observation_count"] == 0


def test_performance_wearable_connection_oauth_start_and_callback(
    client, identity_headers
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    connection = client.post(
        "/api/v1/performance/wearable-connections",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "provider": "garmin",
            "display_name": "Garmin Connect",
            "external_athlete_ref": "garmin-athlete-1",
            "scopes": ["wellness.read"],
        },
    ).json()

    oauth_start = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/oauth/start",
        headers=identity_headers,
        json={
            "client_id": "garmin-client-1",
            "authorization_url": "https://connect.garmin.example/oauth/authorize",
            "token_url": "https://connect.garmin.example/oauth/token",
            "redirect_uri": "https://app.afrolete.local/performance/wearables/callback",
            "scopes": ["wellness.read", "sleep.read"],
        },
    )

    assert oauth_start.status_code == 200
    start_payload = oauth_start.json()
    assert "response_type=code" in start_payload["authorization_url"]
    assert "client_id=garmin-client-1" in start_payload["authorization_url"]
    assert start_payload["state"]
    assert start_payload["scopes"] == ["wellness.read", "sleep.read"]

    listed_pending = client.get(
        f"/api/v1/performance/wearable-connections?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert listed_pending[0]["status"] == "oauth_pending"
    assert listed_pending[0]["oauth_state_pending"] is True

    callback = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/oauth/callback",
        headers=identity_headers,
        json={
            "state": start_payload["state"],
            "code": "provider-code-123",
            "access_token_secret_path": "secret/data/afrolete/wearables/garmin/access",
            "refresh_token_secret_path": "secret/data/afrolete/wearables/garmin/refresh",
            "provider_token_response": {
                "access_token": "provider-access-token-1",
                "refresh_token": "provider-refresh-token-1",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "wellness.read sleep.read",
            },
        },
    )

    assert callback.status_code == 200
    callback_payload = callback.json()
    assert callback_payload["status"] == "authorized"
    assert callback_payload["connection"]["status"] == "authorized"
    assert callback_payload["connection"]["access_token_configured"] is True
    assert callback_payload["connection"]["refresh_token_configured"] is True
    assert callback_payload["connection"]["access_token_recorded"] is True
    assert callback_payload["connection"]["refresh_token_recorded"] is True
    assert callback_payload["connection"]["refresh_token_family_id"]
    assert callback_payload["connection"]["token_type"] == "Bearer"
    assert callback_payload["connection"]["token_scope"] == ["wellness.read", "sleep.read"]
    assert "provider-access-token-1" not in callback.text
    assert "provider-refresh-token-1" not in callback.text
    assert callback_payload["connection"]["oauth_state_pending"] is False
    assert callback_payload["connection"]["oauth_authorized_at"] is not None

    refresh = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/oauth/refresh",
        headers=identity_headers,
        json={
            "provider_token_response": {
                "access_token": "provider-access-token-2",
                "refresh_token": "provider-refresh-token-2",
                "expires_in": 7200,
                "token_type": "Bearer",
                "scope": ["wellness.read", "sleep.read", "activity.read"],
            },
        },
    )
    assert refresh.status_code == 200
    refresh_payload = refresh.json()
    assert refresh_payload["status"] == "refreshed"
    assert refresh_payload["refresh_token_rotated"] is True
    assert refresh_payload["connection"]["refresh_token_rotated_at"] is not None
    assert refresh_payload["connection"]["token_last_refreshed_at"] is not None
    assert refresh_payload["connection"]["token_scope"] == ["wellness.read", "sleep.read", "activity.read"]
    assert "provider-access-token-2" not in refresh.text
    assert "provider-refresh-token-2" not in refresh.text

    bad_replay = client.post(
        f"/api/v1/performance/wearable-connections/{connection['id']}/oauth/callback",
        headers=identity_headers,
        json={
            "state": start_payload["state"],
            "code": "provider-code-456",
        },
    )
    assert bad_replay.status_code == 401


def test_performance_ingestion_uses_metric_specific_video_text(client, identity_headers) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    metric = client.post(
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
        },
    ).json()

    response = client.post(
        "/api/v1/performance/ingest",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "metric_definition_id": metric["id"],
            "source": "video_analysis",
            "evidence_ref": "video://matchday/clip-070",
            "evidence_text": "70th minute clip: first touch quality 8.4 under pressure after two scans.",
        },
    )

    assert response.status_code == 201
    ingestion = response.json()
    assert ingestion["observation"]["value"] == 8.4
    assert ingestion["parser_method"] == "metric_specific_text"
    assert ingestion["parser_confidence_reason"].startswith("Found the metric label")


def test_video_coaching_analysis_creates_pending_review_outputs(
    client,
    identity_headers,
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)

    response = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/video-coaching",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "athletics",
            "video_uri": "video://training/sprint-001",
            "clip_label": "100m acceleration block",
            "analysis_focus": "stride mechanics, posture, arm drive, ground contact, rhythm",
            "evidence_text": (
                "Stride efficiency 8.1. Posture control 6.4 due to late torso collapse. "
                "Ground contact control 7.2. Arm drive 6.8 with cross-body swing. "
                "Rhythm consistency 7.5."
            ),
        },
    )

    assert response.status_code == 201
    coaching = response.json()
    assert coaching["review_required"] is True
    assert coaching["sport"] == "athletics"
    assert len(coaching["observations"]) == 5
    assert {observation["source"] for observation in coaching["observations"]} == {
        "video_analysis"
    }
    assert {
        observation["verification_status"]
        for observation in coaching["observations"]
    } == {"pending_review"}
    assert coaching["assessment"]["verification_status"] == "pending_review"
    assert "Posture Control" in coaching["summary"]
    assert "Review the clip" in coaching["coaching_plan"]
    metric_codes = {metric["metric_code"] for metric in coaching["metrics"]}
    assert "video_stride_efficiency" in metric_codes
    assert coaching["next_actions"]


def test_opposition_scouting_video_generates_tactical_report(client, identity_headers) -> None:
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    video_bytes = b"opponent tactical match video"
    upload_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Pressing City",
            "sport": "football",
            "filename": "pressing-city.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(video_bytes).decode(),
            "clip_label": "Round 3 opponent full match",
            "match_context": "4-2-3-1 high press with corners and fast counter attacks.",
            "analysis_focus": "formation, high press, set pieces, transition defense",
        },
    )
    assert upload_response.status_code == 201
    video_asset = upload_response.json()
    assert video_asset["opponent_name"] == "Pressing City"
    assert video_asset["status"] == "uploaded"

    tracking_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/tracking-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "source_provider": "provider_tracking_import",
            "replace_existing": True,
            "samples": [
                {
                    "track_id": "home-8",
                    "team_label": "Pressing City",
                    "player_label": "Pressing City 8",
                    "timestamp_seconds": 0,
                    "x_percent": 40,
                    "y_percent": 50,
                },
                {
                    "track_id": "home-9",
                    "team_label": "Pressing City",
                    "player_label": "Pressing City 9",
                    "timestamp_seconds": 1,
                    "x_percent": 70,
                    "y_percent": 50,
                },
                {
                    "track_id": "home-9",
                    "team_label": "Pressing City",
                    "player_label": "Pressing City 9",
                    "timestamp_seconds": 2,
                    "x_percent": 98,
                    "y_percent": 50,
                },
                {
                    "track_id": "away-5",
                    "team_label": "AfroLete",
                    "player_label": "AfroLete 5",
                    "timestamp_seconds": 3,
                    "x_percent": 60,
                    "y_percent": 50,
                },
                {
                    "track_id": "ball",
                    "team_label": "ball",
                    "player_label": "Ball",
                    "timestamp_seconds": 0,
                    "x_percent": 40,
                    "y_percent": 50,
                },
                {
                    "track_id": "ball",
                    "team_label": "ball",
                    "player_label": "Ball",
                    "timestamp_seconds": 1,
                    "x_percent": 70,
                    "y_percent": 50,
                },
                {
                    "track_id": "ball",
                    "team_label": "ball",
                    "player_label": "Ball",
                    "timestamp_seconds": 2,
                    "x_percent": 98,
                    "y_percent": 50,
                },
                {
                    "track_id": "ball",
                    "team_label": "ball",
                    "player_label": "Ball",
                    "timestamp_seconds": 3,
                    "x_percent": 60,
                    "y_percent": 50,
                },
            ],
        },
    )
    assert tracking_response.status_code == 201
    tracking = tracking_response.json()
    assert tracking["ball_tracking_metrics"]["pass_attempt_count"] == 2
    assert tracking["ball_tracking_metrics"]["shot_count"] == 1
    assert tracking["ball_tracking_metrics"]["interception_count"] == 1

    report_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/reports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "observed_formation": "4-2-3-1",
            "evidence_text": (
                "Opponent presses after back passes, attacks set pieces with zonal screens, "
                "and leaves space behind fullbacks."
            ),
        },
    )
    assert report_response.status_code == 201
    report = report_response.json()
    assert report["model_policy"] == "afrolete-opposition-scout-v2"
    assert report["formation_detected"] == "4-2-3-1"
    assert report["confidence"] >= 0.9
    assert "Tracking evidence adds" in report["tactical_summary"]
    assert any(finding["category"] == "set_piece" for finding in report["weaknesses"])
    assert any("weak-side" in finding["title"].lower() for finding in report["recommendations"])
    tracking_categories = {finding["category"] for finding in report["tracking_evidence"]}
    assert "tracking_evidence" in tracking_categories
    assert "passing_weakness" in tracking_categories
    assert "chance_profile" in tracking_categories
    assert "defensive_profile" in tracking_categories

    videos = client.get(
        f"/api/v1/performance/scouting/videos?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert videos.status_code == 200
    assert videos.json()[0]["status"] == "scouted"
    reports = client.get(
        f"/api/v1/performance/scouting/reports?organization_id={organization['id']}&team_id={team['id']}",
        headers=identity_headers,
    )
    assert reports.status_code == 200
    assert reports.json()[0]["id"] == report["id"]


def test_match_video_tracking_computes_player_distances_and_speed_metrics(client, identity_headers) -> None:
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    upload_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Tracking City",
            "sport": "football",
            "filename": "tracking-city.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"match tracking video").decode(),
            "clip_label": "Full match tracking",
            "match_context": "11v11 football match with GPS-like tracking samples.",
            "analysis_focus": "player locations, total distance, speed zones, heatmap",
        },
    )
    assert upload_response.status_code == 201
    video_asset = upload_response.json()

    calibration_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/pitch-calibrations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Broadcast wide camera",
            "pitch_length_m": 100,
            "pitch_width_m": 50,
            "points": [
                {"label": "top left", "image_x_percent": 0, "image_y_percent": 0, "pitch_x_meters": 0, "pitch_y_meters": 0},
                {"label": "top right", "image_x_percent": 100, "image_y_percent": 0, "pitch_x_meters": 100, "pitch_y_meters": 0},
                {"label": "bottom right", "image_x_percent": 100, "image_y_percent": 100, "pitch_x_meters": 100, "pitch_y_meters": 50},
                {"label": "bottom left", "image_x_percent": 0, "image_y_percent": 100, "pitch_x_meters": 0, "pitch_y_meters": 50},
            ],
        },
    )
    assert calibration_response.status_code == 201
    calibration = calibration_response.json()
    assert calibration["quality_score"] >= 0.9

    tracking_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/tracking-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "calibration_id": calibration["id"],
            "source_provider": "provider_tracking_import",
            "replace_existing": True,
            "samples": [
                {"track_id": "home-9", "team_label": "Home", "player_label": "Striker", "jersey_number": "9", "timestamp_seconds": 0, "x_percent": 0, "y_percent": 60},
                {"track_id": "home-9", "team_label": "Home", "player_label": "Striker", "jersey_number": "9", "timestamp_seconds": 1, "x_percent": 10, "y_percent": 60},
                {"track_id": "home-9", "team_label": "Home", "player_label": "Striker", "jersey_number": "9", "timestamp_seconds": 2, "x_percent": 20, "y_percent": 60},
                {"track_id": "home-4", "team_label": "Home", "player_label": "Center Back", "jersey_number": "4", "timestamp_seconds": 0, "x_percent": 0, "y_percent": 20},
                {"track_id": "home-4", "team_label": "Home", "player_label": "Center Back", "jersey_number": "4", "timestamp_seconds": 1, "x_percent": 0, "y_percent": 20},
                {"track_id": "home-4", "team_label": "Home", "player_label": "Center Back", "jersey_number": "4", "timestamp_seconds": 2, "x_percent": 0, "y_percent": 20},
                {"track_id": "away-6", "team_label": "Away", "player_label": "Midfielder", "jersey_number": "6", "timestamp_seconds": 0, "x_percent": 0, "y_percent": 0},
                {"track_id": "away-6", "team_label": "Away", "player_label": "Midfielder", "jersey_number": "6", "timestamp_seconds": 1, "x_percent": 3, "y_percent": 8},
                {"track_id": "away-6", "team_label": "Away", "player_label": "Midfielder", "jersey_number": "6", "timestamp_seconds": 2, "x_percent": 6, "y_percent": 16},
                {"track_id": "ball", "team_label": "ball", "player_label": "Ball", "timestamp_seconds": 0, "x_percent": 0, "y_percent": 60},
                {"track_id": "ball", "team_label": "ball", "player_label": "Ball", "timestamp_seconds": 1, "x_percent": 0, "y_percent": 20},
                {"track_id": "ball", "team_label": "ball", "player_label": "Ball", "timestamp_seconds": 2, "x_percent": 6, "y_percent": 16},
            ],
        },
    )
    assert tracking_response.status_code == 201
    tracking = tracking_response.json()
    assert tracking["model_policy"] == "afrolete-match-tracking-import-v1"
    assert tracking["calibration_id"] == calibration["id"]
    assert tracking["calibration"]["name"] == "Broadcast wide camera"
    assert tracking["sample_count"] == 12
    assert tracking["player_count"] == 3
    assert tracking["total_distance_m"] == 30.0
    assert tracking["max_speed_mps"] == 10.0
    assert tracking["high_speed_distance_m"] == 20.0
    assert tracking["sprint_count"] == 1
    assert tracking["tracking_quality_score"] >= 0.8
    assert tracking["identity_continuity_score"] == 1.0
    assert tracking["readiness_level"] == "coach_ready"
    assert any("coach review" in warning for warning in tracking["quality_warnings"])
    assert any("high-speed load" in guidance for guidance in tracking["coaching_guidance"])
    striker = next(metric for metric in tracking["player_metrics"] if metric["track_id"] == "home-9")
    assert striker["distance_m"] == 20.0
    assert striker["sprint_count"] == 1
    assert striker["work_rate_m_per_min"] == 600.0
    assert striker["off_ball_run_count"] >= 1
    assert striker["territorial_advance_count"] >= 1
    assert striker["tracking_quality_score"] > 0.5
    assert any("High peak speed" in flag for flag in striker["coaching_flags"])
    assert striker["dominant_zone"] == "defensive_central"
    home_shape = next(shape for shape in tracking["team_shape_metrics"] if shape["team_label"] == "Home")
    assert home_shape["track_count"] == 2
    assert home_shape["average_width_percent"] == 40.0
    assert home_shape["shape_hint"] == "deep_block_shape"
    home_phase = next(phase for phase in tracking["team_phase_metrics"] if phase["team_label"] == "Home")
    assert home_phase["defensive_third_percent"] > 0
    assert home_phase["territorial_advance_count"] >= 1
    assert tracking["pressure_events"]
    assert tracking["pressure_events"][0]["distance_m"] <= 8.0
    assert tracking["ball_tracking_metrics"]["ball_sample_count"] == 3
    assert tracking["ball_tracking_metrics"]["pass_count"] == 1
    assert tracking["ball_tracking_metrics"]["turnover_count"] == 1
    assert tracking["possession_estimates"][0]["team_label"] == "Home"
    assert tracking["possession_estimates"][0]["possession_percent"] > 60
    assert {event["event_type"] for event in tracking["ball_action_events"]} == {"pass", "turnover"}
    recognized_actions = {event["action_type"] for event in tracking["recognized_action_events"]}
    assert {"pass_completion", "tackle", "pressure", "high_speed_run"} <= recognized_actions
    assert tracking["action_recognition_metrics"]["model_policy"] == "afrolete-tracking-action-recognition-v1"
    assert tracking["action_recognition_metrics"]["event_count"] == len(tracking["recognized_action_events"])
    assert tracking["action_recognition_metrics"]["average_confidence"] > 0
    assert any(snapshot["team_label"] == "Home" for snapshot in tracking["formation_snapshots"])
    assert any("Home" in guidance for guidance in tracking["tactical_guidance"])

    calibrations = client.get(
        f"/api/v1/performance/scouting/pitch-calibrations?organization_id={organization['id']}&video_asset_id={video_asset['id']}",
        headers=identity_headers,
    )
    assert calibrations.status_code == 200
    assert calibrations.json()[0]["id"] == calibration["id"]

    runs = client.get(
        f"/api/v1/performance/scouting/tracking-runs?organization_id={organization['id']}&video_asset_id={video_asset['id']}",
        headers=identity_headers,
    )
    assert runs.status_code == 200
    assert runs.json()[0]["id"] == tracking["id"]

    review_response = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/identity-reviews",
        headers=identity_headers,
        json={
            "track_id": "home-9",
            "team_label": "AfroLete",
            "player_label": "Confirmed Forward",
            "jersey_number": "99",
            "decision": "confirmed",
            "notes": "Coach confirmed the track identity after slow-motion review.",
        },
    )
    assert review_response.status_code == 201
    review_result = review_response.json()
    review = review_result["review"]
    revised_tracking = review_result["tracking_run"]
    assert review["track_id"] == "home-9"
    assert review["sample_count"] == 3
    assert review["before"]["player_labels"] == ["Striker"]
    assert review["after"]["player_label"] == "Confirmed Forward"
    assert revised_tracking["status"] == "reviewed"
    revised_forward = next(metric for metric in revised_tracking["player_metrics"] if metric["track_id"] == "home-9")
    assert revised_forward["player_label"] == "Confirmed Forward"
    assert revised_forward["team_label"] == "AfroLete"
    assert revised_forward["jersey_number"] == "99"
    assert revised_forward["distance_m"] == 20.0
    assert all(
        sample["source"].endswith("identity_review")
        for sample in revised_tracking["samples"]
        if sample["track_id"] == "home-9"
    )

    reviews = client.get(
        f"/api/v1/performance/scouting/tracking-identity-reviews?organization_id={organization['id']}&tracking_run_id={tracking['id']}",
        headers=identity_headers,
    )
    assert reviews.status_code == 200
    assert reviews.json()[0]["id"] == review["id"]

    report_response = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{revised_tracking['id']}/analysis-reports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "audience": "coach",
            "report_scope": "team_match_review",
            "title": "Tracking City player guidance",
            "include_player_cards": True,
            "include_tactical_shape": True,
            "notes": "Share after coach review.",
        },
    )
    assert report_response.status_code == 201
    report = report_response.json()
    assert report["status"] == "generated"
    assert report["model_policy"] == "afrolete-match-analysis-report-v1"
    assert report["summary"]["total_distance_m"] == 30.0
    assert report["summary"]["player_count"] == 3
    assert report["summary"]["pressure_event_count"] >= 1
    assert report["summary"]["pass_count"] == 0
    assert report["summary"]["turnover_count"] == 2
    assert report["player_cards"][0]["player_label"] == "Confirmed Forward"
    assert report["player_cards"][0]["high_speed_distance_m"] == 20.0
    assert any(shape["team_label"] == "Home" for shape in report["team_shape"])
    assert any("high-speed load" in recommendation for recommendation in report["recommendations"])
    assert len(report["checksum"]) == 64
    assert report["size_bytes"] > 400
    assert report["storage_url"].startswith("local://performance-match-reports/")

    reports = client.get(
        f"/api/v1/performance/scouting/match-analysis-reports?organization_id={organization['id']}&tracking_run_id={tracking['id']}",
        headers=identity_headers,
    )
    assert reports.status_code == 200
    assert reports.json()[0]["id"] == report["id"]

    download_response = client.get(
        f"/api/v1/performance/scouting/match-analysis-reports/{report['id']}/download",
        headers=identity_headers,
    )
    assert download_response.status_code == 200
    assert download_response.headers["X-Afrolete-Match-Report-Checksum"] == report["checksum"]
    report_text = download_response.text
    assert "# Tracking City player guidance" in report_text
    assert "Confirmed Forward" in report_text
    assert "## Tactical Shape" in report_text
    assert "## Team Phase And Pressure" in report_text
    assert "## Possession And Ball Actions" in report_text
    assert "## Data Quality" in report_text

    guidance_review_response = client.get(
        f"/api/v1/performance/scouting/tracking-runs/{revised_tracking['id']}/player-guidance-review",
        headers=identity_headers,
    )
    assert guidance_review_response.status_code == 200
    guidance_review = guidance_review_response.json()
    assert guidance_review["guidance_status"] == "coach_review_required"
    assert guidance_review["player_card_count"] == len(guidance_review["player_cards"])
    assert guidance_review["player_guidance"][0]["player_label"] == "Confirmed Forward"
    assert any("longer sample window" in action for action in guidance_review["required_actions"])
    assert any("draft-only" in note for note in guidance_review["review_notes"])
    assert guidance_review["coach_guidance"]

    blocked_publish_response = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{revised_tracking['id']}/player-guidance-publish",
        headers=identity_headers,
        json={"organization_id": organization["id"], "channel": "in_app"},
    )
    assert blocked_publish_response.status_code == 422
    assert "required_actions" in blocked_publish_response.json()["detail"]


def test_match_video_auto_tracking_uses_video_frame_extractor(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    video_bytes = b"raw football match bytes"
    upload_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Auto Track FC",
            "sport": "football",
            "filename": "auto-track-fc.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(video_bytes).decode(),
            "clip_label": "Broadcast feed",
            "match_context": "Raw football match feed for OpenCV player tracking.",
            "analysis_focus": "automated player tracking",
        },
    )
    assert upload_response.status_code == 201
    video_asset = upload_response.json()

    def fake_extract(content: bytes, **kwargs: object) -> dict[str, object]:
        assert content == video_bytes
        assert kwargs["max_frames"] == 12
        assert kwargs["sample_every_seconds"] == 0.25
        return {
            "samples": [
                {
                    "track_id": "cv-1",
                    "team_label": None,
                    "player_label": "Track cv-1",
                    "timestamp_seconds": 0,
                    "x_percent": 10,
                    "y_percent": 50,
                    "confidence": 0.82,
                    "source": "opencv_motion_tracker",
                },
                {
                    "track_id": "cv-1",
                    "team_label": None,
                    "player_label": "Track cv-1",
                    "timestamp_seconds": 1,
                    "x_percent": 20,
                    "y_percent": 50,
                    "confidence": 0.84,
                    "source": "opencv_motion_tracker",
                },
                {
                    "track_id": "cv-2",
                    "team_label": None,
                    "player_label": "Track cv-2",
                    "timestamp_seconds": 0,
                    "x_percent": 40,
                    "y_percent": 25,
                    "confidence": 0.76,
                    "source": "opencv_motion_tracker",
                },
                {
                    "track_id": "cv-2",
                    "team_label": None,
                    "player_label": "Track cv-2",
                    "timestamp_seconds": 1,
                    "x_percent": 45,
                    "y_percent": 30,
                    "confidence": 0.78,
                    "source": "opencv_motion_tracker",
                },
                {
                    "track_id": "ball",
                    "team_label": "ball",
                    "player_label": "Ball",
                    "timestamp_seconds": 0,
                    "x_percent": 10,
                    "y_percent": 50,
                    "confidence": 0.72,
                    "source": "opencv_ball_tracker",
                },
                {
                    "track_id": "ball",
                    "team_label": "ball",
                    "player_label": "Ball",
                    "timestamp_seconds": 1,
                    "x_percent": 20,
                    "y_percent": 50,
                    "confidence": 0.74,
                    "source": "opencv_ball_tracker",
                },
            ],
            "decoded_frame_count": 24,
            "processed_frame_count": 4,
            "source_provider": "opencv_motion_tracker",
            "model_policy": "opencv-background-subtraction-match-tracker-v2",
            "warnings": ["Synthetic extractor warning"],
        }

    monkeypatch.setattr(performance_service, "extract_match_tracking_samples_from_video_content", fake_extract)

    tracking_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/tracking-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "source_provider": "opencv_motion_tracker",
            "auto_track": True,
            "replace_existing": True,
            "max_frames": 12,
            "sample_every_seconds": 0.25,
            "min_detection_confidence": 0.3,
            "samples": [],
        },
    )

    assert tracking_response.status_code == 201
    tracking = tracking_response.json()
    assert tracking["source_provider"] == "opencv_motion_tracker"
    assert tracking["model_policy"] == "opencv-background-subtraction-match-tracker-v2"
    assert tracking["sample_count"] == 6
    assert tracking["player_count"] == 2
    assert tracking["total_distance_m"] > 0
    assert tracking["ball_tracking_metrics"]["ball_sample_count"] == 2
    assert tracking["ball_tracking_metrics"]["carry_count"] == 1
    assert any("Synthetic extractor warning" in warning for warning in tracking["quality_warnings"])
    assert any(sample["source"] == "opencv_motion_tracker" for sample in tracking["samples"])
    assert any(sample["source"] == "opencv_ball_tracker" for sample in tracking["samples"])


def test_publishable_match_guidance_sends_private_player_messages(client, identity_headers) -> None:
    organization, team, member, _ = create_rostered_athlete(client, identity_headers)
    upload_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Share Ready FC",
            "sport": "football",
            "filename": "share-ready-fc.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"share ready match video").decode(),
            "clip_label": "Share-ready player guidance",
            "match_context": "Calibrated provider tracking for player guidance publishing.",
            "analysis_focus": "player guidance distribution",
        },
    )
    assert upload_response.status_code == 201
    video_asset = upload_response.json()
    calibration_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/pitch-calibrations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Share-ready camera",
            "pitch_length_m": 100,
            "pitch_width_m": 50,
            "points": [
                {"label": "top left", "image_x_percent": 0, "image_y_percent": 0, "pitch_x_meters": 0, "pitch_y_meters": 0},
                {"label": "top right", "image_x_percent": 100, "image_y_percent": 0, "pitch_x_meters": 100, "pitch_y_meters": 0},
                {"label": "bottom right", "image_x_percent": 100, "image_y_percent": 100, "pitch_x_meters": 100, "pitch_y_meters": 50},
                {"label": "bottom left", "image_x_percent": 0, "image_y_percent": 100, "pitch_x_meters": 0, "pitch_y_meters": 50},
            ],
        },
    )
    assert calibration_response.status_code == 201
    calibration = calibration_response.json()
    tracking_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/tracking-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "calibration_id": calibration["id"],
            "source_provider": "provider_tracking_import",
            "replace_existing": True,
            "samples": [
                {
                    "track_id": "home-9",
                    "person_id": member["subject_id"],
                    "team_label": "Home",
                    "player_label": "Performance Athlete",
                    "jersey_number": "9",
                    "timestamp_seconds": second,
                    "x_percent": 10 + second * 10,
                    "y_percent": 50,
                    "confidence": 0.92,
                }
                for second in range(6)
            ],
        },
    )
    assert tracking_response.status_code == 201
    tracking = tracking_response.json()

    review_response = client.get(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/player-guidance-review",
        headers=identity_headers,
    )
    assert review_response.status_code == 200
    review = review_response.json()
    assert review["publishable"] is True
    assert review["guidance_status"] == "player_shareable"

    publish_response = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/player-guidance-publish",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "in_app",
            "subject_prefix": "Coach-reviewed match guidance",
            "message_intro": "Your coach has cleared this player guidance card for review.",
        },
    )
    assert publish_response.status_code == 201
    published = publish_response.json()
    assert published["publishable"] is True
    assert published["message_count"] == 1
    assert published["recipient_count"] == 1
    assert published["messages"][0]["player_person_id"] == member["subject_id"]
    assert published["messages"][0]["track_id"] == "home-9"
    assert published["audits"][0]["message_id"] == published["messages"][0]["message_id"]
    assert published["audits"][0]["track_id"] == "home-9"
    assert published["audits"][0]["recipient_count"] == 1
    assert published["audits"][0]["queued_count"] == 1

    recipients = client.get(
        f"/api/v1/communications/messages/{published['messages'][0]['message_id']}/recipients",
        headers=identity_headers,
    )
    assert recipients.status_code == 200
    assert recipients.json()[0]["person_id"] == member["subject_id"]
    messages = client.get(
        f"/api/v1/communications/messages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert any(message["subject"].startswith("Coach-reviewed match guidance") for message in messages)

    publish_audits = client.get(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/player-guidance-publishes",
        headers=identity_headers,
    )
    assert publish_audits.status_code == 200
    assert publish_audits.json()[0]["message_id"] == published["messages"][0]["message_id"]
    assert publish_audits.json()[0]["player_person_id"] == member["subject_id"]
    assert publish_audits.json()[0]["queued_count"] == 1

    read_response = client.patch(
        f"/api/v1/communications/recipients/{recipients.json()[0]['id']}",
        headers=identity_headers,
        json={"delivery_status": "read"},
    )
    assert read_response.status_code == 200
    updated_audits = client.get(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/player-guidance-publishes",
        headers=identity_headers,
    ).json()
    assert updated_audits[0]["read_count"] == 1
    assert updated_audits[0]["queued_count"] == 0


def test_match_tracking_provider_import_frames_feed_player_metrics_and_reports(client, identity_headers) -> None:
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    upload_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Provider Track FC",
            "sport": "football",
            "filename": "provider-track-fc.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"provider tracking video").decode(),
            "clip_label": "Provider tracked broadcast",
            "match_context": "Imported YOLO/ByteTrack style tracking package.",
            "analysis_focus": "provider player tracking, ball tracking, player guidance",
        },
    )
    assert upload_response.status_code == 201
    video_asset = upload_response.json()

    import_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/tracking-provider-imports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "source_provider": "bytetrack_yolo_provider",
            "model_policy": "yolo-bytetrack-provider-import-v1",
            "replace_existing": True,
            "provider_metadata": {"detector": "yolov9", "tracker": "bytetrack", "camera_id": "main"},
            "quality_warnings": ["Provider confidence below match-publication threshold on two detections."],
            "frames": [
                {
                    "timestamp_seconds": 0,
                    "frame_index": 0,
                    "detections": [
                        {
                            "track_id": "home-9",
                            "team_label": "Home",
                            "player_label": "Forward",
                            "jersey_number": "9",
                            "bbox_x_percent": 10,
                            "bbox_y_percent": 40,
                            "bbox_width_percent": 4,
                            "bbox_height_percent": 18,
                            "confidence": 0.96,
                        },
                        {
                            "track_id": "away-4",
                            "team_label": "Opponent",
                            "player_label": "Center back",
                            "jersey_number": "4",
                            "foot_x_percent": 58,
                            "foot_y_percent": 58,
                            "confidence": 0.93,
                        },
                        {
                            "track_id": "ball",
                            "object_type": "ball",
                            "x_percent": 12,
                            "y_percent": 58,
                            "confidence": 0.88,
                        },
                    ],
                },
                {
                    "timestamp_seconds": 1,
                    "frame_index": 25,
                    "detections": [
                        {
                            "track_id": "home-9",
                            "team_label": "Home",
                            "player_label": "Forward",
                            "jersey_number": "9",
                            "bbox_x_percent": 24,
                            "bbox_y_percent": 39,
                            "bbox_width_percent": 4,
                            "bbox_height_percent": 18,
                            "confidence": 0.97,
                        },
                        {
                            "track_id": "away-4",
                            "team_label": "Opponent",
                            "player_label": "Center back",
                            "jersey_number": "4",
                            "foot_x_percent": 63,
                            "foot_y_percent": 57,
                            "confidence": 0.94,
                        },
                        {
                            "track_id": "ball",
                            "object_type": "ball",
                            "x_percent": 27,
                            "y_percent": 57,
                            "confidence": 0.9,
                        },
                    ],
                },
                {
                    "timestamp_seconds": 2,
                    "frame_index": 50,
                    "detections": [
                        {
                            "track_id": "home-9",
                            "team_label": "Home",
                            "player_label": "Forward",
                            "jersey_number": "9",
                            "bbox_x_percent": 40,
                            "bbox_y_percent": 39,
                            "bbox_width_percent": 4,
                            "bbox_height_percent": 18,
                            "confidence": 0.95,
                        },
                        {
                            "track_id": "away-4",
                            "team_label": "Opponent",
                            "player_label": "Center back",
                            "jersey_number": "4",
                            "foot_x_percent": 69,
                            "foot_y_percent": 56,
                            "confidence": 0.92,
                        },
                        {
                            "track_id": "ball",
                            "object_type": "ball",
                            "x_percent": 43,
                            "y_percent": 57,
                            "confidence": 0.9,
                        },
                    ],
                },
            ],
        },
    )

    assert import_response.status_code == 201
    tracking = import_response.json()
    assert tracking["source_provider"] == "bytetrack_yolo_provider"
    assert tracking["model_policy"] == "yolo-bytetrack-provider-import-v1"
    assert tracking["sample_count"] == 9
    assert tracking["player_count"] == 2
    assert tracking["total_distance_m"] > 20
    assert tracking["ball_tracking_metrics"]["ball_sample_count"] == 3
    assert any("Provider confidence" in warning for warning in tracking["quality_warnings"])
    forward = next(metric for metric in tracking["player_metrics"] if metric["track_id"] == "home-9")
    assert forward["player_label"] == "Forward"
    assert forward["distance_m"] > 20

    sample_export = client.get(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/export?export_format=samples_csv",
        headers=identity_headers,
    )
    assert sample_export.status_code == 200
    assert sample_export.headers["content-type"].startswith("text/csv")
    assert sample_export.headers["x-afrolete-match-tracking-export-checksum"]
    sample_rows = list(csv.DictReader(io.StringIO(sample_export.text)))
    assert len(sample_rows) == tracking["sample_count"]
    assert sample_rows[0]["track_id"] == "away-4"
    assert sample_rows[0]["x_meters"]

    metrics_export = client.get(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/export?export_format=player_metrics_csv",
        headers=identity_headers,
    )
    assert metrics_export.status_code == 200
    metric_rows = list(csv.DictReader(io.StringIO(metrics_export.text)))
    assert any(row["track_id"] == "home-9" and row["distance_m"] for row in metric_rows)

    json_export = client.get(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/export?export_format=analysis_json",
        headers=identity_headers,
    )
    assert json_export.status_code == 200
    exported = json_export.json()
    assert exported["tracking_run"]["id"] == tracking["id"]
    assert len(exported["samples"]) == tracking["sample_count"]
    assert exported["summary"]["player_metrics"]

    report_response = client.post(
        f"/api/v1/performance/scouting/tracking-runs/{tracking['id']}/analysis-reports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "audience": "player",
            "report_scope": "provider_tracking_review",
            "title": "Provider tracking player report",
            "include_player_cards": True,
            "include_tactical_shape": True,
        },
    )
    assert report_response.status_code == 201
    report = report_response.json()
    assert report["summary"]["player_count"] == 2
    assert any(card["track_id"] == "home-9" for card in report["player_cards"])


def test_match_tracking_provider_webhook_is_signed_and_replay_safe(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    performance_service.get_settings.cache_clear()
    monkeypatch.setenv("AFROLETE_PERFORMANCE_MATCH_TRACKING_WEBHOOK_SIGNING_KEY", "tracking-secret")
    performance_service.get_settings.cache_clear()
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    upload_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Webhook Camera FC",
            "sport": "football",
            "filename": "webhook-camera-fc.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"webhook tracking video").decode(),
            "clip_label": "Signed provider callback",
            "match_context": "External camera posts tracking frames.",
            "analysis_focus": "provider callback replay and player metrics",
        },
    )
    assert upload_response.status_code == 201
    video_asset = upload_response.json()
    payload = {
        "organization_id": organization["id"],
        "video_asset_id": video_asset["id"],
        "external_event_id": "camera-main-match-2026-05-30T10:00:00Z",
        "source_provider": "camera_bytetrack",
        "model_policy": "camera-bytetrack-provider-v1",
        "replace_existing": True,
        "provider_metadata": {"camera_id": "main-stand", "detector": "yolov9"},
        "frames": [
            {
                "timestamp_seconds": 0,
                "frame_index": 0,
                "detections": [
                    {
                        "track_id": "home-7",
                        "team_label": "Home",
                        "player_label": "Winger",
                        "jersey_number": "7",
                        "foot_x_percent": 20,
                        "foot_y_percent": 52,
                        "confidence": 0.95,
                    },
                    {
                        "track_id": "ball",
                        "object_type": "ball",
                        "x_percent": 22,
                        "y_percent": 52,
                        "confidence": 0.86,
                    },
                ],
            },
            {
                "timestamp_seconds": 1,
                "frame_index": 25,
                "detections": [
                    {
                        "track_id": "home-7",
                        "team_label": "Home",
                        "player_label": "Winger",
                        "jersey_number": "7",
                        "foot_x_percent": 36,
                        "foot_y_percent": 50,
                        "confidence": 0.96,
                    },
                    {
                        "track_id": "ball",
                        "object_type": "ball",
                        "x_percent": 38,
                        "y_percent": 50,
                        "confidence": 0.87,
                    },
                ],
            },
        ],
    }
    raw_body = json.dumps(payload, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"tracking-secret",
        timestamp.encode() + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Afrolete-Performance-Timestamp": timestamp,
        "X-Afrolete-Performance-Signature": f"sha256={signature}",
    }

    response = client.post("/api/v1/performance/webhooks/match-tracking", content=raw_body, headers=headers)

    assert response.status_code == 202
    ingest = response.json()
    assert ingest["source_provider"] == "camera_bytetrack"
    assert ingest["external_event_id"] == payload["external_event_id"]
    assert ingest["replayed"] is False
    assert ingest["signature_required"] is True
    assert ingest["signature_validated"] is True
    assert ingest["sample_count"] == 4
    assert ingest["player_count"] == 1
    assert ingest["tracking_run"]["source_provider"] == "camera_bytetrack"
    assert ingest["tracking_run"]["player_metrics"][0]["track_id"] == "home-7"

    replay = client.post("/api/v1/performance/webhooks/match-tracking", content=raw_body, headers=headers)

    assert replay.status_code == 202
    replay_body = replay.json()
    assert replay_body["replayed"] is True
    assert replay_body["tracking_run_id"] == ingest["tracking_run_id"]
    assert replay_body["sample_count"] == 4

    runs = client.get(
        f"/api/v1/performance/scouting/tracking-runs?organization_id={organization['id']}"
        f"&video_asset_id={video_asset['id']}",
        headers=identity_headers,
    )
    assert runs.status_code == 200
    assert len(runs.json()) == 1

    audit_response = client.get(
        f"/api/v1/performance/scouting/tracking-provider-ingests?organization_id={organization['id']}"
        f"&video_asset_id={video_asset['id']}",
        headers=identity_headers,
    )
    assert audit_response.status_code == 200
    audit_rows = audit_response.json()
    assert len(audit_rows) == 1
    assert audit_rows[0]["source_provider"] == "camera_bytetrack"
    assert audit_rows[0]["external_event_id"] == payload["external_event_id"]
    assert audit_rows[0]["tracking_run_id"] == ingest["tracking_run_id"]
    assert audit_rows[0]["signature_required"] is True
    assert audit_rows[0]["signature_validated"] is True
    assert audit_rows[0]["sample_count"] == 4
    assert audit_rows[0]["player_count"] == 1
    assert audit_rows[0]["payload_hash"]
    assert audit_rows[0]["payload_available"] is True
    assert audit_rows[0]["frame_count"] == 2

    reprocess_response = client.post(
        f"/api/v1/performance/scouting/tracking-provider-ingests/{audit_rows[0]['id']}/reprocess",
        headers=identity_headers,
        json={"notes": "Reprocess after calibration review."},
    )
    assert reprocess_response.status_code == 200
    reprocessed = reprocess_response.json()
    assert reprocessed["reprocessed"] is True
    assert reprocessed["tracking_run_id"] != ingest["tracking_run_id"]
    assert reprocessed["sample_count"] == 4
    assert reprocessed["tracking_run"]["model_policy"].endswith("-reprocess")

    runs_after_reprocess = client.get(
        f"/api/v1/performance/scouting/tracking-runs?organization_id={organization['id']}"
        f"&video_asset_id={video_asset['id']}",
        headers=identity_headers,
    )
    assert runs_after_reprocess.status_code == 200
    run_rows = runs_after_reprocess.json()
    assert len(run_rows) == 2
    assert any(row["status"] == "superseded" for row in run_rows)

    audit_after_reprocess = client.get(
        f"/api/v1/performance/scouting/tracking-provider-ingests?organization_id={organization['id']}"
        f"&video_asset_id={video_asset['id']}",
        headers=identity_headers,
    )
    assert audit_after_reprocess.status_code == 200
    audit_row = audit_after_reprocess.json()[0]
    assert audit_row["status"] == "reprocessed"
    assert audit_row["tracking_run_id"] == reprocessed["tracking_run_id"]
    assert audit_row["payload_available"] is True
    performance_service.get_settings.cache_clear()


def test_match_tracking_provider_webhook_rejects_bad_signature(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    performance_service.get_settings.cache_clear()
    monkeypatch.setenv("AFROLETE_PERFORMANCE_MATCH_TRACKING_WEBHOOK_SIGNING_KEY", "tracking-secret")
    performance_service.get_settings.cache_clear()
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    video_asset = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Bad Signature FC",
            "sport": "football",
            "filename": "bad-signature-fc.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"bad signature video").decode(),
            "clip_label": "Bad provider callback",
            "match_context": "External camera posts tracking frames.",
            "analysis_focus": "signature validation",
        },
    ).json()
    payload = {
        "organization_id": organization["id"],
        "video_asset_id": video_asset["id"],
        "external_event_id": "bad-signature-event",
        "source_provider": "camera_bytetrack",
        "frames": [
            {
                "timestamp_seconds": 0,
                "detections": [
                    {
                        "track_id": "home-7",
                        "team_label": "Home",
                        "foot_x_percent": 20,
                        "foot_y_percent": 52,
                    }
                ],
            }
        ],
    }

    response = client.post(
        "/api/v1/performance/webhooks/match-tracking",
        json=payload,
        headers={
            "X-Afrolete-Performance-Timestamp": str(int(time.time())),
            "X-Afrolete-Performance-Signature": "sha256=invalid",
        },
    )

    assert response.status_code == 401
    performance_service.get_settings.cache_clear()


def test_match_tracking_derives_shot_xg_and_key_pass_network() -> None:
    samples = [
        {
            "track_id": "home-8",
            "team_label": "Home",
            "player_label": "Midfielder",
            "timestamp_seconds": 0,
            "x_percent": 40,
            "y_percent": 50,
            "x_meters": 40,
            "y_meters": 25,
        },
        {
            "track_id": "home-9",
            "team_label": "Home",
            "player_label": "Forward",
            "timestamp_seconds": 0,
            "x_percent": 70,
            "y_percent": 50,
            "x_meters": 70,
            "y_meters": 25,
        },
        {
            "track_id": "home-9",
            "team_label": "Home",
            "player_label": "Forward",
            "timestamp_seconds": 1,
            "x_percent": 70,
            "y_percent": 50,
            "x_meters": 70,
            "y_meters": 25,
        },
        {
            "track_id": "home-9",
            "team_label": "Home",
            "player_label": "Forward",
            "timestamp_seconds": 2,
            "x_percent": 82,
            "y_percent": 50,
            "x_meters": 82,
            "y_meters": 25,
        },
        {
            "track_id": "away-5",
            "team_label": "Away",
            "player_label": "Defender",
            "timestamp_seconds": 3,
            "x_percent": 60,
            "y_percent": 50,
            "x_meters": 60,
            "y_meters": 25,
        },
        {
            "track_id": "ball",
            "team_label": "ball",
            "player_label": "Ball",
            "timestamp_seconds": 0,
            "x_percent": 40,
            "y_percent": 50,
            "x_meters": 40,
            "y_meters": 25,
        },
        {
            "track_id": "ball",
            "team_label": "ball",
            "player_label": "Ball",
            "timestamp_seconds": 1,
            "x_percent": 70,
            "y_percent": 50,
            "x_meters": 70,
            "y_meters": 25,
        },
        {
            "track_id": "ball",
            "team_label": "ball",
            "player_label": "Ball",
            "timestamp_seconds": 2,
            "x_percent": 98,
            "y_percent": 50,
            "x_meters": 98,
            "y_meters": 25,
        },
        {
            "track_id": "ball",
            "team_label": "ball",
            "player_label": "Ball",
            "timestamp_seconds": 3,
            "x_percent": 60,
            "y_percent": 50,
            "x_meters": 60,
            "y_meters": 25,
        },
    ]

    summary = performance_service.summarize_match_tracking_samples(samples)

    assert summary["ball_tracking_metrics"]["pass_count"] == 1
    assert summary["ball_tracking_metrics"]["pass_attempt_count"] == 2
    assert summary["ball_tracking_metrics"]["pass_accuracy_percent"] == 50.0
    assert summary["ball_tracking_metrics"]["interception_count"] == 1
    assert summary["ball_tracking_metrics"]["shot_count"] == 1
    assert summary["ball_tracking_metrics"]["shot_on_target_count"] == 1
    assert summary["ball_tracking_metrics"]["expected_goals"] > 0.3
    assert summary["chance_creation_metrics"]["key_pass_count"] == 1
    assert summary["shot_events"][0]["shooter_track_id"] == "home-9"
    assert summary["shot_events"][0]["target_goal"] == "right"
    assert summary["shot_events"][0]["on_target"] is True
    assert summary["pass_network"][0]["from_track_id"] == "home-8"
    assert summary["pass_network"][0]["to_track_id"] == "home-9"
    assert summary["pass_network"][0]["key_pass_count"] == 1
    assert summary["pass_type_metrics"][0]["team_label"] == "Home"
    assert summary["pass_type_metrics"][0]["attempt_count"] == 1
    assert {event["defensive_action_type"] for event in summary["defensive_action_events"]} == {"interception"}
    midfielder = next(metric for metric in summary["player_metrics"] if metric["track_id"] == "home-8")
    forward = next(metric for metric in summary["player_metrics"] if metric["track_id"] == "home-9")
    defender = next(metric for metric in summary["player_metrics"] if metric["track_id"] == "away-5")
    assert midfielder["key_pass_count"] == 1
    assert midfielder["expected_assists"] == summary["shot_events"][0]["expected_goals"]
    assert midfielder["pass_attempt_count"] == 1
    assert midfielder["pass_accuracy_percent"] == 100.0
    assert forward["shot_count"] == 1
    assert forward["expected_goals"] == summary["shot_events"][0]["expected_goals"]
    assert forward["pass_attempt_count"] == 1
    assert forward["pass_accuracy_percent"] == 0.0
    assert defender["interception_count"] == 1


def test_match_tracking_contour_classifier_separates_ball_and_player_candidates() -> None:
    frame_area = 1920 * 1080

    ball = performance_service.match_tracking_contour_kind(
        area=900,
        width=32,
        height=31,
        perimeter=100,
        frame_area=frame_area,
        min_detection_confidence=0.35,
    )
    player = performance_service.match_tracking_contour_kind(
        area=12000,
        width=42,
        height=190,
        perimeter=470,
        frame_area=frame_area,
        min_detection_confidence=0.35,
    )
    noise = performance_service.match_tracking_contour_kind(
        area=8,
        width=4,
        height=3,
        perimeter=14,
        frame_area=frame_area,
        min_detection_confidence=0.35,
    )

    assert ball is not None
    assert ball[0] == "ball"
    assert player is not None
    assert player[0] == "player"
    assert noise is None
    assert performance_service.select_match_ball_candidate(
        [(100, 100, 0.8), (220, 220, 0.9)],
        previous_ball=(105, 104),
    ) == (100, 100, 0.8)


def test_match_tracking_assigns_team_labels_from_jersey_color_clusters() -> None:
    frame = np.zeros((140, 100, 3), dtype=np.uint8)
    frame[28:68, 35:65] = (20, 35, 220)

    color = performance_service.match_tracking_jersey_color_signature(frame, 20, 20, 60, 100)
    assert color is not None
    assert color[0] > 180

    samples = [
        {
            "track_id": "blue-1",
            "team_label": None,
            "player_label": "Track blue-1",
            "timestamp_seconds": 0,
            "x_percent": 10,
            "y_percent": 40,
            "jersey_color_rgb": (20, 70, 220),
        },
        {
            "track_id": "blue-2",
            "team_label": None,
            "player_label": "Track blue-2",
            "timestamp_seconds": 0,
            "x_percent": 12,
            "y_percent": 50,
            "jersey_color_rgb": (25, 80, 210),
        },
        {
            "track_id": "red-1",
            "team_label": None,
            "player_label": "Track red-1",
            "timestamp_seconds": 0,
            "x_percent": 60,
            "y_percent": 40,
            "jersey_color_rgb": (220, 45, 25),
        },
        {
            "track_id": "ball",
            "team_label": "ball",
            "player_label": "Ball",
            "timestamp_seconds": 0,
            "x_percent": 30,
            "y_percent": 45,
        },
    ]

    labelled = performance_service.assign_match_tracking_team_labels(samples)
    labels = {sample["track_id"]: sample["team_label"] for sample in labelled}

    assert labels["blue-1"] == labels["blue-2"]
    assert labels["blue-1"] != labels["red-1"]
    assert {labels["blue-1"], labels["red-1"]} == {"Team A", "Team B"}
    assert labels["ball"] == "ball"
    assert next(sample for sample in labelled if sample["track_id"] == "blue-1")["player_label"].startswith("Team ")


def test_match_video_highlight_reel_uses_tracking_and_scouting_signals(client, identity_headers, monkeypatch) -> None:
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    upload_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Highlight City",
            "sport": "football",
            "filename": "highlight-city.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"highlight match video").decode(),
            "clip_label": "Highlight feed",
            "match_context": "Pressing opponent with late fatigue and weak-side space.",
            "analysis_focus": "automated highlights, pressing, sprint actions, tactical threats",
        },
    )
    assert upload_response.status_code == 201
    video_asset = upload_response.json()

    report_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/reports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "observed_formation": "4-3-3",
            "match_context": "Opponent tires late and leaves space behind the fullbacks.",
            "analysis_focus": "pressing triggers, transition defense, set pieces",
            "evidence_text": "High press, weak-side fullback space, late-game fatigue after 70 minutes.",
        },
    )
    assert report_response.status_code == 201

    tracking_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/tracking-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "source_provider": "provider_tracking_import",
            "replace_existing": True,
            "samples": [
                {"track_id": "home-7", "team_label": "Home", "player_label": "Winger", "jersey_number": "7", "timestamp_seconds": 0, "x_meters": 10, "y_meters": 20},
                {"track_id": "home-7", "team_label": "Home", "player_label": "Winger", "jersey_number": "7", "timestamp_seconds": 1, "x_meters": 20, "y_meters": 20},
                {"track_id": "home-7", "team_label": "Home", "player_label": "Winger", "jersey_number": "7", "timestamp_seconds": 2, "x_meters": 31, "y_meters": 21},
                {"track_id": "away-10", "team_label": "Opponent", "player_label": "Playmaker", "jersey_number": "10", "timestamp_seconds": 0, "x_meters": 60, "y_meters": 40},
                {"track_id": "away-10", "team_label": "Opponent", "player_label": "Playmaker", "jersey_number": "10", "timestamp_seconds": 1, "x_meters": 56, "y_meters": 37},
                {"track_id": "away-10", "team_label": "Opponent", "player_label": "Playmaker", "jersey_number": "10", "timestamp_seconds": 2, "x_meters": 52, "y_meters": 34},
            ],
        },
    )
    assert tracking_response.status_code == 201
    tracking = tracking_response.json()

    reel_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/highlight-reels",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "tracking_run_id": tracking["id"],
            "audience": "scout",
            "purpose": "recruiting",
            "target_duration_seconds": 75,
            "channels": ["coach_review", "scout_packet"],
            "tags": ["wide-play", "transition"],
            "branding": {"club": "AfroLete Demo"},
        },
    )
    assert reel_response.status_code == 201
    reel = reel_response.json()
    assert reel["status"] == "generated"
    assert reel["clip_count"] >= 3
    assert reel["duration_seconds"] <= 75
    assert reel["distribution"]["share_policy"] == "guardian_approval_required"
    assert "scout_packet" in reel["distribution"]["channels"]
    assert any(clip["category"] == "high_speed_run" for clip in reel["clips"])
    assert any("scouting" in clip["tags"] for clip in reel["clips"])

    timeline_response = client.post(
        f"/api/v1/performance/scouting/highlight-reels/{reel['id']}/exports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "export_format": "timeline_json",
            "delivery_channel": "scout_packet",
            "notes": "Test export for a scout packet.",
        },
    )
    assert timeline_response.status_code == 201
    timeline = timeline_response.json()
    assert timeline["status"] == "rendered"
    assert timeline["export_format"] == "timeline_json"
    assert timeline["filename"].endswith("-timeline.json")
    assert timeline["content_type"] == "application/json"
    assert timeline["size_bytes"] > 100
    assert len(timeline["checksum"]) == 64
    assert timeline["manifest"]["reel"]["id"] == reel["id"]
    assert timeline["manifest"]["source_video"]["id"] == video_asset["id"]

    edl_response = client.post(
        f"/api/v1/performance/scouting/highlight-reels/{reel['id']}/exports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "export_format": "mp4",
            "delivery_channel": "coach_review",
        },
    )
    assert edl_response.status_code == 201
    edl = edl_response.json()
    assert edl["export_format"] == "mp4_edit_decision_list"
    assert edl["status"] == "needs_renderer"
    assert edl["manifest"]["renderer_status"] == "needs_renderer"
    assert len(edl["manifest"]["edit_decisions"]) == reel["clip_count"]

    monkeypatch.setattr(performance_service.shutil, "which", lambda path: path)

    def fake_ffmpeg_run(command, **kwargs):
        output_path = command[-1]
        if str(output_path).endswith(".mp4"):
            with open(output_path, "wb") as handle:
                handle.write(b"fake rendered afrolete highlight reel")
        return performance_service.subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(performance_service.subprocess, "run", fake_ffmpeg_run)
    render_response = client.post(
        f"/api/v1/performance/scouting/highlight-reel-exports/{edl['id']}/render",
        headers=identity_headers,
    )
    assert render_response.status_code == 201
    rendered = render_response.json()
    assert rendered["export_format"] == "mp4_render"
    assert rendered["status"] == "rendered"
    assert rendered["content_type"] == "video/mp4"
    assert rendered["filename"].endswith("-render.mp4")
    assert rendered["manifest"]["source_export_id"] == edl["id"]

    rendered_download = client.get(
        f"/api/v1/performance/scouting/highlight-reel-exports/{rendered['id']}/content",
        headers=identity_headers,
    )
    assert rendered_download.status_code == 200
    assert rendered_download.content == b"fake rendered afrolete highlight reel"

    exports = client.get(
        f"/api/v1/performance/scouting/highlight-reel-exports?organization_id={organization['id']}&highlight_reel_id={reel['id']}",
        headers=identity_headers,
    )
    assert exports.status_code == 200
    assert {artifact["id"] for artifact in exports.json()} == {timeline["id"], edl["id"], rendered["id"]}

    download_response = client.get(
        f"/api/v1/performance/scouting/highlight-reel-exports/{timeline['id']}/content",
        headers=identity_headers,
    )
    assert download_response.status_code == 200
    assert download_response.headers["X-Afrolete-Highlight-Export-Checksum"] == timeline["checksum"]
    downloaded = json.loads(download_response.content)
    assert downloaded["reel"]["title"] == reel["title"]

    reels = client.get(
        f"/api/v1/performance/scouting/highlight-reels?organization_id={organization['id']}&video_asset_id={video_asset['id']}",
        headers=identity_headers,
    )
    assert reels.status_code == 200
    assert reels.json()[0]["id"] == reel["id"]


def test_performance_hardware_kit_device_sync_creates_tracking_run(client, identity_headers) -> None:
    organization, team, _, _ = create_rostered_athlete(client, identity_headers)
    video_response = client.post(
        "/api/v1/performance/scouting/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "opponent_name": "Hardware City",
            "sport": "football",
            "filename": "hardware-city.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(b"hardware sync match video").decode(),
            "clip_label": "Hardware tracking feed",
            "match_context": "Camera and GPS synced match sample.",
            "analysis_focus": "hardware tracking samples, distance, speed, acceleration",
        },
    )
    assert video_response.status_code == 201
    video_asset = video_response.json()

    calibration_response = client.post(
        f"/api/v1/performance/scouting/videos/{video_asset['id']}/pitch-calibrations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Veo halfway camera",
            "pitch_length_m": 100,
            "pitch_width_m": 50,
            "points": [
                {"label": "top left", "image_x_percent": 0, "image_y_percent": 0, "pitch_x_meters": 0, "pitch_y_meters": 0},
                {"label": "top right", "image_x_percent": 100, "image_y_percent": 0, "pitch_x_meters": 100, "pitch_y_meters": 0},
                {"label": "bottom right", "image_x_percent": 100, "image_y_percent": 100, "pitch_x_meters": 100, "pitch_y_meters": 50},
                {"label": "bottom left", "image_x_percent": 0, "image_y_percent": 100, "pitch_x_meters": 0, "pitch_y_meters": 50},
            ],
        },
    )
    assert calibration_response.status_code == 201
    calibration = calibration_response.json()

    kit_response = client.post(
        "/api/v1/performance/hardware-kits",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Football match analysis kit",
            "kit_type": "hybrid",
            "provider": "veo",
            "sport": "football",
            "level": "club",
            "recommended_camera_count": 2,
            "recommended_gps_unit_count": 24,
            "supported_metrics": ["speed", "distance", "acceleration", "heatmap"],
            "setup_steps": ["Mount cameras", "Pair GPS units", "Run pitch calibration"],
            "estimated_cost": 4200,
            "currency": "USD",
        },
    )
    assert kit_response.status_code == 201
    kit = kit_response.json()
    assert kit["recommended_gps_unit_count"] == 24
    assert "heatmap" in kit["supported_metrics"]

    device_response = client.post(
        "/api/v1/performance/hardware-devices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "kit_id": kit["id"],
            "team_id": team["id"],
            "device_type": "camera",
            "provider": "veo",
            "device_label": "Veo Cam 1",
            "external_device_id": "veo-cam-001",
            "api_key": "sample-api-key",
            "api_key_secret_path": "secret/data/afrolete/performance/devices/veo-cam-001",
            "metrics_supported": ["player_location", "distance", "speed", "heatmap"],
            "calibration_id": calibration["id"],
            "battery_percent": 91,
        },
    )
    assert device_response.status_code == 201
    device = device_response.json()
    assert device["api_key_configured"] is True
    assert device["calibration_id"] == calibration["id"]

    sync_response = client.post(
        f"/api/v1/performance/hardware-devices/{device['id']}/sync-runs",
        headers=identity_headers,
        json={
            "video_asset_id": video_asset["id"],
            "sync_mode": "match_tracking_payload",
            "battery_percent": 84,
            "metrics": {"camera_uptime_minutes": 92},
            "tracking_samples": [
                {"track_id": "home-11", "team_label": "Home", "player_label": "Winger", "jersey_number": "11", "timestamp_seconds": 0, "x_percent": 10, "y_percent": 30},
                {"track_id": "home-11", "team_label": "Home", "player_label": "Winger", "jersey_number": "11", "timestamp_seconds": 1, "x_percent": 19, "y_percent": 30},
                {"track_id": "home-11", "team_label": "Home", "player_label": "Winger", "jersey_number": "11", "timestamp_seconds": 2, "x_percent": 28, "y_percent": 30},
            ],
        },
    )
    assert sync_response.status_code == 202
    sync = sync_response.json()
    assert sync["status"] == "completed"
    assert sync["sample_count"] == 3
    assert sync["metrics_ingested"] == 1
    assert sync["tracking_run_id"] is not None
    assert sync["tracking_run"]["source_provider"] == "veo_camera_hardware"
    assert sync["tracking_run"]["player_metrics"][0]["player_label"] == "Winger"

    devices = client.get(
        f"/api/v1/performance/hardware-devices?organization_id={organization['id']}&kit_id={kit['id']}",
        headers=identity_headers,
    )
    assert devices.status_code == 200
    assert devices.json()[0]["last_seen_at"] is not None
    assert devices.json()[0]["battery_percent"] == 84


def test_performance_video_upload_pose_gait_analysis_and_annotations(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    organization, _, _, roster = create_rostered_athlete(client, identity_headers)
    video_bytes = b"fake mp4 sprint clip"
    upload = client.post(
        f"/api/v1/performance/athletes/{roster['athlete_profile_id']}/videos",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "athletics",
            "filename": "sprint-start.mp4",
            "content_type": "video/mp4",
            "content_base64": base64.b64encode(video_bytes).decode(),
            "clip_label": "Sprint start side view",
            "analysis_focus": "pose, gait, front knee drive, ground contact",
            "duration_seconds": 8,
            "frame_rate": 120,
            "frame_width": 1920,
            "frame_height": 1080,
        },
    )

    assert upload.status_code == 201
    video_asset = upload.json()
    assert video_asset["video_uri"].startswith("performance-video://")
    assert video_asset["slow_motion_rates"] == [0.125, 0.25, 0.5, 0.75, 1.0]

    annotation = client.post(
        f"/api/v1/performance/videos/{video_asset['id']}/annotations",
        headers=identity_headers,
        json={
            "timestamp_seconds": 2.25,
            "playback_rate": 0.25,
            "annotation_type": "pose_correction",
            "label": "Torso collapse",
            "notes": "Pause here and compare trunk line with the optimal projection.",
            "body_region": "torso",
            "x_percent": 42,
            "y_percent": 18,
            "width_percent": 18,
            "height_percent": 40,
            "tags": ["posture", "slow-motion"],
        },
    )
    assert annotation.status_code == 201
    assert annotation.json()["tags"] == ["posture", "slow-motion"]

    def sprint_pose_sample(timestamp: float, foot: str, stride_index: int) -> dict[str, object]:
        return {
            "source_provider": "mediapipe_pose_solution",
            "timestamp_seconds": timestamp,
            "phase": "ground_contact",
            "contact_foot": foot,
            "stride_index": stride_index,
            "sample_confidence": 0.91,
            "keypoints": [
                {"name": "left_shoulder", "x_percent": 45, "y_percent": 30, "confidence": 0.96},
                {"name": "right_shoulder", "x_percent": 55, "y_percent": 30, "confidence": 0.96},
                {"name": "left_hip", "x_percent": 48, "y_percent": 50, "confidence": 0.95},
                {"name": "right_hip", "x_percent": 58, "y_percent": 50, "confidence": 0.95},
                {"name": "left_knee", "x_percent": 58, "y_percent": 40, "confidence": 0.93},
                {"name": "right_knee", "x_percent": 56, "y_percent": 61, "confidence": 0.92},
                {"name": "left_ankle", "x_percent": 62, "y_percent": 72, "confidence": 0.91},
                {"name": "right_ankle", "x_percent": 54, "y_percent": 76, "confidence": 0.91},
                {"name": "left_elbow", "x_percent": 42, "y_percent": 45, "confidence": 0.9},
                {"name": "right_elbow", "x_percent": 58, "y_percent": 45, "confidence": 0.9},
            ],
        }

    extracted_samples = [
        sprint_pose_sample(1.00, "left", 0),
        sprint_pose_sample(1.10, "left", 0),
        sprint_pose_sample(1.23, "right", 1),
        sprint_pose_sample(1.33, "right", 1),
        sprint_pose_sample(1.45, "left", 2),
        sprint_pose_sample(1.55, "left", 2),
        sprint_pose_sample(1.68, "right", 3),
        sprint_pose_sample(1.78, "right", 3),
    ]

    def fake_extract_pose_samples_from_video_content(*args, **kwargs) -> dict[str, object]:
        return {
            "samples": extracted_samples,
            "decoded_frame_count": 24,
            "processed_frame_count": 8,
            "frame_rate": 120,
            "frame_count": 960,
            "duration_seconds": 8.0,
            "warnings": [],
            "source_provider": "mediapipe_pose_solution",
            "model_policy": "mediapipe-pose-solution-v1",
        }

    monkeypatch.setattr(
        performance_service,
        "extract_pose_samples_from_video_content",
        fake_extract_pose_samples_from_video_content,
    )
    pose_processing = client.post(
        f"/api/v1/performance/videos/{video_asset['id']}/pose-processing-runs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "replace_existing": True,
            "max_frames": 45,
            "sample_every_seconds": 0.2,
            "run_analysis": False,
        },
    )
    assert pose_processing.status_code == 201
    processed = pose_processing.json()
    assert processed["model_policy"] == "mediapipe-pose-solution-v1"
    assert processed["source_provider"] == "mediapipe_pose_solution"
    assert processed["processed_frame_count"] == 8
    assert processed["decoded_frame_count"] == 24
    assert processed["sample_count"] == 8
    assert processed["pose_samples"]["sample_count"] == 8
    assert processed["pose_samples"]["source_providers"] == ["mediapipe_pose_solution"]

    reference_profile = client.post(
        "/api/v1/performance/movement-reference-profiles",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "athletics",
            "name": "Elite 100m side-view profile",
            "benchmark_profile": "world_class_sprint",
            "performer_name": "Reference sprinter",
            "source_label": "World-class 100m final side-view model",
            "competition_context": "championship final",
            "consent_basis": "licensed coaching reference",
            "metric_targets": [
                {
                    "key": "torso_lean_angle",
                    "label": "Torso Lean Angle",
                    "category": "technical",
                    "unit": "degrees",
                    "optimal_min": 9,
                    "optimal_max": 13,
                    "benchmark_label": "reference sprinter max-velocity posture",
                    "coaching_cue": "Hold the trunk tall through mid-stance.",
                },
                {
                    "key": "ground_contact_time",
                    "label": "Ground Contact Time",
                    "category": "physical",
                    "unit": "ms",
                    "optimal_min": 85,
                    "optimal_max": 105,
                    "benchmark_label": "reference sprinter contact window",
                    "coaching_cue": "Strike down and back under the hip.",
                },
            ],
        },
    )
    assert reference_profile.status_code == 201
    assert reference_profile.json()["source_label"] == "World-class 100m final side-view model"

    analysis = client.post(
        f"/api/v1/performance/videos/{video_asset['id']}/pose-gait-analysis",
        headers=identity_headers,
        json={
            "benchmark_profile": "world_class_sprint",
            "reference_profile_id": reference_profile.json()["id"],
            "evidence_text": (
                "Torso lean angle 18 degrees with late torso collapse. "
                "Front knee drive 64 degrees. Ground contact time 138 ms. "
                "Arm swing symmetry 6.5 with cross-body movement. Stride frequency 4.1 Hz."
            ),
            "create_coaching_outputs": True,
        },
    )

    assert analysis.status_code == 201
    payload = analysis.json()
    assert payload["video_asset"]["status"] == "analyzed"
    assert payload["benchmark_profile"] == "world_class_sprint"
    assert payload["reference_profile_name"] == "Elite 100m side-view profile"
    assert payload["reference_profile_source"] == "World-class 100m final side-view model"
    assert payload["pose_sample_count"] == 8
    assert payload["pose_sample_source_providers"] == ["mediapipe_pose_solution"]
    assert payload["model_policy"] == "afrolete-pose-gait-keypoints-v1"
    assert len(payload["metrics"]) >= 5
    assert any(
        metric["key"] == "ground_contact_time"
        and metric["source"] == "pose_keypoints"
        and metric["optimal_max"] == 105
        for metric in payload["metrics"]
    )
    assert payload["optimal_projections"]
    assert payload["annotations"][0]["label"] == "Torso collapse"
    assert payload["coaching"]["review_required"] is True
    assert len(payload["coaching"]["observations"]) == 5


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
