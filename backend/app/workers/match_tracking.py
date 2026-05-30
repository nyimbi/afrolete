import argparse
import asyncio
import json
from collections.abc import Mapping
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.models.performance import OppositionScoutingVideoAsset, PerformanceMatchPitchCalibration


class MatchTrackingEndpointPostError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-track stored football match videos.")
    parser.add_argument("--organization-id", type=UUID, default=None)
    parser.add_argument("--video-asset-id", type=UUID, default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--sample-every-seconds", type=float, default=None)
    parser.add_argument("--min-detection-confidence", type=float, default=None)
    parser.add_argument(
        "--api-base-url",
        default=None,
        help="Backend API base URL used to create tracking runs from extracted samples.",
    )
    parser.add_argument("--bearer-token", default=None, help="Bearer token for Keycloak-mode API ingestion.")
    parser.add_argument("--local-auth-sub", default=None, help="Local-mode X-Afrolete-Sub header.")
    parser.add_argument("--local-auth-email", default=None, help="Local-mode X-Afrolete-Email header.")
    parser.add_argument("--local-auth-name", default=None, help="Local-mode X-Afrolete-Name header.")
    parser.add_argument("--api-header", action="append", default=None, help="Additional 'Name: value' header.")
    parser.add_argument("--api-timeout", type=float, default=None)
    parser.add_argument("--replace-existing", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def match_tracking_worker_api_headers(
    args: argparse.Namespace,
    settings: Settings | None = None,
) -> dict[str, str]:
    selected_settings = settings or get_settings()
    headers: dict[str, str] = {}
    bearer_token = args.bearer_token or selected_settings.performance_match_tracking_worker_bearer_token
    local_auth_sub = (
        args.local_auth_sub or selected_settings.performance_match_tracking_worker_local_auth_sub
    )
    local_auth_email = (
        args.local_auth_email or selected_settings.performance_match_tracking_worker_local_auth_email
    )
    local_auth_name = (
        args.local_auth_name or selected_settings.performance_match_tracking_worker_local_auth_name
    )
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if local_auth_sub:
        headers["X-Afrolete-Sub"] = local_auth_sub
    if local_auth_email:
        headers["X-Afrolete-Email"] = local_auth_email
    if local_auth_name:
        headers["X-Afrolete-Name"] = local_auth_name
    for raw_header in args.api_header or []:
        name, separator, value = raw_header.partition(":")
        if not separator or not name.strip() or not value.strip():
            raise ValueError("--api-header must use 'Name: value' format")
        headers[name.strip()] = value.strip()
    return headers


async def post_match_tracking_run_to_endpoint(
    *,
    api_base_url: str,
    video_asset: OppositionScoutingVideoAsset,
    calibration_id: UUID | None,
    max_frames: int,
    sample_every_seconds: float,
    min_detection_confidence: float,
    replace_existing: bool,
    request_headers: Mapping[str, str],
    timeout_seconds: float = 30.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, object]:
    payload = {
        "organization_id": str(video_asset.organization_id),
        "calibration_id": str(calibration_id) if calibration_id else None,
        "source_provider": "opencv_motion_tracker",
        "replace_existing": replace_existing,
        "auto_track": True,
        "max_frames": max_frames,
        "sample_every_seconds": sample_every_seconds,
        "min_detection_confidence": min_detection_confidence,
        "pitch_length_m": 105,
        "pitch_width_m": 68,
        "samples": [],
    }
    async with httpx.AsyncClient(
        base_url=api_base_url.rstrip("/"),
        timeout=timeout_seconds,
        transport=transport,
    ) as client:
        response = await client.post(
            f"/api/v1/performance/scouting/videos/{video_asset.id}/tracking-runs",
            json=payload,
            headers=dict(request_headers),
        )
    if not 200 <= response.status_code < 300:
        raise MatchTrackingEndpointPostError(
            f"Match tracking endpoint returned {response.status_code}: {response.text[:300]}"
        )
    return response.json()


async def run_opposition_match_tracking_endpoint_worker(
    db: AsyncSession,
    *,
    api_base_url: str,
    organization_id: UUID | None = None,
    video_asset_id: UUID | None = None,
    limit: int = 10,
    max_frames: int | None = None,
    sample_every_seconds: float | None = None,
    min_detection_confidence: float | None = None,
    replace_existing: bool = True,
    request_headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 30.0,
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    if selected_settings.performance_match_tracking_worker_provider == "disabled":
        return {
            "organization_id": str(organization_id) if organization_id else None,
            "eligible_count": 0,
            "processed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "ingest_mode": "api_endpoint",
            "provider_status": "disabled",
            "results": [],
        }
    statement = select(OppositionScoutingVideoAsset).where(
        OppositionScoutingVideoAsset.sport == "football",
        OppositionScoutingVideoAsset.status.in_(["uploaded", "analyzed", "tracking_failed"]),
    )
    if organization_id is not None:
        statement = statement.where(OppositionScoutingVideoAsset.organization_id == organization_id)
    if video_asset_id is not None:
        statement = statement.where(OppositionScoutingVideoAsset.id == video_asset_id)
    videos = list((await db.scalars(statement.order_by(OppositionScoutingVideoAsset.created_at.asc()).limit(limit))).all())
    processed_count = 0
    failed_count = 0
    results: list[dict[str, object]] = []
    for video_asset in videos:
        calibration = await latest_match_pitch_calibration(db, video_asset)
        try:
            tracking_run = await post_match_tracking_run_to_endpoint(
                api_base_url=api_base_url,
                video_asset=video_asset,
                calibration_id=calibration.id if calibration else None,
                max_frames=max_frames or selected_settings.performance_match_tracking_worker_max_frames,
                sample_every_seconds=(
                    sample_every_seconds
                    or selected_settings.performance_match_tracking_worker_sample_every_seconds
                ),
                min_detection_confidence=(
                    min_detection_confidence
                    if min_detection_confidence is not None
                    else selected_settings.performance_match_tracking_worker_min_detection_confidence
                ),
                replace_existing=replace_existing,
                request_headers=request_headers or {},
                timeout_seconds=timeout_seconds,
                transport=transport,
            )
            processed_count += 1
            results.append(
                {
                    "video_asset_id": str(video_asset.id),
                    "status": "tracked",
                    "tracking_run_id": tracking_run.get("id"),
                    "player_count": tracking_run.get("player_count"),
                    "sample_count": tracking_run.get("sample_count"),
                    "tracking_quality_score": tracking_run.get("tracking_quality_score"),
                    "calibration_id": str(calibration.id) if calibration else None,
                    "ingest_endpoint": f"/api/v1/performance/scouting/videos/{video_asset.id}/tracking-runs",
                }
            )
        except Exception as exc:
            video_asset.status = "tracking_failed"
            await db.commit()
            failed_count += 1
            results.append({"video_asset_id": str(video_asset.id), "status": "tracking_failed", "error": str(exc)})
    return {
        "organization_id": str(organization_id) if organization_id else None,
        "eligible_count": len(videos),
        "processed_count": processed_count,
        "failed_count": failed_count,
        "skipped_count": 0,
        "ingest_mode": "api_endpoint",
        "provider_status": selected_settings.performance_match_tracking_worker_provider,
        "results": results,
    }


async def latest_match_pitch_calibration(
    db: AsyncSession,
    video_asset: OppositionScoutingVideoAsset,
) -> PerformanceMatchPitchCalibration | None:
    return await db.scalar(
        select(PerformanceMatchPitchCalibration)
        .where(
            PerformanceMatchPitchCalibration.organization_id == video_asset.organization_id,
            PerformanceMatchPitchCalibration.video_asset_id == video_asset.id,
        )
        .order_by(PerformanceMatchPitchCalibration.created_at.desc())
        .limit(1)
    )


async def run() -> None:
    args = parse_args()
    settings = get_settings()
    api_base_url = args.api_base_url or settings.performance_match_tracking_worker_api_base_url
    if not api_base_url:
        raise SystemExit("Match tracking worker requires --api-base-url or AFROLETE_PERFORMANCE_MATCH_TRACKING_WORKER_API_BASE_URL")
    async with SessionLocal() as db:
        result = await run_opposition_match_tracking_endpoint_worker(
            db,
            api_base_url=api_base_url,
            organization_id=args.organization_id,
            video_asset_id=args.video_asset_id,
            limit=args.limit,
            max_frames=args.max_frames,
            sample_every_seconds=args.sample_every_seconds,
            min_detection_confidence=args.min_detection_confidence,
            replace_existing=args.replace_existing,
            request_headers=match_tracking_worker_api_headers(args, settings),
            timeout_seconds=(
                args.api_timeout or settings.performance_match_tracking_worker_api_timeout_seconds
            ),
            settings=settings,
        )
    print(json.dumps(result, indent=2 if args.pretty else None))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
