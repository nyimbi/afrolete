def create_competition_team(client, identity_headers, organization_id, name):
    return client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization_id,
            "name": name,
            "sport": "football",
            "sport_format": "team",
        },
    ).json()


def create_competition_context(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Competition Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    home_team = create_competition_team(client, identity_headers, organization["id"], "Riverside")
    away_team = create_competition_team(client, identity_headers, organization["id"], "City Stars")
    official = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "referee@example.com",
            "display_name": "Referee Example",
            "role": "staff",
            "title": "Certified Referee",
        },
    ).json()
    return organization, home_team, away_team, official


def test_competition_fixture_result_standings_official_and_events(
    client,
    identity_headers,
) -> None:
    organization, home_team, away_team, official = create_competition_context(
        client,
        identity_headers,
    )

    competition_response = client.post(
        "/api/v1/competitions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U17 City League",
            "sport": "football",
            "competition_type": "league",
            "format": "round_robin",
            "season_label": "2026",
            "starts_on": "2026-06-01",
            "ends_on": "2026-08-31",
            "tiebreakers": "Points, goal difference, goals for",
            "rules_summary": "Standard league scoring.",
        },
    )

    assert competition_response.status_code == 201
    competition = competition_response.json()
    assert competition["status"] == "draft"

    for seed, team in enumerate([home_team, away_team], start=1):
        participant_response = client.post(
            f"/api/v1/competitions/{competition['id']}/participants",
            headers=identity_headers,
            json={"team_id": team["id"], "seed": seed, "group_label": "A"},
        )
        assert participant_response.status_code == 201

    fixture_response = client.post(
        f"/api/v1/competitions/{competition['id']}/fixtures",
        headers=identity_headers,
        json={
            "home_team_id": home_team["id"],
            "away_team_id": away_team["id"],
            "round_label": "Round 1",
            "stage_label": "League",
            "scheduled_at": "2026-06-05T16:00:00Z",
            "venue_name": "City Stadium",
            "notes": "Opening fixture.",
        },
    )

    assert fixture_response.status_code == 201
    fixture = fixture_response.json()
    assert fixture["home_team_name"] == "Riverside"
    assert fixture["away_team_name"] == "City Stars"

    official_response = client.post(
        f"/api/v1/competitions/fixtures/{fixture['id']}/officials",
        headers=identity_headers,
        json={
            "person_id": official["subject_id"],
            "role": "referee",
            "status": "confirmed",
            "certification_level": "Regional",
        },
    )

    assert official_response.status_code == 201
    assert official_response.json()["status"] == "confirmed"

    match_event_response = client.post(
        f"/api/v1/competitions/fixtures/{fixture['id']}/events",
        headers=identity_headers,
        json={
            "team_id": home_team["id"],
            "minute": 31,
            "event_type": "goal",
            "description": "Opening goal from a set piece.",
        },
    )

    assert match_event_response.status_code == 201
    assert match_event_response.json()["event_type"] == "goal"

    result_response = client.patch(
        f"/api/v1/competitions/fixtures/{fixture['id']}/result",
        headers=identity_headers,
        json={
            "home_score": 2,
            "away_score": 1,
            "confirmed": True,
            "notes": "Result confirmed by match official.",
        },
    )

    assert result_response.status_code == 200
    result = result_response.json()
    assert result["status"] == "final"
    assert result["home_score"] == 2
    assert result["away_score"] == 1
    assert result["result_confirmed_at"] is not None

    standings = client.get(f"/api/v1/competitions/{competition['id']}/standings").json()
    assert standings[0]["team_id"] == home_team["id"]
    assert standings[0]["played"] == 1
    assert standings[0]["wins"] == 1
    assert standings[0]["points"] == 3
    assert standings[1]["losses"] == 1


def test_competition_fixture_rejects_cross_organization_team(client, identity_headers) -> None:
    organization, home_team, _, _ = create_competition_context(client, identity_headers)
    other_organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Other Competition Club", "organization_type": "club"},
    ).json()
    other_team = create_competition_team(
        client,
        identity_headers,
        other_organization["id"],
        "External Team",
    )
    competition = client.post(
        "/api/v1/competitions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Cross Org League",
            "sport": "football",
            "competition_type": "league",
            "format": "round_robin",
        },
    ).json()
    client.post(
        f"/api/v1/competitions/{competition['id']}/participants",
        headers=identity_headers,
        json={"team_id": home_team["id"]},
    )

    response = client.post(
        f"/api/v1/competitions/{competition['id']}/fixtures",
        headers=identity_headers,
        json={
            "home_team_id": home_team["id"],
            "away_team_id": other_team["id"],
            "scheduled_at": "2026-06-05T16:00:00Z",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"
