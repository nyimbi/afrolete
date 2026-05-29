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
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It is
dependency-free and works in modern browsers, Node.js runtimes with `fetch`, and
edge runtimes.
