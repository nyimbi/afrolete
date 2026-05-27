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

## Backend Runtime

Set the API to Keycloak mode outside local tests:

```env
AFROLETE_AUTH_MODE=keycloak
AFROLETE_KEYCLOAK_ISSUER=https://auth.lindela.io/realms/lindela
AFROLETE_KEYCLOAK_AUDIENCE=afrolete-api
AFROLETE_KEYCLOAK_ALGORITHMS=RS256
```

The backend derives the JWKS URL from the issuer at
`/protocol/openid-connect/certs`, verifies issuer and audience, then provisions
or updates the local `app_users` and `persons` records from token identity
claims.
