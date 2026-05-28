import base64
import hashlib


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
    assert docs["api_base_path"] == "/api/v1/sdk"
    assert docs["auth_header"] == "X-Afrolete-API-Key"
    assert docs["webhook_signature_header"] == "X-Afrolete-Webhook-Signature"
    assert len(docs["quickstarts"]) >= 4
    assert "read:organization" in {scope["scope"] for scope in docs["scopes"]}
    assert any(event["event_type"] == "training.drill.created" for event in docs["webhook_events"])
    assert any(sdk["language"] == "Raw HTTP" and sdk["status"] == "active" for sdk in docs["sdks"])
    assert "operations" in docs["marketplace_categories"]
    assert docs["security_requirements"]


def test_developer_application_webhook_marketplace_workflow(client, identity_headers) -> None:
    organization = create_developer_org(client, identity_headers)

    application_response = client.post(
        "/api/v1/developers/applications",
        json={
            "organization_id": organization["id"],
            "name": "Matchday Sync",
            "app_type": "server_to_server",
            "redirect_uris": ["https://sync.example/callback"],
            "scopes": ["read:organization", "write:events", "write:training"],
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
    assert application["scopes"] == ["read:organization", "write:events", "write:training"]

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
            "scopes": ["read:organization", "write:events", "write:training"],
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
    assert api_key["scopes"] == ["read:organization", "write:events", "write:training"]
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
    training_event = next(
        event for event in catalog["webhook_events"] if event["event_type"] == "training.drill.created"
    )
    assert training_event["emission_status"] == "active"
    assert "write:training" in training_event["recommended_scopes"]
    assert any(sdk["language"] == "Raw HTTP" and sdk["status"] == "active" for sdk in catalog["sdks"])

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
    assert summary["api_key_count"] == 5
    assert summary["active_api_key_count"] == 5
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
