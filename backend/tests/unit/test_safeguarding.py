import base64
import hmac
import json
import time
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from app.core.config import get_settings
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
from app.services import safeguarding as safeguarding_service
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
    assert markdown["artifact_url"].startswith("local://safeguarding-incident-artifacts/")
    assert markdown["storage_key"].endswith(markdown["download_filename"])

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
    assert pdf["artifact_url"].startswith("local://safeguarding-incident-artifacts/")
    assert pdf["storage_key"].endswith(pdf["download_filename"])

    link_response = client.post(
        f"/api/v1/safeguarding/incident-report-packages/{report_package['id']}/artifact-link?artifact_format=pdf&ttl_seconds=600",
        headers=identity_headers,
    )
    assert link_response.status_code == 200
    link = link_response.json()
    assert link["artifact_format"] == "pdf"
    assert link["filename"].endswith(".pdf")
    assert link["signed_url"].startswith("/api/v1/safeguarding/incident-report-artifacts/")
    assert link["artifact_url"].startswith("local://safeguarding-incident-artifacts/")
    assert link["storage_key"].endswith(link["filename"])
    signed_response = client.get(link["signed_url"])
    assert signed_response.status_code == 200
    assert signed_response.content.startswith(b"%PDF-1.4")
    assert signed_response.headers["x-afrolete-safeguarding-artifact-checksum"] == link["checksum"]

    bad_link = link["signed_url"].replace("signature=", "signature=bad", 1)
    bad_response = client.get(bad_link)
    assert bad_response.status_code == 403

    regulator_response = client.post(
        f"/api/v1/safeguarding/incident-report-packages/{report_package['id']}/submit-regulator?artifact_format=pdf",
        headers=identity_headers,
    )
    assert regulator_response.status_code == 200
    regulator = regulator_response.json()
    assert regulator["delivery_mode"] == "record_only"
    assert regulator["delivery_attempted"] is False
    assert regulator["package_status"] == "submitted"
    assert regulator["artifact_url"].startswith("local://safeguarding-incident-artifacts/")
    assert regulator["storage_key"].endswith(".pdf")
    assert regulator["checksum"]
    assert regulator["failure_reason"].startswith("Record-only regulatory mode")

    packages = client.get(
        f"/api/v1/safeguarding/incident-report-packages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    synced_package = next(item for item in packages if item["id"] == report_package["id"])
    assert synced_package["status"] == "submitted"
    assert "incident_report_package.submit" in synced_package["submission_payload"]
    assert "Record-only regulatory submission" in synced_package["notes"]


def test_insurance_claim_provider_submit_and_status_poll_record_only(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Claims Integration Club", "organization_type": "club"},
    ).json()
    incident = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_type": "injury",
            "severity": "medium",
            "occurred_at": "2026-05-28T11:15:00Z",
            "location": "Training pitch",
            "title": "Ankle injury claim",
            "description": "Athlete rolled ankle during training.",
            "immediate_action": "First aid and clinic referral.",
            "medical_follow_up_required": "yes",
        },
    ).json()
    claim_response = client.post(
        "/api/v1/safeguarding/insurance-claims",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_id": incident["id"],
            "provider_name": "Demo Mutual",
            "policy_number": "POL-2026-CLAIM",
            "claim_type": "injury_medical",
            "claimed_amount_cents": 125000,
            "currency": "USD",
            "reserve_amount_cents": 150000,
            "documentation_checklist_json": '{"medical_note": true}',
        },
    )
    assert claim_response.status_code == 201
    claim = claim_response.json()

    submit_response = client.post(
        f"/api/v1/safeguarding/insurance-claims/{claim['id']}/submit-provider",
        headers=identity_headers,
    )
    assert submit_response.status_code == 200
    submitted = submit_response.json()
    assert submitted["delivery_mode"] == "record_only"
    assert submitted["delivery_attempted"] is False
    assert submitted["claim_status"] == "submitted"
    assert submitted["failure_reason"].startswith("Record-only insurer mode")

    poll_response = client.post(
        f"/api/v1/safeguarding/insurance-claims/{claim['id']}/poll-provider-status",
        headers=identity_headers,
    )
    assert poll_response.status_code == 200
    polled = poll_response.json()
    assert polled["action"] == "status_poll"
    assert polled["claim_status"] == "submitted"

    claims = client.get(
        f"/api/v1/safeguarding/insurance-claims?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    synced_claim = next(item for item in claims if item["id"] == claim["id"])
    assert synced_claim["status"] == "submitted"
    assert "Record-only insurer status_poll" in synced_claim["communication_log"]
    assert "incident_insurance_claim.submit" in synced_claim["submission_payload"]


def test_signed_screening_provider_result_updates_background_check(
    client,
    identity_headers,
    athlete_person,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AFROLETE_SAFEGUARDING_SCREENING_WEBHOOK_SIGNING_KEY", "screening-secret")
    get_settings.cache_clear()
    safeguarding_service.get_settings.cache_clear()
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Screening Provider Club", "organization_type": "club"},
    ).json()
    check = client.post(
        "/api/v1/safeguarding/background-checks",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "person_id": str(athlete_person.id),
            "provider": "SafeScreen",
            "check_type": "Safeguarding background",
            "requested_at": "2026-05-28T09:00:00Z",
            "external_reference": "safe-ref-001",
        },
    ).json()
    payload = {
        "organization_id": organization["id"],
        "background_check_id": check["id"],
        "provider": "SafeScreen",
        "external_reference": "safe-ref-001",
        "provider_result_id": "safe-result-001",
        "provider_status": "consider",
        "risk_level": "high",
        "completed_at": "2026-05-28T11:00:00Z",
        "expires_at": "2027-05-28",
        "result_summary": "Provider found a safeguarding record that requires review.",
        "notes": "Manual adjudication required.",
        "raw_payload": {"score": 87, "risk_band": "high"},
    }
    raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"screening-secret",
        timestamp.encode() + b"." + raw_body.encode(),
        sha256,
    ).hexdigest()

    response = client.post(
        "/api/v1/safeguarding/background-check-provider-results",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Afrolete-Safeguarding-Timestamp": timestamp,
            "X-Afrolete-Safeguarding-Signature": f"sha256={signature}",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["accepted"] is True
    assert result["signature_required"] is True
    assert result["signature_validated"] is True
    assert result["status"] == "review_required"
    assert result["risk_level"] == "high"

    checks = client.get(
        f"/api/v1/safeguarding/background-checks?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    updated = next(item for item in checks if item["id"] == check["id"])
    assert updated["status"] == "review_required"
    assert updated["risk_level"] == "high"
    assert updated["completed_at"].startswith("2026-05-28T11:00:00")
    assert updated["expires_at"] == "2027-05-28"
    assert "safe-result-001" in updated["notes"]
    get_settings.cache_clear()
    safeguarding_service.get_settings.cache_clear()


def test_screening_provider_result_rejects_bad_signature(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AFROLETE_SAFEGUARDING_SCREENING_WEBHOOK_SIGNING_KEY", "screening-secret")
    get_settings.cache_clear()
    safeguarding_service.get_settings.cache_clear()
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Bad Screening Signature Club", "organization_type": "club"},
    ).json()
    payload = {
        "organization_id": organization["id"],
        "provider": "SafeScreen",
        "external_reference": "missing-ref",
        "provider_status": "clear",
        "risk_level": "low",
    }
    raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    response = client.post(
        "/api/v1/safeguarding/background-check-provider-results",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Afrolete-Safeguarding-Timestamp": str(int(time.time())),
            "X-Afrolete-Safeguarding-Signature": "sha256=bad",
        },
    )

    assert response.status_code == 401
    get_settings.cache_clear()
    safeguarding_service.get_settings.cache_clear()


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
