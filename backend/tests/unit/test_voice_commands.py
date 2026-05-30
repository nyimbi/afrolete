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

    session_response = client.post(
        "/api/v1/voice-commands/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
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
