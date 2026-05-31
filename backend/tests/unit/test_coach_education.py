def test_coach_education_certification_dashboard(client, identity_headers) -> None:
    catalog_response = client.get("/api/v1/coach-education/catalog")
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    foundation = next(program for program in catalog["programs"] if program["key"] == "foundation_coach")
    assert foundation["certification_badge"] == "Foundation Coach Badge"
    assert foundation["modules"][0]["key"] == "platform_basics"

    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Coach Academy Club",
            "slug": "coach-academy-club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()

    enrollment_response = client.post(
        "/api/v1/coach-education/enrollments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "program_key": "foundation_coach",
            "role": "head_coach",
            "skill_level": "intermediate",
            "learning_style": "hands_on",
            "cpd_hours_required": 20,
        },
    )
    assert enrollment_response.status_code == 201
    enrollment = enrollment_response.json()
    assert enrollment["program_title"] == "Foundation Coach"
    assert enrollment["progress_percent"] == 0
    assert enrollment["next_module"]["key"] == "platform_basics"

    for module in foundation["modules"]:
        activity_response = client.post(
            f"/api/v1/coach-education/enrollments/{enrollment['id']}/activities",
            headers=identity_headers,
            json={
                "module_key": module["key"],
                "evidence_ref": f"coach-lab://{module['key']}",
                "score_percent": 92,
                "cpd_hours": 4,
                "feedback": f"Reviewed {module['title']} evidence.",
            },
        )
        assert activity_response.status_code == 201
        enrollment = activity_response.json()["enrollment"]

    assert enrollment["status"] == "certified"
    assert enrollment["progress_percent"] == 100
    assert "Foundation Coach Badge" in enrollment["badges"]
    assert enrollment["accreditation_provider"] == "AfroLete Coach Academy"
    assert enrollment["certificate_number"].startswith("CE-FOUNDATION-COACH-")
    assert enrollment["certification_issued_on"] is not None
    assert enrollment["certification_expires_on"] is not None
    assert enrollment["renewal_due_on"] is not None
    assert enrollment["certification_state"] == "current"
    assert enrollment["cpd_hours_completed"] == 12
    assert enrollment["cpd_gap_hours"] == 8

    cpd_response = client.post(
        f"/api/v1/coach-education/enrollments/{enrollment['id']}/certification-review",
        headers=identity_headers,
        json={
            "action": "record_cpd",
            "cpd_hours_completed": 20,
            "portfolio_evidence_ref": "coach-portfolio://foundation-renewal",
            "review_notes": "CPD evidence accepted for renewal readiness.",
        },
    )
    assert cpd_response.status_code == 200
    cpd_review = cpd_response.json()
    assert cpd_review["cpd_gap_hours"] == 0
    assert cpd_review["enrollment"]["portfolio_evidence_ref"] == "coach-portfolio://foundation-renewal"

    renewal_response = client.post(
        f"/api/v1/coach-education/enrollments/{enrollment['id']}/certification-review",
        headers=identity_headers,
        json={
            "action": "renew",
            "cpd_hours_completed": 20,
            "certification_expires_on": "2028-05-31",
            "review_notes": "Renewed after CPD evidence review.",
        },
    )
    assert renewal_response.status_code == 200
    renewal = renewal_response.json()
    assert renewal["renewed"] is True
    assert renewal["enrollment"]["certification_expires_on"] == "2028-05-31"
    assert renewal["enrollment"]["renewal_due_on"] == "2028-05-01"
    assert renewal["enrollment"]["cpd_hours_completed"] == 0

    dashboard_response = client.get(
        f"/api/v1/coach-education/dashboard?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["certified_count"] == 1
    assert dashboard["renewal_due_count"] == 0
    assert dashboard["expired_count"] == 0
    assert dashboard["cpd_gap_count"] == 1
    assert dashboard["total_xp"] == sum(module["xp"] for module in foundation["modules"])
    assert dashboard["leaderboard"][0]["person_name"] == "Owner Example"
    assert dashboard["leaderboard"][0]["badges"] == ["Foundation Coach Badge"]
    assert any(challenge["key"] == "analyze_training_session" for challenge in dashboard["daily_challenges"])
