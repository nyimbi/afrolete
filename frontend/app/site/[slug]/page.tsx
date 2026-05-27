"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { apiRequest } from "@/lib/api";
import type { OrganizationPublicSiteRead, RegistrationInquiryRead } from "@/types/operations";

export default function PublicOrganizationSitePage({ params }: { params: { slug: string } }) {
  const [site, setSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [inquiry, setInquiry] = useState({
    team_id: "",
    athlete_name: "",
    guardian_name: "",
    email: "",
    phone: "",
    age_group: "",
    sport_interest: "",
    message: ""
  });
  const [submittedInquiry, setSubmittedInquiry] = useState<RegistrationInquiryRead | null>(null);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiRequest<OrganizationPublicSiteRead>(`/organizations/public/${encodeURIComponent(params.slug)}`)
      .then((data) => {
        if (!cancelled) {
          setSite(data);
          setError("");
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Site not found");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [params.slug]);

  const colors = useMemo(
    () => ({
      "--site-primary": site?.brand_primary_color ?? "#0f766e",
      "--site-secondary": site?.brand_secondary_color ?? "#b7791f"
    }) as CSSProperties,
    [site?.brand_primary_color, site?.brand_secondary_color]
  );

  if (error) {
    return (
      <main className="public-site-page" style={colors}>
        <section className="public-site-shell">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>Organization site</span>
            </div>
          </div>
          <h1>Site unavailable</h1>
          <p>{error}</p>
        </section>
      </main>
    );
  }

  if (!site) {
    return (
      <main className="public-site-page" style={colors}>
        <section className="public-site-shell">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>Loading site</span>
            </div>
          </div>
        </section>
      </main>
    );
  }

  const displayName = site.public_name ?? site.name;

  const submitInquiry = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setFormError("");
    try {
      const created = await apiRequest<RegistrationInquiryRead>(
        `/organizations/public/${encodeURIComponent(site.slug)}/registration-inquiries`,
        {
          method: "POST",
          body: {
            team_id: inquiry.team_id || null,
            athlete_name: inquiry.athlete_name,
            guardian_name: inquiry.guardian_name || null,
            email: inquiry.email,
            phone: inquiry.phone || null,
            age_group: inquiry.age_group || null,
            sport_interest: inquiry.sport_interest || site.primary_sport,
            message: inquiry.message || null,
            source_url: window.location.href
          }
        }
      );
      setSubmittedInquiry(created);
      setInquiry({
        team_id: "",
        athlete_name: "",
        guardian_name: "",
        email: "",
        phone: "",
        age_group: "",
        sport_interest: "",
        message: ""
      });
    } catch (caught) {
      setFormError(caught instanceof Error ? caught.message : "Inquiry could not be sent");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="public-site-page" style={colors}>
      <section className="public-site-hero">
        <div className="public-site-shell">
          <div className="public-site-brand">
            {site.logo_url ? <img src={site.logo_url} alt="" /> : <div className="mark">{initials(displayName)}</div>}
            <div>
              <strong>{displayName}</strong>
              <span>{site.primary_sport ?? site.organization_type} · {site.country_code ?? "global"}</span>
            </div>
          </div>
          <div className="public-site-copy">
            <p className="section-label">{site.organization_type}</p>
            <h1>{displayName}</h1>
            <p>{site.mission ?? "A sports organization operating on AfroLete."}</p>
            <div className="public-site-actions">
              {site.contact_email ? <a href={`mailto:${site.contact_email}`}>Contact</a> : null}
              {site.website_url ? <a href={site.website_url}>Website</a> : null}
            </div>
          </div>
        </div>
      </section>

      <section className="public-site-shell public-site-grid">
        <article>
          <p className="section-label">Teams</p>
          <h2>{site.teams.length} squads</h2>
          <div className="public-site-list">
            {site.teams.map((team) => (
              <div key={team.id}>
                <strong>{team.name}</strong>
                <span>{team.sport} · {team.age_group ?? "open"} · {team.season_label ?? "active"}</span>
              </div>
            ))}
            {site.teams.length === 0 ? <span>No public teams yet</span> : null}
          </div>
        </article>
        <article>
          <p className="section-label">Schedule</p>
          <h2>{site.upcoming_events.length} upcoming</h2>
          <div className="public-site-list">
            {site.upcoming_events.map((event) => (
              <div key={event.id}>
                <strong>{event.title}</strong>
                <span>{event.event_type} · {formatDate(event.starts_at)} · {event.venue_name ?? "venue pending"}</span>
              </div>
            ))}
            {site.upcoming_events.length === 0 ? <span>No upcoming public events</span> : null}
          </div>
        </article>
      </section>

      <section className="public-site-shell public-site-inquiry">
        <div>
          <p className="section-label">Registration</p>
          <h2>Join {displayName}</h2>
          <p>Send a player or family inquiry to the organization staff.</p>
        </div>
        {submittedInquiry ? (
          <div className="public-site-success">
            <strong>Inquiry received</strong>
            <span>{submittedInquiry.athlete_name} · {submittedInquiry.status}</span>
          </div>
        ) : (
          <form onSubmit={submitInquiry}>
            <label>
              Athlete name
              <input
                value={inquiry.athlete_name}
                onChange={(event) => setInquiry({ ...inquiry, athlete_name: event.target.value })}
                required
              />
            </label>
            <label>
              Guardian name
              <input
                value={inquiry.guardian_name}
                onChange={(event) => setInquiry({ ...inquiry, guardian_name: event.target.value })}
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={inquiry.email}
                onChange={(event) => setInquiry({ ...inquiry, email: event.target.value })}
                required
              />
            </label>
            <label>
              Phone
              <input value={inquiry.phone} onChange={(event) => setInquiry({ ...inquiry, phone: event.target.value })} />
            </label>
            <label>
              Team
              <select value={inquiry.team_id} onChange={(event) => setInquiry({ ...inquiry, team_id: event.target.value })}>
                <option value="">Any suitable team</option>
                {site.teams.map((team) => (
                  <option value={team.id} key={team.id}>{team.name}</option>
                ))}
              </select>
            </label>
            <label>
              Age group
              <input
                value={inquiry.age_group}
                onChange={(event) => setInquiry({ ...inquiry, age_group: event.target.value })}
              />
            </label>
            <label>
              Sport interest
              <input
                value={inquiry.sport_interest}
                onChange={(event) => setInquiry({ ...inquiry, sport_interest: event.target.value })}
              />
            </label>
            <label className="public-site-wide">
              Message
              <textarea value={inquiry.message} onChange={(event) => setInquiry({ ...inquiry, message: event.target.value })} />
            </label>
            {formError ? <p className="form-error public-site-wide">{formError}</p> : null}
            <button type="submit" disabled={busy}>{busy ? "Sending" : "Send inquiry"}</button>
          </form>
        )}
      </section>
    </main>
  );
}

function initials(value: string): string {
  return value
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}
