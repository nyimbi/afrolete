def test_coach_voice_commands_process_match_intents_and_shortcuts(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Voice Command FC",
            "slug": "voice-command-fc",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    home_team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Voice Command FC U17",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    away_team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "City FC U17",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    competition = client.post(
        "/api/v1/competitions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Voice Command League",
            "sport": "football",
            "competition_type": "league",
            "format": "round_robin",
            "season_label": "2026",
            "starts_on": "2026-06-01",
            "ends_on": "2026-08-31",
            "tiebreakers": "Points, goal difference, goals for",
        },
    ).json()
    for seed, team in enumerate([home_team, away_team], start=1):
        participant_response = client.post(
            f"/api/v1/competitions/{competition['id']}/participants",
            headers=identity_headers,
            json={"team_id": team["id"], "seed": seed, "group_label": "A"},
        )
        assert participant_response.status_code == 201
    fixture = client.post(
        f"/api/v1/competitions/{competition['id']}/fixtures",
        headers=identity_headers,
        json={
            "home_team_id": home_team["id"],
            "away_team_id": away_team["id"],
            "round_label": "Round 1",
            "stage_label": "League",
            "scheduled_at": "2026-06-05T16:00:00Z",
            "venue_name": "City Stadium",
        },
    ).json()

    session_response = client.post(
        "/api/v1/voice-commands/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": home_team["id"],
            "session_label": "City FC match voice desk",
            "context_type": "match",
            "input_device": "sideline_headset",
            "listening_mode": "push_to_talk",
            "consent_recorded": True,
        },
    )
    assert session_response.status_code == 201
    session = session_response.json()
    assert session["raw_audio_retention_policy"] == "delete_raw_audio_after_transcription"
    assert session["command_count"] == 0

    goal_response = client.post(
        f"/api/v1/voice-commands/sessions/{session['id']}/commands",
        headers=identity_headers,
        json={
            "transcript": "Goal for Emma in minute 62",
            "source_device": "coach_watch",
            "latency_ms": 280,
        },
    )
    assert goal_response.status_code == 201
    goal = goal_response.json()
    assert goal["intent"] == "score_event"
    assert goal["confidence"] >= 0.85
    assert goal["requires_confirmation"] is True
    assert goal["command_status"] == "needs_confirmation"
    assert goal["entities"]["player_label"] == "Emma"
    assert goal["entities"]["minute"] == 62
    assert goal["action_result"]["action"] == "prepared_official_record_change"
    assert goal["action_result"]["official_record_mutated"] is False
    assert "Review" in goal["response_text"]

    review_response = client.post(
        f"/api/v1/voice-commands/commands/{goal['id']}/review",
        headers=identity_headers,
        json={
            "decision": "confirm",
            "notes": "Coach reviewed replay and confirmed scorer.",
            "fixture_id": fixture["id"],
            "team_id": home_team["id"],
            "apply_to_official_record": True,
        },
    )
    assert review_response.status_code == 200
    reviewed_goal = review_response.json()
    assert reviewed_goal["command_status"] == "confirmed"
    assert reviewed_goal["review_decision"] == "confirm"
    assert reviewed_goal["confirmed_at"] is not None
    assert reviewed_goal["review_result"]["applied_to_official_record"] is True
    assert reviewed_goal["review_result"]["match_event_type"] == "goal"

    fixture_events_response = client.get(
        f"/api/v1/competitions/fixtures/{fixture['id']}/events",
        headers=identity_headers,
    )
    assert fixture_events_response.status_code == 200
    fixture_events = fixture_events_response.json()
    assert fixture_events[0]["event_type"] == "goal"
    assert fixture_events[0]["team_id"] == home_team["id"]
    assert fixture_events[0]["minute"] == 62
    assert "Goal for Emma" in fixture_events[0]["description"]

    safety_response = client.post(
        f"/api/v1/voice-commands/sessions/{session['id']}/commands",
        headers=identity_headers,
        json={"transcript": "Log injury: ankle sprain for Sarah"},
    )
    assert safety_response.status_code == 201
    safety = safety_response.json()
    assert safety["intent"] == "injury_log"
    assert "medical_or_emergency_language_detected" in safety["safety_flags"]
    assert safety["permission_scope"] == "competition_official_log_review"

    shortcut_response = client.post(
        "/api/v1/voice-commands/shortcuts",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "phrase": "time for fresh legs",
            "intent": "custom_command",
            "action_sequence": [
                "check_fatigue",
                "suggest_substitution",
                "alert_assistant_coach",
            ],
            "parameters": {"fatigue_threshold": 70},
            "trained_sample_count": 5,
        },
    )
    assert shortcut_response.status_code == 201
    shortcut = shortcut_response.json()
    assert shortcut["action_sequence"][0] == "check_fatigue"
    assert shortcut["parameters"]["fatigue_threshold"] == 70

    custom_response = client.post(
        f"/api/v1/voice-commands/sessions/{session['id']}/commands",
        headers=identity_headers,
        json={"transcript": "Time for fresh legs"},
    )
    assert custom_response.status_code == 201
    custom = custom_response.json()
    assert custom["intent"] == "custom_command"
    assert custom["action_result"]["action"] == "custom_command_sequence_prepared"
    assert custom["action_result"]["sequence"] == [
        "check_fatigue",
        "suggest_substitution",
        "alert_assistant_coach",
    ]

    sessions_response = client.get(
        f"/api/v1/voice-commands/sessions?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    assert sessions[0]["command_count"] == 3
    assert [command["intent"] for command in sessions[0]["commands"]] == [
        "custom_command",
        "injury_log",
        "score_event",
    ]
