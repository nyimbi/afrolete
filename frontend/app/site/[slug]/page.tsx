"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { useParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import type {
  AgentEthicalScorecardRead,
  OrganizationPublicSiteRead,
  VolunteerGroupApplicationRead,
  PublicVolunteerSignupRead,
  VolunteerOpportunityRead,
  RegistrationInquiryRead,
  RegistrationPacketRead,
  RegistrationPaymentSessionRead
} from "@/types/operations";

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Registration document could not be read"));
    reader.onload = () => {
      const result = String(reader.result ?? "");
      resolve(result.includes(",") ? result.split(",").pop() ?? "" : result);
    };
    reader.readAsDataURL(file);
  });
}

const defaultPacketForm = {
  date_of_birth: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  medical_notes: "",
  consent_signer_name: "",
  guardian_consent_acknowledged: false,
  privacy_acknowledged: false,
  proof_of_age_filename: "",
  medical_information_filename: "",
  guardian_consent_filename: "",
  photo_release_filename: "",
  payment_amount: "",
  payment_currency: "KES",
  payment_method: "mobile_money",
  payment_reference: "",
  payment_status: "pending"
};

export default function PublicOrganizationSitePage() {
  const params = useParams<{ slug?: string | string[] }>();
  const slug = routeParam(params.slug);
  const [site, setSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [scorecard, setScorecard] = useState<AgentEthicalScorecardRead | null>(null);
  const [volunteerOpportunities, setVolunteerOpportunities] = useState<VolunteerOpportunityRead[]>([]);
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
  const [volunteerSignup, setVolunteerSignup] = useState({
    opportunity_id: "",
    display_name: "",
    email: "",
    phone: "",
    availability: "",
    skills: "",
    emergency_contact: "",
    message: ""
  });
  const [volunteerGroupSignup, setVolunteerGroupSignup] = useState({
    opportunity_id: "",
    company_name: "",
    coordinator_name: "",
    coordinator_email: "",
    coordinator_phone: "",
    group_size: 8,
    requested_slots: 4,
    availability: "",
    skills: "",
    message: ""
  });
  const [submittedInquiry, setSubmittedInquiry] = useState<RegistrationInquiryRead | null>(null);
  const [packetForm, setPacketForm] = useState(defaultPacketForm);
  const [registrationPacket, setRegistrationPacket] = useState<RegistrationPacketRead | null>(null);
  const [paymentSession, setPaymentSession] = useState<RegistrationPaymentSessionRead | null>(null);
  const [submittedVolunteerSignup, setSubmittedVolunteerSignup] = useState<PublicVolunteerSignupRead | null>(null);
  const [submittedVolunteerGroup, setSubmittedVolunteerGroup] = useState<VolunteerGroupApplicationRead | null>(null);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [packetError, setPacketError] = useState("");
  const [volunteerFormError, setVolunteerFormError] = useState("");
  const [volunteerGroupFormError, setVolunteerGroupFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [packetBusy, setPacketBusy] = useState("");
  const [volunteerBusy, setVolunteerBusy] = useState(false);
  const [volunteerGroupBusy, setVolunteerGroupBusy] = useState(false);

  useEffect(() => {
    if (!slug) {
      return;
    }
    let cancelled = false;
    apiRequest<OrganizationPublicSiteRead>(`/organizations/public/${encodeURIComponent(slug)}`)
      .then((data) => {
        if (!cancelled) {
          setSite(data);
          setError("");
          void apiRequest<VolunteerOpportunityRead[]>(`/volunteers/public/${encodeURIComponent(data.slug)}/opportunities`)
            .then((opportunities) => {
              if (!cancelled) {
                setVolunteerOpportunities(opportunities);
              }
            })
            .catch(() => {
              if (!cancelled) {
                setVolunteerOpportunities([]);
              }
            });
          void apiRequest<AgentEthicalScorecardRead>(`/agents/ethical-scorecard?organization_id=${data.id}`)
            .then((scorecardData) => {
              if (!cancelled) {
                setScorecard(scorecardData);
              }
            })
            .catch(() => {
              if (!cancelled) {
                setScorecard(null);
              }
            });
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
  }, [slug]);

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
      setRegistrationPacket(null);
      setPaymentSession(null);
      setPacketForm((current) => ({
        ...current,
        emergency_contact_name: created.guardian_name ?? current.emergency_contact_name,
        emergency_contact_phone: created.phone ?? current.emergency_contact_phone,
        consent_signer_name: created.guardian_name ?? current.consent_signer_name,
        medical_information_filename: `${created.athlete_name.replaceAll(" ", "-").toLowerCase()}-medical.pdf`,
        payment_amount: created.payment_amount ?? current.payment_amount,
        payment_currency: created.payment_currency ?? current.payment_currency,
        payment_method: created.payment_method ?? current.payment_method,
        payment_status: created.payment_status ?? current.payment_status
      }));
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

  const submitRegistrationPacket = async () => {
    if (!site || !submittedInquiry) {
      setPacketError("Send the registration inquiry before completing the packet.");
      return;
    }
    setPacketBusy("packet");
    setPacketError("");
    try {
      const documents = [
        { document_type: "proof_of_age", filename: packetForm.proof_of_age_filename },
        { document_type: "medical_information", filename: packetForm.medical_information_filename },
        { document_type: "guardian_consent", filename: packetForm.guardian_consent_filename },
        { document_type: "photo_release", filename: packetForm.photo_release_filename }
      ]
        .filter((item) => item.filename.trim())
        .map((item) => ({
          document_type: item.document_type,
          filename: item.filename.trim(),
          storage_url: null,
          checksum: null,
          content_type: null,
          size_bytes: null,
          notes: null
        }));
      const packet = await apiRequest<RegistrationPacketRead>(
        `/organizations/public/${encodeURIComponent(site.slug)}/registration-inquiries/${submittedInquiry.id}/packet`,
        {
          method: "PATCH",
          body: {
            email: submittedInquiry.email,
            date_of_birth: packetForm.date_of_birth || null,
            emergency_contact_name: packetForm.emergency_contact_name || null,
            emergency_contact_phone: packetForm.emergency_contact_phone || null,
            medical_notes: packetForm.medical_notes || null,
            consent_signer_name: packetForm.consent_signer_name || null,
            guardian_consent_acknowledged: packetForm.guardian_consent_acknowledged,
            privacy_acknowledged: packetForm.privacy_acknowledged,
            documents,
            payment_amount: packetForm.payment_amount || null,
            payment_currency: packetForm.payment_currency || null,
            payment_method: packetForm.payment_method || null,
            payment_reference: packetForm.payment_reference || null,
            payment_status: packetForm.payment_status || null
          }
        }
      );
      setRegistrationPacket(packet);
      setSubmittedInquiry(packet.inquiry);
    } catch (caught) {
      setPacketError(caught instanceof Error ? caught.message : "Registration packet could not be saved");
    } finally {
      setPacketBusy("");
    }
  };

  const uploadRegistrationDocument = async (documentType: string, file: File) => {
    if (!site || !submittedInquiry) {
      setPacketError("Send the registration inquiry before uploading documents.");
      return;
    }
    setPacketBusy(`upload-${documentType}`);
    setPacketError("");
    try {
      const contentBase64 = await readFileAsBase64(file);
      const packet = await apiRequest<RegistrationPacketRead>(
        `/organizations/public/${encodeURIComponent(site.slug)}/registration-inquiries/${submittedInquiry.id}/documents`,
        {
          method: "POST",
          body: {
            email: submittedInquiry.email,
            document_type: documentType,
            filename: file.name,
            content_type: file.type || "application/octet-stream",
            content_base64: contentBase64,
            notes: "Uploaded from public registration form"
          }
        }
      );
      setRegistrationPacket(packet);
      setSubmittedInquiry(packet.inquiry);
    } catch (caught) {
      setPacketError(caught instanceof Error ? caught.message : "Registration document could not be uploaded");
    } finally {
      setPacketBusy("");
    }
  };

  const createRegistrationPaymentSession = async () => {
    if (!site || !submittedInquiry) {
      setPacketError("Send the registration inquiry before creating a payment link.");
      return;
    }
    setPacketBusy("payment");
    setPacketError("");
    try {
      const baseUrl = `${window.location.origin}/pay/sessions`;
      const session = await apiRequest<RegistrationPaymentSessionRead>(
        `/organizations/public/${encodeURIComponent(site.slug)}/registration-inquiries/${submittedInquiry.id}/payment-session`,
        {
          method: "POST",
          body: {
            email: submittedInquiry.email,
            checkout_base_url: baseUrl,
            provider: "manual_gateway",
            payment_method: packetForm.payment_method || "mobile_money"
          }
        }
      );
      setPaymentSession(session);
      setSubmittedInquiry(session.inquiry);
      window.open(session.checkout_url, "_blank", "noopener,noreferrer");
    } catch (caught) {
      setPacketError(caught instanceof Error ? caught.message : "Registration payment link could not be created");
    } finally {
      setPacketBusy("");
    }
  };

  const submitVolunteerSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setVolunteerBusy(true);
    setVolunteerFormError("");
    try {
      const created = await apiRequest<PublicVolunteerSignupRead>(
        `/volunteers/public/${encodeURIComponent(site.slug)}/signups`,
        {
          method: "POST",
          body: {
            opportunity_id: volunteerSignup.opportunity_id,
            display_name: volunteerSignup.display_name,
            email: volunteerSignup.email,
            phone: volunteerSignup.phone || null,
            availability: splitCsv(volunteerSignup.availability),
            skills: splitCsv(volunteerSignup.skills),
            emergency_contact: volunteerSignup.emergency_contact || null,
            message: volunteerSignup.message || null,
            source_url: window.location.href
          }
        }
      );
      setSubmittedVolunteerSignup(created);
      setVolunteerSignup({
        opportunity_id: "",
        display_name: "",
        email: "",
        phone: "",
        availability: "",
        skills: "",
        emergency_contact: "",
        message: ""
      });
    } catch (caught) {
      setVolunteerFormError(caught instanceof Error ? caught.message : "Volunteer signup could not be sent");
    } finally {
      setVolunteerBusy(false);
    }
  };

  const submitVolunteerGroupSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setVolunteerGroupBusy(true);
    setVolunteerGroupFormError("");
    try {
      const created = await apiRequest<VolunteerGroupApplicationRead>(
        `/volunteers/public/${encodeURIComponent(site.slug)}/group-signups`,
        {
          method: "POST",
          body: {
            opportunity_id: volunteerGroupSignup.opportunity_id,
            company_name: volunteerGroupSignup.company_name,
            coordinator_name: volunteerGroupSignup.coordinator_name,
            coordinator_email: volunteerGroupSignup.coordinator_email,
            coordinator_phone: volunteerGroupSignup.coordinator_phone || null,
            group_size: volunteerGroupSignup.group_size,
            requested_slots: volunteerGroupSignup.requested_slots,
            availability: splitCsv(volunteerGroupSignup.availability),
            skills: splitCsv(volunteerGroupSignup.skills),
            message: volunteerGroupSignup.message || null,
            source_url: window.location.href
          }
        }
      );
      setSubmittedVolunteerGroup(created);
      setVolunteerGroupSignup({
        opportunity_id: "",
        company_name: "",
        coordinator_name: "",
        coordinator_email: "",
        coordinator_phone: "",
        group_size: 8,
        requested_slots: 4,
        availability: "",
        skills: "",
        message: ""
      });
    } catch (caught) {
      setVolunteerGroupFormError(caught instanceof Error ? caught.message : "Group volunteer signup could not be sent");
    } finally {
      setVolunteerGroupBusy(false);
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
              {scorecard ? <a href={`/site/${encodeURIComponent(site.slug)}/ai-scorecard`}>AI scorecard</a> : null}
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

      {site.sponsors.length > 0 || site.fundraising_campaigns.length > 0 || site.ticket_products.length > 0 ? (
        <section className="public-site-shell public-site-support">
          <div className="public-site-support-heading">
            <div>
              <p className="section-label">Support</p>
              <h2>Back the program</h2>
            </div>
            <p>
              Sponsorship, fundraising, and match-day ticket offers are published from the organization commerce
              workspace.
            </p>
          </div>
          <div className="public-site-support-grid">
            <article>
              <h3>Partners</h3>
              <div className="public-site-list">
                {site.sponsors.slice(0, 4).map((sponsor) => (
                  <div key={sponsor.sponsor_id}>
                    <strong>{sponsor.name}</strong>
                    <span>
                      {sponsor.tier ?? sponsor.industry ?? "Partner"} · {sponsor.currency ?? ""}{" "}
                      {sponsor.active_value}
                    </span>
                    {sponsor.deliverables.length > 0 ? <small>{sponsor.deliverables.join(" · ")}</small> : null}
                  </div>
                ))}
                {site.sponsors.length === 0 ? <span>No public partners yet</span> : null}
              </div>
            </article>
            <article>
              <h3>Fundraising</h3>
              <div className="public-site-list">
                {site.fundraising_campaigns.slice(0, 4).map((campaign) => (
                  <div key={campaign.id}>
                    <strong>{campaign.name}</strong>
                    <span>
                      {campaign.currency} {campaign.raised_amount} of {campaign.goal_amount} ·{" "}
                      {fundraisingPercent(campaign.raised_amount, campaign.goal_amount)}%
                    </span>
                    <small>{campaign.purpose}</small>
                    {campaign.public_url ? <a href={campaign.public_url}>Open campaign</a> : null}
                  </div>
                ))}
                {site.fundraising_campaigns.length === 0 ? <span>No public campaigns yet</span> : null}
              </div>
            </article>
            <article>
              <h3>Tickets</h3>
              <div className="public-site-list">
                {site.ticket_products.slice(0, 4).map((product) => (
                  <div key={product.id}>
                    <strong>{product.name}</strong>
                    <span>
                      {product.currency} {product.price} · {product.available_count}/{product.capacity} available
                    </span>
                    <small>
                      {product.event_title ?? "Event"} ·{" "}
                      {product.event_starts_at ? formatDate(product.event_starts_at) : "schedule pending"} ·{" "}
                      {product.venue_name ?? product.access_zone ?? "venue pending"}
                    </small>
                  </div>
                ))}
                {site.ticket_products.length === 0 ? <span>No public ticket offers yet</span> : null}
              </div>
            </article>
          </div>
        </section>
      ) : null}

      {volunteerOpportunities.length > 0 ? (
        <section className="public-site-shell public-site-inquiry public-site-volunteers">
          <div>
            <p className="section-label">Volunteers</p>
            <h2>Help run matchday</h2>
            <p>Apply for an open role and staff will confirm fit, training, and clearance requirements.</p>
            <div className="public-site-list">
              {volunteerOpportunities.slice(0, 4).map((opportunity) => (
                <div key={opportunity.id}>
                  <strong>{opportunity.title}</strong>
                  <span>
                    {opportunity.role_type.replaceAll("_", " ")} · {formatDate(opportunity.starts_at)} ·{" "}
                    {opportunity.open_slots} open
                  </span>
                  <small>
                    {opportunity.location ?? "Location pending"}
                    {opportunity.required_skills.length ? ` · ${opportunity.required_skills.join(" · ")}` : ""}
                  </small>
                </div>
              ))}
            </div>
          </div>
          {submittedVolunteerSignup ? (
            <div className="public-site-success">
              <strong>Volunteer signup received</strong>
              <span>
                {submittedVolunteerSignup.person_name} · {submittedVolunteerSignup.opportunity_title} ·{" "}
                {submittedVolunteerSignup.status}
              </span>
            </div>
          ) : (
            <form onSubmit={submitVolunteerSignup}>
              <label className="public-site-wide">
                Role
                <select
                  value={volunteerSignup.opportunity_id}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, opportunity_id: event.target.value })}
                  required
                >
                  <option value="">Choose a volunteer role</option>
                  {volunteerOpportunities.map((opportunity) => (
                    <option value={opportunity.id} key={opportunity.id}>
                      {opportunity.title}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Name
                <input
                  value={volunteerSignup.display_name}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, display_name: event.target.value })}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={volunteerSignup.email}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, email: event.target.value })}
                  required
                />
              </label>
              <label>
                Phone
                <input
                  value={volunteerSignup.phone}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, phone: event.target.value })}
                />
              </label>
              <label>
                Availability
                <input
                  value={volunteerSignup.availability}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, availability: event.target.value })}
                  placeholder="Saturday, evenings"
                />
              </label>
              <label>
                Skills
                <input
                  value={volunteerSignup.skills}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, skills: event.target.value })}
                  placeholder="First aid, timing"
                />
              </label>
              <label>
                Emergency contact
                <input
                  value={volunteerSignup.emergency_contact}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, emergency_contact: event.target.value })}
                />
              </label>
              <label className="public-site-wide">
                Message
                <textarea
                  value={volunteerSignup.message}
                  onChange={(event) => setVolunteerSignup({ ...volunteerSignup, message: event.target.value })}
                />
              </label>
              {volunteerFormError ? <p className="form-error public-site-wide">{volunteerFormError}</p> : null}
              <button type="submit" disabled={volunteerBusy}>{volunteerBusy ? "Sending" : "Apply to volunteer"}</button>
            </form>
          )}
          {submittedVolunteerGroup ? (
            <div className="public-site-success">
              <strong>Group application received</strong>
              <span>
                {submittedVolunteerGroup.company_name} · {submittedVolunteerGroup.requested_slots} requested ·{" "}
                {submittedVolunteerGroup.status}
              </span>
            </div>
          ) : (
            <form onSubmit={submitVolunteerGroupSignup}>
              <label className="public-site-wide">
                Group role
                <select
                  value={volunteerGroupSignup.opportunity_id}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, opportunity_id: event.target.value })
                  }
                  required
                >
                  <option value="">Choose a volunteer role</option>
                  {volunteerOpportunities.map((opportunity) => (
                    <option value={opportunity.id} key={opportunity.id}>
                      {opportunity.title}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Company
                <input
                  value={volunteerGroupSignup.company_name}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, company_name: event.target.value })
                  }
                  required
                />
              </label>
              <label>
                Coordinator
                <input
                  value={volunteerGroupSignup.coordinator_name}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, coordinator_name: event.target.value })
                  }
                  required
                />
              </label>
              <label>
                Coordinator email
                <input
                  type="email"
                  value={volunteerGroupSignup.coordinator_email}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, coordinator_email: event.target.value })
                  }
                  required
                />
              </label>
              <label>
                Coordinator phone
                <input
                  value={volunteerGroupSignup.coordinator_phone}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, coordinator_phone: event.target.value })
                  }
                />
              </label>
              <label>
                Group size
                <input
                  type="number"
                  min="2"
                  value={volunteerGroupSignup.group_size}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, group_size: Number(event.target.value) })
                  }
                />
              </label>
              <label>
                Slots requested
                <input
                  type="number"
                  min="1"
                  value={volunteerGroupSignup.requested_slots}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, requested_slots: Number(event.target.value) })
                  }
                />
              </label>
              <label>
                Group skills
                <input
                  value={volunteerGroupSignup.skills}
                  onChange={(event) => setVolunteerGroupSignup({ ...volunteerGroupSignup, skills: event.target.value })}
                  placeholder="Wayfinding, hospitality"
                />
              </label>
              <label>
                Group availability
                <input
                  value={volunteerGroupSignup.availability}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, availability: event.target.value })
                  }
                  placeholder="Saturday morning"
                />
              </label>
              <label className="public-site-wide">
                Group message
                <textarea
                  value={volunteerGroupSignup.message}
                  onChange={(event) =>
                    setVolunteerGroupSignup({ ...volunteerGroupSignup, message: event.target.value })
                  }
                />
              </label>
              {volunteerGroupFormError ? (
                <p className="form-error public-site-wide">{volunteerGroupFormError}</p>
              ) : null}
              <button type="submit" disabled={volunteerGroupBusy}>
                {volunteerGroupBusy ? "Sending" : "Apply as a group"}
              </button>
            </form>
          )}
        </section>
      ) : null}

      {scorecard ? (
        <section className="public-site-shell public-site-scorecard">
          <div>
            <p className="section-label">Ethical AI</p>
            <h2>Public AI scorecard</h2>
            <p>{scorecard.public_summary}</p>
          </div>
          <div className="public-site-score">
            <strong>{scorecard.score}</strong>
            <span>{scorecard.grade}</span>
          </div>
          <div className="public-site-score-grid">
            <div>
              <strong>{scorecard.approved_models}/{scorecard.total_models}</strong>
              <span>Models approved</span>
            </div>
            <div>
              <strong>{scorecard.bias_audits}</strong>
              <span>Fairness audits</span>
            </div>
            <div>
              <strong>{scorecard.pending_appeals}</strong>
              <span>Open appeals</span>
            </div>
            <div>
              <strong>{scorecard.ledger_valid ? "Valid" : "Review"}</strong>
              <span>Audit ledger</span>
            </div>
          </div>
          <div className="public-site-score-actions">
            {scorecard.improvement_actions.slice(0, 3).map((action) => (
              <span key={action}>{action}</span>
            ))}
            <a href={`/site/${encodeURIComponent(site.slug)}/ai-scorecard`}>Open public scorecard</a>
          </div>
        </section>
      ) : null}

      <section className="public-site-shell public-site-inquiry">
        <div>
          <p className="section-label">Registration</p>
          <h2>Join {displayName}</h2>
          <p>Send a player or family inquiry to the organization staff.</p>
          <div className="public-registration-settings">
            <strong>{site.registration_open ? "Registration open" : "Registration closed"}</strong>
            <span>
              Fee: {site.registration_fee_amount ? `${site.registration_fee_currency ?? "USD"} ${site.registration_fee_amount}` : "not required"}
            </span>
            {site.registration_required_documents.length ? (
              <span>Documents: {site.registration_required_documents.map((item) => item.replaceAll("_", " ")).join(", ")}</span>
            ) : null}
            {site.registration_payment_instructions ? <span>{site.registration_payment_instructions}</span> : null}
          </div>
        </div>
        {submittedInquiry ? (
          <div className="public-registration-packet">
            <div className="public-site-success">
              <strong>Inquiry received</strong>
              <span>{submittedInquiry.athlete_name} · {submittedInquiry.status} · {submittedInquiry.verification_status}</span>
            </div>
            <div className="public-registration-packet-head">
              <div>
                <p className="section-label">Registration packet</p>
                <h3>Documents, consent, and fees</h3>
              </div>
              <button type="button" onClick={submitRegistrationPacket} disabled={packetBusy !== ""}>
                {packetBusy === "packet" ? "Saving" : "Save packet"}
              </button>
            </div>
            <div className="public-registration-grid">
              <label>
                Date of birth
                <input
                  type="date"
                  value={packetForm.date_of_birth}
                  onChange={(event) => setPacketForm({ ...packetForm, date_of_birth: event.target.value })}
                />
              </label>
              <label>
                Emergency contact
                <input
                  value={packetForm.emergency_contact_name}
                  onChange={(event) => setPacketForm({ ...packetForm, emergency_contact_name: event.target.value })}
                />
              </label>
              <label>
                Emergency phone
                <input
                  value={packetForm.emergency_contact_phone}
                  onChange={(event) => setPacketForm({ ...packetForm, emergency_contact_phone: event.target.value })}
                />
              </label>
              <label>
                Consent signer
                <input
                  value={packetForm.consent_signer_name}
                  onChange={(event) => setPacketForm({ ...packetForm, consent_signer_name: event.target.value })}
                />
              </label>
              <label className="public-site-wide">
                Medical notes
                <textarea
                  value={packetForm.medical_notes}
                  onChange={(event) => setPacketForm({ ...packetForm, medical_notes: event.target.value })}
                />
              </label>
              <RegistrationDocumentInput
                label="Proof of age"
                documentType="proof_of_age"
                value={packetForm.proof_of_age_filename}
                onChange={(value) => setPacketForm({ ...packetForm, proof_of_age_filename: value })}
                onUpload={uploadRegistrationDocument}
                busy={packetBusy}
              />
              <RegistrationDocumentInput
                label="Medical information"
                documentType="medical_information"
                value={packetForm.medical_information_filename}
                onChange={(value) => setPacketForm({ ...packetForm, medical_information_filename: value })}
                onUpload={uploadRegistrationDocument}
                busy={packetBusy}
              />
              <RegistrationDocumentInput
                label="Guardian consent"
                documentType="guardian_consent"
                value={packetForm.guardian_consent_filename}
                onChange={(value) => setPacketForm({ ...packetForm, guardian_consent_filename: value })}
                onUpload={uploadRegistrationDocument}
                busy={packetBusy}
              />
              <RegistrationDocumentInput
                label="Photo release"
                documentType="photo_release"
                value={packetForm.photo_release_filename}
                onChange={(value) => setPacketForm({ ...packetForm, photo_release_filename: value })}
                onUpload={uploadRegistrationDocument}
                busy={packetBusy}
              />
              <label>
                Fee amount
                <input
                  value={packetForm.payment_amount}
                  onChange={(event) => setPacketForm({ ...packetForm, payment_amount: event.target.value })}
                  placeholder="1000.00"
                />
              </label>
              <label>
                Currency
                <input
                  maxLength={3}
                  value={packetForm.payment_currency}
                  onChange={(event) => setPacketForm({ ...packetForm, payment_currency: event.target.value.toUpperCase() })}
                />
              </label>
              <label>
                Payment method
                <select
                  value={packetForm.payment_method}
                  onChange={(event) => setPacketForm({ ...packetForm, payment_method: event.target.value })}
                >
                  <option value="mobile_money">Mobile money</option>
                  <option value="card">Card</option>
                  <option value="bank_transfer">Bank transfer</option>
                  <option value="cash_office">Cash office</option>
                  <option value="waiver">Waiver</option>
                </select>
              </label>
              <label>
                Payment reference
                <input
                  value={packetForm.payment_reference}
                  onChange={(event) => setPacketForm({ ...packetForm, payment_reference: event.target.value })}
                />
              </label>
              <label className="public-registration-checkbox">
                <input
                  type="checkbox"
                  checked={packetForm.privacy_acknowledged}
                  onChange={(event) => setPacketForm({ ...packetForm, privacy_acknowledged: event.target.checked })}
                />
                Privacy consent acknowledged
              </label>
              <label className="public-registration-checkbox">
                <input
                  type="checkbox"
                  checked={packetForm.guardian_consent_acknowledged}
                  onChange={(event) => setPacketForm({ ...packetForm, guardian_consent_acknowledged: event.target.checked })}
                />
                Guardian consent acknowledged
              </label>
            </div>
            <div className="public-registration-actions">
              <button type="button" onClick={submitRegistrationPacket} disabled={packetBusy !== ""}>
                {packetBusy === "packet" ? "Saving packet" : "Save packet"}
              </button>
              <button type="button" className="secondary" onClick={createRegistrationPaymentSession} disabled={packetBusy !== "" || !packetForm.payment_amount}>
                {packetBusy === "payment" ? "Preparing link" : "Open payment link"}
              </button>
            </div>
            {packetError ? <p className="form-error">{packetError}</p> : null}
            {paymentSession ? (
              <div className="public-site-success">
                <strong>Payment link ready</strong>
                <a href={paymentSession.checkout_url}>{paymentSession.hosted_checkout.registration_reference}</a>
              </div>
            ) : null}
            {registrationPacket ? (
              <div className="public-registration-summary">
                <strong>{registrationPacket.packet_complete ? "Ready for staff verification" : "Still needs attention"}</strong>
                <span>Missing: {registrationPacket.missing_documents.length ? registrationPacket.missing_documents.join(", ") : "none"}</span>
                {registrationPacket.submitted_documents.map((document) => (
                  <small key={`${document.document_type}-${document.checksum ?? document.filename}`}>
                    {document.document_type}: {document.filename} · {document.storage_url ?? "not stored"}
                  </small>
                ))}
                {registrationPacket.next_steps.map((step) => (
                  <small key={step}>{step}</small>
                ))}
              </div>
            ) : null}
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
            <button type="submit" disabled={busy || !site.registration_open}>
              {!site.registration_open ? "Registration closed" : busy ? "Sending" : "Send inquiry"}
            </button>
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

function routeParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function fundraisingPercent(raisedAmount: string, goalAmount: string): number {
  const raised = Number(raisedAmount);
  const goal = Number(goalAmount);
  if (!Number.isFinite(raised) || !Number.isFinite(goal) || goal <= 0) {
    return 0;
  }
  return Math.min(Math.round((raised / goal) * 100), 100);
}

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function RegistrationDocumentInput({
  label,
  documentType,
  value,
  onChange,
  onUpload,
  busy
}: {
  label: string;
  documentType: string;
  value: string;
  onChange: (value: string) => void;
  onUpload: (documentType: string, file: File) => void;
  busy: string;
}) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const uploadDisabled = busy !== "" || selectedFile === null;

  return (
    <label className="public-registration-document">
      {label}
      <span>
        <input
          type="file"
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null;
            setSelectedFile(file);
            onChange(file?.name ?? "");
          }}
        />
        <button type="button" onClick={() => selectedFile && onUpload(documentType, selectedFile)} disabled={uploadDisabled}>
          {busy === `upload-${documentType}` ? "Uploading" : "Upload"}
        </button>
      </span>
      {value ? <small>{value}</small> : null}
    </label>
  );
}
