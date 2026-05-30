def test_athlete_development_hub_builds_wellness_academic_scholarship_dashboard(
    client,
    identity_headers,
) -> None:
    organization, _, roster = create_rostered_athlete(client, identity_headers)
    athlete_profile_id = roster["athlete_profile_id"]

    wellness = client.post(
        f"/api/v1/development/athletes/{athlete_profile_id}/wellness-check-ins",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "mood_score": 4,
            "stress_score": 8,
            "sleep_hours": 5.5,
            "energy_score": 4,
            "soreness_score": 7,
            "resilience_score": 5,
            "support_requested": True,
            "notes": "Exam week and tournament travel are creating pressure.",
        },
    )
    assert wellness.status_code == 201
    assert wellness.json()["risk_band"] in {"high", "critical"}

    academic = client.post(
        f"/api/v1/development/athletes/{athlete_profile_id}/academic-records",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "school_name": "AfroLete Academy",
            "term_label": "2026 Term 2",
            "grade_level": "Form 3",
            "gpa": 3.3,
            "attendance_rate": 93,
            "study_hours_weekly": 8,
            "missing_assignment_count": 1,
            "next_review_on": "2026-07-01",
            "notes": "Eligible with math support.",
        },
    )
    assert academic.status_code == 201
    assert academic.json()["eligibility_status"] in {"eligible", "eligible_watch"}

    skill = client.post(
        f"/api/v1/development/athletes/{athlete_profile_id}/life-skill-assignments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "module_code": "media-training-101",
            "title": "Media Training 101",
            "category": "media_training",
            "level": "intermediate",
            "due_on": "2026-07-15",
            "evidence_notes": "Prepare for local interview practice.",
        },
    )
    assert skill.status_code == 201
    progress = client.patch(
        f"/api/v1/development/life-skill-assignments/{skill.json()['id']}",
        headers=identity_headers,
        json={
            "status": "in_progress",
            "progress_percent": 60,
            "evidence_notes": "Completed mock-interview checklist.",
        },
    )
    assert progress.status_code == 200
    assert progress.json()["progress_percent"] == 60

    scholarship = client.post(
        f"/api/v1/development/athletes/{athlete_profile_id}/scholarship-applications",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "program_name": "Future Leaders Athletic Scholarship",
            "scholarship_type": "need_based_athletic",
            "donor_or_fund": "Alumni Opportunity Fund",
            "amount_requested": 1500,
            "currency": "USD",
            "deadline_on": "2026-08-01",
            "submitted_on": "2026-06-01",
            "notes": "Family needs partial fee support.",
        },
    )
    assert scholarship.status_code == 201
    assert scholarship.json()["eligibility_score"] >= 60
    assert "scholarship" in scholarship.json()["committee_recommendation"].lower()

    review = client.patch(
        f"/api/v1/development/scholarship-applications/{scholarship.json()['id']}",
        headers=identity_headers,
        json={
            "status": "approved",
            "amount_awarded": 1000,
            "decided_on": "2026-06-15",
            "notes": "Approved with academic monitoring.",
        },
    )
    assert review.status_code == 200
    assert review.json()["status"] == "approved"
    assert review.json()["amount_awarded"] == 1000

    dashboard = client.get(
        f"/api/v1/development/athletes/{athlete_profile_id}/dashboard?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert data["athlete_name"] == "Development Athlete"
    assert data["latest_wellness"]["risk_band"] in {"high", "critical"}
    assert data["latest_academic"]["term_label"] == "2026 Term 2"
    assert data["life_skill_progress_percent"] == 60
    assert data["scholarship_readiness_score"] >= 60
    assert data["scholarship_applications"][0]["status"] == "approved"
    assert any(action["key"] in {"wellness-support", "scholarship-review"} for action in data["actions"])


def create_rostered_athlete(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Development Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U17 Development",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "development-athlete@example.com",
            "display_name": "Development Athlete",
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
            "primary_position": "Midfielder",
        },
    ).json()
    return organization, team, roster
