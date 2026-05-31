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


def test_club_manages_member_dues_without_saas_subscription_coupling(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Dues Managed FC",
            "organization_type": "club",
            "country_code": "KE",
            "primary_sport": "football",
        },
    ).json()

    member_response = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "member-dues@example.com",
            "display_name": "Member Dues",
            "country_code": "KE",
            "role": "athlete",
            "title": "Senior player",
        },
    )
    assert member_response.status_code == 201
    member = member_response.json()

    plan_response = client.post(
        f"/api/v1/organizations/{organization['id']}/member-subscription-plans",
        headers=identity_headers,
        json={
            "name": "Senior player monthly dues",
            "member_role": "athlete",
            "amount": "1500.00",
            "currency": "KES",
            "billing_interval": "monthly",
            "due_day": 5,
            "grace_period_days": 10,
            "benefits": "Training access, league registration, member voting eligibility.",
        },
    )
    assert plan_response.status_code == 201
    plan = plan_response.json()
    assert plan["currency"] == "KES"
    assert plan["billing_interval"] == "monthly"

    subscription_response = client.post(
        f"/api/v1/organizations/{organization['id']}/member-subscriptions",
        headers=identity_headers,
        json={
            "plan_id": plan["id"],
            "membership_id": member["id"],
            "starts_on": "2026-06-01",
            "current_period_start": "2026-06-01",
            "current_period_end": "2026-06-30",
            "next_due_on": "2026-06-05",
            "external_reference": "club-dues-2026-06",
        },
    )
    assert subscription_response.status_code == 201
    subscription = subscription_response.json()
    assert subscription["subject_type"] == "person"
    assert subscription["subject_id"] == member["subject_id"]
    assert subscription["subject_label"] == "Member Dues"
    assert subscription["plan_name"] == "Senior player monthly dues"
    assert subscription["balance_amount"] == "1500.00"

    payment_response = client.post(
        f"/api/v1/organizations/member-subscriptions/{subscription['id']}/payments",
        headers=identity_headers,
        json={
            "amount": "1000.00",
            "provider": "mpesa",
            "method": "stk_push",
            "external_payment_id": "MPESA-ABC-123",
            "raw_reference": "Till 123456 confirmed receipt.",
        },
    )
    assert payment_response.status_code == 201
    payment = payment_response.json()
    assert payment["provider"] == "mpesa"
    assert payment["subscription_balance_amount"] == "500.00"
    assert payment["subscription_status"] == "active"

    subscriptions_response = client.get(
        f"/api/v1/organizations/{organization['id']}/member-subscriptions",
        headers=identity_headers,
    )
    assert subscriptions_response.status_code == 200
    assert subscriptions_response.json()[0]["balance_amount"] == "500.00"


def test_organization_program_season_and_group_crud(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Program Managed Academy",
            "organization_type": "academy",
            "country_code": "KE",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "U15 Development",
            "sport": "football",
            "sport_format": "team",
            "age_group": "U15",
            "season_label": "2026",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "group-member@example.com",
            "display_name": "Group Member",
            "role": "athlete",
        },
    ).json()

    program_response = client.post(
        f"/api/v1/organizations/{organization['id']}/programs",
        headers=identity_headers,
        json={
            "name": "Foundation Development Pathway",
            "program_type": "academy_pathway",
            "sport": "football",
            "age_group": "U13-U17",
            "gender_category": "open",
            "capacity": 80,
            "starts_on": "2026-01-10",
            "ends_on": "2026-11-30",
            "description": "Technical, tactical, academic, and safeguarding development pathway.",
        },
    )
    assert program_response.status_code == 201
    program = program_response.json()

    season_response = client.post(
        f"/api/v1/organizations/{organization['id']}/seasons",
        headers=identity_headers,
        json={
            "name": "2026 Long Rains Season",
            "sport": "football",
            "starts_on": "2026-03-01",
            "ends_on": "2026-08-31",
            "registration_opens_on": "2026-01-15",
            "registration_closes_on": "2026-02-20",
            "status": "registration_open",
            "notes": "Registration, dues, team assignments, and competition readiness window.",
        },
    )
    assert season_response.status_code == 201
    season = season_response.json()

    group_response = client.post(
        f"/api/v1/organizations/{organization['id']}/groups",
        headers=identity_headers,
        json={
            "name": "Advanced Midfield Cohort",
            "group_type": "position_group",
            "program_id": program["id"],
            "season_id": season["id"],
            "team_id": team["id"],
            "sport": "football",
            "age_group": "U15",
            "capacity": 16,
            "description": "Position-specific small group for tactical and video review work.",
        },
    )
    assert group_response.status_code == 201
    group = group_response.json()
    assert group["member_count"] == 0
    assert group["program_id"] == program["id"]
    assert group["season_id"] == season["id"]

    group_member_response = client.post(
        f"/api/v1/organizations/groups/{group['id']}/members",
        headers=identity_headers,
        json={
            "subject_type": "person",
            "subject_id": member["subject_id"],
            "role": "athlete",
            "notes": "Primary midfield development cohort.",
        },
    )
    assert group_member_response.status_code == 201
    group_member = group_member_response.json()
    assert group_member["subject_label"] == "Group Member"
    assert group_member["role"] == "athlete"

    groups = client.get(f"/api/v1/organizations/{organization['id']}/groups", headers=identity_headers).json()
    assert groups[0]["member_count"] == 1
    members = client.get(f"/api/v1/organizations/groups/{group['id']}/members", headers=identity_headers).json()
    assert members[0]["subject_id"] == member["subject_id"]


def test_organization_data_migration_and_recovery_crud(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Continuity Ready Club",
            "organization_type": "club",
            "country_code": "KE",
            "primary_sport": "football",
        },
    ).json()

    project_response = client.post(
        f"/api/v1/organizations/{organization['id']}/data-migration-projects",
        headers=identity_headers,
        json={
            "name": "Legacy SportsEngine import",
            "source_system": "sportsengine",
            "source_format": "csv",
            "migration_type": "initial_import",
            "data_domains": "people,teams,rosters,fees",
            "risk_level": "medium",
            "records_expected": 120,
            "notes": "Move member, team, roster, and dues history into AfroLete.",
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()
    assert project["run_count"] == 0
    assert project["records_imported"] == 0

    validation_response = client.post(
        f"/api/v1/organizations/data-migration-projects/{project['id']}/runs",
        headers=identity_headers,
        json={
            "run_type": "validation",
            "status": "partial",
            "records_seen": 120,
            "records_skipped": 4,
            "error_count": 2,
            "mapping_summary": "Mapped people, teams, guardians, and fee plans; two rows need cleanup.",
            "report_url": "https://example.test/reports/migration-validation",
        },
    )
    assert validation_response.status_code == 201
    assert validation_response.json()["records_seen"] == 120

    import_response = client.post(
        f"/api/v1/organizations/data-migration-projects/{project['id']}/runs",
        headers=identity_headers,
        json={
            "run_type": "import",
            "status": "succeeded",
            "records_seen": 120,
            "records_created": 80,
            "records_updated": 36,
            "records_skipped": 4,
            "error_count": 0,
            "checksum": "sha256:demo-import",
            "notes": "Dry-run corrections applied before import.",
        },
    )
    assert import_response.status_code == 201

    projects_response = client.get(
        f"/api/v1/organizations/{organization['id']}/data-migration-projects",
        headers=identity_headers,
    )
    assert projects_response.status_code == 200
    listed_project = projects_response.json()[0]
    assert listed_project["run_count"] == 2
    assert listed_project["records_imported"] == 116
    assert listed_project["error_count"] == 2
    assert listed_project["status"] == "reconciled"

    runs_response = client.get(
        f"/api/v1/organizations/data-migration-projects/{project['id']}/runs",
        headers=identity_headers,
    )
    assert runs_response.status_code == 200
    assert len(runs_response.json()) == 2

    plan_response = client.post(
        f"/api/v1/organizations/{organization['id']}/recovery-plans",
        headers=identity_headers,
        json={
            "name": "Club continuity plan",
            "scope": "tenant_operational_data",
            "rpo_minutes": 60,
            "rto_minutes": 240,
            "backup_frequency": "daily",
            "storage_location": "lindela-minio/afrolete-backups",
            "retention_days": 90,
            "encryption_policy": "OpenBao-managed keys",
            "status": "active",
            "notes": "Covers PostgreSQL tenant data and object-storage evidence.",
        },
    )
    assert plan_response.status_code == 201
    plan = plan_response.json()
    assert plan["drill_count"] == 0

    drill_response = client.post(
        f"/api/v1/organizations/recovery-plans/{plan['id']}/drills",
        headers=identity_headers,
        json={
            "drill_type": "restore_test",
            "status": "passed",
            "rpo_minutes_observed": 45,
            "rto_minutes_observed": 180,
            "data_loss_summary": "No data loss beyond accepted backup window.",
            "result_summary": "Tenant restored into isolated rehearsal environment.",
            "action_items": "Automate quarterly evidence collection.",
            "evidence_url": "https://example.test/evidence/recovery-drill",
        },
    )
    assert drill_response.status_code == 201
    assert drill_response.json()["status"] == "passed"

    plans_response = client.get(
        f"/api/v1/organizations/{organization['id']}/recovery-plans",
        headers=identity_headers,
    )
    assert plans_response.status_code == 200
    listed_plan = plans_response.json()[0]
    assert listed_plan["drill_count"] == 1
    assert listed_plan["last_tested_at"] is not None
    assert listed_plan["status"] == "active"

    drills_response = client.get(
        f"/api/v1/organizations/recovery-plans/{plan['id']}/drills",
        headers=identity_headers,
    )
    assert drills_response.status_code == 200
    assert drills_response.json()[0]["rto_minutes_observed"] == 180


def test_organization_compliance_document_register_versions_and_summary(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Document Ready Club",
            "organization_type": "club",
            "country_code": "KE",
            "primary_sport": "football",
        },
    ).json()

    document_response = client.post(
        f"/api/v1/organizations/{organization['id']}/compliance-documents",
        headers=identity_headers,
        json={
            "title": "Public liability insurance",
            "category": "legal_regulatory",
            "document_type": "insurance_certificate",
            "issuer": "ABC Insurance",
            "reference_number": "PLI-2026-001",
            "status": "verified",
            "renewal_status": "in_progress",
            "effective_on": "2026-01-01",
            "expires_on": "2026-06-30",
            "next_review_on": "2026-06-01",
            "retention_until": "2033-01-01",
            "auto_renewal_enabled": True,
            "storage_url": "local://compliance/public-liability-v1.pdf",
            "checksum": "sha256:insurance-v1",
            "confidentiality": "restricted",
            "tags": "insurance,facility,event",
            "notes": "Required for matchday operations and facility hire.",
        },
    )
    assert document_response.status_code == 201
    document = document_response.json()
    assert document["version_count"] == 1
    assert document["current_version"] == 1
    assert document["auto_renewal_enabled"] is True
    assert document["days_until_expiry"] is not None

    version_response = client.post(
        f"/api/v1/organizations/compliance-documents/{document['id']}/versions",
        headers=identity_headers,
        json={
            "storage_url": "local://compliance/public-liability-v2.pdf",
            "checksum": "sha256:insurance-v2",
            "filename": "public-liability-v2.pdf",
            "content_type": "application/pdf",
            "size_bytes": 2048,
            "change_summary": "Renewal quote and updated coverage schedule added.",
            "status": "current",
        },
    )
    assert version_response.status_code == 201
    version = version_response.json()
    assert version["version_number"] == 2
    assert version["status"] == "current"

    versions_response = client.get(
        f"/api/v1/organizations/compliance-documents/{document['id']}/versions",
        headers=identity_headers,
    )
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert [item["version_number"] for item in versions] == [2, 1]
    assert versions[1]["status"] == "superseded"

    documents_response = client.get(
        f"/api/v1/organizations/{organization['id']}/compliance-documents",
        headers=identity_headers,
    )
    assert documents_response.status_code == 200
    listed = documents_response.json()[0]
    assert listed["current_version"] == 2
    assert listed["checksum"] == "sha256:insurance-v2"
    assert listed["version_count"] == 2

    summary_response = client.get(
        f"/api/v1/organizations/{organization['id']}/compliance-documents/summary",
        headers=identity_headers,
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_documents"] == 1
    assert summary["verified_documents"] == 1
    assert summary["auto_renewal_documents"] == 1
    assert summary["category_counts"]["legal_regulatory"] == 1
    assert summary["renewal_status_counts"]["in_progress"] == 1


def test_organization_awards_nomination_voting_and_certificate_crud(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Awards Managed Club",
            "organization_type": "club",
            "country_code": "KE",
            "primary_sport": "football",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "award-winner@example.com",
            "display_name": "Award Winner",
            "role": "athlete",
            "title": "Forward",
        },
    ).json()

    program_response = client.post(
        f"/api/v1/organizations/{organization['id']}/award-programs",
        headers=identity_headers,
        json={
            "name": "Season Awards",
            "season_label": "2026",
            "level": "club",
            "frequency": "seasonal",
            "nomination_opens_at": "2026-11-01T08:00:00Z",
            "nomination_closes_at": "2026-11-15T18:00:00Z",
            "voting_opens_at": "2026-11-16T08:00:00Z",
            "voting_closes_at": "2026-11-25T18:00:00Z",
            "eligibility_summary": "Active members in good standing with attendance and dues complete.",
            "ceremony_name": "Awards Night",
            "ceremony_at": "2026-12-05T17:00:00Z",
            "ceremony_venue": "Clubhouse Hall",
            "certificate_template": "Presented to {{name}} for {{award}}.",
            "status": "nominations_open",
        },
    )
    assert program_response.status_code == 201
    program = program_response.json()
    assert program["category_count"] == 0
    assert program["recipient_count"] == 0

    category_response = client.post(
        f"/api/v1/organizations/award-programs/{program['id']}/categories",
        headers=identity_headers,
        json={
            "name": "Player of the Season",
            "award_type": "individual",
            "judging_method": "weighted_vote",
            "criteria": "Attendance, match impact, leadership, and coachability.",
            "max_recipients": 1,
            "voter_roles": "coaches,players,committee",
        },
    )
    assert category_response.status_code == 201
    category = category_response.json()
    assert category["program_id"] == program["id"]

    nomination_response = client.post(
        f"/api/v1/organizations/award-categories/{category['id']}/nominations",
        headers=identity_headers,
        json={
            "nominee_subject_type": "person",
            "nominee_subject_id": member["subject_id"],
            "title": "Relentless season leader",
            "nomination_summary": "Led training attendance, match contribution, and teammate mentoring.",
            "evidence_url": "https://example.test/evidence/award-winner",
            "status": "shortlisted",
            "finalist": True,
            "score": "88.50",
        },
    )
    assert nomination_response.status_code == 201
    nomination = nomination_response.json()
    assert nomination["nominee_label"] == "Award Winner"
    assert nomination["vote_count"] == 0

    vote_response = client.post(
        f"/api/v1/organizations/award-nominations/{nomination['id']}/votes",
        headers=identity_headers,
        json={
            "score": "92.00",
            "weight": "1.50",
            "comment": "Clear winner on performance and leadership.",
        },
    )
    assert vote_response.status_code == 201
    assert vote_response.json()["score"] == "92.00"

    nominations_response = client.get(
        f"/api/v1/organizations/award-categories/{category['id']}/nominations",
        headers=identity_headers,
    )
    assert nominations_response.status_code == 200
    nominations = nominations_response.json()
    assert nominations[0]["vote_count"] == 1
    assert nominations[0]["weighted_score"] == "138.00"

    recipient_response = client.post(
        f"/api/v1/organizations/award-categories/{category['id']}/recipients",
        headers=identity_headers,
        json={
            "nomination_id": nomination["id"],
            "recipient_subject_type": "person",
            "recipient_subject_id": member["subject_id"],
            "awarded_on": "2026-12-05",
            "public_citation": "Recognized for sustained excellence, leadership, and club impact.",
            "certificate_url": "https://example.test/certificates/award-winner.pdf",
        },
    )
    assert recipient_response.status_code == 201
    recipient = recipient_response.json()
    assert recipient["recipient_label"] == "Award Winner"
    assert recipient["certificate_number"].startswith("AFROLETE-AWARD-")

    recipients_response = client.get(
        f"/api/v1/organizations/award-programs/{program['id']}/recipients",
        headers=identity_headers,
    )
    assert recipients_response.status_code == 200
    assert recipients_response.json()[0]["certificate_number"] == recipient["certificate_number"]


def test_registration_learning_path_personalizes_onboarding(client) -> None:
    response = client.post(
        "/api/v1/organizations/registration-learning-path",
        json={
            "role": "head_coach",
            "primary_goal": "track_performance",
            "skill_level": "intermediate",
            "learning_style": "visual",
            "accessibility_mode": "captions",
        },
    )

    assert response.status_code == 200
    path = response.json()
    assert path["role"] == "head_coach"
    assert path["primary_goal"] == "track_performance"
    assert path["difficulty"] == "applied"
    assert path["path_title"] == "Head Coach path: Track Performance"
    assert path["estimated_minutes"] == sum(module["duration_minutes"] for module in path["modules"])
    assert path["modules"][0]["title"] == "Set up the coaching workspace"
    assert path["modules"][1]["key"] == "performance_analytics"
    assert path["modules"][1]["format"] == "visual walkthrough"
    assert path["modules"][-1]["completion_badge"] == "Performance Tracking Pro"
    assert "captions" in path["accessibility_supports"]


def test_registration_onboarding_presets_filter_school_and_club_defaults(client) -> None:
    school_response = client.get("/api/v1/organizations/onboarding-presets?organization_type=school")

    assert school_response.status_code == 200
    school_presets = school_response.json()
    assert school_presets
    assert {preset["organization_type"] for preset in school_presets} == {"school"}
    assert any(preset["key"] == "school_term_athletics" for preset in school_presets)
    term_preset = next(preset for preset in school_presets if preset["key"] == "school_term_athletics")
    assert term_preset["starter_team_sport_format"] == "individual"
    assert "school_clearance" in term_preset["registration_required_documents"]
    assert any("school" in step.lower() for step in term_preset["checklist"])

    club_response = client.get("/api/v1/organizations/onboarding-presets?organization_type=club")

    assert club_response.status_code == 200
    club_presets = club_response.json()
    assert club_presets
    assert {preset["organization_type"] for preset in club_presets} == {"club"}
    assert any(preset["key"] == "club_youth_team" for preset in club_presets)
    youth_preset = next(preset for preset in club_presets if preset["key"] == "club_youth_team")
    assert youth_preset["starter_team_sport_format"] == "team"
    assert "guardian_consent" in youth_preset["registration_required_documents"]


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
    assert onboarding["concierge_task"]["task_type"] == "organization_onboarding_concierge"
    assert onboarding["concierge_task"]["status"] == "queued"
    assert onboarding["concierge_task"]["organization_id"] == onboarding["organization"]["id"]
    assert "Makini Track" in onboarding["concierge_task"]["title"]
    assert "Open registration for term two athletics" in onboarding["concierge_task"]["input_ref"]
    launch_center = onboarding["launch_center"]
    assert launch_center["organization_id"] == onboarding["organization"]["id"]
    assert launch_center["launch_status"] == "ready"
    assert launch_center["readiness_score"] >= 80
    assert launch_center["agent_task"] is None
    assert {link["key"] for link in launch_center["launch_links"]} >= {
        "public_site",
        "registration",
        "admissions",
        "family_portal",
    }
    assert any(copy["channel"] == "whatsapp" and "Makini Track" in copy["body"] for copy in launch_center["channel_copies"])
    assert any(metric["key"] == "teams" and metric["value"] == 1 for metric in launch_center["metrics"])
    assert any(action.startswith("Queue the Registration Growth Agent") for action in launch_center["staff_actions"])
    concierge_run_response = client.post(
        f"/api/v1/agents/tasks/{onboarding['concierge_task']['id']}/execute",
        headers=identity_headers,
    )
    assert concierge_run_response.status_code == 200
    concierge_run = concierge_run_response.json()
    assert concierge_run["status"] == "waiting_for_review"
    assert concierge_run["output_ref"].startswith("agent://tasks/")
    assert "Onboarding Concierge Agent prepared a deterministic launch readiness draft" in concierge_run["review_notes"]
    assert "Open registration for term two athletics" in concierge_run["review_notes"]
    assert "Publish the player/family registration link" in concierge_run["review_notes"]
    concierge_accept_response = client.patch(
        f"/api/v1/agents/tasks/{onboarding['concierge_task']['id']}",
        headers=identity_headers,
        json={
            "status": "completed",
            "review_notes": (
                f"{concierge_run['review_notes']}\n\n"
                "Owner accepted the onboarding concierge launch plan from registration."
            ),
        },
    )
    assert concierge_accept_response.status_code == 200
    concierge_accept = concierge_accept_response.json()
    assert concierge_accept["status"] == "completed"
    assert "Owner accepted the onboarding concierge launch plan" in concierge_accept["review_notes"]
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

    owner_readiness_response = client.get("/api/v1/organizations/registration-readiness", headers=identity_headers)
    assert owner_readiness_response.status_code == 200
    owner_readiness = owner_readiness_response.json()
    assert owner_readiness["auth_mode"] == "local"
    assert owner_readiness["identity_email"] == identity_headers["X-Afrolete-Email"]
    assert owner_readiness["managed_organization_count"] == 1
    assert owner_readiness["registration_open_count"] == 1
    assert owner_readiness["public_directory_count"] == 1
    assert owner_readiness["admissions_inquiry_count"] == 0
    assert owner_readiness["family_registration_count"] == 0
    assert owner_readiness["organizations"][0]["registration_page_path"] == "/register?mode=player&site=makini-track"
    owner_steps = {step["key"]: step for step in owner_readiness["steps"]}
    assert owner_steps["identity"]["status"] == "ready"
    assert owner_steps["workspace"]["href"] == f"/admissions?organization_id={onboarding['organization']['id']}"
    assert owner_steps["public_registration"]["href"] == "/site/makini-track"
    owner_missions = {mission["key"]: mission for mission in owner_readiness["missions"]}
    assert owner_missions["launch_workspace"]["status"] == "complete"
    assert owner_missions["publish_family_intake"]["progress_percent"] == 100
    assert owner_missions["complete_family_packet"]["status"] == "available"
    assert owner_missions["review_admissions"]["status"] == "locked"

    launch_get_response = client.get(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-launch-center"
        "?base_url=http://localhost:3000",
        headers=identity_headers,
    )
    assert launch_get_response.status_code == 200
    launch_get = launch_get_response.json()
    assert launch_get["launch_links"][1]["url"].startswith("http://localhost:3000/register?")
    assert launch_get["metrics"][0]["label"] == "Teams/programs"

    launch_agent_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-launch-center/agent-task"
        "?base_url=http://localhost:3000",
        headers=identity_headers,
    )
    assert launch_agent_response.status_code == 200
    launch_agent_center = launch_agent_response.json()
    assert launch_agent_center["agent_task"]["task_type"] == "registration_launch_campaign"
    assert launch_agent_center["agent_task"]["status"] == "queued"
    assert f"registration-launch:{onboarding['organization']['id']};" in launch_agent_center["agent_task"]["input_ref"]
    assert any("Review Registration Growth Agent task" in action for action in launch_agent_center["staff_actions"])

    duplicate_launch_agent_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-launch-center/agent-task",
        headers=identity_headers,
    )
    assert duplicate_launch_agent_response.status_code == 200
    assert duplicate_launch_agent_response.json()["agent_task"]["id"] == launch_agent_center["agent_task"]["id"]

    launch_agent_run_response = client.post(
        f"/api/v1/agents/tasks/{launch_agent_center['agent_task']['id']}/execute",
        headers=identity_headers,
    )
    assert launch_agent_run_response.status_code == 200
    launch_agent_run = launch_agent_run_response.json()
    assert launch_agent_run["status"] == "waiting_for_review"
    assert "Registration Growth Agent prepared a deterministic registration launch campaign" in launch_agent_run["review_notes"]
    assert "Current funnel: 0 inquiries, 0 ready packets, 0 pending payments" in launch_agent_run["review_notes"]

    template_response = client.get(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/import-template",
        headers=identity_headers,
    )
    assert template_response.status_code == 200
    template = template_response.json()
    assert template["filename"] == "makini-track-school-registration-import-template.csv"
    assert template["columns"] == [
        "athlete_name",
        "guardian_name",
        "email",
        "phone",
        "age_group",
        "sport_interest",
        "team",
        "message",
    ]
    assert "Junior Sprint Squad" in template["csv_text"]

    import_csv = (
        "athlete_name,guardian_name,email,phone,age_group,sport_interest,team,message\n"
        "Brian Import,Parent Import,parent.import@example.com,+254700000010,U15,athletics,Junior Sprint Squad,CSV intake\n"
        "Missing Email,Parent Import,,+254700000011,U13,athletics,Junior Sprint Squad,Needs email\n"
    )
    import_preview_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/import",
        headers=identity_headers,
        json={
            "csv_text": import_csv,
            "source_url": "admissions-csv-import",
            "dry_run": True,
        },
    )
    assert import_preview_response.status_code == 200
    import_preview = import_preview_response.json()
    assert import_preview["dry_run"] is True
    assert import_preview["created_count"] == 0
    assert import_preview["preview_count"] == 1
    assert import_preview["error_count"] == 1
    assert import_preview["preview_rows"][0]["athlete_name"] == "Brian Import"
    assert import_preview["preview_rows"][0]["team_name"] == "Junior Sprint Squad"

    import_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/import",
        headers=identity_headers,
        json={
            "csv_text": import_csv,
            "source_url": "admissions-csv-import",
        },
    )
    assert import_response.status_code == 200
    imported = import_response.json()
    assert imported["dry_run"] is False
    assert imported["created_count"] == 1
    assert imported["preview_count"] == 1
    assert imported["error_count"] == 1
    assert imported["inquiries"][0]["athlete_name"] == "Brian Import"
    assert imported["inquiries"][0]["team_id"] == onboarding["starter_team"]["id"]
    assert imported["inquiries"][0]["guardian_contact_status"] == "pending_account"
    assert imported["inquiries"][0]["payment_status"] == "pending"
    assert imported["errors"][0]["row_number"] == 3
    assert "email" in imported["errors"][0]["message"].lower()

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
    guardian_readiness_response = client.get("/api/v1/organizations/registration-readiness", headers=guardian_identity_headers)
    assert guardian_readiness_response.status_code == 200
    guardian_readiness = guardian_readiness_response.json()
    assert guardian_readiness["managed_organization_count"] == 0
    assert guardian_readiness["family_registration_count"] == 2
    assert guardian_readiness["family_packet_complete_count"] == 0
    assert guardian_readiness["family_registrations"][0]["organization_public_name"] == "Makini Track"
    guardian_steps = {step["key"]: step for step in guardian_readiness["steps"]}
    assert guardian_steps["family_registration"]["status"] == "action"
    assert guardian_steps["family_registration"]["action_label"] == "Resume family registration"
    guardian_missions = {mission["key"]: mission for mission in guardian_readiness["missions"]}
    assert guardian_missions["complete_family_packet"]["status"] == "active"
    assert guardian_missions["complete_family_packet"]["progress_percent"] == 60
    assert guardian_missions["complete_family_packet"]["action_label"] == "Resume packet"
    family_coordination_response = client.get(
        f"/api/v1/safeguarding/my-family/coordination?organization_id={onboarding['organization']['id']}",
        headers=guardian_identity_headers,
    )
    assert family_coordination_response.status_code == 200
    coordination_rows = family_coordination_response.json()
    coordination_by_name = {row["athlete_name"]: row for row in coordination_rows}
    assert {"Amina Runner", "Asha Runner"} <= set(coordination_by_name)
    amina_coordination = coordination_by_name["Amina Runner"]
    assert amina_coordination["registration_count"] == 1
    assert amina_coordination["missing_document_count"] >= 1
    assert amina_coordination["next_action_label"] == "Continue packet"
    assert amina_coordination["action_href"].startswith("/site/makini-track?inquiry_id=")
    assert "email=parent.runner%40example.com" in amina_coordination["action_href"]
    assert amina_coordination["urgency_score"] > 0
    digest_response = client.post(
        "/api/v1/safeguarding/my-family/coordination/digest",
        headers=guardian_identity_headers,
        json={
            "organization_id": onboarding["organization"]["id"],
            "channel": "in_app",
            "portal_url": "http://localhost:3000/family",
            "max_rows": 2,
        },
    )
    assert digest_response.status_code == 200
    digest = digest_response.json()
    assert digest["guardian_person_id"]
    assert digest["action_count"] >= 2
    assert digest["top_urgency_score"] >= amina_coordination["urgency_score"]
    assert digest["delivery_status"] == "delivered"
    assert "Amina Runner" in digest["body"]
    assert "Open the family portal: http://localhost:3000/family?organization_id=" in digest["body"]
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
    owner_ready_queue_response = client.get("/api/v1/organizations/registration-readiness", headers=identity_headers)
    assert owner_ready_queue_response.status_code == 200
    owner_ready_queue = owner_ready_queue_response.json()
    assert owner_ready_queue["admissions_inquiry_count"] == 3
    assert owner_ready_queue["admissions_ready_count"] == 1
    assert {step["key"]: step for step in owner_ready_queue["steps"]}["admissions"]["status"] == "ready"
    owner_ready_missions = {mission["key"]: mission for mission in owner_ready_queue["missions"]}
    assert owner_ready_missions["review_admissions"]["status"] == "complete"
    assert owner_ready_missions["review_admissions"]["progress_percent"] == 100

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

    agent_review_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/{inquiry['id']}/agent-review",
        headers=identity_headers,
    )
    assert agent_review_response.status_code == 201
    agent_review = agent_review_response.json()
    assert agent_review["task_type"] == "registration_inquiry_review"
    assert agent_review["title"] == "Review registration packet for Amina Runner"
    assert agent_review["input_ref"].startswith(f"registration-inquiry:{inquiry['id']};")
    assert "packet_complete:False" in agent_review["input_ref"]
    agent_review_run_response = client.post(
        f"/api/v1/agents/tasks/{agent_review['id']}/execute",
        headers=identity_headers,
    )
    assert agent_review_run_response.status_code == 200
    agent_review_run = agent_review_run_response.json()
    assert "Admissions Intake Agent prepared a deterministic admissions intake draft" in agent_review_run["review_notes"]
    assert "Payment is pending" in agent_review_run["review_notes"]
    assert "Packet is not complete" in agent_review_run["review_notes"]

    duplicate_agent_review_response = client.post(
        f"/api/v1/organizations/{onboarding['organization']['id']}/registration-inquiries/{inquiry['id']}/agent-review",
        headers=identity_headers,
    )
    assert duplicate_agent_review_response.status_code == 201
    assert duplicate_agent_review_response.json()["id"] == agent_review["id"]

    agent_tasks_response = client.get(
        f"/api/v1/agents/tasks?organization_id={onboarding['organization']['id']}",
        headers=identity_headers,
    )
    assert agent_tasks_response.status_code == 200
    agent_tasks_by_type = {task["task_type"]: task for task in agent_tasks_response.json()}
    assert agent_tasks_by_type["registration_inquiry_review"]["id"] == agent_review["id"]
    assert agent_tasks_by_type["organization_onboarding_concierge"]["id"] == onboarding["concierge_task"]["id"]
    assert agent_tasks_by_type["registration_launch_campaign"]["id"] == launch_agent_center["agent_task"]["id"]

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
    assert checkout["guardian_email"] == "parent.runner@example.com"
    assert checkout["public_registration_path"].startswith("/register?mode=player&site=makini-track")
    assert f"inquiry_id={inquiry['id']}" in checkout["public_registration_path"]
    assert checkout["family_portal_path"].startswith(f"/family?organization_id={onboarding['organization']['id']}")
    assert "autoload=1" in checkout["family_portal_path"]

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
    supporter_tier = client.post(
        "/api/v1/community/supporter-tiers",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Family Stand Member",
            "slug": "family-stand",
            "monthly_price": "5.00",
            "currency": "USD",
            "benefits": "Priority updates, supporter challenges, and family stand recognition.",
            "voting_weight": 2,
        },
    ).json()
    challenge = client.post(
        "/api/v1/community/fan-challenges",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "title": "Derby day voice",
            "description": "Join the fan zone and record matchday support.",
            "challenge_type": "matchday",
            "target_activity_type": "matchday_support",
            "target_count": 2,
            "points_reward": 500,
            "badge_name": "Derby Voice",
        },
    ).json()
    supporter_signup = client.post(
        "/api/v1/organizations/public/supporter-city/supporters",
        json={
            "tier_id": supporter_tier["id"],
            "display_name": "Sarah Stand",
            "email": "sarah.stand@example.com",
            "phone": "+254700000000",
            "interests": ["matchday", "challenges"],
            "message": "I want to support the youth academy.",
            "source_url": "https://supporter-city.example",
        },
    ).json()
    assert supporter_signup["signup_status"] == "created"
    assert supporter_signup["points_awarded"] == 100
    assert supporter_signup["tier_name"] == "Family Stand Member"

    in_progress = client.post(
        f"/api/v1/organizations/public/supporter-city/fan-challenges/{challenge['id']}/progress",
        json={"email": "sarah.stand@example.com", "progress_count": 1},
    ).json()
    assert in_progress["status"] == "in_progress"

    completed = client.post(
        f"/api/v1/organizations/public/supporter-city/fan-challenges/{challenge['id']}/progress",
        json={"email": "sarah.stand@example.com", "progress_count": 1},
    ).json()
    assert completed["status"] == "completed"
    assert completed["points_awarded"] == 500

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
    assert site["supporter_tiers"][0]["name"] == "Family Stand Member"
    assert site["fan_challenges"][0]["title"] == "Derby day voice"
    assert site["fan_challenges"][0]["completion_count"] == 1
    assert site["fan_leaderboard"][0]["supporter_name"] == "Sarah Stand"
    assert site["fan_leaderboard"][0]["engagement_points"] == 600
    assert site["fan_leaderboard"][0]["completed_challenge_count"] == 1


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
