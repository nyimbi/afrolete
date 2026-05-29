# AfroLete TypeScript SDK

Repository package for tenant-facing AfroLete developer APIs.

```ts
import { AfroLeteClient } from "@afrolete/sdk";
import { AFROLETE_SDK_ENDPOINTS } from "@afrolete/sdk";
import { verifyAfroLeteWebhookSignature } from "@afrolete/sdk";

const client = new AfroLeteClient({
  baseUrl: "https://api.afrolete.example",
  apiKey: process.env.AFROLETE_API_KEY!,
});

const organization = await client.organization.get({
  organizationId: process.env.AFROLETE_ORG_ID!,
});

const writeEndpoints = AFROLETE_SDK_ENDPOINTS.filter((endpoint) =>
  endpoint.required_scopes.some((scope) => scope.startsWith("write:")),
);

const events = await client.events.list({
  organizationId: organization.id,
});

const teams = await client.teams.list({
  organizationId: organization.id,
});

const athlete = await client.people.create({
  organization_id: organization.id,
  display_name: "Amina Otieno",
  primary_email: "amina@example.org",
  membership_role: "athlete",
});

const guardianLink = await client.people.linkGuardian(athlete.id, {
  organization_id: organization.id,
  guardian_email: "parent@example.org",
  guardian_display_name: "Parent Otieno",
  relationship_kind: "parent",
  can_sign_consent: true,
});

const request = await client.people.createConsentRequest(athlete.id, {
  organization_id: organization.id,
  guardian_person_id: guardianLink.guardian_person_id,
  scope_type: "organization",
  channel: "email",
});

const team = await client.teams.create({
  organization_id: organization.id,
  name: "U17 Girls",
  sport: "football",
});

await client.teams.addMember(team.id, {
  person_id: athlete.id,
  role: "player",
});

const [event] = events;
if (event) {
  await client.events.attendance.record(event.id, { organizationId: organization.id }, {
    person_id: athlete.id,
    status: "invited",
    note: "Imported from the matchday kiosk.",
  });
}

const [agent] = await client.agents.list({
  organizationId: organization.id,
});

if (agent) {
  await client.agents.tasks.queue(agent.id, {
    organization_id: organization.id,
    task_type: "training_plan_review",
    title: "Review imported academy training data",
    input_ref: `person:${athlete.id}`,
  });
}

const template = await client.communications.templates.create({
  organization_id: organization.id,
  name: "Partner reminder",
  message_type: "reminder",
  channel: "email",
  subject_template: "Reminder for {member.name}",
  body_template: "Please confirm the latest schedule update.",
});

const message = await client.communications.messages.create({
  organization_id: organization.id,
  template_id: template.id,
  message_type: "reminder",
  channel: "email",
  scope_type: "person",
  scope_id: athlete.id,
  subject: "Schedule updated",
  body: "Your schedule was updated by a trusted integration.",
});

await client.communications.messages.dispatch(message.id, {
  organizationId: organization.id,
});

const [subscription] = await client.billing.subscriptions.list({
  organizationId: organization.id,
});
const [meter] = await client.billing.meters.list();

if (subscription && meter) {
  await client.billing.usage.record({
    organization_id: organization.id,
    subscription_id: subscription.id,
    usage_meter_id: meter.id,
    quantity: 14,
    source: "partner_billing_sync",
    external_reference: "usage-sdk-001",
  });

  await client.billing.summary.get({
    organizationId: organization.id,
  });
}

const [metric] = await client.performance.metrics.list({
  organizationId: organization.id,
  sport: "football",
});

if (metric) {
  await client.performance.observations.create("athlete-profile-uuid", {
    organization_id: organization.id,
    metric_definition_id: metric.id,
    value: 8.7,
    source: "wearable",
    confidence: 0.91,
    verification_status: "pending_review",
  });
}

const drill = await client.training.drills.create({
  organization_id: organization.id,
  sport: "football",
  name: "Advanced Passing Circuit",
  focus_area: "Passing",
  category: "technical",
  description: "One-touch passing square with timed support angles.",
});

const plan = await client.training.plans.create({
  organization_id: organization.id,
  team_id: team.id,
  title: "Match-week training block",
  focus_area: "Transition speed",
  period_start: "2026-06-01",
  period_end: "2026-06-07",
  source_summary: "Imported from a partner coaching workspace.",
});

await client.training.plans.items.add(plan.id, { organizationId: organization.id }, {
  drill_id: drill.id,
  day_label: "Day 1",
  title: "Passing circuit progression",
  focus_area: "Passing",
  duration_minutes: 20,
  intensity: 6,
});

const session = await client.training.sessions.create({
  organization_id: organization.id,
  team_id: team.id,
  plan_id: plan.id,
  title: "Partner synced session",
  scheduled_for: "2026-06-03T15:00:00Z",
  duration_minutes: 75,
  rpe_target: 6,
});

await client.training.sessions.feedback.record(session.id, { organizationId: organization.id }, {
  readiness_score: 72,
  actual_rpe: 6,
  actual_duration_minutes: 74,
  completed: true,
  feedback: "Synced from the partner app after training.",
});

const calendar = await client.training.calendar.export({
  organizationId: organization.id,
  teamId: team.id,
  startsAt: "2026-06-01T00:00:00Z",
  endsAt: "2026-06-30T00:00:00Z",
});

const availability = await client.training.availability.suggest({
  organization_id: organization.id,
  team_id: team.id,
  starts_at: "2026-06-01T06:00:00Z",
  duration_minutes: 75,
});

const signatureOk = await verifyAfroLeteWebhookSignature({
  payload: rawWebhookBody,
  timestamp: request.headers.get("X-Afrolete-Webhook-Timestamp")!,
  signature: request.headers.get("X-Afrolete-Webhook-Signature")!,
  signingSecret: process.env.AFROLETE_WEBHOOK_SECRET!,
});
if (!signatureOk) {
  throw new Error("Invalid AfroLete webhook signature");
}
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It is
dependency-free and works in modern browsers, Node.js runtimes with `fetch`, and
edge runtimes. Webhook helpers verify the same timestamped HMAC-SHA256 contract
used by AfroLete developer webhook deliveries.

## Release Verification

Build and inspect the npm package from the repository root:

```bash
python scripts/verify_sdk_release.py --out-dir dist/sdk-release
```

The release verifier checks the backend-generated endpoint manifest, runs
`pnpm --filter @afrolete/sdk build`, creates the npm tarball, and checks that
`dist/index.js`, `dist/index.d.ts`, `dist/generated/sdk-endpoints.*`,
`README.md`, and package metadata are present before publication.
