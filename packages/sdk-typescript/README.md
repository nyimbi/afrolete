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

await client.people.linkGuardian(athlete.id, {
  organization_id: organization.id,
  guardian_email: "parent@example.org",
  guardian_display_name: "Parent Otieno",
  relationship_kind: "parent",
  can_sign_consent: true,
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
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It is
dependency-free and works in modern browsers, Node.js runtimes with `fetch`, and
edge runtimes.
