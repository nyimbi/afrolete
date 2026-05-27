"use client";

import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import { apiBaseUrl } from "@/lib/config";
import type {
  AgentAssignmentRead,
  AgentKind,
  AgentRead,
  AgentTaskRead,
  AgentTaskStatus,
  AttendanceRecordRead,
  AttendanceSeedRead,
  AttendanceStatus,
  ConsentRequestRead,
  EventRead,
  EventType,
  GuardianRelationshipRead,
  LocalIdentity,
  MembershipRead,
  OrganizationRead,
  OrganizationType,
  ParticipationClearanceRead,
  SportFormat,
  TeamRead,
  TeamRole
} from "@/types/operations";

const defaultIdentity: LocalIdentity = {
  sub: "kc-owner-1",
  email: "owner@example.com",
  name: "Owner Example"
};

type LogEntry = {
  id: string;
  tone: "good" | "bad" | "neutral";
  message: string;
};

type AthleteEntry = {
  personId: string;
  name: string;
  email: string;
  rosterEntryId?: string;
};

export default function HomePage() {
  const [identity, setIdentity] = useState<LocalIdentity>(defaultIdentity);
  const [organizations, setOrganizations] = useState<OrganizationRead[]>([]);
  const [teams, setTeams] = useState<TeamRead[]>([]);
  const [events, setEvents] = useState<EventRead[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecordRead[]>([]);
  const [agents, setAgents] = useState<AgentRead[]>([]);
  const [agentTasks, setAgentTasks] = useState<AgentTaskRead[]>([]);
  const [athletes, setAthletes] = useState<AthleteEntry[]>([]);
  const [guardians, setGuardians] = useState<GuardianRelationshipRead[]>([]);
  const [consentRequest, setConsentRequest] = useState<ConsentRequestRead | null>(null);
  const [clearance, setClearance] = useState<ParticipationClearanceRead | null>(null);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState("");
  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [selectedEventId, setSelectedEventId] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [selectedAthleteId, setSelectedAthleteId] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const [organizationForm, setOrganizationForm] = useState({
    name: "Nairobi Rising FC",
    organization_type: "club" as OrganizationType,
    country_code: "KE",
    primary_sport: "football",
    public_name: "Nairobi Rising",
    subdomain: "nairobi-rising",
    brand_primary_color: "#0f766e",
    brand_secondary_color: "#f59e0b",
    contact_email: "hello@rising.example"
  });
  const [teamForm, setTeamForm] = useState({
    name: "U16 Rising",
    sport: "football",
    sport_format: "team" as SportFormat,
    age_group: "U16",
    gender_category: "open",
    season_label: "2026"
  });
  const [athleteForm, setAthleteForm] = useState({
    display_name: "Amani Otieno",
    email: "amani@example.com",
    role: "player" as TeamRole,
    primary_position: "Midfielder",
    jersey_number: "8",
    is_captain: false
  });
  const [eventForm, setEventForm] = useState({
    title: "U16 League Match",
    event_type: "match" as EventType,
    starts_at: "2026-05-28T09:00",
    duration_minutes: 90,
    timezone: "Africa/Nairobi",
    venue_name: "City Stadium",
    notes: "Matchday operations and consent clearance."
  });
  const [guardianForm, setGuardianForm] = useState({
    guardian_display_name: "Parent Example",
    guardian_email: "parent@example.com",
    guardian_phone: "+254700000000"
  });
  const [agentForm, setAgentForm] = useState({
    name: "Safeguarding Watch",
    kind: "safeguarding" as AgentKind,
    purpose: "Monitor consent gaps, unsafe participation, and review tasks before messages go out.",
    model_policy: "human_review_required"
  });
  const [taskForm, setTaskForm] = useState({
    task_type: "consent_gap_review",
    title: "Review missing consent before matchday",
    input_ref: "event-clearance"
  });

  const selectedOrganization = useMemo(
    () => organizations.find((organization) => organization.id === selectedOrganizationId) ?? null,
    [organizations, selectedOrganizationId]
  );
  const selectedTeam = useMemo(
    () => teams.find((team) => team.id === selectedTeamId) ?? null,
    [teams, selectedTeamId]
  );
  const selectedEvent = useMemo(
    () => events.find((event) => event.id === selectedEventId) ?? null,
    [events, selectedEventId]
  );
  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) ?? null,
    [agents, selectedAgentId]
  );
  const selectedAthlete = useMemo(
    () => athletes.find((athlete) => athlete.personId === selectedAthleteId) ?? null,
    [athletes, selectedAthleteId]
  );

  const addLog = useCallback((message: string, tone: LogEntry["tone"] = "neutral") => {
    setLogs((current) => [
      { id: crypto.randomUUID(), message, tone },
      ...current.slice(0, 7)
    ]);
  }, []);

  const runAction = useCallback(
    async <T,>(label: string, action: () => Promise<T>, success: (value: T) => void) => {
      setBusyAction(label);
      try {
        const value = await action();
        success(value);
      } catch (error) {
        addLog(error instanceof Error ? error.message : "Request failed", "bad");
      } finally {
        setBusyAction(null);
      }
    },
    [addLog]
  );

  const loadOrganizations = useCallback(async () => {
    const data = await apiRequest<OrganizationRead[]>("/organizations", { identity });
    setOrganizations(data);
    if (!selectedOrganizationId && data[0]) {
      setSelectedOrganizationId(data[0].id);
    }
  }, [identity, selectedOrganizationId]);

  const loadTeams = useCallback(
    async (organizationId: string) => {
      const data = await apiRequest<TeamRead[]>(`/teams/by-organization/${organizationId}`);
      setTeams(data);
      setSelectedTeamId((current) => (data.some((team) => team.id === current) ? current : data[0]?.id ?? ""));
    },
    []
  );

  const loadEvents = useCallback(async (organizationId: string, teamId?: string) => {
    const query = teamId ? `&team_id=${teamId}` : "";
    const data = await apiRequest<EventRead[]>(`/events?organization_id=${organizationId}${query}`);
    setEvents(data);
    setSelectedEventId((current) => (data.some((event) => event.id === current) ? current : data[0]?.id ?? ""));
  }, []);

  const loadAttendance = useCallback(async (eventId: string) => {
    const data = await apiRequest<AttendanceRecordRead[]>(`/events/${eventId}/attendance`);
    setAttendance(data);
  }, []);

  const loadAgents = useCallback(async (organizationId: string) => {
    const data = await apiRequest<AgentRead[]>(`/agents?organization_id=${organizationId}`);
    setAgents(data);
    setSelectedAgentId((current) =>
      data.some((agent) => agent.id === current) ? current : data[0]?.id ?? ""
    );
  }, []);

  const loadAgentTasks = useCallback(async (organizationId: string, agentId?: string) => {
    const query = agentId ? `&agent_id=${agentId}` : "";
    const data = await apiRequest<AgentTaskRead[]>(
      `/agents/tasks?organization_id=${organizationId}${query}`
    );
    setAgentTasks(data);
  }, []);

  useEffect(() => {
    const stored = window.localStorage.getItem("afrolete.localIdentity");
    if (stored) {
      setIdentity(JSON.parse(stored) as LocalIdentity);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("afrolete.localIdentity", JSON.stringify(identity));
  }, [identity]);

  useEffect(() => {
    runAction("load-organizations", loadOrganizations, () => addLog("Workspace synchronized", "good"));
  }, [loadOrganizations, runAction, addLog]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      setTeams([]);
      setEvents([]);
      return;
    }
    runAction("load-tenant-data", async () => {
      await loadTeams(selectedOrganizationId);
      await loadEvents(selectedOrganizationId);
      await loadAgents(selectedOrganizationId);
      await loadAgentTasks(selectedOrganizationId);
    }, () => addLog("Organization workspace loaded", "good"));
  }, [selectedOrganizationId, loadTeams, loadEvents, loadAgents, loadAgentTasks, runAction, addLog]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      return;
    }
    runAction(
      "load-team-events",
      () => loadEvents(selectedOrganizationId, selectedTeamId || undefined),
      () => addLog("Event lane refreshed", "good")
    );
  }, [selectedTeamId, selectedOrganizationId, loadEvents, runAction, addLog]);

  useEffect(() => {
    if (!selectedEventId) {
      setAttendance([]);
      return;
    }
    runAction("load-attendance", () => loadAttendance(selectedEventId), () => undefined);
  }, [selectedEventId, loadAttendance, runAction]);

  useEffect(() => {
    if (!selectedOrganizationId) {
      setAgentTasks([]);
      return;
    }
    runAction(
      "load-agent-tasks",
      () => loadAgentTasks(selectedOrganizationId, selectedAgentId || undefined),
      () => undefined
    );
  }, [selectedAgentId, selectedOrganizationId, loadAgentTasks, runAction]);

  const createOrganization = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    runAction(
      "create-organization",
      () =>
        apiRequest<OrganizationRead>("/organizations", {
          method: "POST",
          identity,
          body: {
            ...organizationForm,
            mission: "Build an accountable athlete development pathway."
          }
        }),
      (organization) => {
        setOrganizations((current) => [organization, ...current.filter((item) => item.id !== organization.id)]);
        setSelectedOrganizationId(organization.id);
        addLog(`${organization.name} is ready`, "good");
      }
    );
  };

  const createTeam = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId) {
      addLog("Create or select an organization first", "bad");
      return;
    }
    runAction(
      "create-team",
      () =>
        apiRequest<TeamRead>("/teams", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...teamForm
          }
        }),
      (team) => {
        setTeams((current) => [team, ...current.filter((item) => item.id !== team.id)]);
        setSelectedTeamId(team.id);
        addLog(`${team.name} roster lane opened`, "good");
      }
    );
  };

  const addAthlete = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId || !selectedTeamId) {
      addLog("Select an organization and team first", "bad");
      return;
    }

    runAction(
      "add-athlete",
      async () => {
        const member = await apiRequest<MembershipRead>(`/organizations/${selectedOrganizationId}/members`, {
          method: "POST",
          identity,
          body: {
            email: athleteForm.email,
            display_name: athleteForm.display_name,
            role: "athlete",
            title: athleteForm.primary_position
          }
        });
        const roster = await apiRequest<{ id: string }>(`/teams/${selectedTeamId}/members`, {
          method: "POST",
          identity,
          body: {
            person_id: member.subject_id,
            role: athleteForm.role,
            status: athleteForm.role === "substitute" ? "substitute" : "active",
            primary_position: athleteForm.primary_position,
            jersey_number: athleteForm.jersey_number,
            is_captain: athleteForm.is_captain
          }
        });
        return { member, roster };
      },
      ({ member, roster }) => {
        const athlete = {
          personId: member.subject_id,
          name: athleteForm.display_name,
          email: athleteForm.email,
          rosterEntryId: roster.id
        };
        setAthletes((current) => [athlete, ...current.filter((item) => item.personId !== athlete.personId)]);
        setSelectedAthleteId(athlete.personId);
        addLog(`${athlete.name} joined ${selectedTeam?.name ?? "the team"}`, "good");
      }
    );
  };

  const createEvent = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    const startsAt = new Date(eventForm.starts_at);
    const endsAt = new Date(startsAt.getTime() + eventForm.duration_minutes * 60_000);

    runAction(
      "create-event",
      () =>
        apiRequest<EventRead>("/events", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            team_id: selectedTeamId || null,
            event_type: eventForm.event_type,
            title: eventForm.title,
            starts_at: startsAt.toISOString(),
            ends_at: endsAt.toISOString(),
            timezone: eventForm.timezone,
            venue_name: eventForm.venue_name,
            notes: eventForm.notes
          }
        }),
      (createdEvent) => {
        setEvents((current) => [createdEvent, ...current.filter((item) => item.id !== createdEvent.id)]);
        setSelectedEventId(createdEvent.id);
        addLog(`${createdEvent.title} scheduled`, "good");
      }
    );
  };

  const seedAttendance = () => {
    if (!selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      "seed-attendance",
      () =>
        apiRequest<AttendanceSeedRead>(`/events/${selectedEventId}/attendance/from-roster`, {
          method: "POST",
          identity
        }),
      (seed) => {
        addLog(`Attendance seeded: ${seed.created} created, ${seed.existing} existing`, "good");
        void loadAttendance(selectedEventId);
      }
    );
  };

  const recordAttendance = (personId: string, status: AttendanceStatus) => {
    if (!selectedEventId) {
      addLog("Select an event first", "bad");
      return;
    }
    runAction(
      `attendance-${personId}-${status}`,
      () =>
        apiRequest<AttendanceRecordRead>(`/events/${selectedEventId}/attendance`, {
          method: "POST",
          identity,
          body: {
            person_id: personId,
            status,
            note: `${status} from AfroLete console`
          }
        }),
      (record) => {
        setAttendance((current) => [record, ...current.filter((item) => item.person_id !== record.person_id)]);
        addLog(`Attendance recorded as ${record.status}`, "good");
      }
    );
  };

  const createGuardian = () => {
    if (!selectedOrganizationId || !selectedAthleteId) {
      addLog("Select an athlete first", "bad");
      return;
    }
    runAction(
      "create-guardian",
      () =>
        apiRequest<GuardianRelationshipRead>("/safeguarding/guardians", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_person_id: selectedAthleteId,
            guardian_email: guardianForm.guardian_email,
            guardian_phone: guardianForm.guardian_phone,
            guardian_display_name: guardianForm.guardian_display_name,
            relationship_kind: "parent",
            can_sign_consent: true,
            emergency_contact: true,
            is_primary: true
          }
        }),
      (guardian) => {
        setGuardians((current) => [guardian, ...current.filter((item) => item.id !== guardian.id)]);
        addLog(`${guardianForm.guardian_display_name} linked as guardian`, "good");
      }
    );
  };

  const requestConsent = () => {
    const guardian = guardians.find((item) => item.athlete_person_id === selectedAthleteId);
    if (!selectedOrganizationId || !selectedEventId || !selectedAthleteId || !guardian) {
      addLog("Select an athlete, event, and guardian first", "bad");
      return;
    }
    runAction(
      "request-consent",
      () =>
        apiRequest<ConsentRequestRead>("/safeguarding/consent-requests", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            athlete_person_id: selectedAthleteId,
            guardian_person_id: guardian.guardian_person_id,
            scope_type: "event",
            scope_id: selectedEventId,
            channel: "email",
            destination: guardianForm.guardian_email,
            notes: `Consent for ${selectedEvent?.title ?? "event"}`
          }
        }),
      (request) => {
        setConsentRequest(request);
        addLog("Consent request created", "good");
      }
    );
  };

  const checkClearance = () => {
    if (!selectedEventId || !selectedAthleteId) {
      addLog("Select an event and athlete first", "bad");
      return;
    }
    runAction(
      "check-clearance",
      () =>
        apiRequest<ParticipationClearanceRead>(
          `/safeguarding/events/${selectedEventId}/athletes/${selectedAthleteId}/clearance`
        ),
      (value) => {
        setClearance(value);
        addLog(`Clearance: ${value.status}`, value.status === "cleared" ? "good" : "neutral");
      }
    );
  };

  const createAgent = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId) {
      addLog("Select an organization first", "bad");
      return;
    }
    runAction(
      "create-agent",
      () =>
        apiRequest<AgentRead>("/agents", {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...agentForm
          }
        }),
      (agent) => {
        setAgents((current) => [agent, ...current.filter((item) => item.id !== agent.id)]);
        setSelectedAgentId(agent.id);
        addLog(`${agent.name} is active`, "good");
      }
    );
  };

  const assignAgent = (scopeType: "organization" | "team" | "event") => {
    if (!selectedOrganizationId || !selectedAgentId) {
      addLog("Select an organization and agent first", "bad");
      return;
    }
    const scopeId =
      scopeType === "organization"
        ? selectedOrganizationId
        : scopeType === "team"
          ? selectedTeamId
          : selectedEventId;
    if (!scopeId) {
      addLog(`Select a ${scopeType} first`, "bad");
      return;
    }
    runAction(
      `assign-agent-${scopeType}`,
      () =>
        apiRequest<AgentAssignmentRead>(`/agents/${selectedAgentId}/assignments`, {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            scope_type: scopeType,
            scope_id: scopeId
          }
        }),
      (assignment) => addLog(`Agent assigned to ${assignment.scope_type}`, "good")
    );
  };

  const queueAgentTask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrganizationId || !selectedAgentId) {
      addLog("Select an organization and agent first", "bad");
      return;
    }
    runAction(
      "queue-agent-task",
      () =>
        apiRequest<AgentTaskRead>(`/agents/${selectedAgentId}/tasks`, {
          method: "POST",
          identity,
          body: {
            organization_id: selectedOrganizationId,
            ...taskForm,
            input_ref: selectedEventId ? `event:${selectedEventId}` : taskForm.input_ref
          }
        }),
      (task) => {
        setAgentTasks((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        addLog(`${selectedAgent?.name ?? "Agent"} task queued`, "good");
      }
    );
  };

  const updateAgentTask = (taskId: string, status: AgentTaskStatus) => {
    runAction(
      `agent-task-${taskId}-${status}`,
      () =>
        apiRequest<AgentTaskRead>(`/agents/tasks/${taskId}`, {
          method: "PATCH",
          identity,
          body: {
            status,
            output_ref: status === "completed" ? `reviewed:${taskId}` : undefined,
            review_notes:
              status === "waiting_for_review"
                ? "Agent output needs human review before action."
                : `Marked ${status} from the command console.`
          }
        }),
      (task) => {
        setAgentTasks((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        addLog(`Task moved to ${task.status}`, "good");
      }
    );
  };

  const consentUrl = consentRequest?.one_time_token
    ? `${window.location.origin}/consent/${consentRequest.one_time_token}`
    : "";

  return (
    <main className="app-shell">
      <aside className="app-rail" aria-label="Primary">
        <div className="brand-lockup">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Operations</span>
          </div>
        </div>
        <nav>
          <a href="#command" className="active">Command</a>
          <a href="#tenant">Tenant</a>
          <a href="#roster">Roster</a>
          <a href="#events">Events</a>
          <a href="#agents">Agents</a>
          <a href="#safeguarding">Safeguarding</a>
        </nav>
        <div className="rail-status">
          <span>API</span>
          <strong>{apiBaseUrl.replace("http://", "")}</strong>
        </div>
      </aside>

      <section className="workspace" id="command">
        <header className="topbar">
          <div>
            <p className="eyebrow">Live command surface</p>
            <h1>{selectedOrganization?.public_name ?? selectedOrganization?.name ?? "Build an operating tenant"}</h1>
          </div>
          <div className="topbar-actions">
            <button type="button" onClick={() => void loadOrganizations()} disabled={busyAction !== null}>
              Sync
            </button>
          </div>
        </header>

        <section className="operator-grid" aria-label="Workspace summary">
          <form className="panel identity-panel" onSubmit={(event) => event.preventDefault()}>
            <p className="section-label">Operator</p>
            <label>
              Name
              <input value={identity.name} onChange={(event) => setIdentity({ ...identity, name: event.target.value })} />
            </label>
            <label>
              Email
              <input value={identity.email} onChange={(event) => setIdentity({ ...identity, email: event.target.value })} />
            </label>
            <label>
              Subject
              <input value={identity.sub} onChange={(event) => setIdentity({ ...identity, sub: event.target.value })} />
            </label>
          </form>

          <div className="panel status-panel">
            <p className="section-label">State</p>
            <div className="stat-row">
              <span>Organizations</span>
              <strong>{organizations.length}</strong>
            </div>
            <div className="stat-row">
              <span>Teams</span>
              <strong>{teams.length}</strong>
            </div>
            <div className="stat-row">
              <span>Events</span>
              <strong>{events.length}</strong>
            </div>
            <div className="stat-row">
              <span>Attendance</span>
              <strong>{attendance.length}</strong>
            </div>
            <div className="stat-row">
              <span>Agents</span>
              <strong>{agents.length}</strong>
            </div>
          </div>

          <div className="panel log-panel">
            <p className="section-label">Activity</p>
            <div className="activity-list">
              {logs.length === 0 ? <span className="muted">No activity yet</span> : null}
              {logs.map((log) => (
                <p key={log.id} className={`log-line ${log.tone}`}>{log.message}</p>
              ))}
            </div>
          </div>
        </section>

        <section className="work-grid">
          <form className="panel form-panel" id="tenant" onSubmit={createOrganization}>
            <div className="panel-head">
              <div>
                <p className="section-label">Tenant</p>
                <h2>Organization workspace</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Create</button>
            </div>
            <div className="form-grid">
              <label>
                Name
                <input value={organizationForm.name} onChange={(event) => setOrganizationForm({ ...organizationForm, name: event.target.value })} />
              </label>
              <label>
                Type
                <select value={organizationForm.organization_type} onChange={(event) => setOrganizationForm({ ...organizationForm, organization_type: event.target.value as OrganizationType })}>
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
              <label>
                Sport
                <input value={organizationForm.primary_sport} onChange={(event) => setOrganizationForm({ ...organizationForm, primary_sport: event.target.value })} />
              </label>
              <label>
                Contact
                <input value={organizationForm.contact_email} onChange={(event) => setOrganizationForm({ ...organizationForm, contact_email: event.target.value })} />
              </label>
            </div>
            <div className="selection-list">
              {organizations.map((organization) => (
                <button
                  type="button"
                  key={organization.id}
                  className={organization.id === selectedOrganizationId ? "selected" : ""}
                  onClick={() => setSelectedOrganizationId(organization.id)}
                >
                  <span>{organization.name}</span>
                  <small>{organization.organization_type} · {organization.my_roles.join(", ")}</small>
                </button>
              ))}
            </div>
          </form>

          <form className="panel form-panel" onSubmit={createTeam}>
            <div className="panel-head">
              <div>
                <p className="section-label">Team</p>
                <h2>Squad builder</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Create</button>
            </div>
            <div className="form-grid">
              <label>
                Name
                <input value={teamForm.name} onChange={(event) => setTeamForm({ ...teamForm, name: event.target.value })} />
              </label>
              <label>
                Format
                <select value={teamForm.sport_format} onChange={(event) => setTeamForm({ ...teamForm, sport_format: event.target.value as SportFormat })}>
                  <option value="team">Team sport</option>
                  <option value="individual">Individual sport</option>
                  <option value="mixed">Mixed program</option>
                </select>
              </label>
              <label>
                Sport
                <input value={teamForm.sport} onChange={(event) => setTeamForm({ ...teamForm, sport: event.target.value })} />
              </label>
              <label>
                Age
                <input value={teamForm.age_group} onChange={(event) => setTeamForm({ ...teamForm, age_group: event.target.value })} />
              </label>
              <label>
                Gender
                <input value={teamForm.gender_category} onChange={(event) => setTeamForm({ ...teamForm, gender_category: event.target.value })} />
              </label>
              <label>
                Season
                <input value={teamForm.season_label} onChange={(event) => setTeamForm({ ...teamForm, season_label: event.target.value })} />
              </label>
            </div>
            <div className="selection-list">
              {teams.map((team) => (
                <button
                  type="button"
                  key={team.id}
                  className={team.id === selectedTeamId ? "selected" : ""}
                  onClick={() => setSelectedTeamId(team.id)}
                >
                  <span>{team.name}</span>
                  <small>{team.sport} · {team.sport_format}</small>
                </button>
              ))}
            </div>
          </form>
        </section>

        <section className="work-grid">
          <form className="panel form-panel" id="roster" onSubmit={addAthlete}>
            <div className="panel-head">
              <div>
                <p className="section-label">Roster</p>
                <h2>Athlete intake</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Add</button>
            </div>
            <div className="form-grid">
              <label>
                Athlete
                <input value={athleteForm.display_name} onChange={(event) => setAthleteForm({ ...athleteForm, display_name: event.target.value })} />
              </label>
              <label>
                Email
                <input value={athleteForm.email} onChange={(event) => setAthleteForm({ ...athleteForm, email: event.target.value })} />
              </label>
              <label>
                Role
                <select value={athleteForm.role} onChange={(event) => setAthleteForm({ ...athleteForm, role: event.target.value as TeamRole })}>
                  <option value="player">Player</option>
                  <option value="captain">Captain</option>
                  <option value="substitute">Substitute</option>
                  <option value="bench">Bench</option>
                  <option value="individual_athlete">Individual athlete</option>
                </select>
              </label>
              <label>
                Position
                <input value={athleteForm.primary_position} onChange={(event) => setAthleteForm({ ...athleteForm, primary_position: event.target.value })} />
              </label>
              <label>
                Jersey
                <input value={athleteForm.jersey_number} onChange={(event) => setAthleteForm({ ...athleteForm, jersey_number: event.target.value })} />
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={athleteForm.is_captain} onChange={(event) => setAthleteForm({ ...athleteForm, is_captain: event.target.checked })} />
                Captain
              </label>
            </div>
            <div className="selection-list">
              {athletes.map((athlete) => (
                <button
                  type="button"
                  key={athlete.personId}
                  className={athlete.personId === selectedAthleteId ? "selected" : ""}
                  onClick={() => setSelectedAthleteId(athlete.personId)}
                >
                  <span>{athlete.name}</span>
                  <small>{athlete.email}</small>
                </button>
              ))}
            </div>
          </form>

          <form className="panel form-panel" id="events" onSubmit={createEvent}>
            <div className="panel-head">
              <div>
                <p className="section-label">Events</p>
                <h2>Schedule and check-in</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Schedule</button>
            </div>
            <div className="form-grid">
              <label>
                Title
                <input value={eventForm.title} onChange={(event) => setEventForm({ ...eventForm, title: event.target.value })} />
              </label>
              <label>
                Type
                <select value={eventForm.event_type} onChange={(event) => setEventForm({ ...eventForm, event_type: event.target.value as EventType })}>
                  <option value="match">Match</option>
                  <option value="training">Training</option>
                  <option value="tournament">Tournament</option>
                  <option value="assessment">Assessment</option>
                  <option value="meeting">Meeting</option>
                </select>
              </label>
              <label>
                Start
                <input type="datetime-local" value={eventForm.starts_at} onChange={(event) => setEventForm({ ...eventForm, starts_at: event.target.value })} />
              </label>
              <label>
                Minutes
                <input type="number" min="15" value={eventForm.duration_minutes} onChange={(event) => setEventForm({ ...eventForm, duration_minutes: Number(event.target.value) })} />
              </label>
              <label>
                Venue
                <input value={eventForm.venue_name} onChange={(event) => setEventForm({ ...eventForm, venue_name: event.target.value })} />
              </label>
              <label>
                Timezone
                <input value={eventForm.timezone} onChange={(event) => setEventForm({ ...eventForm, timezone: event.target.value })} />
              </label>
            </div>
            <div className="event-toolbar">
              <button type="button" onClick={seedAttendance} disabled={busyAction !== null}>Seed roster</button>
              <button type="button" onClick={checkClearance} disabled={busyAction !== null}>Clearance</button>
            </div>
            <div className="selection-list compact">
              {events.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={item.id === selectedEventId ? "selected" : ""}
                  onClick={() => setSelectedEventId(item.id)}
                >
                  <span>{item.title}</span>
                  <small>{item.event_type} · {new Date(item.starts_at).toLocaleString()}</small>
                </button>
              ))}
            </div>
            <div className="attendance-table">
              {attendance.map((record) => (
                <div key={record.id} className="attendance-row">
                  <span>{record.person_id.slice(0, 8)}</span>
                  <strong>{record.status}</strong>
                  <button type="button" onClick={() => recordAttendance(record.person_id, "present")}>
                    Present
                  </button>
                  <button type="button" onClick={() => recordAttendance(record.person_id, "confirmed")}>
                    Confirm
                  </button>
                </div>
              ))}
            </div>
          </form>
        </section>

        <section className="work-grid">
          <form className="panel form-panel" id="agents" onSubmit={createAgent}>
            <div className="panel-head">
              <div>
                <p className="section-label">Agents</p>
                <h2>Agent identity and scope</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Create</button>
            </div>
            <div className="form-grid">
              <label>
                Agent
                <input value={agentForm.name} onChange={(event) => setAgentForm({ ...agentForm, name: event.target.value })} />
              </label>
              <label>
                Kind
                <select value={agentForm.kind} onChange={(event) => setAgentForm({ ...agentForm, kind: event.target.value as AgentKind })}>
                  <option value="safeguarding">Safeguarding</option>
                  <option value="coaching">Coaching</option>
                  <option value="operations">Operations</option>
                  <option value="analytics">Analytics</option>
                  <option value="communications">Communications</option>
                  <option value="scouting">Scouting</option>
                </select>
              </label>
              <label>
                Model policy
                <input value={agentForm.model_policy} onChange={(event) => setAgentForm({ ...agentForm, model_policy: event.target.value })} />
              </label>
              <label>
                Purpose
                <textarea value={agentForm.purpose} onChange={(event) => setAgentForm({ ...agentForm, purpose: event.target.value })} />
              </label>
            </div>
            <div className="event-toolbar">
              <button type="button" onClick={() => assignAgent("organization")} disabled={busyAction !== null}>Assign org</button>
              <button type="button" onClick={() => assignAgent("team")} disabled={busyAction !== null}>Assign team</button>
              <button type="button" onClick={() => assignAgent("event")} disabled={busyAction !== null}>Assign event</button>
            </div>
            <div className="selection-list compact">
              {agents.map((agent) => (
                <button
                  type="button"
                  key={agent.id}
                  className={agent.id === selectedAgentId ? "selected" : ""}
                  onClick={() => setSelectedAgentId(agent.id)}
                >
                  <span>{agent.name}</span>
                  <small>{agent.kind} · {agent.model_policy ?? "default policy"}</small>
                </button>
              ))}
            </div>
          </form>

          <form className="panel form-panel" onSubmit={queueAgentTask}>
            <div className="panel-head">
              <div>
                <p className="section-label">Task inbox</p>
                <h2>Human-reviewed agent work</h2>
              </div>
              <button type="submit" disabled={busyAction !== null}>Queue</button>
            </div>
            <div className="form-grid">
              <label>
                Task type
                <input value={taskForm.task_type} onChange={(event) => setTaskForm({ ...taskForm, task_type: event.target.value })} />
              </label>
              <label>
                Input
                <input value={taskForm.input_ref} onChange={(event) => setTaskForm({ ...taskForm, input_ref: event.target.value })} />
              </label>
              <label className="wide-field">
                Title
                <input value={taskForm.title} onChange={(event) => setTaskForm({ ...taskForm, title: event.target.value })} />
              </label>
            </div>
            <div className="task-list">
              {agentTasks.map((task) => (
                <article key={task.id} className="task-card">
                  <div>
                    <strong>{task.title}</strong>
                    <span>{task.task_type} · {task.status}</span>
                  </div>
                  <div className="event-toolbar">
                    <button type="button" onClick={() => updateAgentTask(task.id, "running")}>Run</button>
                    <button type="button" onClick={() => updateAgentTask(task.id, "waiting_for_review")}>Review</button>
                    <button type="button" onClick={() => updateAgentTask(task.id, "completed")}>Done</button>
                  </div>
                </article>
              ))}
            </div>
          </form>
        </section>

        <section className="panel safeguarding-panel" id="safeguarding">
          <div className="panel-head">
            <div>
              <p className="section-label">Safeguarding</p>
              <h2>Guardian consent and event clearance</h2>
            </div>
            <div className="event-toolbar">
              <button type="button" onClick={createGuardian} disabled={busyAction !== null}>Link guardian</button>
              <button type="button" onClick={requestConsent} disabled={busyAction !== null}>Request consent</button>
            </div>
          </div>
          <div className="form-grid three">
            <label>
              Guardian
              <input value={guardianForm.guardian_display_name} onChange={(event) => setGuardianForm({ ...guardianForm, guardian_display_name: event.target.value })} />
            </label>
            <label>
              Email
              <input value={guardianForm.guardian_email} onChange={(event) => setGuardianForm({ ...guardianForm, guardian_email: event.target.value })} />
            </label>
            <label>
              Phone
              <input value={guardianForm.guardian_phone} onChange={(event) => setGuardianForm({ ...guardianForm, guardian_phone: event.target.value })} />
            </label>
          </div>
          <div className="consent-grid">
            <div>
              <span className="muted">Athlete</span>
              <strong>{selectedAthlete?.name ?? "None selected"}</strong>
            </div>
            <div>
              <span className="muted">Event</span>
              <strong>{selectedEvent?.title ?? "None selected"}</strong>
            </div>
            <div>
              <span className="muted">Clearance</span>
              <strong>{clearance?.status ?? "Unchecked"}</strong>
            </div>
            <div>
              <span className="muted">Guardian link</span>
              {consentUrl ? <a href={consentUrl}>{consentUrl}</a> : <strong>Not issued</strong>}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
