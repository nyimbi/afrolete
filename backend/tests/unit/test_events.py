from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.models.enums import MedicalClearanceStatus, TravelRiskLevel
from app.models.identity import Person
from app.schemas.event import EventTravelManifestParticipantRead, EventTravelManifestRead
from app.services.authz.service import authorization_service
from app.services.events import travel_manifest_pdf, travel_manifest_text


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


def test_travel_manifest_pdf_is_branded_field_document() -> None:
    manifest = EventTravelManifestRead(
        event_id=uuid4(),
        travel_plan_id=uuid4(),
        organization_id=uuid4(),
        organization_name="Nairobi Rising FC",
        organization_contact_email="ops@nairobi-rising.example",
        organization_contact_phone="+254700000001",
        organization_logo_url="https://static.example/logo.png",
        brand_primary_color="#0E5A6F",
        brand_secondary_color="#20B486",
        event_title="Regional Final",
        event_starts_at=datetime(2026, 6, 6, 10, 0, tzinfo=UTC),
        venue_name="City Stadium",
        destination="City Stadium",
        travel_mode="Club minibus",
        departure_at=datetime(2026, 6, 6, 7, 30, tzinfo=UTC),
        return_at=datetime(2026, 6, 6, 14, 0, tzinfo=UTC),
        route_summary="Clubhouse to City Stadium via Mombasa Road with backup stop at South C.",
        vehicle_details="KDA 123A, 29-seat minibus, inspection current.",
        driver_details="Driver: Amina Yusuf, PSV current.",
        consent_required=True,
        risk_level=TravelRiskLevel.MEDIUM,
        risk_assessment="Driver certification, vehicle inspection, consent, and medical access reviewed.",
        participant_count=1,
        emergency_contacts="Coach Maria +254700000010; Medic Amina +254700000011",
        medical_access_plan="Nearest hospital: City Medical Center.",
        participants=[
            EventTravelManifestParticipantRead(
                person_id=uuid4(),
                display_name="Amani Otieno",
                guardian_names=["Parent Otieno"],
                guardian_contacts=["parent@example.com", "+254700000020"],
                medical_clearance_status=MedicalClearanceStatus.CLEARED,
                medical_clearance_reason="Cleared for full participation.",
            )
        ],
    )

    text_manifest = travel_manifest_text(manifest)
    pdf = travel_manifest_pdf(manifest)

    assert "Nairobi Rising FC travel manifest" in text_manifest
    assert "Risk: medium" in text_manifest
    assert pdf.startswith(b"%PDF-1.4")
    assert b"Nairobi Rising FC" in pdf
    assert b"OFFLINE TRAVEL MANIFEST" in pdf
    assert b"Regional Final" in pdf
    assert b"DEPARTURE SAFETY CHECKLIST" in pdf
    assert b"Amani Otieno" in pdf
    assert b"0.0549 0.3529 0.4353 rg 0 720 612 72 re f" in pdf


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


def test_event_attendance_policy_can_warn_instead_of_blocking_minor_clearance(
    client,
    identity_headers,
    minor_person,
) -> None:
    _, team, event = create_org_team_event(client, identity_headers, sport="netball")
    client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={"person_id": str(minor_person.id), "role": "player", "status": "active"},
    )

    policy_response = client.put(
        f"/api/v1/events/{event['id']}/attendance-policy",
        headers=identity_headers,
        json={
            "policy_code": "tournament-arrival-desk",
            "title": "Tournament arrival desk",
            "participation_statuses": ["present"],
            "no_guardian_action": "warn",
            "minor_consent_action": "warn",
            "denied_consent_action": "block",
            "expired_consent_action": "warn",
            "restricted_medical_action": "warn",
            "notes": "Allow front-desk arrival while safeguarding resolves consent.",
        },
    )
    assert policy_response.status_code == 200
    policy = policy_response.json()
    assert policy["policy_code"] == "tournament-arrival-desk"
    assert policy["no_guardian_action"] == "warn"

    check_in_response = client.post(
        f"/api/v1/events/{event['id']}/attendance",
        headers=identity_headers,
        json={"person_id": str(minor_person.id), "status": "present"},
    )
    assert check_in_response.status_code == 201
    check_in = check_in_response.json()
    assert check_in["status"] == "present"
    assert check_in["clearance_status"] == "no_guardian"
    assert check_in["attendance_policy_code"] == "tournament-arrival-desk"
    assert check_in["attendance_policy_decision"] == "warn"
    assert "No guardian with consent authority" in check_in["attendance_policy_warnings"][0]

    listed = client.get(f"/api/v1/events/{event['id']}/attendance").json()
    assert listed[0]["attendance_policy_code"] == "tournament-arrival-desk"
    assert listed[0]["attendance_policy_decision"] == "warn"

    strict_response = client.patch(
        f"/api/v1/events/{event['id']}/attendance-policy",
        headers=identity_headers,
        json={"no_guardian_action": "block"},
    )
    assert strict_response.status_code == 200
    assert strict_response.json()["no_guardian_action"] == "block"

    blocked_response = client.post(
        f"/api/v1/events/{event['id']}/attendance",
        headers=identity_headers,
        json={"person_id": str(minor_person.id), "status": "present"},
    )
    assert blocked_response.status_code == 409
    assert blocked_response.json()["detail"]["attendance_policy_code"] == "tournament-arrival-desk"
