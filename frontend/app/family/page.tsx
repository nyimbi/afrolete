"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
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
  ActivityConsentRead,
  AgentDecisionAppealFormRead,
  AgentDecisionAppealRead,
  AgentFamilyTaskRead,
  AttendanceStatus,
  CommunicationInboxItemRead,
  ConsentStatus,
  FamilyAthleteSummaryRead,
  FamilyConsentRequestRead,
  FamilyDashboardRead,
  FamilyEventSummaryRead,
  FamilyRegistrationInquiryRead,
  FamilyPerformanceSummaryRead,
  LocalIdentity,
  MessageRecipientRead
} from "@/types/operations";

const defaultFamilyIdentity: LocalIdentity = {
  sub: "kc-parent-1",
  email: "parent@example.com",
  name: "Parent Example"
};

const keycloakEnabled = afroleteAuthMode === "keycloak";

function registrationStatusLabel(status: string): string {
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

function registrationResumeHref(registration: FamilyRegistrationInquiryRead): string {
  const params = new URLSearchParams({
    inquiry_id: registration.id,
    email: registration.email
  });
  return `${registration.public_site_path}?${params.toString()}`;
}

export default function FamilyPortalPage() {
  const [organizationId, setOrganizationId] = useState("");
  const [identity, setIdentity] = useState<LocalIdentity>(defaultFamilyIdentity);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [inviteRelationshipId, setInviteRelationshipId] = useState("");
  const [loadedInviteKey, setLoadedInviteKey] = useState("");
  const [family, setFamily] = useState<FamilyAthleteSummaryRead[]>([]);
  const [registrations, setRegistrations] = useState<FamilyRegistrationInquiryRead[]>([]);
  const [dashboard, setDashboard] = useState<FamilyDashboardRead | null>(null);
  const [performance, setPerformance] = useState<FamilyPerformanceSummaryRead[]>([]);
  const [events, setEvents] = useState<FamilyEventSummaryRead[]>([]);
  const [consentRequests, setConsentRequests] = useState<FamilyConsentRequestRead[]>([]);
  const [aiAppeals, setAiAppeals] = useState<AgentDecisionAppealRead[]>([]);
  const [aiTasks, setAiTasks] = useState<AgentFamilyTaskRead[]>([]);
  const [items, setItems] = useState<CommunicationInboxItemRead[]>([]);
  const [appealForm, setAppealForm] = useState({
    task_id: "",
    question: "Please explain and review this AI recommendation for my family."
  });
  const [selectedRecipientId, setSelectedRecipientId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let nextOrganizationId = "";
    let nextIdentity = defaultFamilyIdentity;
    let nextInviteRelationshipId = "";
    const stored = window.localStorage.getItem("afrolete.familyPortal");
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as {
          organizationId?: string;
          identity?: LocalIdentity;
          relationshipId?: string;
        };
        nextOrganizationId = parsed.organizationId ?? "";
        nextIdentity = parsed.identity ?? defaultFamilyIdentity;
        nextInviteRelationshipId = parsed.relationshipId ?? "";
      } catch {
        window.localStorage.removeItem("afrolete.familyPortal");
      }
    }

    const params = new URLSearchParams(window.location.search);
    const organizationParam = params.get("organization_id") ?? params.get("organizationId");
    const relationshipParam = params.get("relationship_id") ?? "";
    const emailParam = params.get("guardian_email") ?? params.get("email");
    const nameParam = params.get("guardian_name") ?? params.get("name") ?? emailParam;
    const subParam = params.get("guardian_sub") ?? params.get("sub");

    if (organizationParam) {
      nextOrganizationId = organizationParam;
    }
    if (relationshipParam) {
      nextInviteRelationshipId = relationshipParam;
    }
    if (emailParam || nameParam || subParam) {
      nextIdentity = {
        sub: subParam ?? (emailParam ? `guardian-${emailParam}` : nextIdentity.sub),
        email: emailParam ?? nextIdentity.email,
        name: nameParam ?? nextIdentity.name
      };
    }

    setOrganizationId(nextOrganizationId);
    setIdentity(nextIdentity);
    setInviteRelationshipId(nextInviteRelationshipId);
    if (keycloakEnabled) {
      completeKeycloakCallbackFromUrl()
        .then((session) => setAuthSession(session ?? getStoredAuthSession()))
        .catch((caught) => {
          setAuthSession(null);
          setError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
        });
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      "afrolete.familyPortal",
      JSON.stringify({ organizationId, identity, relationshipId: inviteRelationshipId })
    );
  }, [identity, inviteRelationshipId, organizationId]);

  const requestIdentity = useMemo(() => (keycloakEnabled ? undefined : identity), [identity]);
  const signedInLabel = authSession?.email ?? authSession?.name ?? identity.email;
  const inviteEmailMismatch =
    keycloakEnabled &&
    authSession?.email !== undefined &&
    identity.email !== "" &&
    authSession.email.toLowerCase() !== identity.email.toLowerCase();

  const beginKeycloakLogin = () => {
    setBusy(true);
    setError("");
    void startKeycloakLogin({ loginHint: identity.email || undefined, prompt: "login" }).catch((caught) => {
      setBusy(false);
      setError(caught instanceof Error ? caught.message : "Keycloak sign-in failed");
    });
  };

  const beginKeycloakRegistration = () => {
    setBusy(true);
    setError("");
    void startKeycloakRegistration({ loginHint: identity.email || undefined }).catch((caught) => {
      setBusy(false);
      setError(caught instanceof Error ? caught.message : "Keycloak account creation failed");
    });
  };

  const signOut = () => {
    clearStoredAuthSession();
    setAuthSession(null);
  };

  const selectedItem = useMemo(
    () => items.find((item) => item.recipient_id === selectedRecipientId) ?? items[0] ?? null,
    [items, selectedRecipientId]
  );

  const unreadCount = items.filter((item) => item.delivery_status !== "read").length;
  const pendingConsentCount = consentRequests.length;

  const loadWorkspace = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!organizationId) {
      setError("Organization id is required");
      return;
    }
    if (keycloakEnabled && authSession === null) {
      setError("Sign in with Keycloak to open the family portal.");
      return;
    }
    if (inviteEmailMismatch) {
      setError("The signed-in Keycloak email does not match this guardian invitation.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const organizationQuery = encodeURIComponent(organizationId);
      const [
        dashboardSummary,
        familyRows,
        registrationRows,
        performanceRows,
        eventRows,
        pendingRequests,
        appeals,
        aiTaskRows,
        inbox
      ] = await Promise.all([
        apiRequest<FamilyDashboardRead>(`/safeguarding/my-family/dashboard?organization_id=${organizationQuery}`, {
          identity: requestIdentity
        }),
        apiRequest<FamilyAthleteSummaryRead[]>(`/safeguarding/my-family?organization_id=${organizationQuery}`, {
          identity: requestIdentity
        }),
        apiRequest<FamilyRegistrationInquiryRead[]>(
          `/organizations/my-registration-inquiries?organization_id=${organizationQuery}`,
          {
            identity: requestIdentity
          }
        ),
        apiRequest<FamilyPerformanceSummaryRead[]>(
          `/safeguarding/my-family/performance?organization_id=${organizationQuery}`,
          { identity: requestIdentity }
        ),
        apiRequest<FamilyEventSummaryRead[]>(`/safeguarding/my-family/events?organization_id=${organizationQuery}`, {
          identity: requestIdentity
        }),
        apiRequest<FamilyConsentRequestRead[]>(
          `/safeguarding/my-family/consent-requests?organization_id=${organizationQuery}`,
          { identity: requestIdentity }
        ),
        apiRequest<AgentDecisionAppealRead[]>(`/agents/my-appeals?organization_id=${organizationQuery}`, {
          identity: requestIdentity
        }),
        apiRequest<AgentFamilyTaskRead[]>(`/agents/my-family-tasks?organization_id=${organizationQuery}`, {
          identity: requestIdentity
        }),
        apiRequest<CommunicationInboxItemRead[]>(`/communications/my-inbox?organization_id=${organizationQuery}`, {
          identity: requestIdentity
        })
      ]);
      setDashboard(dashboardSummary);
      setFamily(familyRows);
      setRegistrations(registrationRows);
      setPerformance(performanceRows);
      setEvents(eventRows);
      setConsentRequests(pendingRequests);
      setAiTasks(aiTaskRows);
      setAiAppeals(appeals);
      setItems(inbox);
      setSelectedRecipientId((current) =>
        inbox.some((item) => item.recipient_id === current) ? current : inbox[0]?.recipient_id ?? ""
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Inbox load failed");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!inviteRelationshipId || !organizationId || loadedInviteKey === inviteRelationshipId) {
      return;
    }
    if (keycloakEnabled && authSession === null) {
      return;
    }
    if (inviteEmailMismatch) {
      return;
    }
    setLoadedInviteKey(inviteRelationshipId);
    void loadWorkspace();
  }, [authSession, identity, inviteEmailMismatch, inviteRelationshipId, loadedInviteKey, organizationId, requestIdentity]);

  const markRead = async (recipientId: string) => {
    setBusy(true);
    setError("");
    try {
      const recipient = await apiRequest<MessageRecipientRead>(`/communications/inbox/${recipientId}/read`, {
        method: "POST",
        identity: requestIdentity
      });
      setItems((current) =>
        current.map((item) =>
          item.recipient_id === recipient.id
            ? {
                ...item,
                delivery_status: recipient.delivery_status,
                delivered_at: recipient.delivered_at,
                read_at: recipient.read_at,
                failure_reason: recipient.failure_reason
              }
            : item
        )
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Read update failed");
    } finally {
      setBusy(false);
    }
  };

  const respondToEvent = async (event: FamilyEventSummaryRead, status: AttendanceStatus) => {
    setBusy(true);
    setError("");
    try {
      const updated = await apiRequest<FamilyEventSummaryRead>(
        `/safeguarding/my-family/events/${event.event_id}/athletes/${event.athlete_person_id}/rsvp`,
        {
          method: "POST",
          identity: requestIdentity,
          body: {
            organization_id: organizationId,
            status
          }
        }
      );
      setEvents((current) =>
        current.map((item) =>
          item.event_id === updated.event_id && item.athlete_person_id === updated.athlete_person_id
            ? updated
            : item
        )
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "RSVP update failed");
    } finally {
      setBusy(false);
    }
  };

  const respondToConsent = async (request: FamilyConsentRequestRead, status: ConsentStatus) => {
    setBusy(true);
    setError("");
    try {
      const consent = await apiRequest<ActivityConsentRead>(
        `/safeguarding/my-family/consent-requests/${request.id}/response`,
        {
          method: "POST",
          identity: requestIdentity,
          body: {
            status,
            notes: `Family portal response: ${status}`
          }
        }
      );
      const eventRows = await apiRequest<FamilyEventSummaryRead[]>(
        `/safeguarding/my-family/events?organization_id=${encodeURIComponent(organizationId)}`,
        { identity: requestIdentity }
      );
      setConsentRequests((current) => current.filter((item) => item.id !== request.id));
      setEvents(eventRows);
      setFamily((current) =>
        current.map((athlete) =>
          athlete.athlete_person_id === consent.athlete_person_id
            ? {
                ...athlete,
                pending_consent_requests: Math.max(athlete.pending_consent_requests - 1, 0),
                latest_consent_status: consent.status,
                latest_consent_scope_type: consent.scope_type,
                latest_consent_signed_at: consent.signed_at
              }
            : athlete
        )
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Consent response failed");
    } finally {
      setBusy(false);
    }
  };

  const submitAiAppeal = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!organizationId || !appealForm.task_id) {
      setError("Organization and agent task id are required");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const appeal = await apiRequest<AgentDecisionAppealRead>("/agents/my-appeals", {
        method: "POST",
        identity: requestIdentity,
        body: {
          organization_id: organizationId,
          task_id: appealForm.task_id,
          reason: "family_review",
          question: appealForm.question,
          supporting_evidence_ref: `family-portal:${signedInLabel}`
        }
      });
      setAiAppeals((current) => [appeal, ...current.filter((item) => item.id !== appeal.id)]);
      setAppealForm({
        task_id: "",
        question: "Please explain and review this AI recommendation for my family."
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AI appeal could not be submitted");
    } finally {
      setBusy(false);
    }
  };

  const base64ToBlob = (value: string, contentType: string) => {
    const binary = window.atob(value);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return new Blob([bytes], { type: contentType });
  };

  const downloadAiAppealForm = async (taskId: string, artifactFormat: "markdown" | "pdf" = "markdown") => {
    if (!organizationId) {
      setError("Organization id is required");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const form = await apiRequest<AgentDecisionAppealFormRead>(
        `/agents/my-family-tasks/${taskId}/appeal-form?organization_id=${encodeURIComponent(organizationId)}&artifact_format=${artifactFormat}`,
        { identity: requestIdentity }
      );
      const blob =
        form.content_base64 !== null
          ? base64ToBlob(form.content_base64, form.content_type)
          : new Blob([form.content], { type: form.content_type });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = form.download_filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AI appeal form could not be downloaded");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="consent-page family-page">
      <section className="consent-shell family-shell">
        <div className="consent-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Family portal</span>
          </div>
        </div>

        <form className="family-toolbar" onSubmit={loadWorkspace}>
          <label>
            Organization
            <input value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} />
          </label>
          {keycloakEnabled ? (
            <div className="family-auth-summary">
              <span>Keycloak</span>
              <strong>{authSession ? signedInLabel : "No browser session"}</strong>
              <small>{keycloakClientId} at {keycloakIssuer}</small>
              {identity.email ? <small>Invitation email: {identity.email}</small> : null}
              {inviteEmailMismatch ? <small className="form-error">Signed in with a different email.</small> : null}
            </div>
          ) : (
            <>
              <label>
                Name
                <input value={identity.name} onChange={(event) => setIdentity({ ...identity, name: event.target.value })} />
              </label>
              <label>
                Email
                <input
                  value={identity.email}
                  onChange={(event) => setIdentity({ ...identity, email: event.target.value })}
                />
              </label>
              <label>
                Account
                <input value={identity.sub} onChange={(event) => setIdentity({ ...identity, sub: event.target.value })} />
              </label>
            </>
          )}
          {keycloakEnabled ? (
            authSession ? (
              <button type="button" onClick={signOut} disabled={busy}>Sign out</button>
            ) : (
              <div className="family-auth-actions">
                <button type="button" onClick={beginKeycloakRegistration} disabled={busy}>
                  Create account
                </button>
                <button type="button" onClick={beginKeycloakLogin} disabled={busy}>
                  Sign in
                </button>
              </div>
            )
          ) : null}
          <button type="submit" disabled={busy}>{busy ? "Loading" : "Load"}</button>
        </form>

        {error ? <p className="form-error">{error}</p> : null}

        <div className="family-metrics">
          <div>
            <span>Unread</span>
            <strong>{dashboard?.unread_message_count ?? unreadCount}</strong>
          </div>
          <div>
            <span>Urgent</span>
            <strong>{dashboard?.urgent_unread_count ?? items.filter((item) => item.urgent && item.delivery_status !== "read").length}</strong>
          </div>
          <div>
            <span>Children</span>
            <strong>{dashboard?.child_count ?? family.length}</strong>
          </div>
          <div>
            <span>Registration</span>
            <strong>{registrations.filter((item) => item.status !== "converted").length}</strong>
          </div>
          <div>
            <span>Consent</span>
            <strong>{dashboard?.pending_consent_count ?? pendingConsentCount}</strong>
          </div>
          <div>
            <span>RSVPs</span>
            <strong>{dashboard?.rsvp_needed_count ?? events.filter((event) => event.attendance_status === null).length}</strong>
          </div>
          <div>
            <span>Clearance</span>
            <strong>{dashboard?.clearance_blocked_count ?? events.filter((event) => event.clearance_status !== "cleared").length}</strong>
          </div>
          <div>
            <span>Conflicts</span>
            <strong>{dashboard?.schedule_conflict_count ?? 0}</strong>
          </div>
          <div>
            <span>AI</span>
            <strong>{dashboard?.ai_recommendation_count ?? aiTasks.length}</strong>
          </div>
        </div>

        {dashboard ? (
          <section className="family-ai-appeals">
            <div>
              <p className="section-label">Family command</p>
              <h2>{dashboard.next_action_label}</h2>
              <p>
                {dashboard.upcoming_event_count} upcoming events · {dashboard.active_goal_count} goals · {dashboard.award_count} awards
                {dashboard.next_event_at ? ` · next ${formatDate(dashboard.next_event_at)}` : ""}
              </p>
            </div>
            <div className="family-appeal-list">
              {dashboard.schedule_conflicts.map((conflict) => (
                <article key={`${conflict.event_ids.join("-")}-${conflict.starts_at}`}>
                  <strong>Schedule conflict</strong>
                  <span>{conflict.athlete_names.join(" and ")} · {formatDate(conflict.starts_at)}</span>
                  <small>{conflict.recommendation}</small>
                  <small>{conflict.event_titles.join(" · ")}</small>
                </article>
              ))}
              {dashboard.action_items.map((item) => (
                <article key={`${item.action_type}-${item.title}-${item.due_at ?? "now"}`}>
                  <strong>{item.title}</strong>
                  <span>{item.priority} · {item.action_type.replaceAll("_", " ")}</span>
                  <small>{item.detail}</small>
                  <small>{item.due_at ? formatDate(item.due_at) : "Open action"}</small>
                </article>
              ))}
              {dashboard.action_items.length === 0 ? <span>No urgent family actions</span> : null}
            </div>
          </section>
        ) : null}

        {registrations.length > 0 ? (
          <section className="family-ai-appeals">
            <div>
              <p className="section-label">Registration</p>
              <h2>Pending player onboarding</h2>
              <p>Track inquiries, packet readiness, missing documents, and account handoff before staff conversion.</p>
            </div>
            <div className="family-appeal-list">
              {registrations.map((registration) => (
                <article key={registration.id}>
                  <strong>{registration.athlete_name}</strong>
                  <span>
                    {registration.organization_public_name ?? registration.organization_name} ·{" "}
                    {registration.status.replaceAll("_", " ")} · {registration.verification_status.replaceAll("_", " ")}
                  </span>
                  <small>
                    {registration.packet_complete ? "Packet complete" : "Packet incomplete"} · payment{" "}
                    {registration.payment_status.replaceAll("_", " ")} · {registrationStatusLabel(registration.account_status)}
                  </small>
                  <small>
                    {registration.missing_documents.length > 0
                      ? `Missing: ${registration.missing_documents.join(", ")}`
                      : registration.next_steps[0] ?? "Awaiting staff review"}
                  </small>
                  <a href={registrationResumeHref(registration)}>Continue packet</a>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <div className="family-athletes">
          {family.map((athlete) => (
            <article key={athlete.athlete_person_id}>
              <strong>{athlete.athlete_name}</strong>
              <span>{athlete.relationship} · {athlete.can_sign_consent ? "signer" : "viewer"}</span>
              <small>
                {athlete.pending_consent_requests} pending · {athlete.latest_consent_status ?? "no consent"}
              </small>
            </article>
          ))}
        </div>

        <div className="family-consents">
          {consentRequests.map((request) => (
            <article key={request.id}>
              <div>
                <strong>{request.athlete_name}</strong>
                <span>{request.scope_type} consent · {request.channel}</span>
                {request.expires_at ? <small>Expires {formatDate(request.expires_at)}</small> : null}
              </div>
              <span>
                <button type="button" onClick={() => respondToConsent(request, "granted")} disabled={busy}>
                  Grant
                </button>
                <button type="button" onClick={() => respondToConsent(request, "denied")} disabled={busy}>
                  Deny
                </button>
              </span>
            </article>
          ))}
        </div>

        <div className="family-events">
          {events.slice(0, 6).map((event) => (
            <article key={`${event.athlete_person_id}-${event.event_id}`}>
              <div>
                <strong>{event.title}</strong>
                <span>{event.athlete_name} · {event.event_type} · {formatDate(event.starts_at)}</span>
              </div>
              <div className="family-event-status">
                <small>{event.attendance_status ?? "not invited"} · {event.clearance_status}</small>
                <span>
                  <button type="button" onClick={() => respondToEvent(event, "confirmed")} disabled={busy}>
                    Confirm
                  </button>
                  <button type="button" onClick={() => respondToEvent(event, "declined")} disabled={busy}>
                    Decline
                  </button>
                </span>
              </div>
            </article>
          ))}
        </div>

        <section className="family-ai-appeals">
          <div>
            <p className="section-label">Performance</p>
            <h2>Goals and achievements</h2>
            <p>Track active targets, earned badges, and personal bests for linked athletes.</p>
          </div>
          <div className="family-appeal-list">
            {performance.flatMap((athlete) =>
              athlete.awards.slice(0, 2).map((award) => (
                <article key={award.id}>
                  <strong>{award.title}</strong>
                  <span>{athlete.athlete_name} · {award.achievement_type.replaceAll("_", " ")}</span>
                  <small>{award.source_summary ?? `Badge ${award.badge_code}`}</small>
                  <small>Awarded {formatDate(award.awarded_at)}</small>
                </article>
              ))
            )}
            {performance.every((athlete) => athlete.awards.length === 0) ? (
              <span>No awards yet</span>
            ) : null}
          </div>
          <div className="family-appeal-list">
            {performance.flatMap((athlete) =>
              athlete.goals.slice(0, 2).map((goal) => (
                <article key={goal.id}>
                  <strong>{goal.title} · {goal.status}</strong>
                  <span>
                    {athlete.athlete_name} · current {goal.current_value ?? "—"} / target {goal.target_value}
                  </span>
                  <small>{goal.reward_badge ?? "Performance goal"} · {goal.due_at ? `Due ${formatDate(goal.due_at)}` : "No due date"}</small>
                </article>
              ))
            )}
            {performance.every((athlete) => athlete.goals.length === 0) ? (
              <span>No active performance goals yet</span>
            ) : null}
          </div>
        </section>

        <section className="family-ai-appeals">
          <div>
            <p className="section-label">AI appeals</p>
            <h2>Question an AI recommendation</h2>
            <p>Request a human explanation, data review, or outcome change for an agent task affecting your family.</p>
          </div>
          <form onSubmit={submitAiAppeal}>
            <label>
              Agent task
              <select
                value={appealForm.task_id}
                onChange={(event) => setAppealForm({ ...appealForm, task_id: event.target.value })}
              >
                <option value="">Select an AI recommendation</option>
                {aiTasks.map((task) => (
                  <option value={task.id} key={task.id}>
                    {task.title} · {task.athlete_name ?? task.agent_name} · {task.status}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Question
              <textarea
                value={appealForm.question}
                onChange={(event) => setAppealForm({ ...appealForm, question: event.target.value })}
              />
            </label>
            <button type="submit" disabled={busy}>Submit appeal</button>
          </form>
          <div className="family-appeal-list">
            {aiTasks.slice(0, 4).map((task) => (
              <article key={task.id}>
                <strong>{task.title} · {task.status}</strong>
                <span>{task.athlete_name ?? "Linked family"} · {task.agent_name} · {task.task_type}</span>
                <small>{task.simple_explanation}</small>
                <small>{task.data_summary}</small>
                <small>{task.governance_note}</small>
                <small>{task.appeal_status ? `Appeal ${task.appeal_status}` : "No appeal opened"}</small>
                <button type="button" onClick={() => downloadAiAppealForm(task.id, "markdown")} disabled={busy}>
                  Markdown form
                </button>
                <button type="button" onClick={() => downloadAiAppealForm(task.id, "pdf")} disabled={busy}>
                  PDF form
                </button>
              </article>
            ))}
            {aiTasks.length === 0 ? <span>No linked AI recommendations yet</span> : null}
          </div>
          <div className="family-appeal-list">
            {aiAppeals.slice(0, 4).map((appeal) => (
              <article key={appeal.id}>
                <strong>{appeal.model_policy} · {appeal.status}</strong>
                <span>{appeal.simple_explanation}</span>
                <small>Due {formatDate(appeal.due_at)} · {appeal.resolution_notes ?? appeal.alternative_options}</small>
              </article>
            ))}
            {aiAppeals.length === 0 ? <span>No AI appeals yet</span> : null}
          </div>
        </section>

        <div className="family-layout">
          <div className="family-list" aria-label="Inbox messages">
            {items.map((item) => (
              <button
                type="button"
                key={item.recipient_id}
                className={item.recipient_id === selectedItem?.recipient_id ? "selected" : ""}
                onClick={() => setSelectedRecipientId(item.recipient_id)}
              >
                <strong>{item.subject}</strong>
                <span>{item.channel} · {item.delivery_status}{item.urgent ? " · urgent" : ""}</span>
              </button>
            ))}
            {items.length === 0 ? <div className="family-empty">No messages</div> : null}
          </div>

          <article className="family-message">
            {selectedItem ? (
              <>
                <div className="panel-head">
                  <div>
                    <p className="section-label">{selectedItem.message_type}</p>
                    <h1>{selectedItem.subject}</h1>
                  </div>
                  <button
                    type="button"
                    onClick={() => markRead(selectedItem.recipient_id)}
                    disabled={busy || selectedItem.delivery_status === "read"}
                  >
                    Read
                  </button>
                </div>
                <p>{selectedItem.body}</p>
                <dl>
                  <div>
                    <dt>Sent</dt>
                    <dd>{formatDate(selectedItem.sent_at)}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{selectedItem.delivery_status}</dd>
                  </div>
                  <div>
                    <dt>Channel</dt>
                    <dd>{selectedItem.channel}</dd>
                  </div>
                </dl>
              </>
            ) : (
              <h1>Family inbox</h1>
            )}
          </article>
        </div>
      </section>
    </main>
  );
}

function formatDate(value: string | null): string {
  if (!value) {
    return "Pending";
  }
  return new Date(value).toLocaleString();
}
