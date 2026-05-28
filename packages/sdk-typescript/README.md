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
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It is
dependency-free and works in modern browsers, Node.js runtimes with `fetch`, and
edge runtimes.
