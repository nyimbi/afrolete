"use client";

import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
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
  AgentTaskRead,
  LocalIdentity,
  OrganizationRead,
  RegistrationInquiryConversionRead,
  RegistrationInquiryFollowUpRead,
  RegistrationInquiryRead
} from "@/types/operations";

type AdmissionQueue = "all" | "ready" | "incomplete" | "paid" | "unpaid" | "converted";

type ReviewForm = {
  status: string;
  review_notes: string;
  follow_up_at: string;
  payment_status: string;
  payment_method: string;
  payment_reference: string;
};

const keycloakEnabled = afroleteAuthMode === "keycloak";

const defaultIdentity: LocalIdentity = {
  sub: "local-admissions-owner",
  email: "owner@example.com",
  name: "Admissions Owner"
};

const queueLabels: Record<AdmissionQueue, string> = {
  all: "All",
  ready: "Ready",
  incomplete: "Incomplete",
  paid: "Paid",
  unpaid: "Unpaid",
  converted: "Converted"
};

function readAdmissionsOrganizationId(): string {
  return new URLSearchParams(window.location.search).get("organization_id") ?? "";
}

function readAdmissionsQueue(): AdmissionQueue | null {
  const value = new URLSearchParams(window.location.search).get("queue");
  return value && value in queueLabels ? (value as AdmissionQueue) : null;
}

export default function AdmissionsPage() {
  const [identity, setIdentity] = useState<LocalIdentity>(defaultIdentity);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationRead[]>([]);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState("");
  const [inquiries, setInquiries] = useState<RegistrationInquiryRead[]>([]);
  const [agentTasks, setAgentTasks] = useState<AgentTaskRead[]>([]);
  const [reviewForms, setReviewForms] = useState<Record<string, ReviewForm>>({});
  const [queue, setQueue] = useState<AdmissionQueue>("all");
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [log, setLog] = useState<string[]>([]);

  const requestIdentity = useMemo(() => (keycloakEnabled ? undefined : identity), [identity]);
  const signedInLabel = authSession?.email ?? authSession?.name ?? identity.email;
  const selectedOrganization = organizations.find((organization) => organization.id === selectedOrganizationId) ?? null;

  useEffect(() => {
    const requestedQueue = readAdmissionsQueue();
    if (requestedQueue) {
      setQueue(requestedQueue);
    }
    if (!keycloakEnabled) {
      const stored = window.localStorage.getItem("afrolete.admissionsIdentity");
      if (stored) {
        try {
          setIdentity(JSON.parse(stored) as LocalIdentity);
        } catch {
          window.localStorage.removeItem("afrolete.admissionsIdentity");
        }
      }
      return;
    }

    completeKeycloakCallbackFromUrl()
      .then((session) => setAuthSession(session ?? getStoredAuthSession()))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Keycloak sign-in failed"));
  }, []);

  useEffect(() => {
    if (!keycloakEnabled) {
      window.localStorage.setItem("afrolete.admissionsIdentity", JSON.stringify(identity));
    }
  }, [identity]);

  useEffect(() => {
    if (keycloakEnabled && !authSession) {
      return;
    }
    void loadOrganizations();
    // Auth session and local identity intentionally drive the reload.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authSession, identity.email, identity.name, identity.sub]);

  useEffect(() => {
    if (selectedOrganizationId) {
      void loadInquiries(selectedOrganizationId);
      void loadAgentTasks(selectedOrganizationId);
    }
    // Explicit organization selection drives this load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedOrganizationId]);

  const metrics = useMemo(() => {
    const ready = inquiries.filter((inquiry) => inquiry.verification_status === "ready_for_review").length;
    const paid = inquiries.filter((inquiry) => ["paid", "waived", "not_required"].includes(inquiry.payment_status)).length;
    const converted = inquiries.filter((inquiry) => inquiry.status === "converted").length;
    const needsAction = inquiries.filter((inquiry) => inquiry.status !== "converted" && inquiry.verification_status !== "ready_for_review").length;
    return { ready, paid, converted, needsAction, total: inquiries.length };
  }, [inquiries]);

  const filteredInquiries = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return inquiries.filter((inquiry) => {
      const queueMatch =
        queue === "all"
          || (queue === "ready" && inquiry.verification_status === "ready_for_review")
          || (queue === "incomplete" && inquiry.verification_status !== "ready_for_review" && inquiry.status !== "converted")
          || (queue === "paid" && ["paid", "waived", "not_required"].includes(inquiry.payment_status))
          || (queue === "unpaid" && !["paid", "waived", "not_required"].includes(inquiry.payment_status))
          || (queue === "converted" && inquiry.status === "converted");
      if (!queueMatch) {
        return false;
      }
      if (!normalizedSearch) {
        return true;
      }
      return [
        inquiry.athlete_name,
        inquiry.guardian_name,
        inquiry.email,
        inquiry.phone,
        inquiry.age_group,
        inquiry.sport_interest,
        inquiry.status,
        inquiry.verification_status
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalizedSearch));
    });
  }, [inquiries, queue, search]);

  const beginKeycloakLogin = () => {
    setBusy("keycloak");
    void startKeycloakLogin().catch((caught) => {
      setBusy("");
      setError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
    });
  };

  const beginKeycloakRegistration = () => {
    setBusy("keycloak");
    void startKeycloakRegistration().catch((caught) => {
      setBusy("");
      setError(caught instanceof Error ? caught.message : "Keycloak account creation failed");
    });
  };

  const signOut = () => {
    clearStoredAuthSession();
    setAuthSession(null);
  };

  const loadOrganizations = async () => {
    setBusy("organizations");
    setError("");
    try {
      const loaded = await apiRequest<OrganizationRead[]>("/organizations", { identity: requestIdentity });
      setOrganizations(loaded);
      setSelectedOrganizationId((current) => {
        if (current) {
          return current;
        }
        const requestedOrganizationId = readAdmissionsOrganizationId();
        if (requestedOrganizationId && loaded.some((organization) => organization.id === requestedOrganizationId)) {
          return requestedOrganizationId;
        }
        return loaded[0]?.id || "";
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Organizations could not be loaded");
    } finally {
      setBusy("");
    }
  };

  const loadInquiries = async (organizationId: string) => {
    setBusy("inquiries");
    setError("");
    try {
      const loaded = await apiRequest<RegistrationInquiryRead[]>(
        `/organizations/${organizationId}/registration-inquiries`,
        { identity: requestIdentity }
      );
      setInquiries(loaded);
      setReviewForms((current) => {
        const next = { ...current };
        loaded.forEach((inquiry) => {
          next[inquiry.id] = next[inquiry.id] ?? {
            status: inquiry.status,
            review_notes: inquiry.review_notes ?? "",
            follow_up_at: toDateTimeLocalValue(inquiry.follow_up_at),
            payment_status: inquiry.payment_status,
            payment_method: inquiry.payment_method ?? "",
            payment_reference: inquiry.payment_reference ?? ""
          };
        });
        return next;
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration inquiries could not be loaded");
    } finally {
      setBusy("");
    }
  };

  const loadAgentTasks = async (organizationId: string) => {
    try {
      const loaded = await apiRequest<AgentTaskRead[]>(
        `/agents/tasks?organization_id=${organizationId}`,
        { identity: requestIdentity }
      );
      setAgentTasks(loaded.filter((task) => task.task_type === "registration_inquiry_review"));
    } catch {
      setAgentTasks([]);
    }
  };

  const updateReviewForm = (inquiry: RegistrationInquiryRead, field: keyof ReviewForm, value: string) => {
    setReviewForms((current) => ({
      ...current,
      [inquiry.id]: {
        status: current[inquiry.id]?.status ?? inquiry.status,
        review_notes: current[inquiry.id]?.review_notes ?? inquiry.review_notes ?? "",
        follow_up_at: current[inquiry.id]?.follow_up_at ?? toDateTimeLocalValue(inquiry.follow_up_at),
        payment_status: current[inquiry.id]?.payment_status ?? inquiry.payment_status,
        payment_method: current[inquiry.id]?.payment_method ?? inquiry.payment_method ?? "",
        payment_reference: current[inquiry.id]?.payment_reference ?? inquiry.payment_reference ?? "",
        [field]: value
      }
    }));
  };

  const saveReview = async (inquiry: RegistrationInquiryRead, statusOverride?: string) => {
    if (!selectedOrganizationId) {
      setError("Choose an organization before reviewing admissions.");
      return;
    }
    const form = reviewForms[inquiry.id] ?? {
      status: inquiry.status,
      review_notes: inquiry.review_notes ?? "",
      follow_up_at: toDateTimeLocalValue(inquiry.follow_up_at),
      payment_status: inquiry.payment_status,
      payment_method: inquiry.payment_method ?? "",
      payment_reference: inquiry.payment_reference ?? ""
    };
    const nextStatus = statusOverride ?? form.status;
    setBusy(`review-${inquiry.id}`);
    setError("");
    try {
      const body: {
        status?: string;
        review_notes: string | null;
        follow_up_at: string | null;
        payment_status: string;
        payment_method: string | null;
        payment_reference: string | null;
      } = {
        review_notes: form.review_notes || null,
        follow_up_at: form.follow_up_at ? new Date(form.follow_up_at).toISOString() : null,
        payment_status: form.payment_status,
        payment_method: form.payment_method || null,
        payment_reference: form.payment_reference || null
      };
      if (nextStatus !== "converted") {
        body.status = nextStatus;
      }
      const updated = await apiRequest<RegistrationInquiryRead>(
        `/organizations/${selectedOrganizationId}/registration-inquiries/${inquiry.id}`,
        { method: "PATCH", identity: requestIdentity, body }
      );
      replaceInquiry(updated);
      addLog(`${updated.athlete_name} moved to ${updated.status}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Review could not be saved");
    } finally {
      setBusy("");
    }
  };

  const sendFollowUp = async (inquiry: RegistrationInquiryRead) => {
    if (!selectedOrganizationId) {
      setError("Choose an organization before sending follow-up.");
      return;
    }
    const form = reviewForms[inquiry.id];
    const subject = `Registration follow-up for ${inquiry.athlete_name}`;
    const resumeLink = selectedOrganization ? registrationResumeHref(selectedOrganization, inquiry) : "";
    const missingDocuments = inquiry.missing_documents.length
      ? `Missing documents: ${inquiry.missing_documents.join(", ")}.`
      : null;
    const body = [
      `Hello ${inquiry.guardian_name || inquiry.athlete_name},`,
      "",
      `Thank you for your interest in ${selectedOrganization?.public_name || selectedOrganization?.name || "our program"}.`,
      inquiry.verification_status === "ready_for_review"
        ? "Your packet is ready for staff verification."
        : "We still need a few details before staff can verify the packet.",
      missingDocuments,
      inquiry.next_steps.length ? `Next step: ${inquiry.next_steps[0]}` : null,
      inquiry.payment_status ? `Payment status: ${inquiry.payment_status}.` : null,
      resumeLink ? `Continue your registration packet: ${resumeLink}` : null,
      form?.review_notes ? `Staff note: ${form.review_notes}` : null,
      "",
      "Please reply with any questions or missing information."
    ].filter(Boolean).join("\n");
    setBusy(`follow-up-${inquiry.id}`);
    setError("");
    try {
      const result = await apiRequest<RegistrationInquiryFollowUpRead>(
        `/organizations/${selectedOrganizationId}/registration-inquiries/${inquiry.id}/follow-up`,
        {
          method: "POST",
          identity: requestIdentity,
          body: {
            channel: "email",
            subject,
            body,
            urgent: false,
            quiet_hours_override: false
          }
        }
      );
      replaceInquiry(result.inquiry);
      addLog(`Follow-up queued for ${result.inquiry.athlete_name}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Follow-up could not be queued");
    } finally {
      setBusy("");
    }
  };

  const queueAiReview = async (inquiry: RegistrationInquiryRead) => {
    if (!selectedOrganizationId) {
      setError("Choose an organization before queueing AI review.");
      return;
    }
    setBusy(`ai-review-${inquiry.id}`);
    setError("");
    try {
      const task = await apiRequest<AgentTaskRead>(
        `/organizations/${selectedOrganizationId}/registration-inquiries/${inquiry.id}/agent-review`,
        { method: "POST", identity: requestIdentity }
      );
      setAgentTasks((current) => [task, ...current.filter((item) => item.id !== task.id)]);
      addLog(`AI review queued for ${inquiry.athlete_name}: ${task.status.replaceAll("_", " ")}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AI review could not be queued");
    } finally {
      setBusy("");
    }
  };

  const runAiReview = async (task: AgentTaskRead, inquiry: RegistrationInquiryRead) => {
    setBusy(`run-ai-${inquiry.id}`);
    setError("");
    try {
      const executed = await apiRequest<AgentTaskRead>(
        `/agents/tasks/${task.id}/execute`,
        { method: "POST", identity: requestIdentity }
      );
      setAgentTasks((current) => current.map((item) => (item.id === executed.id ? executed : item)));
      addLog(`AI review ready for ${inquiry.athlete_name}: ${executed.status.replaceAll("_", " ")}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AI review could not be run");
    } finally {
      setBusy("");
    }
  };

  const applyAiReviewNotes = (task: AgentTaskRead, inquiry: RegistrationInquiryRead) => {
    const note = aiReviewNote(task);
    if (!note) {
      setError("Run the AI review before applying notes.");
      return;
    }
    setReviewForms((current) => {
      const existing = current[inquiry.id] ?? {
        status: inquiry.status,
        review_notes: inquiry.review_notes ?? "",
        follow_up_at: toDateTimeLocalValue(inquiry.follow_up_at),
        payment_status: inquiry.payment_status,
        payment_method: inquiry.payment_method ?? "",
        payment_reference: inquiry.payment_reference ?? ""
      };
      return {
        ...current,
        [inquiry.id]: {
          ...existing,
          review_notes: appendUniqueNote(existing.review_notes, note)
        }
      };
    });
    addLog(`AI notes staged for ${inquiry.athlete_name}`);
  };

  const closeAiReview = async (task: AgentTaskRead, inquiry: RegistrationInquiryRead) => {
    setBusy(`close-ai-${inquiry.id}`);
    setError("");
    try {
      const updated = await apiRequest<AgentTaskRead>(
        `/agents/tasks/${task.id}`,
        {
          method: "PATCH",
          identity: requestIdentity,
          body: {
            status: "completed",
            review_notes: task.review_notes || "Admissions staff reviewed the AI admissions recommendation.",
            output_ref: task.output_ref
          }
        }
      );
      setAgentTasks((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      addLog(`AI review completed for ${inquiry.athlete_name}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AI review could not be completed");
    } finally {
      setBusy("");
    }
  };

  const convertInquiry = async (inquiry: RegistrationInquiryRead) => {
    if (!selectedOrganizationId) {
      setError("Choose an organization before converting admissions.");
      return;
    }
    setBusy(`convert-${inquiry.id}`);
    setError("");
    try {
      const conversion = await apiRequest<RegistrationInquiryConversionRead>(
        `/organizations/${selectedOrganizationId}/registration-inquiries/${inquiry.id}/convert`,
        {
          method: "POST",
          identity: requestIdentity,
          body: {
            team_id: inquiry.team_id,
            role: "player",
            create_guardian: true,
            send_guardian_invite: true,
            guardian_invite_channel: "email",
            guardian_portal_url: `${window.location.origin}/family`
          }
        }
      );
      replaceInquiry(conversion.inquiry);
      addLog(`${conversion.inquiry.athlete_name} converted to athlete profile`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Inquiry could not be converted");
    } finally {
      setBusy("");
    }
  };

  const replaceInquiry = (updated: RegistrationInquiryRead) => {
    setInquiries((current) => current.map((inquiry) => (inquiry.id === updated.id ? updated : inquiry)));
    setReviewForms((current) => ({
      ...current,
      [updated.id]: {
        status: updated.status,
        review_notes: updated.review_notes ?? "",
        follow_up_at: toDateTimeLocalValue(updated.follow_up_at),
        payment_status: updated.payment_status,
        payment_method: updated.payment_method ?? "",
        payment_reference: updated.payment_reference ?? ""
      }
    }));
  };

  const addLog = (message: string) => {
    setLog((current) => [message, ...current].slice(0, 5));
  };

  return (
    <main className="admissions-page">
      <section className="admissions-hero">
        <div className="admissions-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Admissions</span>
          </div>
        </div>
        <div>
          <p className="section-label">Registration review</p>
          <h1>Move families from inquiry to verified athlete records.</h1>
        </div>
        <div className="admissions-auth">
          <span>{keycloakEnabled ? "Keycloak" : "Local demo identity"}</span>
          <strong>{keycloakEnabled && !authSession ? "No browser session" : signedInLabel}</strong>
          {keycloakEnabled ? <small>{keycloakClientId} at {keycloakIssuer}</small> : <small>Used for local API headers.</small>}
          {keycloakEnabled ? (
            authSession ? (
              <button type="button" onClick={signOut}>Sign out</button>
            ) : (
              <div className="admissions-auth-actions">
                <button type="button" onClick={beginKeycloakRegistration}>Create account</button>
                <button type="button" onClick={beginKeycloakLogin}>Sign in</button>
              </div>
            )
          ) : null}
        </div>
      </section>

      {error ? <p className="form-error admissions-error">{error}</p> : null}

      <section className="admissions-toolbar">
        {!keycloakEnabled ? (
          <>
            <label>
              Staff name
              <input value={identity.name} onChange={(event) => setIdentity({ ...identity, name: event.target.value })} />
            </label>
            <label>
              Staff email
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
          </>
        ) : null}
        <label>
          Organization
          <select value={selectedOrganizationId} onChange={(event) => setSelectedOrganizationId(event.target.value)}>
            <option value="">Choose organization</option>
            {organizations.map((organization) => (
              <option key={organization.id} value={organization.id}>
                {organization.public_name ?? organization.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Search
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Athlete, guardian, email, sport" />
        </label>
        <button type="button" onClick={() => selectedOrganizationId && loadInquiries(selectedOrganizationId)} disabled={!selectedOrganizationId || busy !== ""}>
          {busy === "inquiries" ? "Refreshing" : "Refresh"}
        </button>
      </section>

      <section className="admissions-metrics">
        <Metric label="Total" value={metrics.total} />
        <Metric label="Ready" value={metrics.ready} />
        <Metric label="Paid" value={metrics.paid} />
        <Metric label="Needs action" value={metrics.needsAction} />
        <Metric label="Converted" value={metrics.converted} />
      </section>

      <section className="admissions-layout">
        <aside className="admissions-queue">
          <p className="section-label">Queue</p>
          {Object.entries(queueLabels).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={queue === value ? "selected" : ""}
              onClick={() => setQueue(value as AdmissionQueue)}
            >
              {label}
            </button>
          ))}
          <div className="admissions-log">
            <strong>Activity</strong>
            {log.length ? log.map((item) => <span key={item}>{item}</span>) : <span>No admissions actions yet.</span>}
          </div>
        </aside>

        <section className="admissions-list">
          {filteredInquiries.map((inquiry) => {
            const aiTask = agentTaskForInquiry(agentTasks, inquiry);
            const form = reviewForms[inquiry.id] ?? {
              status: inquiry.status,
              review_notes: inquiry.review_notes ?? "",
              follow_up_at: toDateTimeLocalValue(inquiry.follow_up_at),
              payment_status: inquiry.payment_status,
              payment_method: inquiry.payment_method ?? "",
              payment_reference: inquiry.payment_reference ?? ""
            };
            return (
              <article className="admission-card" key={inquiry.id}>
                <div className="admission-card-head">
                  <div>
                    <strong>{inquiry.athlete_name}</strong>
                    <span>{inquiry.guardian_name ?? "No guardian name"} · {inquiry.email}</span>
                  </div>
                  <StatusPill status={inquiry.verification_status} />
                </div>

                <div className="admission-facts">
                  <span>{inquiry.age_group ?? "age open"}</span>
                  <span>{inquiry.sport_interest ?? "sport open"}</span>
                  <span>{inquiry.status}</span>
                  <span>payment {inquiry.payment_status}</span>
                  <span>{inquiry.packet_complete ? "packet complete" : "packet incomplete"}</span>
                  <span>{inquiry.packet_submitted_at ? `packet ${new Date(inquiry.packet_submitted_at).toLocaleDateString()}` : "packet not submitted"}</span>
                  <span>{inquiry.guardian_contact_status.replaceAll("_", " ")}</span>
                  {aiTask ? (
                    <span className="admission-ai-fact">
                      AI {aiTask.status.replaceAll("_", " ")}
                      {aiTask.approval_pending_count > 0 ? ` · ${aiTask.approval_pending_count} approvals` : ""}
                    </span>
                  ) : (
                    <span className="admission-ai-fact muted">AI not queued</span>
                  )}
                </div>
                {aiTask ? (
                  <div className="admission-ai-panel">
                    <div>
                      <strong>{aiTask.title}</strong>
                      {canRunAiTask(aiTask) ? (
                        <button type="button" onClick={() => runAiReview(aiTask, inquiry)} disabled={busy !== ""}>
                          {busy === `run-ai-${inquiry.id}` ? "Running AI" : "Run AI"}
                        </button>
                      ) : null}
                    </div>
                    <span>
                      {aiTask.governance_policy_code
                        ? `${aiTask.governance_policy_code} · ${aiTask.governance_policy_decision ?? "governed"}`
                        : "Governance check passed without a matching policy."}
                    </span>
                    {aiTask.governance_policy_rationale ? <small>{aiTask.governance_policy_rationale}</small> : null}
                    {aiTask.review_notes ? <small>{aiTask.review_notes}</small> : null}
                    {aiTask.output_ref ? <small>{aiTask.output_ref}</small> : null}
                    {aiTask.review_notes || canCloseAiTask(aiTask) ? (
                      <div className="admission-ai-actions">
                        {aiTask.review_notes ? (
                          <button type="button" onClick={() => applyAiReviewNotes(aiTask, inquiry)} disabled={busy !== ""}>
                            Use notes
                          </button>
                        ) : null}
                        {canCloseAiTask(aiTask) ? (
                          <button type="button" onClick={() => closeAiReview(aiTask, inquiry)} disabled={busy !== ""}>
                            {busy === `close-ai-${inquiry.id}` ? "Closing AI" : "Complete AI"}
                          </button>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {inquiry.missing_documents.length > 0 || inquiry.next_steps.length > 0 ? (
                  <div className="admission-facts">
                    {inquiry.missing_documents.length > 0 ? (
                      <span>missing {inquiry.missing_documents.join(", ")}</span>
                    ) : null}
                    {inquiry.next_steps.slice(0, 2).map((step) => (
                      <span key={step}>{step}</span>
                    ))}
                  </div>
                ) : null}

                <div className="admission-review-grid">
                  <label>
                    Review
                    <select
                      value={form.status}
                      onChange={(event) => updateReviewForm(inquiry, "status", event.target.value)}
                      disabled={inquiry.status === "converted"}
                    >
                      <option value="new">New</option>
                      <option value="reviewing">Reviewing</option>
                      <option value="contacted">Contacted</option>
                      <option value="waitlisted">Waitlisted</option>
                      <option value="rejected">Rejected</option>
                      {inquiry.status === "converted" ? <option value="converted">Converted</option> : null}
                    </select>
                  </label>
                  <label>
                    Follow-up
                    <input
                      type="datetime-local"
                      value={form.follow_up_at}
                      onChange={(event) => updateReviewForm(inquiry, "follow_up_at", event.target.value)}
                    />
                  </label>
                  <label>
                    Payment
                    <select
                      value={form.payment_status}
                      onChange={(event) => updateReviewForm(inquiry, "payment_status", event.target.value)}
                      disabled={inquiry.status === "converted"}
                    >
                      <option value="pending">Pending</option>
                      <option value="pending_verification">Pending verification</option>
                      <option value="paid">Paid</option>
                      <option value="waived">Waived</option>
                      <option value="not_required">Not required</option>
                      <option value="failed">Failed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </label>
                  <label>
                    Method
                    <input
                      value={form.payment_method}
                      onChange={(event) => updateReviewForm(inquiry, "payment_method", event.target.value)}
                      placeholder="M-Pesa, card, waiver"
                      disabled={inquiry.status === "converted"}
                    />
                  </label>
                  <label>
                    Reference
                    <input
                      value={form.payment_reference}
                      onChange={(event) => updateReviewForm(inquiry, "payment_reference", event.target.value)}
                      placeholder="Receipt or waiver code"
                      disabled={inquiry.status === "converted"}
                    />
                  </label>
                  <label className="admission-wide">
                    Notes
                    <textarea
                      value={form.review_notes}
                      onChange={(event) => updateReviewForm(inquiry, "review_notes", event.target.value)}
                      placeholder="Eligibility, missing documents, coach review, payment verification"
                    />
                  </label>
                </div>

                <div className="admission-actions">
                  {selectedOrganization ? (
                    <>
                      <a href={registrationResumeHref(selectedOrganization, inquiry)} target="_blank" rel="noreferrer">
                        Open packet
                      </a>
                      <a href={familyPortalHref(inquiry)} target="_blank" rel="noreferrer">
                        Family portal
                      </a>
                    </>
                  ) : null}
                  <button type="button" onClick={() => saveReview(inquiry)} disabled={busy !== "" || inquiry.status === "converted"}>
                    {busy === `review-${inquiry.id}` ? "Saving" : "Save"}
                  </button>
                  <button type="button" onClick={() => saveReview(inquiry, "waitlisted")} disabled={busy !== "" || inquiry.status === "converted"}>
                    Waitlist
                  </button>
                  <button type="button" onClick={() => sendFollowUp(inquiry)} disabled={busy !== "" || inquiry.status === "converted"}>
                    Follow up
                  </button>
                  <button
                    type="button"
                    onClick={() => queueAiReview(inquiry)}
                    disabled={busy !== "" || inquiry.status === "converted" || aiTask !== null}
                  >
                    {aiTask ? "AI queued" : busy === `ai-review-${inquiry.id}` ? "Queueing AI" : "AI review"}
                  </button>
                  <button
                    type="button"
                    className="primary"
                    onClick={() => convertInquiry(inquiry)}
                    disabled={busy !== "" || inquiry.status === "converted" || !inquiry.packet_complete}
                    title={!inquiry.packet_complete ? "Complete documents, consent, emergency details, medical details, and payment before conversion." : undefined}
                  >
                    {busy === `convert-${inquiry.id}` ? "Converting" : inquiry.packet_complete ? "Convert" : "Packet incomplete"}
                  </button>
                </div>
              </article>
            );
          })}
          {filteredInquiries.length === 0 ? (
            <div className="admissions-empty">
              <strong>No admissions in this queue</strong>
              <span>Choose another queue, refresh the organization, or publish the public registration page.</span>
            </div>
          ) : null}
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.replaceAll("_", " ");
  return <span className={`admission-status ${status}`}>{normalized}</span>;
}

function registrationResumeHref(organization: OrganizationRead, inquiry: RegistrationInquiryRead): string {
  const params = new URLSearchParams({
    inquiry_id: inquiry.id,
    email: inquiry.email
  });
  return `${window.location.origin}/site/${organization.subdomain || organization.slug}?${params.toString()}`;
}

function familyPortalHref(inquiry: RegistrationInquiryRead): string {
  const params = new URLSearchParams({
    organization_id: inquiry.organization_id,
    inquiry_id: inquiry.id,
    guardian_email: inquiry.email,
    guardian_name: inquiry.guardian_name ?? inquiry.email,
    athlete_name: inquiry.athlete_name,
    autoload: "1"
  });
  return `${window.location.origin}/family?${params.toString()}`;
}

function agentTaskForInquiry(tasks: AgentTaskRead[], inquiry: RegistrationInquiryRead): AgentTaskRead | null {
  const marker = `registration-inquiry:${inquiry.id};`;
  return tasks.find((task) => task.input_ref?.includes(marker)) ?? null;
}

function canRunAiTask(task: AgentTaskRead): boolean {
  return task.status === "queued" || task.status === "failed";
}

function canCloseAiTask(task: AgentTaskRead): boolean {
  return task.status === "waiting_for_review" && task.approval_pending_count === 0;
}

function aiReviewNote(task: AgentTaskRead): string {
  if (!task.review_notes && !task.output_ref) {
    return "";
  }
  return [
    task.review_notes ? `AI review: ${task.review_notes}` : null,
    task.output_ref ? `AI output: ${task.output_ref}` : null
  ].filter(Boolean).join("\n");
}

function appendUniqueNote(existing: string, note: string): string {
  const trimmedExisting = existing.trim();
  const trimmedNote = note.trim();
  if (!trimmedExisting) {
    return trimmedNote;
  }
  if (trimmedExisting.includes(trimmedNote)) {
    return trimmedExisting;
  }
  return `${trimmedExisting}\n\n${trimmedNote}`;
}

function toDateTimeLocalValue(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}
