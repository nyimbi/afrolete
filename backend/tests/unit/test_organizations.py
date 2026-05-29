from base64 import b64encode

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


def test_organization_handle_availability_suggests_conflict_recovery(client, identity_headers) -> None:
    created = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Harbor Youth Club",
            "organization_type": "club",
            "subdomain": "harbor-youth",
        },
    ).json()

    availability_response = client.get(
        "/api/v1/organizations/handles/availability?name=Harbor%20Youth%20Club&subdomain=harbor-youth"
    )

    assert availability_response.status_code == 200
    availability = availability_response.json()
    assert availability["desired_slug"] == created["slug"]
    assert availability["slug_available"] is False
    assert availability["slug_suggestions"][0] == "harbor-youth-club-2"
    assert availability["desired_subdomain"] == "harbor-youth"
    assert availability["subdomain_available"] is False
    assert availability["subdomain_suggestions"][0] == "harbor-youth-2"

    duplicate_name_response = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Harbor Youth Club",
            "organization_type": "club",
        },
    )

    assert duplicate_name_response.status_code == 201
    assert duplicate_name_response.json()["slug"] == "harbor-youth-club-2"

    conflicting_subdomain_response = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Harbor Youth Academy",
            "organization_type": "academy",
            "subdomain": "harbor-youth",
        },
    )

    assert conflicting_subdomain_response.status_code == 409
    detail = conflicting_subdomain_response.json()["detail"]
    assert detail["message"] == "Organization subdomain exists"
    assert detail["subdomain_suggestions"][0] == "harbor-youth-2"


def test_self_service_onboarding_creates_school_and_public_directory(client, identity_headers) -> None:
    response = client.post(
        "/api/v1/organizations/onboarding",
        headers=identity_headers,
        json={
            "launch_goal": "Open registration for term two athletics",
            "starter_team_name": "Junior Sprint Squad",
            "starter_team_sport": "athletics",
            "starter_team_sport_format": "individual",
            "starter_team_age_group": "U15",
            "starter_team_gender_category": "open",
            "starter_team_season_label": "Term 2",
            "organization": {
                "name": "Makini Track School",
                "organization_type": "school",
                "country_code": "KE",
                "primary_sport": "athletics",
                "public_name": "Makini Track",
                "contact_email": "sports@makini.example",
                "subdomain": "makini-track",
                "mission": "Run school athletics safely and transparently.",
                "registration_open": True,
                "registration_fee_amount": "1000.00",
                "registration_fee_currency": "KES",
                "registration_payment_instructions": "Use the hosted checkout link after uploading documents.",
                "registration_required_documents": [
                    "proof_of_age",
                    "medical_information",
                    "guardian_consent",
                    "photo_release",
                ],
            },
        },
    )

    assert response.status_code == 201
    onboarding = response.json()
    assert onboarding["organization"]["organization_type"] == "school"
    assert onboarding["organization"]["my_roles"] == ["owner"]
    assert onboarding["owner_email"] == identity_headers["X-Afrolete-Email"]
    assert onboarding["public_site_path"] == "/site/makini-track"
    assert onboarding["registration_page_path"] == "/register?mode=player&site=makini-track"
    assert onboarding["admissions_path"] == f"/admissions?organization_id={onboarding['organization']['id']}"
    assert onboarding["family_portal_path"] == f"/family?organization_id={onboarding['organization']['id']}"
    assert onboarding["dashboard_path"].startswith("/?organization_id=")
    assert onboarding["starter_team"]["name"] == "Junior Sprint Squad"
    assert onboarding["starter_team"]["sport_format"] == "individual"
    assert onboarding["starter_team"]["age_group"] == "U15"
    assert onboarding["starter_team"]["season_label"] == "Term 2"
    assert onboarding["organization"]["registration_fee_amount"] == "1000.00"
    assert onboarding["organization"]["registration_fee_currency"] == "KES"
    assert onboarding["organization"]["registration_required_documents"] == [
        "proof_of_age",
        "medical_information",
        "guardian_consent",
        "photo_release",
    ]
    assert onboarding["checklist"][0] == "Confirm launch goal: Open registration for term two athletics"
    assert any("school teams" in step for step in onboarding["checklist"])

    directory_response = client.get(
        "/api/v1/organizations/directory?q=Makini&organization_type=school&sport=athletics"
    )

    assert directory_response.status_code == 200
    directory = directory_response.json()
    assert [item["slug"] for item in directory] == ["makini-track-school"]
    assert directory[0]["public_site_path"] == "/site/makini-track"
    assert directory[0]["team_count"] == 1

    public_site_response = client.get("/api/v1/organizations/public/makini-track")
    assert public_site_response.status_code == 200
    public_site = public_site_response.json()
    assert [team["name"] for team in public_site["teams"]] == ["Junior Sprint Squad"]
    assert public_site["registration_open"] is True
    assert public_site["registration_fee_amount"] == "1000.00"
    assert public_site["registration_payment_instructions"] == "Use the hosted checkout link after uploading documents."

    inquiry_response = client.post(
        "/api/v1/organizations/public/makini-track/registration-inquiries",
        json={
            "athlete_name": "Amina Runner",
            "guardian_name": "Parent Runner",
            "email": "parent.runner@example.com",
            "phone": "+254700000001",
            "age_group": "U15",
            "sport_interest": "athletics",
            "team_id": onboarding["starter_team"]["id"],
            "message": "Interested in sprint training.",
            "source_url": "https://makini-track.afrolete.local/register",
        },
    )

    assert inquiry_response.status_code == 201
    inquiry = inquiry_response.json()
    assert inquiry["athlete_name"] == "Amina Runner"
    assert inquiry["status"] == "new"
    assert inquiry["organization_id"] == onboarding["organization"]["id"]
    assert inquiry["team_id"] == onboarding["starter_team"]["id"]
    assert inquiry["verification_status"] == "inquiry"
    assert inquiry["payment_amount"] == "1000.00"
    assert inquiry["payment_currency"] == "KES"
    assert inquiry["payment_status"] == "pending"
    assert inquiry["guardian_person_id"]
    assert inquiry["guardian_contact_status"] == "pending_account"
    assert inquiry["packet_complete"] is False
    assert "proof_of_age" in inquiry["missing_documents"]
    assert any("Upload missing documents" in step for step in inquiry["next_steps"])

    repeat_inquiry_response = client.post(
        "/api/v1/organizations/public/makini-track/registration-inquiries",
        json={
            "athlete_name": "Asha Runner",
            "guardian_name": "Parent Runner",
            "email": "PARENT.RUNNER@example.com",
            "phone": "+254700000001",
            "age_group": "U13",
            "sport_interest": "athletics",
            "team_id": onboarding["starter_team"]["id"],
        },
    )
    assert repeat_inquiry_response.status_code == 201
    repeat_inquiry = repeat_inquiry_response.json()
    assert repeat_inquiry["email"] == "parent.runner@example.com"
    assert repeat_inquiry["guardian_person_id"] == inquiry["guardian_person_id"]
    assert repeat_inquiry["guardian_contact_status"] == "pending_account"

    premature_conversion_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/{inquiry['id']}/convert",
        headers=identity_headers,
        json={
            "team_id": onboarding["starter_team"]["id"],
            "role": "player",
            "create_guardian": True,
            "send_guardian_invite": False,
        },
    )
    assert premature_conversion_response.status_code == 409
    premature_detail = premature_conversion_response.json()["detail"]
    assert premature_detail["message"] == "Registration packet is not ready for conversion"
    assert "proof_of_age" in premature_detail["missing_documents"]

    readiness_response = client.get(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/account-readiness"
        "?email=parent.runner@example.com"
    )
    assert readiness_response.status_code == 200
    readiness = readiness_response.json()
    assert readiness["guardian_person_id"] == inquiry["guardian_person_id"]
    assert readiness["account_status"] == "invite_ready"
    assert readiness["can_create_account"] is True
    assert readiness["can_sign_in"] is True

    mismatch_readiness_response = client.get(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/account-readiness"
        "?email=other.parent@example.com"
    )
    assert mismatch_readiness_response.status_code == 403

    guardian_identity_headers = {
        "X-Afrolete-Sub": "kc-parent-runner",
        "X-Afrolete-Email": "parent.runner@example.com",
        "X-Afrolete-Name": "Parent Runner",
    }
    family_response = client.get(
        f"/api/v1/safeguarding/my-family?organization_id={onboarding['organization']['id']}",
        headers=guardian_identity_headers,
    )
    assert family_response.status_code == 200
    family_registration_response = client.get(
        f"/api/v1/organizations/my-registration-inquiries?organization_id={onboarding['organization']['id']}",
        headers=guardian_identity_headers,
    )
    assert family_registration_response.status_code == 200
    family_registrations = family_registration_response.json()
    family_registration_by_id = {item["id"]: item for item in family_registrations}
    assert set(family_registration_by_id) == {repeat_inquiry["id"], inquiry["id"]}
    amina_registration = family_registration_by_id[inquiry["id"]]
    assert amina_registration["athlete_name"] == "Amina Runner"
    assert amina_registration["organization_public_name"] == "Makini Track"
    assert amina_registration["public_site_path"] == "/site/makini-track"
    assert amina_registration["account_status"] == "linked"
    assert amina_registration["packet_complete"] is False
    assert "proof_of_age" in amina_registration["missing_documents"]
    resume_packet_response = client.get(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/packet"
        "?email=parent.runner@example.com"
    )
    assert resume_packet_response.status_code == 200
    resume_packet = resume_packet_response.json()
    assert resume_packet["inquiry"]["id"] == inquiry["id"]
    assert resume_packet["inquiry"]["guardian_person_id"] == inquiry["guardian_person_id"]
    assert resume_packet["packet_complete"] is False
    assert "proof_of_age" in resume_packet["missing_documents"]
    forbidden_resume_response = client.get(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/packet"
        "?email=other.parent@example.com"
    )
    assert forbidden_resume_response.status_code == 403
    linked_readiness_response = client.get(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/account-readiness"
        "?email=parent.runner@example.com"
    )
    assert linked_readiness_response.status_code == 200
    linked_readiness = linked_readiness_response.json()
    assert linked_readiness["account_status"] == "linked"
    assert linked_readiness["can_create_account"] is False
    assert linked_readiness["can_sign_in"] is True

    document_response = client.post(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/documents",
        json={
            "email": "parent.runner@example.com",
            "document_type": "proof_of_age",
            "filename": "birth certificate.pdf",
            "content_type": "application/pdf",
            "content_base64": b64encode(b"proof-of-age").decode(),
            "notes": "Birth certificate scan.",
        },
    )

    assert document_response.status_code == 200
    uploaded_packet = document_response.json()
    assert uploaded_packet["submitted_documents"][0]["document_type"] == "proof_of_age"
    assert uploaded_packet["submitted_documents"][0]["filename"] == "birth-certificate.pdf"
    assert uploaded_packet["submitted_documents"][0]["storage_url"].startswith("local://registration-documents/")
    assert uploaded_packet["submitted_documents"][0]["size_bytes"] == len(b"proof-of-age")
    assert "proof_of_age" not in uploaded_packet["missing_documents"]

    packet_response = client.patch(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/packet",
        json={
            "email": "parent.runner@example.com",
            "date_of_birth": "2012-03-04",
            "emergency_contact_name": "Parent Runner",
            "emergency_contact_phone": "+254700000001",
            "medical_notes": "No known allergies.",
            "consent_signer_name": "Parent Runner",
            "guardian_consent_acknowledged": True,
            "privacy_acknowledged": True,
            "documents": [
                {
                    "document_type": "proof_of_age",
                    "filename": "birth-certificate.pdf",
                    "storage_url": uploaded_packet["submitted_documents"][0]["storage_url"],
                    "checksum": uploaded_packet["submitted_documents"][0]["checksum"],
                    "content_type": "application/pdf",
                    "size_bytes": len(b"proof-of-age"),
                },
                {"document_type": "medical_information", "filename": "medical-form.pdf"},
                {"document_type": "guardian_consent", "filename": "guardian-consent.pdf"},
                {"document_type": "photo_release", "filename": "photo-release.pdf"},
            ],
            "payment_amount": "1000.00",
            "payment_currency": "KES",
            "payment_method": "mpesa",
            "payment_reference": None,
            "payment_status": "pending",
        },
    )

    assert packet_response.status_code == 200
    packet = packet_response.json()
    assert packet["packet_complete"] is False
    assert packet["missing_documents"] == []
    assert packet["consent_complete"] is True
    assert packet["payment_complete"] is False
    assert packet["inquiry"]["status"] == "reviewing"
    assert packet["inquiry"]["verification_status"] == "packet_incomplete"
    assert packet["inquiry"]["packet_complete"] is False
    assert packet["inquiry"]["missing_documents"] == []
    assert "Record payment, waiver, or not-required status." in packet["next_steps"]

    waiver_response = client.patch(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/{inquiry['id']}",
        headers=identity_headers,
        json={
            "status": "reviewing",
            "review_notes": "Fee waived for scholarship review.",
            "payment_status": "waived",
            "payment_method": "staff_waiver",
            "payment_reference": "WAIVE-2026",
        },
    )
    assert waiver_response.status_code == 200
    waiver = waiver_response.json()
    assert waiver["payment_status"] == "waived"
    assert waiver["payment_method"] == "staff_waiver"
    assert waiver["payment_reference"] == "WAIVE-2026"
    assert waiver["verification_status"] == "ready_for_review"
    assert waiver["packet_complete"] is True
    assert waiver["next_steps"] == ["Registration packet is ready for staff verification."]

    pending_payment_response = client.patch(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/{inquiry['id']}",
        headers=identity_headers,
        json={
            "status": "reviewing",
            "payment_status": "pending",
            "payment_method": "registration_checkout",
            "payment_reference": None,
        },
    )
    assert pending_payment_response.status_code == 200
    assert pending_payment_response.json()["verification_status"] == "packet_incomplete"

    payment_session_response = client.post(
        f"/api/v1/organizations/public/makini-track/registration-inquiries/{inquiry['id']}/payment-session",
        json={
            "email": "parent.runner@example.com",
            "checkout_base_url": "/pay/sessions",
            "provider": "manual_gateway",
            "payment_method": "mobile_money",
        },
    )
    assert payment_session_response.status_code == 200
    payment_session = payment_session_response.json()
    assert payment_session["checkout_url"].startswith(f"/pay/sessions/{payment_session['session_id']}")
    assert "kind=registration" in payment_session["checkout_url"]
    assert f"inquiry_id={inquiry['id']}" in payment_session["checkout_url"]
    assert payment_session["hosted_checkout"]["open_amount"] == "1000.00"
    assert payment_session["inquiry"]["payment_reference"] == payment_session["session_id"]

    checkout_response = client.get(
        f"/api/v1/organizations/registration-checkout-sessions/{payment_session['session_id']}"
        f"?site=makini-track&inquiry_id={inquiry['id']}&provider=manual_gateway"
    )
    assert checkout_response.status_code == 200
    checkout = checkout_response.json()
    assert checkout["registration_reference"].startswith("REG-")
    assert checkout["client_reference"] == f"registration-payment:{inquiry['id']}"

    settlement_response = client.post(
        f"/api/v1/organizations/registration-checkout-sessions/{payment_session['session_id']}/settle?site=makini-track",
        json={
            "inquiry_id": inquiry["id"],
            "provider": "manual_gateway",
            "amount": "1000.00",
            "currency": "KES",
            "method": "hosted_payment_page",
            "external_payment_id": "MPESA-ABC123",
            "status": "succeeded",
        },
    )
    assert settlement_response.status_code == 200
    settlement = settlement_response.json()
    assert settlement["payment_status"] == "paid"
    assert settlement["payment_reference"] == "MPESA-ABC123"
    assert settlement["open_amount"] == "0.00"

    team_response = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": onboarding["organization"]["id"],
            "name": "Makini U15 Sprint",
            "sport": "athletics",
            "sport_format": "individual",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    conversion_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/{inquiry['id']}/convert",
        headers=identity_headers,
        json={
            "team_id": team["id"],
            "role": "player",
            "create_guardian": True,
            "send_guardian_invite": True,
            "guardian_invite_channel": "email",
            "guardian_portal_url": "http://localhost:3000/family",
            "jersey_number": "7",
            "primary_position": "sprinter",
        },
    )

    assert conversion_response.status_code == 200
    conversion = conversion_response.json()
    assert conversion["inquiry"]["status"] == "converted"
    assert conversion["inquiry"]["guardian_person_id"] == inquiry["guardian_person_id"]
    assert conversion["inquiry"]["guardian_contact_status"] == "linked_to_athlete"
    assert conversion["roster_entry_id"]
    assert conversion["guardian_person_id"] == inquiry["guardian_person_id"]
    assert conversion["guardian_invite_message_id"]
    assert conversion["guardian_invite_portal_url"].startswith("http://localhost:3000/family?")
    assert f"organization_id={onboarding['organization']['id']}" in conversion["guardian_invite_portal_url"]
    assert f"athlete_id={conversion['athlete_person_id']}" in conversion["guardian_invite_portal_url"]
    assert "autoload=1" in conversion["guardian_invite_portal_url"]
    assert "guardian_email=parent.runner%40example.com" in conversion["guardian_invite_portal_url"]

    messages_response = client.get(
        f"/api/v1/communications/messages?organization_id={onboarding['organization']['id']}"
    )
    assert messages_response.status_code == 200
    invite_message = next(
        item for item in messages_response.json() if item["id"] == conversion["guardian_invite_message_id"]
    )
    assert invite_message["message_type"] == "request"
    assert invite_message["channel"] == "email"
    assert "family portal invitation" in invite_message["subject"]
    assert conversion["guardian_invite_portal_url"] in invite_message["body"]


def test_public_site_exposes_commercial_support_opportunities(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Supporter City FC",
            "organization_type": "club",
            "primary_sport": "football",
            "subdomain": "supporter-city",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U17 Supporters",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    event = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_type": "match",
            "title": "Sponsor Showcase Derby",
            "starts_at": "2026-08-01T15:00:00Z",
            "ends_at": "2026-08-01T17:00:00Z",
            "venue_name": "Partner Park",
        },
    ).json()
    sponsor = client.post(
        "/api/v1/commercial/sponsors",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "AfroBank",
            "industry": "Financial services",
            "website_url": "https://afrobank.example",
            "brand_assets_url": "https://cdn.example/afrobank.png",
        },
    ).json()
    client.post(
        "/api/v1/commercial/sponsorships",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "event_id": event["id"],
            "name": "Community Match Partner",
            "tier": "Gold",
            "value_amount": "2500.00",
            "deliverables": "Shirt logo, pitch board, livestream mention",
            "activation_notes": "Family ticket bundle live.",
        },
    )
    campaign = client.post(
        "/api/v1/commercial/campaigns",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "name": "Boot fund",
            "purpose": "Boots for academy players",
            "goal_amount": "1000.00",
            "public_url": "https://supporter-city.example/boot-fund",
        },
    ).json()
    client.post(
        "/api/v1/commercial/donations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "campaign_id": campaign["id"],
            "donor_name": "Local Donor",
            "amount": "125.00",
        },
    )
    client.post(
        "/api/v1/commercial/tickets/products",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "event_id": event["id"],
            "name": "Family Stand",
            "price": "7.50",
            "capacity": 120,
            "access_zone": "East gate",
        },
    )

    site_response = client.get("/api/v1/organizations/public/supporter-city")

    assert site_response.status_code == 200
    site = site_response.json()
    assert site["sponsors"][0]["name"] == "AfroBank"
    assert site["sponsors"][0]["tier"] == "Gold"
    assert site["sponsors"][0]["active_value"] == "2500.00"
    assert site["sponsors"][0]["deliverables"] == ["Shirt logo", "pitch board", "livestream mention"]
    assert site["fundraising_campaigns"][0]["raised_amount"] == "125.00"
    assert site["ticket_products"][0]["name"] == "Family Stand"
    assert site["ticket_products"][0]["event_title"] == "Sponsor Showcase Derby"
    assert site["ticket_products"][0]["available_count"] == 120


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
