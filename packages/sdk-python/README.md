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
```

The client sends `X-Afrolete-API-Key` and targets `/api/v1/sdk/*` routes. It
uses only the Python standard library, so it can run in small worker jobs,
serverless functions, and integration scripts without extra runtime packages.
