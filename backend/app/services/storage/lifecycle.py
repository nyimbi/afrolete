from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import Settings, get_settings
from app.services.storage.objects import put_s3_bucket_lifecycle


@dataclass(frozen=True)
class LocalLifecycleTarget:
    label: str
    root: str


def configured_local_lifecycle_targets(settings: Settings) -> list[LocalLifecycleTarget]:
    return [
        LocalLifecycleTarget("report-artifacts", settings.report_artifact_dir),
        LocalLifecycleTarget("equipment-files", settings.equipment_file_dir),
        LocalLifecycleTarget("travel-receipts", settings.travel_receipt_file_dir),
        LocalLifecycleTarget("travel-checklist-files", settings.travel_checklist_file_dir),
        LocalLifecycleTarget("travel-manifests", settings.travel_manifest_file_dir),
        LocalLifecycleTarget("safeguarding-incident-evidence", settings.safeguarding_incident_evidence_dir),
        LocalLifecycleTarget("safeguarding-incident-artifacts", settings.safeguarding_incident_artifact_dir),
        LocalLifecycleTarget("performance-videos", settings.performance_video_file_dir),
    ]


def run_object_storage_lifecycle(
    settings: Settings | None = None,
    *,
    retention_days: int | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    selected_retention_days = max(
        int(retention_days or selected_settings.object_storage_lifecycle_retention_days),
        1,
    )
    if not selected_settings.object_storage_lifecycle_enabled:
        return {
            "mode": selected_settings.object_storage_mode,
            "enabled": False,
            "retention_days": selected_retention_days,
            "eligible_count": 0,
            "processed_count": 0,
            "deleted_count": 0,
            "skipped_count": 1,
            "failed_count": 0,
            "results": [],
            "message": "Object storage lifecycle policy is disabled.",
        }
    if selected_settings.object_storage_mode == "s3":
        if dry_run:
            return {
                "mode": "s3",
                "enabled": True,
                "retention_days": selected_retention_days,
                "eligible_count": len(selected_settings.object_storage_lifecycle_prefixes),
                "processed_count": 0,
                "deleted_count": 0,
                "skipped_count": len(selected_settings.object_storage_lifecycle_prefixes),
                "failed_count": 0,
                "results": [
                    {
                        "prefix": prefix,
                        "action": "would_configure_expiration",
                        "expiration_days": selected_retention_days,
                    }
                    for prefix in selected_settings.object_storage_lifecycle_prefixes
                ],
            }
        configured = put_s3_bucket_lifecycle(
            selected_settings,
            prefixes=selected_settings.object_storage_lifecycle_prefixes,
            expiration_days=selected_retention_days,
        )
        return {
            "mode": "s3",
            "enabled": True,
            "retention_days": selected_retention_days,
            "eligible_count": int(configured["prefix_count"]),
            "processed_count": int(configured["prefix_count"]),
            "deleted_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "results": [configured],
        }
    return run_local_object_lifecycle(
        selected_settings,
        retention_days=selected_retention_days,
        dry_run=dry_run,
    )


def run_local_object_lifecycle(
    settings: Settings,
    *,
    retention_days: int,
    dry_run: bool,
) -> dict[str, object]:
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    results: list[dict[str, object]] = []
    eligible_count = 0
    deleted_count = 0
    byte_count = 0
    for target in configured_local_lifecycle_targets(settings):
        result = prune_local_lifecycle_target(target, cutoff=cutoff, dry_run=dry_run)
        results.append(result)
        eligible_count += int(result["eligible_count"])
        deleted_count += int(result["deleted_count"])
        byte_count += int(result["deleted_bytes"])
    return {
        "mode": "local",
        "enabled": True,
        "retention_days": retention_days,
        "eligible_count": eligible_count,
        "processed_count": deleted_count if not dry_run else 0,
        "deleted_count": deleted_count,
        "deleted_bytes": byte_count,
        "skipped_count": eligible_count if dry_run else 0,
        "failed_count": 0,
        "dry_run": dry_run,
        "cutoff": cutoff.isoformat(),
        "results": results,
    }


def prune_local_lifecycle_target(
    target: LocalLifecycleTarget,
    *,
    cutoff: datetime,
    dry_run: bool,
) -> dict[str, object]:
    root = Path(target.root)
    if not root.exists():
        return {
            "target": target.label,
            "root": str(root),
            "eligible_count": 0,
            "deleted_count": 0,
            "deleted_bytes": 0,
            "status": "missing",
            "objects": [],
        }
    eligible: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, UTC)
        if modified_at >= cutoff:
            continue
        relative_path = path.relative_to(root).as_posix()
        eligible.append(
            {
                "key": relative_path,
                "size_bytes": stat.st_size,
                "modified_at": modified_at.isoformat(),
            }
        )
        if not dry_run:
            path.unlink()
    if not dry_run:
        remove_empty_directories(root)
    return {
        "target": target.label,
        "root": str(root),
        "eligible_count": len(eligible),
        "deleted_count": 0 if dry_run else len(eligible),
        "deleted_bytes": 0 if dry_run else sum(int(item["size_bytes"]) for item in eligible),
        "status": "dry_run" if dry_run else "processed",
        "objects": eligible[:25],
    }


def remove_empty_directories(root: Path) -> None:
    for path in sorted((candidate for candidate in root.rglob("*") if candidate.is_dir()), reverse=True):
        try:
            path.rmdir()
        except OSError:
            continue
