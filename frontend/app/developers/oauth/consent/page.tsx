"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type {
  DeveloperApiScopeCatalogRead,
  DeveloperOAuthAuthorizationCreate,
  DeveloperOAuthAuthorizationRead,
  DeveloperPublicDocsRead,
  LocalIdentity
} from "@/types/operations";

const defaultIdentity: LocalIdentity = {
  sub: "kc-owner-1",
  email: "owner@example.com",
  name: "Owner Example"
};

const parseScopes = (value: string) =>
  value
    .split(/[,\s]+/)
    .map((scope) => scope.trim())
    .filter(Boolean);

export default function DeveloperOAuthConsentPage() {
  const [identity, setIdentity] = useState<LocalIdentity>(defaultIdentity);
  const [form, setForm] = useState({
    organization_id: "",
    client_id: "",
    redirect_uri: "",
    scopes: "read:organization",
    state: "",
    code_challenge: "",
    code_challenge_method: "S256"
  });
  const [scopeCatalog, setScopeCatalog] = useState<DeveloperApiScopeCatalogRead[]>([]);
  const [grant, setGrant] = useState<DeveloperOAuthAuthorizationRead | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const nextIdentity = {
      sub: params.get("manager_sub") ?? params.get("sub") ?? defaultIdentity.sub,
      email: params.get("manager_email") ?? params.get("email") ?? defaultIdentity.email,
      name: params.get("manager_name") ?? params.get("name") ?? defaultIdentity.name
    };
    setIdentity(nextIdentity);
    setForm({
      organization_id: params.get("organization_id") ?? "",
      client_id: params.get("client_id") ?? "",
      redirect_uri: params.get("redirect_uri") ?? "",
      scopes: params.get("scope") ?? params.get("scopes") ?? "read:organization",
      state: params.get("state") ?? "",
      code_challenge: params.get("code_challenge") ?? "",
      code_challenge_method: params.get("code_challenge_method") ?? "S256"
    });

    let cancelled = false;
    apiRequest<DeveloperPublicDocsRead>("/developers/public/docs")
      .then((docs) => {
        if (!cancelled) {
          setScopeCatalog(docs.scopes);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setScopeCatalog([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const requestedScopes = useMemo(() => parseScopes(form.scopes), [form.scopes]);
  const scopeDescriptions = useMemo(() => {
    const index = new Map(scopeCatalog.map((scope) => [scope.scope, scope]));
    return requestedScopes.map((scope) => ({
      scope,
      detail: index.get(scope)?.description ?? "Scope details unavailable"
    }));
  }, [requestedScopes, scopeCatalog]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setGrant(null);
    const payload: DeveloperOAuthAuthorizationCreate = {
      organization_id: form.organization_id,
      client_id: form.client_id,
      redirect_uri: form.redirect_uri,
      scopes: requestedScopes,
      state: form.state || null,
      code_challenge: form.code_challenge || null,
      code_challenge_method: form.code_challenge ? form.code_challenge_method : null
    };
    try {
      setGrant(
        await apiRequest<DeveloperOAuthAuthorizationRead>("/developers/oauth/authorizations", {
          method: "POST",
          identity,
          body: payload
        })
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "OAuth consent failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="developer-oauth-page">
      <section className="developer-oauth-shell">
        <div className="public-site-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Developer OAuth consent</span>
          </div>
        </div>
        <div className="developer-oauth-heading">
          <p className="section-label">Tenant authorization</p>
          <h1>Grant developer access</h1>
        </div>

        <form className="developer-oauth-form" onSubmit={submit}>
          <div className="developer-oauth-grid">
            <label>
              Organization
              <input
                required
                value={form.organization_id}
                onChange={(event) => setForm({ ...form, organization_id: event.target.value })}
              />
            </label>
            <label>
              Client ID
              <input
                required
                value={form.client_id}
                onChange={(event) => setForm({ ...form, client_id: event.target.value })}
              />
            </label>
            <label className="developer-oauth-wide">
              Redirect URI
              <input
                required
                value={form.redirect_uri}
                onChange={(event) => setForm({ ...form, redirect_uri: event.target.value })}
              />
            </label>
            <label className="developer-oauth-wide">
              Scopes
              <input
                required
                value={form.scopes}
                onChange={(event) => setForm({ ...form, scopes: event.target.value })}
              />
            </label>
            <label>
              Manager email
              <input
                required
                value={identity.email}
                onChange={(event) => setIdentity({ ...identity, email: event.target.value })}
              />
            </label>
            <label>
              Manager name
              <input
                required
                value={identity.name}
                onChange={(event) => setIdentity({ ...identity, name: event.target.value })}
              />
            </label>
            <label>
              Manager subject
              <input
                required
                value={identity.sub}
                onChange={(event) => setIdentity({ ...identity, sub: event.target.value })}
              />
            </label>
            <label>
              State
              <input value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })} />
            </label>
            <label>
              PKCE challenge
              <input
                value={form.code_challenge}
                onChange={(event) => setForm({ ...form, code_challenge: event.target.value })}
              />
            </label>
            <label>
              PKCE method
              <select
                value={form.code_challenge_method}
                onChange={(event) => setForm({ ...form, code_challenge_method: event.target.value })}
              >
                <option value="S256">S256</option>
                <option value="plain">Plain</option>
              </select>
            </label>
          </div>

          <div className="developer-oauth-scopes">
            {scopeDescriptions.map((scope) => (
              <article key={scope.scope}>
                <strong>{scope.scope}</strong>
                <span>{scope.detail}</span>
              </article>
            ))}
          </div>

          {error ? <p className="form-error">{error}</p> : null}

          <button type="submit" disabled={busy || requestedScopes.length === 0}>
            {busy ? "Granting..." : "Grant access"}
          </button>
        </form>

        {grant ? (
          <section className="developer-oauth-result">
            <div>
              <span>Authorization code</span>
              <strong>{grant.authorization_code}</strong>
            </div>
            <div>
              <span>Redirect</span>
              {grant.redirect_url ? <a href={grant.redirect_url}>{grant.redirect_url}</a> : <strong>{grant.redirect_uri}</strong>}
            </div>
            <div>
              <span>Expires</span>
              <strong>{new Date(grant.expires_at).toLocaleString()}</strong>
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}
