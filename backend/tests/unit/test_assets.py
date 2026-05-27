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
