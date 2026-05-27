"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { apiRequest } from "@/lib/api";
import type { AgentEthicalScorecardRead, OrganizationPublicSiteRead } from "@/types/operations";

export default function PublicAiScorecardPage({ params }: { params: { slug: string } }) {
  const [site, setSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [scorecard, setScorecard] = useState<AgentEthicalScorecardRead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    apiRequest<OrganizationPublicSiteRead>(`/organizations/public/${encodeURIComponent(params.slug)}`)
      .then((siteData) => {
        if (cancelled) {
          return;
        }
        setSite(siteData);
        setError("");
        return apiRequest<AgentEthicalScorecardRead>(
          `/agents/ethical-scorecard?organization_id=${siteData.id}`
        );
      })
      .then((scorecardData) => {
        if (!cancelled && scorecardData) {
          setScorecard(scorecardData);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "AI scorecard unavailable");
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

  const displayName = site?.public_name ?? site?.name ?? "AfroLete organization";

  if (error) {
    return (
      <main className="public-site-page public-ai-page" style={colors}>
        <section className="public-site-shell public-ai-error">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>AI scorecard</span>
            </div>
          </div>
          <h1>Scorecard unavailable</h1>
          <p>{error}</p>
        </section>
      </main>
    );
  }

  if (!site || !scorecard) {
    return (
      <main className="public-site-page public-ai-page" style={colors}>
        <section className="public-site-shell public-ai-error">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>Loading AI scorecard</span>
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="public-site-page public-ai-page" style={colors}>
      <section className="public-ai-hero">
        <div className="public-site-shell public-ai-hero-grid">
          <div className="public-site-brand">
            {site.logo_url ? <img src={site.logo_url} alt="" /> : <div className="mark">{initials(displayName)}</div>}
            <div>
              <strong>{displayName}</strong>
              <span>Public AI accountability scorecard</span>
            </div>
          </div>
          <div className="public-ai-copy">
            <p className="section-label">Ethical AI</p>
            <h1>{displayName} AI scorecard</h1>
            <p>{scorecard.public_summary}</p>
          </div>
          <div className="public-ai-score">
            <strong>{scorecard.score}</strong>
            <span>Grade {scorecard.grade}</span>
          </div>
        </div>
      </section>

      <section className="public-site-shell public-ai-panel">
        <div className="public-ai-metrics">
          <Metric label="Approved models" value={`${scorecard.approved_models}/${scorecard.total_models}`} />
          <Metric label="Blocked models" value={scorecard.blocked_models} />
          <Metric label="Undocumented models" value={scorecard.undocumented_models} />
          <Metric label="Fairness audits" value={scorecard.bias_audits} />
          <Metric label="Passing audits" value={scorecard.passing_bias_audits} />
          <Metric label="Failing audits" value={scorecard.failing_bias_audits} />
          <Metric label="Open mitigations" value={scorecard.open_mitigations} />
          <Metric label="Open appeals" value={scorecard.pending_appeals} />
          <Metric label="Resolved appeals" value={scorecard.resolved_appeals} />
          <Metric label="Human review queue" value={scorecard.human_review_required} />
          <Metric label="Ledger status" value={scorecard.ledger_valid ? "Valid" : "Review"} />
          <Metric label="Generated" value={formatDate(scorecard.generated_at)} />
        </div>

        <div className="public-ai-actions">
          <div>
            <p className="section-label">Improvement plan</p>
            <h2>What the organization is watching</h2>
          </div>
          <div>
            {scorecard.improvement_actions.map((action) => (
              <span key={action}>{action}</span>
            ))}
          </div>
        </div>

        <div className="public-ai-footer">
          <a href={`/site/${encodeURIComponent(site.slug)}`}>Organization site</a>
          <span>Published through AfroLete governance records</span>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
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
  return new Date(value).toLocaleDateString();
}
