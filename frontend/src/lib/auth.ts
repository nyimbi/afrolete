import { keycloakClientId, keycloakIssuer, keycloakScope } from "@/lib/config";

const SESSION_KEY = "afrolete.keycloakSession";
const STATE_KEY = "afrolete.pkceState";
const VERIFIER_KEY = "afrolete.pkceVerifier";

export type AuthSession = {
  accessToken: string;
  idToken?: string;
  refreshToken?: string;
  expiresAt: number;
  subject?: string;
  email?: string;
  name?: string;
};

export type KeycloakLoginOptions = {
  loginHint?: string;
  prompt?: "consent" | "login" | "none" | "select_account";
};

type TokenResponse = {
  access_token: string;
  id_token?: string;
  refresh_token?: string;
  expires_in?: number;
};

type JwtClaims = {
  sub?: string;
  email?: string;
  name?: string;
  preferred_username?: string;
};

export function getStoredAuthSession(): AuthSession | null {
  if (!isBrowser()) {
    return null;
  }

  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    const session = JSON.parse(raw) as AuthSession;
    if (!session.accessToken || session.expiresAt <= Date.now() + 30_000) {
      clearStoredAuthSession();
      return null;
    }
    return session;
  } catch {
    clearStoredAuthSession();
    return null;
  }
}

export function clearStoredAuthSession(): void {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.removeItem(SESSION_KEY);
  window.sessionStorage.removeItem(STATE_KEY);
  window.sessionStorage.removeItem(VERIFIER_KEY);
}

export async function startKeycloakLogin(options: KeycloakLoginOptions = {}): Promise<void> {
  assertBrowser();

  const verifier = randomString(64);
  const state = randomString(32);
  const challenge = await codeChallenge(verifier);

  window.sessionStorage.setItem(VERIFIER_KEY, verifier);
  window.sessionStorage.setItem(STATE_KEY, state);

  const url = new URL(`${keycloakIssuer}/protocol/openid-connect/auth`);
  url.searchParams.set("client_id", keycloakClientId);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("redirect_uri", redirectUri());
  url.searchParams.set("scope", keycloakScope);
  url.searchParams.set("state", state);
  url.searchParams.set("code_challenge", challenge);
  url.searchParams.set("code_challenge_method", "S256");
  if (options.loginHint) {
    url.searchParams.set("login_hint", options.loginHint);
  }
  if (options.prompt) {
    url.searchParams.set("prompt", options.prompt);
  }

  window.location.assign(url.toString());
}

export async function completeKeycloakCallbackFromUrl(): Promise<AuthSession | null> {
  if (!isBrowser()) {
    return null;
  }

  const url = new URL(window.location.href);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  if (!code && !state) {
    return getStoredAuthSession();
  }

  const expectedState = window.sessionStorage.getItem(STATE_KEY);
  const verifier = window.sessionStorage.getItem(VERIFIER_KEY);
  if (!code || !state || !expectedState || state !== expectedState || !verifier) {
    clearCallbackParams(url);
    throw new Error("Keycloak sign-in could not be verified. Please start sign-in again.");
  }

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: keycloakClientId,
    redirect_uri: redirectUri(),
    code,
    code_verifier: verifier
  });

  const response = await fetch(`${keycloakIssuer}/protocol/openid-connect/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json"
    },
    body
  });

  if (!response.ok) {
    clearCallbackParams(url);
    throw new Error(await tokenErrorMessage(response));
  }

  const token = (await response.json()) as TokenResponse;
  const session = sessionFromTokenResponse(token);
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  window.sessionStorage.removeItem(STATE_KEY);
  window.sessionStorage.removeItem(VERIFIER_KEY);
  clearCallbackParams(url);
  return session;
}

export function keycloakLogoutUrl(session: AuthSession | null): string {
  assertBrowser();

  const url = new URL(`${keycloakIssuer}/protocol/openid-connect/logout`);
  url.searchParams.set("post_logout_redirect_uri", redirectUri());
  if (session?.idToken) {
    url.searchParams.set("id_token_hint", session.idToken);
  }
  return url.toString();
}

function sessionFromTokenResponse(token: TokenResponse): AuthSession {
  const claims = decodeJwtClaims(token.id_token ?? token.access_token);
  return {
    accessToken: token.access_token,
    idToken: token.id_token,
    refreshToken: token.refresh_token,
    expiresAt: Date.now() + Math.max(token.expires_in ?? 300, 60) * 1000,
    subject: claims.sub,
    email: claims.email,
    name: claims.name ?? claims.preferred_username
  };
}

function clearCallbackParams(url: URL): void {
  url.searchParams.delete("code");
  url.searchParams.delete("state");
  url.searchParams.delete("session_state");
  url.searchParams.delete("iss");
  const query = url.searchParams.toString();
  window.history.replaceState(null, document.title, `${url.pathname}${query ? `?${query}` : ""}${url.hash}`);
}

function decodeJwtClaims(token: string): JwtClaims {
  if (!isBrowser()) {
    return {};
  }

  const [, payload] = token.split(".");
  if (!payload) {
    return {};
  }

  try {
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const binary = window.atob(padded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes)) as JwtClaims;
  } catch {
    return {};
  }
}

async function codeChallenge(verifier: string): Promise<string> {
  assertBrowser();
  const digest = await window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  return base64Url(new Uint8Array(digest));
}

function randomString(length: number): string {
  assertBrowser();
  const bytes = new Uint8Array(length);
  window.crypto.getRandomValues(bytes);
  return base64Url(bytes);
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return window.btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function redirectUri(): string {
  assertBrowser();
  return `${window.location.origin}${window.location.pathname}`;
}

async function tokenErrorMessage(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) {
    return "Keycloak token exchange failed.";
  }

  try {
    const parsed = JSON.parse(text) as { error_description?: string; error?: string };
    return parsed.error_description ?? parsed.error ?? "Keycloak token exchange failed.";
  } catch {
    return text;
  }
}

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function assertBrowser(): void {
  if (!isBrowser()) {
    throw new Error("Browser session is required.");
  }
}
