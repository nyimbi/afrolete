"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { LocalIdentity, PlayerPerformanceProfileRead } from "@/types/operations";

const defaultPlayerIdentity: LocalIdentity = {
  sub: "kc-athlete-1",
  email: "performance-athlete@example.com",
  name: "Performance Athlete"
};

export default function PlayerPerformancePage() {
  const [organizationId, setOrganizationId] = useState("");
  const [identity, setIdentity] = useState<LocalIdentity>(defaultPlayerIdentity);
  const [profiles, setProfiles] = useState<PlayerPerformanceProfileRead[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("afrolete.playerPortal");
    if (!stored) {
      return;
    }
    try {
      const parsed = JSON.parse(stored) as { organizationId?: string; identity?: LocalIdentity };
      setOrganizationId(parsed.organizationId ?? "");
      setIdentity(parsed.identity ?? defaultPlayerIdentity);
    } catch {
      window.localStorage.removeItem("afrolete.playerPortal");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("afrolete.playerPortal", JSON.stringify({ organizationId, identity }));
  }, [identity, organizationId]);

  const selectedProfile = useMemo(
    () => profiles.find((profile) => profile.athlete_profile_id === selectedProfileId) ?? profiles[0] ?? null,
    [profiles, selectedProfileId]
  );

  const loadProfiles = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!organizationId) {
      setError("Organization id is required");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const rows = await apiRequest<PlayerPerformanceProfileRead[]>(
        `/performance/my-profiles?organization_id=${encodeURIComponent(organizationId)}&observation_limit=8`,
        { identity }
      );
      setProfiles(rows);
      setSelectedProfileId((current) =>
        rows.some((profile) => profile.athlete_profile_id === current)
          ? current
          : rows[0]?.athlete_profile_id ?? ""
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Player performance load failed");
    } finally {
      setBusy(false);
    }
  };

  const strongestTrend = selectedProfile?.trends.find((trend) => trend.trend_direction === "improving");
  const watchBenchmark = selectedProfile?.benchmarks.find((benchmark) => benchmark.benchmark_band === "watch");

  return (
    <main className="player-page">
      <section className="player-shell">
        <form className="player-toolbar" onSubmit={loadProfiles}>
          <div>
            <strong>AfroLete Player</strong>
            <span>{identity.name}</span>
          </div>
          <input
            placeholder="Organization id"
            value={organizationId}
            onChange={(event) => setOrganizationId(event.target.value)}
          />
          <input
            placeholder="Email"
            value={identity.email}
            onChange={(event) => setIdentity({ ...identity, email: event.target.value })}
          />
          <button type="submit" disabled={busy}>{busy ? "Loading" : "Refresh"}</button>
        </form>

        {error ? <p className="player-message">{error}</p> : null}

        {profiles.length > 1 ? (
          <div className="player-tabs">
            {profiles.map((profile) => (
              <button
                key={profile.athlete_profile_id}
                type="button"
                className={profile.athlete_profile_id === selectedProfile?.athlete_profile_id ? "selected" : ""}
                onClick={() => setSelectedProfileId(profile.athlete_profile_id)}
              >
                {profile.athlete_name}
              </button>
            ))}
          </div>
        ) : null}

        {selectedProfile ? (
          <>
            <section className="player-hero">
              <div>
                <span>Current ALS</span>
                <strong>{selectedProfile.latest_overall_score?.toFixed(1) ?? "No score"}</strong>
                <small>{selectedProfile.rating ?? "Awaiting assessment"}</small>
              </div>
              <dl>
                <div>
                  <dt>Observations</dt>
                  <dd>{selectedProfile.observation_count}</dd>
                </div>
                <div>
                  <dt>Goals</dt>
                  <dd>{selectedProfile.active_goal_count}/{selectedProfile.achieved_goal_count}</dd>
                </div>
                <div>
                  <dt>Awards</dt>
                  <dd>{selectedProfile.award_count}</dd>
                </div>
              </dl>
            </section>

            <section className="player-insights">
              <article>
                <span>Momentum</span>
                <strong>{strongestTrend?.metric_name ?? "Collecting trend data"}</strong>
                <p>{strongestTrend?.recommendation ?? "Two or more accepted observations unlock a trend signal."}</p>
              </article>
              <article>
                <span>Focus</span>
                <strong>{watchBenchmark?.metric_name ?? "No urgent cohort gap"}</strong>
                <p>{watchBenchmark?.recommendation ?? "Current benchmark cards do not show a watch-band priority."}</p>
              </article>
            </section>

            <section className="player-columns">
              <div>
                <h2>Goals</h2>
                <div className="player-list">
                  {selectedProfile.goals.map((goal) => (
                    <article key={goal.id}>
                      <strong>{goal.title}</strong>
                      <span>{goal.current_value ?? "No value"} / {goal.target_value} · {goal.status}</span>
                      <small>{goal.due_at ?? "Open timeline"}</small>
                    </article>
                  ))}
                  {selectedProfile.goals.length === 0 ? <span>No active goals yet.</span> : null}
                </div>
              </div>

              <div>
                <h2>Awards</h2>
                <div className="player-awards">
                  {selectedProfile.awards.map((award) => (
                    <article key={award.id}>
                      <strong>{award.title}</strong>
                      <span>{award.badge_code}</span>
                      <small>{award.source_summary ?? award.achievement_type}</small>
                    </article>
                  ))}
                  {selectedProfile.awards.length === 0 ? <span>No awards yet.</span> : null}
                </div>
              </div>
            </section>

            <section className="player-columns">
              <div>
                <h2>Trends</h2>
                <div className="player-list">
                  {selectedProfile.trends.slice(0, 5).map((trend) => (
                    <article key={trend.metric_definition_id}>
                      <strong>{trend.metric_name}</strong>
                      <span>{trend.trend_direction} · latest {trend.latest_value ?? "n/a"}</span>
                      <small>{trend.recommendation}</small>
                    </article>
                  ))}
                  {selectedProfile.trends.length === 0 ? <span>No trend lines yet.</span> : null}
                </div>
              </div>

              <div>
                <h2>Recent Measurements</h2>
                <div className="player-list">
                  {selectedProfile.observations.map((observation) => (
                    <article key={observation.id}>
                      <strong>{observation.value}</strong>
                      <span>{observation.source} · {observation.verification_status}</span>
                      <small>{new Date(observation.observed_at).toLocaleString()}</small>
                    </article>
                  ))}
                  {selectedProfile.observations.length === 0 ? <span>No observations yet.</span> : null}
                </div>
              </div>
            </section>
          </>
        ) : (
          <section className="player-empty">
            <strong>No player profile loaded</strong>
            <span>Use a player-linked account for the selected organization.</span>
          </section>
        )}
      </section>
    </main>
  );
}
