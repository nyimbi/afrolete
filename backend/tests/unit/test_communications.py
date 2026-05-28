from app.core.config import Settings, get_settings


def create_communications_context(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Communications Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U15 Comms",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "comms-athlete@example.com",
            "display_name": "Comms Athlete",
            "role": "athlete",
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
    return organization, team, member


def test_template_team_message_recipients_and_read_receipt(client, identity_headers) -> None:
    organization, team, member = create_communications_context(client, identity_headers)

    template_response = client.post(
        "/api/v1/communications/templates",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Training Reminder",
            "message_type": "reminder",
            "channel": "email",
            "subject_template": "Training reminder for {team.name}",
            "body_template": "Please arrive 15 minutes early for {event.type}.",
            "variables": "team.name,event.type",
        },
    )

    assert template_response.status_code == 201
    template = template_response.json()
    assert template["message_type"] == "reminder"

    message_response = client.post(
        "/api/v1/communications/messages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "template_id": template["id"],
            "message_type": "reminder",
            "channel": "email",
            "scope_type": "team",
            "scope_id": team["id"],
            "subject": "Training reminder",
            "body": "Training starts at 16:00. Bring boots and water.",
        },
    )

    assert message_response.status_code == 201
    message = message_response.json()
    assert message["recipient_count"] == 1
    assert message["status"] == "sent"
    assert message["sent_at"] is not None

    recipients = client.get(f"/api/v1/communications/messages/{message['id']}/recipients").json()
    assert len(recipients) == 1
    assert recipients[0]["person_id"] == member["subject_id"]
    assert recipients[0]["destination"] == "comms-athlete@example.com"
    assert recipients[0]["delivery_status"] == "queued"

    read_response = client.patch(
        f"/api/v1/communications/recipients/{recipients[0]['id']}",
        headers=identity_headers,
        json={"delivery_status": "read"},
    )

    assert read_response.status_code == 200
    assert read_response.json()["delivery_status"] == "read"
    assert read_response.json()["read_at"] is not None


def test_record_only_dispatch_and_delivery_callback(client, identity_headers) -> None:
    organization, team, _ = create_communications_context(client, identity_headers)
    message = client.post(
        "/api/v1/communications/messages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "message_type": "reminder",
            "channel": "email",
            "scope_type": "team",
            "scope_id": team["id"],
            "subject": "Fixture transport",
            "body": "The bus leaves at 14:00.",
        },
    ).json()

    dispatch_response = client.post(
        f"/api/v1/communications/messages/{message['id']}/dispatch",
        headers=identity_headers,
    )

    assert dispatch_response.status_code == 200
    summary = dispatch_response.json()
    assert summary["attempted"] == 1
    assert summary["transport_mode"] == "record_only"
    assert summary["queued"] == 1

    recipients = client.get(f"/api/v1/communications/messages/{message['id']}/recipients").json()
    assert recipients[0]["delivery_status"] == "queued"
    assert "No email delivery webhook configured" in recipients[0]["failure_reason"]

    callback_response = client.post(
        "/api/v1/communications/delivery-events",
        json={
            "recipient_id": recipients[0]["id"],
            "delivery_status": "delivered",
        },
    )

    assert callback_response.status_code == 200
    callback = callback_response.json()
    assert callback["delivery_status"] == "delivered"
    assert callback["delivered_at"] is not None


def test_delivery_readiness_reports_record_only_and_webhook_channels(client, identity_headers) -> None:
    record_only_response = client.get("/api/v1/communications/delivery-readiness", headers=identity_headers)

    assert record_only_response.status_code == 200
    record_only = record_only_response.json()
    assert record_only["delivery_mode"] == "record_only"
    assert record_only["dispatch_ready_count"] == 6
    assert record_only["live_ready_count"] == 1
    channels = {item["channel"]: item for item in record_only["channels"]}
    assert channels["in_app"]["status"] == "in_app"
    assert channels["email"]["status"] == "record_only"
    assert channels["email"]["dispatch_ready"] is True
    assert channels["email"]["live_ready"] is False

    client.app.dependency_overrides[get_settings] = lambda: Settings(
        communication_delivery_mode="webhook",
        communication_email_webhook_url="https://email-provider.example/dispatch",
        communication_webhook_key="shared-secret",
    )
    webhook_response = client.get("/api/v1/communications/delivery-readiness", headers=identity_headers)

    assert webhook_response.status_code == 200
    webhook = webhook_response.json()
    webhook_channels = {item["channel"]: item for item in webhook["channels"]}
    assert webhook["delivery_mode"] == "webhook"
    assert webhook["key_source"] == "env"
    assert webhook["key_configured"] is True
    assert webhook_channels["email"]["status"] == "ready"
    assert webhook_channels["email"]["webhook_source"] == "channel"
    assert webhook_channels["email"]["live_ready"] is True
    assert webhook_channels["sms"]["status"] == "missing_webhook"
    assert webhook["blocked_count"] == 4


def test_inbox_digest_and_ai_assisted_draft(client, identity_headers) -> None:
    organization, team, member = create_communications_context(client, identity_headers)
    message = client.post(
        "/api/v1/communications/messages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "message_type": "announcement",
            "channel": "in_app",
            "scope_type": "team",
            "scope_id": team["id"],
            "subject": "Parent update",
            "body": "Training has moved to pitch two.",
        },
    ).json()

    inbox_response = client.get(
        "/api/v1/communications/inbox",
        headers=identity_headers,
        params={
            "organization_id": organization["id"],
            "person_id": member["subject_id"],
        },
    )

    assert inbox_response.status_code == 200
    inbox = inbox_response.json()
    assert inbox[0]["message_id"] == message["id"]
    assert inbox[0]["subject"] == "Parent update"

    digest_response = client.post(
        "/api/v1/communications/digests",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "person_id": member["subject_id"],
            "frequency": "daily_digest",
        },
    )

    assert digest_response.status_code == 201
    digest = digest_response.json()
    assert digest["item_count"] == 1
    assert digest["channel"] == "in_app"
    assert "Parent update" in digest["body"]

    draft_response = client.post(
        "/api/v1/communications/drafts",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "message_type": "reminder",
            "channel": "email",
            "scope_type": "team",
            "scope_id": team["id"],
            "intent": "Remind families that the fixture bus leaves at 14:00.",
            "tone": "firm and warm",
            "audience": "players and guardians",
        },
    )

    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert team["name"] in draft["subject"]
    assert "fixture bus leaves at 14:00" in draft["body"]
    assert draft["review_required"] is True


def test_notification_preferences_and_cross_org_recipient_guard(client, identity_headers) -> None:
    organization, _, member = create_communications_context(client, identity_headers)
    other_organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={"name": "Other Comms Club", "organization_type": "club"},
    ).json()
    other_member = client.post(
        f"/api/v1/organizations/{other_organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "other-comms-athlete@example.com",
            "display_name": "Other Comms Athlete",
            "role": "athlete",
        },
    ).json()

    preference_response = client.put(
        "/api/v1/communications/preferences",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "person_id": member["subject_id"],
            "frequency": "daily_digest",
            "channel_preference": "email",
            "language": "en",
            "quiet_hours_start": "21:00",
            "quiet_hours_end": "06:00",
            "emergency_override": True,
        },
    )

    assert preference_response.status_code == 200
    preference = preference_response.json()
    assert preference["frequency"] == "daily_digest"
    assert preference["quiet_hours_start"] == "21:00"

    response = client.post(
        "/api/v1/communications/messages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "message_type": "announcement",
            "channel": "email",
            "scope_type": "organization",
            "scope_id": organization["id"],
            "recipient_person_ids": [other_member["subject_id"]],
            "subject": "Cross org message",
            "body": "This should not be allowed.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


def test_quiet_hours_override_requires_urgent(client, identity_headers) -> None:
    organization, team, _ = create_communications_context(client, identity_headers)

    response = client.post(
        "/api/v1/communications/messages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "message_type": "announcement",
            "channel": "email",
            "scope_type": "team",
            "scope_id": team["id"],
            "subject": "Non-urgent override",
            "body": "Quiet hour override is only for urgent messages.",
            "quiet_hours_override": True,
        },
    )

    assert response.status_code == 422


def test_scheduled_urgent_message_escalation_suppresses_repeats(client, identity_headers) -> None:
    organization, team, _member = create_communications_context(client, identity_headers)
    message_response = client.post(
        "/api/v1/communications/messages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "message_type": "alert",
            "channel": "email",
            "scope_type": "team",
            "scope_id": team["id"],
            "subject": "Lightning delay",
            "body": "Lightning has delayed the match. Confirm pickup arrangements.",
            "urgent": True,
            "quiet_hours_override": True,
        },
    )
    assert message_response.status_code == 201
    message = message_response.json()

    run_response = client.post(
        "/api/v1/communications/escalations/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "in_app",
            "escalation_level": 2,
            "failed_only": False,
            "unresolved_after_minutes": 0,
            "repeat_after_minutes": 60,
            "limit": 10,
        },
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["eligible_count"] == 1
    assert run["escalated_count"] == 1
    assert run["skipped_count"] == 0
    assert run["original_message_ids"] == [message["id"]]
    assert len(run["escalation_message_ids"]) == 1
    assert run["runs"][0]["recipient_count"] == 1

    messages = client.get(
        f"/api/v1/communications/messages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    escalation = next(item for item in messages if item["id"] == run["escalation_message_ids"][0])
    assert escalation["escalates_message_id"] == message["id"]
    assert escalation["escalation_level"] == 2
    assert escalation["escalation_triggered_at"] is not None
    assert "Scheduled escalation" in escalation["escalation_reason"]

    repeat_response = client.post(
        "/api/v1/communications/escalations/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "channel": "in_app",
            "escalation_level": 2,
            "unresolved_after_minutes": 0,
            "repeat_after_minutes": 60,
            "limit": 10,
        },
    )
    assert repeat_response.status_code == 200
    repeat = repeat_response.json()
    assert repeat["eligible_count"] == 1
    assert repeat["escalated_count"] == 0
    assert repeat["skipped_count"] == 1
