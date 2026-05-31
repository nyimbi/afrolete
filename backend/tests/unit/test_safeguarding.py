import base64
import hmac
import json
import time
from datetime import UTC, date, datetime
from hashlib import sha256
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.config import get_settings
from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.enums import (
    ConsentCaptureChannel,
    ConsentScopeType,
    ConsentStatus,
    EventType,
    GuardianRelationshipKind,
    OrganizationType,
)
from app.models.event import ActivityConsent, Event
from app.models.identity import AppUser, Person
from app.services import safeguarding as safeguarding_service
from app.services.authz.service import authorization_service
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


async def test_guardian_account_readiness_maps_portal_onboarding_status(
    client,
    identity_headers,
    db_session,
) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Guardian Account Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "readiness-athlete@example.com",
            "display_name": "Readiness Athlete",
            "role": "athlete",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Readiness U14",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": member["subject_id"],
            "role": "player",
            "status": "active",
        },
    )
    invite_ready = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": member["subject_id"],
            "guardian_email": "invite-ready-parent@example.com",
            "guardian_display_name": "Invite Ready Parent",
            "relationship_kind": "parent",
            "can_sign_consent": True,
        },
    ).json()
    linked = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": member["subject_id"],
            "guardian_email": "linked-parent@example.com",
            "guardian_display_name": "Linked Parent",
            "relationship_kind": "legal_guardian",
            "can_sign_consent": True,
        },
    ).json()
    batch_ready = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": member["subject_id"],
            "guardian_email": "batch-ready-parent@example.com",
            "guardian_display_name": "Batch Ready Parent",
            "relationship_kind": "parent",
            "can_sign_consent": True,
        },
    ).json()
    db_session.add(
        AppUser(
            keycloak_sub="kc-linked-parent",
            person_id=linked["guardian_person_id"],
            email="linked-parent@example.com",
            display_name="Linked Parent",
        )
    )
    await db_session.commit()

    response = client.get(
        f"/api/v1/safeguarding/guardian-account-readiness?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert response.status_code == 200
    readiness = {item["guardian_person_id"]: item for item in response.json()}
    assert readiness[invite_ready["guardian_person_id"]]["account_status"] == "invite_ready"
    assert readiness[invite_ready["guardian_person_id"]]["can_receive_invite"] is True
    assert readiness[invite_ready["guardian_person_id"]]["last_invite_message_id"] is None
    assert "identity bridge" in readiness[invite_ready["guardian_person_id"]]["recommended_action"]
    assert readiness[batch_ready["guardian_person_id"]]["account_status"] == "invite_ready"
    assert readiness[linked["guardian_person_id"]]["account_status"] == "linked"
    assert readiness[linked["guardian_person_id"]]["linked_app_user_id"]
    assert readiness[linked["guardian_person_id"]]["keycloak_sub"] == "kc-linked-parent"

    invite_response = client.post(
        f"/api/v1/safeguarding/guardian-account-readiness/{invite_ready['id']}/invite",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "email",
            "portal_url": "http://localhost:3000/family",
            "dispatch_now": True,
        },
    )

    assert invite_response.status_code == 200
    invite = invite_response.json()
    assert invite["guardian_person_id"] == invite_ready["guardian_person_id"]
    assert invite["account_status"] == "invite_ready"
    assert invite["destination"] == "invite-ready-parent@example.com"
    parsed_invite_url = urlparse(invite["portal_url"])
    invite_query = parse_qs(parsed_invite_url.query)
    assert parsed_invite_url.scheme == "http"
    assert parsed_invite_url.netloc == "localhost:3000"
    assert parsed_invite_url.path == "/family"
    assert invite_query["organization_id"] == [organization["id"]]
    assert invite_query["relationship_id"] == [invite_ready["id"]]
    assert invite_query["guardian_email"] == ["invite-ready-parent@example.com"]
    assert invite_query["guardian_name"] == ["Invite Ready Parent"]
    assert invite_query["guardian_sub"] == [f"guardian-{invite_ready['id']}"]
    assert invite["delivery_status"] == "queued"
    assert invite["dispatch_attempted"] == 1
    assert invite["dispatch_queued"] == 1
    assert invite["dispatch_delivered"] == 0
    message = await db_session.get(CommunicationMessage, invite["message_id"])
    assert message is not None
    assert message.subject == "Guardian Account Club family portal invitation"
    assert "Readiness Athlete" in message.body
    assert invite["portal_url"] in message.body
    recipient = await db_session.get(MessageRecipient, invite["recipient_id"])
    assert recipient is not None
    assert str(recipient.person_id) == invite_ready["guardian_person_id"]
    readiness_response = client.get(
        f"/api/v1/safeguarding/guardian-account-readiness?organization_id={organization['id']}",
        headers=identity_headers,
    )
    readiness_after_invite = {
        item["guardian_person_id"]: item for item in readiness_response.json()
    }
    invite_ready_after = readiness_after_invite[invite_ready["guardian_person_id"]]
    assert invite_ready_after["last_invite_message_id"] == invite["message_id"]
    assert invite_ready_after["last_invite_channel"] == "email"
    assert invite_ready_after["last_invite_destination"] == "invite-ready-parent@example.com"
    assert invite_ready_after["last_invite_delivery_status"] == "queued"
    assert invite_ready_after["last_invite_sent_at"]
    batch_response = client.post(
        "/api/v1/safeguarding/guardian-account-readiness/invite-batch",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "email",
            "portal_url": "http://localhost:3000/family",
            "dispatch_now": True,
            "skip_recent_hours": 24,
        },
    )
    assert batch_response.status_code == 200
    batch = batch_response.json()
    assert batch["considered"] == 3
    assert batch["invited"] == 1
    assert batch["skipped_recent"] == 1
    assert batch["skipped_linked"] == 1
    assert batch["dispatch_attempted"] == 1
    assert batch["dispatch_queued"] == 1
    assert batch["invites"][0]["guardian_person_id"] == batch_ready["guardian_person_id"]
    assert any("invited recently" in item for item in batch["skipped"])
    assert any("already linked" in item for item in batch["skipped"])
    family_response = client.get(
        f"/api/v1/safeguarding/my-family?organization_id={organization['id']}",
        headers={
            "X-Afrolete-Sub": invite_query["guardian_sub"][0],
            "X-Afrolete-Email": invite_query["guardian_email"][0],
            "X-Afrolete-Name": invite_query["guardian_name"][0],
        },
    )
    assert family_response.status_code == 200
    assert family_response.json()[0]["athlete_name"] == "Readiness Athlete"
    linked_readiness_response = client.get(
        f"/api/v1/safeguarding/guardian-account-readiness?organization_id={organization['id']}",
        headers=identity_headers,
    )
    linked_readiness = {
        item["guardian_person_id"]: item for item in linked_readiness_response.json()
    }
    linked_invite_ready = linked_readiness[invite_ready["guardian_person_id"]]
    assert linked_invite_ready["account_status"] == "linked"
    assert linked_invite_ready["keycloak_sub"] == invite_query["guardian_sub"][0]


async def test_family_dashboard_summarizes_parent_actions(client, identity_headers, db_session) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Family Dashboard Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Family U14",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "dashboard-athlete@example.com",
            "display_name": "Dashboard Athlete",
            "role": "athlete",
        },
    ).json()
    athlete = await db_session.get(Person, member["subject_id"])
    athlete.date_of_birth = date(2013, 4, 1)
    await db_session.commit()
    client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": member["subject_id"],
            "role": "player",
            "status": "active",
        },
    )
    guardian = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": member["subject_id"],
            "guardian_email": "dashboard-parent@example.com",
            "guardian_display_name": "Dashboard Parent",
            "relationship_kind": "parent",
            "can_sign_consent": True,
            "emergency_contact": True,
        },
    ).json()
    second_team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Family U12",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    second_member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "dashboard-second-athlete@example.com",
            "display_name": "Dashboard Second Athlete",
            "role": "athlete",
        },
    ).json()
    client.post(
        f"/api/v1/teams/{second_team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": second_member["subject_id"],
            "role": "player",
            "status": "active",
        },
    )
    client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": second_member["subject_id"],
            "guardian_person_id": guardian["guardian_person_id"],
            "relationship_kind": "parent",
            "can_sign_consent": True,
            "emergency_contact": True,
        },
    )
    event = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_type": "match",
            "title": "Family dashboard fixture",
            "starts_at": "2099-06-10T15:00:00Z",
            "venue_name": "North Field",
        },
    ).json()
    client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": second_team["id"],
            "event_type": "training",
            "title": "Overlapping sibling training",
            "starts_at": "2099-06-10T15:30:00Z",
            "ends_at": "2099-06-10T16:30:00Z",
            "venue_name": "East Gym",
        },
    )
    client.post(
        "/api/v1/safeguarding/consent-requests",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": member["subject_id"],
            "guardian_person_id": guardian["guardian_person_id"],
            "scope_type": "event",
            "scope_id": event["id"],
            "channel": "email",
            "expires_at": "2099-06-09T12:00:00Z",
        },
    )
    client.post(
        "/api/v1/communications/messages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "message_type": "reminder",
            "channel": "in_app",
            "scope_type": "person",
            "scope_id": guardian["guardian_person_id"],
            "recipient_person_ids": [guardian["guardian_person_id"]],
            "subject": "Urgent family update",
            "body": "Please review consent and RSVP before travel.",
            "urgent": True,
        },
    )
    parent_headers = {
        "X-Afrolete-Sub": "kc-parent-dashboard",
        "X-Afrolete-Email": "dashboard-parent@example.com",
        "X-Afrolete-Name": "Dashboard Parent",
    }

    dashboard_response = client.get(
        f"/api/v1/safeguarding/my-family/dashboard?organization_id={organization['id']}",
        headers=parent_headers,
    )

    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["child_count"] == 2
    assert dashboard["pending_consent_count"] == 1
    assert dashboard["unread_message_count"] == 1
    assert dashboard["urgent_unread_count"] == 1
    assert dashboard["upcoming_event_count"] == 2
    assert dashboard["rsvp_needed_count"] == 2
    assert dashboard["clearance_blocked_count"] == 1
    assert dashboard["schedule_conflict_count"] == 1
    assert dashboard["schedule_conflicts"][0]["athlete_names"] == [
        "Dashboard Athlete",
        "Dashboard Second Athlete",
    ]
    assert "overlapping commitments" in dashboard["schedule_conflicts"][0]["recommendation"]
    assert dashboard["next_event_at"].startswith("2099-06-10T15:00:00")
    action_types = {item["action_type"] for item in dashboard["action_items"]}
    assert {"consent", "clearance", "rsvp", "message", "schedule_conflict"}.issubset(action_types)


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
    assert regulator["provider_profile"] == "local_safeguarding_office"
    assert regulator["provider_schema_id"] == "safeguarding.regulatory.local_safeguarding_office.v1"
    assert regulator["failure_reason"].startswith("Record-only regulatory mode")

    packages = client.get(
        f"/api/v1/safeguarding/incident-report-packages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    synced_package = next(item for item in packages if item["id"] == report_package["id"])
    assert synced_package["status"] == "submitted"
    assert "incident_report_package.submit" in synced_package["submission_payload"]
    regulatory_payload = json.loads(synced_package["submission_payload"])
    assert regulatory_payload["provider_schema"]["provider_payload"]["statutory_incident_report"]
    assert regulatory_payload["provider_schema"]["required_fields"]
    assert "Record-only regulatory submission" in synced_package["notes"]


def test_incident_investigation_actions_assign_escalate_and_close(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Investigation Workflow Club", "organization_type": "club"},
    ).json()
    incident = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_type": "safeguarding",
            "severity": "medium",
            "occurred_at": "2026-05-28T10:45:00Z",
            "location": "Away changing room",
            "title": "Safeguarding concern",
            "description": "Athlete reported an uncomfortable interaction after training.",
            "immediate_action": "Separated parties and notified safeguarding lead.",
            "medical_follow_up_required": "unknown",
        },
    ).json()

    assign_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/investigation-actions",
        headers=identity_headers,
        json={
            "action_type": "assign_self",
            "assign_to_self": True,
            "next_step": "Lead accepts ownership and starts witness collection.",
        },
    )
    assert assign_response.status_code == 200
    assigned = assign_response.json()
    assert assigned["status"] == "triaged"
    assert assigned["assigned_to_person_id"] is not None
    assert "Assigned to" in assigned["action_summary"]

    escalate_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/investigation-actions",
        headers=identity_headers,
        json={
            "action_type": "escalate",
            "finding_summary": "Initial review suggests statutory reporting may be required.",
            "parent_notified": True,
            "medical_follow_up_required": "yes",
        },
    )
    assert escalate_response.status_code == 200
    escalated = escalate_response.json()
    assert escalated["status"] == "investigating"
    assert escalated["severity"] == "high"
    assert escalated["regulatory_report_required"] is True
    assert escalated["medical_follow_up_required"] == "yes"
    assert "Regulatory reporting required" in escalated["action_summary"]

    close_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/investigation-actions",
        headers=identity_headers,
        json={
            "action_type": "close",
            "close_incident": True,
            "finding_summary": "Case reviewed and controls documented.",
            "next_step": "Monitor future sessions for recurrence.",
        },
    )
    assert close_response.status_code == 200
    closed = close_response.json()
    assert closed["status"] == "closed"
    assert "Case reviewed" in closed["resolution_notes"]

    incidents = client.get(
        f"/api/v1/safeguarding/incidents?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    synced = next(item for item in incidents if item["id"] == incident["id"])
    assert synced["status"] == "closed"
    assert synced["assigned_to_person_id"] == assigned["assigned_to_person_id"]
    assert synced["regulatory_report_required"] is True
    assert synced["parent_notified_at"] is not None


def test_incident_access_controls_sync_case_relationships(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Access Controlled Safeguarding Club", "organization_type": "club"},
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Access Control U15",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    athlete = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "access-control-athlete@example.com",
            "display_name": "Access Control Athlete",
            "country_code": "KE",
            "role": "athlete",
        },
    ).json()
    roster_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": athlete["subject_id"],
            "role": "player",
            "status": "active",
        },
    )
    assert roster_response.status_code == 201
    guardian = client.post(
        "/api/v1/safeguarding/guardians",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": athlete["subject_id"],
            "guardian_email": "medical-guardian@example.com",
            "guardian_display_name": "Medical Guardian",
            "relationship_kind": "parent",
            "can_sign_consent": True,
            "can_view_medical": True,
        },
    ).json()
    incident_response = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_person_id": athlete["subject_id"],
            "team_id": team["id"],
            "incident_type": "safeguarding",
            "severity": "high",
            "occurred_at": "2026-05-28T12:15:00Z",
            "location": "Medical room",
            "title": "Access controlled case",
            "description": "Sensitive safeguarding case with guardian medical visibility.",
            "immediate_action": "Restricted case access and notified safeguarding lead.",
            "medical_follow_up_required": "yes",
            "regulatory_report_required": True,
        },
    )
    assert incident_response.status_code == 201
    incident = incident_response.json()

    sync_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/access-controls/sync",
        headers=identity_headers,
    )
    assert sync_response.status_code == 200
    sync = sync_response.json()
    assert sync["can_manage_case"] is True
    assert sync["can_review_evidence"] is True
    assert sync["relationship_count"] >= 8
    assert any("#parent_org@organization:" in item for item in sync["touched_relationships"])
    assert any("#case_manager@user:" in item for item in sync["touched_relationships"])
    assert any(f"#athlete@person:{athlete['subject_id']}" in item for item in sync["touched_relationships"])
    assert any(f"#guardian@person:{guardian['guardian_person_id']}" in item for item in sync["touched_relationships"])
    assert any(f"#medical_viewer@person:{guardian['guardian_person_id']}" in item for item in sync["touched_relationships"])
    assert any("#regulator@person:" in item for item in sync["touched_relationships"])

    reviewer_headers = {
        "X-Afrolete-Sub": "kc-incident-reviewer",
        "X-Afrolete-Email": "incident-reviewer@example.com",
        "X-Afrolete-Name": "Incident Reviewer",
    }
    reviewer_member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "incident-reviewer@example.com",
            "display_name": "Incident Reviewer",
            "role": "staff",
        },
    ).json()
    assert client.get("/api/v1/organizations", headers=reviewer_headers).status_code == 200
    owner_upload_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence",
        headers=identity_headers,
        json={
            "filename": "Grant Evidence.txt",
            "content_type": "text/plain",
            "content_base64": base64.b64encode(b"grant evidence").decode(),
            "evidence_type": "safeguarding_case_note",
            "review_status": "needs_review",
        },
    )
    assert owner_upload_response.status_code == 200
    owner_upload = owner_upload_response.json()
    grant_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/access-grants",
        headers=identity_headers,
        json={
            "person_id": reviewer_member["subject_id"],
            "relation": "evidence_reviewer",
            "reason": "Temporary external safeguarding evidence review.",
        },
    )
    assert grant_response.status_code == 201
    grant = grant_response.json()
    assert grant["active"] is True
    assert grant["relation"] == "evidence_reviewer"

    authorization_service.relationships = {
        relationship
        for relationship in authorization_service.relationships
        if relationship.resource_type != "organization"
    }
    reviewer_link_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence-link",
        headers=reviewer_headers,
        json={
            "storage_key": owner_upload["storage_key"],
            "filename": owner_upload["filename"],
            "content_type": owner_upload["content_type"],
            "checksum": owner_upload["checksum"],
            "ttl_seconds": 300,
        },
    )
    assert reviewer_link_response.status_code == 200

    revoke_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/access-grants/{grant['id']}/revoke",
        headers=identity_headers,
        json={"reason": "Review window closed."},
    )
    assert revoke_response.status_code == 200
    revoked = revoke_response.json()
    assert revoked["active"] is False
    assert revoked["revoked_at"] is not None
    assert revoked["revoked_reason"] == "Review window closed."

    revoked_link_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence-link",
        headers=reviewer_headers,
        json={
            "storage_key": owner_upload["storage_key"],
            "filename": owner_upload["filename"],
            "content_type": owner_upload["content_type"],
            "checksum": owner_upload["checksum"],
            "ttl_seconds": 300,
        },
    )
    assert revoked_link_response.status_code == 403

    historical_grants_response = client.get(
        f"/api/v1/safeguarding/incidents/{incident['id']}/access-grants",
        headers=identity_headers,
    )
    assert historical_grants_response.status_code == 200
    historical_grants = historical_grants_response.json()
    assert historical_grants[0]["id"] == grant["id"]
    assert historical_grants[0]["active"] is False

    evidence_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence",
        headers=identity_headers,
        json={
            "filename": "Restricted Evidence.txt",
            "content_type": "text/plain",
            "content_base64": base64.b64encode(b"restricted evidence").decode(),
            "evidence_type": "safeguarding_case_note",
            "review_status": "needs_review",
        },
    )
    assert evidence_response.status_code == 200
    assert evidence_response.json()["storage_key"].endswith("Restricted-Evidence.txt")


def test_incident_evidence_upload_stores_file_and_case_note(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Evidence Review Club", "organization_type": "club"},
    ).json()
    incident = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_type": "misconduct",
            "severity": "high",
            "occurred_at": "2026-05-28T13:45:00Z",
            "location": "Training pitch",
            "title": "Evidence review case",
            "description": "Staff uploaded a written witness statement for review.",
            "immediate_action": "Safeguarding lead opened an investigation.",
            "medical_follow_up_required": "no",
        },
    ).json()
    content = b"Witness statement: coach separated the parties and logged the concern."

    response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence",
        headers=identity_headers,
        json={
            "filename": "Witness Statement.txt",
            "content_type": "text/plain",
            "content_base64": base64.b64encode(content).decode(),
            "evidence_type": "witness_statement",
            "review_status": "accepted",
            "notes": "Reviewed by safeguarding lead.",
        },
    )

    assert response.status_code == 200
    upload = response.json()
    assert upload["filename"] == "Witness-Statement.txt"
    assert upload["content_type"] == "text/plain"
    assert upload["size_bytes"] == len(content)
    assert upload["checksum"] == sha256(content).hexdigest()
    assert upload["evidence_url"].startswith("local://safeguarding-incident-evidence/")
    assert upload["storage_key"].endswith("Witness-Statement.txt")
    assert upload["incident"]["status"] == "investigating"
    assert "Evidence uploaded" in upload["incident"]["resolution_notes"]

    link_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence-link",
        headers=identity_headers,
        json={
            "storage_key": upload["storage_key"],
            "filename": upload["filename"],
            "content_type": upload["content_type"],
            "checksum": upload["checksum"],
            "ttl_seconds": 600,
        },
    )
    assert link_response.status_code == 200
    link = link_response.json()
    assert link["signed_url"].startswith("/api/v1/safeguarding/incident-evidence/")
    assert link["checksum"] == upload["checksum"]
    assert link["storage_key"] == upload["storage_key"]

    signed_response = client.get(link["signed_url"])
    assert signed_response.status_code == 200
    assert signed_response.content == content
    assert signed_response.headers["x-afrolete-safeguarding-evidence-checksum"] == upload["checksum"]

    bad_link = link["signed_url"].replace("signature=", "signature=bad", 1)
    bad_response = client.get(bad_link)
    assert bad_response.status_code == 403


def test_incident_evidence_review_queue_and_actions(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Evidence Queue Club", "organization_type": "club"},
    ).json()
    policy_rule_response = client.post(
        "/api/v1/safeguarding/evidence-policy-rules",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "rule_code": "case-note-board-escalation",
            "title": "Case note board escalation",
            "incident_type": "safeguarding",
            "minimum_severity": "medium",
            "evidence_type_contains": "case_note",
            "required_approval_level": "board_safeguarding_panel",
            "risk_level": "critical",
            "recommended_review_status": "escalated",
            "block_acceptance": True,
            "rationale": "Tenant-authored policy requires board safeguarding panel review for case notes.",
        },
    )
    assert policy_rule_response.status_code == 201
    policy_rule = policy_rule_response.json()
    assert policy_rule["rule_code"] == "case-note-board-escalation"

    duplicate_rule_response = client.post(
        "/api/v1/safeguarding/evidence-policy-rules",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "rule_code": "case-note-board-escalation",
            "title": "Duplicate rule",
            "required_approval_level": "duplicate_panel",
            "rationale": "Duplicate tenant policy should be rejected.",
        },
    )
    assert duplicate_rule_response.status_code == 409

    listed_rules_response = client.get(
        f"/api/v1/safeguarding/evidence-policy-rules?organization_id={organization['id']}&active=true",
        headers=identity_headers,
    )
    assert listed_rules_response.status_code == 200
    assert [rule["rule_code"] for rule in listed_rules_response.json()] == ["case-note-board-escalation"]

    incident = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_type": "safeguarding",
            "severity": "medium",
            "occurred_at": "2026-05-28T14:45:00Z",
            "location": "Clubhouse",
            "title": "Safeguarding evidence queue case",
            "description": "A safeguarding lead needs to approve submitted evidence.",
            "immediate_action": "Evidence was quarantined for lead review.",
            "medical_follow_up_required": "no",
        },
    ).json()
    content = b"Safeguarding evidence that requires review."
    upload_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence",
        headers=identity_headers,
        json={
            "filename": "Lead Review.txt",
            "content_type": "text/plain",
            "content_base64": base64.b64encode(content).decode(),
            "evidence_type": "case_note",
            "review_status": "needs_review",
            "notes": "Awaiting safeguarding lead decision.",
        },
    )
    assert upload_response.status_code == 200
    upload = upload_response.json()

    queue_response = client.get(
        f"/api/v1/safeguarding/incident-evidence-review-queue?organization_id={organization['id']}&review_status=needs_review",
        headers=identity_headers,
    )
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert len(queue) == 1
    assert queue[0]["incident_id"] == incident["id"]
    assert queue[0]["filename"] == "Lead-Review.txt"
    assert queue[0]["review_status"] == "needs_review"
    assert queue[0]["storage_key"] == upload["storage_key"]
    assert queue[0]["checksum"] == upload["checksum"]
    assert queue[0]["approval_policy"]["policy_risk_level"] == "critical"
    assert queue[0]["approval_policy"]["recommended_review_status"] == "escalated"
    assert queue[0]["approval_policy"]["acceptance_blocked_by_policy"] is True
    assert "safeguarding_committee" in queue[0]["approval_policy"]["required_approval_levels"]
    assert "board_safeguarding_panel" in queue[0]["approval_policy"]["required_approval_levels"]
    assert queue[0]["approval_policy"]["matched_rule_codes"] == ["case-note-board-escalation"]

    policy_response = client.get(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence-approval-policy?storage_key={upload['storage_key']}",
        headers=identity_headers,
    )
    assert policy_response.status_code == 200
    policy = policy_response.json()
    assert policy["approval_status"] == "escalation_required"
    assert policy["approval_required"] is True
    assert policy["matched_rule_codes"] == ["case-note-board-escalation"]

    direct_accept_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence-review",
        headers=identity_headers,
        json={
            "storage_key": upload["storage_key"],
            "filename": upload["filename"],
            "checksum": upload["checksum"],
            "review_status": "accepted",
            "review_notes": "Trying to bypass escalation.",
        },
    )
    assert direct_accept_response.status_code == 409
    assert direct_accept_response.json()["detail"] == "Evidence approval policy requires escalation before acceptance"

    review_response = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence-review",
        headers=identity_headers,
        json={
            "storage_key": upload["storage_key"],
            "filename": upload["filename"],
            "checksum": upload["checksum"],
            "review_status": "escalated",
            "review_notes": "Escalate to the safeguarding committee.",
            "escalate_incident": True,
        },
    )
    assert review_response.status_code == 200
    review = review_response.json()
    assert review["review_status"] == "escalated"
    assert review["incident_status"] == "investigating"
    assert review["incident_severity"] == "high"
    assert review["regulatory_report_required"] is True
    assert review["approval_policy"]["approval_status"] == "escalated"
    assert review["approval_policy"]["acceptance_blocked_by_policy"] is False
    assert "Evidence review" in review["resolution_notes"]

    escalated_queue_response = client.get(
        f"/api/v1/safeguarding/incident-evidence-review-queue?organization_id={organization['id']}&review_status=escalated",
        headers=identity_headers,
    )
    assert escalated_queue_response.status_code == 200
    escalated_queue = escalated_queue_response.json()
    assert len(escalated_queue) == 1
    assert escalated_queue[0]["review_status"] == "escalated"
    assert escalated_queue[0]["latest_review_notes"] == "Escalate to the safeguarding committee."

    disable_rule_response = client.patch(
        f"/api/v1/safeguarding/evidence-policy-rules/{policy_rule['id']}",
        headers=identity_headers,
        json={"active": False},
    )
    assert disable_rule_response.status_code == 200
    assert disable_rule_response.json()["active"] is False

    active_rules_after_disable = client.get(
        f"/api/v1/safeguarding/evidence-policy-rules?organization_id={organization['id']}&active=true",
        headers=identity_headers,
    )
    assert active_rules_after_disable.status_code == 200
    assert active_rules_after_disable.json() == []

    bad_review = client.post(
        f"/api/v1/safeguarding/incidents/{incident['id']}/evidence-review",
        headers=identity_headers,
        json={
            "storage_key": upload["storage_key"],
            "filename": upload["filename"],
            "checksum": "0" * 64,
            "review_status": "accepted",
        },
    )
    assert bad_review.status_code == 409


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
    assert submitted["provider_profile"] == "medical_claim"
    assert submitted["provider_schema_id"] == "safeguarding.insurance.medical_claim.v1"
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
    claim_payload = json.loads(synced_claim["submission_payload"])
    assert claim_payload["provider_schema"]["provider_payload"]["medical_expense_claim"]
    assert claim_payload["provider_schema"]["field_map"]["policy_id"] == "policy_number"


def test_insurance_policy_portfolio_links_coverage_and_claims(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Insurance Portfolio Club", "organization_type": "club"},
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
            "title": "Covered ankle injury",
            "description": "Athlete rolled ankle during training.",
            "immediate_action": "First aid and clinic referral.",
            "medical_follow_up_required": "yes",
        },
    ).json()

    policy_response = client.post(
        "/api/v1/safeguarding/insurance-policies",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Accident Medical 2026",
            "policy_type": "accident_medical",
            "provider_name": "Athletic Health Insurers",
            "policy_number": "AHI-2026-001",
            "group_number": "RFC-2026",
            "broker_name": "Nairobi Sports Brokers",
            "broker_email": "broker@example.com",
            "coverage_summary": "Primary athlete injury coverage.",
            "covered_subjects": "Registered athletes, sanctioned training, matches, and travel.",
            "coverage_limit_cents": 2500000,
            "deductible_cents": 0,
            "premium_cents": 1200000,
            "currency": "USD",
            "effective_on": "2026-01-01",
            "expires_on": "2026-12-31",
            "renewal_notice_days": 365,
            "certificate_url": "https://example.test/certificates/ahi-2026.pdf",
        },
    )
    assert policy_response.status_code == 201
    policy = policy_response.json()
    assert policy["renewal_due"] is True
    assert policy["claim_count"] == 0

    coverage_response = client.post(
        "/api/v1/safeguarding/insurance-coverage/verify",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_id": incident["id"],
            "claim_type": "injury_medical",
            "amount_cents": 125000,
        },
    )
    assert coverage_response.status_code == 200
    coverage = coverage_response.json()
    assert coverage["covered"] is True
    assert coverage["policy_id"] == policy["id"]
    assert coverage["policy_number"] == "AHI-2026-001"
    assert coverage["estimated_payable_cents"] == 125000
    assert coverage["certificate_url"].endswith("ahi-2026.pdf")

    claim_response = client.post(
        "/api/v1/safeguarding/insurance-claims",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_id": incident["id"],
            "insurance_policy_id": policy["id"],
            "provider_name": "Placeholder Provider",
            "claim_type": "injury_medical",
            "claimed_amount_cents": 125000,
            "currency": "KES",
            "reserve_amount_cents": 150000,
        },
    )
    assert claim_response.status_code == 201
    claim = claim_response.json()
    assert claim["insurance_policy_id"] == policy["id"]
    assert claim["provider_name"] == "Athletic Health Insurers"
    assert claim["policy_number"] == "AHI-2026-001"
    assert claim["currency"] == "USD"

    listed_policies = client.get(
        f"/api/v1/safeguarding/insurance-policies?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert listed_policies[0]["claim_count"] == 1
    assert listed_policies[0]["open_claim_count"] == 1

    summary = client.get(
        f"/api/v1/safeguarding/insurance-portfolio/summary?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert summary["policy_count"] == 1
    assert summary["active_policy_count"] == 1
    assert summary["expiring_policy_count"] == 1
    assert summary["annual_premium_cents"] == 1200000
    assert summary["open_claim_count"] == 1
    assert "Accident Medical 2026" in summary["renewal_alerts"][0]


def test_medical_clearance_provider_submit_and_status_poll_record_only(
    client,
    identity_headers,
) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Medical Portal Club", "organization_type": "club"},
    ).json()
    athlete = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "medical-clearance-athlete@example.com",
            "display_name": "Medical Clearance Athlete",
            "country_code": "KE",
            "role": "athlete",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Medical Portal U15",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    roster_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": athlete["subject_id"],
            "role": "player",
            "status": "active",
        },
    )
    assert roster_response.status_code == 201
    incident = client.post(
        "/api/v1/safeguarding/incidents",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_type": "injury",
            "severity": "medium",
            "occurred_at": "2026-05-28T12:15:00Z",
            "location": "Clinic room",
            "athlete_person_id": athlete["subject_id"],
            "title": "Return-to-play review",
            "description": "Athlete needs physician clearance after injury.",
            "immediate_action": "Held from training pending medical review.",
            "medical_follow_up_required": "yes",
        },
    ).json()
    clearance_response = client.post(
        "/api/v1/safeguarding/medical-clearances",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "incident_id": incident["id"],
            "athlete_person_id": athlete["subject_id"],
            "clearance_type": "return_to_play",
            "provider_name": "Demo Sports Clinic",
            "return_to_play_stage": "assessment",
            "restrictions": "No contact drills.",
        },
    )
    assert clearance_response.status_code == 201
    clearance = clearance_response.json()

    submit_response = client.post(
        f"/api/v1/safeguarding/medical-clearances/{clearance['id']}/submit-provider",
        headers=identity_headers,
    )
    assert submit_response.status_code == 200
    submitted = submit_response.json()
    assert submitted["delivery_mode"] == "record_only"
    assert submitted["delivery_attempted"] is False
    assert submitted["clearance_status"] == "pending_review"
    assert submitted["provider_profile"] == "return_to_play_clearance"
    assert submitted["provider_schema_id"] == "safeguarding.medical.return_to_play_clearance.v1"
    assert submitted["failure_reason"].startswith("Record-only medical portal mode")

    poll_response = client.post(
        f"/api/v1/safeguarding/medical-clearances/{clearance['id']}/poll-provider-status",
        headers=identity_headers,
    )
    assert poll_response.status_code == 200
    polled = poll_response.json()
    assert polled["action"] == "status_poll"
    assert polled["clearance_status"] == "pending_review"

    clearances = client.get(
        f"/api/v1/safeguarding/medical-clearances?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    synced_clearance = next(item for item in clearances if item["id"] == clearance["id"])
    assert synced_clearance["reviewed_by_person_id"] is not None
    assert "Record-only medical portal status_poll" in synced_clearance["notes"]


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
    submission_response = client.post(
        f"/api/v1/safeguarding/background-checks/{check['id']}/submit-provider",
        headers=identity_headers,
    )
    assert submission_response.status_code == 200
    submission = submission_response.json()
    assert submission["delivery_mode"] == "record_only"
    assert submission["delivery_attempted"] is False
    assert submission["check_status"] == "in_progress"
    assert submission["provider_profile"] == "safe_sport_screening"
    assert submission["provider_schema_id"] == "safeguarding.screening.safe_sport_screening.v1"
    assert submission["provider_payload"]["safesport_screening_request"]["case_reference"] == "safe-ref-001"
    assert submission["failure_reason"].startswith("Record-only screening mode")
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


def test_background_check_evidence_document_review_and_signed_access(
    client,
    identity_headers,
    athlete_person,
) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Screening Evidence Club", "organization_type": "club"},
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
            "external_reference": "safe-evidence-001",
        },
    ).json()
    content = b"SafeScreen report: candidate cleared after manual safeguarding review."

    upload_response = client.post(
        f"/api/v1/safeguarding/background-checks/{check['id']}/evidence",
        headers=identity_headers,
        json={
            "filename": "Screening Report.txt",
            "content_type": "text/plain",
            "content_base64": base64.b64encode(content).decode(),
            "document_type": "screening_report",
            "review_status": "needs_review",
            "provider_reference": "safe-evidence-001",
            "notes": "Provider report uploaded by the safeguarding desk.",
        },
    )
    assert upload_response.status_code == 201
    document = upload_response.json()
    assert document["filename"] == "Screening-Report.txt"
    assert document["checksum"] == sha256(content).hexdigest()
    assert document["review_status"] == "needs_review"
    assert document["background_check_status"] == "review_required"
    assert document["evidence_url"].startswith("local://safeguarding-incident-evidence/background-checks/")
    assert document["storage_key"].endswith("Screening-Report.txt")

    list_response = client.get(
        f"/api/v1/safeguarding/background-checks/{check['id']}/evidence",
        headers=identity_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == document["id"]

    review_response = client.post(
        f"/api/v1/safeguarding/background-check-evidence/{document['id']}/review",
        headers=identity_headers,
        json={
            "review_status": "accepted",
            "review_notes": "Safeguarding lead accepted the provider evidence.",
            "check_status": "clear",
            "risk_level": "low",
            "result_summary": "Evidence accepted; candidate cleared.",
        },
    )
    assert review_response.status_code == 200
    reviewed = review_response.json()
    assert reviewed["review_status"] == "accepted"
    assert reviewed["reviewed_by_person_id"] is not None
    assert reviewed["reviewed_at"] is not None
    assert reviewed["background_check_status"] == "clear"
    assert reviewed["background_check_risk_level"] == "low"

    link_response = client.post(
        f"/api/v1/safeguarding/background-check-evidence/{document['id']}/link",
        headers=identity_headers,
        json={"ttl_seconds": 600},
    )
    assert link_response.status_code == 200
    link = link_response.json()
    assert link["signed_url"].startswith("/api/v1/safeguarding/background-check-evidence/")
    assert link["checksum"] == reviewed["checksum"]
    assert link["storage_key"] == reviewed["storage_key"]

    signed_response = client.get(link["signed_url"])
    assert signed_response.status_code == 200
    assert signed_response.content == content
    assert signed_response.headers["x-afrolete-background-check-evidence-checksum"] == reviewed["checksum"]

    checks = client.get(
        f"/api/v1/safeguarding/background-checks?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    updated = next(item for item in checks if item["id"] == check["id"])
    assert updated["status"] == "clear"
    assert updated["risk_level"] == "low"
    assert "Evidence document Screening-Report.txt" in updated["notes"]


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
