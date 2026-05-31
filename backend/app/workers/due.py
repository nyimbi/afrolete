import argparse
import asyncio
import json
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings, parse_positive_int_map
from app.db.session import SessionLocal
from app.models.enums import CommunicationChannel, NotificationFrequency
from app.services.agents import run_agent_task_worker
from app.services.assets import run_emergency_escalation_timer_worker
from app.services.billing import (
    run_dunning_worker,
    run_late_fee_worker,
    run_payment_retry_worker,
    run_recurring_invoice_worker,
)
from app.services.coach_education import run_coach_education_renewal_reminder_worker
from app.services.commercial import run_grant_saved_search_alert_worker
from app.services.communications import (
    run_digest_scheduler_worker,
    run_message_escalation_worker,
    run_scheduled_message_dispatch_worker,
)
from app.services.developer import run_developer_webhook_retry_due
from app.services.events import run_event_travel_consent_reminder_worker
from app.services.organizations import run_member_subscription_charge_worker, run_member_subscription_reminder_worker
from app.services.performance import (
    run_assessment_review_escalation_worker,
    run_performance_achievement_worker,
    run_performance_forecast_validation_worker,
    run_performance_highlight_reel_reminder_worker,
    run_performance_injury_risk_alert_scan_worker,
    run_performance_video_pose_worker,
    run_wearable_pull_retry_worker,
)
from app.services.safeguarding import (
    run_compliance_credential_renewal_reminder_worker,
    run_compliance_reconciliation_worker,
    run_family_coordination_digest_worker,
    run_guardian_portal_invite_reminder_worker,
    run_insurance_policy_renewal_reminder_worker,
)
from app.services.storage.lifecycle import run_object_storage_lifecycle
from app.services.volunteers import run_volunteer_reminder_worker
from app.workers.video_pose import run_performance_video_pose_endpoint_worker

WORKER_LANES = (
    "agent-tasks",
    "billing-dunning",
    "billing-late-fees",
    "billing-payment-retries",
    "billing-recurring-invoices",
    "communication-digests",
    "communication-escalations",
    "communication-scheduled-dispatch",
    "coach-education-renewal-reminders",
    "commercial-grant-alerts",
    "compliance-credential-renewal-reminders",
    "compliance-reconciliation",
    "developer-webhooks",
    "emergency-escalations",
    "event-travel-consent-reminders",
    "family-coordination-digests",
    "family-portal-invite-reminders",
    "insurance-renewal-reminders",
    "member-dues-charges",
    "member-dues-reminders",
    "object-storage-lifecycle",
    "performance-achievements",
    "performance-forecast-validations",
    "performance-highlight-reel-reminders",
    "performance-review-escalations",
    "performance-injury-risk-alerts",
    "performance-video-pose",
    "volunteer-reminders",
    "wearable-pull-retries",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run due AfroLete background worker lanes.")
    parser.add_argument("--organization-id", type=UUID, default=None)
    parser.add_argument("--lane", choices=(*WORKER_LANES, "all"), action="append", default=None)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--agent-limit", type=int, default=None)
    parser.add_argument("--billing-dunning-limit", type=int, default=None)
    parser.add_argument("--billing-dunning-overdue-as-of", type=date_from_isoformat, default=None)
    parser.add_argument("--billing-dunning-overdue-after-days", type=int, default=0)
    parser.add_argument("--billing-dunning-repeat-after-days", type=int, default=7)
    parser.add_argument("--dry-run-billing-dunning", action="store_true")
    parser.add_argument("--billing-late-fee-limit", type=int, default=None)
    parser.add_argument("--billing-late-fee-apply-on", type=date_from_isoformat, default=None)
    parser.add_argument("--billing-late-fee-overdue-after-days", type=int, default=0)
    parser.add_argument("--billing-late-fee-repeat-after-days", type=int, default=30)
    parser.add_argument("--billing-late-fee-fixed-fee", type=Decimal, default=Decimal("0"))
    parser.add_argument("--billing-late-fee-percentage-rate", type=Decimal, default=Decimal("2.00"))
    parser.add_argument("--billing-late-fee-max-fee", type=Decimal, default=None)
    parser.add_argument("--dry-run-billing-late-fees", action="store_true")
    parser.add_argument("--billing-payment-retry-limit", type=int, default=None)
    parser.add_argument("--billing-payment-retry-at", type=datetime_from_isoformat, default=None)
    parser.add_argument("--billing-payment-retry-overdue-after-days", type=int, default=0)
    parser.add_argument("--billing-payment-retry-repeat-after-hours", type=int, default=24)
    parser.add_argument("--billing-payment-retry-max-attempts", type=int, default=3)
    parser.add_argument("--billing-payment-retry-provider", default="billing_provider")
    parser.add_argument("--dry-run-billing-payment-retries", action="store_true")
    parser.add_argument("--billing-recurring-invoice-limit", type=int, default=None)
    parser.add_argument("--billing-recurring-invoice-bill-on", type=date_from_isoformat, default=None)
    parser.add_argument("--billing-recurring-invoice-due-in-days", type=int, default=14)
    parser.add_argument("--billing-recurring-invoice-prefix", default="SAAS")
    parser.add_argument("--dry-run-billing-recurring-invoices", action="store_true")
    parser.add_argument("--communication-digest-limit", type=int, default=None)
    parser.add_argument("--communication-escalation-limit", type=int, default=None)
    parser.add_argument("--communication-escalation-unresolved-after-minutes", type=int, default=15)
    parser.add_argument("--communication-escalation-repeat-after-minutes", type=int, default=60)
    parser.add_argument("--communication-escalation-level", type=int, default=2)
    parser.add_argument("--communication-escalation-failed-only", action="store_true")
    parser.add_argument("--dry-run-communication-escalations", action="store_true")
    parser.add_argument("--communication-scheduled-dispatch-limit", type=int, default=None)
    parser.add_argument("--dry-run-communication-scheduled-dispatch", action="store_true")
    parser.add_argument("--coach-education-renewal-reminder-limit", type=int, default=None)
    parser.add_argument("--coach-education-renewal-reminder-as-of", type=date_from_isoformat, default=None)
    parser.add_argument("--coach-education-renewal-reminder-horizon-days", type=int, default=45)
    parser.add_argument("--coach-education-renewal-reminder-repeat-after-days", type=int, default=14)
    parser.add_argument(
        "--coach-education-renewal-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.EMAIL.value,
    )
    parser.add_argument("--dry-run-coach-education-renewal-reminders", action="store_true")
    parser.add_argument("--commercial-grant-alert-limit", type=int, default=None)
    parser.add_argument("--dry-run-commercial-grant-alerts", action="store_true")
    parser.add_argument(
        "--communication-escalation-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=None,
    )
    parser.add_argument("--compliance-reconciliation-limit", type=int, default=None)
    parser.add_argument("--compliance-credential-renewal-reminder-limit", type=int, default=None)
    parser.add_argument("--compliance-credential-renewal-reminder-as-of", type=date_from_isoformat, default=None)
    parser.add_argument("--compliance-credential-renewal-reminder-horizon-days", type=int, default=60)
    parser.add_argument("--compliance-credential-renewal-reminder-repeat-after-days", type=int, default=14)
    parser.add_argument(
        "--compliance-credential-renewal-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.EMAIL.value,
    )
    parser.add_argument("--dry-run-compliance-credential-renewal-reminders", action="store_true")
    parser.add_argument(
        "--communication-digest-frequency",
        choices=[NotificationFrequency.DAILY_DIGEST.value, NotificationFrequency.WEEKLY_DIGEST.value],
        default=None,
    )
    parser.add_argument("--webhook-limit", type=int, default=None)
    parser.add_argument("--emergency-escalation-limit", type=int, default=None)
    parser.add_argument("--emergency-escalation-unresolved-after-minutes", type=int, default=15)
    parser.add_argument("--emergency-escalation-repeat-after-minutes", type=int, default=15)
    parser.add_argument("--dry-run-emergency-escalations", action="store_true")
    parser.add_argument("--event-travel-consent-reminder-limit", type=int, default=None)
    parser.add_argument("--event-travel-consent-reminder-due-within-hours", type=int, default=48)
    parser.add_argument("--event-travel-consent-reminder-repeat-after-hours", type=int, default=24)
    parser.add_argument(
        "--event-travel-consent-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.EMAIL.value,
    )
    parser.add_argument("--dry-run-event-travel-consent-reminders", action="store_true")
    parser.add_argument("--family-coordination-digest-limit", type=int, default=None)
    parser.add_argument("--family-coordination-digest-repeat-after-hours", type=int, default=24)
    parser.add_argument(
        "--family-coordination-digest-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.IN_APP.value,
    )
    parser.add_argument(
        "--family-coordination-digest-portal-url",
        default="https://afrolete.lindela.io/family",
    )
    parser.add_argument("--dry-run-family-coordination-digests", action="store_true")
    parser.add_argument("--family-portal-invite-reminder-limit", type=int, default=None)
    parser.add_argument("--family-portal-invite-reminder-invited-before-hours", type=int, default=24)
    parser.add_argument("--family-portal-invite-reminder-repeat-after-hours", type=int, default=24)
    parser.add_argument(
        "--family-portal-invite-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.EMAIL.value,
    )
    parser.add_argument("--dry-run-family-portal-invite-reminders", action="store_true")
    parser.add_argument("--insurance-renewal-reminder-limit", type=int, default=None)
    parser.add_argument("--insurance-renewal-reminder-as-of", type=date_from_isoformat, default=None)
    parser.add_argument("--insurance-renewal-reminder-horizon-days", type=int, default=120)
    parser.add_argument("--insurance-renewal-reminder-repeat-after-days", type=int, default=14)
    parser.add_argument(
        "--insurance-renewal-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.EMAIL.value,
    )
    parser.add_argument("--dry-run-insurance-renewal-reminders", action="store_true")
    parser.add_argument("--member-dues-charge-limit", type=int, default=None)
    parser.add_argument("--member-dues-charge-on", type=date_from_isoformat, default=None)
    parser.add_argument("--dry-run-member-dues-charges", action="store_true")
    parser.add_argument("--member-dues-reminder-limit", type=int, default=None)
    parser.add_argument("--member-dues-reminder-as-of", type=date_from_isoformat, default=None)
    parser.add_argument("--member-dues-reminder-due-within-days", type=int, default=7)
    parser.add_argument("--member-dues-reminder-repeat-after-days", type=int, default=7)
    parser.add_argument(
        "--member-dues-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.EMAIL.value,
    )
    parser.add_argument("--dry-run-member-dues-reminders", action="store_true")
    parser.add_argument("--volunteer-reminder-limit", type=int, default=None)
    parser.add_argument("--volunteer-reminder-due-within-days", type=int, default=7)
    parser.add_argument("--volunteer-reminder-repeat-after-hours", type=int, default=24)
    parser.add_argument(
        "--volunteer-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.EMAIL.value,
    )
    parser.add_argument("--dry-run-volunteer-reminders", action="store_true")
    parser.add_argument("--object-storage-lifecycle-retention-days", type=int, default=None)
    parser.add_argument("--dry-run-object-storage-lifecycle", action="store_true")
    parser.add_argument("--performance-limit", type=int, default=None)
    parser.add_argument("--performance-forecast-validation-limit", type=int, default=None)
    parser.add_argument("--performance-highlight-reel-reminder-limit", type=int, default=None)
    parser.add_argument("--performance-highlight-reel-reminder-shared-before-hours", type=int, default=24)
    parser.add_argument("--performance-highlight-reel-reminder-repeat-after-hours", type=int, default=24)
    parser.add_argument(
        "--performance-highlight-reel-reminder-channel",
        choices=[channel.value for channel in CommunicationChannel],
        default=CommunicationChannel.IN_APP.value,
    )
    parser.add_argument("--dry-run-performance-highlight-reel-reminders", action="store_true")
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
    parser.add_argument("--performance-video-pose-limit", type=int, default=None)
    parser.add_argument("--performance-video-pose-video-asset-id", type=UUID, default=None)
    parser.add_argument("--performance-video-pose-max-frames", type=int, default=None)
    parser.add_argument("--performance-video-pose-sample-every-seconds", type=float, default=None)
    parser.add_argument("--performance-video-pose-api-base-url", default=None)
    parser.add_argument("--performance-video-pose-bearer-token", default=None)
    parser.add_argument("--performance-video-pose-local-auth-sub", default=None)
    parser.add_argument("--performance-video-pose-local-auth-email", default=None)
    parser.add_argument("--performance-video-pose-local-auth-name", default=None)
    parser.add_argument("--performance-video-pose-api-timeout", type=float, default=None)
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


def performance_video_pose_request_headers(
    args: argparse.Namespace,
    settings: Settings | None = None,
) -> dict[str, str]:
    selected_settings = settings or get_settings()
    headers: dict[str, str] = {}
    bearer_token = (
        args.performance_video_pose_bearer_token
        or selected_settings.performance_pose_worker_bearer_token
    )
    local_auth_sub = (
        args.performance_video_pose_local_auth_sub
        or selected_settings.performance_pose_worker_local_auth_sub
    )
    local_auth_email = (
        args.performance_video_pose_local_auth_email
        or selected_settings.performance_pose_worker_local_auth_email
    )
    local_auth_name = (
        args.performance_video_pose_local_auth_name
        or selected_settings.performance_pose_worker_local_auth_name
    )
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if local_auth_sub:
        headers["X-Afrolete-Sub"] = local_auth_sub
    if local_auth_email:
        headers["X-Afrolete-Email"] = local_auth_email
    if local_auth_name:
        headers["X-Afrolete-Name"] = local_auth_name
    return headers


async def run_due_workers(
    db: AsyncSession,
    *,
    organization_id: UUID | None = None,
    lanes: Sequence[str] = ("all",),
    limit: int = 25,
    agent_limit: int | None = None,
    billing_dunning_limit: int | None = None,
    billing_dunning_overdue_as_of: date | None = None,
    billing_dunning_overdue_after_days: int = 0,
    billing_dunning_repeat_after_days: int = 7,
    dry_run_billing_dunning: bool = False,
    billing_late_fee_limit: int | None = None,
    billing_late_fee_apply_on: date | None = None,
    billing_late_fee_overdue_after_days: int = 0,
    billing_late_fee_repeat_after_days: int = 30,
    billing_late_fee_fixed_fee: Decimal = Decimal("0"),
    billing_late_fee_percentage_rate: Decimal = Decimal("2.00"),
    billing_late_fee_max_fee: Decimal | None = None,
    dry_run_billing_late_fees: bool = False,
    billing_payment_retry_limit: int | None = None,
    billing_payment_retry_at: datetime | None = None,
    billing_payment_retry_overdue_after_days: int = 0,
    billing_payment_retry_repeat_after_hours: int = 24,
    billing_payment_retry_max_attempts: int = 3,
    billing_payment_retry_provider: str = "billing_provider",
    dry_run_billing_payment_retries: bool = False,
    billing_recurring_invoice_limit: int | None = None,
    billing_recurring_invoice_bill_on: date | None = None,
    billing_recurring_invoice_due_in_days: int = 14,
    billing_recurring_invoice_prefix: str = "SAAS",
    dry_run_billing_recurring_invoices: bool = False,
    communication_digest_limit: int | None = None,
    communication_digest_frequency: NotificationFrequency | None = None,
    communication_escalation_limit: int | None = None,
    communication_escalation_unresolved_after_minutes: int = 15,
    communication_escalation_repeat_after_minutes: int = 60,
    communication_escalation_level: int = 2,
    communication_escalation_failed_only: bool = False,
    communication_escalation_channel: CommunicationChannel | None = None,
    dry_run_communication_escalations: bool = False,
    communication_scheduled_dispatch_limit: int | None = None,
    dry_run_communication_scheduled_dispatch: bool = False,
    coach_education_renewal_reminder_limit: int | None = None,
    coach_education_renewal_reminder_as_of: date | None = None,
    coach_education_renewal_reminder_horizon_days: int = 45,
    coach_education_renewal_reminder_repeat_after_days: int = 14,
    coach_education_renewal_reminder_channel: CommunicationChannel = CommunicationChannel.EMAIL,
    dry_run_coach_education_renewal_reminders: bool = False,
    commercial_grant_alert_limit: int | None = None,
    dry_run_commercial_grant_alerts: bool = False,
    compliance_reconciliation_limit: int | None = None,
    compliance_credential_renewal_reminder_limit: int | None = None,
    compliance_credential_renewal_reminder_as_of: date | None = None,
    compliance_credential_renewal_reminder_horizon_days: int = 60,
    compliance_credential_renewal_reminder_repeat_after_days: int = 14,
    compliance_credential_renewal_reminder_channel: CommunicationChannel = CommunicationChannel.EMAIL,
    dry_run_compliance_credential_renewal_reminders: bool = False,
    webhook_limit: int | None = None,
    emergency_escalation_limit: int | None = None,
    emergency_escalation_unresolved_after_minutes: int = 15,
    emergency_escalation_repeat_after_minutes: int = 15,
    dry_run_emergency_escalations: bool = False,
    event_travel_consent_reminder_limit: int | None = None,
    event_travel_consent_reminder_due_within_hours: int = 48,
    event_travel_consent_reminder_repeat_after_hours: int = 24,
    event_travel_consent_reminder_channel: CommunicationChannel = CommunicationChannel.EMAIL,
    dry_run_event_travel_consent_reminders: bool = False,
    family_portal_invite_reminder_limit: int | None = None,
    family_coordination_digest_limit: int | None = None,
    family_coordination_digest_repeat_after_hours: int = 24,
    family_coordination_digest_channel: CommunicationChannel = CommunicationChannel.IN_APP,
    family_coordination_digest_portal_url: str = "https://afrolete.lindela.io/family",
    dry_run_family_coordination_digests: bool = False,
    family_portal_invite_reminder_invited_before_hours: int = 24,
    family_portal_invite_reminder_repeat_after_hours: int = 24,
    family_portal_invite_reminder_channel: CommunicationChannel = CommunicationChannel.EMAIL,
    dry_run_family_portal_invite_reminders: bool = False,
    insurance_renewal_reminder_limit: int | None = None,
    insurance_renewal_reminder_as_of: date | None = None,
    insurance_renewal_reminder_horizon_days: int = 120,
    insurance_renewal_reminder_repeat_after_days: int = 14,
    insurance_renewal_reminder_channel: CommunicationChannel = CommunicationChannel.EMAIL,
    dry_run_insurance_renewal_reminders: bool = False,
    member_dues_charge_limit: int | None = None,
    member_dues_charge_on: date | None = None,
    dry_run_member_dues_charges: bool = False,
    member_dues_reminder_limit: int | None = None,
    member_dues_reminder_as_of: date | None = None,
    member_dues_reminder_due_within_days: int = 7,
    member_dues_reminder_repeat_after_days: int = 7,
    member_dues_reminder_channel: CommunicationChannel = CommunicationChannel.EMAIL,
    dry_run_member_dues_reminders: bool = False,
    volunteer_reminder_limit: int | None = None,
    volunteer_reminder_due_within_days: int = 7,
    volunteer_reminder_repeat_after_hours: int = 24,
    volunteer_reminder_channel: CommunicationChannel = CommunicationChannel.EMAIL,
    dry_run_volunteer_reminders: bool = False,
    object_storage_lifecycle_retention_days: int | None = None,
    dry_run_object_storage_lifecycle: bool = False,
    performance_limit: int | None = None,
    performance_forecast_validation_limit: int | None = None,
    performance_highlight_reel_reminder_limit: int | None = None,
    performance_highlight_reel_reminder_shared_before_hours: int = 24,
    performance_highlight_reel_reminder_repeat_after_hours: int = 24,
    performance_highlight_reel_reminder_channel: CommunicationChannel = CommunicationChannel.IN_APP,
    dry_run_performance_highlight_reel_reminders: bool = False,
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
    performance_video_pose_limit: int | None = None,
    performance_video_pose_video_asset_id: UUID | None = None,
    performance_video_pose_max_frames: int | None = None,
    performance_video_pose_sample_every_seconds: float | None = None,
    performance_video_pose_api_base_url: str | None = None,
    performance_video_pose_request_headers: dict[str, str] | None = None,
    performance_video_pose_api_timeout_seconds: float = 30.0,
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
    if "billing-dunning" in active_lanes:
        results["billing_dunning"] = (
            await run_dunning_worker(
                db,
                organization_id=organization_id,
                overdue_as_of=billing_dunning_overdue_as_of,
                overdue_after_days=billing_dunning_overdue_after_days,
                repeat_after_days=billing_dunning_repeat_after_days,
                limit=billing_dunning_limit or limit,
                dry_run=dry_run_billing_dunning,
            )
        ).model_dump(mode="json")
    if "billing-late-fees" in active_lanes:
        results["billing_late_fees"] = (
            await run_late_fee_worker(
                db,
                organization_id=organization_id,
                apply_on=billing_late_fee_apply_on,
                overdue_after_days=billing_late_fee_overdue_after_days,
                repeat_after_days=billing_late_fee_repeat_after_days,
                fixed_fee=billing_late_fee_fixed_fee,
                percentage_rate=billing_late_fee_percentage_rate,
                max_fee=billing_late_fee_max_fee,
                limit=billing_late_fee_limit or limit,
                dry_run=dry_run_billing_late_fees,
            )
        ).model_dump(mode="json")
    if "billing-payment-retries" in active_lanes:
        results["billing_payment_retries"] = (
            await run_payment_retry_worker(
                db,
                organization_id=organization_id,
                retry_at=billing_payment_retry_at,
                overdue_after_days=billing_payment_retry_overdue_after_days,
                repeat_after_hours=billing_payment_retry_repeat_after_hours,
                max_attempts=billing_payment_retry_max_attempts,
                provider=billing_payment_retry_provider,
                limit=billing_payment_retry_limit or limit,
                dry_run=dry_run_billing_payment_retries,
            )
        ).model_dump(mode="json")
    if "billing-recurring-invoices" in active_lanes:
        results["billing_recurring_invoices"] = (
            await run_recurring_invoice_worker(
                db,
                organization_id=organization_id,
                bill_on=billing_recurring_invoice_bill_on,
                due_in_days=billing_recurring_invoice_due_in_days,
                limit=billing_recurring_invoice_limit or limit,
                dry_run=dry_run_billing_recurring_invoices,
                invoice_prefix=billing_recurring_invoice_prefix,
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
    if "communication-escalations" in active_lanes:
        results["communication_escalations"] = (
            await run_message_escalation_worker(
                db,
                organization_id=organization_id,
                channel=communication_escalation_channel,
                escalation_level=communication_escalation_level,
                failed_only=communication_escalation_failed_only,
                unresolved_after_minutes=communication_escalation_unresolved_after_minutes,
                repeat_after_minutes=communication_escalation_repeat_after_minutes,
                limit=communication_escalation_limit or limit,
                dry_run=dry_run_communication_escalations,
            )
        ).model_dump(mode="json")
    if "communication-scheduled-dispatch" in active_lanes:
        results["communication_scheduled_dispatch"] = (
            await run_scheduled_message_dispatch_worker(
                db,
                organization_id=organization_id,
                limit=communication_scheduled_dispatch_limit or limit,
                dry_run=dry_run_communication_scheduled_dispatch,
            )
        ).model_dump(mode="json")
    if "coach-education-renewal-reminders" in active_lanes:
        results["coach_education_renewal_reminders"] = (
            await run_coach_education_renewal_reminder_worker(
                db,
                organization_id=organization_id,
                channel=coach_education_renewal_reminder_channel,
                as_of=coach_education_renewal_reminder_as_of,
                horizon_days=coach_education_renewal_reminder_horizon_days,
                repeat_after_days=coach_education_renewal_reminder_repeat_after_days,
                limit=coach_education_renewal_reminder_limit or limit,
                dry_run=dry_run_coach_education_renewal_reminders,
            )
        ).model_dump(mode="json")
    if "commercial-grant-alerts" in active_lanes:
        results["commercial_grant_alerts"] = (
            await run_grant_saved_search_alert_worker(
                db,
                organization_id=organization_id,
                limit=commercial_grant_alert_limit or limit,
                dry_run=dry_run_commercial_grant_alerts,
            )
        ).model_dump(mode="json")
    if "compliance-reconciliation" in active_lanes:
        results["compliance_reconciliation"] = (
            await run_compliance_reconciliation_worker(
                db,
                organization_id=organization_id,
                limit=compliance_reconciliation_limit or limit,
            )
        ).model_dump(mode="json")
    if "compliance-credential-renewal-reminders" in active_lanes:
        results["compliance_credential_renewal_reminders"] = (
            await run_compliance_credential_renewal_reminder_worker(
                db,
                organization_id=organization_id,
                channel=compliance_credential_renewal_reminder_channel,
                as_of=compliance_credential_renewal_reminder_as_of,
                horizon_days=compliance_credential_renewal_reminder_horizon_days,
                repeat_after_days=compliance_credential_renewal_reminder_repeat_after_days,
                limit=compliance_credential_renewal_reminder_limit or limit,
                dry_run=dry_run_compliance_credential_renewal_reminders,
            )
        ).model_dump(mode="json")
    if "event-travel-consent-reminders" in active_lanes:
        results["event_travel_consent_reminders"] = (
            await run_event_travel_consent_reminder_worker(
                db,
                organization_id=organization_id,
                channel=event_travel_consent_reminder_channel,
                due_within_hours=event_travel_consent_reminder_due_within_hours,
                repeat_after_hours=event_travel_consent_reminder_repeat_after_hours,
                limit=event_travel_consent_reminder_limit or limit,
                dry_run=dry_run_event_travel_consent_reminders,
            )
        ).model_dump(mode="json")
    if "family-portal-invite-reminders" in active_lanes:
        results["family_portal_invite_reminders"] = (
            await run_guardian_portal_invite_reminder_worker(
                db,
                organization_id=organization_id,
                channel=family_portal_invite_reminder_channel,
                invited_before_hours=family_portal_invite_reminder_invited_before_hours,
                repeat_after_hours=family_portal_invite_reminder_repeat_after_hours,
                limit=family_portal_invite_reminder_limit or limit,
                dry_run=dry_run_family_portal_invite_reminders,
            )
        ).model_dump(mode="json")
    if "family-coordination-digests" in active_lanes:
        results["family_coordination_digests"] = (
            await run_family_coordination_digest_worker(
                db,
                organization_id=organization_id,
                channel=family_coordination_digest_channel,
                portal_url=family_coordination_digest_portal_url,
                repeat_after_hours=family_coordination_digest_repeat_after_hours,
                limit=family_coordination_digest_limit or limit,
                dry_run=dry_run_family_coordination_digests,
            )
        ).model_dump(mode="json")
    if "insurance-renewal-reminders" in active_lanes:
        results["insurance_renewal_reminders"] = (
            await run_insurance_policy_renewal_reminder_worker(
                db,
                organization_id=organization_id,
                channel=insurance_renewal_reminder_channel,
                as_of=insurance_renewal_reminder_as_of,
                horizon_days=insurance_renewal_reminder_horizon_days,
                repeat_after_days=insurance_renewal_reminder_repeat_after_days,
                limit=insurance_renewal_reminder_limit or limit,
                dry_run=dry_run_insurance_renewal_reminders,
            )
        ).model_dump(mode="json")
    if "member-dues-charges" in active_lanes:
        results["member_dues_charges"] = (
            await run_member_subscription_charge_worker(
                db,
                organization_id=organization_id,
                charge_on=member_dues_charge_on,
                limit=member_dues_charge_limit or limit,
                dry_run=dry_run_member_dues_charges,
            )
        ).model_dump(mode="json")
    if "member-dues-reminders" in active_lanes:
        results["member_dues_reminders"] = (
            await run_member_subscription_reminder_worker(
                db,
                organization_id=organization_id,
                channel=member_dues_reminder_channel,
                as_of=member_dues_reminder_as_of,
                due_within_days=member_dues_reminder_due_within_days,
                repeat_after_days=member_dues_reminder_repeat_after_days,
                limit=member_dues_reminder_limit or limit,
                dry_run=dry_run_member_dues_reminders,
            )
        ).model_dump(mode="json")
    if "volunteer-reminders" in active_lanes:
        results["volunteer_reminders"] = (
            await run_volunteer_reminder_worker(
                db,
                organization_id=organization_id,
                channel=volunteer_reminder_channel,
                due_within_days=volunteer_reminder_due_within_days,
                repeat_after_hours=volunteer_reminder_repeat_after_hours,
                limit=volunteer_reminder_limit or limit,
                dry_run=dry_run_volunteer_reminders,
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
    if "object-storage-lifecycle" in active_lanes:
        results["object_storage_lifecycle"] = run_object_storage_lifecycle(
            retention_days=object_storage_lifecycle_retention_days,
            dry_run=dry_run_object_storage_lifecycle,
        )
    if "emergency-escalations" in active_lanes:
        results["emergency_escalations"] = (
            await run_emergency_escalation_timer_worker(
                db,
                organization_id=organization_id,
                unresolved_after_minutes=emergency_escalation_unresolved_after_minutes,
                repeat_after_minutes=emergency_escalation_repeat_after_minutes,
                limit=emergency_escalation_limit or limit,
                dry_run=dry_run_emergency_escalations,
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
    if "performance-highlight-reel-reminders" in active_lanes:
        results["performance_highlight_reel_reminders"] = (
            await run_performance_highlight_reel_reminder_worker(
                db,
                organization_id=organization_id,
                channel=performance_highlight_reel_reminder_channel,
                shared_before_hours=performance_highlight_reel_reminder_shared_before_hours,
                repeat_after_hours=performance_highlight_reel_reminder_repeat_after_hours,
                limit=performance_highlight_reel_reminder_limit or performance_limit or limit,
                dry_run=dry_run_performance_highlight_reel_reminders,
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
    if "performance-video-pose" in active_lanes:
        if performance_video_pose_api_base_url:
            results["performance_video_pose"] = await run_performance_video_pose_endpoint_worker(
                db,
                api_base_url=performance_video_pose_api_base_url,
                organization_id=organization_id,
                video_asset_id=performance_video_pose_video_asset_id,
                limit=performance_video_pose_limit or performance_limit or limit,
                max_frames=performance_video_pose_max_frames,
                sample_every_seconds=performance_video_pose_sample_every_seconds,
                request_headers=performance_video_pose_request_headers,
                timeout_seconds=performance_video_pose_api_timeout_seconds,
            )
        else:
            results["performance_video_pose"] = await run_performance_video_pose_worker(
                db,
                organization_id=organization_id,
                video_asset_id=performance_video_pose_video_asset_id,
                limit=performance_video_pose_limit or performance_limit or limit,
                max_frames=performance_video_pose_max_frames,
                sample_every_seconds=performance_video_pose_sample_every_seconds,
            )
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
            or result.get("dispatched_count")
            or result.get("alerted_count")
            or result.get("invoiced_count")
            or result.get("charged_count")
            or result.get("fee_count")
            or result.get("retry_count")
            or result.get("notice_count")
            or result.get("reminded_count")
            or result.get("retried_count")
            or result.get("processed_count")
            or 0
        )
        summary["skipped_count"] += int(result.get("skipped_count") or 0)
        summary["failed_count"] += int(result.get("failed_count") or 0) + int(
            result.get("alert_failed_count") or 0
        )
    return summary


async def run() -> None:
    args = parse_args()
    settings = get_settings()
    async with SessionLocal() as db:
        result = await run_due_workers(
            db,
            organization_id=args.organization_id,
            lanes=args.lane or ("all",),
            limit=args.limit,
            agent_limit=args.agent_limit,
            billing_dunning_limit=args.billing_dunning_limit,
            billing_dunning_overdue_as_of=args.billing_dunning_overdue_as_of,
            billing_dunning_overdue_after_days=args.billing_dunning_overdue_after_days,
            billing_dunning_repeat_after_days=args.billing_dunning_repeat_after_days,
            dry_run_billing_dunning=args.dry_run_billing_dunning,
            billing_late_fee_limit=args.billing_late_fee_limit,
            billing_late_fee_apply_on=args.billing_late_fee_apply_on,
            billing_late_fee_overdue_after_days=args.billing_late_fee_overdue_after_days,
            billing_late_fee_repeat_after_days=args.billing_late_fee_repeat_after_days,
            billing_late_fee_fixed_fee=args.billing_late_fee_fixed_fee,
            billing_late_fee_percentage_rate=args.billing_late_fee_percentage_rate,
            billing_late_fee_max_fee=args.billing_late_fee_max_fee,
            dry_run_billing_late_fees=args.dry_run_billing_late_fees,
            billing_payment_retry_limit=args.billing_payment_retry_limit,
            billing_payment_retry_at=args.billing_payment_retry_at,
            billing_payment_retry_overdue_after_days=args.billing_payment_retry_overdue_after_days,
            billing_payment_retry_repeat_after_hours=args.billing_payment_retry_repeat_after_hours,
            billing_payment_retry_max_attempts=args.billing_payment_retry_max_attempts,
            billing_payment_retry_provider=args.billing_payment_retry_provider,
            dry_run_billing_payment_retries=args.dry_run_billing_payment_retries,
            billing_recurring_invoice_limit=args.billing_recurring_invoice_limit,
            billing_recurring_invoice_bill_on=args.billing_recurring_invoice_bill_on,
            billing_recurring_invoice_due_in_days=args.billing_recurring_invoice_due_in_days,
            billing_recurring_invoice_prefix=args.billing_recurring_invoice_prefix,
            dry_run_billing_recurring_invoices=args.dry_run_billing_recurring_invoices,
            communication_digest_limit=args.communication_digest_limit,
            communication_digest_frequency=NotificationFrequency(args.communication_digest_frequency)
            if args.communication_digest_frequency
            else None,
            communication_escalation_limit=args.communication_escalation_limit,
            communication_escalation_unresolved_after_minutes=args.communication_escalation_unresolved_after_minutes,
            communication_escalation_repeat_after_minutes=args.communication_escalation_repeat_after_minutes,
            communication_escalation_level=args.communication_escalation_level,
            communication_escalation_failed_only=args.communication_escalation_failed_only,
            communication_escalation_channel=CommunicationChannel(args.communication_escalation_channel)
            if args.communication_escalation_channel
            else None,
            dry_run_communication_escalations=args.dry_run_communication_escalations,
            communication_scheduled_dispatch_limit=args.communication_scheduled_dispatch_limit,
            dry_run_communication_scheduled_dispatch=args.dry_run_communication_scheduled_dispatch,
            coach_education_renewal_reminder_limit=args.coach_education_renewal_reminder_limit,
            coach_education_renewal_reminder_as_of=args.coach_education_renewal_reminder_as_of,
            coach_education_renewal_reminder_horizon_days=args.coach_education_renewal_reminder_horizon_days,
            coach_education_renewal_reminder_repeat_after_days=args.coach_education_renewal_reminder_repeat_after_days,
            coach_education_renewal_reminder_channel=CommunicationChannel(
                args.coach_education_renewal_reminder_channel
            ),
            dry_run_coach_education_renewal_reminders=args.dry_run_coach_education_renewal_reminders,
            commercial_grant_alert_limit=args.commercial_grant_alert_limit,
            dry_run_commercial_grant_alerts=args.dry_run_commercial_grant_alerts,
            compliance_reconciliation_limit=args.compliance_reconciliation_limit,
            compliance_credential_renewal_reminder_limit=args.compliance_credential_renewal_reminder_limit,
            compliance_credential_renewal_reminder_as_of=args.compliance_credential_renewal_reminder_as_of,
            compliance_credential_renewal_reminder_horizon_days=args.compliance_credential_renewal_reminder_horizon_days,
            compliance_credential_renewal_reminder_repeat_after_days=args.compliance_credential_renewal_reminder_repeat_after_days,
            compliance_credential_renewal_reminder_channel=CommunicationChannel(
                args.compliance_credential_renewal_reminder_channel
            ),
            dry_run_compliance_credential_renewal_reminders=args.dry_run_compliance_credential_renewal_reminders,
            webhook_limit=args.webhook_limit,
            emergency_escalation_limit=args.emergency_escalation_limit,
            emergency_escalation_unresolved_after_minutes=args.emergency_escalation_unresolved_after_minutes,
            emergency_escalation_repeat_after_minutes=args.emergency_escalation_repeat_after_minutes,
            dry_run_emergency_escalations=args.dry_run_emergency_escalations,
            event_travel_consent_reminder_limit=args.event_travel_consent_reminder_limit,
            event_travel_consent_reminder_due_within_hours=args.event_travel_consent_reminder_due_within_hours,
            event_travel_consent_reminder_repeat_after_hours=args.event_travel_consent_reminder_repeat_after_hours,
            event_travel_consent_reminder_channel=CommunicationChannel(
                args.event_travel_consent_reminder_channel
            ),
            dry_run_event_travel_consent_reminders=args.dry_run_event_travel_consent_reminders,
            family_coordination_digest_limit=args.family_coordination_digest_limit,
            family_coordination_digest_repeat_after_hours=args.family_coordination_digest_repeat_after_hours,
            family_coordination_digest_channel=CommunicationChannel(
                args.family_coordination_digest_channel
            ),
            family_coordination_digest_portal_url=args.family_coordination_digest_portal_url,
            dry_run_family_coordination_digests=args.dry_run_family_coordination_digests,
            family_portal_invite_reminder_limit=args.family_portal_invite_reminder_limit,
            family_portal_invite_reminder_invited_before_hours=args.family_portal_invite_reminder_invited_before_hours,
            family_portal_invite_reminder_repeat_after_hours=args.family_portal_invite_reminder_repeat_after_hours,
            family_portal_invite_reminder_channel=CommunicationChannel(
                args.family_portal_invite_reminder_channel
            ),
            dry_run_family_portal_invite_reminders=args.dry_run_family_portal_invite_reminders,
            insurance_renewal_reminder_limit=args.insurance_renewal_reminder_limit,
            insurance_renewal_reminder_as_of=args.insurance_renewal_reminder_as_of,
            insurance_renewal_reminder_horizon_days=args.insurance_renewal_reminder_horizon_days,
            insurance_renewal_reminder_repeat_after_days=args.insurance_renewal_reminder_repeat_after_days,
            insurance_renewal_reminder_channel=CommunicationChannel(
                args.insurance_renewal_reminder_channel
            ),
            dry_run_insurance_renewal_reminders=args.dry_run_insurance_renewal_reminders,
            member_dues_charge_limit=args.member_dues_charge_limit,
            member_dues_charge_on=args.member_dues_charge_on,
            dry_run_member_dues_charges=args.dry_run_member_dues_charges,
            member_dues_reminder_limit=args.member_dues_reminder_limit,
            member_dues_reminder_as_of=args.member_dues_reminder_as_of,
            member_dues_reminder_due_within_days=args.member_dues_reminder_due_within_days,
            member_dues_reminder_repeat_after_days=args.member_dues_reminder_repeat_after_days,
            member_dues_reminder_channel=CommunicationChannel(args.member_dues_reminder_channel),
            dry_run_member_dues_reminders=args.dry_run_member_dues_reminders,
            volunteer_reminder_limit=args.volunteer_reminder_limit,
            volunteer_reminder_due_within_days=args.volunteer_reminder_due_within_days,
            volunteer_reminder_repeat_after_hours=args.volunteer_reminder_repeat_after_hours,
            volunteer_reminder_channel=CommunicationChannel(args.volunteer_reminder_channel),
            dry_run_volunteer_reminders=args.dry_run_volunteer_reminders,
            object_storage_lifecycle_retention_days=args.object_storage_lifecycle_retention_days,
            dry_run_object_storage_lifecycle=args.dry_run_object_storage_lifecycle,
            performance_limit=args.performance_limit,
            performance_forecast_validation_limit=args.performance_forecast_validation_limit,
            performance_highlight_reel_reminder_limit=args.performance_highlight_reel_reminder_limit,
            performance_highlight_reel_reminder_shared_before_hours=(
                args.performance_highlight_reel_reminder_shared_before_hours
            ),
            performance_highlight_reel_reminder_repeat_after_hours=(
                args.performance_highlight_reel_reminder_repeat_after_hours
            ),
            performance_highlight_reel_reminder_channel=CommunicationChannel(
                args.performance_highlight_reel_reminder_channel
            ),
            dry_run_performance_highlight_reel_reminders=args.dry_run_performance_highlight_reel_reminders,
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
            performance_video_pose_limit=args.performance_video_pose_limit,
            performance_video_pose_video_asset_id=args.performance_video_pose_video_asset_id,
            performance_video_pose_max_frames=args.performance_video_pose_max_frames,
            performance_video_pose_sample_every_seconds=args.performance_video_pose_sample_every_seconds,
            performance_video_pose_api_base_url=(
                args.performance_video_pose_api_base_url
                or settings.performance_pose_worker_api_base_url
                or None
            ),
            performance_video_pose_request_headers=performance_video_pose_request_headers(args, settings),
            performance_video_pose_api_timeout_seconds=(
                args.performance_video_pose_api_timeout
                or settings.performance_pose_worker_api_timeout_seconds
            ),
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


def date_from_isoformat(value: str) -> date:
    return date.fromisoformat(value)


def datetime_from_isoformat(value: str) -> datetime:
    return datetime.fromisoformat(value)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
