# AfroLete Python SDK

Repository package for server-side AfroLete developer API integrations.

```python
from afrolete_sdk import AfroLeteClient

client = AfroLeteClient(
    base_url="https://api.afrolete.example",
    api_key="afl_live_example",
)

organization = client.organization.get(organization_id="tenant-uuid")
teams = client.teams.list(organization_id=organization["id"])
athlete = client.people.create(
    {
        "organization_id": organization["id"],
        "display_name": "Amina Otieno",
        "primary_email": "amina@example.org",
        "membership_role": "athlete",
    }
)
guardian_link = client.people.link_guardian(
    athlete["id"],
    {
        "organization_id": organization["id"],
        "guardian_email": "parent@example.org",
        "guardian_display_name": "Parent Otieno",
        "relationship_kind": "parent",
        "can_sign_consent": True,
    },
)
request = client.people.create_consent_request(
    athlete["id"],
    {
        "organization_id": organization["id"],
        "guardian_person_id": guardian_link["guardian_person_id"],
        "scope_type": "organization",
        "channel": "email",
    },
)
team = client.teams.create(
    {
        "organization_id": organization["id"],
        "name": "U17 Girls",
        "sport": "football",
    }
)
client.teams.add_member(
    team["id"],
    {
        "person_id": athlete["id"],
        "role": "player",
    },
)
events = client.events.list(organization_id=organization["id"])
if events:
    client.events.attendance.record(
        events[0]["id"],
        organization_id=organization["id"],
        payload={
            "person_id": athlete["id"],
            "status": "invited",
            "note": "Imported from the matchday kiosk.",
        },
    )
metrics = client.performance.metrics.list(
    organization_id=organization["id"],
    sport="football",
)
if metrics:
    client.performance.observations.create(
        "athlete-profile-uuid",
        {
            "organization_id": organization["id"],
            "metric_definition_id": metrics[0]["id"],
            "value": 8.7,
            "source": "wearable",
            "confidence": 0.91,
            "verification_status": "pending_review",
        },
    )
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It
uses only the Python standard library, so it can run in small worker jobs,
serverless functions, and integration scripts without extra runtime packages.
