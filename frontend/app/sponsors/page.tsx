"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type {
  LocalIdentity,
  SponsorPortalAgreementRead,
  SponsorPortalInvoiceRead,
  SponsorPortalRead
} from "@/types/operations";

const defaultSponsorIdentity: LocalIdentity = {
  sub: "kc-sponsor-1",
  email: "sponsor@example.com",
  name: "Sponsor Example"
};

export default function SponsorPortalPage() {
  const [identity, setIdentity] = useState<LocalIdentity>(defaultSponsorIdentity);
  const [organizationId, setOrganizationId] = useState("");
  const [portal, setPortal] = useState<SponsorPortalRead | null>(null);
  const [selectedAgreementId, setSelectedAgreementId] = useState("");
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("afrolete.sponsorPortal");
    if (!stored) {
      return;
    }
    try {
      const parsed = JSON.parse(stored) as { organizationId?: string; identity?: LocalIdentity };
      setOrganizationId(parsed.organizationId ?? "");
      setIdentity(parsed.identity ?? defaultSponsorIdentity);
    } catch {
      window.localStorage.removeItem("afrolete.sponsorPortal");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("afrolete.sponsorPortal", JSON.stringify({ organizationId, identity }));
  }, [identity, organizationId]);

  const selectedAgreement = useMemo(
    () => portal?.agreements.find((agreement) => agreement.id === selectedAgreementId) ?? portal?.agreements[0] ?? null,
    [portal?.agreements, selectedAgreementId]
  );
  const selectedInvoice = useMemo(
    () => portal?.invoices.find((invoice) => invoice.id === selectedInvoiceId) ?? portal?.invoices[0] ?? null,
    [portal?.invoices, selectedInvoiceId]
  );
  const sponsorName = portal?.sponsors[0]?.sponsor_name ?? identity.name;

  const loadPortal = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    setBusy(true);
    setError("");
    try {
      const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : "";
      const data = await apiRequest<SponsorPortalRead>(`/commercial/sponsor-portal${query}`, { identity });
      setPortal(data);
      setSelectedAgreementId((current) =>
        data.agreements.some((agreement) => agreement.id === current) ? current : data.agreements[0]?.id ?? ""
      );
      setSelectedInvoiceId((current) =>
        data.invoices.some((invoice) => invoice.id === current) ? current : data.invoices[0]?.id ?? ""
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sponsor portal unavailable");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="sponsor-page">
      <section className="sponsor-shell sponsor-hero">
        <div className="sponsor-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Sponsor portal</span>
          </div>
        </div>
        <div>
          <p className="section-label">Partner workspace</p>
          <h1>{sponsorName}</h1>
          <p>Track agreement value, deliverables, activation notes, invoices, and public-site exposure.</p>
        </div>
      </section>

      <section className="sponsor-shell sponsor-controls">
        <form onSubmit={loadPortal}>
          <label>
            Sponsor contact email
            <input
              type="email"
              value={identity.email}
              onChange={(event) => setIdentity({ ...identity, email: event.target.value })}
            />
          </label>
          <label>
            Contact name
            <input value={identity.name} onChange={(event) => setIdentity({ ...identity, name: event.target.value })} />
          </label>
          <label>
            Identity subject
            <input value={identity.sub} onChange={(event) => setIdentity({ ...identity, sub: event.target.value })} />
          </label>
          <label>
            Organization id
            <input
              value={organizationId}
              onChange={(event) => setOrganizationId(event.target.value)}
              placeholder="Optional"
            />
          </label>
          <button type="submit" disabled={busy}>{busy ? "Loading" : "Open portal"}</button>
        </form>
        {error ? <p className="form-error">{error}</p> : null}
      </section>

      {portal ? (
        <>
          <section className="sponsor-shell sponsor-metrics">
            <Metric label="Active value" value={`${portal.summary.active_value}`} />
            <Metric label="Outstanding" value={`${portal.summary.outstanding_invoice_amount}`} />
            <Metric label="Deliverables" value={portal.summary.deliverable_count} />
            <Metric label="Upcoming events" value={portal.summary.upcoming_event_count} />
          </section>

          <section className="sponsor-shell sponsor-layout">
            <article className="sponsor-panel sponsor-summary">
              <p className="section-label">Sponsor accounts</p>
              <h2>{portal.summary.sponsor_count} linked profile{portal.summary.sponsor_count === 1 ? "" : "s"}</h2>
              <p>{portal.summary.recommendation}</p>
              <div className="sponsor-list">
                {portal.sponsors.map((sponsor) => (
                  <div key={sponsor.id}>
                    <strong>{sponsor.sponsor_name}</strong>
                    <span>{sponsor.organization_name} · {sponsor.industry ?? "Partner"}</span>
                    <a href={sponsor.public_site_path}>Open public site</a>
                  </div>
                ))}
              </div>
            </article>

            <article className="sponsor-panel">
              <p className="section-label">Agreements</p>
              <h2>{portal.agreements.length} agreement{portal.agreements.length === 1 ? "" : "s"}</h2>
              <div className="sponsor-list">
                {portal.agreements.map((agreement) => (
                  <button
                    type="button"
                    key={agreement.id}
                    className={agreement.id === selectedAgreement?.id ? "selected" : ""}
                    onClick={() => setSelectedAgreementId(agreement.id)}
                  >
                    <strong>{agreement.name}</strong>
                    <span>{agreement.tier} · {agreement.currency} {agreement.value_amount} · {agreement.status}</span>
                  </button>
                ))}
                {portal.agreements.length === 0 ? <span>No linked agreements yet</span> : null}
              </div>
            </article>

            <article className="sponsor-panel">
              <p className="section-label">Invoices</p>
              <h2>{portal.invoices.length} invoice{portal.invoices.length === 1 ? "" : "s"}</h2>
              <div className="sponsor-list">
                {portal.invoices.map((invoice) => (
                  <button
                    type="button"
                    key={invoice.id}
                    className={invoice.id === selectedInvoice?.id ? "selected" : ""}
                    onClick={() => setSelectedInvoiceId(invoice.id)}
                  >
                    <strong>{invoice.invoice_number}</strong>
                    <span>
                      {invoice.currency} {invoice.outstanding_amount} due · {invoice.payment_session_status ?? invoice.status}
                    </span>
                  </button>
                ))}
                {portal.invoices.length === 0 ? <span>No sponsor invoices yet</span> : null}
              </div>
            </article>
          </section>

          <section className="sponsor-shell sponsor-detail-grid">
            <AgreementDetail agreement={selectedAgreement} />
            <InvoiceDetail invoice={selectedInvoice} />
          </section>
        </>
      ) : (
        <section className="sponsor-shell sponsor-empty">
          <strong>Enter the sponsor contact email used by an organization.</strong>
          <span>The portal opens only for matching sponsor contact records.</span>
        </section>
      )}
    </main>
  );
}

function AgreementDetail({ agreement }: { agreement: SponsorPortalAgreementRead | null }) {
  if (!agreement) {
    return (
      <article className="sponsor-panel">
        <p className="section-label">Activation</p>
        <h2>No agreement selected</h2>
      </article>
    );
  }

  return (
    <article className="sponsor-panel">
      <p className="section-label">Activation</p>
      <h2>{agreement.name}</h2>
      <dl className="sponsor-facts">
        <div>
          <dt>Organization</dt>
          <dd>{agreement.organization_name}</dd>
        </div>
        <div>
          <dt>Event</dt>
          <dd>{agreement.event_title ?? "No event linked"}</dd>
        </div>
        <div>
          <dt>Schedule</dt>
          <dd>{agreement.event_starts_at ? new Date(agreement.event_starts_at).toLocaleString() : "Pending"}</dd>
        </div>
        <div>
          <dt>Venue</dt>
          <dd>{agreement.event_venue_name ?? "Pending"}</dd>
        </div>
      </dl>
      <div className="sponsor-chip-row">
        {agreement.deliverables.map((deliverable) => <span key={deliverable}>{deliverable}</span>)}
        {agreement.deliverables.length === 0 ? <span>No deliverables listed</span> : null}
      </div>
      <p>{agreement.activation_notes ?? agreement.roi_notes ?? "Activation notes will appear here once staff publish them."}</p>
    </article>
  );
}

function InvoiceDetail({ invoice }: { invoice: SponsorPortalInvoiceRead | null }) {
  if (!invoice) {
    return (
      <article className="sponsor-panel">
        <p className="section-label">Invoice</p>
        <h2>No invoice selected</h2>
      </article>
    );
  }

  return (
    <article className="sponsor-panel">
      <p className="section-label">Invoice</p>
      <h2>{invoice.title}</h2>
      <dl className="sponsor-facts">
        <div>
          <dt>Invoice</dt>
          <dd>{invoice.invoice_number}</dd>
        </div>
        <div>
          <dt>Due</dt>
          <dd>{invoice.due_on ?? "No due date"}</dd>
        </div>
        <div>
          <dt>Paid</dt>
          <dd>{invoice.currency} {invoice.amount_paid}</dd>
        </div>
        <div>
          <dt>Outstanding</dt>
          <dd>{invoice.currency} {invoice.outstanding_amount}</dd>
        </div>
      </dl>
      <p>{invoice.memo ?? "Payment instructions and settlement references will appear here."}</p>
      {invoice.payment_session_url ? (
        <a className="sponsor-pay-link" href={invoice.payment_session_url}>
          Pay balance
        </a>
      ) : (
        <span className="sponsor-paid-note">No payment is due for this invoice.</span>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
