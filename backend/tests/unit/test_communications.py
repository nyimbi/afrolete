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
