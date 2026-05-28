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

    dashboard = client.get(
        f"/api/v1/commercial/sponsorship-dashboard?organization_id={organization['id']}"
    ).json()
    assert dashboard[0]["sponsor_name"] == "Acme Sports"
    assert dashboard[0]["deliverable_count"] == 3
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
