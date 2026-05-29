import base64
import hashlib
from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.services import developer as developer_service


def create_developer_org(client, identity_headers):
    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "Developer Platform Club",
            "organization_type": "club",
            "primary_sport": "football",
            "country_code": "KE",
        },
        headers=identity_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_public_developer_docs(client) -> None:
    response = client.get("/api/v1/developers/public/docs")
    assert response.status_code == 200
    docs = response.json()
    assert docs["title"] == "AfroLete Developer Platform"
    assert docs["search_query"] is None
    assert docs["search_result_count"] >= len(docs["quickstarts"])
    assert docs["api_base_path"] == "/api/v1/sdk"
    assert docs["auth_header"] == "X-Afrolete-API-Key"
    assert docs["webhook_signature_header"] == "X-Afrolete-Webhook-Signature"
    assert len(docs["quickstarts"]) >= 5
    assert len(docs["sdk_endpoints"]) >= 40
    assert "read:organization" in {scope["scope"] for scope in docs["scopes"]}
    assert "read:agents" in {scope["scope"] for scope in docs["scopes"]}
    assert "write:agents" in {scope["scope"] for scope in docs["scopes"]}
    assert any(event["event_type"] == "training.drill.created" for event in docs["webhook_events"])
    assert any(event["event_type"] == "agents.task.queued" for event in docs["webhook_events"])
    assert any(
        endpoint["method"] == "POST"
        and endpoint["path"] == "/sdk/agents/{agent_id}/tasks"
        and endpoint["typescript_entry_point"] == "client.agents.tasks.queue"
        and endpoint["webhook_events"] == ["agents.task.queued"]
        for endpoint in docs["sdk_endpoints"]
    )
    assert any(
        endpoint["method"] == "GET"
        and endpoint["path"] == "/sdk/training/calendar-artifact"
        and "read:training" in endpoint["required_scopes"]
        for endpoint in docs["sdk_endpoints"]
    )
    assert any(sdk["language"] == "Raw HTTP" and sdk["status"] == "active" for sdk in docs["sdks"])
    raw_http_sdk = next(sdk for sdk in docs["sdks"] if sdk["language"] == "Raw HTTP")
    assert {
        f"{endpoint['method']} {endpoint['path']}"
        for endpoint in docs["sdk_endpoints"]
    } == set(raw_http_sdk["entry_points"])
    assert any(
        "verifyAfroLeteWebhookSignature" in sdk["entry_points"]
        for sdk in docs["sdks"]
        if sdk["language"] == "TypeScript"
    )
    assert any(
        "verify_webhook_signature" in sdk["entry_points"]
        for sdk in docs["sdks"]
        if sdk["language"] == "Python"
    )
    assert any(
        quickstart["title"] == "Exchange an OAuth code"
        and "/developers/oauth/consent" in " ".join(quickstart["steps"])
        for quickstart in docs["quickstarts"]
    )
    assert "operations" in docs["marketplace_categories"]
    assert docs["security_requirements"]


def test_public_developer_docs_search(client) -> None:
    response = client.get("/api/v1/developers/public/docs", params={"q": "billing"})
    assert response.status_code == 200
    docs = response.json()

    assert docs["search_query"] == "billing"
    assert docs["search_result_count"] > 0
    assert docs["quickstarts"]
    assert all("billing" in str(item).lower() for item in docs["quickstarts"])
    assert {scope["scope"] for scope in docs["scopes"]} >= {"read:billing", "write:billing"}
    assert all("billing" in str(event).lower() for event in docs["webhook_events"])
    assert docs["sdk_endpoints"]
    assert all("billing" in str(endpoint).lower() for endpoint in docs["sdk_endpoints"])
    assert docs["marketplace_categories"] == ["billing"]


def test_developer_application_webhook_marketplace_workflow(client, identity_headers) -> None:
    organization = create_developer_org(client, identity_headers)

    application_response = client.post(
        "/api/v1/developers/applications",
        json={
            "organization_id": organization["id"],
            "name": "Matchday Sync",
            "app_type": "server_to_server",
            "redirect_uris": ["https://sync.example/callback"],
            "scopes": [
                "read:organization",
                "write:events",
                "write:people",
                "read:attendance",
                "write:attendance",
                "read:agents",
                "write:agents",
                "read:communications",
                "write:communications",
                "read:billing",
                "write:billing",
                "write:training",
            ],
            "contact_email": "integrations@example.com",
        },
        headers=identity_headers,
    )
    assert application_response.status_code == 201
    provisioned_application = application_response.json()
    application = provisioned_application["application"]
    original_secret = provisioned_application["client_secret"]
    assert application["client_id"].startswith("afrolete_")
    assert original_secret
    assert application["scopes"] == [
        "read:organization",
        "write:events",
        "write:people",
        "read:attendance",
        "write:attendance",
        "read:agents",
        "write:agents",
        "read:communications",
        "write:communications",
        "read:billing",
        "write:billing",
        "write:training",
    ]

    application_list_response = client.get(
        f"/api/v1/developers/applications?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert application_list_response.status_code == 200
    listed_application = application_list_response.json()[0]
    assert listed_application["id"] == application["id"]
    assert "client_secret_hash" not in listed_application

    rotation_response = client.post(
        f"/api/v1/developers/applications/{application['id']}/rotate-secret",
        headers=identity_headers,
    )
    assert rotation_response.status_code == 200
    rotated_secret = rotation_response.json()["client_secret"]
    assert rotated_secret
    assert rotated_secret != original_secret

    api_key_response = client.post(
        "/api/v1/developers/api-keys",
        json={
            "organization_id": organization["id"],
            "application_id": application["id"],
            "name": "Sandbox SDK Key",
            "scopes": [
                "read:organization",
                "write:events",
                "write:people",
                "read:attendance",
                "write:attendance",
                "read:agents",
                "write:agents",
                "read:communications",
                "write:communications",
                "read:billing",
                "write:billing",
                "write:training",
            ],
            "environment": "sandbox",
            "rate_limit_per_minute": 120,
        },
        headers=identity_headers,
    )
    assert api_key_response.status_code == 201
    provisioned_api_key = api_key_response.json()
    api_key = provisioned_api_key["api_key"]
    raw_key = provisioned_api_key["key"]
    assert raw_key.startswith("al_developerpla_sandbox_")
    assert api_key["key_prefix"] == raw_key.split(".", 1)[0]
    assert api_key["scopes"] == [
        "read:organization",
        "write:events",
        "write:people",
        "read:attendance",
        "write:attendance",
        "read:agents",
        "write:agents",
        "read:communications",
        "write:communications",
        "read:billing",
        "write:billing",
        "write:training",
    ]
    assert "key_hash" not in api_key

    inspect_response = client.get(
        "/api/v1/developers/auth/inspect",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert inspect_response.status_code == 200
    inspection = inspect_response.json()
    assert inspection["valid"] is True
    assert inspection["application_id"] == application["id"]
    assert inspection["usage_count"] == 1

    api_key_list_response = client.get(
        f"/api/v1/developers/api-keys?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert api_key_list_response.status_code == 200
    listed_api_key = api_key_list_response.json()[0]
    assert listed_api_key["usage_count"] == 1
    assert "key_hash" not in listed_api_key

    oauth_authorization_response = client.post(
        "/api/v1/developers/oauth/authorizations",
        json={
            "organization_id": organization["id"],
            "client_id": application["client_id"],
            "redirect_uri": "https://sync.example/callback",
            "scopes": ["read:organization", "write:training"],
            "state": "tenant-console-test",
        },
        headers=identity_headers,
    )
    assert oauth_authorization_response.status_code == 201
    oauth_authorization = oauth_authorization_response.json()
    authorization_code = oauth_authorization["authorization_code"]
    assert authorization_code
    assert oauth_authorization["status"] == "granted"
    assert oauth_authorization["granted_scopes"] == ["read:organization", "write:training"]
    assert "tenant-console-test" in oauth_authorization["redirect_url"]

    oauth_list_response = client.get(
        f"/api/v1/developers/oauth/authorizations?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert oauth_list_response.status_code == 200
    assert oauth_list_response.json()[0]["authorization_code"] is None

    oauth_token_response = client.post(
        "/api/v1/developers/oauth/token",
        json={
            "client_id": application["client_id"],
            "client_secret": rotated_secret,
            "code": authorization_code,
            "redirect_uri": "https://sync.example/callback",
        },
    )
    assert oauth_token_response.status_code == 200
    oauth_token = oauth_token_response.json()
    assert oauth_token["token_type"] == "AfroleteApiKey"
    assert oauth_token["auth_header"] == "X-Afrolete-API-Key"
    assert oauth_token["api_key"]["environment"] == "oauth"
    assert oauth_token["scopes"] == ["read:organization", "write:training"]
    assert oauth_token["refresh_token"]
    assert oauth_token["refresh_expires_in"] == 90 * 24 * 60 * 60

    refreshed_oauth_response = client.post(
        "/api/v1/developers/oauth/refresh",
        json={
            "client_id": application["client_id"],
            "refresh_token": oauth_token["refresh_token"],
        },
    )
    assert refreshed_oauth_response.status_code == 200
    refreshed_oauth = refreshed_oauth_response.json()
    assert refreshed_oauth["access_token"] != oauth_token["access_token"]
    assert refreshed_oauth["refresh_token"] != oauth_token["refresh_token"]
    assert refreshed_oauth["scopes"] == ["read:organization", "write:training"]

    old_oauth_inspect_response = client.get(
        "/api/v1/developers/auth/inspect",
        headers={"X-Afrolete-API-Key": oauth_token["access_token"]},
    )
    assert old_oauth_inspect_response.status_code == 401

    new_oauth_inspect_response = client.get(
        "/api/v1/developers/auth/inspect",
        headers={"X-Afrolete-API-Key": refreshed_oauth["access_token"]},
    )
    assert new_oauth_inspect_response.status_code == 200

    reused_refresh_response = client.post(
        "/api/v1/developers/oauth/refresh",
        json={
            "client_id": application["client_id"],
            "refresh_token": oauth_token["refresh_token"],
        },
    )
    assert reused_refresh_response.status_code == 401
    duplicate_reused_refresh_response = client.post(
        "/api/v1/developers/oauth/refresh",
        json={
            "client_id": application["client_id"],
            "refresh_token": oauth_token["refresh_token"],
        },
    )
    assert duplicate_reused_refresh_response.status_code == 401
    compromised_oauth_inspect_response = client.get(
        "/api/v1/developers/auth/inspect",
        headers={"X-Afrolete-API-Key": refreshed_oauth["access_token"]},
    )
    assert compromised_oauth_inspect_response.status_code == 401

    compromised_keys_response = client.get(
        f"/api/v1/developers/api-keys?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert compromised_keys_response.status_code == 200
    compromised_oauth_keys = [
        key for key in compromised_keys_response.json() if key["environment"] == "oauth" and key["refresh_reused_at"]
    ]
    assert len(compromised_oauth_keys) == 1
    assert "security incident" in compromised_oauth_keys[0]["notes"]

    incidents_response = client.get(
        f"/api/v1/safeguarding/incidents?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert incidents_response.status_code == 200
    replay_incidents = [
        incident
        for incident in incidents_response.json()
        if incident["title"] == "OAuth refresh-token replay detected"
    ]
    assert len(replay_incidents) == 1
    replay_incident = replay_incidents[0]
    assert replay_incident["incident_type"] == "security"
    assert replay_incident["severity"] == "high"
    assert replay_incident["status"] == "open"
    assert "Refresh-token family ID" in replay_incident["description"]
    assert "Revoked active OAuth tokens" in replay_incident["immediate_action"]

    reused_oauth_token_response = client.post(
        "/api/v1/developers/oauth/token",
        json={
            "client_id": application["client_id"],
            "client_secret": rotated_secret,
            "code": authorization_code,
            "redirect_uri": "https://sync.example/callback",
        },
    )
    assert reused_oauth_token_response.status_code == 422

    pkce_verifier = "public-client-verifier-for-afrolete-oauth"
    pkce_challenge = base64.urlsafe_b64encode(hashlib.sha256(pkce_verifier.encode()).digest()).decode().rstrip("=")
    pkce_authorization_response = client.post(
        "/api/v1/developers/oauth/authorizations",
        json={
            "organization_id": organization["id"],
            "client_id": application["client_id"],
            "redirect_uri": "https://sync.example/callback",
            "scopes": ["read:organization"],
            "state": "pkce-public-client",
            "code_challenge": pkce_challenge,
            "code_challenge_method": "S256",
        },
        headers=identity_headers,
    )
    assert pkce_authorization_response.status_code == 201
    pkce_authorization = pkce_authorization_response.json()
    assert pkce_authorization["public_client"] is True
    assert pkce_authorization["code_challenge_method"] == "S256"

    missing_verifier_response = client.post(
        "/api/v1/developers/oauth/token",
        json={
            "client_id": application["client_id"],
            "code": pkce_authorization["authorization_code"],
            "redirect_uri": "https://sync.example/callback",
        },
    )
    assert missing_verifier_response.status_code == 401

    pkce_token_response = client.post(
        "/api/v1/developers/oauth/token",
        json={
            "client_id": application["client_id"],
            "code": pkce_authorization["authorization_code"],
            "redirect_uri": "https://sync.example/callback",
            "code_verifier": pkce_verifier,
        },
    )
    assert pkce_token_response.status_code == 200
    assert pkce_token_response.json()["api_key"]["environment"] == "oauth"
    assert pkce_token_response.json()["scopes"] == ["read:organization"]
    assert pkce_token_response.json()["refresh_token"]

    sdk_me_response = client.get(
        "/api/v1/sdk/me",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_me_response.status_code == 200
    assert sdk_me_response.json()["organization_id"] == organization["id"]

    sdk_organization_response = client.get(
        f"/api/v1/sdk/organization?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_organization_response.status_code == 200
    assert sdk_organization_response.json()["slug"] == organization["slug"]

    sdk_webhook_response = client.post(
        "/api/v1/developers/webhook-subscriptions",
        json={
            "organization_id": organization["id"],
            "application_id": application["id"],
            "name": "SDK Training Events",
            "target_url": "https://sync.example/webhooks/training",
            "event_types": ["training.drill.created"],
            "delivery_mode": "record_only",
        },
        headers=identity_headers,
    )
    assert sdk_webhook_response.status_code == 201
    sdk_webhook = sdk_webhook_response.json()["subscription"]

    catalog_response = client.get(
        f"/api/v1/developers/catalog?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert catalog["api_base_path"] == "/api/v1/sdk"
    assert catalog["auth_header"] == "X-Afrolete-API-Key"
    assert "training.drill.created" in catalog["configured_event_types"]
    assert "read:organization" in {scope["scope"] for scope in catalog["scopes"]}
    assert "read:events" in {scope["scope"] for scope in catalog["scopes"]}
    training_event = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "training.drill.created"
    )
    assert training_event["emission_status"] == "active"
    assert "write:training" in training_event["recommended_scopes"]
    training_plan_event = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "training.plan.created"
    )
    assert training_plan_event["emission_status"] == "active"
    assert "write:training" in training_plan_event["recommended_scopes"]
    training_session_event = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "training.session.created"
    )
    assert training_session_event["emission_status"] == "active"
    assert "write:training" in training_session_event["recommended_scopes"]
    training_feedback_event = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "training.feedback.recorded"
    )
    assert training_feedback_event["emission_status"] == "active"
    assert "write:training" in training_feedback_event["recommended_scopes"]
    sdk_event_created = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "events.created"
    )
    assert sdk_event_created["emission_status"] == "active"
    assert "write:events" in sdk_event_created["recommended_scopes"]
    sdk_agent_queued = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "agents.task.queued"
    )
    assert sdk_agent_queued["emission_status"] == "active"
    assert "write:agents" in sdk_agent_queued["recommended_scopes"]
    sdk_message_created = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "communications.message.created"
    )
    assert sdk_message_created["emission_status"] == "active"
    assert "write:communications" in sdk_message_created["recommended_scopes"]
    sdk_message_dispatched = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "communications.message.dispatched"
    )
    assert sdk_message_dispatched["emission_status"] == "active"
    assert "write:communications" in sdk_message_dispatched["recommended_scopes"]
    sdk_billing_usage_recorded = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "billing.usage.recorded"
    )
    assert sdk_billing_usage_recorded["emission_status"] == "active"
    assert "write:billing" in sdk_billing_usage_recorded["recommended_scopes"]
    assert any(
        "client.agents.tasks.queue" in sdk["entry_points"]
        for sdk in catalog["sdks"]
        if sdk["language"] == "TypeScript"
    )
    assert any(
        "client.communications.messages.dispatch" in sdk["entry_points"]
        for sdk in catalog["sdks"]
        if sdk["language"] == "TypeScript"
    )
    assert any(
        "client.billing.usage.record" in sdk["entry_points"]
        for sdk in catalog["sdks"]
        if sdk["language"] == "TypeScript"
    )
    assert any(
        "client.training.sessions.feedback.record" in sdk["entry_points"]
        for sdk in catalog["sdks"]
        if sdk["language"] == "Python"
    )
    assert any(
        "POST /sdk/communications/messages/{message_id}/dispatch" in sdk["entry_points"]
        for sdk in catalog["sdks"]
        if sdk["language"] == "Raw HTTP"
    )
    assert any(
        "POST /sdk/billing/usage" in sdk["entry_points"]
        for sdk in catalog["sdks"]
        if sdk["language"] == "Raw HTTP"
    )
    assert any(
        "GET /sdk/training/calendar-artifact" in sdk["entry_points"]
        for sdk in catalog["sdks"]
        if sdk["language"] == "Raw HTTP"
    )
    assert any(sdk["language"] == "Raw HTTP" and sdk["status"] == "active" for sdk in catalog["sdks"])

    agent_response = client.post(
        "/api/v1/agents",
        json={
            "organization_id": organization["id"],
            "name": "SDK Coaching Agent",
            "kind": "coaching",
            "purpose": "Review imported partner data and prepare coach-facing recommendations.",
            "model_policy": "sdk-agent-policy-v1",
        },
        headers=identity_headers,
    )
    assert agent_response.status_code == 201
    agent = agent_response.json()
    policy_response = client.post(
        "/api/v1/agents/governance-policy-rules",
        json={
            "organization_id": organization["id"],
            "rule_code": "sdk_training_plan_review",
            "title": "SDK training plan review gate",
            "agent_kind": "coaching",
            "task_type_contains": "training_plan",
            "decision": "require_approval",
            "required_approval_count": 2,
            "risk_level": "high",
            "rationale": "Partner-queued coaching changes require human review before reaching athletes.",
        },
        headers=identity_headers,
    )
    assert policy_response.status_code == 201
    team_response = client.post(
        "/api/v1/teams",
        json={
            "organization_id": organization["id"],
            "name": "SDK Training Team",
            "sport": "football",
            "sport_format": "team",
        },
        headers=identity_headers,
    )
    assert team_response.status_code == 201
    team = team_response.json()

    billing_plan_response = client.post(
        "/api/v1/billing/plans",
        json={
            "code": "sdk-growth",
            "name": "SDK Growth",
            "description": "Plan used by trusted SDK billing integrations.",
            "base_price": "199.00",
            "currency": "USD",
            "billing_cycle": "monthly",
            "included_athletes": 50,
            "included_teams": 4,
            "included_agent_tasks": 25,
            "included_storage_gb": 100,
            "per_athlete_price": "2.00",
            "per_agent_task_price": "0.50",
            "features": "sdk,billing,agents",
        },
        headers=identity_headers,
    )
    assert billing_plan_response.status_code == 201
    billing_plan = billing_plan_response.json()

    billing_subscription_response = client.post(
        "/api/v1/billing/subscriptions",
        json={
            "organization_id": organization["id"],
            "billing_plan_id": billing_plan["id"],
            "billing_cycle": "monthly",
            "current_period_start": "2026-06-01",
            "current_period_end": "2026-06-30",
            "next_billing_on": "2026-07-01",
            "seats_purchased": 50,
            "negotiated_price": "149.00",
            "discount_code": "SDK",
            "notes": "Provisioned for SDK billing workflow coverage.",
        },
        headers=identity_headers,
    )
    assert billing_subscription_response.status_code == 201
    billing_subscription = billing_subscription_response.json()

    usage_meter_response = client.post(
        "/api/v1/billing/meters",
        json={
            "code": "sdk-agent-task",
            "name": "SDK Agent Tasks",
            "unit": "agent_task",
            "included_quantity": 10,
            "overage_price": "0.2500",
            "aggregation": "sum",
        },
        headers=identity_headers,
    )
    assert usage_meter_response.status_code == 201
    usage_meter = usage_meter_response.json()

    entitlement_response = client.post(
        "/api/v1/billing/entitlements",
        json={
            "organization_id": organization["id"],
            "subscription_id": billing_subscription["id"],
            "feature_key": "agent_tasks",
            "limit_value": 25,
            "used_value": 0,
        },
        headers=identity_headers,
    )
    assert entitlement_response.status_code == 201
    billing_entitlement = entitlement_response.json()

    invoice_response = client.post(
        "/api/v1/billing/invoices",
        json={
            "organization_id": organization["id"],
            "subscription_id": billing_subscription["id"],
            "invoice_number": "SDK-2026-001",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "tax_amount": "0.00",
            "discount_amount": "0.00",
            "due_on": "2026-07-14",
        },
        headers=identity_headers,
    )
    assert invoice_response.status_code == 201
    billing_invoice = invoice_response.json()

    event_start = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    sdk_event_response = client.post(
        "/api/v1/sdk/events",
        json={
            "organization_id": organization["id"],
            "event_type": "match",
            "title": "SDK Cup Final",
            "starts_at": event_start,
            "timezone": "Africa/Nairobi",
            "venue_name": "AfroLete Stadium",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_event_response.status_code == 201
    assert sdk_event_response.json()["title"] == "SDK Cup Final"

    sdk_events_response = client.get(
        f"/api/v1/sdk/events?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_events_response.status_code == 200
    assert any(event["title"] == "SDK Cup Final" for event in sdk_events_response.json())
    sdk_created_event_id = sdk_event_response.json()["id"]

    sdk_person_response = client.post(
        "/api/v1/sdk/people",
        json={
            "organization_id": organization["id"],
            "display_name": "SDK Attendance Player",
            "primary_email": "sdk-attendance-player@example.com",
            "membership_role": "athlete",
            "membership_title": "External roster import",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_person_response.status_code == 201
    sdk_person = sdk_person_response.json()

    sdk_template_response = client.post(
        "/api/v1/sdk/communications/templates",
        json={
            "organization_id": organization["id"],
            "name": "SDK reminder template",
            "message_type": "reminder",
            "channel": "email",
            "subject_template": "Reminder for {member.name}",
            "body_template": "Please confirm the latest schedule update.",
            "variables": "member.name",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_template_response.status_code == 201
    sdk_template = sdk_template_response.json()
    assert sdk_template["name"] == "SDK reminder template"

    sdk_templates_response = client.get(
        f"/api/v1/sdk/communications/templates?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_templates_response.status_code == 200
    assert sdk_templates_response.json()[0]["id"] == sdk_template["id"]

    sdk_message_response = client.post(
        "/api/v1/sdk/communications/messages",
        json={
            "organization_id": organization["id"],
            "template_id": sdk_template["id"],
            "message_type": "reminder",
            "channel": "email",
            "scope_type": "person",
            "scope_id": sdk_person["id"],
            "subject": "SDK schedule reminder",
            "body": "Your schedule was updated by a trusted integration.",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_message_response.status_code == 201
    sdk_message = sdk_message_response.json()
    assert sdk_message["created_by_person_id"] is None
    assert sdk_message["recipient_count"] == 1

    sdk_messages_response = client.get(
        f"/api/v1/sdk/communications/messages?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_messages_response.status_code == 200
    assert sdk_messages_response.json()[0]["id"] == sdk_message["id"]

    sdk_recipients_response = client.get(
        f"/api/v1/sdk/communications/messages/{sdk_message['id']}/recipients?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_recipients_response.status_code == 200
    sdk_recipient = sdk_recipients_response.json()[0]
    assert sdk_recipient["person_id"] == sdk_person["id"]
    assert sdk_recipient["destination"] == "sdk-attendance-player@example.com"

    sdk_dispatch_response = client.post(
        f"/api/v1/sdk/communications/messages/{sdk_message['id']}/dispatch?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_dispatch_response.status_code == 200
    assert sdk_dispatch_response.json()["attempted"] == 1
    assert sdk_dispatch_response.json()["queued"] == 1

    sdk_billing_plans_response = client.get(
        "/api/v1/sdk/billing/plans",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_billing_plans_response.status_code == 200
    assert any(plan["id"] == billing_plan["id"] for plan in sdk_billing_plans_response.json())

    sdk_billing_subscriptions_response = client.get(
        f"/api/v1/sdk/billing/subscriptions?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_billing_subscriptions_response.status_code == 200
    assert sdk_billing_subscriptions_response.json()[0]["id"] == billing_subscription["id"]

    sdk_billing_meters_response = client.get(
        "/api/v1/sdk/billing/meters",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_billing_meters_response.status_code == 200
    assert any(meter["id"] == usage_meter["id"] for meter in sdk_billing_meters_response.json())

    sdk_usage_record_response = client.post(
        "/api/v1/sdk/billing/usage",
        json={
            "organization_id": organization["id"],
            "subscription_id": billing_subscription["id"],
            "usage_meter_id": usage_meter["id"],
            "quantity": 14,
            "source": "partner_billing_sync",
            "external_reference": "usage-sdk-001",
            "notes": "Imported from partner metering.",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_usage_record_response.status_code == 201
    sdk_usage_record = sdk_usage_record_response.json()
    assert sdk_usage_record["quantity"] == 14
    assert sdk_usage_record["source"] == "partner_billing_sync"

    sdk_usage_records_response = client.get(
        f"/api/v1/sdk/billing/usage?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_usage_records_response.status_code == 200
    assert sdk_usage_records_response.json()[0]["id"] == sdk_usage_record["id"]

    sdk_billing_invoices_response = client.get(
        f"/api/v1/sdk/billing/invoices?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_billing_invoices_response.status_code == 200
    assert sdk_billing_invoices_response.json()[0]["invoice_number"] == billing_invoice["invoice_number"]

    sdk_billing_entitlements_response = client.get(
        f"/api/v1/sdk/billing/entitlements?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_billing_entitlements_response.status_code == 200
    assert sdk_billing_entitlements_response.json()[0]["id"] == billing_entitlement["id"]

    sdk_billing_summary_response = client.get(
        f"/api/v1/sdk/billing/summary?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_billing_summary_response.status_code == 200
    sdk_billing_summary = sdk_billing_summary_response.json()
    assert sdk_billing_summary["usage_records"] >= 1
    assert sdk_billing_summary["open_invoices"] >= 1
    assert sdk_billing_summary["entitlements"] >= 1

    sdk_attendance_response = client.post(
        f"/api/v1/sdk/events/{sdk_created_event_id}/attendance?organization_id={organization['id']}",
        json={
            "person_id": sdk_person["id"],
            "status": "invited",
            "note": "Imported by external attendance kiosk.",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_attendance_response.status_code == 201
    attendance = sdk_attendance_response.json()
    assert attendance["person_id"] == sdk_person["id"]
    assert attendance["status"] == "invited"
    assert attendance["recorded_by_person_id"] is None

    sdk_attendance_list_response = client.get(
        f"/api/v1/sdk/events/{sdk_created_event_id}/attendance?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_attendance_list_response.status_code == 200
    assert sdk_attendance_list_response.json()[0]["note"] == "Imported by external attendance kiosk."

    sdk_agents_response = client.get(
        f"/api/v1/sdk/agents?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_agents_response.status_code == 200
    assert sdk_agents_response.json()[0]["name"] == "SDK Coaching Agent"

    sdk_agent_task_response = client.post(
        f"/api/v1/sdk/agents/{agent['id']}/tasks",
        json={
            "organization_id": organization["id"],
            "task_type": "training_plan_review",
            "title": "Review SDK imported training load",
            "input_ref": f"person:{sdk_person['id']}",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_agent_task_response.status_code == 201
    sdk_agent_task = sdk_agent_task_response.json()
    assert sdk_agent_task["requested_by_person_id"] is None
    assert sdk_agent_task["governance_policy_code"] == "sdk_training_plan_review"
    assert sdk_agent_task["approval_required_count"] == 2
    assert sdk_agent_task["approval_pending_count"] == 2

    sdk_agent_tasks_response = client.get(
        f"/api/v1/sdk/agents/tasks?organization_id={organization['id']}&agent_id={agent['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_agent_tasks_response.status_code == 200
    assert sdk_agent_tasks_response.json()[0]["id"] == sdk_agent_task["id"]

    sdk_drill_response = client.post(
        "/api/v1/sdk/training/drills",
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "name": "Advanced Passing Circuit",
            "focus_area": "Passing",
            "category": "technical",
            "equipment": "cones, balls, goals",
            "description": "Players circulate through a one-touch passing square with timed progressions.",
            "coaching_points": "Open body shape, scan before receiving, firm pass weight.",
            "default_duration_minutes": 20,
            "default_intensity": 6,
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_drill_response.status_code == 201
    assert sdk_drill_response.json()["name"] == "Advanced Passing Circuit"

    sdk_drills_response = client.get(
        f"/api/v1/sdk/training/drills?organization_id={organization['id']}&sport=football",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_drills_response.status_code == 200
    assert sdk_drills_response.json()[0]["name"] == "Advanced Passing Circuit"

    sdk_plan_response = client.post(
        "/api/v1/sdk/training/plans",
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "title": "SDK imported training block",
            "focus_area": "Passing and decision speed",
            "period_start": "2026-06-01",
            "period_end": "2026-06-14",
            "source_summary": "Imported from an external coaching workspace.",
            "load_guidance": "Keep the first week moderate before matchday.",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_plan_response.status_code == 201
    sdk_plan = sdk_plan_response.json()
    assert sdk_plan["created_by_person_id"] is None
    assert sdk_plan["team_id"] == team["id"]

    sdk_plan_item_response = client.post(
        f"/api/v1/sdk/training/plans/{sdk_plan['id']}/items?organization_id={organization['id']}",
        json={
            "drill_id": sdk_drill_response.json()["id"],
            "sequence": 1,
            "day_label": "Week 1 Day 1",
            "title": "Passing circuit progression",
            "focus_area": "Passing",
            "duration_minutes": 20,
            "intensity": 6,
            "notes": "Imported from partner coach planning software.",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_plan_item_response.status_code == 201
    assert sdk_plan_item_response.json()["plan_id"] == sdk_plan["id"]

    sdk_plan_items_response = client.get(
        f"/api/v1/sdk/training/plans/{sdk_plan['id']}/items?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_plan_items_response.status_code == 200
    assert sdk_plan_items_response.json()[0]["title"] == "Passing circuit progression"

    sdk_session_response = client.post(
        "/api/v1/sdk/training/sessions",
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "plan_id": sdk_plan["id"],
            "title": "SDK partner session",
            "scheduled_for": "2026-06-03T15:00:00Z",
            "duration_minutes": 75,
            "rpe_target": 6,
            "objectives": "Translate partner plan into an AfroLete-managed session.",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_session_response.status_code == 201
    sdk_session = sdk_session_response.json()
    assert sdk_session["load_score"] == 450.0

    sdk_sessions_response = client.get(
        f"/api/v1/sdk/training/sessions?organization_id={organization['id']}&team_id={team['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_sessions_response.status_code == 200
    assert sdk_sessions_response.json()[0]["id"] == sdk_session["id"]

    sdk_availability_response = client.post(
        "/api/v1/sdk/training/availability",
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "starts_at": "2026-06-01T06:00:00Z",
            "days": 3,
            "duration_minutes": 75,
            "earliest_hour": 8,
            "latest_hour": 18,
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_availability_response.status_code == 200
    assert sdk_availability_response.json()["slots"]

    sdk_calendar_response = client.get(
        (
            f"/api/v1/sdk/training/calendar-artifact?organization_id={organization['id']}"
            f"&team_id={team['id']}&starts_at=2026-06-01T00:00:00Z&ends_at=2026-06-30T00:00:00Z"
        ),
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_calendar_response.status_code == 200
    assert sdk_calendar_response.json()["session_count"] == 1
    assert "SUMMARY:SDK partner session" in sdk_calendar_response.json()["content"]

    sdk_feedback_response = client.post(
        f"/api/v1/sdk/training/sessions/{sdk_session['id']}/feedback?organization_id={organization['id']}",
        json={
            "readiness_score": 72,
            "soreness_score": 2,
            "sleep_quality": 8,
            "mood_score": 7,
            "actual_rpe": 6,
            "actual_duration_minutes": 74,
            "completed": True,
            "feedback": "Partner app synced post-session feedback.",
        },
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_feedback_response.status_code == 201
    sdk_feedback = sdk_feedback_response.json()
    assert sdk_feedback["recorded_by_person_id"] is None
    assert sdk_feedback["completed"] is True

    sdk_feedback_list_response = client.get(
        f"/api/v1/sdk/training/sessions/{sdk_session['id']}/feedback?organization_id={organization['id']}",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert sdk_feedback_list_response.status_code == 200
    assert sdk_feedback_list_response.json()[0]["id"] == sdk_feedback["id"]

    webhook_deliveries_response = client.get(
        f"/api/v1/developers/webhook-deliveries?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert webhook_deliveries_response.status_code == 200
    deliveries = webhook_deliveries_response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["subscription_id"] == sdk_webhook["id"]
    assert deliveries[0]["event_type"] == "training.drill.created"
    assert deliveries[0]["status"] == "recorded"
    assert deliveries[0]["attempt_count"] == 1
    assert deliveries[0]["last_attempted_at"]
    assert deliveries[0]["next_attempt_at"] is None
    replay_delivery_response = client.post(
        f"/api/v1/developers/webhook-deliveries/{deliveries[0]['id']}/replay",
        headers=identity_headers,
    )
    assert replay_delivery_response.status_code == 200
    replayed_delivery = replay_delivery_response.json()
    assert replayed_delivery["status"] == "recorded"
    assert replayed_delivery["attempt_count"] == 2

    retry_run_response = client.post(
        (
            f"/api/v1/developers/webhook-deliveries/retry-due?organization_id={organization['id']}"
            "&include_recorded=true&max_attempts=5"
        ),
        headers=identity_headers,
    )
    assert retry_run_response.status_code == 200
    retry_run = retry_run_response.json()
    assert retry_run["eligible_count"] == 1
    assert retry_run["replayed_count"] == 1
    assert retry_run["failed_count"] == 0
    assert retry_run["statuses"]["recorded"] == 1
    assert retry_run["max_attempts"] == 5
    assert retry_run["include_recorded"] is True

    retried_deliveries_response = client.get(
        f"/api/v1/developers/webhook-deliveries?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert retried_deliveries_response.status_code == 200
    assert retried_deliveries_response.json()[0]["attempt_count"] == 3

    read_only_key_response = client.post(
        "/api/v1/developers/api-keys",
        json={
            "organization_id": organization["id"],
            "application_id": application["id"],
            "name": "Read Only SDK Key",
            "scopes": ["read:organization"],
            "environment": "sandbox",
        },
        headers=identity_headers,
    )
    assert read_only_key_response.status_code == 201
    read_only_raw_key = read_only_key_response.json()["key"]
    denied_sdk_drill_response = client.post(
        "/api/v1/sdk/training/drills",
        json={
            "organization_id": organization["id"],
            "sport": "football",
            "name": "Denied Drill",
            "focus_area": "Passing",
            "category": "technical",
            "description": "This drill should be denied by API-key scope enforcement.",
        },
        headers={"X-Afrolete-API-Key": read_only_raw_key},
    )
    assert denied_sdk_drill_response.status_code == 403

    limited_key_response = client.post(
        "/api/v1/developers/api-keys",
        json={
            "organization_id": organization["id"],
            "application_id": application["id"],
            "name": "Limited SDK Key",
            "scopes": ["read:organization"],
            "environment": "sandbox",
            "rate_limit_per_minute": 1,
        },
        headers=identity_headers,
    )
    assert limited_key_response.status_code == 201
    limited_raw_key = limited_key_response.json()["key"]
    first_limited_response = client.get(
        "/api/v1/sdk/me",
        headers={"X-Afrolete-API-Key": limited_raw_key},
    )
    assert first_limited_response.status_code == 200
    assert first_limited_response.json()["window_request_count"] == 1
    second_limited_response = client.get(
        "/api/v1/sdk/me",
        headers={"X-Afrolete-API-Key": limited_raw_key},
    )
    assert second_limited_response.status_code == 429

    webhook_response = client.post(
        "/api/v1/developers/webhook-subscriptions",
        json={
            "organization_id": organization["id"],
            "application_id": application["id"],
            "name": "Event Updates",
            "target_url": "https://sync.example/webhooks/afrolete",
            "event_types": ["events.created", "events.updated"],
            "delivery_mode": "webhook",
        },
        headers=identity_headers,
    )
    assert webhook_response.status_code == 201
    provisioned_webhook = webhook_response.json()
    webhook = provisioned_webhook["subscription"]
    assert provisioned_webhook["signing_secret"]
    assert webhook["event_types"] == ["events.created", "events.updated"]

    paused_webhook_response = client.patch(
        f"/api/v1/developers/webhook-subscriptions/{webhook['id']}",
        json={"status": "paused", "delivery_mode": "record_only"},
        headers=identity_headers,
    )
    assert paused_webhook_response.status_code == 200
    assert paused_webhook_response.json()["status"] == "paused"
    assert paused_webhook_response.json()["delivery_mode"] == "record_only"

    listing_response = client.post(
        "/api/v1/developers/marketplace-listings",
        json={
            "organization_id": organization["id"],
            "application_id": application["id"],
            "name": "Matchday Sync Connector",
            "category": "operations",
            "summary": "Synchronizes fixtures, attendance, and matchday logistics.",
            "install_url": "https://sync.example/install",
            "support_url": "https://sync.example/support",
        },
        headers=identity_headers,
    )
    assert listing_response.status_code == 201
    listing = listing_response.json()
    assert listing["review_status"] == "draft"

    review_response = client.patch(
        f"/api/v1/developers/marketplace-listings/{listing['id']}/review",
        json={"review_status": "approved", "visibility": "public"},
        headers=identity_headers,
    )
    assert review_response.status_code == 200
    assert review_response.json()["review_status"] == "approved"
    assert review_response.json()["visibility"] == "public"

    install_response = client.post(
        f"/api/v1/developers/marketplace-listings/{listing['id']}/install",
        headers=identity_headers,
    )
    assert install_response.status_code == 200
    assert install_response.json()["install_count"] == 1

    summary_response = client.get(
        f"/api/v1/developers/summary?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["application_count"] == 1
    assert summary["api_key_count"] == 6
    assert summary["active_api_key_count"] == 4
    assert summary["webhook_subscription_count"] == 2
    assert summary["marketplace_listing_count"] == 1
    assert summary["approved_marketplace_listing_count"] == 1
    assert summary["install_count"] == 1

    revoke_response = client.post(
        f"/api/v1/developers/api-keys/{api_key['id']}/revoke",
        headers=identity_headers,
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"

    revoked_inspect_response = client.get(
        "/api/v1/developers/auth/inspect",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert revoked_inspect_response.status_code == 401


def test_developer_api_key_uses_distributed_quota_counter(client, identity_headers, monkeypatch) -> None:
    organization = create_developer_org(client, identity_headers)
    application = client.post(
        "/api/v1/developers/applications",
        json={
            "organization_id": organization["id"],
            "name": "Distributed Quota App",
            "app_type": "server_to_server",
            "redirect_uris": ["https://quota.example/callback"],
            "scopes": ["read:organization"],
            "contact_email": "quota@example.com",
        },
        headers=identity_headers,
    ).json()["application"]
    limited_key_response = client.post(
        "/api/v1/developers/api-keys",
        json={
            "organization_id": organization["id"],
            "application_id": application["id"],
            "name": "Redis Limited SDK Key",
            "scopes": ["read:organization"],
            "environment": "sandbox",
            "rate_limit_per_minute": 1,
        },
        headers=identity_headers,
    )
    raw_key = limited_key_response.json()["key"]
    counts = iter([1, 2])
    observed_key_ids = []

    async def fake_increment(settings, api_key, now):
        observed_key_ids.append(str(api_key.id))
        return next(counts), now.replace(second=0, microsecond=0)

    monkeypatch.setattr(
        developer_service,
        "get_settings",
        lambda: Settings(developer_api_quota_counter_mode="redis"),
    )
    monkeypatch.setattr(developer_service, "increment_developer_quota_redis", fake_increment)

    first_response = client.get(
        "/api/v1/sdk/me",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert first_response.status_code == 200
    assert first_response.json()["quota_counter_mode"] == "redis"
    assert first_response.json()["window_request_count"] == 1
    second_response = client.get(
        "/api/v1/sdk/me",
        headers={"X-Afrolete-API-Key": raw_key},
    )
    assert second_response.status_code == 429
    assert len(observed_key_ids) == 2
