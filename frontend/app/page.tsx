const operatingLanes = [
  { label: "Athletes", value: "1,248", detail: "profiles, guardians, readiness" },
  { label: "Sessions", value: "86", detail: "training, fixtures, attendance" },
  { label: "Signals", value: "14.2k", detail: "metrics, notes, video events" },
  { label: "Agents", value: "9", detail: "coaching, safety, operations" }
];

const workflows = [
  "Register athlete and guardian",
  "Build team roster",
  "Plan session",
  "Record attendance",
  "Review AI insights",
  "Issue consent request",
  "Generate report"
];

const agents = [
  {
    name: "Coach Intelligence",
    state: "Reviewing U16 load",
    accent: "teal"
  },
  {
    name: "Safeguarding Watch",
    state: "Monitoring consent gaps",
    accent: "amber"
  },
  {
    name: "Event Operator",
    state: "Balancing venue conflicts",
    accent: "violet"
  }
];

export default function HomePage() {
  return (
    <main className="shell">
      <aside className="rail" aria-label="Primary">
        <div className="mark">AL</div>
        <nav>
          <a className="active">Command</a>
          <a>Roster</a>
          <a>Events</a>
          <a>Insights</a>
          <a>Agents</a>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">AfroLete V2</p>
            <h1>Sports operations, athlete intelligence, and governed AI agents.</h1>
          </div>
          <button type="button">Open command center</button>
        </header>

        <section className="hero-grid" aria-label="Platform overview">
          <div className="mission-panel">
            <p className="section-label">Mission Control</p>
            <h2>Every athlete, session, consent, signal, and decision in one operating surface.</h2>
            <p>
              AfroLete coordinates clubs, schools, teams, parents, coaches, officials, sponsors,
              and AI agents through one auditable SaaS platform.
            </p>
            <div className="workflow-strip">
              {workflows.map((workflow) => (
                <span key={workflow}>{workflow}</span>
              ))}
            </div>
          </div>

          <div className="signal-panel">
            <p className="section-label">Today</p>
            <div className="pulse">
              <span />
              <strong>14 workflows need attention</strong>
            </div>
            <ul>
              <li>5 athletes missing guardian consent</li>
              <li>3 training loads above planned intensity</li>
              <li>2 venue conflicts flagged by Event Operator</li>
              <li>4 assessment reviews queued for coaches</li>
            </ul>
          </div>
        </section>

        <section className="metric-grid" aria-label="Operating lanes">
          {operatingLanes.map((lane) => (
            <article key={lane.label} className="metric-card">
              <p>{lane.label}</p>
              <strong>{lane.value}</strong>
              <span>{lane.detail}</span>
            </article>
          ))}
        </section>

        <section className="lower-grid">
          <div className="agents-panel">
            <p className="section-label">First-class AI agents</p>
            <h2>Agents act with identity, scope, permission, task state, and review trails.</h2>
            <div className="agent-list">
              {agents.map((agent) => (
                <article key={agent.name} className={`agent-card ${agent.accent}`}>
                  <span />
                  <div>
                    <strong>{agent.name}</strong>
                    <p>{agent.state}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="architecture-panel">
            <p className="section-label">Platform spine</p>
            <dl>
              <div>
                <dt>Backend</dt>
                <dd>FastAPI, SQLAlchemy, Alembic, OpenAPI</dd>
              </div>
              <div>
                <dt>Identity</dt>
                <dd>Keycloak realm, internal user bridge</dd>
              </div>
              <div>
                <dt>Authorization</dt>
                <dd>SpiceDB resource relationships</dd>
              </div>
              <div>
                <dt>Operations</dt>
                <dd>Postgres, Redis, Temporal, MinIO, OpenBao</dd>
              </div>
            </dl>
          </div>
        </section>
      </section>
    </main>
  );
}

