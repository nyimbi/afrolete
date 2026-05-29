def test_volunteer_management_covers_profiles_shifts_training_and_recognition(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Volunteer City FC", "organization_type": "club", "primary_sport": "football"},
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U15 Volunteers",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    event = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_type": "match",
            "title": "Community Derby",
            "starts_at": "2026-07-04T10:00:00Z",
            "ends_at": "2026-07-04T12:00:00Z",
            "venue_name": "Volunteer Park",
        },
    ).json()

    profile_response = client.post(
        "/api/v1/volunteers/profiles",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "email": "maria.volunteer@example.com",
            "display_name": "Maria Volunteer",
            "volunteer_type": "first_aid",
            "certification_level": "Certified first responder",
            "availability": ["saturday", "evenings"],
            "skills": ["first aid", "safeguarding", "spanish"],
            "background_check_status": "cleared",
            "background_check_expires_on": "2027-07-01",
            "training_status": "in_progress",
            "onboarding_status": "active",
            "reliability_score": 0.96,
            "emergency_contact": "+254711000001",
        },
    )
    assert profile_response.status_code == 201
    profile = profile_response.json()
    assert profile["person_name"] == "Maria Volunteer"
    assert profile["skills"] == ["first aid", "safeguarding", "spanish"]

    opportunity_response = client.post(
        "/api/v1/volunteers/opportunities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_id": event["id"],
            "title": "Matchday first aid station",
            "role_type": "first_aid",
            "description": "Cover the medical table and incident log.",
            "required_skills": ["first aid", "safeguarding"],
            "starts_at": "2026-07-04T09:00:00Z",
            "ends_at": "2026-07-04T13:00:00Z",
            "location": "North touchline",
            "slots_required": 1,
            "background_check_required": True,
            "training_required": True,
            "priority": "high",
        },
    )
    assert opportunity_response.status_code == 201
    opportunity = opportunity_response.json()
    assert opportunity["open_slots"] == 1

    training_response = client.post(
        "/api/v1/volunteers/training-records",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "volunteer_profile_id": profile["id"],
            "module_name": "Safeguarding for Matchday Volunteers",
            "role_type": "first_aid",
            "required": True,
            "status": "complete",
            "completed_at": "2026-06-25T08:00:00Z",
            "expires_on": "2027-06-25",
            "score": 94,
        },
    )
    assert training_response.status_code == 201
    assert training_response.json()["status"] == "complete"

    assignment_response = client.post(
        "/api/v1/volunteers/assignments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "volunteer_profile_id": profile["id"],
            "notes": "Bring trauma kit and incident tablet.",
        },
    )
    assert assignment_response.status_code == 201
    assignment = assignment_response.json()
    assert assignment["person_name"] == "Maria Volunteer"
    assert assignment["match_score"] >= 0.8

    full_response = client.post(
        "/api/v1/volunteers/assignments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "volunteer_profile_id": profile["id"],
        },
    )
    assert full_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/volunteers/assignments/{assignment['id']}",
        headers=identity_headers,
        json={
            "status": "confirmed",
            "checked_in_at": "2026-07-04T09:00:00Z",
            "checked_out_at": "2026-07-04T13:00:00Z",
            "notes": "Completed without incident.",
        },
    )
    assert update_response.status_code == 200
    completed = update_response.json()
    assert completed["status"] == "completed"
    assert completed["hours_logged"] == 4

    recognition_response = client.post(
        "/api/v1/volunteers/recognitions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "volunteer_profile_id": profile["id"],
            "recognition_type": "badge",
            "badge_code": "first-aid-certified",
            "title": "First Aid Certified",
            "points": 250,
            "awarded_on": "2026-07-05",
            "source_summary": "Covered matchday medical station.",
        },
    )
    assert recognition_response.status_code == 201
    assert recognition_response.json()["points"] == 250

    opportunities = client.get(
        f"/api/v1/volunteers/opportunities?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert opportunities[0]["assigned_count"] == 1
    assert opportunities[0]["open_slots"] == 0

    summary = client.get(
        f"/api/v1/volunteers/summary?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert summary["active_volunteers"] == 1
    assert summary["open_slots"] == 0
    assert summary["completed_hours"] == 4
    assert summary["training_compliance_percent"] == 100
    assert "first aid" in summary["top_skills"]


def test_public_volunteer_recruitment_signup_creates_application(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Public Volunteer Club",
            "slug": "public-volunteer-club",
            "organization_type": "club",
            "primary_sport": "athletics",
            "public_name": "Public Volunteer Track",
        },
    ).json()
    event = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "event_type": "community",
            "title": "Saturday Youth Meet",
            "starts_at": "2026-08-15T09:00:00Z",
            "ends_at": "2026-08-15T13:00:00Z",
            "venue_name": "City Track",
        },
    ).json()
    opportunity = client.post(
        "/api/v1/volunteers/opportunities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "event_id": event["id"],
            "title": "Finish-line marshal",
            "role_type": "marshal",
            "description": "Help athletes exit the finish area safely.",
            "required_skills": ["crowd control", "timing"],
            "starts_at": "2026-08-15T08:00:00Z",
            "ends_at": "2026-08-15T14:00:00Z",
            "location": "Finish chute",
            "slots_required": 2,
            "public_signup": True,
        },
    ).json()

    public_list_response = client.get("/api/v1/volunteers/public/public-volunteer-club/opportunities")

    assert public_list_response.status_code == 200
    public_opportunities = public_list_response.json()
    assert public_opportunities[0]["title"] == "Finish-line marshal"
    assert public_opportunities[0]["open_slots"] == 2

    signup_response = client.post(
        "/api/v1/volunteers/public/public-volunteer-club/signups",
        json={
            "opportunity_id": opportunity["id"],
            "display_name": "Nia Community",
            "email": "nia.community@example.com",
            "phone": "+254711222333",
            "availability": ["saturday"],
            "skills": ["timing", "crowd control", "first aid"],
            "emergency_contact": "+254733222111",
            "message": "I can cover the finish line and athlete flow.",
            "source_url": "https://public-volunteer-club.afrolete.test",
        },
    )

    assert signup_response.status_code == 201
    signup = signup_response.json()
    assert signup["status"] == "applied"
    assert signup["opportunity_title"] == "Finish-line marshal"
    assert signup["person_name"] == "Nia Community"
    assert signup["match_score"] >= 0.8

    duplicate_response = client.post(
        "/api/v1/volunteers/public/public-volunteer-club/signups",
        json={
            "opportunity_id": opportunity["id"],
            "display_name": "Nia Community",
            "email": "nia.community@example.com",
            "skills": ["timing"],
            "message": "Updated availability note.",
        },
    )

    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["assignment_id"] == signup["assignment_id"]
    assert duplicate_response.json()["message"] == "Updated availability note."

    profiles = client.get(
        f"/api/v1/volunteers/profiles?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert profiles[0]["person_email"] == "nia.community@example.com"
    assert profiles[0]["onboarding_status"] == "applied"
    assert "crowd control" in profiles[0]["skills"]

    assignments = client.get(
        f"/api/v1/volunteers/assignments?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert assignments[0]["status"] == "applied"

    manager_list = client.get(
        f"/api/v1/volunteers/opportunities?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert manager_list[0]["assigned_count"] == 0
    assert manager_list[0]["open_slots"] == 2
