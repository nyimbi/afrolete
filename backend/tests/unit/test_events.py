from datetime import UTC, date, datetime

import pytest

from app.models.identity import Person
from app.services.authz.service import authorization_service


@pytest.fixture
async def adult_person(db_session) -> Person:
    person = Person(
        display_name="Adult Athlete",
        primary_email="adult-athlete@example.com",
        date_of_birth=date(2000, 1, 1),
    )
    db_session.add(person)
    await db_session.commit()
    await db_session.refresh(person)
    return person


@pytest.fixture
async def minor_person(db_session) -> Person:
    person = Person(
        display_name="Minor Event Athlete",
        primary_email="minor-event-athlete@example.com",
        date_of_birth=date(2014, 1, 1),
    )
    db_session.add(person)
    await db_session.commit()
    await db_session.refresh(person)
    return person


def create_org_team_event(client, identity_headers, sport: str = "football"):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": f"{sport.title()} Event Club", "organization_type": "club"},
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U17 Match Squad",
            "sport": sport,
            "sport_format": "team",
        },
    ).json()
    event_response = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_type": "match",
            "title": "Saturday Fixture",
            "starts_at": datetime(2026, 6, 6, 10, 0, tzinfo=UTC).isoformat(),
            "ends_at": datetime(2026, 6, 6, 12, 0, tzinfo=UTC).isoformat(),
            "venue_name": "Main Field",
        },
    )

    assert event_response.status_code == 201
    event = event_response.json()
    assert any(
        relationship.resource_type == "event"
        and relationship.resource_id == event["id"]
        and relationship.relation == "parent_org"
        and relationship.subject_type == "organization"
        and relationship.subject_id == organization["id"]
        for relationship in authorization_service.relationships
    )
    assert any(
        relationship.resource_type == "event"
        and relationship.resource_id == event["id"]
        and relationship.relation == "team"
        and relationship.subject_type == "team"
        and relationship.subject_id == team["id"]
        for relationship in authorization_service.relationships
    )
    return organization, team, event


def test_team_event_seed_and_attendance_check_in(
    client,
    identity_headers,
    adult_person,
) -> None:
    _, team, event = create_org_team_event(client, identity_headers)
    roster_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={"person_id": str(adult_person.id), "role": "player", "status": "active"},
    )
    assert roster_response.status_code == 201

    seed_response = client.post(
        f"/api/v1/events/{event['id']}/attendance/from-roster",
        headers=identity_headers,
    )

    assert seed_response.status_code == 200
    assert seed_response.json() == {"event_id": event["id"], "created": 1, "existing": 0}

    attendance_list = client.get(f"/api/v1/events/{event['id']}/attendance").json()
    assert len(attendance_list) == 1
    assert attendance_list[0]["status"] == "invited"

    check_in_response = client.post(
        f"/api/v1/events/{event['id']}/attendance",
        headers=identity_headers,
        json={
            "person_id": str(adult_person.id),
            "status": "present",
            "note": "Checked in at gate.",
        },
    )

    assert check_in_response.status_code == 201
    check_in = check_in_response.json()
    assert check_in["status"] == "present"
    assert check_in["clearance_status"] == "cleared"


def test_minor_attendance_requires_guardian_consent_before_participation(
    client,
    identity_headers,
    minor_person,
) -> None:
    organization, team, event = create_org_team_event(client, identity_headers, sport="basketball")
    client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={"person_id": str(minor_person.id), "role": "player", "status": "active"},
    )

    blocked_response = client.post(
        f"/api/v1/events/{event['id']}/attendance",
        headers=identity_headers,
        json={"person_id": str(minor_person.id), "status": "present"},
    )

    assert blocked_response.status_code == 409
    assert blocked_response.json()["detail"]["clearance_status"] == "no_guardian"

    guardian = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": str(minor_person.id),
            "guardian_email": "event-parent@example.com",
            "guardian_display_name": "Event Parent",
            "relationship_kind": "parent",
            "can_sign_consent": True,
        },
    ).json()
    consent = client.post(
        "/api/v1/safeguarding/consents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": str(minor_person.id),
            "guardian_person_id": guardian["guardian_person_id"],
            "scope_type": "event",
            "scope_id": event["id"],
            "status": "granted",
            "consent_text": "I consent to participation in this match.",
        },
    ).json()

    check_in_response = client.post(
        f"/api/v1/events/{event['id']}/attendance",
        headers=identity_headers,
        json={"person_id": str(minor_person.id), "status": "present"},
    )

    assert check_in_response.status_code == 201
    check_in = check_in_response.json()
    assert check_in["status"] == "present"
    assert check_in["guardian_consent_id"] == consent["id"]
    assert check_in["clearance_status"] == "cleared"
