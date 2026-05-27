"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type {
  ActivityConsentRead,
  AttendanceStatus,
  CommunicationInboxItemRead,
  ConsentStatus,
  FamilyAthleteSummaryRead,
  FamilyConsentRequestRead,
  FamilyEventSummaryRead,
  LocalIdentity,
  MessageRecipientRead
} from "@/types/operations";

const defaultFamilyIdentity: LocalIdentity = {
  sub: "kc-parent-1",
  email: "parent@example.com",
  name: "Parent Example"
};

export default function FamilyPortalPage() {
  const [organizationId, setOrganizationId] = useState("");
  const [identity, setIdentity] = useState<LocalIdentity>(defaultFamilyIdentity);
  const [family, setFamily] = useState<FamilyAthleteSummaryRead[]>([]);
  const [events, setEvents] = useState<FamilyEventSummaryRead[]>([]);
  const [consentRequests, setConsentRequests] = useState<FamilyConsentRequestRead[]>([]);
  const [items, setItems] = useState<CommunicationInboxItemRead[]>([]);
  const [selectedRecipientId, setSelectedRecipientId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("afrolete.familyPortal");
    if (!stored) {
      return;
    }
    try {
      const parsed = JSON.parse(stored) as { organizationId?: string; identity?: LocalIdentity };
      setOrganizationId(parsed.organizationId ?? "");
      setIdentity(parsed.identity ?? defaultFamilyIdentity);
    } catch {
      window.localStorage.removeItem("afrolete.familyPortal");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("afrolete.familyPortal", JSON.stringify({ organizationId, identity }));
  }, [identity, organizationId]);

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
    setBusy(true);
    setError("");
    try {
      const organizationQuery = encodeURIComponent(organizationId);
      const [familyRows, eventRows, pendingRequests, inbox] = await Promise.all([
        apiRequest<FamilyAthleteSummaryRead[]>(`/safeguarding/my-family?organization_id=${organizationQuery}`, {
          identity
        }),
        apiRequest<FamilyEventSummaryRead[]>(`/safeguarding/my-family/events?organization_id=${organizationQuery}`, {
          identity
        }),
        apiRequest<FamilyConsentRequestRead[]>(
          `/safeguarding/my-family/consent-requests?organization_id=${organizationQuery}`,
          { identity }
        ),
        apiRequest<CommunicationInboxItemRead[]>(`/communications/my-inbox?organization_id=${organizationQuery}`, {
          identity
        })
      ]);
      setFamily(familyRows);
      setEvents(eventRows);
      setConsentRequests(pendingRequests);
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

  const markRead = async (recipientId: string) => {
    setBusy(true);
    setError("");
    try {
      const recipient = await apiRequest<MessageRecipientRead>(`/communications/inbox/${recipientId}/read`, {
        method: "POST",
        identity
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
          identity,
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
          identity,
          body: {
            status,
            notes: `Family portal response: ${status}`
          }
        }
      );
      const eventRows = await apiRequest<FamilyEventSummaryRead[]>(
        `/safeguarding/my-family/events?organization_id=${encodeURIComponent(organizationId)}`,
        { identity }
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
          <button type="submit" disabled={busy}>{busy ? "Loading" : "Load"}</button>
        </form>

        {error ? <p className="form-error">{error}</p> : null}

        <div className="family-metrics">
          <div>
            <span>Unread</span>
            <strong>{unreadCount}</strong>
          </div>
          <div>
            <span>Total</span>
            <strong>{items.length}</strong>
          </div>
          <div>
            <span>Children</span>
            <strong>{family.length}</strong>
          </div>
          <div>
            <span>Consent</span>
            <strong>{pendingConsentCount}</strong>
          </div>
        </div>

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
