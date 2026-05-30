"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { useParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import {
  completeKeycloakCallbackFromUrl,
  getStoredAuthSession,
  startKeycloakLogin,
  startKeycloakRegistration,
  type AuthSession
} from "@/lib/auth";
import { afroleteAuthMode } from "@/lib/config";
import type {
  AgentEthicalScorecardRead,
  FacilityBookingCheckoutRead,
  FacilityBookingWaitlistRead,
  FacilityPublicListingRead,
  OrganizationPublicSiteRead,
  PublicSupporterChallengeProgressRead,
  PublicSupporterSignupRead,
  VolunteerGroupApplicationRead,
  PublicVolunteerSignupRead,
  VolunteerOpportunityRead,
  RegistrationInquiryAccountReadinessRead,
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

const keycloakEnabled = afroleteAuthMode === "keycloak";

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

export default function PublicOrganizationSitePage() {
  const params = useParams<{ slug?: string | string[] }>();
  const slug = routeParam(params.slug);
  const [site, setSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [scorecard, setScorecard] = useState<AgentEthicalScorecardRead | null>(null);
  const [volunteerOpportunities, setVolunteerOpportunities] = useState<VolunteerOpportunityRead[]>([]);
  const [publicFacilities, setPublicFacilities] = useState<FacilityPublicListingRead[]>([]);
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
  const [supporterSignup, setSupporterSignup] = useState({
    tier_id: "",
    display_name: "",
    email: "",
    phone: "",
    interests: "matchday updates, challenges, merchandise",
    message: ""
  });
  const [facilityHireForm, setFacilityHireForm] = useState({
    facility_id: "",
    activity_type: "football training",
    title: "Community field hire",
    starts_at: "2026-06-13T10:00",
    duration_hours: 2,
    requester_name: "",
    requester_email: "",
    requester_phone: "",
    expected_attendees: 30,
    insurance_certificate_ref: "",
    special_requirements: "Goals and changing room access.",
    add_ons: "Locker room"
  });
  const [submittedInquiry, setSubmittedInquiry] = useState<RegistrationInquiryRead | null>(null);
  const [accountReadiness, setAccountReadiness] = useState<RegistrationInquiryAccountReadinessRead | null>(null);
  const [packetForm, setPacketForm] = useState(defaultPacketForm);
  const [registrationPacket, setRegistrationPacket] = useState<RegistrationPacketRead | null>(null);
  const [paymentSession, setPaymentSession] = useState<RegistrationPaymentSessionRead | null>(null);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [submittedVolunteerSignup, setSubmittedVolunteerSignup] = useState<PublicVolunteerSignupRead | null>(null);
  const [submittedVolunteerGroup, setSubmittedVolunteerGroup] = useState<VolunteerGroupApplicationRead | null>(null);
  const [submittedSupporter, setSubmittedSupporter] = useState<PublicSupporterSignupRead | null>(null);
  const [facilityBookingCheckout, setFacilityBookingCheckout] = useState<FacilityBookingCheckoutRead | null>(null);
  const [facilityWaitlistEntry, setFacilityWaitlistEntry] = useState<FacilityBookingWaitlistRead | null>(null);
  const [supporterChallengeProgress, setSupporterChallengeProgress] =
    useState<PublicSupporterChallengeProgressRead | null>(null);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [packetError, setPacketError] = useState("");
  const [volunteerFormError, setVolunteerFormError] = useState("");
  const [volunteerGroupFormError, setVolunteerGroupFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [packetBusy, setPacketBusy] = useState("");
  const [accountBusy, setAccountBusy] = useState("");
  const [volunteerBusy, setVolunteerBusy] = useState(false);
  const [volunteerGroupBusy, setVolunteerGroupBusy] = useState(false);
  const [supporterBusy, setSupporterBusy] = useState("");
  const [supporterFormError, setSupporterFormError] = useState("");
  const [facilityHireBusy, setFacilityHireBusy] = useState(false);
  const [facilityHireError, setFacilityHireError] = useState("");
  const [loadedResumeKey, setLoadedResumeKey] = useState("");

  useEffect(() => {
    if (!keycloakEnabled) {
      return;
    }
    completeKeycloakCallbackFromUrl()
      .then((session) => setAuthSession(session ?? getStoredAuthSession()))
      .catch((caught) => {
        setAuthSession(null);
        setPacketError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
      });
  }, []);

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
          void apiRequest<FacilityPublicListingRead[]>(
            `/assets/public/${encodeURIComponent(data.slug)}/facilities?starts_at=2026-06-01T00:00:00Z&ends_at=2026-07-15T00:00:00Z`
          )
            .then((facilities) => {
              if (!cancelled) {
                setPublicFacilities(facilities);
                setFacilityHireForm((current) =>
                  current.facility_id ? current : { ...current, facility_id: facilities[0]?.id ?? "" }
                );
              }
            })
            .catch(() => {
              if (!cancelled) {
                setPublicFacilities([]);
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

  useEffect(() => {
    if (!site?.supporter_tiers.length) {
      return;
    }
    setSupporterSignup((current) => (
      current.tier_id ? current : { ...current, tier_id: site.supporter_tiers[0]?.id ?? "" }
    ));
  }, [site?.supporter_tiers]);

  useEffect(() => {
    if (!site) {
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const inquiryId = params.get("inquiry_id") ?? params.get("inquiryId");
    const email = params.get("email") ?? params.get("guardian_email");
    if (!inquiryId || !email) {
      return;
    }
    const resumeKey = `${site.slug}:${inquiryId}:${email.toLowerCase()}`;
    if (loadedResumeKey === resumeKey) {
      return;
    }
    setLoadedResumeKey(resumeKey);
    setPacketBusy("resume");
    setPacketError("");
    const query = new URLSearchParams({ email });
    apiRequest<RegistrationPacketRead>(
      `/organizations/public/${encodeURIComponent(site.slug)}/registration-inquiries/${inquiryId}/packet?${query.toString()}`
    )
      .then((packet) => {
        const submittedByType = new Map(
          packet.submitted_documents.map((document) => [document.document_type, document.filename])
        );
        setRegistrationPacket(packet);
        setSubmittedInquiry(packet.inquiry);
        setPaymentSession(null);
        setPacketForm((current) => ({
          ...current,
          date_of_birth: packet.inquiry.date_of_birth ?? "",
          emergency_contact_name: packet.inquiry.emergency_contact_name ?? packet.inquiry.guardian_name ?? "",
          emergency_contact_phone: packet.inquiry.emergency_contact_phone ?? packet.inquiry.phone ?? "",
          medical_notes: packet.inquiry.medical_notes ?? "",
          consent_signer_name: packet.inquiry.consent_signer_name ?? packet.inquiry.guardian_name ?? "",
          proof_of_age_filename: submittedByType.get("proof_of_age") ?? current.proof_of_age_filename,
          medical_information_filename:
            submittedByType.get("medical_information") ?? current.medical_information_filename,
          guardian_consent_filename: submittedByType.get("guardian_consent") ?? current.guardian_consent_filename,
          photo_release_filename: submittedByType.get("photo_release") ?? current.photo_release_filename,
          payment_amount: packet.inquiry.payment_amount ?? current.payment_amount,
          payment_currency: packet.inquiry.payment_currency ?? current.payment_currency,
          payment_method: packet.inquiry.payment_method ?? current.payment_method,
          payment_reference: packet.inquiry.payment_reference ?? current.payment_reference,
          payment_status: packet.inquiry.payment_status ?? current.payment_status,
          privacy_acknowledged: packet.inquiry.privacy_acknowledged_at !== null,
          guardian_consent_acknowledged: packet.inquiry.guardian_consent_acknowledged_at !== null
        }));
        return apiRequest<RegistrationInquiryAccountReadinessRead>(
          `/organizations/public/${encodeURIComponent(site.slug)}/registration-inquiries/${packet.inquiry.id}/account-readiness?${query.toString()}`
        );
      })
      .then((readiness) => {
        setAccountReadiness(readiness);
      })
      .catch((caught) => {
        setPacketError(caught instanceof Error ? caught.message : "Registration packet could not be resumed");
      })
      .finally(() => {
        setPacketBusy("");
      });
  }, [loadedResumeKey, site]);

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
      await loadAccountReadiness(site.slug, created);
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
      await loadAccountReadiness(site.slug, packet.inquiry);
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

  const beginFamilyKeycloakRegistration = () => {
    if (!submittedInquiry || !site) {
      return;
    }
    setAccountBusy("registration");
    void startKeycloakRegistration({
      loginHint: submittedInquiry.email,
      returnTo: publicRegistrationReturnTo(site.slug, submittedInquiry)
    }).catch((caught) => {
      setAccountBusy("");
      setPacketError(caught instanceof Error ? caught.message : "Keycloak account creation failed");
    });
  };

  const beginFamilyKeycloakLogin = () => {
    if (!submittedInquiry || !site) {
      return;
    }
    setAccountBusy("login");
    void startKeycloakLogin({
      loginHint: submittedInquiry.email,
      prompt: "login",
      returnTo: publicRegistrationReturnTo(site.slug, submittedInquiry)
    }).catch((caught) => {
      setAccountBusy("");
      setPacketError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
    });
  };

  const submitFacilityHire = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!site || !facilityHireForm.facility_id) {
      setFacilityHireError("Choose a public facility first.");
      return;
    }
    setFacilityHireBusy(true);
    setFacilityHireError("");
    try {
      const startsAt = new Date(facilityHireForm.starts_at);
      const endsAt = new Date(startsAt.getTime() + facilityHireForm.duration_hours * 60 * 60_000);
      const checkout = await apiRequest<FacilityBookingCheckoutRead>(
        `/assets/public/${encodeURIComponent(site.slug)}/bookings`,
        {
          method: "POST",
          body: {
            facility_id: facilityHireForm.facility_id,
            activity_type: facilityHireForm.activity_type,
            title: facilityHireForm.title,
            starts_at: startsAt.toISOString(),
            ends_at: endsAt.toISOString(),
            requester_name: facilityHireForm.requester_name,
            requester_email: facilityHireForm.requester_email,
            requester_phone: facilityHireForm.requester_phone || null,
            expected_attendees: facilityHireForm.expected_attendees,
            insurance_certificate_ref: facilityHireForm.insurance_certificate_ref || null,
            special_requirements: facilityHireForm.special_requirements,
            add_ons: facilityHireForm.add_ons || null,
            provider: "manual_gateway",
            checkout_base_url: `${window.location.origin}/pay/sessions`
          }
        }
      );
      setFacilityBookingCheckout(checkout);
      window.open(checkout.checkout_url, "_blank", "noopener,noreferrer");
    } catch (caught) {
      setFacilityHireError(caught instanceof Error ? caught.message : "Facility booking could not be created");
    } finally {
      setFacilityHireBusy(false);
    }
  };

  const submitFacilityWaitlist = async () => {
    if (!site || !facilityHireForm.facility_id) {
      setFacilityHireError("Choose a public facility first.");
      return;
    }
    setFacilityHireBusy(true);
    setFacilityHireError("");
    try {
      const startsAt = new Date(facilityHireForm.starts_at);
      const endsAt = new Date(startsAt.getTime() + facilityHireForm.duration_hours * 60 * 60_000);
      const entry = await apiRequest<FacilityBookingWaitlistRead>(
        `/assets/public/${encodeURIComponent(site.slug)}/waitlist`,
        {
          method: "POST",
          body: {
            facility_id: facilityHireForm.facility_id,
            activity_type: facilityHireForm.activity_type,
            title: facilityHireForm.title,
            desired_starts_at: startsAt.toISOString(),
            desired_ends_at: endsAt.toISOString(),
            requester_name: facilityHireForm.requester_name,
            requester_email: facilityHireForm.requester_email,
            requester_phone: facilityHireForm.requester_phone || null,
            expected_attendees: facilityHireForm.expected_attendees,
            insurance_certificate_ref: facilityHireForm.insurance_certificate_ref || null,
            special_requirements: facilityHireForm.special_requirements,
            add_ons: facilityHireForm.add_ons || null
          }
        }
      );
      setFacilityWaitlistEntry(entry);
    } catch (caught) {
      setFacilityHireError(caught instanceof Error ? caught.message : "Facility waitlist request could not be created");
    } finally {
      setFacilityHireBusy(false);
    }
  };

  const submitSupporterSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSupporterBusy("signup");
    setSupporterFormError("");
    try {
      const supporter = await apiRequest<PublicSupporterSignupRead>(
        `/organizations/public/${encodeURIComponent(site.slug)}/supporters`,
        {
          method: "POST",
          body: {
            tier_id: supporterSignup.tier_id || null,
            display_name: supporterSignup.display_name,
            email: supporterSignup.email,
            phone: supporterSignup.phone || null,
            interests: splitCsv(supporterSignup.interests),
            message: supporterSignup.message || null,
            source_url: window.location.href
          }
        }
      );
      setSubmittedSupporter(supporter);
      setSupporterChallengeProgress(null);
      setSupporterSignup((current) => ({
        ...current,
        display_name: supporter.display_name,
        email: supporter.email,
        tier_id: supporter.tier_id ?? current.tier_id,
        phone: "",
        message: ""
      }));
    } catch (caught) {
      setSupporterFormError(caught instanceof Error ? caught.message : "Supporter signup could not be saved");
    } finally {
      setSupporterBusy("");
    }
  };

  const advancePublicFanChallenge = async (challengeId: string) => {
    const email = submittedSupporter?.email ?? supporterSignup.email;
    if (!email.trim()) {
      setSupporterFormError("Join with an email before recording challenge progress.");
      return;
    }
    setSupporterBusy(`challenge-${challengeId}`);
    setSupporterFormError("");
    try {
      const progress = await apiRequest<PublicSupporterChallengeProgressRead>(
        `/organizations/public/${encodeURIComponent(site.slug)}/fan-challenges/${challengeId}/progress`,
        {
          method: "POST",
          body: {
            email,
            progress_count: 1
          }
        }
      );
      setSupporterChallengeProgress(progress);
    } catch (caught) {
      setSupporterFormError(caught instanceof Error ? caught.message : "Challenge progress could not be saved");
    } finally {
      setSupporterBusy("");
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

      {publicFacilities.length > 0 ? (
        <section className="public-site-shell public-site-inquiry public-site-facilities">
          <div>
            <p className="section-label">Facility hire</p>
            <h2>Book public facility time</h2>
            <p>External teams, community groups, and event organizers can reserve published facilities and pay online.</p>
            <div className="public-site-list">
              {publicFacilities.slice(0, 4).map((facility) => (
                <div key={facility.id}>
                  <strong>{facility.name}</strong>
                  <span>
                    {facility.facility_type} · {facility.rate_summary}
                  </span>
                  <small>
                    {facility.next_available_slot ? `Next open ${formatDate(facility.next_available_slot)}` : "Staff calendar is full for this window"} ·{" "}
                    {facility.availability.conflict_count} conflicts
                  </small>
                </div>
              ))}
            </div>
            {facilityBookingCheckout ? (
              <div className="public-site-success">
                <strong>{facilityBookingCheckout.booking.public_booking_reference}</strong>
                <span>
                  {facilityBookingCheckout.booking.status} · {facilityBookingCheckout.invoice.currency}{" "}
                  {facilityBookingCheckout.invoice.amount_due} due
                </span>
                <a href={facilityBookingCheckout.checkout_url}>Open payment link</a>
              </div>
            ) : null}
            {facilityWaitlistEntry ? (
              <div className="public-site-success">
                <strong>{facilityWaitlistEntry.title}</strong>
                <span>
                  {facilityWaitlistEntry.status} waitlist · priority {facilityWaitlistEntry.priority_score}
                </span>
                <span>{new Date(facilityWaitlistEntry.desired_starts_at).toLocaleString()}</span>
              </div>
            ) : null}
          </div>
          <form onSubmit={submitFacilityHire}>
            <label className="public-site-wide">
              Facility
              <select
                value={facilityHireForm.facility_id}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, facility_id: event.target.value })}
                required
              >
                <option value="">Choose a facility</option>
                {publicFacilities.map((facility) => (
                  <option value={facility.id} key={facility.id}>
                    {facility.name} · {facility.public_rate}/hr
                  </option>
                ))}
              </select>
            </label>
            <label>
              Activity
              <input
                value={facilityHireForm.activity_type}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, activity_type: event.target.value })}
                required
              />
            </label>
            <label>
              Starts
              <input
                type="datetime-local"
                value={facilityHireForm.starts_at}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, starts_at: event.target.value })}
                required
              />
            </label>
            <label>
              Hours
              <input
                type="number"
                min="1"
                max="8"
                value={facilityHireForm.duration_hours}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, duration_hours: Number(event.target.value) })}
              />
            </label>
            <label>
              Attendees
              <input
                type="number"
                min="0"
                value={facilityHireForm.expected_attendees}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, expected_attendees: Number(event.target.value) })}
              />
            </label>
            <label>
              Name
              <input
                value={facilityHireForm.requester_name}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, requester_name: event.target.value })}
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={facilityHireForm.requester_email}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, requester_email: event.target.value })}
                required
              />
            </label>
            <label>
              Phone
              <input
                value={facilityHireForm.requester_phone}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, requester_phone: event.target.value })}
              />
            </label>
            <label>
              Insurance
              <input
                value={facilityHireForm.insurance_certificate_ref}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, insurance_certificate_ref: event.target.value })}
              />
            </label>
            <label className="public-site-wide">
              Booking title
              <input
                value={facilityHireForm.title}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, title: event.target.value })}
                required
              />
            </label>
            <label className="public-site-wide">
              Requirements
              <textarea
                value={facilityHireForm.special_requirements}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, special_requirements: event.target.value })}
              />
            </label>
            <label className="public-site-wide">
              Add-ons
              <input
                value={facilityHireForm.add_ons}
                onChange={(event) => setFacilityHireForm({ ...facilityHireForm, add_ons: event.target.value })}
              />
            </label>
            {facilityHireError ? <p className="form-error public-site-wide">{facilityHireError}</p> : null}
            <button type="submit" disabled={facilityHireBusy}>
              {facilityHireBusy ? "Preparing" : "Book and pay"}
            </button>
            <button type="button" disabled={facilityHireBusy} onClick={submitFacilityWaitlist}>
              Join waitlist
            </button>
          </form>
        </section>
      ) : null}

      <section className="public-site-shell public-site-inquiry public-site-fan-zone">
        <div>
          <p className="section-label">Fan zone</p>
          <h2>Support {displayName}</h2>
          <p>Join as a supporter, pick a tier, earn points, and take part in active public challenges.</p>
          <div className="public-registration-settings">
            <strong>{site.fan_leaderboard.length ? "Leaderboard live" : "Supporter program ready"}</strong>
            <span>{site.supporter_tiers.length} tiers · {site.fan_challenges.length} open challenges</span>
            <span>Top supporters earn badges, experiences, and staff-reviewed rewards.</span>
          </div>
          <div className="public-site-list">
            {site.fan_leaderboard.slice(0, 4).map((entry) => (
              <div key={entry.supporter_profile_id}>
                <strong>#{entry.rank} {entry.supporter_name}</strong>
                <span>{entry.engagement_points} points · {entry.completed_challenge_count} challenges</span>
                <small>{entry.tier_name ?? "Community supporter"}</small>
              </div>
            ))}
          </div>
        </div>
        <div className="public-supporter-workspace">
          {submittedSupporter ? (
            <div className="public-site-success">
              <strong>{submittedSupporter.display_name} joined the fan zone</strong>
              <span>
                {submittedSupporter.tier_name ?? "Supporter"} · {submittedSupporter.engagement_points} points ·{" "}
                {submittedSupporter.signup_status}
              </span>
              {submittedSupporter.next_actions.slice(0, 2).map((action) => (
                <small key={action}>{action}</small>
              ))}
            </div>
          ) : null}
          <form onSubmit={submitSupporterSignup}>
            <label>
              Supporter name
              <input
                value={supporterSignup.display_name}
                onChange={(event) => setSupporterSignup({ ...supporterSignup, display_name: event.target.value })}
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={supporterSignup.email}
                onChange={(event) => setSupporterSignup({ ...supporterSignup, email: event.target.value })}
                required
              />
            </label>
            <label>
              Tier
              <select
                value={supporterSignup.tier_id}
                onChange={(event) => setSupporterSignup({ ...supporterSignup, tier_id: event.target.value })}
              >
                <option value="">Community supporter</option>
                {site.supporter_tiers.map((tier) => (
                  <option value={tier.id} key={tier.id}>
                    {tier.name} · {tier.currency} {tier.monthly_price}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Phone
              <input
                value={supporterSignup.phone}
                onChange={(event) => setSupporterSignup({ ...supporterSignup, phone: event.target.value })}
              />
            </label>
            <label className="public-site-wide">
              Interests
              <input
                value={supporterSignup.interests}
                onChange={(event) => setSupporterSignup({ ...supporterSignup, interests: event.target.value })}
              />
            </label>
            <label className="public-site-wide">
              Message
              <textarea
                value={supporterSignup.message}
                onChange={(event) => setSupporterSignup({ ...supporterSignup, message: event.target.value })}
              />
            </label>
            {supporterFormError ? <p className="form-error public-site-wide">{supporterFormError}</p> : null}
            <button type="submit" disabled={supporterBusy !== ""}>
              {supporterBusy === "signup" ? "Joining" : submittedSupporter ? "Update supporter profile" : "Join fan zone"}
            </button>
          </form>
          <div className="public-site-support-grid public-fan-challenge-grid">
            {site.fan_challenges.slice(0, 4).map((challenge) => (
              <article key={challenge.id}>
                <h3>{challenge.title}</h3>
                <p>{challenge.description || "Complete the activity and earn supporter points."}</p>
                <div className="public-challenge-meter">
                  <span>{challenge.target_activity_type.replaceAll("_", " ")}</span>
                  <strong>{challenge.completion_count}/{challenge.target_count}</strong>
                </div>
                <small>
                  {challenge.points_reward} points
                  {challenge.badge_name ? ` · ${challenge.badge_name}` : ""}
                </small>
                <button
                  type="button"
                  onClick={() => advancePublicFanChallenge(challenge.id)}
                  disabled={supporterBusy !== "" || (!submittedSupporter && !supporterSignup.email)}
                >
                  {supporterBusy === `challenge-${challenge.id}` ? "Recording" : "Record progress"}
                </button>
              </article>
            ))}
            {site.fan_challenges.length === 0 ? (
              <article>
                <h3>Challenges opening soon</h3>
                <p>Staff can launch matchday, referral, voting, and merch challenges from the AfroLete console.</p>
              </article>
            ) : null}
          </div>
          {supporterChallengeProgress ? (
            <div className="public-site-success">
              <strong>{supporterChallengeProgress.challenge_title}</strong>
              <span>
                {supporterChallengeProgress.progress_count}/{supporterChallengeProgress.target_count} ·{" "}
                {supporterChallengeProgress.status} · {supporterChallengeProgress.points_awarded} points awarded
              </span>
            </div>
          ) : null}
        </div>
      </section>

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
                    <a href={familyPortalHref(site.id, submittedInquiry)}>Continue in family portal</a>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={beginFamilyKeycloakRegistration}
                        disabled={
                          accountBusy !== "" || (accountReadiness !== null && !accountReadiness.can_create_account)
                        }
                      >
                        {accountBusy === "registration" ? "Starting" : "Create account"}
                      </button>
                      <button
                        type="button"
                        onClick={beginFamilyKeycloakLogin}
                        disabled={accountBusy !== "" || (accountReadiness !== null && !accountReadiness.can_sign_in)}
                      >
                        {accountBusy === "login" ? "Starting" : "Sign in"}
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <a href={familyPortalHref(site.id, submittedInquiry)}>Open family portal</a>
              )}
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

function publicRegistrationReturnTo(siteSlug: string, inquiry: RegistrationInquiryRead): string {
  const params = new URLSearchParams({
    inquiry_id: inquiry.id,
    email: inquiry.email
  });
  return `/site/${encodeURIComponent(siteSlug)}?${params.toString()}`;
}

function isSessionForInquiry(session: AuthSession | null, inquiry: RegistrationInquiryRead): boolean {
  return normalizeEmail(session?.email) !== "" && normalizeEmail(session?.email) === normalizeEmail(inquiry.email);
}

function normalizeEmail(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase();
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
