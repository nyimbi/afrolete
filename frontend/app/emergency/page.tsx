"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type {
  CommunicationChannel,
  EmergencyActivationAlertRead,
  EmergencyActivationStatus,
  EmergencyActionPlanRead,
  EmergencyPlanActivationRead,
  EmergencyType,
  LocalIdentity,
  OrganizationPublicSiteRead,
  SafeguardingIncidentRead
} from "@/types/operations";

const defaultEmergencyIdentity: LocalIdentity = {
  sub: "kc-owner-1",
  email: "owner@example.com",
  name: "Owner Example"
};

const defaultStarterPlan = {
  title: "Mobile matchday emergency action plan",
  emergency_type: "medical" as EmergencyType,
  emergency_contacts: "Safety lead, medical lead, venue security, emergency services.",
  medical_protocols: "Stabilize, clear the area, assign first-aid lead, document actions, escalate if symptoms worsen.",
  communication_protocols: "Notify staff, guardians, venue operations, and leadership from the emergency channel.",
  incident_command_roles: "Incident lead, medical responder, crowd control, family liaison, documentation lead.",
  escalation_matrix: "Level 1 staff response; Level 2 guardians and venue operations; Level 3 emergency services.",
  external_agency_contacts: "Emergency services; venue security; nearest clinic or hospital.",
  equipment_locations: "First aid kit, AED, ice, stretcher, evacuation route map.",
  assembly_points: "Primary: main gate. Secondary: parking zone B.",
  special_needs_plan: "Check athlete medical notes, accessibility needs, and guardian instructions.",
  notes: "Created from the mobile emergency console."
};

export default function EmergencyConsolePage() {
  const [organizationInput, setOrganizationInput] = useState("demo-city-fc");
  const [organizationId, setOrganizationId] = useState("");
  const [siteName, setSiteName] = useState("");
  const [identity, setIdentity] = useState<LocalIdentity>(defaultEmergencyIdentity);
  const [plans, setPlans] = useState<EmergencyActionPlanRead[]>([]);
  const [activations, setActivations] = useState<EmergencyPlanActivationRead[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [locationDetail, setLocationDetail] = useState("Main field touchline");
  const [responders, setResponders] = useState("Coach, medic, safety officer");
  const [alertChannel, setAlertChannel] = useState<CommunicationChannel>("push");
  const [alertBody, setAlertBody] = useState("Emergency response is active. Follow staff instructions and keep access routes clear.");
  const [lastAlert, setLastAlert] = useState<EmergencyActivationAlertRead | null>(null);
  const [lastIncident, setLastIncident] = useState<SafeguardingIncidentRead | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const activeActivations = activations.filter((activation) => activation.status === "active");
  const selectedPlan = useMemo(
    () => plans.find((plan) => plan.id === selectedPlanId) ?? plans[0] ?? null,
    [plans, selectedPlanId]
  );
  const latestActivation = activeActivations[0] ?? activations[0] ?? null;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const input = params.get("organization_id") ?? params.get("org") ?? params.get("slug") ?? params.get("site");
    const email = params.get("email");
    const name = params.get("name");
    const sub = params.get("sub");
    if (input) {
      setOrganizationInput(input);
      void loadWorkspace(input);
    }
    if (email || name || sub) {
      setIdentity({
        sub: sub ?? (email ? `operator-${email}` : defaultEmergencyIdentity.sub),
        email: email ?? defaultEmergencyIdentity.email,
        name: name ?? email ?? defaultEmergencyIdentity.name
      });
    }
  }, []);

  const loadWorkspace = async (input = organizationInput) => {
    if (!input.trim()) {
      setError("Organization id or public slug is required");
      return;
    }
    await withBusy(async () => {
      const resolved = await resolveOrganization(input.trim());
      setOrganizationId(resolved.id);
      setSiteName(resolved.name);
      const [planRows, activationRows] = await Promise.all([
        apiRequest<EmergencyActionPlanRead[]>(`/assets/emergency-plans?organization_id=${resolved.id}`),
        apiRequest<EmergencyPlanActivationRead[]>(`/assets/emergency-activations?organization_id=${resolved.id}`)
      ]);
      setPlans(planRows);
      setActivations(activationRows);
      setSelectedPlanId((current) =>
        planRows.some((plan) => plan.id === current) ? current : planRows[0]?.id ?? ""
      );
      setNotice(`${resolved.name} emergency workspace loaded`);
    }, "Emergency workspace load failed");
  };

  const resolveOrganization = async (input: string) => {
    if (looksLikeUuid(input)) {
      return { id: input, name: "Organization" };
    }
    const site = await apiRequest<OrganizationPublicSiteRead>(`/organizations/public/${encodeURIComponent(input)}`);
    return { id: site.id, name: site.public_name ?? site.name };
  };

  const createStarterPlan = async () => {
    if (!organizationId) {
      setError("Load an organization first");
      return;
    }
    await withBusy(async () => {
      const plan = await apiRequest<EmergencyActionPlanRead>("/assets/emergency-plans", {
        method: "POST",
        identity,
        body: {
          organization_id: organizationId,
          ...defaultStarterPlan
        }
      });
      setPlans((current) => [plan, ...current.filter((item) => item.id !== plan.id)]);
      setSelectedPlanId(plan.id);
      setNotice(`${plan.title} is ready`);
    }, "Starter emergency plan could not be created");
  };

  const activatePlan = async () => {
    if (!selectedPlan || !organizationId) {
      setError("Select or create an emergency plan first");
      return;
    }
    await withBusy(async () => {
      const activation = await apiRequest<EmergencyPlanActivationRead>("/assets/emergency-activations", {
        method: "POST",
        identity,
        body: {
          organization_id: organizationId,
          plan_id: selectedPlan.id,
          facility_id: selectedPlan.facility_id,
          emergency_type: selectedPlan.emergency_type,
          location_detail: locationDetail,
          escalation_level: 1,
          assigned_responders: responders || null,
          guidance_steps: selectedPlan.medical_protocols ?? selectedPlan.weather_protocols ?? selectedPlan.evacuation_routes,
          communication_log: selectedPlan.communication_protocols,
          notes: "Activated from the mobile emergency console."
        }
      });
      setActivations((current) => [activation, ...current.filter((item) => item.id !== activation.id)]);
      setNotice(`${activation.emergency_type} emergency active at ${activation.location_detail}`);
    }, "Emergency activation failed");
  };

  const updateActivation = async (
    activation: EmergencyPlanActivationRead,
    statusValue: EmergencyActivationStatus | null,
    escalationLevel = activation.escalation_level
  ) => {
    await withBusy(async () => {
      const resolved = statusValue === "resolved";
      const updated = await apiRequest<EmergencyPlanActivationRead>(`/assets/emergency-activations/${activation.id}`, {
        method: "PATCH",
        identity,
        body: {
          status: statusValue,
          escalation_level: escalationLevel,
          closed_at: resolved ? new Date().toISOString() : null,
          response_time_seconds: resolved ? responseTimeSeconds(activation.activated_at) : null,
          outcome_summary: resolved ? "Emergency response resolved from the mobile console." : activation.outcome_summary,
          notes: resolved ? "Resolved by mobile operator." : "Updated by mobile operator."
        }
      });
      setActivations((current) => [updated, ...current.filter((item) => item.id !== updated.id)]);
      setNotice(`${updated.emergency_type} emergency is ${updated.status} at level ${updated.escalation_level}`);
    }, "Emergency update failed");
  };

  const dispatchAlert = async (activation: EmergencyPlanActivationRead) => {
    await withBusy(async () => {
      const alert = await apiRequest<EmergencyActivationAlertRead>(`/assets/emergency-activations/${activation.id}/alerts`, {
        method: "POST",
        identity,
        body: {
          channel: alertChannel,
          scope_type: "organization",
          scope_id: organizationId || activation.organization_id,
          body: alertBody || null,
          copy_guardians_for_minors: true
        }
      });
      setLastAlert(alert);
      setNotice(`${alert.channel} emergency alert sent to ${alert.recipient_count} recipients`);
    }, "Emergency alert failed");
  };

  const logIncident = async (activation: EmergencyPlanActivationRead) => {
    await withBusy(async () => {
      const incident = await apiRequest<SafeguardingIncidentRead>(
        `/assets/emergency-activations/${activation.id}/incident`,
        {
          method: "POST",
          identity,
          body: {
            severity: activation.escalation_level >= 4 ? "critical" : activation.escalation_level >= 2 ? "high" : "medium",
            title: `${titleCase(activation.emergency_type)} emergency response`,
            medical_follow_up_required: activation.emergency_type === "medical" ? "yes" : "unknown",
            regulatory_report_required: activation.escalation_level >= 4
          }
        }
      );
      setLastIncident(incident);
      setActivations((current) =>
        current.map((item) => (item.id === activation.id ? { ...item, incident_id: incident.id } : item))
      );
      setNotice(`Incident ${incident.title} created`);
    }, "Incident log failed");
  };

  const withBusy = async (operation: () => Promise<void>, failureMessage: string) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : failureMessage);
    } finally {
      setBusy(false);
    }
  };

  const submitLoad = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void loadWorkspace();
  };

  return (
    <main className="emergency-page">
      <section className="emergency-shell">
        <header className="emergency-header">
          <div>
            <p className="section-label">Emergency</p>
            <h1>Mobile response console</h1>
            <p>{siteName || "Load an organization to activate and coordinate an emergency action plan."}</p>
          </div>
          <strong>{activeActivations.length}</strong>
        </header>

        <form className="emergency-load" onSubmit={submitLoad}>
          <label>
            Organization id or public slug
            <input value={organizationInput} onChange={(event) => setOrganizationInput(event.target.value)} />
          </label>
          <label>
            Operator email
            <input value={identity.email} onChange={(event) => setIdentity({ ...identity, email: event.target.value })} />
          </label>
          <button type="submit" disabled={busy}>Load</button>
        </form>

        {error ? <p className="form-error">{error}</p> : null}
        {notice ? <p className="form-success">{notice}</p> : null}

        <section className="emergency-status-grid">
          <article>
            <span>Active</span>
            <strong>{activeActivations.length}</strong>
          </article>
          <article>
            <span>Plans</span>
            <strong>{plans.length}</strong>
          </article>
          <article>
            <span>Level</span>
            <strong>{latestActivation?.escalation_level ?? 0}</strong>
          </article>
        </section>

        <section className="emergency-command">
          <label>
            Emergency action plan
            <select value={selectedPlan?.id ?? ""} onChange={(event) => setSelectedPlanId(event.target.value)}>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.title}
                </option>
              ))}
              {plans.length === 0 ? <option value="">No plan loaded</option> : null}
            </select>
          </label>
          <label>
            Location
            <input value={locationDetail} onChange={(event) => setLocationDetail(event.target.value)} />
          </label>
          <label>
            Responders
            <input value={responders} onChange={(event) => setResponders(event.target.value)} />
          </label>
          <label>
            Alert channel
            <select value={alertChannel} onChange={(event) => setAlertChannel(event.target.value as CommunicationChannel)}>
              <option value="push">Push</option>
              <option value="in_app">In app</option>
              <option value="sms">SMS</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="telegram">Telegram</option>
              <option value="email">Email</option>
            </select>
          </label>
          <label className="wide-field">
            Alert body
            <textarea value={alertBody} onChange={(event) => setAlertBody(event.target.value)} />
          </label>
          <div className="emergency-actions">
            <button type="button" onClick={createStarterPlan} disabled={busy || !organizationId}>Starter EAP</button>
            <button type="button" className="danger" onClick={activatePlan} disabled={busy || !selectedPlan}>Activate</button>
          </div>
        </section>

        {selectedPlan ? (
          <section className="emergency-guidance">
            <article>
              <span>Contacts</span>
              <strong>{selectedPlan.emergency_contacts}</strong>
            </article>
            <article>
              <span>Command</span>
              <strong>{selectedPlan.incident_command_roles ?? "Assign response roles before activation."}</strong>
            </article>
            <article>
              <span>Escalation</span>
              <strong>{selectedPlan.escalation_matrix ?? "Use organization emergency escalation policy."}</strong>
            </article>
            <article>
              <span>Equipment</span>
              <strong>{selectedPlan.equipment_locations ?? "Attach equipment locations to this EAP."}</strong>
            </article>
          </section>
        ) : null}

        <section className="emergency-activations">
          {activations.map((activation) => (
            <article key={activation.id} className={activation.status === "active" ? "active" : ""}>
              <div>
                <strong>{titleCase(activation.emergency_type)} emergency</strong>
                <span>{activation.status} · level {activation.escalation_level} · {formatDate(activation.activated_at)}</span>
                <small>{activation.location_detail}</small>
                <small>{activation.outcome_summary ?? activation.guidance_steps ?? "Response in progress"}</small>
              </div>
              <div className="emergency-action-row">
                <button type="button" onClick={() => dispatchAlert(activation)} disabled={busy}>Alert</button>
                <button type="button" onClick={() => updateActivation(activation, null, Math.min(5, activation.escalation_level + 1))} disabled={busy}>Escalate</button>
                <button type="button" onClick={() => logIncident(activation)} disabled={busy}>{activation.incident_id ? "Incident" : "Log"}</button>
                <button type="button" onClick={() => updateActivation(activation, "resolved")} disabled={busy}>Resolve</button>
              </div>
            </article>
          ))}
          {activations.length === 0 ? <span className="emergency-empty">No emergency activations yet.</span> : null}
        </section>

        {lastAlert || lastIncident ? (
          <section className="emergency-receipts">
            {lastAlert ? (
              <article>
                <span>Last alert</span>
                <strong>{lastAlert.subject}</strong>
                <small>{lastAlert.channel} · {lastAlert.recipient_count} recipients</small>
              </article>
            ) : null}
            {lastIncident ? (
              <article>
                <span>Last incident</span>
                <strong>{lastIncident.title}</strong>
                <small>{lastIncident.status} · {lastIncident.severity}</small>
              </article>
            ) : null}
          </section>
        ) : null}
      </section>
    </main>
  );
}

function looksLikeUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

function responseTimeSeconds(activatedAt: string): number {
  return Math.max(0, Math.round((Date.now() - new Date(activatedAt).getTime()) / 1000));
}

function titleCase(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}
