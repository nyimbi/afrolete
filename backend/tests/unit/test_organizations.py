from app.services.authz.service import authorization_service


def test_create_and_list_organization(client, identity_headers) -> None:
    create_response = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Nairobi Rising FC",
            "organization_type": "club",
            "country_code": "KE",
            "primary_sport": "football",
            "mission": "Build an athlete development pathway.",
            "public_name": "Nairobi Rising",
            "contact_email": "hello@rising.example",
            "contact_phone": "+254711000000",
            "website_url": "https://rising.example",
            "subdomain": "nairobi-rising",
            "logo_url": "https://cdn.example/logo.png",
            "brand_primary_color": "#0f766e",
            "brand_secondary_color": "#f59e0b",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["slug"] == "nairobi-rising-fc"
    assert created["public_name"] == "Nairobi Rising"
    assert created["subdomain"] == "nairobi-rising"
    assert created["brand_primary_color"] == "#0f766e"
    assert created["my_roles"] == ["owner"]

    list_response = client.get("/api/v1/organizations", headers=identity_headers)

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [created["id"]]
    assert any(
        relationship.resource_type == "organization"
        and relationship.resource_id == created["id"]
        and relationship.relation == "owner"
        and relationship.subject_type == "user"
        for relationship in authorization_service.relationships
    )


def test_add_member_requires_manage_permission(client, identity_headers) -> None:
    create_response = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Kisumu Hoops Academy",
            "organization_type": "academy",
            "country_code": "KE",
            "primary_sport": "basketball",
        },
    )
    organization_id = create_response.json()["id"]

    add_response = client.post(
        f"/api/v1/organizations/{organization_id}/members",
        headers=identity_headers,
        json={
            "email": "coach@example.com",
            "display_name": "Coach Example",
            "role": "coach",
            "title": "Head Coach",
        },
    )

    assert add_response.status_code == 201
    member = add_response.json()
    assert member["role"] == "coach"
    assert member["organization_id"] == organization_id
    assert member["subject_type"] == "person"


def test_member_cannot_manage_unowned_organization(client, identity_headers) -> None:
    create_response = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Mombasa Athletics",
            "organization_type": "club",
        },
    )
    organization_id = create_response.json()["id"]

    other_headers = {
        "X-Afrolete-Sub": "kc-outsider",
        "X-Afrolete-Email": "outsider@example.com",
        "X-Afrolete-Name": "Outsider",
    }
    add_response = client.post(
        f"/api/v1/organizations/{organization_id}/members",
        headers=other_headers,
        json={
            "email": "coach@example.com",
            "display_name": "Coach Example",
            "role": "coach",
        },
    )

    assert add_response.status_code == 403


def test_association_can_have_school_member(client, identity_headers) -> None:
    association = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Kenya Youth Sports Association",
            "organization_type": "association",
            "country_code": "KE",
        },
    ).json()
    school = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Lakeview School",
            "organization_type": "school",
            "country_code": "KE",
        },
    ).json()

    add_response = client.post(
        f"/api/v1/organizations/{association['id']}/members",
        headers=identity_headers,
        json={
            "subject_type": "organization",
            "subject_id": school["id"],
            "role": "viewer",
            "title": "Member school",
        },
    )

    assert add_response.status_code == 201
    member = add_response.json()
    assert member["subject_type"] == "organization"
    assert member["subject_id"] == school["id"]
    assert any(
        relationship.resource_type == "organization"
        and relationship.resource_id == association["id"]
        and relationship.relation == "member_org"
        and relationship.subject_type == "organization"
        and relationship.subject_id == school["id"]
        for relationship in authorization_service.relationships
    )


def test_association_can_have_team_member(client, identity_headers) -> None:
    association = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Urban Basketball Association",
            "organization_type": "association",
            "association_level": "regional",
        },
    ).json()
    club = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Metro Hoops Club", "organization_type": "club"},
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": club["id"],
            "name": "U16 Girls",
            "sport": "basketball",
            "sport_format": "team",
        },
    ).json()

    add_response = client.post(
        f"/api/v1/organizations/{association['id']}/members",
        headers=identity_headers,
        json={
            "subject_type": "team",
            "subject_id": team["id"],
            "role": "viewer",
            "title": "Registered team",
        },
    )

    assert add_response.status_code == 201
    member = add_response.json()
    assert member["subject_type"] == "team"
    assert member["subject_id"] == team["id"]
    assert any(
        relationship.resource_type == "organization"
        and relationship.resource_id == association["id"]
        and relationship.relation == "member_team"
        and relationship.subject_type == "team"
        and relationship.subject_id == team["id"]
        for relationship in authorization_service.relationships
    )


def test_club_can_be_member_of_multiple_associations(client, identity_headers) -> None:
    association_one = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Regional Football Association", "organization_type": "association"},
    ).json()
    association_two = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Youth Development Network", "organization_type": "association"},
    ).json()
    club = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Green City Club", "organization_type": "club"},
    ).json()

    for association in [association_one, association_two]:
        add_response = client.post(
            f"/api/v1/organizations/{association['id']}/members",
            headers=identity_headers,
            json={
                "subject_type": "organization",
                "subject_id": club["id"],
                "role": "viewer",
                "title": "Member club",
            },
        )
        assert add_response.status_code == 201
        assert add_response.json()["subject_id"] == club["id"]


def test_association_levels_and_committees_support_cross_level_membership(
    client,
    identity_headers,
    athlete_person,
) -> None:
    national = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "National Athletics Association",
            "organization_type": "association",
            "association_level": "national",
        },
    ).json()
    local = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Nakuru Local Athletics",
            "organization_type": "association",
            "association_level": "local",
        },
    ).json()

    national_committee = client.post(
        f"/api/v1/organizations/{national['id']}/committees",
        headers=identity_headers,
        json={
            "name": "Technical Committee",
            "level": "national",
            "mandate": "National competition standards.",
        },
    )
    local_committee = client.post(
        f"/api/v1/organizations/{local['id']}/committees",
        headers=identity_headers,
        json={
            "name": "Local Development Committee",
            "level": "local",
        },
    )

    assert national_committee.status_code == 201
    assert national_committee.json()["level"] == "national"
    assert local_committee.status_code == 201
    assert local_committee.json()["level"] == "local"

    for committee, role in [
        (national_committee.json(), "advisor"),
        (local_committee.json(), "member"),
    ]:
        add_response = client.post(
            f"/api/v1/organizations/committees/{committee['id']}/members",
            headers=identity_headers,
            json={
                "person_id": str(athlete_person.id),
                "role": role,
            },
        )
        assert add_response.status_code == 201
        assert add_response.json()["person_id"] == str(athlete_person.id)
