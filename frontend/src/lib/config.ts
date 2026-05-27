export type AfroleteAuthMode = "local" | "keycloak";

export const apiBaseUrl = process.env.NEXT_PUBLIC_AFROLETE_API_URL ?? "http://127.0.0.1:8000";

export const afroleteAuthMode: AfroleteAuthMode =
  process.env.NEXT_PUBLIC_AFROLETE_AUTH_MODE === "keycloak" ? "keycloak" : "local";

export const keycloakIssuer = stripTrailingSlash(
  process.env.NEXT_PUBLIC_AFROLETE_KEYCLOAK_ISSUER ?? "https://auth.lindela.io/realms/lindela"
);

export const keycloakClientId =
  process.env.NEXT_PUBLIC_AFROLETE_KEYCLOAK_CLIENT_ID ?? "afrolete-web";

export const keycloakScope =
  process.env.NEXT_PUBLIC_AFROLETE_KEYCLOAK_SCOPE ?? "openid profile email";

function stripTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
