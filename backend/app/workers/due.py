import argparse
import asyncio
import json
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import parse_positive_int_map
from app.db.session import SessionLocal
from app.models.enums import CommunicationChannel, NotificationFrequency
from app.services.agents import run_agent_task_worker
from app.services.communications import run_digest_scheduler_worker
from app.services.developer import run_developer_webhook_retry_due
from app.services.performance import (
    run_assessment_review_escalation_worker,
    run_performance_achievement_worker,
    run_performance_forecast_validation_worker,
    run_performance_injury_risk_alert_scan_worker,
    run_wearable_pull_retry_worker,
)

WORKER_LANES = (
    "agent-tasks",
    "communication-digests",
    "developer-webhooks",
    "performance-achievements",
    "performance-forecast-validations",
    "performance-review-escalations",
    "performance-injury-risk-alerts",
    "wearable-pull-retries",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run due AfroLete background worker lanes.")
    parser.add_argument("--organization-id", type=UUID, default=None)
    parser.add_argument("--lane", choices=(*WORKER_LANES, "all"), action="append", default=None)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--agent-limit", type=int, default=None)
    parser.add_argument("--communication-digest-limit", type=int, default=None)
    parser.add_argument(
        "--communication-digest-frequency",
        choices=[NotificationFrequency.DAILY_DIGEST.value, NotificationFrequency.WEEKLY_DIGEST.value],
        default=None,
    )
    parser.add_argument("--webhook-limit", type=int, default=None)
    parser.add_argument("--performance-limit", type=int, default=None)
    parser.add_argument("--performance-forecast-validation-limit", type=int, default=None)
    parser.add_argument("--auto-alert-performance-forecast-drift", action="store_true")
    parser.add_argument("--performance-forecast-drift-repeat-after-hours", type=int, default=24)
    parser.add_argument(
        "--performance-forecast-drift-channel",
        choices=[channel.value for channel in CommunicationChannel],
        action="append",
        default=None,
    )
    parser.add_argument("--dry-run-performance-forecast-drift-alerts", action="store_true")
    parser.add_argument("--performance-review-limit", type=int, default=None)
    parser.add_argument("--performance-review-horizon-hours", type=int, default=24)
    parser.add_argument("--performance-review-repeat-after-hours", type=int, default=24)
    parser.add_argument("--dry-run-performance-review-escalations", action="store_true")
    parser.add_argument("--performance-injury-risk-limit", type=int, default=None)
    parser.add_argument("--performance-injury-risk-threshold", type=int, default=65)
    parser.add_argument("--performance-injury-risk-repeat-after-hours", type=int, default=24)
    parser.add_argument(
        "--performance-injury-risk-channel",
        choices=[channel.value for channel in CommunicationChannel],
        action="append",
        default=None,
    )
    parser.add_argument("--dry-run-performance-injury-risk-alerts", action="store_true")
    parser.add_argument("--wearable-pull-limit", type=int, default=None)
    parser.add_argument("--wearable-pull-max-pages", type=int, default=3)
    parser.add_argument("--wearable-pull-default-retry-after-seconds", type=int, default=300)
    parser.add_argument(
        "--wearable-pull-provider-retry-after-seconds",
        default=None,
        help="Comma-separated provider retry windows, for example whoop=900,garmin=300.",
    )
    parser.add_argument(
        "--wearable-pull-provider-max-pages",
        default=None,
        help="Comma-separated provider max-page limits, for example whoop=1,fitbit=5.",
    )
    parser.add_argument("--webhook-max-attempts", type=int, default=3)
    parser.add_argument("--include-recorded-webhooks", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def selected_lanes(lanes: Sequence[str]) -> set[str]:
    if "all" in lanes:
        return set(WORKER_LANES)
    return set(lanes)


async def run_due_workers(
    db: AsyncSession,
    *,
    organization_id: UUID | None = None,
    lanes: Sequence[str] = ("all",),
    limit: int = 25,
    agent_limit: int | None = None,
    communication_digest_limit: int | None = None,
    communication_digest_frequency: NotificationFrequency | None = None,
    webhook_limit: int | None = None,
    performance_limit: int | None = None,
    performance_forecast_validation_limit: int | None = None,
    auto_alert_performance_forecast_drift: bool = False,
    performance_forecast_drift_repeat_after_hours: int = 24,
    performance_forecast_drift_channels: Sequence[CommunicationChannel] | None = None,
    dry_run_performance_forecast_drift_alerts: bool = False,
    performance_review_limit: int | None = None,
    performance_review_horizon_hours: int = 24,
    performance_review_repeat_after_hours: int = 24,
    dry_run_performance_review_escalations: bool = False,
    performance_injury_risk_limit: int | None = None,
    performance_injury_risk_threshold: int = 65,
    performance_injury_risk_repeat_after_hours: int = 24,
    performance_injury_risk_channels: Sequence[CommunicationChannel] | None = None,
    dry_run_performance_injury_risk_alerts: bool = False,
    wearable_pull_limit: int | None = None,
    wearable_pull_max_pages: int = 3,
    wearable_pull_default_retry_after_seconds: int = 300,
    wearable_pull_provider_retry_after_seconds: dict[str, int] | None = None,
    wearable_pull_provider_max_pages: dict[str, int] | None = None,
    webhook_max_attempts: int = 3,
    include_recorded_webhooks: bool = False,
) -> dict[str, object]:
    active_lanes = selected_lanes(lanes)
    results: dict[str, object] = {}
    if "agent-tasks" in active_lanes:
        results["agent_tasks"] = (
            await run_agent_task_worker(
                db,
                organization_id=organization_id,
                limit=agent_limit or limit,
            )
        ).model_dump(mode="json")
    if "communication-digests" in active_lanes:
        results["communication_digests"] = (
            await run_digest_scheduler_worker(
                db,
                organization_id=organization_id,
                frequency=communication_digest_frequency,
                limit=communication_digest_limit or limit,
            )
        ).model_dump(mode="json")
    if "developer-webhooks" in active_lanes:
        results["developer_webhooks"] = (
            await run_developer_webhook_retry_due(
                db,
                organization_id=organization_id,
                max_attempts=webhook_max_attempts,
                limit=webhook_limit or limit,
                include_recorded=include_recorded_webhooks,
            )
        ).model_dump(mode="json")
    if "performance-achievements" in active_lanes:
        results["performance_achievements"] = (
            await run_performance_achievement_worker(
                db,
                organization_id=organization_id,
                limit=performance_limit or limit,
            )
        ).model_dump(mode="json")
    if "performance-forecast-validations" in active_lanes:
        results["performance_forecast_validations"] = (
            await run_performance_forecast_validation_worker(
                db,
                organization_id=organization_id,
                limit=performance_forecast_validation_limit or performance_limit or limit,
                auto_alerts=auto_alert_performance_forecast_drift,
                alert_repeat_after_hours=performance_forecast_drift_repeat_after_hours,
                alert_channels=list(performance_forecast_drift_channels)
                if performance_forecast_drift_channels
                else None,
                dry_run_alerts=dry_run_performance_forecast_drift_alerts,
            )
        ).model_dump(mode="json")
    if "performance-review-escalations" in active_lanes:
        results["performance_review_escalations"] = (
            await run_assessment_review_escalation_worker(
                db,
                organization_id=organization_id,
                limit=performance_review_limit or limit,
                horizon_hours=performance_review_horizon_hours,
                repeat_after_hours=performance_review_repeat_after_hours,
                dry_run=dry_run_performance_review_escalations,
            )
        ).model_dump(mode="json")
    if "performance-injury-risk-alerts" in active_lanes:
        results["performance_injury_risk_alerts"] = (
            await run_performance_injury_risk_alert_scan_worker(
                db,
                organization_id=organization_id,
                limit=performance_injury_risk_limit or limit,
                threshold_score=performance_injury_risk_threshold,
                repeat_after_hours=performance_injury_risk_repeat_after_hours,
                channels=list(performance_injury_risk_channels) if performance_injury_risk_channels else None,
                dry_run=dry_run_performance_injury_risk_alerts,
            )
        ).model_dump(mode="json")
    if "wearable-pull-retries" in active_lanes:
        results["wearable_pull_retries"] = (
            await run_wearable_pull_retry_worker(
                db,
                organization_id=organization_id,
                limit=wearable_pull_limit or limit,
                max_pages=wearable_pull_max_pages,
                default_retry_after_seconds=wearable_pull_default_retry_after_seconds,
                provider_retry_after_seconds=wearable_pull_provider_retry_after_seconds,
                provider_max_pages=wearable_pull_provider_max_pages,
            )
        ).model_dump(mode="json")
    return {
        "organization_id": str(organization_id) if organization_id else None,
        "lanes": sorted(active_lanes),
        "results": results,
        "summary": worker_summary(results),
    }


def worker_summary(results: dict[str, object]) -> dict[str, int]:
    summary = {
        "lane_count": len(results),
        "eligible_count": 0,
        "processed_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
    }
    for result in results.values():
        if not isinstance(result, dict):
            continue
        summary["eligible_count"] += int(result.get("eligible_count") or 0)
        summary["processed_count"] += int(
            result.get("executed_count")
            or result.get("replayed_count")
            or result.get("escalated_count")
            or result.get("alerted_count")
            or result.get("retried_count")
            or 0
        )
        summary["skipped_count"] += int(result.get("skipped_count") or 0)
        summary["failed_count"] += int(result.get("failed_count") or 0) + int(
            result.get("alert_failed_count") or 0
        )
    return summary


async def run() -> None:
    args = parse_args()
    async with SessionLocal() as db:
        result = await run_due_workers(
            db,
            organization_id=args.organization_id,
            lanes=args.lane or ("all",),
            limit=args.limit,
            agent_limit=args.agent_limit,
            communication_digest_limit=args.communication_digest_limit,
            communication_digest_frequency=NotificationFrequency(args.communication_digest_frequency)
            if args.communication_digest_frequency
            else None,
            webhook_limit=args.webhook_limit,
            performance_limit=args.performance_limit,
            performance_forecast_validation_limit=args.performance_forecast_validation_limit,
            auto_alert_performance_forecast_drift=args.auto_alert_performance_forecast_drift,
            performance_forecast_drift_repeat_after_hours=args.performance_forecast_drift_repeat_after_hours,
            performance_forecast_drift_channels=[
                CommunicationChannel(channel) for channel in args.performance_forecast_drift_channel
            ]
            if args.performance_forecast_drift_channel
            else None,
            dry_run_performance_forecast_drift_alerts=args.dry_run_performance_forecast_drift_alerts,
            performance_review_limit=args.performance_review_limit,
            performance_review_horizon_hours=args.performance_review_horizon_hours,
            performance_review_repeat_after_hours=args.performance_review_repeat_after_hours,
            dry_run_performance_review_escalations=args.dry_run_performance_review_escalations,
            performance_injury_risk_limit=args.performance_injury_risk_limit,
            performance_injury_risk_threshold=args.performance_injury_risk_threshold,
            performance_injury_risk_repeat_after_hours=args.performance_injury_risk_repeat_after_hours,
            performance_injury_risk_channels=[
                CommunicationChannel(channel) for channel in args.performance_injury_risk_channel
            ]
            if args.performance_injury_risk_channel
            else None,
            dry_run_performance_injury_risk_alerts=args.dry_run_performance_injury_risk_alerts,
            wearable_pull_limit=args.wearable_pull_limit,
            wearable_pull_max_pages=args.wearable_pull_max_pages,
            wearable_pull_default_retry_after_seconds=args.wearable_pull_default_retry_after_seconds,
            wearable_pull_provider_retry_after_seconds=parse_positive_int_map(
                args.wearable_pull_provider_retry_after_seconds
            )
            if args.wearable_pull_provider_retry_after_seconds
            else None,
            wearable_pull_provider_max_pages=parse_positive_int_map(args.wearable_pull_provider_max_pages)
            if args.wearable_pull_provider_max_pages
            else None,
            webhook_max_attempts=args.webhook_max_attempts,
            include_recorded_webhooks=args.include_recorded_webhooks,
        )
    print(json.dumps(result, indent=2 if args.pretty else None))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
