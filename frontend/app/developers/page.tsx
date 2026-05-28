"use client";

import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { DeveloperPublicDocsRead } from "@/types/operations";

export default function DeveloperDocsPage() {
  const [docs, setDocs] = useState<DeveloperPublicDocsRead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    apiRequest<DeveloperPublicDocsRead>("/developers/public/docs")
      .then((data) => {
        if (!cancelled) {
          setDocs(data);
          setError("");
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Developer docs unavailable");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeEvents = useMemo(
    () => docs?.webhook_events.filter((event) => event.emission_status === "active") ?? [],
    [docs?.webhook_events]
  );

  if (error) {
    return (
      <main className="developer-docs-page">
        <section className="developer-docs-shell developer-docs-error">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>Developer platform</span>
            </div>
          </div>
          <h1>Developer docs unavailable</h1>
          <p>{error}</p>
        </section>
      </main>
    );
  }

  if (!docs) {
    return (
      <main className="developer-docs-page">
        <section className="developer-docs-shell developer-docs-error">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>Loading developer platform</span>
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="developer-docs-page">
      <section className="developer-docs-hero">
        <div className="developer-docs-shell developer-docs-hero-grid">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>Developer platform {docs.version}</span>
            </div>
          </div>
          <div>
            <p className="section-label">Developer ecosystem</p>
            <h1>{docs.title}</h1>
            <p>{docs.authentication}</p>
          </div>
          <div className="developer-docs-terminal">
            <span>{docs.auth_header}</span>
            <strong>{docs.api_base_path}</strong>
            <small>{activeEvents.length} active event contract{activeEvents.length === 1 ? "" : "s"}</small>
          </div>
        </div>
      </section>

      <section className="developer-docs-shell developer-docs-metrics">
        <Metric label="Scopes" value={docs.scopes.length} />
        <Metric label="Webhook events" value={docs.webhook_events.length} />
        <Metric label="SDK surfaces" value={docs.sdks.length} />
        <Metric label="Marketplace lanes" value={docs.marketplace_categories.length} />
      </section>

      <section className="developer-docs-shell developer-docs-section">
        <div>
          <p className="section-label">Quickstarts</p>
          <h2>Build against live tenant APIs</h2>
        </div>
        <div className="developer-docs-quickstarts">
          {docs.quickstarts.map((quickstart) => (
            <article key={quickstart.title}>
              <div>
                <span>{quickstart.language}</span>
                <h3>{quickstart.title}</h3>
                <p>{quickstart.description}</p>
              </div>
              <ol>
                {quickstart.steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <pre>{quickstart.code_sample}</pre>
            </article>
          ))}
        </div>
      </section>

      <section className="developer-docs-shell developer-docs-two-column">
        <article>
          <p className="section-label">Scopes</p>
          <h2>Permission model</h2>
          <div className="developer-docs-list">
            {docs.scopes.map((scope) => (
              <div key={scope.scope}>
                <strong>{scope.scope}</strong>
                <span>{scope.category} · {scope.description}</span>
              </div>
            ))}
          </div>
        </article>
        <article>
          <p className="section-label">SDKs</p>
          <h2>Client surfaces</h2>
          <div className="developer-docs-list">
            {docs.sdks.map((sdk) => (
              <div key={sdk.language}>
                <strong>{sdk.language} · {sdk.status}</strong>
                <span>{sdk.install_command}</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="developer-docs-shell developer-docs-section">
        <div>
          <p className="section-label">Webhooks</p>
          <h2>Event contracts and signatures</h2>
          <p className="developer-docs-muted">
            Verify {docs.webhook_signature_header} with {docs.webhook_timestamp_header} before processing payloads.
          </p>
        </div>
        <div className="developer-docs-events">
          {docs.webhook_events.map((event) => (
            <article key={event.event_type}>
              <div>
                <strong>{event.event_type}</strong>
                <span>{event.category} · {event.emission_status}</span>
              </div>
              <p>{event.description}</p>
              <small>{event.payload_fields.join(", ")}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="developer-docs-shell developer-docs-footer">
        <div>
          <p className="section-label">Security</p>
          <h2>Production expectations</h2>
        </div>
        <div>
          {docs.security_requirements.map((requirement) => (
            <span key={requirement}>{requirement}</span>
          ))}
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
