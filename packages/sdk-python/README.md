# AfroLete Python SDK

Repository package for server-side AfroLete developer API integrations.

```python
from afrolete_sdk import AfroLeteClient, types, verify_webhook_signature

client = AfroLeteClient(
    base_url="https://api.afrolete.example",
    api_key="afl_live_example",
)

organization: types.Organization = client.organization.get(organization_id="tenant-uuid")
teams: list[types.Team] = client.teams.list(organization_id=organization["id"])
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
agents = client.agents.list(organization_id=organization["id"])
if agents:
    client.agents.tasks.queue(
        agents[0]["id"],
        {
            "organization_id": organization["id"],
            "task_type": "training_plan_review",
            "title": "Review imported academy training data",
            "input_ref": f"person:{athlete['id']}",
        },
    )
template = client.communications.templates.create(
    {
        "organization_id": organization["id"],
        "name": "Partner reminder",
        "message_type": "reminder",
        "channel": "email",
        "subject_template": "Reminder for {member.name}",
        "body_template": "Please confirm the latest schedule update.",
    }
)
message = client.communications.messages.create(
    {
        "organization_id": organization["id"],
        "template_id": template["id"],
        "message_type": "reminder",
        "channel": "email",
        "scope_type": "person",
        "scope_id": athlete["id"],
        "subject": "Schedule updated",
        "body": "Your schedule was updated by a trusted integration.",
    }
)
client.communications.messages.dispatch(
    message["id"],
    organization_id=organization["id"],
)
subscriptions = client.billing.subscriptions.list(organization_id=organization["id"])
meters = client.billing.meters.list()
if subscriptions and meters:
    client.billing.usage.record(
        {
            "organization_id": organization["id"],
            "subscription_id": subscriptions[0]["id"],
            "usage_meter_id": meters[0]["id"],
            "quantity": 14,
            "source": "partner_billing_sync",
            "external_reference": "usage-sdk-001",
        }
    )
    client.billing.summary.get(organization_id=organization["id"])
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
drill = client.training.drills.create(
    {
        "organization_id": organization["id"],
        "sport": "football",
        "name": "Advanced Passing Circuit",
        "focus_area": "Passing",
        "category": "technical",
        "description": "One-touch passing square with timed support angles.",
    }
)
plan = client.training.plans.create(
    {
        "organization_id": organization["id"],
        "team_id": team["id"],
        "title": "Match-week training block",
        "focus_area": "Transition speed",
        "period_start": "2026-06-01",
        "period_end": "2026-06-07",
        "source_summary": "Imported from a partner coaching workspace.",
    }
)
client.training.plans.items.add(
    plan["id"],
    organization_id=organization["id"],
    payload={
        "drill_id": drill["id"],
        "day_label": "Day 1",
        "title": "Passing circuit progression",
        "focus_area": "Passing",
        "duration_minutes": 20,
        "intensity": 6,
    },
)
session = client.training.sessions.create(
    {
        "organization_id": organization["id"],
        "team_id": team["id"],
        "plan_id": plan["id"],
        "title": "Partner synced session",
        "scheduled_for": "2026-06-03T15:00:00Z",
        "duration_minutes": 75,
        "rpe_target": 6,
    }
)
client.training.sessions.feedback.record(
    session["id"],
    organization_id=organization["id"],
    payload={
        "readiness_score": 72,
        "actual_rpe": 6,
        "actual_duration_minutes": 74,
        "completed": True,
        "feedback": "Synced from the partner app after training.",
    },
)
calendar = client.training.calendar.export(
    organization_id=organization["id"],
    team_id=team["id"],
    starts_at="2026-06-01T00:00:00Z",
    ends_at="2026-06-30T00:00:00Z",
)
availability = client.training.availability.suggest(
    {
        "organization_id": organization["id"],
        "team_id": team["id"],
        "starts_at": "2026-06-01T06:00:00Z",
        "duration_minutes": 75,
    }
)

signature_ok = verify_webhook_signature(
    payload=raw_webhook_body,
    timestamp=headers["X-Afrolete-Webhook-Timestamp"],
    signature=headers["X-Afrolete-Webhook-Signature"],
    signing_secret=AFROLETE_WEBHOOK_SECRET,
)
if not signature_ok:
    raise ValueError("Invalid AfroLete webhook signature")
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It
uses only the Python standard library, so it can run in small worker jobs,
serverless functions, and integration scripts without extra runtime packages.
Webhook helpers verify the same timestamped HMAC-SHA256 contract used by
AfroLete developer webhook deliveries.

The package is PEP 561 typed. Import `afrolete_sdk.types` for `TypedDict`
request and response contracts such as `Organization`, `PersonCreate`,
`TrainingPlanCreate`, `BillingUsageRecord`, and `PerformanceObservation`.

## Release Verification

Build and inspect the Python package from the repository root:

```bash
python scripts/verify_sdk_release.py --out-dir dist/sdk-release
```

The release verifier compiles the SDK package, builds one wheel and one source
distribution with `uv build`, and checks that `client.py`, `types.py`, and the
PEP 561 `py.typed` marker are present in the wheel before publication.
