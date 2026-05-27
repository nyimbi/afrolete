# Keycloak Setup

Use the shared `lindela` realm.

## Clients

| Client | Type | Purpose |
| --- | --- | --- |
| `afrolete-web` | Browser client | Next/TypeScript frontend sign-in. |
| `afrolete-api` | API audience | Bearer token audience expected by FastAPI. |

## Required Claims

- `sub`
- `email`
- `preferred_username`
- `given_name`
- `family_name`
- `realm_access.roles`

The backend maps `sub` to `app_users.keycloak_sub` and uses the internal
`app_users.id` for SpiceDB relationships.

