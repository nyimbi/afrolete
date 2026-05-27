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
