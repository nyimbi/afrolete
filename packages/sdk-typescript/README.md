# AfroLete TypeScript SDK

Repository package for tenant-facing AfroLete developer APIs.

```ts
import { AfroLeteClient } from "@afrolete/sdk";

const client = new AfroLeteClient({
  baseUrl: "https://api.afrolete.example",
  apiKey: process.env.AFROLETE_API_KEY!,
});

const organization = await client.organization.get({
  organizationId: process.env.AFROLETE_ORG_ID!,
});

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
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It is
dependency-free and works in modern browsers, Node.js runtimes with `fetch`, and
edge runtimes.
