def test_voice_coaching_profiles_sessions_and_metric_queries(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Voice Coaching Club",
            "slug": "voice-coaching-club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()

    profile_response = client.post(
        "/api/v1/voice-coaching/profiles",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "voice_style": "professional_coach",
            "feedback_frequency": "detailed",
            "language": "en",
            "terminology_level": "advanced",
            "preferred_device": "bone_conduction_headphones",
        },
    )
    assert profile_response.status_code == 201
    profile = profile_response.json()
    assert profile["person_name"] == "Owner Example"
    assert profile["feedback_frequency"] == "detailed"

    session_response = client.post(
        "/api/v1/voice-coaching/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "profile_id": profile["id"],
            "activity_type": "football sprint training",
            "stage": "main",
            "intensity": 78,
            "elapsed_seconds": 300,
            "distance_m": 820,
            "heart_rate_bpm": 168,
            "speed_mps": 7.4,
            "context_note": "Acceleration block before small-sided game.",
        },
    )
    assert session_response.status_code == 201
    session = session_response.json()
    assert session["model_policy"] == "afrolete-context-aware-voice-coach-v1"
    assert session["delivered_count"] >= 4
    assert session["suppressed_count"] == 0
    assert any(cue["category"] == "form_correction" for cue in session["cues"])
    assert any(cue["audio_layer"] == "secondary" for cue in session["cues"])
    assert "820 meters" in session["debrief"]

    high_intensity_response = client.post(
        "/api/v1/voice-coaching/sessions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "profile_id": profile["id"],
            "activity_type": "football sprint training",
            "stage": "main",
            "intensity": 97,
            "elapsed_seconds": 45,
            "distance_m": 120,
            "heart_rate_bpm": 193,
            "speed_mps": 8.6,
        },
    )
    assert high_intensity_response.status_code == 201
    high_intensity = high_intensity_response.json()
    assert high_intensity["safety_flags"]
    assert high_intensity["delivered_count"] >= 1
    assert high_intensity["suppressed_count"] >= 1
    assert any(cue["priority"] == "critical" for cue in high_intensity["cues"])
    assert any(cue["delivery_mode"] == "suppressed" for cue in high_intensity["cues"])

    query_response = client.post(
        "/api/v1/voice-coaching/metric-query",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "profile_id": profile["id"],
            "query": "How far have I run?",
        },
    )
    assert query_response.status_code == 200
    query = query_response.json()
    assert query["query_type"] == "distance"
    assert "120 meters" in query["answer"]
    assert query["recommended_actions"]

    sessions_response = client.get(
        f"/api/v1/voice-coaching/sessions?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert sessions_response.status_code == 200
    assert {session["id"] for session in sessions_response.json()} >= {session["id"], high_intensity["id"]}
