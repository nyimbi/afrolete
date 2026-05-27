from app.services.authz.service import authorization_service


def test_club_can_create_team_and_add_person_member(client, identity_headers, athlete_person) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "River Plate Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()

    team_response = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U14 Boys",
            "sport": "football",
            "sport_format": "team",
            "age_group": "U14",
            "gender_category": "boys",
            "season_label": "2026",
        },
    )

    assert team_response.status_code == 201
    team = team_response.json()
    assert team["organization_id"] == organization["id"]

    list_response = client.get(f"/api/v1/teams/by-organization/{organization['id']}")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [team["id"]]

    roster_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": str(athlete_person.id),
            "role": "captain",
            "status": "starter",
            "primary_position": "midfielder",
            "jersey_number": "8",
            "is_captain": True,
        },
    )

    assert roster_response.status_code == 201
    roster_entry = roster_response.json()
    assert roster_entry["team_id"] == team["id"]
    assert roster_entry["role"] == "captain"
    assert roster_entry["status"] == "starter"
    assert roster_entry["primary_position"] == "midfielder"
    assert roster_entry["is_captain"] is True
    assert any(
        relationship.resource_type == "team"
        and relationship.resource_id == team["id"]
        and relationship.relation == "captain"
        and relationship.subject_type == "person"
        and relationship.subject_id == str(athlete_person.id)
        for relationship in authorization_service.relationships
    )


def test_individual_sport_training_group_and_team_committee(
    client,
    identity_headers,
    athlete_person,
) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Blue Track School",
            "organization_type": "school",
            "primary_sport": "athletics",
        },
    ).json()
    group = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Sprint Squad",
            "sport": "athletics",
            "sport_format": "individual",
            "age_group": "senior",
        },
    ).json()
    assert group["sport_format"] == "individual"

    roster_response = client.post(
        f"/api/v1/teams/{group['id']}/members",
        headers=identity_headers,
        json={
            "person_id": str(athlete_person.id),
            "role": "individual_athlete",
            "status": "active",
        },
    )
    assert roster_response.status_code == 201
    assert roster_response.json()["role"] == "individual_athlete"
    assert any(
        relationship.resource_type == "team"
        and relationship.resource_id == group["id"]
        and relationship.relation == "individual_athlete"
        and relationship.subject_type == "person"
        and relationship.subject_id == str(athlete_person.id)
        for relationship in authorization_service.relationships
    )

    committee_response = client.post(
        f"/api/v1/teams/{group['id']}/committees",
        headers=identity_headers,
        json={"name": "Selection Committee", "mandate": "Pick relay teams and travel squads."},
    )
    assert committee_response.status_code == 201

    member_response = client.post(
        f"/api/v1/teams/committees/{committee_response.json()['id']}/members",
        headers=identity_headers,
        json={"person_id": str(athlete_person.id), "role": "member"},
    )
    assert member_response.status_code == 201
    assert member_response.json()["person_id"] == str(athlete_person.id)
