def test_athlete_nutrition_hub_covers_profile_plans_logs_education_and_dashboard(
    client,
    identity_headers,
) -> None:
    organization, _, roster = create_rostered_athlete(client, identity_headers)
    athlete_profile_id = roster["athlete_profile_id"]

    profile = client.post(
        f"/api/v1/nutrition/athletes/{athlete_profile_id}/profile",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "dietary_pattern": "balanced_high_carbohydrate",
            "allergies": "Peanuts; shellfish",
            "medical_notes": "Exercise-induced reflux when meals are too close to kickoff.",
            "hydration_target_liters": 3.0,
            "daily_calorie_target": 2800,
            "protein_target_grams": 120,
            "carbohydrate_target_grams": 390,
            "fat_target_grams": 80,
            "supplement_policy": "No supplements without guardian and medical officer approval.",
            "travel_food_risk": "high",
            "consent_to_share_with_caterers": True,
        },
    )
    assert profile.status_code == 201
    assert profile.json()["allergies"] == "Peanuts; shellfish"
    assert profile.json()["hydration_target_liters"] == 3.0

    plan = client.post(
        f"/api/v1/nutrition/athletes/{athlete_profile_id}/meal-plans",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "title": "Tournament Travel Fueling Plan",
            "plan_type": "travel_matchday",
            "period_start": "2026-07-01",
            "period_end": "2026-07-05",
            "daily_calorie_target": 2800,
            "hydration_target_liters": 3.0,
            "menu_summary": "Breakfast oats, banana, eggs; lunch rice/chicken; pre-match fruit; recovery milk.",
            "shopping_list": "Oats, bananas, rice, chicken, oral rehydration sachets.",
            "caterer_notes": "Peanut-free prep area and sealed recovery snacks.",
            "risk_flags": "High travel-food risk due allergy and tournament heat.",
            "ai_generated": True,
        },
    )
    assert plan.status_code == 201
    assert plan.json()["plan_type"] == "travel_matchday"

    log = client.post(
        f"/api/v1/nutrition/athletes/{athlete_profile_id}/meal-logs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "meal_plan_id": plan.json()["id"],
            "logged_at": "2026-07-02T13:00:00Z",
            "meal_type": "pre_match_lunch",
            "calories": 2550,
            "protein_grams": 105,
            "carbohydrate_grams": 350,
            "fat_grams": 65,
            "hydration_liters": 2.6,
            "perceived_energy_score": 8,
            "gut_comfort_score": 8,
            "compliance_status": "on_plan",
            "notes": "Tolerated travel meal well.",
        },
    )
    assert log.status_code == 201
    assert log.json()["compliance_status"] == "on_plan"

    education = client.post(
        f"/api/v1/nutrition/athletes/{athlete_profile_id}/education-assignments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "module_code": "travel-fueling-101",
            "title": "Travel Fueling 101",
            "category": "travel_nutrition",
            "due_on": "2026-07-04",
            "evidence_notes": "Athlete and guardian to review allergy-safe travel snacks.",
        },
    )
    assert education.status_code == 201
    progress = client.patch(
        f"/api/v1/nutrition/education-assignments/{education.json()['id']}",
        headers=identity_headers,
        json={
            "status": "in_progress",
            "progress_percent": 75,
            "evidence_notes": "Completed allergy label-reading module.",
        },
    )
    assert progress.status_code == 200
    assert progress.json()["progress_percent"] == 75

    dashboard = client.get(
        f"/api/v1/nutrition/athletes/{athlete_profile_id}/dashboard?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert data["athlete_name"] == "Nutrition Athlete"
    assert data["profile"]["dietary_pattern"] == "balanced_high_carbohydrate"
    assert data["active_plan"]["title"] == "Tournament Travel Fueling Plan"
    assert data["recent_logs"][0]["meal_type"] == "pre_match_lunch"
    assert data["hydration_adherence_percent"] >= 80
    assert data["fueling_adherence_percent"] >= 80
    assert data["education_progress_percent"] == 75
    assert data["nutrition_score"] >= 60
    assert any(action["key"] in {"nutrition-review", "education-progress"} for action in data["actions"])


def create_rostered_athlete(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Nutrition Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U17 Nutrition",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "nutrition-athlete@example.com",
            "display_name": "Nutrition Athlete",
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
    return organization, team, roster
