"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { AthleteAssessmentRead, LocalIdentity, PlayerPerformanceProfileRead } from "@/types/operations";

const defaultPlayerIdentity: LocalIdentity = {
  sub: "kc-athlete-1",
  email: "performance-athlete@example.com",
  name: "Performance Athlete"
};

const playerChartColors = ["var(--teal)", "var(--blue)", "var(--amber)", "var(--violet)", "var(--green)"];
type BenchmarkCohortScope = "tenant" | "age_group" | "position" | "region";

function playerValueLabel(value: number | null | undefined, unit?: string | null) {
  if (typeof value !== "number") {
    return "n/a";
  }
  const rounded = Number.isInteger(value) ? value.toString() : value.toFixed(1);
  return unit ? `${rounded} ${unit}` : rounded;
}

function boundedPercent(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 4;
  }
  return Math.max(4, Math.min(100, value));
}

function goalProgress(goal: PlayerPerformanceProfileRead["goals"][number]) {
  if (typeof goal.current_value !== "number") {
    return 4;
  }
  const baseline = goal.baseline_value ?? (goal.direction === "decrease" ? goal.target_value * 1.25 : 0);
  if (goal.direction === "decrease") {
    const span = baseline - goal.target_value;
    return span > 0 ? boundedPercent(((baseline - goal.current_value) / span) * 100) : boundedPercent(goal.target_value / goal.current_value * 100);
  }
  const span = goal.target_value - baseline;
  return span > 0 ? boundedPercent(((goal.current_value - baseline) / span) * 100) : boundedPercent(goal.current_value / goal.target_value * 100);
}

function PlayerPerformanceVisuals({ profile }: { profile: PlayerPerformanceProfileRead }) {
  const latestAssessment = profile.latest_assessment;
  const visibleSeries = profile.trend_series.filter((series) => series.points.length > 0).slice(0, 4);
  const composition = latestAssessment
    ? [
        { label: "Physical", value: latestAssessment.physical_score, color: "var(--teal)" },
        { label: "Technical", value: latestAssessment.technical_score, color: "var(--blue)" },
        { label: "Tactical", value: latestAssessment.tactical_score, color: "var(--amber)" },
        { label: "Mental", value: latestAssessment.mental_score, color: "var(--violet)" }
      ]
    : [];
  const trendMax = Math.max(
    1,
    ...profile.trends.slice(0, 4).flatMap((trend) => [
      Math.abs(trend.first_value ?? 0),
      Math.abs(trend.latest_value ?? 0),
      Math.abs(trend.forecast_next_value ?? 0),
      Math.abs(trend.best_value ?? 0)
    ])
  );

  return (
    <>
      <section className="player-visual-grid">
        <article className="player-chart-card">
        <div>
          <span>ALS composition</span>
          <strong>{profile.latest_overall_score?.toFixed(1) ?? "No score"}</strong>
          <small>{profile.rating ?? "Verified coach scores will appear here."}</small>
        </div>
        <div className="chart-bars">
          {composition.map((score) => (
            <div className="chart-bar-row" key={score.label}>
              <span>{score.label}</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: `${boundedPercent(score.value)}%`, backgroundColor: score.color }} />
              </div>
              <strong>{score.value.toFixed(0)}</strong>
            </div>
          ))}
          {composition.length === 0 ? (
            <div className="chart-bar-row">
              <span>No scores</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--quiet)" }} />
              </div>
              <strong>n/a</strong>
            </div>
          ) : null}
        </div>
        </article>

        <article className="player-chart-card">
        <div>
          <span>Trend runway</span>
          <strong>{profile.trends.length} metrics</strong>
          <small>Latest value compared with the next simple forecast.</small>
        </div>
        <div className="chart-bars">
          {profile.trends.slice(0, 4).map((trend, index) => {
            const width = boundedPercent((Math.abs(trend.forecast_next_value ?? trend.latest_value ?? 0) / trendMax) * 100);
            return (
              <div className="chart-bar-row" key={`${trend.metric_definition_id}-player-trend`}>
                <span>{trend.metric_name}</span>
                <div className="chart-track">
                  <div className="chart-fill" style={{ width: `${width}%`, backgroundColor: playerChartColors[index % playerChartColors.length] }} />
                </div>
                <strong>{playerValueLabel(trend.forecast_next_value ?? trend.latest_value, trend.unit)}</strong>
              </div>
            );
          })}
          {profile.trends.length === 0 ? (
            <div className="chart-bar-row">
              <span>No trend</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--quiet)" }} />
              </div>
              <strong>n/a</strong>
            </div>
          ) : null}
        </div>
        </article>

        <article className="player-chart-card">
        <div>
          <span>Cohort standing</span>
          <strong>{profile.benchmarks.length} benchmarks</strong>
          <small>
            {profile.benchmarks[0]?.cohort_label ?? "All athletes"} ·{" "}
            {(profile.benchmarks[0]?.cohort_scope ?? "tenant").replaceAll("_", " ")}
          </small>
        </div>
        <div className="chart-bars">
          {profile.benchmarks.slice(0, 4).map((benchmark, index) => (
            <div className="chart-bar-row" key={`${benchmark.metric_definition_id}-player-benchmark`}>
              <span>{benchmark.metric_name}</span>
              <div className="chart-track">
                <div
                  className="chart-fill"
                  style={{
                    width: `${boundedPercent(benchmark.percentile_rank)}%`,
                    backgroundColor: playerChartColors[(index + 1) % playerChartColors.length]
                  }}
                />
              </div>
              <strong>{benchmark.percentile_rank === null ? "n/a" : `${benchmark.percentile_rank}%`}</strong>
            </div>
          ))}
          {profile.benchmarks.length === 0 ? (
            <div className="chart-bar-row">
              <span>No cohort</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--quiet)" }} />
              </div>
              <strong>n/a</strong>
            </div>
          ) : null}
        </div>
        </article>

        <article className="player-chart-card">
        <div>
          <span>Goal pace</span>
          <strong>{profile.active_goal_count}/{profile.achieved_goal_count}</strong>
          <small>Active progress and achieved targets.</small>
        </div>
        <div className="chart-bars">
          {profile.goals.slice(0, 4).map((goal, index) => (
            <div className="chart-bar-row" key={`${goal.id}-player-goal`}>
              <span>{goal.title}</span>
              <div className="chart-track">
                <div
                  className="chart-fill"
                  style={{
                    width: `${goal.status === "achieved" ? 100 : goalProgress(goal)}%`,
                    backgroundColor: goal.status === "achieved" ? "var(--green)" : playerChartColors[(index + 2) % playerChartColors.length]
                  }}
                />
              </div>
              <strong>{goal.current_value === null ? "n/a" : playerValueLabel(goal.current_value)}</strong>
            </div>
          ))}
          {profile.goals.length === 0 ? (
            <div className="chart-bar-row">
              <span>No goals</span>
              <div className="chart-track">
                <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--quiet)" }} />
              </div>
              <strong>n/a</strong>
            </div>
          ) : null}
        </div>
        </article>
      </section>

      <section className="player-visual-grid player-history-grid">
        {profile.cohort_comparisons.slice(0, 4).map((comparison, index) => (
          <article className="player-chart-card" key={`${comparison.cohort_scope}-player-comparison`}>
            <div>
              <span>Cohort comparison</span>
              <strong>{comparison.cohort_label}</strong>
              <small>
                {comparison.cohort_scope.replaceAll("_", " ")} · {comparison.metric_count} metrics · {comparison.watch_count} watch
              </small>
            </div>
            <div className="chart-bars">
              <div className="chart-bar-row">
                <span>Average</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{
                      width: `${boundedPercent(comparison.average_percentile)}%`,
                      backgroundColor: playerChartColors[index % playerChartColors.length]
                    }}
                  />
                </div>
                <strong>{comparison.average_percentile === null ? "n/a" : `${comparison.average_percentile}%`}</strong>
              </div>
              <div className="chart-bar-row">
                <span>{comparison.top_metric_name ?? "Top metric"}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{
                      width: `${boundedPercent(comparison.top_percentile)}%`,
                      backgroundColor: playerChartColors[(index + 1) % playerChartColors.length]
                    }}
                  />
                </div>
                <strong>{comparison.top_percentile === null ? "n/a" : `${comparison.top_percentile}%`}</strong>
              </div>
            </div>
            <small>{comparison.recommendation}</small>
          </article>
        ))}
        {visibleSeries.map((series, index) => (
          <article className="player-chart-card" key={`${series.metric_definition_id}-player-series`}>
            <div>
              <span>Metric history</span>
              <strong>{series.metric_name}</strong>
              <small>
                {series.sample_size} points · latest {playerValueLabel(series.latest_value, series.unit)} · forecast{" "}
                {playerValueLabel(series.forecast_next_value, series.unit)}
              </small>
            </div>
            <div className="spark-bars" aria-label={`${series.metric_name} player time series`}>
              {series.points.map((point) => (
                <i
                  key={point.observation_id}
                  title={`${new Date(point.observed_at).toLocaleDateString()} · ${playerValueLabel(point.value, series.unit)}`}
                  style={{
                    height: `${boundedPercent(point.normalized_value)}%`,
                    backgroundColor: playerChartColors[index % playerChartColors.length]
                  }}
                />
              ))}
            </div>
            <small>{series.recommendation}</small>
          </article>
        ))}
        {visibleSeries.length === 0 ? (
          <article className="player-chart-card">
            <div>
              <span>Metric history</span>
              <strong>Collecting observations</strong>
              <small>Accepted observations will render here as athlete-friendly time-series bars.</small>
            </div>
            <div className="spark-bars empty">
              <i />
              <i />
              <i />
            </div>
          </article>
        ) : null}
      </section>
    </>
  );
}

export default function PlayerPerformancePage() {
  const [organizationId, setOrganizationId] = useState("");
  const [identity, setIdentity] = useState<LocalIdentity>(defaultPlayerIdentity);
  const [benchmarkScope, setBenchmarkScope] = useState<BenchmarkCohortScope>("tenant");
  const [profiles, setProfiles] = useState<PlayerPerformanceProfileRead[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [selfAssessment, setSelfAssessment] = useState({
    physical_score: 70,
    technical_score: 70,
    tactical_score: 70,
    mental_score: 70,
    perceived_exertion: 5,
    effort_rating: 8,
    summary: ""
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("afrolete.playerPortal");
    if (!stored) {
      return;
    }
    try {
      const parsed = JSON.parse(stored) as {
        organizationId?: string;
        identity?: LocalIdentity;
        benchmarkScope?: BenchmarkCohortScope;
      };
      setOrganizationId(parsed.organizationId ?? "");
      setIdentity(parsed.identity ?? defaultPlayerIdentity);
      setBenchmarkScope(parsed.benchmarkScope ?? "tenant");
    } catch {
      window.localStorage.removeItem("afrolete.playerPortal");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("afrolete.playerPortal", JSON.stringify({ organizationId, identity, benchmarkScope }));
  }, [benchmarkScope, identity, organizationId]);

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
        `/performance/my-profiles?organization_id=${encodeURIComponent(organizationId)}&observation_limit=8&benchmark_cohort_scope=${benchmarkScope}`,
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

  const submitSelfAssessment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedProfile || !organizationId) {
      setError("Load a player profile before submitting an assessment");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await apiRequest<AthleteAssessmentRead>(
        `/performance/my-profiles/${selectedProfile.athlete_profile_id}/self-assessments`,
        {
          method: "POST",
          identity,
          body: {
            organization_id: organizationId,
            ...selfAssessment,
            summary: selfAssessment.summary || null
          }
        }
      );
      setSelfAssessment((current) => ({ ...current, summary: "" }));
      await loadProfiles();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Self-assessment submission failed");
    } finally {
      setBusy(false);
    }
  };

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
          <select
            value={benchmarkScope}
            onChange={(event) => setBenchmarkScope(event.target.value as BenchmarkCohortScope)}
          >
            <option value="tenant">All athletes</option>
            <option value="age_group">Age group</option>
            <option value="position">Position</option>
            <option value="region">Country/region</option>
          </select>
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

            <PlayerPerformanceVisuals profile={selectedProfile} />

            <form className="player-self-check" onSubmit={submitSelfAssessment}>
              <div>
                <h2>Self-Assessment</h2>
                <span>Scores are submitted for coach review before they become verified performance evidence.</span>
              </div>
              <label>
                Physical
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={selfAssessment.physical_score}
                  onChange={(event) => setSelfAssessment({ ...selfAssessment, physical_score: Number(event.target.value) })}
                />
              </label>
              <label>
                Technical
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={selfAssessment.technical_score}
                  onChange={(event) => setSelfAssessment({ ...selfAssessment, technical_score: Number(event.target.value) })}
                />
              </label>
              <label>
                Tactical
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={selfAssessment.tactical_score}
                  onChange={(event) => setSelfAssessment({ ...selfAssessment, tactical_score: Number(event.target.value) })}
                />
              </label>
              <label>
                Mental
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={selfAssessment.mental_score}
                  onChange={(event) => setSelfAssessment({ ...selfAssessment, mental_score: Number(event.target.value) })}
                />
              </label>
              <label>
                RPE
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={selfAssessment.perceived_exertion}
                  onChange={(event) => setSelfAssessment({ ...selfAssessment, perceived_exertion: Number(event.target.value) })}
                />
              </label>
              <label>
                Effort
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={selfAssessment.effort_rating}
                  onChange={(event) => setSelfAssessment({ ...selfAssessment, effort_rating: Number(event.target.value) })}
                />
              </label>
              <label className="player-self-note">
                Note
                <textarea
                  value={selfAssessment.summary}
                  onChange={(event) => setSelfAssessment({ ...selfAssessment, summary: event.target.value })}
                />
              </label>
              <button type="submit" disabled={busy}>Submit</button>
            </form>

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
