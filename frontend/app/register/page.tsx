"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import {
  clearStoredAuthSession,
  completeKeycloakCallbackFromUrl,
  getStoredAuthSession,
  startKeycloakLogin,
  type AuthSession
} from "@/lib/auth";
import { afroleteAuthMode, keycloakClientId, keycloakIssuer } from "@/lib/config";
import type {
  LocalIdentity,
  OrganizationDirectoryRead,
  OrganizationOnboardingRead,
  OrganizationPublicSiteRead,
  OrganizationType,
  RegistrationInquiryRead
} from "@/types/operations";

type RegistrationMode = "organization" | "player";

const defaultIdentity: LocalIdentity = {
  name: "New Program Owner",
  email: "owner@example.com",
  sub: "local-onboarding-owner"
};

const defaultOrganizationForm = {
  name: "New Community Sports Club",
  organization_type: "club" as OrganizationType,
  public_name: "New Community Sports",
  subdomain: "new-community-sports",
  primary_sport: "football",
  country_code: "KE",
  contact_email: "hello@example.com",
  contact_phone: "",
  website_url: "",
  mission: "Create a trusted, measurable development pathway for athletes.",
  brand_primary_color: "#0f766e",
  brand_secondary_color: "#b7791f",
  launch_goal: "Register first athletes and invite guardians this week"
};

const defaultInquiryForm = {
  athlete_name: "",
  guardian_name: "",
  email: "",
  phone: "",
  age_group: "",
  sport_interest: "",
  team_id: "",
  message: ""
};

export default function RegistrationPage() {
  const keycloakEnabled = afroleteAuthMode === "keycloak";
  const [mode, setMode] = useState<RegistrationMode>("organization");
  const [identity, setIdentity] = useState<LocalIdentity>(defaultIdentity);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [organizationForm, setOrganizationForm] = useState(defaultOrganizationForm);
  const [onboarding, setOnboarding] = useState<OrganizationOnboardingRead | null>(null);
  const [directoryQuery, setDirectoryQuery] = useState("");
  const [directoryType, setDirectoryType] = useState<OrganizationType | "">("");
  const [directory, setDirectory] = useState<OrganizationDirectoryRead[]>([]);
  const [selectedSite, setSelectedSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [inquiryForm, setInquiryForm] = useState(defaultInquiryForm);
  const [submittedInquiry, setSubmittedInquiry] = useState<RegistrationInquiryRead | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const requestIdentity = useMemo(() => (keycloakEnabled ? undefined : identity), [identity, keycloakEnabled]);
  const signedInLabel = authSession?.email ?? authSession?.name ?? identity.email;

  useEffect(() => {
    if (!keycloakEnabled) {
      const stored = window.localStorage.getItem("afrolete.registrationIdentity");
      if (stored) {
        try {
          setIdentity(JSON.parse(stored) as LocalIdentity);
        } catch {
          window.localStorage.removeItem("afrolete.registrationIdentity");
        }
      }
      return;
    }

    completeKeycloakCallbackFromUrl()
      .then((session) => {
        setAuthSession(session ?? getStoredAuthSession());
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
      });
  }, [keycloakEnabled]);

  useEffect(() => {
    if (!keycloakEnabled) {
      window.localStorage.setItem("afrolete.registrationIdentity", JSON.stringify(identity));
    }
  }, [identity, keycloakEnabled]);

  useEffect(() => {
    void searchDirectory();
    // Directory search is intentionally loaded once; manual controls drive later searches.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const beginKeycloakLogin = () => {
    setBusy("keycloak");
    void startKeycloakLogin().catch((caught) => {
      setBusy("");
      setError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
    });
  };

  const signOut = () => {
    clearStoredAuthSession();
    setAuthSession(null);
  };

  const createOrganization = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (keycloakEnabled && !authSession) {
      setError("Sign in with Keycloak before creating a club or school.");
      return;
    }
    setBusy("organization");
    setError("");
    try {
      const created = await apiRequest<OrganizationOnboardingRead>("/organizations/onboarding", {
        method: "POST",
        identity: requestIdentity,
        body: {
          launch_goal: organizationForm.launch_goal || null,
          organization: {
            name: organizationForm.name,
            organization_type: organizationForm.organization_type,
            public_name: organizationForm.public_name || null,
            subdomain: organizationForm.subdomain || null,
            primary_sport: organizationForm.primary_sport || null,
            country_code: organizationForm.country_code || null,
            contact_email: organizationForm.contact_email || null,
            contact_phone: organizationForm.contact_phone || null,
            website_url: organizationForm.website_url || null,
            mission: organizationForm.mission || null,
            brand_primary_color: organizationForm.brand_primary_color || null,
            brand_secondary_color: organizationForm.brand_secondary_color || null
          }
        }
      });
      setOnboarding(created);
      await searchDirectory(organizationForm.name);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Organization onboarding failed");
    } finally {
      setBusy("");
    }
  };

  const searchDirectory = async (overrideQuery?: string) => {
    setBusy((current) => current || "directory");
    setError("");
    try {
      const params = new URLSearchParams({ limit: "12" });
      const query = overrideQuery ?? directoryQuery;
      if (query.trim()) {
        params.set("q", query.trim());
      }
      if (directoryType) {
        params.set("organization_type", directoryType);
      }
      const results = await apiRequest<OrganizationDirectoryRead[]>(`/organizations/directory?${params.toString()}`);
      setDirectory(results);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Organization search failed");
    } finally {
      setBusy((current) => (current === "directory" ? "" : current));
    }
  };

  const selectDirectoryItem = async (item: OrganizationDirectoryRead) => {
    setBusy(`site-${item.id}`);
    setError("");
    setSubmittedInquiry(null);
    try {
      const site = await apiRequest<OrganizationPublicSiteRead>(`/organizations/public/${encodeURIComponent(item.slug)}`);
      setSelectedSite(site);
      setInquiryForm((current) => ({
        ...current,
        sport_interest: current.sport_interest || site.primary_sport || "",
        team_id: ""
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Organization site could not be loaded");
    } finally {
      setBusy("");
    }
  };

  const submitInquiry = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedSite) {
      setError("Choose a club or school before sending registration details.");
      return;
    }
    setBusy("inquiry");
    setError("");
    try {
      const inquiry = await apiRequest<RegistrationInquiryRead>(
        `/organizations/public/${encodeURIComponent(selectedSite.slug)}/registration-inquiries`,
        {
          method: "POST",
          body: {
            athlete_name: inquiryForm.athlete_name,
            guardian_name: inquiryForm.guardian_name || null,
            email: inquiryForm.email,
            phone: inquiryForm.phone || null,
            age_group: inquiryForm.age_group || null,
            sport_interest: inquiryForm.sport_interest || selectedSite.primary_sport,
            team_id: inquiryForm.team_id || null,
            message: inquiryForm.message || null,
            source_url: window.location.href
          }
        }
      );
      setSubmittedInquiry(inquiry);
      setInquiryForm(defaultInquiryForm);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration inquiry failed");
    } finally {
      setBusy("");
    }
  };

  return (
    <main className="register-page">
      <section className="register-hero">
        <div className="register-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Registration</span>
          </div>
        </div>
        <div className="register-hero-copy">
          <p className="section-label">Self-service onboarding</p>
          <h1>Start a sports organization or join one already operating on AfroLete.</h1>
        </div>
        <div className="register-auth-card">
          <span>{keycloakEnabled ? "Keycloak" : "Local demo identity"}</span>
          <strong>{keycloakEnabled && !authSession ? "No browser session" : signedInLabel}</strong>
          {keycloakEnabled ? <small>{keycloakClientId} at {keycloakIssuer}</small> : <small>Used only by the local demo API headers.</small>}
          {keycloakEnabled ? (
            authSession ? (
              <button type="button" onClick={signOut}>Sign out</button>
            ) : (
              <button type="button" onClick={beginKeycloakLogin} disabled={busy !== ""}>Sign in</button>
            )
          ) : null}
        </div>
      </section>

      <section className="register-shell">
        <div className="register-mode-switch" aria-label="Registration mode">
          <button type="button" className={mode === "organization" ? "selected" : ""} onClick={() => setMode("organization")}>
            Club or school
          </button>
          <button type="button" className={mode === "player" ? "selected" : ""} onClick={() => setMode("player")}>
            Player or family
          </button>
        </div>

        {error ? <p className="form-error register-error">{error}</p> : null}

        {mode === "organization" ? (
          <section className="register-workspace">
            <form className="register-panel" onSubmit={createOrganization}>
              <div className="panel-head">
                <div>
                  <p className="section-label">Launch workspace</p>
                  <h2>Register a club, school, or academy</h2>
                </div>
                <button type="submit" disabled={busy !== "" || (keycloakEnabled && !authSession)}>
                  {busy === "organization" ? "Creating" : "Create workspace"}
                </button>
              </div>
              {!keycloakEnabled ? (
                <div className="register-inline-grid">
                  <label>
                    Owner name
                    <input value={identity.name} onChange={(event) => setIdentity({ ...identity, name: event.target.value })} />
                  </label>
                  <label>
                    Owner email
                    <input
                      type="email"
                      value={identity.email}
                      onChange={(event) =>
                        setIdentity({
                          ...identity,
                          email: event.target.value,
                          sub: event.target.value ? `local-${event.target.value}` : identity.sub
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
              <div className="register-inline-grid">
                <label>
                  Organization name
                  <input value={organizationForm.name} onChange={(event) => setOrganizationForm({ ...organizationForm, name: event.target.value })} required />
                </label>
                <label>
                  Type
                  <select
                    value={organizationForm.organization_type}
                    onChange={(event) => setOrganizationForm({ ...organizationForm, organization_type: event.target.value as OrganizationType })}
                  >
                    <option value="club">Club</option>
                    <option value="school">School</option>
                    <option value="academy">Academy</option>
                    <option value="association">Association</option>
                    <option value="federation">Federation</option>
                  </select>
                </label>
                <label>
                  Public name
                  <input value={organizationForm.public_name} onChange={(event) => setOrganizationForm({ ...organizationForm, public_name: event.target.value })} />
                </label>
                <label>
                  Subdomain
                  <input value={organizationForm.subdomain} onChange={(event) => setOrganizationForm({ ...organizationForm, subdomain: event.target.value })} />
                </label>
                <label>
                  Primary sport
                  <input value={organizationForm.primary_sport} onChange={(event) => setOrganizationForm({ ...organizationForm, primary_sport: event.target.value })} />
                </label>
                <label>
                  Country
                  <input maxLength={2} value={organizationForm.country_code} onChange={(event) => setOrganizationForm({ ...organizationForm, country_code: event.target.value.toUpperCase() })} />
                </label>
                <label>
                  Contact email
                  <input type="email" value={organizationForm.contact_email} onChange={(event) => setOrganizationForm({ ...organizationForm, contact_email: event.target.value })} />
                </label>
                <label>
                  Contact phone
                  <input value={organizationForm.contact_phone} onChange={(event) => setOrganizationForm({ ...organizationForm, contact_phone: event.target.value })} />
                </label>
                <label>
                  Brand color
                  <input value={organizationForm.brand_primary_color} onChange={(event) => setOrganizationForm({ ...organizationForm, brand_primary_color: event.target.value })} />
                </label>
                <label>
                  Accent color
                  <input value={organizationForm.brand_secondary_color} onChange={(event) => setOrganizationForm({ ...organizationForm, brand_secondary_color: event.target.value })} />
                </label>
                <label className="register-wide">
                  Launch goal
                  <input value={organizationForm.launch_goal} onChange={(event) => setOrganizationForm({ ...organizationForm, launch_goal: event.target.value })} />
                </label>
                <label className="register-wide">
                  Mission
                  <textarea value={organizationForm.mission} onChange={(event) => setOrganizationForm({ ...organizationForm, mission: event.target.value })} />
                </label>
              </div>
            </form>

            <aside className="register-panel register-result-panel">
              <p className="section-label">Next steps</p>
              {onboarding ? (
                <>
                  <h2>{onboarding.organization.public_name ?? onboarding.organization.name}</h2>
                  <div className="register-result-links">
                    <a href={onboarding.dashboard_path}>Open console</a>
                    <a href={onboarding.public_site_path}>Open public site</a>
                  </div>
                  <ol>
                    {onboarding.checklist.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                </>
              ) : (
                <>
                  <h2>One flow creates the tenant, owner role, public page, and operating checklist.</h2>
                  <p>Clubs and schools can start from an authenticated owner account and immediately publish registration.</p>
                </>
              )}
            </aside>
          </section>
        ) : (
          <section className="register-workspace">
            <div className="register-panel">
              <div className="panel-head">
                <div>
                  <p className="section-label">Find organization</p>
                  <h2>Choose a club or school</h2>
                </div>
                <button type="button" onClick={() => searchDirectory()} disabled={busy !== ""}>
                  {busy === "directory" ? "Searching" : "Search"}
                </button>
              </div>
              <div className="register-inline-grid">
                <label>
                  Search
                  <input value={directoryQuery} onChange={(event) => setDirectoryQuery(event.target.value)} placeholder="Club, school, sport, city" />
                </label>
                <label>
                  Type
                  <select value={directoryType} onChange={(event) => setDirectoryType(event.target.value as OrganizationType | "")}>
                    <option value="">Any</option>
                    <option value="club">Club</option>
                    <option value="school">School</option>
                    <option value="academy">Academy</option>
                    <option value="association">Association</option>
                  </select>
                </label>
              </div>
              <div className="register-directory">
                {directory.map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    className={selectedSite?.id === item.id ? "selected" : ""}
                    onClick={() => selectDirectoryItem(item)}
                  >
                    <strong>{item.public_name ?? item.name}</strong>
                    <span>{item.organization_type} · {item.primary_sport ?? "multi-sport"} · {item.country_code ?? "global"}</span>
                    <small>{item.team_count} teams · {item.upcoming_event_count} upcoming events</small>
                  </button>
                ))}
                {directory.length === 0 ? <span>No matching organizations yet.</span> : null}
              </div>
            </div>

            <form className="register-panel" onSubmit={submitInquiry}>
              <div className="panel-head">
                <div>
                  <p className="section-label">Player or family</p>
                  <h2>{selectedSite ? `Join ${selectedSite.public_name ?? selectedSite.name}` : "Send registration details"}</h2>
                </div>
                <button type="submit" disabled={busy !== "" || !selectedSite}>
                  {busy === "inquiry" ? "Sending" : "Send inquiry"}
                </button>
              </div>
              {submittedInquiry ? (
                <div className="register-success">
                  <strong>Inquiry received</strong>
                  <span>{submittedInquiry.athlete_name} · {submittedInquiry.status}</span>
                </div>
              ) : null}
              <div className="register-inline-grid">
                <label>
                  Athlete name
                  <input value={inquiryForm.athlete_name} onChange={(event) => setInquiryForm({ ...inquiryForm, athlete_name: event.target.value })} required />
                </label>
                <label>
                  Guardian name
                  <input value={inquiryForm.guardian_name} onChange={(event) => setInquiryForm({ ...inquiryForm, guardian_name: event.target.value })} />
                </label>
                <label>
                  Email
                  <input type="email" value={inquiryForm.email} onChange={(event) => setInquiryForm({ ...inquiryForm, email: event.target.value })} required />
                </label>
                <label>
                  Phone
                  <input value={inquiryForm.phone} onChange={(event) => setInquiryForm({ ...inquiryForm, phone: event.target.value })} />
                </label>
                <label>
                  Age group
                  <input value={inquiryForm.age_group} onChange={(event) => setInquiryForm({ ...inquiryForm, age_group: event.target.value })} />
                </label>
                <label>
                  Sport
                  <input value={inquiryForm.sport_interest} onChange={(event) => setInquiryForm({ ...inquiryForm, sport_interest: event.target.value })} />
                </label>
                <label className="register-wide">
                  Team
                  <select value={inquiryForm.team_id} onChange={(event) => setInquiryForm({ ...inquiryForm, team_id: event.target.value })}>
                    <option value="">Any suitable team</option>
                    {selectedSite?.teams.map((team) => (
                      <option key={team.id} value={team.id}>{team.name}</option>
                    ))}
                  </select>
                </label>
                <label className="register-wide">
                  Message
                  <textarea value={inquiryForm.message} onChange={(event) => setInquiryForm({ ...inquiryForm, message: event.target.value })} />
                </label>
              </div>
            </form>
          </section>
        )}
      </section>
    </main>
  );
}
