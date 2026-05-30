"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type {
  LocalIdentity,
  MyOfficialAssignmentRead,
  OfficialAssignmentStatus
} from "@/types/operations";

const defaultOfficialIdentity: LocalIdentity = {
  sub: "kc-referee-example",
  email: "referee@example.com",
  name: "Referee Example"
};

export default function OfficialsPortalPage() {
  const [identity, setIdentity] = useState<LocalIdentity>(defaultOfficialIdentity);
  const [organizationId, setOrganizationId] = useState("");
  const [statusFilter, setStatusFilter] = useState<OfficialAssignmentStatus | "all">("all");
  const [assignments, setAssignments] = useState<MyOfficialAssignmentRead[]>([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState("");
  const [responseNotes, setResponseNotes] = useState("Arriving 45 minutes before kickoff.");
  const [resultForm, setResultForm] = useState({
    home_score: 0,
    away_score: 0,
    notes: "Result confirmed by the assigned official."
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("afrolete.officialsPortal");
    if (!stored) {
      return;
    }
    try {
      const parsed = JSON.parse(stored) as {
        organizationId?: string;
        identity?: LocalIdentity;
        statusFilter?: OfficialAssignmentStatus | "all";
      };
      setOrganizationId(parsed.organizationId ?? "");
      setIdentity(parsed.identity ?? defaultOfficialIdentity);
      setStatusFilter(parsed.statusFilter ?? "all");
    } catch {
      window.localStorage.removeItem("afrolete.officialsPortal");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      "afrolete.officialsPortal",
      JSON.stringify({ organizationId, identity, statusFilter })
    );
  }, [identity, organizationId, statusFilter]);

  const selectedAssignment = useMemo(
    () => assignments.find((assignment) => assignment.id === selectedAssignmentId) ?? assignments[0] ?? null,
    [assignments, selectedAssignmentId]
  );
  const responseRequiredCount = assignments.filter((assignment) => assignment.response_required).length;
  const acceptedCount = assignments.filter((assignment) => assignment.status === "accepted" || assignment.status === "confirmed").length;
  const nextAssignment = assignments[0] ?? null;

  const loadAssignments = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    setBusy(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (organizationId) {
        params.set("organization_id", organizationId);
      }
      if (statusFilter !== "all") {
        params.set("status", statusFilter);
      }
      const query = params.toString() ? `?${params.toString()}` : "";
      const data = await apiRequest<MyOfficialAssignmentRead[]>(`/competitions/my-officiating${query}`, { identity });
      setAssignments(data);
      setSelectedAssignmentId((current) =>
        data.some((assignment) => assignment.id === current) ? current : data[0]?.id ?? ""
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Official assignments unavailable");
    } finally {
      setBusy(false);
    }
  };

  const respondToAssignment = async (
    assignment: MyOfficialAssignmentRead,
    status: "accepted" | "declined"
  ) => {
    setBusy(true);
    setError("");
    try {
      const updated = await apiRequest<MyOfficialAssignmentRead>(
        `/competitions/official-assignments/${assignment.id}/response`,
        {
          method: "PATCH",
          identity,
          body: {
            status,
            conflict_notes: status === "declined" ? responseNotes : responseNotes || null
          }
        }
      );
      setAssignments((current) => [
        updated,
        ...current.filter((item) => item.id !== updated.id)
      ].sort((left, right) => new Date(left.scheduled_at).getTime() - new Date(right.scheduled_at).getTime()));
      setSelectedAssignmentId(updated.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Official response failed");
    } finally {
      setBusy(false);
    }
  };

  const submitMatchReport = async (assignment: MyOfficialAssignmentRead) => {
    setBusy(true);
    setError("");
    try {
      const updated = await apiRequest<MyOfficialAssignmentRead>(
        `/competitions/official-assignments/${assignment.id}/match-report`,
        {
          method: "PATCH",
          identity,
          body: resultForm
        }
      );
      setAssignments((current) => [
        updated,
        ...current.filter((item) => item.id !== updated.id)
      ].sort((left, right) => new Date(left.scheduled_at).getTime() - new Date(right.scheduled_at).getTime()));
      setSelectedAssignmentId(updated.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Match report submission failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="official-page">
      <section className="official-shell official-hero">
        <div className="official-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Officials portal</span>
          </div>
        </div>
        <div>
          <p className="section-label">Match-day workspace</p>
          <h1>{identity.name}</h1>
          <p>Review assigned fixtures, confirm availability, share conflict notes, and keep organizers ahead of match-day cover risk.</p>
        </div>
      </section>

      <section className="official-shell official-controls">
        <form onSubmit={loadAssignments}>
          <label>
            Official email
            <input
              type="email"
              value={identity.email}
              onChange={(event) => setIdentity({ ...identity, email: event.target.value })}
            />
          </label>
          <label>
            Official name
            <input value={identity.name} onChange={(event) => setIdentity({ ...identity, name: event.target.value })} />
          </label>
          <label>
            Identity subject
            <input value={identity.sub} onChange={(event) => setIdentity({ ...identity, sub: event.target.value })} />
          </label>
          <label>
            Organization id
            <input value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} placeholder="Optional" />
          </label>
          <label>
            Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as OfficialAssignmentStatus | "all")}>
              <option value="all">All</option>
              <option value="proposed">Proposed</option>
              <option value="accepted">Accepted</option>
              <option value="confirmed">Confirmed</option>
              <option value="declined">Declined</option>
            </select>
          </label>
          <button type="submit" disabled={busy}>{busy ? "Loading" : "Open assignments"}</button>
        </form>
        {error ? <p className="form-error">{error}</p> : null}
      </section>

      <section className="official-shell official-metrics">
        <Metric label="Assignments" value={assignments.length} />
        <Metric label="Need response" value={responseRequiredCount} />
        <Metric label="Accepted" value={acceptedCount} />
        <Metric label="Next kickoff" value={nextAssignment ? new Date(nextAssignment.scheduled_at).toLocaleDateString() : "none"} />
      </section>

      {assignments.length ? (
        <section className="official-shell official-layout">
          <article className="official-panel">
            <p className="section-label">Fixture queue</p>
            <h2>{assignments.length} assignment{assignments.length === 1 ? "" : "s"}</h2>
            <div className="official-list">
              {assignments.map((assignment) => (
                <button
                  type="button"
                  key={assignment.id}
                  className={assignment.id === selectedAssignment?.id ? "selected" : ""}
                  onClick={() => setSelectedAssignmentId(assignment.id)}
                >
                  <strong>{assignment.home_team_name} vs {assignment.away_team_name}</strong>
                  <span>{assignment.role.replaceAll("_", " ")} · {assignment.status.replaceAll("_", " ")} · {new Date(assignment.scheduled_at).toLocaleString()}</span>
                  <small>{assignment.competition_name} · {assignment.venue_name ?? "Venue pending"}</small>
                </button>
              ))}
            </div>
          </article>

          <AssignmentDetail
            assignment={selectedAssignment}
            responseNotes={responseNotes}
            setResponseNotes={setResponseNotes}
            resultForm={resultForm}
            setResultForm={setResultForm}
            busy={busy}
            respondToAssignment={respondToAssignment}
            submitMatchReport={submitMatchReport}
          />
        </section>
      ) : (
        <section className="official-shell official-empty">
          <strong>No official assignments loaded.</strong>
          <span>Enter the email used by the organization when assigning the referee or match official.</span>
        </section>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function AssignmentDetail({
  assignment,
  responseNotes,
  setResponseNotes,
  resultForm,
  setResultForm,
  busy,
  respondToAssignment,
  submitMatchReport
}: {
  assignment: MyOfficialAssignmentRead | null;
  responseNotes: string;
  setResponseNotes: (value: string) => void;
  resultForm: { home_score: number; away_score: number; notes: string };
  setResultForm: (value: { home_score: number; away_score: number; notes: string }) => void;
  busy: boolean;
  respondToAssignment: (assignment: MyOfficialAssignmentRead, status: "accepted" | "declined") => Promise<void>;
  submitMatchReport: (assignment: MyOfficialAssignmentRead) => Promise<void>;
}) {
  if (!assignment) {
    return (
      <article className="official-panel">
        <p className="section-label">Assignment detail</p>
        <h2>Select a fixture</h2>
      </article>
    );
  }

  return (
    <article className="official-panel official-detail">
      <p className="section-label">Assignment detail</p>
      <h2>{assignment.home_team_name} vs {assignment.away_team_name}</h2>
      <dl className="official-facts">
        <div>
          <dt>Competition</dt>
          <dd>{assignment.competition_name}</dd>
        </div>
        <div>
          <dt>Role</dt>
          <dd>{assignment.role.replaceAll("_", " ")}</dd>
        </div>
        <div>
          <dt>Kickoff</dt>
          <dd>{new Date(assignment.scheduled_at).toLocaleString()}</dd>
        </div>
        <div>
          <dt>Venue</dt>
          <dd>{assignment.venue_name ?? "Venue pending"}</dd>
        </div>
        <div>
          <dt>Round</dt>
          <dd>{assignment.stage_label ?? "Stage"} · {assignment.round_label ?? "Round"}</dd>
        </div>
        <div>
          <dt>Certification</dt>
          <dd>{assignment.certification_level ?? "Not recorded"}</dd>
        </div>
      </dl>
      <div className={`official-status official-status-${assignment.status}`}>
        <strong>{assignment.status.replaceAll("_", " ")}</strong>
        <span>{assignment.action_label}</span>
        {assignment.home_score !== null && assignment.away_score !== null ? (
          <small>{assignment.home_team_name} {assignment.home_score} - {assignment.away_score} {assignment.away_team_name}</small>
        ) : null}
      </div>
      <label className="official-notes">
        Response notes
        <textarea value={responseNotes} onChange={(event) => setResponseNotes(event.target.value)} />
      </label>
      {assignment.conflict_notes ? <p className="official-note-preview">{assignment.conflict_notes}</p> : null}
      <div className="official-actions">
        <button type="button" onClick={() => respondToAssignment(assignment, "accepted")} disabled={busy || assignment.status === "accepted"}>
          Accept
        </button>
        <button type="button" onClick={() => respondToAssignment(assignment, "declined")} disabled={busy}>
          Decline
        </button>
      </div>
      <div className="official-report-form">
        <label>
          Home score
          <input
            type="number"
            min="0"
            value={resultForm.home_score}
            onChange={(event) => setResultForm({ ...resultForm, home_score: Number(event.target.value) })}
          />
        </label>
        <label>
          Away score
          <input
            type="number"
            min="0"
            value={resultForm.away_score}
            onChange={(event) => setResultForm({ ...resultForm, away_score: Number(event.target.value) })}
          />
        </label>
        <label>
          Match report notes
          <textarea value={resultForm.notes} onChange={(event) => setResultForm({ ...resultForm, notes: event.target.value })} />
        </label>
        <button
          type="button"
          onClick={() => submitMatchReport(assignment)}
          disabled={busy || !["accepted", "confirmed"].includes(assignment.status)}
        >
          Submit result
        </button>
        {assignment.fixture_notes ? <small>{assignment.fixture_notes}</small> : null}
      </div>
    </article>
  );
}
