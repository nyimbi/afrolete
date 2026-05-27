"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { apiRequest } from "@/lib/api";
import type { OrganizationPublicSiteRead } from "@/types/operations";

export default function PublicOrganizationSitePage({ params }: { params: { slug: string } }) {
  const [site, setSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [error, setError] = useState("");

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
