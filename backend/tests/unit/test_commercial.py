import hmac
import json
import time
from hashlib import sha256
from types import SimpleNamespace

from app.services import commercial as commercial_service


def create_commercial_context(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Commercial Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Commercial U18",
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
            "title": "Commercial derby",
            "starts_at": "2026-06-20T15:00:00Z",
            "ends_at": "2026-06-20T17:00:00Z",
            "venue_name": "Revenue Park",
        },
    ).json()
    return organization, team, event


def test_financial_budget_planning_tracks_variance_cash_and_scenarios(client, identity_headers) -> None:
    organization, _, _ = create_commercial_context(client, identity_headers)

    budget_response = client.post(
        "/api/v1/commercial/budgets",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Club operating budget 2026",
            "fiscal_year": 2026,
            "period_start": "2026-01-01",
            "period_end": "2026-12-31",
            "budget_type": "operating",
            "scope_type": "organization",
            "currency": "KES",
            "beginning_cash_balance": "45000.00",
            "minimum_cash_reserve": "20000.00",
            "assumptions": ["Membership growth 12%", "Sponsor renewals on time"],
            "status": "active",
        },
    )
    assert budget_response.status_code == 201
    budget = budget_response.json()
    assert budget["currency"] == "KES"
    assert budget["assumptions"] == ["Membership growth 12%", "Sponsor renewals on time"]

    revenue_response = client.post(
        "/api/v1/commercial/budgets/lines",
        headers=identity_headers,
        json={
            "budget_id": budget["id"],
            "line_type": "revenue",
            "category": "Membership dues",
            "department": "Membership",
            "amount_budgeted": "90000.00",
            "amount_actual": "92450.00",
            "forecast_amount": "99000.00",
            "cash_timing_month": "2026-03",
            "funding_source": "member_dues",
        },
    )
    assert revenue_response.status_code == 201
    assert revenue_response.json()["variance_amount"] == "2450.00"

    expense_response = client.post(
        "/api/v1/commercial/budgets/lines",
        headers=identity_headers,
        json={
            "budget_id": budget["id"],
            "line_type": "expense",
            "category": "Travel",
            "department": "Competition",
            "amount_budgeted": "25000.00",
            "amount_actual": "26800.00",
            "forecast_amount": "30000.00",
            "cash_timing_month": "2026-04",
            "variance_reason": "Regional finals required an additional away trip.",
        },
    )
    assert expense_response.status_code == 201
    assert expense_response.json()["variance_amount"] == "-1800.00"

    scenario_response = client.post(
        "/api/v1/commercial/budgets/scenarios",
        headers=identity_headers,
        json={
            "budget_id": budget["id"],
            "name": "New training facility conservative",
            "scenario_type": "conservative",
            "revenue_adjustment_percent": "15.00",
            "expense_adjustment_percent": "28.00",
            "cash_adjustment_amount": "-10000.00",
            "membership_growth_percent": "15.00",
            "facility_utilization_percent": "62.50",
            "assumptions": ["One new team", "Moderate rental demand"],
        },
    )
    assert scenario_response.status_code == 201
    scenario = scenario_response.json()
    assert scenario["projected_revenue"] == "113850.00"
    assert scenario["projected_expense"] == "38400.00"
    assert "facility utilization" in scenario["sensitivity_rank"]

    list_response = client.get(
        f"/api/v1/commercial/budgets?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["line_count"] == 2

    summary_response = client.get(
        f"/api/v1/commercial/budgets/{budget['id']}/summary?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["budgeted_revenue"] == "90000.00"
    assert summary["actual_revenue"] == "92450.00"
    assert summary["budgeted_expense"] == "25000.00"
    assert summary["actual_expense"] == "26800.00"
    assert summary["actual_net_income"] == "65650.00"
    assert summary["ending_cash_position"] == "110650.00"
    assert summary["cash_buffer"] == "90650.00"
    assert summary["variance_alert_count"] == 0
    assert summary["scenario_count"] == 1
    assert summary["scenarios"][0]["name"] == "New training facility conservative"


def test_donor_crm_tracks_lifetime_giving_touchpoints_and_stewardship(client, identity_headers) -> None:
    organization, team, _ = create_commercial_context(client, identity_headers)

    campaign = client.post(
        "/api/v1/commercial/campaigns",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "name": "Facility access fund",
            "purpose": "Subsidize training access and equipment",
            "goal_amount": "10000.00",
            "currency": "KES",
        },
    ).json()

    donation_response = client.post(
        "/api/v1/commercial/donations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "campaign_id": campaign["id"],
            "donor_name": "Community Donor",
            "donor_email": "donor@example.com",
            "amount": "1250.00",
            "currency": "KES",
            "external_reference": "MPESA-DONOR-1",
            "message": "For the facility project.",
        },
    )
    assert donation_response.status_code == 201
    donation = donation_response.json()
    assert donation["donor_profile_id"]

    donors_response = client.get(
        f"/api/v1/commercial/donors?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert donors_response.status_code == 200
    donor = donors_response.json()[0]
    assert donor["email"] == "donor@example.com"
    assert donor["lifetime_giving"] == "1250.00"
    assert donor["donation_count"] == 1

    interaction_response = client.post(
        "/api/v1/commercial/donor-interactions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "donor_profile_id": donor["id"],
            "campaign_id": campaign["id"],
            "interaction_type": "impact_update",
            "channel": "email",
            "subject": "Facility access impact story",
            "summary": "Shared photos and scholarship participation metrics.",
            "sentiment": "positive",
            "outcome": "ready_for_visit",
            "owner_name": "Fundraising Lead",
            "next_follow_up_on": "2026-07-15",
            "status": "follow_up_due",
        },
    )
    assert interaction_response.status_code == 201
    assert interaction_response.json()["campaign_name"] == "Facility access fund"

    plan_response = client.post(
        "/api/v1/commercial/donor-stewardship-plans",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "donor_profile_id": donor["id"],
            "name": "Facility campaign stewardship",
            "stage": "cultivation",
            "priority": "high",
            "target_amount": "2500.00",
            "due_on": "2026-07-30",
            "next_step": "Invite donor to visit the facility project.",
            "recognition_level": "Founding supporter",
            "impact_story_needed": True,
            "owner_name": "Fundraising Lead",
        },
    )
    assert plan_response.status_code == 201
    plan = plan_response.json()
    assert plan["donor_name"] == "Community Donor"
    assert plan["impact_story_needed"] is True

    dashboard_response = client.get(
        f"/api/v1/commercial/donor-dashboard?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["donor_count"] == 1
    assert dashboard["major_donor_count"] == 1
    assert dashboard["lifetime_giving"] == "1250.00"
    assert dashboard["active_plan_count"] == 1
    assert dashboard["impact_story_needed_count"] == 1

    complete_response = client.patch(
        f"/api/v1/commercial/donor-stewardship-plans/{plan['id']}/complete?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"


def test_financial_statement_package_generates_pl_balance_sheet_and_cash_flow(client, identity_headers) -> None:
    organization, team, event = create_commercial_context(client, identity_headers)

    sponsor = client.post(
        "/api/v1/commercial/sponsors",
        headers=identity_headers,
        json={"organization_id": organization["id"], "name": "Board Sponsor", "contact_email": "board@example.com"},
    ).json()
    client.post(
        "/api/v1/commercial/sponsorships",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "event_id": event["id"],
            "name": "June sponsor",
            "tier": "Gold",
            "value_amount": "5000.00",
            "starts_on": "2026-06-01",
            "ends_on": "2026-06-30",
        },
    )
    campaign = client.post(
        "/api/v1/commercial/campaigns",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "name": "June appeal",
            "purpose": "Scholarship access",
            "goal_amount": "10000.00",
        },
    ).json()
    client.post(
        "/api/v1/commercial/donations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "campaign_id": campaign["id"],
            "donor_name": "Statement Donor",
            "donor_email": "statement@example.com",
            "amount": "1200.00",
        },
    )
    ticket_product = client.post(
        "/api/v1/commercial/tickets/products",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "event_id": event["id"],
            "name": "June match",
            "price": "100.00",
            "capacity": 100,
        },
    ).json()
    client.post(
        "/api/v1/commercial/tickets/orders",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "ticket_product_id": ticket_product["id"],
            "buyer_name": "Family Fan",
            "buyer_email": "fan@example.com",
            "quantity": 3,
        },
    )
    invoice = client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "invoice_number": "STATEMENT-1",
            "title": "Training services",
            "amount_due": "800.00",
            "due_on": "2026-06-15",
        },
    ).json()
    client.post(
        "/api/v1/commercial/payments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "invoice_id": invoice["id"],
            "amount": "500.00",
            "method": "bank_transfer",
        },
    )
    budget = client.post(
        "/api/v1/commercial/budgets",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "June operating budget",
            "fiscal_year": 2026,
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "currency": "USD",
            "status": "active",
        },
    ).json()
    client.post(
        "/api/v1/commercial/budgets/lines",
        headers=identity_headers,
        json={
            "budget_id": budget["id"],
            "line_type": "expense",
            "category": "Travel",
            "amount_budgeted": "700.00",
            "amount_actual": "650.00",
            "restricted": True,
        },
    )

    statement_response = client.post(
        "/api/v1/commercial/financial-statements",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "period_start": "2026-05-01",
            "period_end": "2026-06-30",
            "statement_type": "monthly",
            "basis": "management",
            "currency": "USD",
            "prepared_by_name": "Treasurer",
        },
    )
    assert statement_response.status_code == 201
    statement = statement_response.json()
    assert statement["total_revenue"] == "7300.00"
    assert statement["total_expense"] == "650.00"
    assert statement["net_income"] == "6650.00"
    assert statement["ending_cash"] == "1350.00"
    assert statement["net_cash_change"] == "1350.00"
    assert any(line["label"] == "Accounts receivable" and line["amount"] == "300.00" for line in statement["balance_sheet"])
    assert len(statement["profit_loss"]) >= 5
    assert statement["highlights"]

    list_response = client.get(
        f"/api/v1/commercial/financial-statements?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == statement["id"]


def test_grant_application_internal_approval_workflow(client, identity_headers) -> None:
    organization, _, _ = create_commercial_context(client, identity_headers)

    opportunity = client.post(
        "/api/v1/commercial/grants/opportunities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "funder_name": "Youth Sport Foundation",
            "program_name": "Access Grant",
            "category": "youth_development",
            "impact_area": "Scholarship access",
            "award_ceiling": "25000.00",
            "matching_required": "2500.00",
            "due_on": "2026-08-01",
        },
    ).json()
    application = client.post(
        "/api/v1/commercial/grants/applications",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "grant_opportunity_id": opportunity["id"],
            "project_title": "Scholarship expansion",
            "requested_amount": "18000.00",
            "status": "draft",
            "narrative": "Expand access to training and travel support.",
            "budget_summary": "Scholarship awards, coach education, travel.",
            "impact_metrics": "50 athletes served.",
        },
    ).json()
    assert application["approval_status"] == "not_requested"

    approval_response = client.post(
        "/api/v1/commercial/grants/application-approvals",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "grant_application_id": application["id"],
            "approval_level": "board",
            "reviewer_name": "Board Treasurer",
            "reviewer_email": "treasurer@example.com",
            "request_notes": "Confirm matching funds and safeguarding requirements before submission.",
        },
    )
    assert approval_response.status_code == 201
    approval = approval_response.json()
    assert approval["status"] == "pending"
    assert approval["project_title"] == "Scholarship expansion"

    applications = client.get(
        f"/api/v1/commercial/grants/applications?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert applications[0]["approval_status"] == "pending"
    assert applications[0]["approval_pending_count"] == 1

    decided_response = client.patch(
        f"/api/v1/commercial/grants/application-approvals/{approval['id']}",
        headers=identity_headers,
        json={"status": "approved", "decision_notes": "Board approves match funding and submission."},
    )
    assert decided_response.status_code == 200
    decided = decided_response.json()
    assert decided["status"] == "approved"
    assert decided["decided_at"] is not None

    applications = client.get(
        f"/api/v1/commercial/grants/applications?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert applications[0]["status"] == "approved_for_submission"
    assert applications[0]["approval_status"] == "approved"
    assert applications[0]["approval_approved_count"] == 1

    package_response = client.post(
        "/api/v1/commercial/grants/submission-packages",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "grant_application_id": application["id"],
            "package_name": "Foundation portal package",
            "submission_method": "online_portal",
            "portal_url": "https://grants.example/submit",
            "checklist_items": [
                "Board approval secured",
                "Budget attached",
                "Impact metrics attached",
            ],
            "completed_checklist_items": [
                "Board approval secured",
                "Budget attached",
                "Impact metrics attached",
            ],
            "document_manifest": [
                "application.pdf",
                "budget.xlsx",
                "safeguarding-policy.pdf",
            ],
            "prepared_by_name": "Grant Manager",
            "status": "submitted",
            "confirmation_reference": "YSF-2026-00042",
            "notes": "Submitted through funder portal after board approval.",
        },
    )
    assert package_response.status_code == 201
    submission_package = package_response.json()
    assert submission_package["status"] == "submitted"
    assert submission_package["ready_to_submit"] is True
    assert submission_package["checklist_completed_count"] == 3
    assert submission_package["document_count"] == 3
    assert submission_package["submitted_at"] is not None
    assert submission_package["approval_status"] == "approved"

    confirmed_response = client.patch(
        f"/api/v1/commercial/grants/submission-packages/{submission_package['id']}",
        headers=identity_headers,
        json={
            "status": "confirmed",
            "confirmation_reference": "YSF-CONFIRMED-00042",
            "completed_checklist_items": submission_package["completed_checklist_items"],
            "blockers": [],
            "notes": "Funder portal confirmed receipt.",
        },
    )
    assert confirmed_response.status_code == 200
    confirmed = confirmed_response.json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["confirmed_at"] is not None
    assert confirmed["confirmation_reference"] == "YSF-CONFIRMED-00042"

    packages = client.get(
        f"/api/v1/commercial/grants/submission-packages?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert packages[0]["id"] == submission_package["id"]
    assert packages[0]["project_title"] == "Scholarship expansion"

    for payload in [
        {
            "record_type": "payment",
            "title": "Initial award payment",
            "amount": "25000.00",
            "category": "disbursement",
            "occurred_on": "2026-03-01",
            "status": "received",
            "external_reference": "PAY-001",
        },
        {
            "record_type": "expenditure",
            "title": "Coach education expenses",
            "amount": "15200.00",
            "category": "coach_education",
            "occurred_on": "2026-04-15",
            "status": "paid",
            "evidence_url": "https://files.example/receipt.pdf",
        },
        {
            "record_type": "compliance",
            "title": "Progress photos due",
            "amount": "0.00",
            "category": "monthly_evidence",
            "due_on": "2026-01-31",
            "status": "planned",
            "requirement": "Upload monthly progress photos.",
        },
        {
            "record_type": "milestone",
            "title": "Coach cohort launched",
            "amount": "0.00",
            "category": "program_delivery",
            "due_on": "2026-04-30",
            "occurred_on": "2026-04-20",
            "status": "completed",
        },
    ]:
        response = client.post(
            "/api/v1/commercial/grants/award-records",
            headers=identity_headers,
            json={
                "organization_id": organization["id"],
                "grant_application_id": application["id"],
                **payload,
            },
        )
        assert response.status_code == 201

    award_records = client.get(
        f"/api/v1/commercial/grants/award-records?organization_id={organization['id']}&grant_application_id={application['id']}",
        headers=identity_headers,
    ).json()
    assert len(award_records) == 4
    assert any(record["record_type"] == "compliance" and record["overdue"] for record in award_records)

    award_summary = client.get(
        f"/api/v1/commercial/grants/award-summary?organization_id={organization['id']}&grant_application_id={application['id']}",
        headers=identity_headers,
    ).json()
    assert award_summary["funds_received"] == "25000.00"
    assert award_summary["expenditures_to_date"] == "15200.00"
    assert award_summary["funds_balance"] == "9800.00"
    assert award_summary["compliance_open_count"] == 1
    assert award_summary["milestone_completed_count"] == 1
    assert award_summary["overdue_count"] == 1
    assert award_summary["health"] == "attention_required"


def test_commercial_finance_settlement_refund_tax_accounting_and_sponsor_dashboard(
    client,
    identity_headers,
) -> None:
    organization, team, event = create_commercial_context(client, identity_headers)

    sponsor = client.post(
        "/api/v1/commercial/sponsors",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Acme Sports",
            "industry": "Retail",
            "contact_email": "sponsor@example.com",
        },
    ).json()
    agreement = client.post(
        "/api/v1/commercial/sponsorships",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "event_id": event["id"],
            "name": "Derby Partner",
            "tier": "Gold",
            "value_amount": "1000.00",
            "deliverables": "Shirt logo, pitch board, newsletter mention",
            "activation_notes": "Coupon campaign launched.",
        },
    ).json()
    assert agreement["status"] == "active"

    activation = client.post(
        "/api/v1/commercial/sponsor-activations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "sponsorship_agreement_id": agreement["id"],
            "title": "Acme matchday coupon",
            "objective": "Track sponsor-driven store and ticket conversion.",
            "offer_summary": "10% off sponsor merchandise and matchday purchases.",
            "coupon_code": " acme derby 10 ",
            "discount_type": "percent",
            "discount_value": "10.00",
            "target_url": "https://shop.example/acme-derby",
        },
    ).json()
    assert activation["coupon_code"] == "ACME-DERBY-10"
    assert activation["sponsor_name"] == "Acme Sports"

    redemption = client.post(
        "/api/v1/commercial/sponsor-coupon-redemptions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "coupon_code": "acme derby 10",
            "redeemer_name": "Family Fan",
            "redeemer_email": "FAMILY@example.com",
            "source": "matchday_store",
            "order_reference": "ORDER-ACME-1",
            "discount_amount": "8.00",
            "purchase_amount": "80.00",
        },
    ).json()
    assert redemption["coupon_code"] == "ACME-DERBY-10"
    assert redemption["redeemer_email"] == "family@example.com"
    assert redemption["purchase_amount"] == "80.00"

    activation_dashboard = client.get(
        f"/api/v1/commercial/sponsor-activation-dashboard?organization_id={organization['id']}"
    ).json()
    assert activation_dashboard["campaign_count"] == 1
    assert activation_dashboard["active_campaign_count"] == 1
    assert activation_dashboard["total_redemptions"] == 1
    assert activation_dashboard["conversion_value"] == "80.00"
    assert activation_dashboard["top_coupon_code"] == "ACME-DERBY-10"
    assert activation_dashboard["roi_signal"] == "building"

    content_asset = client.post(
        "/api/v1/commercial/sponsor-content-assets",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "sponsorship_agreement_id": agreement["id"],
            "title": "Acme scoreboard overlay",
            "asset_type": "digital_signage",
            "channel": "scoreboard",
            "format": "16:9",
            "asset_url": "https://assets.example/acme-scoreboard.png",
            "usage_guidelines": "Show before kickoff and at halftime.",
            "rights_summary": "No athlete likeness in this version.",
            "player_rights_required": False,
        },
    ).json()
    assert content_asset["approval_status"] == "pending_review"
    assert content_asset["sponsor_name"] == "Acme Sports"

    approval = client.post(
        "/api/v1/commercial/sponsor-content-approvals",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "content_asset_id": content_asset["id"],
            "reviewer_name": "Commercial Manager",
            "reviewer_email": "commercial@example.com",
            "decision": "approved",
            "notes": "Brand-safe and rights-cleared for matchday rotation.",
        },
    ).json()
    assert approval["decision"] == "approved"
    assert approval["content_title"] == "Acme scoreboard overlay"

    placement = client.post(
        "/api/v1/commercial/sponsor-placements",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "content_asset_id": content_asset["id"],
            "activation_campaign_id": activation["id"],
            "event_id": event["id"],
            "placement_name": "Main entrance and scoreboard rotation",
            "placement_type": "venue_zone",
            "channel": "event_day",
            "location_name": "Main gate",
            "staff_requirements": "2 setup crew and 1 photographer.",
            "inventory_checklist": "Banner, QR posters, product samples.",
            "weather_contingency": "Move sampling table under covered concourse.",
            "expected_impressions": 2500,
        },
    ).json()
    assert placement["content_title"] == "Acme scoreboard overlay"
    assert placement["campaign_title"] == "Acme matchday coupon"
    assert placement["event_title"] == "Commercial derby"
    assert placement["expected_impressions"] == 2500

    content_dashboard = client.get(
        f"/api/v1/commercial/sponsor-content-dashboard?organization_id={organization['id']}"
    ).json()
    assert content_dashboard["asset_count"] == 1
    assert content_dashboard["approved_asset_count"] == 1
    assert content_dashboard["placement_count"] == 1
    assert content_dashboard["total_expected_impressions"] == 2500

    signage_playlist = client.get(
        (
            f"/api/v1/commercial/sponsor-digital-signage-playlist?organization_id={organization['id']}"
            "&screen_name=Main%20scoreboard&location_name=Main&slot_count=3&slot_seconds=10"
        ),
        headers=identity_headers,
    ).json()
    assert signage_playlist["screen_name"] == "Main scoreboard"
    assert signage_playlist["slot_count"] == 3
    assert signage_playlist["total_duration_seconds"] == 30
    assert signage_playlist["approved_slot_count"] == 3
    assert signage_playlist["review_required_count"] == 0
    assert signage_playlist["items"][0]["content_title"] == "Acme scoreboard overlay"
    assert signage_playlist["items"][0]["coupon_code"] == "ACME-DERBY-10"
    assert signage_playlist["items"][0]["rights_status"] == "cleared"
    assert signage_playlist["items"][0]["asset_url"] == "https://assets.example/acme-scoreboard.png"

    playback = client.post(
        "/api/v1/commercial/sponsor-digital-signage-playback",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "placement_id": signage_playlist["items"][0]["placement_id"],
            "content_asset_id": signage_playlist["items"][0]["content_asset_id"],
            "activation_campaign_id": activation["id"],
            "screen_name": "Main scoreboard",
            "device_id": "scoreboard-01",
            "slot_index": 1,
            "duration_seconds": 10,
            "estimated_impressions": 420,
            "engagements": 17,
            "evidence_ref": "screen-player://scoreboard-01/playbacks/1",
        },
    ).json()
    assert playback["placement"]["actual_impressions"] == 420
    assert playback["placement"]["actual_engagements"] == 17
    assert playback["content_asset"]["impression_count"] == 420
    assert playback["content_asset"]["engagement_count"] == 17
    assert playback["activation_campaign"]["impression_count"] == 420
    assert playback["activation_campaign"]["signup_count"] == 17

    content_assets = client.get(
        f"/api/v1/commercial/sponsor-content-assets?organization_id={organization['id']}"
    ).json()
    assert content_assets[0]["usage_count"] == 1
    assert content_assets[0]["approval_status"] == "approved"
    assert content_assets[0]["impression_count"] == 420

    milestone = client.post(
        "/api/v1/commercial/sponsorship-milestones",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "sponsorship_agreement_id": agreement["id"],
            "title": "Post-match sponsor ROI packet",
            "deliverable_type": "reporting",
            "due_on": "2026-06-30",
            "status": "completed",
            "completed_on": "2026-06-25",
            "owner_name": "Commercial Manager",
            "evidence_url": "https://reports.example/acme-roi",
            "notes": "Includes coupon redemptions, content placement, and event photos.",
        },
    ).json()
    assert milestone["sponsor_name"] == "Acme Sports"
    assert milestone["agreement_name"] == "Derby Partner"
    assert milestone["status"] == "completed"

    interaction = client.post(
        "/api/v1/commercial/sponsor-interactions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "sponsorship_agreement_id": agreement["id"],
            "contact_name": "Alex Sponsor",
            "contact_email": "SPONSOR@example.com",
            "interaction_type": "review_call",
            "subject": "Activation results review",
            "summary": "Sponsor was happy with the coupon conversion and requested renewal options.",
            "sentiment": "renewal_ready",
            "follow_up_on": "2026-07-05",
        },
    ).json()
    assert interaction["contact_email"] == "sponsor@example.com"
    assert interaction["agreement_name"] == "Derby Partner"

    stewardship_dashboard = client.get(
        f"/api/v1/commercial/sponsor-stewardship-dashboard?organization_id={organization['id']}"
    ).json()
    assert stewardship_dashboard["milestone_count"] == 1
    assert stewardship_dashboard["interaction_count"] == 1
    assert stewardship_dashboard["forecasts"][0]["sponsor_name"] == "Acme Sports"
    assert stewardship_dashboard["forecasts"][0]["completed_milestone_count"] == 1
    assert stewardship_dashboard["forecasts"][0]["renewal_signal"] in {"nurture", "renewal_ready"}

    activation_list = client.get(
        f"/api/v1/commercial/sponsor-activations?organization_id={organization['id']}"
    ).json()
    assert activation_list[0]["redemption_count"] == 1

    redemption_list = client.get(
        f"/api/v1/commercial/sponsor-coupon-redemptions?organization_id={organization['id']}"
    ).json()
    assert redemption_list[0]["order_reference"] == "ORDER-ACME-1"

    campaign = client.post(
        "/api/v1/commercial/campaigns",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "name": "Travel fund",
            "purpose": "Tournament travel",
            "goal_amount": "500.00",
        },
    ).json()
    donation = client.post(
        "/api/v1/commercial/donations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "campaign_id": campaign["id"],
            "donor_name": "Donor Example",
            "amount": "50.00",
            "external_reference": "DON-1",
        },
    ).json()
    assert donation["status"] == "paid"

    opportunity = client.post(
        "/api/v1/commercial/grants/opportunities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "funder_name": "Youth Sport Foundation",
            "program_name": "Community Coaching Grant",
            "category": "youth_development",
            "impact_area": "Coach education and athlete access",
            "award_ceiling": "25000.00",
            "matching_required": "2500.00",
            "currency": "USD",
            "opens_on": "2026-05-01",
            "due_on": "2026-06-15",
            "eligibility_summary": "Registered youth clubs with safeguarding policies.",
            "requirements": "Board approval, budget, impact plan, and reporting calendar.",
            "source_url": "https://grants.example/community-coaching",
        },
    ).json()
    assert opportunity["status"] == "open"
    assert opportunity["award_ceiling"] == "25000.00"

    application = client.post(
        "/api/v1/commercial/grants/applications",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "grant_opportunity_id": opportunity["id"],
            "project_title": "Community coaching access",
            "requested_amount": "18000.00",
            "awarded_amount": "12000.00",
            "currency": "USD",
            "status": "awarded",
            "submitted_on": "2026-06-01",
            "decision_on": "2026-06-20",
            "reporting_due_on": "2026-09-30",
            "narrative": "Train volunteer coaches and subsidize athlete participation.",
            "budget_summary": "Coaching education, equipment, travel, and safeguarding.",
            "impact_metrics": "60 athletes served, 12 coaches certified.",
            "external_reference": "YSF-2026-001",
        },
    ).json()
    assert application["funder_name"] == "Youth Sport Foundation"
    assert application["program_name"] == "Community Coaching Grant"
    assert application["status"] == "awarded"

    grant_report = client.post(
        "/api/v1/commercial/grants/reports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "grant_application_id": application["id"],
            "report_type": "quarterly",
            "due_on": "2026-09-30",
            "status": "draft",
            "narrative": "Early coach certification milestones are on track.",
            "metrics_summary": "24 athletes enrolled; 5 coaches completed safeguarding.",
            "artifact_url": "https://storage.example/grants/q1.pdf",
            "external_reference": "YSF-Q1",
        },
    ).json()
    assert grant_report["project_title"] == "Community coaching access"
    assert grant_report["status"] == "draft"

    grant_dashboard = client.get(
        f"/api/v1/commercial/grants/dashboard?organization_id={organization['id']}"
    ).json()
    assert grant_dashboard["opportunity_count"] == 1
    assert grant_dashboard["application_count"] == 1
    assert grant_dashboard["awarded_application_count"] == 1
    assert grant_dashboard["report_count"] == 1
    assert grant_dashboard["requested_amount"] == "18000.00"
    assert grant_dashboard["awarded_amount"] == "12000.00"
    assert grant_dashboard["match_required_amount"] == "2500.00"
    assert grant_dashboard["pipeline_status"] in {"ready", "attention"}
    assert grant_dashboard["recommendations"]

    merchandise_product = client.post(
        "/api/v1/commercial/merchandise/products",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "name": "Home jersey",
            "sku": "HOME-JERSEY-2026",
            "category": "jersey",
            "description": "Replica home jersey with optional player name and number.",
            "price": "45.00",
            "cost": "22.00",
            "currency": "USD",
            "inventory_count": 12,
            "reorder_point": 5,
            "personalization_enabled": True,
            "variants": "Youth S, Youth M, Youth L, Adult S, Adult M",
            "image_url": "https://store.example/home-jersey.png",
        },
    ).json()
    assert merchandise_product["status"] == "active"
    assert merchandise_product["inventory_count"] == 12

    merchandise_order = client.post(
        "/api/v1/commercial/merchandise/orders",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "buyer_name": "Family Buyer",
            "buyer_email": "family@example.com",
            "delivery_method": "pickup",
            "external_payment_reference": "MERCH-1",
            "notes": "Pick up at Saturday match.",
            "lines": [
                {
                    "merchandise_product_id": merchandise_product["id"],
                    "quantity": 2,
                    "size": "Youth M",
                    "color": "Green",
                    "personalization_name": "Amina",
                    "personalization_number": "10",
                }
            ],
        },
    ).json()
    assert merchandise_order["total_amount"] == "90.00"
    assert merchandise_order["fulfillment_status"] == "queued"
    assert merchandise_order["lines"][0]["product_name"] == "Home jersey"
    assert merchandise_order["lines"][0]["line_total"] == "90.00"

    merchandise_products = client.get(
        f"/api/v1/commercial/merchandise/products?organization_id={organization['id']}"
    ).json()
    assert merchandise_products[0]["inventory_count"] == 10

    fulfilled_order = client.patch(
        f"/api/v1/commercial/merchandise/orders/{merchandise_order['id']}/fulfillment",
        headers=identity_headers,
        json={"fulfillment_status": "fulfilled", "notes": "Packed and picked up."},
    ).json()
    assert fulfilled_order["fulfillment_status"] == "fulfilled"
    assert fulfilled_order["fulfilled_at"] is not None
    assert fulfilled_order["lines"][0]["fulfillment_status"] == "fulfilled"

    merchandise_dashboard = client.get(
        f"/api/v1/commercial/merchandise/dashboard?organization_id={organization['id']}"
    ).json()
    assert merchandise_dashboard["product_count"] == 1
    assert merchandise_dashboard["order_count"] == 1
    assert merchandise_dashboard["fulfilled_order_count"] == 1
    assert merchandise_dashboard["units_sold"] == 2
    assert merchandise_dashboard["gross_revenue"] == "90.00"
    assert merchandise_dashboard["estimated_margin"] == "46.00"

    product = client.post(
        "/api/v1/commercial/tickets/products",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "event_id": event["id"],
            "name": "General Admission",
            "price": "10.00",
            "capacity": 20,
        },
    ).json()
    order = client.post(
        "/api/v1/commercial/tickets/orders",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "ticket_product_id": product["id"],
            "buyer_name": "Buyer Example",
            "buyer_email": "buyer@example.com",
            "quantity": 2,
            "external_payment_reference": "PAY-1",
        },
    ).json()
    ticket_id = order["ticket_ids"][0]

    bundle = client.post(
        "/api/v1/commercial/tickets/bundles",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "event_id": event["id"],
            "ticket_product_id": product["id"],
            "merchandise_product_id": merchandise_product["id"],
            "name": "Family derby pack",
            "package_type": "family_merch_bundle",
            "ticket_quantity": 4,
            "price": "55.00",
            "channel": "public_site",
            "sales_limit": 25,
        },
    ).json()
    assert bundle["ticket_product_name"] == "General Admission"
    assert bundle["merchandise_product_name"] == "Home jersey"
    assert bundle["status"] == "active"

    complimentary = client.post(
        "/api/v1/commercial/tickets/complimentary",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "ticket_product_id": product["id"],
            "recipient_name": "Media Guest",
            "recipient_email": "MEDIA@example.com",
            "quantity": 1,
            "reason": "media",
            "sponsor_id": sponsor["id"],
        },
    ).json()
    assert complimentary["total_amount"] == "0.00"
    assert complimentary["buyer_email"] == "media@example.com"
    assert len(complimentary["ticket_ids"]) == 1

    seat = client.post(
        "/api/v1/commercial/tickets/seats",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "ticket_id": ticket_id,
            "section": "East Stand",
            "row": "A",
            "seat": "12",
            "access_zone": "Main gate",
            "accessible": True,
            "companion_seat": True,
        },
    ).json()
    assert seat["section"] == "East Stand"
    assert seat["accessible"] is True
    assert seat["holder_name"] == "Buyer Example"

    resale_listing = client.post(
        "/api/v1/commercial/tickets/resale-listings",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "ticket_id": ticket_id,
            "seller_name": "Buyer Example",
            "seller_email": "BUYER@example.com",
            "resale_price": "8.00",
            "currency": "USD",
            "notes": "Family cannot attend.",
        },
    ).json()
    assert resale_listing["status"] == "listed"
    assert resale_listing["seller_email"] == "buyer@example.com"

    resale_purchase = client.post(
        f"/api/v1/commercial/tickets/resale-listings/{resale_listing['id']}/purchase",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "buyer_name": "Second Buyer",
            "buyer_email": "SECOND@example.com",
        },
    ).json()
    assert resale_purchase["status"] == "sold"
    assert resale_purchase["buyer_email"] == "second@example.com"

    access_dashboard = client.get(
        f"/api/v1/commercial/tickets/access-dashboard?organization_id={organization['id']}"
    ).json()
    assert access_dashboard["ticket_product_count"] == 1
    assert access_dashboard["ticket_count"] == 3
    assert access_dashboard["complimentary_count"] == 1
    assert access_dashboard["assigned_seat_count"] == 1
    assert access_dashboard["accessible_seat_count"] == 1
    assert access_dashboard["resale_sold_count"] == 1
    assert access_dashboard["package_offer_count"] == 1

    invoice = client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "sponsor_id": sponsor["id"],
            "invoice_number": "INV-1",
            "title": "Sponsor activation",
            "amount_due": "100.00",
            "due_on": "2026-06-30",
        },
    ).json()
    payment = client.post(
        "/api/v1/commercial/payments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "invoice_id": invoice["id"],
            "amount": "80.00",
            "method": "card",
            "external_reference": "RCPT-1",
        },
    ).json()
    assert payment["amount"] == "80.00"

    tax = client.get(
        "/api/v1/commercial/tax-quote",
        params={
            "organization_id": organization["id"],
            "subtotal": "100.00",
            "tax_rate": "16.00",
            "jurisdiction": "KE",
        },
    ).json()
    assert tax["tax_amount"] == "16.00"
    assert tax["total"] == "116.00"
    filing = client.post(
        "/api/v1/commercial/tax-filing/deliver",
        headers=identity_headers,
        params={
            "organization_id": organization["id"],
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "jurisdiction": "KE",
            "tax_rate": "16.00",
        },
    ).json()
    assert filing["delivery_mode"] == "record_only"
    assert filing["delivered"] is False
    assert filing["invoice_count"] == 1
    assert filing["taxable_subtotal"] == "100.00"
    assert filing["tax_amount"] == "16.00"
    assert filing["filing_reference"].startswith("COMTAX-KE-")

    settlement = client.get(
        "/api/v1/commercial/settlements",
        params={
            "organization_id": organization["id"],
            "provider": "manual_gateway",
            "fee_rate": "3.00",
            "fixed_fee": "0.00",
        },
    ).json()
    assert settlement["gross_amount"] == "150.00"
    assert settlement["net_amount"] == "145.50"

    payout = client.post(
        "/api/v1/commercial/settlements/payout",
        headers=identity_headers,
        params={
            "organization_id": organization["id"],
            "provider": "manual_gateway",
            "fee_rate": "3.00",
            "fixed_fee": "0.00",
        },
    ).json()
    assert payout["delivery_mode"] == "record_only"
    assert payout["delivered"] is False
    assert payout["gross_amount"] == "150.00"
    assert payout["net_amount"] == "145.50"
    assert payout["payout_batch_reference"].startswith("payout_manual_gateway_")

    ticket_refund = client.post(
        f"/api/v1/commercial/tickets/{ticket_id}/refund",
        headers=identity_headers,
        json={"reason": "Fan requested refund."},
    )
    assert ticket_refund.status_code == 200
    assert ticket_refund.json()["amount"] == "10.00"

    invoice_refund = client.post(
        f"/api/v1/commercial/invoices/{invoice['id']}/refund",
        headers=identity_headers,
        json={"amount": "30.00", "reason": "Partial sponsor credit."},
    )
    assert invoice_refund.status_code == 200
    assert invoice_refund.json()["amount"] == "30.00"

    export = client.get(
        "/api/v1/commercial/accounting-export",
        params={"organization_id": organization["id"], "system": "quickbooks", "basis": "cash"},
    ).json()
    assert export["system"] == "quickbooks"
    assert len(export["rows"]) >= 3
    assert export["credit_total"] >= "130.00"
    sync = client.post(
        "/api/v1/commercial/accounting-export/sync",
        headers=identity_headers,
        params={"organization_id": organization["id"], "system": "quickbooks", "basis": "cash"},
    ).json()
    assert sync["mode"] == "record_only"
    assert sync["delivered"] is False
    assert sync["row_count"] == len(export["rows"])
    assert sync["sync_reference"].startswith("acct_quickbooks_cash_")

    dashboard = client.get(
        f"/api/v1/commercial/sponsorship-dashboard?organization_id={organization['id']}"
    ).json()
    assert dashboard[0]["sponsor_name"] == "Acme Sports"
    assert dashboard[0]["deliverable_count"] == 3
    assert dashboard[0]["activation_count"] == 2
    assert dashboard[0]["roi_score"] >= 85


def test_sponsor_contact_can_open_self_service_portal(client, identity_headers) -> None:
    organization, team, event = create_commercial_context(client, identity_headers)
    sponsor = client.post(
        "/api/v1/commercial/sponsors",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Portal Partner",
            "industry": "Healthcare",
            "contact_name": "Sam Sponsor",
            "contact_email": "portal-sponsor@example.com",
            "website_url": "https://portal-sponsor.example",
        },
    ).json()
    client.post(
        "/api/v1/commercial/sponsorships",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "sponsor_id": sponsor["id"],
            "event_id": event["id"],
            "name": "Match Health Partner",
            "tier": "Silver",
            "value_amount": "750.00",
            "deliverables": "Medical tent, player recovery report",
            "activation_notes": "Sideline clinic scheduled.",
        },
    )
    invoice = client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "sponsor_id": sponsor["id"],
            "invoice_number": "SPONSOR-1",
            "title": "Match Health Partner",
            "amount_due": "500.00",
            "memo": "Portal visible sponsor invoice.",
        },
    ).json()
    client.post(
        "/api/v1/commercial/payments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "invoice_id": invoice["id"],
            "amount": "200.00",
            "method": "bank",
        },
    )
    sponsor_headers = {
        "X-Afrolete-Sub": "kc-sponsor-portal",
        "X-Afrolete-Email": "PORTAL-SPONSOR@example.com",
        "X-Afrolete-Name": "Sam Sponsor",
    }

    portal_response = client.get(
        f"/api/v1/commercial/sponsor-portal?organization_id={organization['id']}",
        headers=sponsor_headers,
    )

    assert portal_response.status_code == 200
    portal = portal_response.json()
    assert portal["identity_email"] == "portal-sponsor@example.com"
    assert portal["sponsors"][0]["sponsor_name"] == "Portal Partner"
    assert portal["sponsors"][0]["public_site_path"] == f"/site/{organization['slug']}"
    assert portal["agreements"][0]["event_title"] == "Commercial derby"
    assert portal["agreements"][0]["deliverables"] == ["Medical tent", "player recovery report"]
    assert portal["invoices"][0]["invoice_number"] == "SPONSOR-1"
    assert portal["invoices"][0]["outstanding_amount"] == "300.00"
    assert portal["invoices"][0]["payment_session_id"].startswith("cics_manual-gateway_")
    assert "kind=commercial" in portal["invoices"][0]["payment_session_url"]
    assert portal["invoices"][0]["payment_session_status"] == "ready"
    assert portal["summary"]["active_value"] == "750.00"
    assert portal["summary"]["outstanding_invoice_amount"] == "300.00"

    checkout_response = client.get(
        f"/api/v1/commercial/invoice-checkout-sessions/{portal['invoices'][0]['payment_session_id']}",
        params={
            "invoice_id": invoice["id"],
            "provider": "manual_gateway",
        },
    )
    assert checkout_response.status_code == 200
    checkout = checkout_response.json()
    assert checkout["invoice_number"] == "SPONSOR-1"
    assert checkout["open_amount"] == "300.00"
    assert checkout["settlement_endpoint"].endswith("/settle")

    provider_session_response = client.post(
        f"/api/v1/commercial/invoice-checkout-sessions/{checkout['session_id']}/provider-session",
        params={
            "invoice_id": invoice["id"],
            "provider": "manual_gateway",
        },
        json={
            "success_url": "https://app.example/pay/success",
            "cancel_url": "https://app.example/pay/cancel",
            "payment_method": "card",
        },
    )
    assert provider_session_response.status_code == 200
    provider_session = provider_session_response.json()
    assert provider_session["mode"] == "local"
    assert provider_session["status"] == "local_ready"
    assert provider_session["amount"] == "300.00"
    assert provider_session["provider_session_id"].startswith("cpay_manual-gateway_")
    assert provider_session["redirect_url"].startswith("/pay/sessions/")

    settlement_response = client.post(
        f"/api/v1/commercial/invoice-checkout-sessions/{checkout['session_id']}/settle",
        json={
            "invoice_id": invoice["id"],
            "provider": "manual_gateway",
            "amount": "300.00",
            "currency": "USD",
            "method": "mobile_money",
            "external_payment_id": "SPONSOR-1-HOSTED",
            "status": "succeeded",
        },
    )
    assert settlement_response.status_code == 200
    settlement = settlement_response.json()
    assert settlement["accepted"] is True
    assert settlement["invoice_status"] == "paid"
    assert settlement["open_amount"] == "0.00"
    assert settlement["session_status"] == "paid"

    paid_portal = client.get(
        f"/api/v1/commercial/sponsor-portal?organization_id={organization['id']}",
        headers=sponsor_headers,
    ).json()
    assert paid_portal["invoices"][0]["outstanding_amount"] == "0.00"
    assert paid_portal["invoices"][0]["payment_session_url"] is None
    assert paid_portal["invoices"][0]["payment_session_status"] == "paid"
    assert paid_portal["summary"]["outstanding_invoice_amount"] == "0.00"

    outsider_response = client.get(
        f"/api/v1/commercial/sponsor-portal?organization_id={organization['id']}",
        headers={
            "X-Afrolete-Sub": "kc-sponsor-outsider",
            "X-Afrolete-Email": "outsider-sponsor@example.com",
            "X-Afrolete-Name": "Outsider Sponsor",
        },
    )
    assert outsider_response.status_code == 404


def test_commercial_provider_checkout_session_delivers_signed_webhook(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return SimpleNamespace(
                status_code=201,
                text='{"redirect_url":"https://pay.example/session/123","provider_session_id":"psp_123"}',
                content=b"{}",
                json=lambda: {
                    "redirect_url": "https://pay.example/session/123",
                    "provider_session_id": "psp_123",
                },
            )

    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYMENT_SESSION_MODE", "webhook")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYMENT_SESSION_WEBHOOK_URL", "https://payments.example/sessions")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYMENT_SESSION_WEBHOOK_KEY", "session-secret")
    commercial_service.get_settings.cache_clear()
    monkeypatch.setattr(commercial_service.httpx, "AsyncClient", FakeAsyncClient)

    organization, team, _ = create_commercial_context(client, identity_headers)
    sponsor = client.post(
        "/api/v1/commercial/sponsors",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Session Sponsor",
            "contact_email": "session@example.com",
        },
    ).json()
    invoice = client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "sponsor_id": sponsor["id"],
            "invoice_number": "SESSION-1",
            "title": "Provider session invoice",
            "amount_due": "88.00",
        },
    ).json()
    session_id = commercial_service.commercial_invoice_checkout_session_id(
        SimpleNamespace(
            id=invoice["id"],
            invoice_number=invoice["invoice_number"],
            amount_due=invoice["amount_due"],
        ),
        "stripe",
    )

    response = client.post(
        f"/api/v1/commercial/invoice-checkout-sessions/{session_id}/provider-session",
        params={"invoice_id": invoice["id"], "provider": "stripe"},
        json={
            "success_url": "https://app.example/success",
            "cancel_url": "https://app.example/cancel",
            "customer_email": "session@example.com",
            "payment_method": "card",
        },
    )
    assert response.status_code == 200
    session = response.json()
    assert session["mode"] == "webhook"
    assert session["status"] == "created"
    assert session["id"] is not None
    assert session["provider_session_id"] == "psp_123"
    assert session["redirect_url"] == "https://pay.example/session/123"
    assert session["provider_status_code"] == 201
    assert captured["url"] == "https://payments.example/sessions"
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["event_type"] == "commercial.invoice_payment_session.create"
    assert payload["amount"] == "88.00"
    assert payload["customer_email"] == "session@example.com"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    timestamp = headers["X-Afrolete-Commercial-Session-Timestamp"]
    expected_signature = hmac.new(
        b"session-secret",
        timestamp.encode() + b"." + json.dumps(payload, sort_keys=True, default=str).encode(),
        sha256,
    ).hexdigest()
    assert headers["X-Afrolete-Commercial-Session-Key"] == "session-secret"
    assert headers["X-Afrolete-Commercial-Session-Signature"] == f"sha256={expected_signature}"

    sessions_response = client.get(
        "/api/v1/commercial/payment-sessions",
        params={"organization_id": organization["id"]},
    )
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    assert len(sessions) == 1
    assert sessions[0]["provider_session_id"] == "psp_123"
    assert sessions[0]["status"] == "created"
    assert sessions[0]["provider_response"] is not None

    commercial_service.get_settings.cache_clear()


def test_commercial_invoice_payment_webhook_accepts_signed_stripe_event(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYMENT_WEBHOOK_SIGNING_KEY", "commercial-webhook-secret")
    commercial_service.get_settings.cache_clear()
    organization, team, _ = create_commercial_context(client, identity_headers)
    sponsor = client.post(
        "/api/v1/commercial/sponsors",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Stripe Sponsor",
            "contact_email": "stripe-sponsor@example.com",
        },
    ).json()
    invoice = client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "sponsor_id": sponsor["id"],
            "invoice_number": "SPONSOR-STRIPE-1",
            "title": "Stripe sponsor package",
            "amount_due": "99.00",
        },
    ).json()
    stripe_session_id = commercial_service.commercial_invoice_checkout_session_id(
        SimpleNamespace(**invoice),
        "stripe",
    )
    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_sponsor",
                "payment_intent": "pi_sponsor_1",
                "amount_total": 9900,
                "currency": "usd",
                "payment_status": "paid",
                "metadata": {
                    "invoice_id": invoice["id"],
                    "session_id": stripe_session_id,
                },
            }
        },
    }
    raw_body = json.dumps(webhook_payload, separators=(",", ":"), sort_keys=True)
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"commercial-webhook-secret",
        timestamp.encode() + b"." + raw_body.encode(),
        sha256,
    ).hexdigest()

    webhook_response = client.post(
        "/api/v1/commercial/invoice-payment-webhooks?provider=stripe",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Afrolete-Commercial-Timestamp": timestamp,
            "X-Afrolete-Commercial-Signature": f"sha256={signature}",
        },
    )
    assert webhook_response.status_code == 200
    settlement = webhook_response.json()
    assert settlement["accepted"] is True
    assert settlement["signature_required"] is True
    assert settlement["signature_validated"] is True
    assert settlement["invoice_status"] == "paid"
    assert settlement["amount_paid"] == "99.00"
    assert settlement["open_amount"] == "0.00"

    duplicate_response = client.post(
        "/api/v1/commercial/invoice-payment-webhooks?provider=stripe",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Afrolete-Commercial-Timestamp": timestamp,
            "X-Afrolete-Commercial-Signature": f"sha256={signature}",
        },
    )
    assert duplicate_response.status_code == 200
    duplicate = duplicate_response.json()
    assert duplicate["accepted"] is False
    assert duplicate["amount_paid"] == "99.00"
    assert duplicate["open_amount"] == "0.00"

    commercial_service.get_settings.cache_clear()


def test_commercial_accounting_sync_delivers_signed_webhook(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return SimpleNamespace(status_code=202, text="accepted")

    monkeypatch.setenv("AFROLETE_COMMERCIAL_ACCOUNTING_SYNC_MODE", "webhook")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_ACCOUNTING_WEBHOOK_URL", "https://accounting.example/sync")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_ACCOUNTING_WEBHOOK_KEY", "accounting-secret")
    commercial_service.get_settings.cache_clear()
    monkeypatch.setattr(commercial_service.httpx, "AsyncClient", FakeAsyncClient)

    organization, team, _ = create_commercial_context(client, identity_headers)
    invoice = client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "invoice_number": "ACCT-SYNC-1",
            "title": "Accounting sync package",
            "amount_due": "60.00",
        },
    ).json()
    client.post(
        "/api/v1/commercial/payments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "invoice_id": invoice["id"],
            "amount": "60.00",
            "method": "bank",
            "external_reference": "ACCT-SYNC-PAYMENT",
        },
    )

    sync_response = client.post(
        "/api/v1/commercial/accounting-export/sync",
        headers=identity_headers,
        params={"organization_id": organization["id"], "system": "quickbooks", "basis": "cash"},
    )
    assert sync_response.status_code == 200
    sync = sync_response.json()
    assert sync["mode"] == "webhook"
    assert sync["delivered"] is True
    assert sync["provider_status_code"] == 202
    assert sync["row_count"] == 2
    assert captured["url"] == "https://accounting.example/sync"
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["sync_reference"] == sync["sync_reference"]
    assert len(payload["rows"]) == 2
    headers = captured["headers"]
    assert isinstance(headers, dict)
    timestamp = headers["X-Afrolete-Commercial-Accounting-Timestamp"]
    expected_signature = hmac.new(
        b"accounting-secret",
        timestamp.encode() + b"." + json.dumps(payload, sort_keys=True, default=str).encode(),
        sha256,
    ).hexdigest()
    assert headers["X-Afrolete-Commercial-Accounting-Key"] == "accounting-secret"
    assert headers["X-Afrolete-Commercial-Accounting-Signature"] == f"sha256={expected_signature}"

    commercial_service.get_settings.cache_clear()


def test_commercial_tax_filing_delivers_signed_webhook(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return SimpleNamespace(status_code=201, text="filed")

    monkeypatch.setenv("AFROLETE_COMMERCIAL_TAX_FILING_DELIVERY_MODE", "webhook")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_TAX_FILING_WEBHOOK_URL", "https://tax.example/commercial")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_TAX_FILING_WEBHOOK_KEY", "commercial-tax-secret")
    commercial_service.get_settings.cache_clear()
    monkeypatch.setattr(commercial_service.httpx, "AsyncClient", FakeAsyncClient)

    organization, team, _ = create_commercial_context(client, identity_headers)
    client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "invoice_number": "COM-TAX-1",
            "title": "Commercial tax filing invoice",
            "amount_due": "125.00",
            "due_on": "2026-07-15",
        },
    )

    filing_response = client.post(
        "/api/v1/commercial/tax-filing/deliver",
        headers=identity_headers,
        params={
            "organization_id": organization["id"],
            "period_start": "2026-07-01",
            "period_end": "2026-07-31",
            "jurisdiction": "ke",
            "tax_rate": "16.00",
        },
    )
    assert filing_response.status_code == 200
    filing = filing_response.json()
    assert filing["delivery_mode"] == "webhook"
    assert filing["delivery_attempted"] is True
    assert filing["delivered"] is True
    assert filing["provider_status_code"] == 201
    assert filing["taxable_subtotal"] == "125.00"
    assert filing["tax_amount"] == "20.00"
    assert captured["url"] == "https://tax.example/commercial"
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["event_type"] == "commercial.tax_filing"
    assert payload["filing_reference"] == filing["filing_reference"]
    assert payload["invoice_count"] == 1
    headers = captured["headers"]
    assert isinstance(headers, dict)
    timestamp = headers["X-Afrolete-Commercial-Tax-Timestamp"]
    expected_signature = hmac.new(
        b"commercial-tax-secret",
        timestamp.encode() + b"." + json.dumps(payload, sort_keys=True, default=str).encode(),
        sha256,
    ).hexdigest()
    assert headers["X-Afrolete-Commercial-Tax-Key"] == "commercial-tax-secret"
    assert headers["X-Afrolete-Commercial-Tax-Signature"] == f"sha256={expected_signature}"

    commercial_service.get_settings.cache_clear()


def test_commercial_settlement_payout_delivers_signed_webhook(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return SimpleNamespace(status_code=202, text="queued")

    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYOUT_DELIVERY_MODE", "webhook")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYOUT_WEBHOOK_URL", "https://payout.example/commercial")
    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYOUT_WEBHOOK_KEY", "commercial-payout-secret")
    commercial_service.get_settings.cache_clear()
    monkeypatch.setattr(commercial_service.httpx, "AsyncClient", FakeAsyncClient)

    organization, team, _ = create_commercial_context(client, identity_headers)
    invoice = client.post(
        "/api/v1/commercial/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "invoice_number": "COM-PAYOUT-1",
            "title": "Commercial payout invoice",
            "amount_due": "60.00",
        },
    ).json()
    client.post(
        "/api/v1/commercial/payments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "invoice_id": invoice["id"],
            "amount": "60.00",
            "method": "card",
            "external_reference": "COM-PAYOUT-PAYMENT",
        },
    )

    payout_response = client.post(
        "/api/v1/commercial/settlements/payout",
        headers=identity_headers,
        params={
            "organization_id": organization["id"],
            "provider": "bank_gateway",
            "fee_rate": "2.90",
            "fixed_fee": "0.30",
        },
    )
    assert payout_response.status_code == 200
    payout = payout_response.json()
    assert payout["delivery_mode"] == "webhook"
    assert payout["delivery_attempted"] is True
    assert payout["delivered"] is True
    assert payout["status"] == "queued"
    assert payout["provider_status_code"] == 202
    assert payout["gross_amount"] == "60.00"
    assert payout["fee_amount"] == "2.04"
    assert payout["net_amount"] == "57.96"
    assert payout["idempotency_key"].startswith("csp_bank-gateway_")
    assert captured["url"] == "https://payout.example/commercial"
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["event_type"] == "commercial.settlement_payout"
    assert payload["payout_batch_reference"] == payout["payout_batch_reference"]
    assert payload["net_amount"] == "57.96"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    timestamp = headers["X-Afrolete-Commercial-Payout-Timestamp"]
    expected_signature = hmac.new(
        b"commercial-payout-secret",
        timestamp.encode() + b"." + json.dumps(payload, sort_keys=True, default=str).encode(),
        sha256,
    ).hexdigest()
    assert headers["X-Afrolete-Commercial-Payout-Key"] == "commercial-payout-secret"
    assert headers["X-Afrolete-Commercial-Payout-Signature"] == f"sha256={expected_signature}"

    payouts_response = client.get(
        "/api/v1/commercial/settlements/payouts",
        params={"organization_id": organization["id"]},
    )
    assert payouts_response.status_code == 200
    payouts = payouts_response.json()
    assert len(payouts) == 1
    assert payouts[0]["payout_batch_reference"] == payout["payout_batch_reference"]

    monkeypatch.setenv("AFROLETE_COMMERCIAL_PAYOUT_CALLBACK_SIGNING_KEY", "commercial-callback-secret")
    commercial_service.get_settings.cache_clear()
    callback_payload = {
        "provider": "bank_gateway",
        "payout_batch_reference": payout["payout_batch_reference"],
        "idempotency_key": payout["idempotency_key"],
        "status": "paid",
        "provider_status_code": 200,
        "external_event_id": "bank-payout-paid-1",
        "raw_payload": {"provider_state": "settled"},
    }
    raw_callback = json.dumps(callback_payload).encode()
    callback_timestamp = str(int(time.time()))
    callback_signature = hmac.new(
        b"commercial-callback-secret",
        callback_timestamp.encode() + b"." + raw_callback,
        sha256,
    ).hexdigest()
    callback_response = client.post(
        "/api/v1/commercial/settlements/payout-callbacks",
        content=raw_callback,
        headers={
            "Content-Type": "application/json",
            "X-Afrolete-Commercial-Payout-Timestamp": callback_timestamp,
            "X-Afrolete-Commercial-Payout-Signature": f"sha256={callback_signature}",
        },
    )
    assert callback_response.status_code == 200
    callback = callback_response.json()
    assert callback["accepted"] is True
    assert callback["signature_required"] is True
    assert callback["signature_validated"] is True
    assert callback["matched_by"] == "payout_batch_reference"
    assert callback["payout_status"] == "paid"
    assert callback["payout"]["status"] == "paid"
    assert callback["payout"]["external_event_id"] == "bank-payout-paid-1"
    assert callback["payout"]["reconciled_at"] is not None

    commercial_service.get_settings.cache_clear()
