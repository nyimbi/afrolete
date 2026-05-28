import base64
from datetime import UTC, datetime

import pytest

from app.models.enums import (
    ConsentCaptureChannel,
    ConsentScopeType,
    ConsentStatus,
    EventType,
    GuardianRelationshipKind,
    OrganizationType,
)
from app.models.event import ActivityConsent, Event
from app.models.identity import Person
from app.services.safeguarding import clearance_for_event


def test_guardian_can_consent_from_one_use_link(client, identity_headers, athlete_person) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Consent Ready Club",
            "organization_type": "club",
            "contact_email": "office@consent-ready.example",
            "contact_phone": "+254700000001",
            "subdomain": "consent-ready",
            "brand_primary_color": "#0f766e",
        },
    ).json()

    guardian_response = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": str(athlete_person.id),
            "guardian_email": "parent@example.com",
            "guardian_phone": "+254700000002",
            "guardian_display_name": "Parent Example",
            "relationship_kind": "parent",
            "can_sign_consent": True,
            "emergency_contact": True,
        },
    )

    assert guardian_response.status_code == 201
    guardian = guardian_response.json()
    assert guardian["can_sign_consent"] is True

    request_response = client.post(
        "/api/v1/safeguarding/consent-requests",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": str(athlete_person.id),
            "guardian_person_id": guardian["guardian_person_id"],
            "scope_type": "organization",
            "channel": "web_link",
        },
    )

    assert request_response.status_code == 201
    consent_request = request_response.json()
    assert consent_request["one_time_token"]
    assert consent_request["channel"] == "web_link"

    consent_response = client.post(
        "/api/v1/safeguarding/consents/by-token",
        json={
            "token": consent_request["one_time_token"],
            "status": "granted",
            "consent_text": "I consent to participation in club activities.",
        },
    )

    assert consent_response.status_code == 200
    consent = consent_response.json()
    assert consent["status"] == "granted"
    assert consent["capture_channel"] == "web_link"
    assert consent["source_request_id"] == consent_request["id"]
    assert consent["scope_id"] == organization["id"]

    reused_response = client.post(
        "/api/v1/safeguarding/consents/by-token",
        json={"token": consent_request["one_time_token"], "status": "granted"},
    )
    assert reused_response.status_code == 409


def test_guardian_can_consent_by_known_sms_number(client, identity_headers, athlete_person) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "SMS Consent School", "organization_type": "school"},
    ).json()
    guardian = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": str(athlete_person.id),
            "guardian_phone": "+254700000003",
            "guardian_display_name": "SMS Parent",
            "relationship_kind": "legal_guardian",
            "can_sign_consent": True,
        },
    ).json()

    consent_response = client.post(
        "/api/v1/safeguarding/consents/by-known-channel",
        json={
            "organization_id": organization["id"],
            "athlete_person_id": str(athlete_person.id),
            "channel": "sms",
            "source_address": "+254700000003",
            "scope_type": "organization",
            "status": "granted",
            "response_payload": "YES",
        },
    )

    assert guardian["relationship_kind"] == "legal_guardian"
    assert consent_response.status_code == 200
    assert consent_response.json()["capture_channel"] == "sms"


def test_incident_report_package_exports_markdown_and_pdf(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Regulatory Export Club", "organization_type": "club"},
    ).json()
    incident_response = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_type": "injury",
            "severity": "high",
            "occurred_at": "2026-05-28T10:15:00Z",
            "location": "Main field",
            "title": "Concussion protocol report",
            "description": "Athlete removed after head impact and assessed by medical staff.",
            "immediate_action": "Removed from play, guardian notified, return-to-play blocked.",
            "medical_follow_up_required": "yes",
            "regulatory_report_required": True,
        },
    )
    assert incident_response.status_code == 201
    incident = incident_response.json()

    package_response = client.post(
        "/api/v1/safeguarding/incident-report-packages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_id": incident["id"],
            "agency_name": "County safeguarding office",
            "jurisdiction": "Local",
            "due_at": "2026-06-04",
            "external_reference": "SAFE-2026-001",
            "checklist_json": '{"guardian_notification": true, "medical_follow_up": "yes"}',
            "submission_payload": '{"portal": "local-record-only"}',
            "notes": "Prepared for statutory review.",
        },
    )
    assert package_response.status_code == 201
    report_package = package_response.json()

    markdown_response = client.get(
        f"/api/v1/safeguarding/incident-report-packages/{report_package['id']}/artifact",
        headers=identity_headers,
    )
    assert markdown_response.status_code == 200
    markdown = markdown_response.json()
    assert markdown["artifact_format"] == "markdown"
    assert markdown["download_filename"].endswith(".md")
    assert markdown["content_base64"] is None
    assert "Concussion protocol report" in markdown["content"]
    assert "County safeguarding office" in markdown["content"]
    assert len(markdown["checksum"]) == 64
    assert markdown["size_bytes"] > 500

    pdf_response = client.get(
        f"/api/v1/safeguarding/incident-report-packages/{report_package['id']}/artifact?artifact_format=pdf",
        headers=identity_headers,
    )
    assert pdf_response.status_code == 200
    pdf = pdf_response.json()
    assert pdf["artifact_format"] == "pdf"
    assert pdf["download_filename"].endswith(".pdf")
    assert pdf["content_type"] == "application/pdf"
    pdf_bytes = base64.b64decode(pdf["content_base64"])
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert pdf["size_bytes"] == len(pdf_bytes)
    assert len(pdf["checksum"]) == 64


@pytest.mark.asyncio
async def test_minor_requires_guardian_consent_for_event_clearance(db_session) -> None:
    minor = Person(
        display_name="Minor Athlete",
        primary_email="minor@example.com",
        date_of_birth=datetime(2014, 1, 1, tzinfo=UTC).date(),
    )
    guardian = Person(display_name="Guardian", primary_email="guardian-clearance@example.com")
    db_session.add_all([minor, guardian])
    await db_session.flush()

    from app.models.organization import Organization
    from app.models.team import GuardianRelationship

    club = Organization(
        name="Clearance Club",
        slug="clearance-club",
        organization_type=OrganizationType.CLUB,
    )
    db_session.add(club)
    await db_session.flush()
    relationship = GuardianRelationship(
        athlete_person_id=minor.id,
        guardian_person_id=guardian.id,
        relationship_kind=GuardianRelationshipKind.PARENT,
        relationship="parent",
        can_sign_consent=True,
    )
    event = Event(
        organization_id=club.id,
        event_type=EventType.MATCH,
        title="Junior Match",
        starts_at=datetime(2026, 6, 1, 9, 0, tzinfo=UTC),
    )
    db_session.add_all([relationship, event])
    await db_session.commit()

    clearance, is_minor, guardian_required, consent_id, _ = await clearance_for_event(
        db_session,
        event.id,
        minor.id,
    )
    assert clearance == "minor_requires_consent"
    assert is_minor is True
    assert guardian_required is True
    assert consent_id is None

    consent = ActivityConsent(
        organization_id=club.id,
        athlete_person_id=minor.id,
        guardian_person_id=guardian.id,
        scope_type=ConsentScopeType.ORGANIZATION,
        scope_id=club.id,
        status=ConsentStatus.GRANTED,
        capture_channel=ConsentCaptureChannel.MANUAL,
        signed_at=datetime.now(tz=UTC),
    )
    db_session.add(consent)
    await db_session.commit()

    clearance, _, _, consent_id, _ = await clearance_for_event(db_session, event.id, minor.id)
    assert clearance == "cleared"
    assert consent_id == consent.id

    consent.status = ConsentStatus.DENIED
    await db_session.commit()

    clearance, _, _, consent_id, _ = await clearance_for_event(db_session, event.id, minor.id)
    assert clearance == "consent_denied"
    assert consent_id == consent.id
