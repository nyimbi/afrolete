"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import type {
  AthleteAssessmentRead,
  LocalIdentity,
  MetricCategory,
  PlayerMatchGuidanceRead,
  PlayerMatchTrainingFollowupRead,
  PlayerPerformanceProfileRead
} from "@/types/operations";

const defaultPlayerIdentity: LocalIdentity = {
  sub: "kc-athlete-1",
  email: "performance-athlete@example.com",
  name: "Performance Athlete"
};

const playerChartColors = ["var(--teal)", "var(--blue)", "var(--amber)", "var(--violet)", "var(--green)"];
type BenchmarkCohortScope = "tenant" | "age_group" | "position" | "region";
const metricCategoryOptions: MetricCategory[] = [
  "physical",
  "technical",
  "tactical",
  "mental",
  "wellness",
  "competition"
];

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

function playerRiskColor(riskBand: string) {
  if (riskBand === "critical") {
    return "var(--red)";
  }
  if (riskBand === "high") {
    return "var(--orange)";
  }
  if (riskBand === "watch") {
    return "var(--amber)";
  }
  return "var(--green)";
}

function isoDateOffset(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
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
  const injuryRisk = profile.injury_risk;
  const visibleSeries = profile.trend_series.filter((series) => series.points.length > 0).slice(0, 4);
  const visibleForecasts = profile.forecast_scenarios.filter((scenario) => scenario.sample_size > 0).slice(0, 4);
  const visibleWhatIfs = profile.what_if_scenarios.filter((scenario) => scenario.sample_size > 0).slice(0, 4);
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
  const forecastMax = Math.max(
    1,
    ...[...visibleForecasts, ...visibleWhatIfs].flatMap((scenario) => [
      Math.abs(scenario.latest_value ?? 0),
      Math.abs(scenario.forecast_next_value ?? 0),
      ...scenario.projected_points.map((point) => Math.abs(point))
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
          <span>Forecast scenario</span>
          <strong>{visibleForecasts.length}/{visibleWhatIfs.length} metrics</strong>
          <small>Baseline and what-if runways with confidence and risk flags.</small>
        </div>
        <div className="chart-bars">
          {visibleForecasts.map((scenario, index) => {
            const width = boundedPercent((Math.abs(scenario.forecast_next_value ?? scenario.latest_value ?? 0) / forecastMax) * 100);
            return (
              <div className="chart-bar-row" key={`${scenario.metric_definition_id}-player-forecast`}>
                <span>{scenario.metric_name}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{ width: `${width}%`, backgroundColor: playerChartColors[(index + 3) % playerChartColors.length] }}
                  />
                </div>
                <strong>{Math.round(scenario.confidence * 100)}%</strong>
              </div>
            );
          })}
          {visibleForecasts.length === 0 ? (
            <div className="chart-bar-row">
              <span>No forecast</span>
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
          <span>What-if plan</span>
          <strong>{visibleWhatIfs[0]?.scenario_label ?? "No scenario"}</strong>
          <small>Projected response to adjusted load and readiness.</small>
        </div>
        <div className="chart-bars">
          {visibleWhatIfs.map((scenario, index) => {
            const width = boundedPercent((Math.abs(scenario.forecast_next_value ?? scenario.latest_value ?? 0) / forecastMax) * 100);
            return (
              <div className="chart-bar-row" key={`${scenario.metric_definition_id}-player-what-if`}>
                <span>{scenario.metric_name}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{ width: `${width}%`, backgroundColor: playerChartColors[(index + 4) % playerChartColors.length] }}
                  />
                </div>
                <strong>{scenario.risk_level.replaceAll("_", " ")}</strong>
              </div>
            );
          })}
          {visibleWhatIfs.length === 0 ? (
            <div className="chart-bar-row">
              <span>No what-if</span>
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
          <span>Safety signal</span>
          <strong>{injuryRisk.risk_band.replaceAll("_", " ")} · {injuryRisk.score}/100</strong>
          <small>{Math.round(injuryRisk.confidence * 100)}% confidence · {injuryRisk.model_policy.replaceAll("_", " ")}</small>
        </div>
        <div className="chart-bars">
          <div className="chart-bar-row">
            <span>Overall risk</span>
            <div className="chart-track">
              <div
                className="chart-fill"
                style={{ width: `${boundedPercent(injuryRisk.score)}%`, backgroundColor: playerRiskColor(injuryRisk.risk_band) }}
              />
            </div>
            <strong>{injuryRisk.risk_band.replaceAll("_", " ")}</strong>
          </div>
          <div className="chart-bar-row">
            <span>Readiness</span>
            <div className="chart-track">
              <div
                className="chart-fill"
                style={{
                  width: `${boundedPercent(injuryRisk.latest_readiness_score ?? injuryRisk.average_readiness_score)}%`,
                  backgroundColor: "var(--teal)"
                }}
              />
            </div>
            <strong>{injuryRisk.latest_readiness_score ?? injuryRisk.average_readiness_score ?? "n/a"}</strong>
          </div>
          <div className="chart-bar-row">
            <span>Load ratio</span>
            <div className="chart-track">
              <div
                className="chart-fill"
                style={{
                  width: `${boundedPercent((injuryRisk.acute_chronic_ratio ?? 0) * 50)}%`,
                  backgroundColor: "var(--violet)"
                }}
              />
            </div>
            <strong>{injuryRisk.acute_chronic_ratio ?? "n/a"}</strong>
          </div>
          <div className="chart-bar-row">
            <span>Movement</span>
            <div className="chart-track">
              <div
                className="chart-fill"
                style={{
                  width: `${boundedPercent((injuryRisk.biomechanical_risk_count ?? 0) * 34)}%`,
                  backgroundColor: "var(--amber)"
                }}
              />
            </div>
            <strong>{injuryRisk.biomechanical_risk_count || "n/a"}</strong>
          </div>
        </div>
        <small>{injuryRisk.drivers[0] ?? injuryRisk.recommendation}</small>
        {injuryRisk.video_risk_labels.length ? <small>Video: {injuryRisk.video_risk_labels.join(", ")}</small> : null}
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
        {visibleForecasts.map((scenario, index) => (
          <article className="player-chart-card" key={`${scenario.metric_definition_id}-player-forecast-scenario`}>
            <div>
              <span>Scenario runway</span>
              <strong>{scenario.metric_name}</strong>
              <small>
                {scenario.risk_level.replaceAll("_", " ")} · {scenario.data_quality.replaceAll("_", " ")} · next{" "}
                {playerValueLabel(scenario.forecast_next_value, scenario.unit)}
              </small>
              <small>{scenario.model_policy.replaceAll("_", " ")}</small>
            </div>
            <div className="spark-bars" aria-label={`${scenario.metric_name} player forecast scenario`}>
              {scenario.projected_points.map((point, pointIndex) => (
                <i
                  key={`${scenario.metric_definition_id}-player-projection-${pointIndex}`}
                  title={`Scenario ${pointIndex + 1} · ${playerValueLabel(point, scenario.unit)}`}
                  style={{
                    height: `${boundedPercent((Math.abs(point) / forecastMax) * 100)}%`,
                    backgroundColor: playerChartColors[(index + pointIndex) % playerChartColors.length]
                  }}
                />
              ))}
            </div>
            <small>{scenario.recommendation}</small>
          </article>
        ))}
        {visibleWhatIfs.map((scenario, index) => (
          <article className="player-chart-card" key={`${scenario.metric_definition_id}-player-what-if-scenario`}>
            <div>
              <span>What-if runway</span>
              <strong>{scenario.metric_name}</strong>
              <small>
                {scenario.scenario_label} · horizon {scenario.horizon} · next{" "}
                {playerValueLabel(scenario.forecast_next_value, scenario.unit)}
              </small>
              <small>{scenario.model_policy.replaceAll("_", " ")}</small>
            </div>
            <div className="spark-bars" aria-label={`${scenario.metric_name} player what-if scenario`}>
              {scenario.projected_points.map((point, pointIndex) => (
                <i
                  key={`${scenario.metric_definition_id}-player-what-if-projection-${pointIndex}`}
                  title={`What-if ${pointIndex + 1} · ${playerValueLabel(point, scenario.unit)}`}
                  style={{
                    height: `${boundedPercent((Math.abs(point) / forecastMax) * 100)}%`,
                    backgroundColor: playerChartColors[(index + pointIndex + 2) % playerChartColors.length]
                  }}
                />
              ))}
            </div>
            <small>{scenario.recommendation}</small>
          </article>
        ))}
        <article className="player-chart-card">
          <div>
            <span>Risk drivers</span>
            <strong>{injuryRisk.risk_band.replaceAll("_", " ")} injury-risk context</strong>
            <small>{injuryRisk.recommendation}</small>
          </div>
          <div className="chart-bars">
            {injuryRisk.drivers.slice(0, 4).map((driver, index) => (
              <div className="chart-bar-row" key={`${driver}-${index}`}>
                <span>{driver}</span>
                <div className="chart-track">
                  <div
                    className="chart-fill"
                    style={{
                      width: `${boundedPercent(injuryRisk.score - index * 12)}%`,
                      backgroundColor: playerRiskColor(injuryRisk.risk_band)
                    }}
                  />
                </div>
                <strong>{index + 1}</strong>
              </div>
            ))}
          </div>
        </article>
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
  const [trendCategory, setTrendCategory] = useState<MetricCategory | "all">("all");
  const [trendMetricCode, setTrendMetricCode] = useState("");
  const [trendPeriodStart, setTrendPeriodStart] = useState("");
  const [trendPeriodEnd, setTrendPeriodEnd] = useState("");
  const [whatIfAdjustment, setWhatIfAdjustment] = useState(10);
  const [whatIfReadiness, setWhatIfReadiness] = useState(72);
  const [whatIfHorizon, setWhatIfHorizon] = useState(4);
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
  const [trainingFollowups, setTrainingFollowups] = useState<PlayerMatchTrainingFollowupRead[]>([]);

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
        trendCategory?: MetricCategory | "all";
        trendMetricCode?: string;
        trendPeriodStart?: string;
        trendPeriodEnd?: string;
        whatIfAdjustment?: number;
        whatIfReadiness?: number;
        whatIfHorizon?: number;
      };
      setOrganizationId(parsed.organizationId ?? "");
      setIdentity(parsed.identity ?? defaultPlayerIdentity);
      setBenchmarkScope(parsed.benchmarkScope ?? "tenant");
      setTrendCategory(parsed.trendCategory ?? "all");
      setTrendMetricCode(parsed.trendMetricCode ?? "");
      setTrendPeriodStart(parsed.trendPeriodStart ?? "");
      setTrendPeriodEnd(parsed.trendPeriodEnd ?? "");
      setWhatIfAdjustment(parsed.whatIfAdjustment ?? 10);
      setWhatIfReadiness(parsed.whatIfReadiness ?? 72);
      setWhatIfHorizon(parsed.whatIfHorizon ?? 4);
    } catch {
      window.localStorage.removeItem("afrolete.playerPortal");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      "afrolete.playerPortal",
      JSON.stringify({
        organizationId,
        identity,
        benchmarkScope,
        trendCategory,
        trendMetricCode,
        trendPeriodStart,
        trendPeriodEnd,
        whatIfAdjustment,
        whatIfReadiness,
        whatIfHorizon
      })
    );
  }, [
    benchmarkScope,
    identity,
    organizationId,
    trendCategory,
    trendMetricCode,
    trendPeriodEnd,
    trendPeriodStart,
    whatIfAdjustment,
    whatIfHorizon,
    whatIfReadiness
  ]);

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
      const params = new URLSearchParams({
        organization_id: organizationId,
        observation_limit: "8",
        benchmark_cohort_scope: benchmarkScope,
        what_if_training_adjustment_percent: String(whatIfAdjustment),
        what_if_readiness_score: String(whatIfReadiness),
        what_if_horizon: String(whatIfHorizon)
      });
      if (trendCategory !== "all") {
        params.set("trend_category", trendCategory);
      }
      if (trendMetricCode.trim()) {
        params.set("trend_metric_code", trendMetricCode.trim().toLowerCase());
      }
      if (trendPeriodStart) {
        params.set("trend_period_start", trendPeriodStart);
      }
      if (trendPeriodEnd) {
        params.set("trend_period_end", trendPeriodEnd);
      }
      const rows = await apiRequest<PlayerPerformanceProfileRead[]>(
        `/performance/my-profiles?${params.toString()}`,
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
  const injuryRisk = selectedProfile?.injury_risk;

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

  const createTrainingFollowup = async (guidance: PlayerMatchGuidanceRead) => {
    if (!selectedProfile || !organizationId) {
      setError("Load a player profile before creating a follow-up plan");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const followup = await apiRequest<PlayerMatchTrainingFollowupRead>(
        `/performance/my-profiles/${selectedProfile.athlete_profile_id}/match-guidance/training-followups`,
        {
          method: "POST",
          identity,
          body: {
            organization_id: organizationId,
            tracking_run_id: guidance.tracking_run_id,
            track_id: guidance.track_id,
            period_start: isoDateOffset(1),
            period_end: isoDateOffset(14),
            max_items: 3
          }
        }
      );
      setTrainingFollowups((current) => [
        followup,
        ...current.filter(
          (item) => !(item.tracking_run_id === followup.tracking_run_id && item.track_id === followup.track_id)
        )
      ]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Training follow-up creation failed");
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
          <select
            value={trendCategory}
            onChange={(event) => setTrendCategory(event.target.value as MetricCategory | "all")}
          >
            <option value="all">All metric domains</option>
            {metricCategoryOptions.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          <input
            placeholder="Trend metric code"
            value={trendMetricCode}
            onChange={(event) => setTrendMetricCode(event.target.value)}
          />
          <input
            type="date"
            aria-label="Trend start"
            value={trendPeriodStart}
            onChange={(event) => setTrendPeriodStart(event.target.value)}
          />
          <input
            type="date"
            aria-label="Trend end"
            value={trendPeriodEnd}
            onChange={(event) => setTrendPeriodEnd(event.target.value)}
          />
          <input
            type="number"
            aria-label="What-if load adjustment"
            min="-50"
            max="50"
            value={whatIfAdjustment}
            onChange={(event) => setWhatIfAdjustment(Number(event.target.value))}
          />
          <input
            type="number"
            aria-label="What-if readiness"
            min="0"
            max="100"
            value={whatIfReadiness}
            onChange={(event) => setWhatIfReadiness(Number(event.target.value))}
          />
          <input
            type="number"
            aria-label="What-if horizon"
            min="1"
            max="8"
            value={whatIfHorizon}
            onChange={(event) => setWhatIfHorizon(Number(event.target.value))}
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
              <article>
                <span>Safety</span>
                <strong>{injuryRisk ? `${injuryRisk.risk_band.replaceAll("_", " ")} · ${injuryRisk.score}/100` : "Awaiting risk signal"}</strong>
                <p>{injuryRisk?.drivers[0] ?? "Readiness, workload, incidents, weather, surfaces, wearable data, and video movement signals will shape this card."}</p>
              </article>
            </section>

            <PlayerPerformanceVisuals profile={selectedProfile} />

            <section className="player-visual-grid">
              {selectedProfile.match_guidance.slice(0, 4).map((guidance) => (
                <article className="player-chart-card" key={`${guidance.tracking_run_id}-${guidance.track_id}`}>
                  {(() => {
                    const followup = trainingFollowups.find(
                      (item) => item.tracking_run_id === guidance.tracking_run_id && item.track_id === guidance.track_id
                    );
                    return (
                      <>
                  <div>
                    <span>Match guidance</span>
                    <strong>{guidance.match_label ?? guidance.opponent_name}</strong>
                    <small>
                      {guidance.team_label ?? "Unassigned"} · {guidance.player_label ?? guidance.track_id}
                      {guidance.jersey_number ? ` · #${guidance.jersey_number}` : ""}
                    </small>
                    <small>
                      {Math.round(guidance.tracking_quality_score * 100)}% quality · {guidance.readiness_level.replaceAll("_", " ")}
                    </small>
                  </div>
                  <div className="chart-bars">
                    <div className="chart-bar-row">
                      <span>Distance</span>
                      <div className="chart-track">
                        <div
                          className="chart-fill"
                          style={{
                            width: `${boundedPercent((guidance.distance_m / 12000) * 100)}%`,
                            backgroundColor: "var(--teal)"
                          }}
                        />
                      </div>
                      <strong>{Math.round(guidance.distance_m)}m</strong>
                    </div>
                    <div className="chart-bar-row">
                      <span>High speed</span>
                      <div className="chart-track">
                        <div
                          className="chart-fill"
                          style={{
                            width: `${boundedPercent((guidance.high_speed_distance_m / 1200) * 100)}%`,
                            backgroundColor: "var(--amber)"
                          }}
                        />
                      </div>
                      <strong>{Math.round(guidance.high_speed_distance_m)}m</strong>
                    </div>
                    <div className="chart-bar-row">
                      <span>Top speed</span>
                      <div className="chart-track">
                        <div
                          className="chart-fill"
                          style={{
                            width: `${boundedPercent((guidance.max_speed_mps / 11) * 100)}%`,
                            backgroundColor: "var(--blue)"
                          }}
                        />
                      </div>
                      <strong>{guidance.max_speed_mps.toFixed(1)} m/s</strong>
                    </div>
                    <div className="chart-bar-row">
                      <span>Work rate</span>
                      <div className="chart-track">
                        <div
                          className="chart-fill"
                          style={{
                            width: `${boundedPercent((guidance.work_rate_m_per_min / 180) * 100)}%`,
                            backgroundColor: "var(--violet)"
                          }}
                        />
                      </div>
                      <strong>{guidance.work_rate_m_per_min.toFixed(0)} m/min</strong>
                    </div>
                  </div>
                  {guidance.player_guidance.slice(0, 3).map((item, index) => (
                    <small key={`${guidance.track_id}-guidance-${index}`}>{item}</small>
                  ))}
                  {guidance.action_plan.slice(0, 3).map((item, index) => (
                    <div className="player-action-plan" key={`${guidance.track_id}-action-${index}`}>
                      <strong>{item.focus}</strong>
                      <span>{item.cue}</span>
                      <small>{item.drill_recommendation}</small>
                      <small>{item.priority} · {item.evidence}</small>
                    </div>
                  ))}
                  {guidance.tactical_context.slice(0, 2).map((item, index) => (
                    <small key={`${guidance.track_id}-context-${index}`}>{item}</small>
                  ))}
                  <button
                    className="player-inline-action"
                    type="button"
                    disabled={busy}
                    onClick={() => createTrainingFollowup(guidance)}
                  >
                    {followup ? "Rebuild follow-up" : "Create follow-up"}
                  </button>
                  {followup ? (
                    <>
                      <small>
                        Training plan ready: {followup.title} · {followup.item_count} item(s) · {followup.period_start} to{" "}
                        {followup.period_end}
                      </small>
                      <small>
                        Agent review: {followup.agent_task_title ?? "Training Strategy Agent"} ·{" "}
                        {(followup.agent_task_status ?? "queued").replaceAll("_", " ")}
                      </small>
                    </>
                  ) : null}
                      </>
                    );
                  })()}
                </article>
              ))}
              {selectedProfile.match_guidance.length === 0 ? (
                <article className="player-chart-card">
                  <div>
                    <span>Match guidance</span>
                    <strong>No confirmed tracks</strong>
                    <small>Coach-confirmed match tracks will appear here after video analysis.</small>
                  </div>
                  <div className="chart-bars">
                    <div className="chart-bar-row">
                      <span>Distance</span>
                      <div className="chart-track">
                        <div className="chart-fill" style={{ width: "4%", backgroundColor: "var(--quiet)" }} />
                      </div>
                      <strong>n/a</strong>
                    </div>
                  </div>
                </article>
              ) : null}
            </section>

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
