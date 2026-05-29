"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api";
import {
  clearStoredAuthSession,
  completeKeycloakCallbackFromUrl,
  getStoredAuthSession,
  startKeycloakLogin,
  startKeycloakRegistration,
  type AuthSession
} from "@/lib/auth";
import { afroleteAuthMode, keycloakClientId, keycloakIssuer } from "@/lib/config";
import type {
  LocalIdentity,
  OrganizationDirectoryRead,
  OrganizationHandleAvailabilityRead,
  OrganizationOnboardingRead,
  OrganizationPublicSiteRead,
  SportFormat,
  OrganizationType,
  RegistrationPacketRead,
  RegistrationInquiryAccountReadinessRead,
  RegistrationInquiryRead,
  RegistrationPaymentSessionRead
} from "@/types/operations";

type RegistrationMode = "organization" | "player";

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
  registration_open: true,
  registration_fee_amount: "1000.00",
  registration_fee_currency: "KES",
  registration_payment_instructions: "Pay online after completing the family packet.",
  registration_required_documents: "proof_of_age, medical_information, guardian_consent, photo_release",
  launch_goal: "Register first athletes and invite guardians this week",
  starter_team_name: "U15 Development",
  starter_team_sport: "football",
  starter_team_sport_format: "team" as SportFormat,
  starter_team_age_group: "U15",
  starter_team_gender_category: "open",
  starter_team_season_label: "2026"
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
  payment_method: "mpesa",
  payment_reference: "",
  payment_status: "pending_verification"
};

function registrationAccountStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    linked: "account linked",
    pending_link: "sign-in ready",
    invite_ready: "account ready",
    account_review_required: "account review needed",
    phone_only: "email needed",
    missing_contact: "contact pending"
  };
  return labels[status] ?? status.replaceAll("_", " ");
}

export default function RegistrationPage() {
  const keycloakEnabled = afroleteAuthMode === "keycloak";
  const [mode, setMode] = useState<RegistrationMode>("organization");
  const [identity, setIdentity] = useState<LocalIdentity>(defaultIdentity);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [organizationForm, setOrganizationForm] = useState(defaultOrganizationForm);
  const [handleAvailability, setHandleAvailability] = useState<OrganizationHandleAvailabilityRead | null>(null);
  const [onboarding, setOnboarding] = useState<OrganizationOnboardingRead | null>(null);
  const [directoryQuery, setDirectoryQuery] = useState("");
  const [directoryType, setDirectoryType] = useState<OrganizationType | "">("");
  const [directory, setDirectory] = useState<OrganizationDirectoryRead[]>([]);
  const [selectedSite, setSelectedSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [inquiryForm, setInquiryForm] = useState(defaultInquiryForm);
  const [submittedInquiry, setSubmittedInquiry] = useState<RegistrationInquiryRead | null>(null);
  const [accountReadiness, setAccountReadiness] = useState<RegistrationInquiryAccountReadinessRead | null>(null);
  const [packetForm, setPacketForm] = useState(defaultPacketForm);
  const [registrationPacket, setRegistrationPacket] = useState<RegistrationPacketRead | null>(null);
  const [paymentSession, setPaymentSession] = useState<RegistrationPaymentSessionRead | null>(null);
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

    const hadCallback = new URLSearchParams(window.location.search).has("code");
    completeKeycloakCallbackFromUrl()
      .then((session) => {
        setAuthSession(session ?? getStoredAuthSession());
        if (hadCallback) {
          void restoreRegistrationContext();
        }
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
    void restoreRegistrationContext();
    // Directory search and optional launch deeplink are intentionally loaded once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const beginKeycloakLogin = () => {
    setBusy("keycloak");
    void startKeycloakLogin({ returnTo: currentRegistrationReturnTo(mode, selectedSite, submittedInquiry) }).catch((caught) => {
      setBusy("");
      setError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
    });
  };

  const beginKeycloakRegistration = () => {
    setBusy("keycloak");
    void startKeycloakRegistration({
      loginHint: organizationForm.contact_email || identity.email || undefined,
      returnTo: "/register?mode=organization"
    }).catch((caught) => {
      setBusy("");
      setError(caught instanceof Error ? caught.message : "Keycloak account creation failed");
    });
  };

  const beginFamilyKeycloakRegistration = () => {
    if (!selectedSite || !submittedInquiry) {
      return;
    }
    setBusy("family-keycloak");
    void startKeycloakRegistration({
      loginHint: submittedInquiry.email,
      returnTo: registrationReturnTo(selectedSite.slug, submittedInquiry)
    }).catch((caught) => {
      setBusy("");
      setError(caught instanceof Error ? caught.message : "Keycloak account creation failed");
    });
  };

  const beginFamilyKeycloakLogin = () => {
    if (!selectedSite || !submittedInquiry) {
      return;
    }
    setBusy("family-keycloak");
    void startKeycloakLogin({
      loginHint: submittedInquiry.email,
      prompt: "login",
      returnTo: registrationReturnTo(selectedSite.slug, submittedInquiry)
    }).catch((caught) => {
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
          starter_team_name: organizationForm.starter_team_name || null,
          starter_team_sport: organizationForm.starter_team_sport || organizationForm.primary_sport || null,
          starter_team_sport_format: organizationForm.starter_team_sport_format,
          starter_team_age_group: organizationForm.starter_team_age_group || null,
          starter_team_gender_category: organizationForm.starter_team_gender_category || null,
          starter_team_season_label: organizationForm.starter_team_season_label || null,
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
            brand_secondary_color: organizationForm.brand_secondary_color || null,
            registration_open: organizationForm.registration_open,
            registration_fee_amount: organizationForm.registration_fee_amount || null,
            registration_fee_currency: organizationForm.registration_fee_currency || null,
            registration_payment_instructions: organizationForm.registration_payment_instructions || null,
            registration_required_documents: splitCsv(organizationForm.registration_required_documents)
          }
        }
      });
      setOnboarding(created);
      setHandleAvailability(null);
      await searchDirectory(organizationForm.name);
    } catch (caught) {
      const suggestion = subdomainSuggestionFromError(caught);
      if (suggestion) {
        setOrganizationForm((current) => ({ ...current, subdomain: suggestion }));
        setError(`That public address is already taken. Suggested address ${suggestion} has been applied; submit again.`);
      } else {
        setError(caught instanceof Error ? caught.message : "Organization onboarding failed");
      }
    } finally {
      setBusy("");
    }
  };

  const checkOrganizationHandles = async () => {
    setBusy("handles");
    setError("");
    try {
      const params = new URLSearchParams();
      if (organizationForm.name.trim()) {
        params.set("name", organizationForm.name.trim());
      }
      if (organizationForm.subdomain.trim()) {
        params.set("subdomain", organizationForm.subdomain.trim());
      }
      const availability = await apiRequest<OrganizationHandleAvailabilityRead>(
        `/organizations/handles/availability?${params.toString()}`
      );
      setHandleAvailability(availability);
      if (availability.subdomain_available === false && availability.subdomain_suggestions[0]) {
        setError(`Public address is already taken. Use ${availability.subdomain_suggestions[0]} or choose another.`);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Address availability check failed");
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

  const loadPublicSite = async (siteIdentifier: string, busyKey = `site-${siteIdentifier}`) => {
    setBusy(busyKey);
    setError("");
    setSubmittedInquiry(null);
    setAccountReadiness(null);
    setRegistrationPacket(null);
    setPaymentSession(null);
    try {
      const site = await apiRequest<OrganizationPublicSiteRead>(`/organizations/public/${encodeURIComponent(siteIdentifier)}`);
      setSelectedSite(site);
      setInquiryForm((current) => ({
        ...current,
        sport_interest: current.sport_interest || site.primary_sport || "",
        team_id: ""
      }));
      setPacketForm((current) => ({
        ...current,
        payment_amount: site.registration_fee_amount ?? "",
        payment_currency: site.registration_fee_currency ?? current.payment_currency,
        payment_status: site.registration_fee_amount ? "pending" : "not_required"
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Organization site could not be loaded");
    } finally {
      setBusy("");
    }
  };

  const selectDirectoryItem = async (item: OrganizationDirectoryRead) => {
    await loadPublicSite(item.slug, `site-${item.id}`);
  };

  const loadAccountReadiness = async (siteSlug: string, inquiry: RegistrationInquiryRead) => {
    setAccountReadiness(null);
    try {
      const params = new URLSearchParams({ email: inquiry.email });
      const readiness = await apiRequest<RegistrationInquiryAccountReadinessRead>(
        `/organizations/public/${encodeURIComponent(siteSlug)}/registration-inquiries/${inquiry.id}/account-readiness?${params.toString()}`
      );
      setAccountReadiness(readiness);
    } catch {
      setAccountReadiness(null);
    }
  };

  const restoreRegistrationContext = async () => {
    const params = new URLSearchParams(window.location.search);
    const requestedMode = params.get("mode");
    const requestedSite = params.get("site");
    const inquiryId = params.get("inquiry_id");
    const email = params.get("email");

    if (requestedMode === "player" || requestedSite) {
      setMode("player");
    } else if (requestedMode === "organization") {
      setMode("organization");
    }

    if (!requestedSite) {
      await searchDirectory();
      return;
    }

    await loadPublicSite(requestedSite);
    await searchDirectory(requestedSite);
    if (inquiryId && email) {
      await restoreRegistrationPacket(requestedSite, inquiryId, email);
    }
  };

  const restoreRegistrationPacket = async (siteSlug: string, inquiryId: string, email: string) => {
    setBusy("restore-packet");
    setError("");
    try {
      const params = new URLSearchParams({ email });
      const packet = await apiRequest<RegistrationPacketRead>(
        `/organizations/public/${encodeURIComponent(siteSlug)}/registration-inquiries/${inquiryId}/packet?${params.toString()}`
      );
      setRegistrationPacket(packet);
      setSubmittedInquiry(packet.inquiry);
      setPacketForm((current) => ({
        ...current,
        date_of_birth: packet.inquiry.date_of_birth ?? current.date_of_birth,
        emergency_contact_name: packet.inquiry.emergency_contact_name ?? packet.inquiry.guardian_name ?? current.emergency_contact_name,
        emergency_contact_phone: packet.inquiry.emergency_contact_phone ?? packet.inquiry.phone ?? current.emergency_contact_phone,
        medical_notes: packet.inquiry.medical_notes ?? current.medical_notes,
        consent_signer_name: packet.inquiry.consent_signer_name ?? packet.inquiry.guardian_name ?? current.consent_signer_name,
        guardian_consent_acknowledged: packet.consent_complete,
        privacy_acknowledged: packet.inquiry.privacy_acknowledged_at !== null,
        proof_of_age_filename: documentFilename(packet, "proof_of_age") ?? current.proof_of_age_filename,
        medical_information_filename: documentFilename(packet, "medical_information") ?? current.medical_information_filename,
        guardian_consent_filename: documentFilename(packet, "guardian_consent") ?? current.guardian_consent_filename,
        photo_release_filename: documentFilename(packet, "photo_release") ?? current.photo_release_filename,
        payment_amount: packet.inquiry.payment_amount ?? current.payment_amount,
        payment_currency: packet.inquiry.payment_currency ?? current.payment_currency,
        payment_method: packet.inquiry.payment_method ?? current.payment_method,
        payment_reference: packet.inquiry.payment_reference ?? current.payment_reference,
        payment_status: packet.inquiry.payment_status ?? current.payment_status
      }));
      await loadAccountReadiness(siteSlug, packet.inquiry);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration packet could not be restored");
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
      setPaymentSession(null);
      await loadAccountReadiness(selectedSite.slug, inquiry);
      setPacketForm((current) => ({
        ...current,
        emergency_contact_name: inquiry.guardian_name ?? current.emergency_contact_name,
        emergency_contact_phone: inquiry.phone ?? current.emergency_contact_phone,
        consent_signer_name: inquiry.guardian_name ?? current.consent_signer_name,
        medical_information_filename: `${inquiry.athlete_name.replaceAll(" ", "-").toLowerCase()}-medical.pdf`,
        payment_amount: inquiry.payment_amount ?? current.payment_amount,
        payment_currency: inquiry.payment_currency ?? current.payment_currency,
        payment_method: inquiry.payment_method ?? current.payment_method,
        payment_status: inquiry.payment_status ?? current.payment_status
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration inquiry failed");
    } finally {
      setBusy("");
    }
  };

  const submitRegistrationPacket = async () => {
    if (!selectedSite || !submittedInquiry) {
      setError("Send the registration inquiry before completing the packet.");
      return;
    }
    setBusy("packet");
    setError("");
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
          notes: null
        }));
      const packet = await apiRequest<RegistrationPacketRead>(
        `/organizations/public/${encodeURIComponent(selectedSite.slug)}/registration-inquiries/${submittedInquiry.id}/packet`,
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
      setPaymentSession(null);
      await loadAccountReadiness(selectedSite.slug, packet.inquiry);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration packet failed");
    } finally {
      setBusy("");
    }
  };

  const uploadRegistrationDocument = async (documentType: string, file: File) => {
    if (!selectedSite || !submittedInquiry) {
      setError("Send the registration inquiry before uploading documents.");
      return;
    }
    setBusy(`upload-${documentType}`);
    setError("");
    try {
      const contentBase64 = await readFileAsBase64(file);
      const packet = await apiRequest<RegistrationPacketRead>(
        `/organizations/public/${encodeURIComponent(selectedSite.slug)}/registration-inquiries/${submittedInquiry.id}/documents`,
        {
          method: "POST",
          body: {
            email: submittedInquiry.email,
            document_type: documentType,
            filename: file.name,
            content_type: file.type || "application/octet-stream",
            content_base64: contentBase64,
            notes: "Uploaded from registration form"
          }
        }
      );
      setRegistrationPacket(packet);
      setSubmittedInquiry(packet.inquiry);
      setPaymentSession(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Document upload failed");
    } finally {
      setBusy("");
    }
  };

  const createRegistrationPaymentSession = async () => {
    if (!selectedSite || !submittedInquiry) {
      setError("Send the registration inquiry before creating a payment link.");
      return;
    }
    setBusy("payment");
    setError("");
    try {
      const session = await apiRequest<RegistrationPaymentSessionRead>(
        `/organizations/public/${encodeURIComponent(selectedSite.slug)}/registration-inquiries/${submittedInquiry.id}/payment-session`,
        {
          method: "POST",
          body: {
            email: submittedInquiry.email,
            checkout_base_url: `${window.location.origin}/pay/sessions`,
            provider: "manual_gateway",
            payment_method: packetForm.payment_method || "mobile_money"
          }
        }
      );
      setPaymentSession(session);
      setSubmittedInquiry(session.inquiry);
      window.open(session.checkout_url, "_blank", "noopener,noreferrer");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration payment link could not be created");
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
              <div className="register-auth-actions">
                <button type="button" onClick={beginKeycloakRegistration} disabled={busy !== ""}>Create account</button>
                <button type="button" onClick={beginKeycloakLogin} disabled={busy !== ""}>Sign in</button>
              </div>
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
                <div className="register-handle-status">
                  <button type="button" onClick={checkOrganizationHandles} disabled={busy !== ""}>
                    {busy === "handles" ? "Checking" : "Check address"}
                  </button>
                  {handleAvailability ? (
                    <span>
                      {handleAvailability.subdomain_available === false
                        ? `Taken · try ${handleAvailability.subdomain_suggestions[0] ?? "another address"}`
                        : `Available · ${handleAvailability.desired_subdomain ?? handleAvailability.desired_slug}`}
                    </span>
                  ) : (
                    <span>Preflight the public site address before creating the workspace.</span>
                  )}
                  {handleAvailability?.subdomain_available === false && handleAvailability.subdomain_suggestions[0] ? (
                    <button
                      type="button"
                      onClick={() =>
                        setOrganizationForm({
                          ...organizationForm,
                          subdomain: handleAvailability.subdomain_suggestions[0]
                        })
                      }
                    >
                      Use suggestion
                    </button>
                  ) : null}
                </div>
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
                <label>
                  Registration fee
                  <input value={organizationForm.registration_fee_amount} onChange={(event) => setOrganizationForm({ ...organizationForm, registration_fee_amount: event.target.value })} />
                </label>
                <label>
                  Fee currency
                  <input maxLength={3} value={organizationForm.registration_fee_currency} onChange={(event) => setOrganizationForm({ ...organizationForm, registration_fee_currency: event.target.value.toUpperCase() })} />
                </label>
                <label className="register-checkbox">
                  <input
                    type="checkbox"
                    checked={organizationForm.registration_open}
                    onChange={(event) => setOrganizationForm({ ...organizationForm, registration_open: event.target.checked })}
                  />
                  Public registration open
                </label>
                <label className="register-wide">
                  Required documents
                  <input value={organizationForm.registration_required_documents} onChange={(event) => setOrganizationForm({ ...organizationForm, registration_required_documents: event.target.value })} />
                </label>
                <label className="register-wide">
                  Payment instructions
                  <textarea value={organizationForm.registration_payment_instructions} onChange={(event) => setOrganizationForm({ ...organizationForm, registration_payment_instructions: event.target.value })} />
                </label>
                <label className="register-wide">
                  Launch goal
                  <input value={organizationForm.launch_goal} onChange={(event) => setOrganizationForm({ ...organizationForm, launch_goal: event.target.value })} />
                </label>
                <label>
                  First team/program
                  <input value={organizationForm.starter_team_name} onChange={(event) => setOrganizationForm({ ...organizationForm, starter_team_name: event.target.value })} />
                </label>
                <label>
                  Team sport
                  <input value={organizationForm.starter_team_sport} onChange={(event) => setOrganizationForm({ ...organizationForm, starter_team_sport: event.target.value })} />
                </label>
                <label>
                  Format
                  <select
                    value={organizationForm.starter_team_sport_format}
                    onChange={(event) =>
                      setOrganizationForm({
                        ...organizationForm,
                        starter_team_sport_format: event.target.value as SportFormat
                      })
                    }
                  >
                    <option value="team">Team sport</option>
                    <option value="individual">Individual sport</option>
                    <option value="mixed">Mixed program</option>
                  </select>
                </label>
                <label>
                  Age group
                  <input value={organizationForm.starter_team_age_group} onChange={(event) => setOrganizationForm({ ...organizationForm, starter_team_age_group: event.target.value })} />
                </label>
                <label>
                  Gender/category
                  <input value={organizationForm.starter_team_gender_category} onChange={(event) => setOrganizationForm({ ...organizationForm, starter_team_gender_category: event.target.value })} />
                </label>
                <label>
                  Season
                  <input value={organizationForm.starter_team_season_label} onChange={(event) => setOrganizationForm({ ...organizationForm, starter_team_season_label: event.target.value })} />
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
                    <a href={onboarding.registration_page_path}>Open registration</a>
                    <a href={onboarding.admissions_path}>Review admissions</a>
                    <a href={onboarding.family_portal_path}>Family portal</a>
                  </div>
                  {onboarding.starter_team ? (
                    <p>
                      Starter program: {onboarding.starter_team.name} · {onboarding.starter_team.sport} ·{" "}
                      {onboarding.starter_team.age_group ?? "all ages"}
                    </p>
                  ) : null}
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
                <button type="submit" disabled={busy !== "" || !selectedSite || submittedInquiry !== null}>
                  {submittedInquiry ? "Inquiry sent" : busy === "inquiry" ? "Sending" : "Send inquiry"}
                </button>
              </div>
              {submittedInquiry ? (
                <div className="register-success">
                  <strong>Inquiry received</strong>
                  <span>
                    {submittedInquiry.athlete_name} · {submittedInquiry.status} · {submittedInquiry.verification_status}
                  </span>
                </div>
              ) : null}
              {submittedInquiry && selectedSite ? (
                <div className="registration-account-card">
                  <div>
                    <strong>{submittedInquiry.email}</strong>
                    <span>
                      {keycloakEnabled ? "Family account" : "Family portal"} ·{" "}
                      {accountReadiness
                        ? registrationAccountStatusLabel(accountReadiness.account_status)
                        : submittedInquiry.guardian_person_id
                          ? "contact ready"
                          : submittedInquiry.guardian_contact_status}
                    </span>
                  </div>
                  {keycloakEnabled ? (
                    <div>
                      {isSessionForInquiry(authSession, submittedInquiry) ? (
                        <a href={familyPortalHref(selectedSite.id, submittedInquiry)}>Continue in family portal</a>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={beginFamilyKeycloakRegistration}
                            disabled={busy !== "" || (accountReadiness !== null && !accountReadiness.can_create_account)}
                          >
                            Create account
                          </button>
                          <button
                            type="button"
                            onClick={beginFamilyKeycloakLogin}
                            disabled={busy !== "" || (accountReadiness !== null && !accountReadiness.can_sign_in)}
                          >
                            Sign in
                          </button>
                        </>
                      )}
                    </div>
                  ) : (
                    <a href={familyPortalHref(selectedSite.id, submittedInquiry)}>Open family portal</a>
                  )}
                </div>
              ) : null}
              {submittedInquiry ? (
                <div className="registration-packet">
                  <div>
                    <p className="section-label">Onboarding packet</p>
                    <h3>Documents, consent, payment, and verification</h3>
                  </div>
                  <div className="register-inline-grid">
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
                    <label className="register-wide">
                      Medical notes
                      <textarea
                        value={packetForm.medical_notes}
                        onChange={(event) => setPacketForm({ ...packetForm, medical_notes: event.target.value })}
                      />
                    </label>
                    <DocumentInput
                      label="Proof of age file"
                      documentType="proof_of_age"
                      value={packetForm.proof_of_age_filename}
                      onChange={(value) => setPacketForm({ ...packetForm, proof_of_age_filename: value })}
                      onUpload={uploadRegistrationDocument}
                      busy={busy}
                    />
                    <DocumentInput
                      label="Medical file"
                      documentType="medical_information"
                      value={packetForm.medical_information_filename}
                      onChange={(value) => setPacketForm({ ...packetForm, medical_information_filename: value })}
                      onUpload={uploadRegistrationDocument}
                      busy={busy}
                    />
                    <DocumentInput
                      label="Guardian consent file"
                      documentType="guardian_consent"
                      value={packetForm.guardian_consent_filename}
                      onChange={(value) => setPacketForm({ ...packetForm, guardian_consent_filename: value })}
                      onUpload={uploadRegistrationDocument}
                      busy={busy}
                    />
                    <DocumentInput
                      label="Photo release file"
                      documentType="photo_release"
                      value={packetForm.photo_release_filename}
                      onChange={(value) => setPacketForm({ ...packetForm, photo_release_filename: value })}
                      onUpload={uploadRegistrationDocument}
                      busy={busy}
                    />
                    <label>
                      Amount
                      <input
                        value={packetForm.payment_amount}
                        onChange={(event) => setPacketForm({ ...packetForm, payment_amount: event.target.value })}
                        placeholder="1000.00"
                      />
                    </label>
                    <label>
                      Currency
                      <input
                        value={packetForm.payment_currency}
                        onChange={(event) => setPacketForm({ ...packetForm, payment_currency: event.target.value.toUpperCase() })}
                        maxLength={3}
                      />
                    </label>
                    <label>
                      Payment method
                      <select
                        value={packetForm.payment_method}
                        onChange={(event) => setPacketForm({ ...packetForm, payment_method: event.target.value })}
                      >
                        <option value="mpesa">M-Pesa</option>
                        <option value="card">Card</option>
                        <option value="bank_transfer">Bank transfer</option>
                        <option value="cash">Cash</option>
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
                    <label>
                      Payment status
                      <select
                        value={packetForm.payment_status}
                        onChange={(event) => setPacketForm({ ...packetForm, payment_status: event.target.value })}
                      >
                        <option value="pending">Pending</option>
                        <option value="pending_verification">Pending verification</option>
                        <option value="paid">Paid</option>
                        <option value="waived">Waived</option>
                        <option value="not_required">Not required</option>
                      </select>
                    </label>
                    <label className="register-checkbox">
                      <input
                        type="checkbox"
                        checked={packetForm.privacy_acknowledged}
                        onChange={(event) => setPacketForm({ ...packetForm, privacy_acknowledged: event.target.checked })}
                      />
                      Privacy consent acknowledged
                    </label>
                    <label className="register-checkbox">
                      <input
                        type="checkbox"
                        checked={packetForm.guardian_consent_acknowledged}
                        onChange={(event) =>
                          setPacketForm({ ...packetForm, guardian_consent_acknowledged: event.target.checked })
                        }
                      />
                      Guardian consent acknowledged
                    </label>
                  </div>
                  <div className="public-registration-actions">
                    <button type="button" onClick={submitRegistrationPacket} disabled={busy !== ""}>
                      {busy === "packet" ? "Saving packet" : "Submit packet"}
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={createRegistrationPaymentSession}
                      disabled={busy !== "" || !packetForm.payment_amount}
                    >
                      {busy === "payment" ? "Preparing link" : "Open payment link"}
                    </button>
                  </div>
                  {paymentSession ? (
                    <div className="register-packet-result">
                      <strong>Payment link ready</strong>
                      <a href={paymentSession.checkout_url}>{paymentSession.hosted_checkout.registration_reference}</a>
                      <small>
                        {paymentSession.hosted_checkout.currency} {paymentSession.hosted_checkout.open_amount} ·{" "}
                        {paymentSession.hosted_checkout.session_status}
                      </small>
                    </div>
                  ) : null}
                  {registrationPacket ? (
                    <div className="register-packet-result">
                      <strong>{registrationPacket.packet_complete ? "Ready for verification" : "Packet needs attention"}</strong>
                      <span>
                        Missing: {registrationPacket.missing_documents.length ? registrationPacket.missing_documents.join(", ") : "none"}
                      </span>
                      {registrationPacket.submitted_documents.map((document) => (
                        <small key={`${document.document_type}-${document.checksum ?? document.filename}`}>
                          {document.document_type}: {document.filename} · {document.size_bytes ?? 0} bytes ·{" "}
                          {document.storage_url ?? "not stored"}
                        </small>
                      ))}
                      {registrationPacket.next_steps.map((step) => (
                        <small key={step}>{step}</small>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}
              {!submittedInquiry ? (
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
              ) : null}
            </form>
          </section>
        )}
      </section>
    </main>
  );
}

function DocumentInput({
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
    <label className="register-document-field">
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

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function subdomainSuggestionFromError(caught: unknown): string | null {
  if (!(caught instanceof ApiError) || caught.status !== 409) {
    return null;
  }
  const detail = caught.detail;
  if (!detail || typeof detail !== "object" || !("detail" in detail)) {
    return null;
  }
  const inner = (detail as { detail: unknown }).detail;
  if (!inner || typeof inner !== "object" || !("subdomain_suggestions" in inner)) {
    return null;
  }
  const suggestions = (inner as { subdomain_suggestions: unknown }).subdomain_suggestions;
  return Array.isArray(suggestions) && typeof suggestions[0] === "string" ? suggestions[0] : null;
}

function currentRegistrationReturnTo(
  mode: RegistrationMode,
  site: OrganizationPublicSiteRead | null,
  inquiry: RegistrationInquiryRead | null
): string {
  if (mode === "player" && site) {
    return registrationReturnTo(site.slug, inquiry);
  }
  return "/register?mode=organization";
}

function registrationReturnTo(siteSlug: string, inquiry: RegistrationInquiryRead | null): string {
  const params = new URLSearchParams({
    mode: "player",
    site: siteSlug
  });
  if (inquiry) {
    params.set("inquiry_id", inquiry.id);
    params.set("email", inquiry.email);
  }
  return `/register?${params.toString()}`;
}

function documentFilename(packet: RegistrationPacketRead, documentType: string): string | null {
  return packet.submitted_documents.find((document) => document.document_type === documentType)?.filename ?? null;
}

function isSessionForInquiry(session: AuthSession | null, inquiry: RegistrationInquiryRead): boolean {
  return normalizeEmail(session?.email) !== "" && normalizeEmail(session?.email) === normalizeEmail(inquiry.email);
}

function normalizeEmail(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

function familyPortalHref(organizationId: string, inquiry: RegistrationInquiryRead): string {
  const params = new URLSearchParams({
    organization_id: organizationId,
    inquiry_id: inquiry.id,
    guardian_email: inquiry.email,
    guardian_name: inquiry.guardian_name ?? inquiry.email,
    athlete_name: inquiry.athlete_name,
    autoload: "1"
  });
  return `/family?${params.toString()}`;
}
