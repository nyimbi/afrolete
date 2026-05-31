import hmac
import json
from hashlib import sha256

import httpx

from app.core.config import Settings
from app.services import billing as billing_service


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


def test_late_fee_run_applies_configured_fee_and_marks_subscription_past_due(client, identity_headers) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)
    invoice = client.post(
        "/api/v1/billing/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "invoice_number": "FEE-2026-001",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "tax_amount": "0.00",
            "discount_amount": "0.00",
            "due_on": "2026-06-01",
        },
    ).json()

    response = client.post(
        "/api/v1/billing/late-fees/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "apply_on": "2026-06-20",
            "overdue_after_days": 0,
            "repeat_after_days": 30,
            "fixed_fee": "10.00",
            "percentage_rate": "5.00",
            "max_fee": "30.00",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    run = response.json()
    assert run["eligible_count"] == 1
    assert run["fee_count"] == 1
    assert run["total_late_fees"] == "22.45"
    assert run["invoice_ids"] == [invoice["id"]]
    assert run["subscription_ids"] == [subscription["id"]]

    invoices = client.get(
        f"/api/v1/billing/invoices?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    charged = next(item for item in invoices if item["id"] == invoice["id"])
    assert charged["total"] == "271.45"
    assert charged["late_fee_total"] == "22.45"
    assert charged["late_fee_count"] == 1
    assert charged["late_fee_last_applied_on"] == "2026-06-20"
    assert "Late fee 22.45 USD applied on 2026-06-20." in charged["line_items"]

    subscriptions = client.get(
        f"/api/v1/billing/subscriptions?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    renewed = next(item for item in subscriptions if item["id"] == subscription["id"])
    assert renewed["status"] == "past_due"


def test_payment_retry_run_records_attempt_and_marks_subscription_past_due(client, identity_headers) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)
    invoice = client.post(
        "/api/v1/billing/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "invoice_number": "RETRY-2026-001",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "tax_amount": "0.00",
            "discount_amount": "0.00",
            "due_on": "2026-06-01",
        },
    ).json()

    response = client.post(
        "/api/v1/billing/payment-retries/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "retry_at": "2026-06-20T10:30:00+00:00",
            "overdue_after_days": 0,
            "repeat_after_hours": 24,
            "max_attempts": 3,
            "provider": "stripe",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    run = response.json()
    assert run["eligible_count"] == 1
    assert run["retry_count"] == 1
    assert run["submitted_count"] == 1
    assert run["failed_count"] == 0
    assert run["delivery_mode"] == "record_only"
    assert run["total_attempted"] == "249.00"
    assert run["total_collected"] == "0.00"
    assert run["status_counts"] == {"recorded": 1}
    assert run["invoice_ids"] == [invoice["id"]]

    invoices = client.get(
        f"/api/v1/billing/invoices?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    retried = next(item for item in invoices if item["id"] == invoice["id"])
    assert retried["payment_retry_count"] == 1
    assert retried["payment_retry_last_status"] == "recorded"
    assert retried["payment_retry_last_attempted_at"] is not None
    assert retried["payment_retry_next_attempt_at"] is not None
    assert "Payment retry recorded for 249.00 USD via stripe" in retried["line_items"]

    subscriptions = client.get(
        f"/api/v1/billing/subscriptions?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    renewed = next(item for item in subscriptions if item["id"] == subscription["id"])
    assert renewed["status"] == "past_due"


def test_saas_invoice_hosted_checkout_settles_invoice(client, identity_headers) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)
    invoice = client.post(
        "/api/v1/billing/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "invoice_number": "CHECKOUT-2026-001",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "tax_amount": "0.00",
            "discount_amount": "0.00",
            "due_on": "2026-06-30",
        },
    ).json()

    link_response = client.post(
        (
            f"/api/v1/billing/invoices/{invoice['id']}/checkout-link"
            f"?organization_id={organization['id']}&provider=manual_gateway&checkout_base_url=/pay/sessions"
        ),
        headers=identity_headers,
    )

    assert link_response.status_code == 200
    link = link_response.json()
    assert link["hosted_checkout"]["open_amount"] == "249.00"
    assert link["hosted_checkout"]["session_status"] == "ready"
    assert link["hosted_checkout"]["payer_type"] == "tenant_organization"
    assert "Individual members are not the platform hosting payer" in link["hosted_checkout"]["payer_note"]
    assert "kind=saas" in link["checkout_url"]

    checkout_response = client.get(
        (
            f"/api/v1/billing/invoice-checkout-sessions/{link['session_id']}"
            f"?invoice_id={invoice['id']}&provider=manual_gateway"
        )
    )
    assert checkout_response.status_code == 200
    checkout = checkout_response.json()
    assert checkout["client_reference"] == f"saas-invoice-checkout:{invoice['id']}"
    assert checkout["checkout_summary"].endswith("outstanding for the tenant organization.")

    settlement_response = client.post(
        f"/api/v1/billing/invoice-checkout-sessions/{link['session_id']}/settle",
        json={
            "invoice_id": invoice["id"],
            "provider": "manual_gateway",
            "amount": "249.00",
            "currency": "USD",
            "method": "hosted_payment_page",
            "external_payment_id": "hosted_saas_checkout_001",
            "status": "succeeded",
            "raw_reference": "Hosted SaaS checkout test.",
        },
    )
    assert settlement_response.status_code == 200
    settlement = settlement_response.json()
    assert settlement["accepted"] is True
    assert settlement["invoice_status"] == "paid"
    assert settlement["amount_paid"] == "249.00"
    assert settlement["open_amount"] == "0.00"
    assert settlement["session_status"] == "paid"

    invoices = client.get(
        f"/api/v1/billing/invoices?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    paid = next(item for item in invoices if item["id"] == invoice["id"])
    assert paid["status"] == "paid"
    assert paid["amount_paid"] == "249.00"


def test_plan_change_applies_proration_and_updates_subscription(client, identity_headers) -> None:
    organization, plan, subscription = create_billing_context(client, identity_headers)
    upgraded_plan = client.post(
        "/api/v1/billing/plans",
        headers=identity_headers,
        json={
            "code": "automation-elite",
            "name": "Automation Elite",
            "base_price": "499.00",
            "currency": "USD",
            "billing_cycle": "annual",
            "included_athletes": 500,
            "included_teams": 40,
            "included_agent_tasks": 5000,
            "included_storage_gb": 1000,
            "per_athlete_price": "0.00",
            "per_agent_task_price": "0.00",
            "features": "Advanced AI agents, enterprise billing, and reporting.",
        },
    ).json()

    quote_response = client.get(
        (
            f"/api/v1/billing/subscriptions/{subscription['id']}/proration"
            f"?organization_id={organization['id']}&new_price=399.00&effective_on=2026-06-16"
        ),
        headers=identity_headers,
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()
    assert quote["current_price"] == "249.00"
    assert quote["new_price"] == "399.00"
    assert quote["remaining_days"] == 15
    assert quote["total_days"] == 30
    assert quote["unused_credit"] == "124.50"
    assert quote["new_charge"] == "199.50"
    assert quote["net_amount"] == "75.00"
    assert "charge" in quote["recommendation"].lower()

    apply_response = client.post(
        f"/api/v1/billing/subscriptions/{subscription['id']}/plan-change",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "new_billing_plan_id": upgraded_plan["id"],
            "new_price": "399.00",
            "effective_on": "2026-06-16",
            "note": "Customer upgraded for academy expansion.",
        },
    )
    assert apply_response.status_code == 200
    applied = apply_response.json()
    assert applied["previous_billing_plan_id"] == plan["id"]
    assert applied["new_billing_plan_id"] == upgraded_plan["id"]
    assert applied["previous_price"] == "249.00"
    assert applied["applied_price"] == "399.00"
    assert applied["net_amount"] == "75.00"
    assert applied["subscription_status"] == "active"

    subscriptions = client.get(
        f"/api/v1/billing/subscriptions?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    changed = next(item for item in subscriptions if item["id"] == subscription["id"])
    assert changed["billing_plan_id"] == upgraded_plan["id"]
    assert changed["billing_cycle"] == "annual"
    assert changed["negotiated_price"] == "399.00"
    assert "plan change" in changed["notes"]
    assert "Customer upgraded for academy expansion." in changed["notes"]


def test_tax_filing_delivery_posts_aggregated_package(client, identity_headers, monkeypatch) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)
    invoice = client.post(
        "/api/v1/billing/invoices",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "invoice_number": "TAX-2026-001",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "tax_amount": "40.00",
            "discount_amount": "10.00",
            "due_on": "2026-06-30",
        },
    ).json()
    payment_response = client.post(
        "/api/v1/billing/payments",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "invoice_id": invoice["id"],
            "amount": "100.00",
            "provider": "manual",
            "external_payment_id": "tax-filing-partial-payment",
        },
    )
    assert payment_response.status_code == 201

    captured: dict[str, object] = {}

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            captured["timeout"] = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, url: str, *, json: dict[str, object], headers: dict[str, str]) -> httpx.Response:
            captured["url"] = url
            captured["payload"] = json
            captured["headers"] = headers
            return httpx.Response(status_code=202, text="accepted")

    monkeypatch.setattr(
        billing_service,
        "get_settings",
        lambda: Settings(
            billing_tax_filing_delivery_mode="webhook",
            billing_tax_filing_webhook_url="https://tax.example/filings",
            billing_tax_filing_webhook_key="tax-secret",
            billing_tax_filing_timeout_seconds=9.0,
        ),
    )
    monkeypatch.setattr(billing_service.httpx, "AsyncClient", FakeAsyncClient)

    response = client.post(
        (
            f"/api/v1/billing/tax-filing/deliver?organization_id={organization['id']}"
            "&period_start=2026-06-01&period_end=2026-06-30&jurisdiction=ke"
        ),
        headers=identity_headers,
    )

    assert response.status_code == 200
    filing = response.json()
    assert filing["jurisdiction"] == "KE"
    assert filing["invoice_count"] == 1
    assert filing["taxable_subtotal"] == "249.00"
    assert filing["tax_amount"] == "40.00"
    assert filing["gross_total"] == "279.00"
    assert filing["outstanding_total"] == "179.00"
    assert filing["delivery_mode"] == "webhook"
    assert filing["delivery_attempted"] is True
    assert filing["delivered"] is True
    assert filing["provider_status_code"] == 202
    assert filing["failure_reason"] is None
    assert captured["timeout"] == 9.0
    assert captured["url"] == "https://tax.example/filings"
    assert captured["payload"]["event_type"] == "billing.tax_filing"
    assert captured["payload"]["filing_reference"] == filing["filing_reference"]
    headers = captured["headers"]
    timestamp = headers["X-Afrolete-Billing-Tax-Timestamp"]
    raw_body = json.dumps(captured["payload"], sort_keys=True, default=str).encode()
    expected_signature = hmac.new(
        b"tax-secret",
        timestamp.encode() + b"." + raw_body,
        sha256,
    ).hexdigest()
    assert headers["X-Afrolete-Billing-Tax-Filing-Key"] == "tax-secret"
    assert headers["X-Afrolete-Billing-Tax-Signature"] == f"sha256={expected_signature}"


def test_subscription_lifecycle_cancel_pause_resume_and_undo(client, identity_headers) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)

    cancel_response = client.post(
        f"/api/v1/billing/subscriptions/{subscription['id']}/lifecycle",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "action": "cancel_at_period_end",
            "effective_on": "2026-06-15",
            "reason": "Customer requested end-of-season cancellation.",
        },
    )
    assert cancel_response.status_code == 200
    cancel = cancel_response.json()
    assert cancel["status"] == "active"
    assert cancel["cancel_at_period_end"] is True
    assert cancel["subscription"]["cancel_at_period_end"] is True

    undo_response = client.post(
        f"/api/v1/billing/subscriptions/{subscription['id']}/lifecycle",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "action": "undo_cancel",
            "effective_on": "2026-06-16",
        },
    )
    assert undo_response.status_code == 200
    assert undo_response.json()["cancel_at_period_end"] is False

    pause_response = client.post(
        f"/api/v1/billing/subscriptions/{subscription['id']}/lifecycle",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "action": "pause",
            "effective_on": "2026-06-20",
            "reason": "Off-season hold.",
        },
    )
    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "paused"

    resume_response = client.post(
        f"/api/v1/billing/subscriptions/{subscription['id']}/lifecycle",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "action": "resume",
            "effective_on": "2026-06-25",
        },
    )
    assert resume_response.status_code == 200
    resumed = resume_response.json()
    assert resumed["previous_status"] == "paused"
    assert resumed["status"] == "active"
    assert "lifecycle resume" in resumed["subscription"]["notes"]


def test_entitlement_enforcement_tracks_usage_limits_and_subscription_state(client, identity_headers) -> None:
    organization, _, subscription = create_billing_context(client, identity_headers)
    entitlement = client.post(
        "/api/v1/billing/entitlements",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "feature_key": "ai_agents",
            "limit_value": 12,
            "used_value": 15,
            "resets_on": "2026-06-30",
        },
    ).json()

    response = client.post(
        "/api/v1/billing/entitlements/enforcement/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "as_of": "2026-06-20",
        },
    )

    assert response.status_code == 200
    run = response.json()
    assert run["checked_count"] == 1
    assert run["would_update_count"] == 1
    assert run["updated_count"] == 1
    assert run["over_limit_count"] == 1
    assert run["items"][0]["entitlement_id"] == entitlement["id"]
    assert run["items"][0]["previous_status"] == "active"
    assert run["items"][0]["status"] == "over_limit"
    assert run["items"][0]["remaining_value"] == 0
    assert run["items"][0]["action"] == "restrict_overage"

    client.post(
        f"/api/v1/billing/subscriptions/{subscription['id']}/lifecycle",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "action": "pause",
            "effective_on": "2026-06-21",
        },
    )
    paused_response = client.post(
        "/api/v1/billing/entitlements/enforcement/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "subscription_id": subscription["id"],
            "as_of": "2026-06-21",
        },
    )

    assert paused_response.status_code == 200
    paused_run = paused_response.json()
    assert paused_run["blocked_count"] == 1
    assert paused_run["items"][0]["previous_status"] == "over_limit"
    assert paused_run["items"][0]["status"] == "paused"
    assert paused_run["items"][0]["action"] == "pause"
