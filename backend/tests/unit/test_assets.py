import hmac
import json
from hashlib import sha256
from types import SimpleNamespace

from app.services import assets as assets_service


def create_assets_context(client, identity_headers, name="Assets Club"):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": name,
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": f"{name} U16",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": f"{name.lower().replace(' ', '-')}-borrower@example.com",
            "display_name": f"{name} Borrower",
            "role": "staff",
        },
    ).json()
    event = client.post(
        "/api/v1/events",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "event_type": "training",
            "title": f"{name} training",
            "starts_at": "2026-06-10T15:00:00Z",
            "ends_at": "2026-06-10T16:30:00Z",
            "venue_name": "Main Field",
        },
    ).json()
    return organization, team, member, event


def test_facility_equipment_checkout_work_order_booking_and_summary(
    client,
    identity_headers,
) -> None:
    organization, team, member, event = create_assets_context(client, identity_headers)

    facility_response = client.post(
        "/api/v1/assets/facilities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Main Field",
            "facility_type": "field",
            "sport": "football",
            "surface": "natural grass",
            "capacity": 500,
            "location": "Riverside campus",
            "dimensions": "105m x 68m",
            "amenities": "Lights, changing rooms, scoreboard",
            "hourly_rate": "120.00",
            "maintenance_budget": "15000.00",
            "condition": "good",
            "insurance_policy_ref": "LIAB-2026",
            "last_inspection_on": "2026-05-01",
        },
    )
    assert facility_response.status_code == 201
    facility = facility_response.json()
    assert facility["status"] == "available"

    equipment_response = client.post(
        "/api/v1/assets/equipment",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": facility["id"],
            "team_id": team["id"],
            "name": "Footballs Size 5",
            "category": "training_equipment",
            "subcategory": "balls",
            "brand": "Nike",
            "model": "Premier League Match Ball",
            "tag_code": "BALL-SET-001",
            "quantity_total": 24,
            "quantity_available": 24,
            "condition": "good",
            "storage_location": "Equipment Room A, Shelf 3",
            "min_stock_level": 10,
            "reorder_point": 8,
            "unit_value": "50.00",
            "depreciation_rate": "20.00",
            "last_audit_on": "2026-05-15",
        },
    )
    assert equipment_response.status_code == 201
    equipment = equipment_response.json()
    assert equipment["quantity_available"] == 24

    checkout_response = client.post(
        "/api/v1/assets/checkouts",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "equipment_item_id": equipment["id"],
            "team_id": team["id"],
            "event_id": event["id"],
            "borrower_person_id": member["subject_id"],
            "quantity": 6,
            "purpose": "Saturday match kit",
            "due_at": "2026-06-11T12:00:00Z",
            "condition_out": "good",
            "condition_notes": "Two balls need inflation.",
        },
    )
    assert checkout_response.status_code == 201
    checkout = checkout_response.json()
    assert checkout["status"] == "checked_out"

    equipment_after_checkout = client.get(
        f"/api/v1/assets/equipment?organization_id={organization['id']}"
    ).json()[0]
    assert equipment_after_checkout["quantity_available"] == 18

    return_response = client.patch(
        f"/api/v1/assets/checkouts/{checkout['id']}/return",
        headers=identity_headers,
        json={
            "returned_at": "2026-06-10T18:00:00Z",
            "condition_in": "fair",
            "late_fee": "0.00",
        },
    )
    assert return_response.status_code == 200
    returned = return_response.json()
    assert returned["status"] == "returned"

    work_order_response = client.post(
        "/api/v1/assets/work-orders",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": facility["id"],
            "equipment_item_id": equipment["id"],
            "assigned_to_person_id": member["subject_id"],
            "title": "Inspect goal nets and ball pressure",
            "priority": "high",
            "due_at": "2026-06-09T12:00:00Z",
            "vendor": "Grounds Crew",
            "estimated_cost": "150.00",
            "safety_related": True,
            "compliance_reference": "Monthly equipment inspection",
            "notes": "Pre-match safety check.",
        },
    )
    assert work_order_response.status_code == 201
    work_order = work_order_response.json()
    assert work_order["status"] == "open"

    complete_response = client.patch(
        f"/api/v1/assets/work-orders/{work_order['id']}",
        headers=identity_headers,
        json={
            "status": "completed",
            "actual_cost": "125.00",
            "notes": "Goals secured and equipment pressure checked.",
        },
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["completed_at"] is not None

    booking_response = client.post(
        "/api/v1/assets/bookings",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": facility["id"],
            "team_id": team["id"],
            "event_id": event["id"],
            "title": "U16 training block",
            "starts_at": "2026-06-12T15:00:00Z",
            "ends_at": "2026-06-12T17:00:00Z",
            "requester_name": "Coach Example",
            "requester_email": "coach@example.com",
            "expected_attendees": 28,
            "rate": "120.00",
            "deposit_required": "50.00",
            "insurance_certificate_ref": "CERT-2026",
            "special_requirements": "Goals, corner flags, and first-aid kit.",
            "access_code": "FIELD-0612",
        },
    )
    assert booking_response.status_code == 201
    booking = booking_response.json()
    assert booking["status"] == "confirmed"

    summary = client.get(f"/api/v1/assets/summary?organization_id={organization['id']}").json()
    assert summary["facilities"] == 1
    assert summary["equipment_items"] == 1
    assert summary["open_checkouts"] == 0
    assert summary["open_work_orders"] == 0
    assert summary["upcoming_bookings"] == 1
    assert summary["booked_hours"] == 2.0
    assert summary["projected_booking_revenue"] == "240.00"


def test_asset_summary_handles_empty_tenant(client, identity_headers) -> None:
    organization, _, _, _ = create_assets_context(client, identity_headers, "Empty Assets Club")

    summary_response = client.get(f"/api/v1/assets/summary?organization_id={organization['id']}")

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["facilities"] == 0
    assert summary["upcoming_bookings"] == 0
    assert summary["projected_booking_revenue"] == "0.00"


def test_facility_booking_rejects_overlap(client, identity_headers) -> None:
    organization, team, _, _ = create_assets_context(client, identity_headers, "Booking Club")
    facility = client.post(
        "/api/v1/assets/facilities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Court 1",
            "facility_type": "court",
            "hourly_rate": "80.00",
        },
    ).json()

    first = client.post(
        "/api/v1/assets/bookings",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": facility["id"],
            "team_id": team["id"],
            "title": "Training reservation",
            "starts_at": "2026-06-15T10:00:00Z",
            "ends_at": "2026-06-15T12:00:00Z",
        },
    )
    assert first.status_code == 201

    overlap = client.post(
        "/api/v1/assets/bookings",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": facility["id"],
            "team_id": team["id"],
            "title": "Overlapping reservation",
            "starts_at": "2026-06-15T11:00:00Z",
            "ends_at": "2026-06-15T13:00:00Z",
        },
    )
    assert overlap.status_code == 409
    assert overlap.json()["detail"] == "Facility is already booked"


def test_emergency_escalation_timer_advances_due_activation(client, identity_headers) -> None:
    organization, _, _, _ = create_assets_context(client, identity_headers, "Emergency Timer Club")
    plan = client.post(
        "/api/v1/assets/emergency-plans",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "title": "Main field emergency response",
            "emergency_type": "medical",
            "emergency_contacts": "Safety officer; medical lead; venue security.",
            "medical_protocols": "Stabilize, clear access, assign first aid, document actions.",
            "communication_protocols": "Notify staff, guardians, and venue operations.",
            "incident_command_roles": "Incident lead, medic, family liaison.",
            "escalation_matrix": "Escalate every 15 minutes while active.",
        },
    ).json()
    activation = client.post(
        "/api/v1/assets/emergency-activations",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "plan_id": plan["id"],
            "emergency_type": "medical",
            "location_detail": "Main field touchline",
            "activated_at": "2026-01-01T08:00:00Z",
            "escalation_level": 1,
            "assigned_responders": "Coach and medic",
        },
    ).json()

    run_response = client.post(
        "/api/v1/assets/emergency-escalations/run",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "unresolved_after_minutes": 0,
            "repeat_after_minutes": 1,
            "limit": 10,
        },
    )

    assert run_response.status_code == 200
    run = run_response.json()
    assert run["eligible_count"] == 1
    assert run["executed_count"] == 1
    assert run["escalated_count"] == 1
    assert run["failed_count"] == 0
    assert run["activation_ids"] == [activation["id"]]

    activations = client.get(
        f"/api/v1/assets/emergency-activations?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    escalated = next(item for item in activations if item["id"] == activation["id"])
    assert escalated["escalation_level"] == 2
    assert "automated emergency escalation timer" in escalated["communication_log"]


def test_asset_procurement_scan_photo_supplier_lease_and_utilization(
    client,
    identity_headers,
) -> None:
    organization, team, member, _ = create_assets_context(client, identity_headers, "Procurement Club")
    facility = client.post(
        "/api/v1/assets/facilities",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Equipment Store",
            "facility_type": "storage",
        },
    ).json()
    equipment = client.post(
        "/api/v1/assets/equipment",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": facility["id"],
            "team_id": team["id"],
            "name": "GPS Pods",
            "category": "wearables",
            "brand": "TrackCo",
            "tag_code": "RFID-GPS-001",
            "serial_number": "SER-GPS-001",
            "quantity_total": 10,
            "quantity_available": 2,
            "min_stock_level": 3,
            "reorder_point": 4,
            "unit_value": "150.00",
            "depreciation_rate": "25.00",
        },
    ).json()

    scan = client.get(
        "/api/v1/assets/equipment/scan",
        headers=identity_headers,
        params={"organization_id": organization["id"], "code": "RFID-GPS-001"},
    )
    assert scan.status_code == 200
    assert scan.json()["match_type"] == "tag_code"
    assert scan.json()["item"]["id"] == equipment["id"]

    photo = client.patch(
        f"/api/v1/assets/equipment/{equipment['id']}/photo",
        headers=identity_headers,
        json={
            "photo_url": "https://cdn.afrolete.test/assets/gps-pods.jpg",
            "notes": "Photo captured during May audit.",
        },
    )
    assert photo.status_code == 200
    assert photo.json()["photo_url"].endswith("gps-pods.jpg")

    procurement = client.get(
        f"/api/v1/assets/procurement/recommendations?organization_id={organization['id']}"
    ).json()
    assert procurement[0]["equipment_item_id"] == equipment["id"]
    assert procurement[0]["recommended_quantity"] >= 8
    assert procurement[0]["supplier_hint"] == "TrackCo"

    work_order = client.post(
        "/api/v1/assets/work-orders",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": facility["id"],
            "equipment_item_id": equipment["id"],
            "assigned_to_person_id": member["subject_id"],
            "title": "Calibrate GPS pods",
            "priority": "medium",
            "vendor": "TrackCo Service",
            "estimated_cost": "200.00",
            "safety_related": False,
        },
    ).json()
    client.patch(
        f"/api/v1/assets/work-orders/{work_order['id']}",
        headers=identity_headers,
        json={"status": "completed", "actual_cost": "190.00"},
    )

    suppliers = client.get(
        f"/api/v1/assets/suppliers/scorecard?organization_id={organization['id']}"
    ).json()
    assert suppliers[0]["supplier_name"] == "TrackCo Service"
    assert suppliers[0]["score"] >= 85

    quote = client.get(
        f"/api/v1/assets/equipment/{equipment['id']}/lease-quote",
        params={"organization_id": organization["id"], "quantity": 2, "term_months": 12},
    ).json()
    assert quote["monthly_amount"] != "0.00"
    assert quote["term_months"] == 12

    recommendations = client.get(
        f"/api/v1/assets/utilization/recommendations?organization_id={organization['id']}"
    ).json()
    assert any(item["target_id"] == equipment["id"] for item in recommendations)


def test_asset_accounting_export_and_signed_sync(
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

    monkeypatch.setenv("AFROLETE_ASSET_ACCOUNTING_SYNC_MODE", "webhook")
    monkeypatch.setenv("AFROLETE_ASSET_ACCOUNTING_WEBHOOK_URL", "https://accounting.example/assets")
    monkeypatch.setenv("AFROLETE_ASSET_ACCOUNTING_WEBHOOK_KEY", "asset-accounting-secret")
    assets_service.get_settings.cache_clear()
    monkeypatch.setattr(assets_service.httpx, "AsyncClient", FakeAsyncClient)

    organization, team, member, _ = create_assets_context(client, identity_headers, "Asset Accounting Club")
    equipment = client.post(
        "/api/v1/assets/equipment",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "name": "Timing Gates",
            "category": "timing",
            "brand": "ChronoCo",
            "quantity_total": 4,
            "quantity_available": 2,
            "unit_value": "500.00",
            "depreciation_rate": "20.00",
        },
    ).json()
    order = client.post(
        "/api/v1/assets/suppliers/orders",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "equipment_item_id": equipment["id"],
            "supplier_name": "ChronoCo",
            "item_name": "Timing Gate Battery Kit",
            "quantity": 2,
            "unit_cost": "125.00",
            "currency": "USD",
            "external_reference": "PO-ASSET-1",
            "submit": True,
        },
    ).json()
    assert order["total_cost"] == "250.00"
    schedule = client.post(
        f"/api/v1/assets/equipment/{equipment['id']}/lease-schedules",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "quantity": 1,
            "term_months": 6,
            "person_id": member["subject_id"],
            "team_id": team["id"],
            "starts_on": "2026-06-01",
            "notes": "Lease schedule for academy timing gates.",
        },
    ).json()
    payment = client.post(
        f"/api/v1/assets/lease-schedules/{schedule['id']}/payments",
        headers=identity_headers,
        json={
            "amount": schedule["monthly_amount"],
            "method": "bank",
            "external_reference": "LEASE-ASSET-PAY-1",
        },
    )
    assert payment.status_code == 200

    export_response = client.get(
        "/api/v1/assets/accounting-export",
        headers=identity_headers,
        params={"organization_id": organization["id"], "system": "quickbooks", "basis": "accrual"},
    )
    assert export_response.status_code == 200
    export = export_response.json()
    assert export["supplier_order_count"] == 1
    assert export["lease_schedule_count"] == 1
    assert export["payment_count"] == 1
    assert export["debit_total"] == export["credit_total"]
    assert {row["row_type"] for row in export["rows"]} >= {
        "supplier_equipment_purchase",
        "supplier_accounts_payable",
        "lease_receivable",
        "lease_revenue",
        "lease_cash_receipt",
        "lease_receivable_reduction",
    }

    sync_response = client.post(
        "/api/v1/assets/accounting-export/sync",
        headers=identity_headers,
        params={"organization_id": organization["id"], "system": "quickbooks", "basis": "accrual"},
    )
    assert sync_response.status_code == 200
    sync = sync_response.json()
    assert sync["mode"] == "webhook"
    assert sync["delivered"] is True
    assert sync["provider_status_code"] == 202
    assert sync["row_count"] == len(export["rows"])
    assert captured["url"] == "https://accounting.example/assets"
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["event_type"] == "assets.accounting_export"
    assert payload["sync_reference"] == sync["sync_reference"]
    assert payload["debit_total"] == sync["debit_total"]
    headers = captured["headers"]
    assert isinstance(headers, dict)
    timestamp = headers["X-Afrolete-Asset-Accounting-Timestamp"]
    expected_signature = hmac.new(
        b"asset-accounting-secret",
        timestamp.encode() + b"." + json.dumps(payload, sort_keys=True, default=str).encode(),
        sha256,
    ).hexdigest()
    assert headers["X-Afrolete-Asset-Accounting-Key"] == "asset-accounting-secret"
    assert headers["X-Afrolete-Asset-Accounting-Signature"] == f"sha256={expected_signature}"

    assets_service.get_settings.cache_clear()


def test_equipment_rejects_facility_from_other_organization(client, identity_headers) -> None:
    organization, team, _, _ = create_assets_context(client, identity_headers, "Home Assets")
    other_organization, _, _, _ = create_assets_context(client, identity_headers, "Other Assets")
    other_facility = client.post(
        "/api/v1/assets/facilities",
        headers=identity_headers,
        json={
            "organization_id": other_organization["id"],
            "name": "Other Storage",
            "facility_type": "storage",
        },
    ).json()

    response = client.post(
        "/api/v1/assets/equipment",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "facility_id": other_facility["id"],
            "team_id": team["id"],
            "name": "Cross-org GPS tracker",
            "category": "wearables",
            "quantity_total": 4,
            "quantity_available": 4,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Facility not found"
