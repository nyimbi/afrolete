def create_billing_context(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Billing Automation Club",
            "slug": "billing-automation-club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    plan = client.post(
        "/api/v1/billing/plans",
        headers=identity_headers,
        json={
            "code": "automation-growth",
            "name": "Automation Growth",
            "base_price": "299.00",
            "currency": "USD",
            "billing_cycle": "monthly",
            "included_athletes": 150,
            "included_teams": 10,
            "included_agent_tasks": 500,
            "included_storage_gb": 100,
            "per_athlete_price": "0.00",
            "per_agent_task_price": "0.00",
            "features": "Recurring billing, AI agents, and operations.",
        },
    ).json()
    subscription = client.post(
        "/api/v1/billing/subscriptions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "billing_plan_id": plan["id"],
            "billing_cycle": "monthly",
            "current_period_start": "2026-06-01",
            "current_period_end": "2026-06-30",
            "trial_ends_on": None,
            "next_billing_on": "2026-06-30",
            "seats_purchased": 150,
            "negotiated_price": "249.00",
            "discount_code": None,
            "external_customer_id": "cus_billing_auto",
            "external_subscription_id": "sub_billing_auto",
            "notes": "Created for recurring billing automation test.",
        },
    ).json()
    return organization, plan, subscription


def test_recurring_invoice_run_creates_invoice_and_advances_subscription(client, identity_headers) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)

    response = client.post(
        "/api/v1/billing/recurring-invoices/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "bill_on": "2026-06-30",
            "due_in_days": 7,
            "limit": 10,
            "invoice_prefix": "AUTO",
        },
    )

    assert response.status_code == 200
    run = response.json()
    assert run["eligible_count"] == 1
    assert run["invoiced_count"] == 1
    assert run["total_invoiced"] == "249.00"
    assert run["subscription_ids"] == [subscription["id"]]

    invoices = client.get(
        f"/api/v1/billing/invoices?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert invoices[0]["invoice_number"].startswith("AUTO-20260630-")
    assert invoices[0]["period_start"] == "2026-06-01"
    assert invoices[0]["period_end"] == "2026-06-30"
    assert invoices[0]["due_on"] == "2026-07-07"
    assert invoices[0]["status"] == "open"

    subscriptions = client.get(
        f"/api/v1/billing/subscriptions?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    renewed = next(item for item in subscriptions if item["id"] == subscription["id"])
    assert renewed["current_period_start"] == "2026-07-01"
    assert renewed["current_period_end"] == "2026-07-31"
    assert renewed["next_billing_on"] == "2026-07-31"


def test_dunning_run_records_notice_and_marks_subscription_past_due(client, identity_headers) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)
    invoice = client.post(
        "/api/v1/billing/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "invoice_number": "DUN-2026-001",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "tax_amount": "0.00",
            "discount_amount": "0.00",
            "due_on": "2026-06-01",
        },
    ).json()

    response = client.post(
        "/api/v1/billing/dunning/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "overdue_as_of": "2026-06-20",
            "overdue_after_days": 0,
            "repeat_after_days": 7,
            "limit": 10,
        },
    )

    assert response.status_code == 200
    run = response.json()
    assert run["eligible_count"] == 1
    assert run["notice_count"] == 1
    assert run["record_only_count"] == 1
    assert run["past_due_count"] == 1
    assert run["invoice_ids"] == [invoice["id"]]
    assert run["severity_counts"] == {"urgent": 1}

    invoices = client.get(
        f"/api/v1/billing/invoices?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    dunned = next(item for item in invoices if item["id"] == invoice["id"])
    assert dunned["dunning_count"] == 1
    assert dunned["dunning_last_severity"] == "urgent"
    assert dunned["dunning_last_sent_at"] is not None

    subscriptions = client.get(
        f"/api/v1/billing/subscriptions?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    renewed = next(item for item in subscriptions if item["id"] == subscription["id"])
    assert renewed["status"] == "past_due"
