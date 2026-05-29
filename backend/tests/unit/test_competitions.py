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


def add_competition_player(client, identity_headers, organization_id, team_id, name, email):
    member = client.post(
        f"/api/v1/organizations/{organization_id}/members",
        headers=identity_headers,
        json={
            "email": email,
            "display_name": name,
            "role": "athlete",
        },
    ).json()
    roster = client.post(
        f"/api/v1/teams/{team_id}/members",
        headers=identity_headers,
        json={
            "person_id": member["subject_id"],
            "role": "player",
            "status": "active",
        },
    ).json()
    return member, roster


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


def test_competition_knockout_advancement_ticketing_broadcast_and_schedule(
    client,
    identity_headers,
) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Tournament Verification Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    teams = [
        create_competition_team(client, identity_headers, organization["id"], name)
        for name in ["Alpha FC", "Bravo FC", "City FC", "Delta FC"]
    ]
    players = []
    for index, team in enumerate(teams, start=1):
        member, _ = add_competition_player(
            client,
            identity_headers,
            organization["id"],
            team["id"],
            f"Tournament Player {index}",
            f"tournament-player-{index}@example.com",
        )
        players.append(member)
    guardian_response = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": players[0]["subject_id"],
            "guardian_email": "tournament-parent@example.com",
            "guardian_display_name": "Tournament Parent",
            "relationship_kind": "parent",
            "can_sign_consent": True,
        },
    )
    assert guardian_response.status_code == 201

    competition_response = client.post(
        "/api/v1/competitions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Academy Cup",
            "sport": "football",
            "competition_type": "tournament",
            "format": "single_elimination",
            "season_label": "2026",
        },
    )
    assert competition_response.status_code == 201
    competition = competition_response.json()

    for seed, team in enumerate(teams, start=1):
        response = client.post(
            f"/api/v1/competitions/{competition['id']}/participants",
            headers=identity_headers,
            json={"team_id": team["id"], "seed": seed},
        )
        assert response.status_code == 201

    semifinal_one = client.post(
        f"/api/v1/competitions/{competition['id']}/fixtures",
        headers=identity_headers,
        json={
            "home_team_id": teams[0]["id"],
            "away_team_id": teams[1]["id"],
            "round_label": "Round 1",
            "stage_label": "Semifinal",
            "scheduled_at": "2026-06-05T10:00:00Z",
            "venue_name": "Main Pitch",
            "notes": "First semifinal.",
        },
    ).json()
    semifinal_two = client.post(
        f"/api/v1/competitions/{competition['id']}/fixtures",
        headers=identity_headers,
        json={
            "home_team_id": teams[2]["id"],
            "away_team_id": teams[3]["id"],
            "round_label": "Round 1",
            "stage_label": "Semifinal",
            "scheduled_at": "2026-06-05T10:30:00Z",
            "venue_name": "Main Pitch",
            "notes": "Second semifinal.",
        },
    ).json()
    placement = client.post(
        f"/api/v1/competitions/{competition['id']}/fixtures",
        headers=identity_headers,
        json={
            "home_team_id": teams[1]["id"],
            "away_team_id": teams[2]["id"],
            "round_label": "Placement",
            "stage_label": "ZZ Placement",
            "scheduled_at": "2026-06-05T10:45:00Z",
            "venue_name": "Main Pitch",
            "notes": "Third-place placement match.",
        },
    ).json()

    conflicts_response = client.get(f"/api/v1/competitions/{competition['id']}/conflicts")
    assert conflicts_response.status_code == 200
    conflict_keys = {item["conflict_key"] for item in conflicts_response.json()}
    assert "venue-overlap" in conflict_keys
    assert "missing-official" in conflict_keys

    for fixture_id, home_score, away_score in [
        (semifinal_one["id"], 2, 0),
        (semifinal_two["id"], 1, 3),
    ]:
        result_response = client.patch(
            f"/api/v1/competitions/fixtures/{fixture_id}/result",
            headers=identity_headers,
            json={
                "home_score": home_score,
                "away_score": away_score,
                "confirmed": True,
                "notes": "Confirmed semifinal result.",
            },
        )
        assert result_response.status_code == 200

    advance_response = client.post(
        f"/api/v1/competitions/{competition['id']}/advance",
        headers=identity_headers,
        json={
            "source_stage_label": "Semifinal",
            "source_round_label": "Round 1",
            "next_stage_label": "Final",
            "next_round_label": "Championship",
            "scheduled_at": "2026-06-05T11:00:00Z",
            "match_spacing_minutes": 120,
            "venue_name": "Main Pitch",
        },
    )
    assert advance_response.status_code == 201
    advancement = advance_response.json()
    assert advancement["winners"] == ["Alpha FC", "Delta FC"]
    assert advancement["created"] == 1
    assert advancement["skipped"] == 0
    final_fixture = advancement["fixtures"][0]
    assert final_fixture["home_team_name"] == "Alpha FC"
    assert final_fixture["away_team_name"] == "Delta FC"

    duplicate_advance_response = client.post(
        f"/api/v1/competitions/{competition['id']}/advance",
        headers=identity_headers,
        json={
            "source_stage_label": "Semifinal",
            "source_round_label": "Round 1",
            "next_stage_label": "Final",
            "next_round_label": "Championship",
            "scheduled_at": "2026-06-05T11:00:00Z",
            "match_spacing_minutes": 120,
            "venue_name": "Main Pitch",
        },
    )
    assert duplicate_advance_response.status_code == 201
    duplicate = duplicate_advance_response.json()
    assert duplicate["created"] == 0
    assert duplicate["skipped"] == 1
    assert duplicate["fixtures"] == []

    ticketing_response = client.post(
        f"/api/v1/competitions/{competition['id']}/ticketing",
        headers=identity_headers,
        json={
            "fixture_id": final_fixture["id"],
            "name": "Academy Cup Final Admission",
            "price": "12.50",
            "currency": "USD",
            "capacity": 500,
            "access_zone": "Main stand",
        },
    )
    assert ticketing_response.status_code == 201
    ticketing = ticketing_response.json()
    assert ticketing["event_id"]
    assert ticketing["ticket_product_id"]
    assert ticketing["fixture_id"] == final_fixture["id"]
    assert ticketing["price"] == "12.50"
    assert ticketing["capacity"] == 500

    ticketing_list_response = client.get(f"/api/v1/competitions/{competition['id']}/ticketing")
    assert ticketing_list_response.status_code == 200
    assert ticketing_list_response.json()[0]["ticket_product_id"] == ticketing["ticket_product_id"]

    optimize_response = client.post(
        f"/api/v1/competitions/{competition['id']}/schedule/optimize",
        headers=identity_headers,
        json={
            "starts_at": "2026-06-05T10:00:00Z",
            "match_spacing_minutes": 120,
            "team_rest_minutes": 240,
            "venue_name": "Main Pitch",
            "preserve_final_results": True,
        },
    )
    assert optimize_response.status_code == 200
    optimized = optimize_response.json()
    assert optimized["protected_finals"] == 2
    assert optimized["moved"] >= 1
    moved_ids = {fixture["id"] for fixture in optimized["fixtures"]}
    assert placement["id"] in moved_ids
    moved_placement = next(fixture for fixture in optimized["fixtures"] if fixture["id"] == placement["id"])
    assert moved_placement["scheduled_at"] >= "2026-06-05T14:30:00"
    assert "Schedule optimized" in moved_placement["notes"]

    bracket_response = client.get(f"/api/v1/competitions/{competition['id']}/bracket")
    assert bracket_response.status_code == 200
    bracket = bracket_response.json()
    assert any(round_item["stage_label"] == "Final" for round_item in bracket["rounds"])

    broadcast_response = client.post(
        f"/api/v1/competitions/{competition['id']}/broadcast",
        headers=identity_headers,
        json={
            "channel": "in_app",
            "subject": "Academy Cup finals update",
            "urgent": True,
            "include_guardians": True,
        },
    )
    assert broadcast_response.status_code == 201
    broadcast = broadcast_response.json()
    assert broadcast["subject"] == "Academy Cup finals update"
    assert broadcast["recipient_count"] == 5
    assert broadcast["attempted"] == 5
    assert broadcast["delivered"] == 5
    assert broadcast["failed"] == 0
