import argparse
import asyncio
import hashlib
import json
from collections.abc import Mapping
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from app.db.session import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.performance import PerformanceVideoAsset
from app.services.performance import (
    extract_pose_samples_from_video_content,
    performance_video_object_key,
    run_performance_video_pose_worker,
)
from app.services.storage.objects import get_object


class PoseSampleEndpointPostError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract pose landmarks from stored performance videos.")
    parser.add_argument("--organization-id", type=UUID, default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--sample-every-seconds", type=float, default=None)
    parser.add_argument(
        "--api-base-url",
        default=None,
        help="When provided, post extracted keypoints to this backend API instead of storing in-process.",
    )
    parser.add_argument("--bearer-token", default=None, help="Bearer token for Keycloak-mode API ingestion.")
    parser.add_argument("--local-auth-sub", default=None, help="Local-mode X-Afrolete-Sub header.")
    parser.add_argument("--local-auth-email", default=None, help="Local-mode X-Afrolete-Email header.")
    parser.add_argument("--local-auth-name", default=None, help="Local-mode X-Afrolete-Name header.")
    parser.add_argument(
        "--api-header",
        action="append",
        default=None,
        help="Additional API header in 'Name: value' form. Can be repeated.",
    )
    parser.add_argument("--api-timeout", type=float, default=30.0)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def worker_api_headers(args: argparse.Namespace) -> dict[str, str]:
    headers: dict[str, str] = {}
    if args.bearer_token:
        headers["Authorization"] = f"Bearer {args.bearer_token}"
    if args.local_auth_sub:
        headers["X-Afrolete-Sub"] = args.local_auth_sub
    if args.local_auth_email:
        headers["X-Afrolete-Email"] = args.local_auth_email
    if args.local_auth_name:
        headers["X-Afrolete-Name"] = args.local_auth_name
    for raw_header in args.api_header or []:
        name, separator, value = raw_header.partition(":")
        if not separator or not name.strip() or not value.strip():
            raise ValueError("--api-header must use 'Name: value' format")
        headers[name.strip()] = value.strip()
    return headers


async def post_pose_samples_to_endpoint(
    *,
    api_base_url: str,
    video_asset_id: UUID,
    organization_id: UUID,
    samples: list[dict[str, object]],
    replace_existing: bool,
    request_headers: Mapping[str, str],
    timeout_seconds: float = 30.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, object]:
    endpoint = f"/api/v1/performance/videos/{video_asset_id}/pose-samples"
    payload = {
        "organization_id": str(organization_id),
        "replace_existing": replace_existing,
        "samples": samples,
    }
    async with httpx.AsyncClient(
        base_url=api_base_url.rstrip("/"),
        timeout=timeout_seconds,
        transport=transport,
    ) as client:
        response = await client.post(endpoint, json=payload, headers=dict(request_headers))
    if not 200 <= response.status_code < 300:
        raise PoseSampleEndpointPostError(
            f"Pose sample endpoint returned {response.status_code}: {response.text[:300]}"
        )
    return response.json()


async def run_performance_video_pose_endpoint_worker(
    db: AsyncSession,
    *,
    api_base_url: str,
    organization_id: UUID | None = None,
    limit: int = 10,
    max_frames: int | None = None,
    sample_every_seconds: float | None = None,
    replace_existing: bool = True,
    request_headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 30.0,
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    statement = select(PerformanceVideoAsset).where(
        PerformanceVideoAsset.status.in_(["uploaded", "pose_failed", "pose_no_subject"])
    )
    if organization_id is not None:
        statement = statement.where(PerformanceVideoAsset.organization_id == organization_id)
    videos = list((await db.scalars(statement.order_by(PerformanceVideoAsset.created_at.asc()).limit(limit))).all())
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    results: list[dict[str, object]] = []
    for video_asset in videos:
        try:
            content = get_object(
                selected_settings,
                local_root=selected_settings.performance_video_file_dir,
                key=performance_video_object_key(video_asset, selected_settings),
            )
            if hashlib.sha256(content).hexdigest() != video_asset.checksum:
                raise PoseSampleEndpointPostError("Stored video checksum mismatch")
            extracted = extract_pose_samples_from_video_content(
                content,
                max_frames=max_frames or selected_settings.performance_pose_worker_max_frames,
                sample_every_seconds=(
                    sample_every_seconds
                    or selected_settings.performance_pose_worker_sample_every_seconds
                ),
                min_detection_confidence=selected_settings.performance_pose_worker_min_detection_confidence,
            )
            samples = list(extracted["samples"])
            endpoint_response: dict[str, object] | None = None
            if samples:
                endpoint_response = await post_pose_samples_to_endpoint(
                    api_base_url=api_base_url,
                    video_asset_id=video_asset.id,
                    organization_id=video_asset.organization_id,
                    samples=samples,
                    replace_existing=replace_existing,
                    request_headers=request_headers or {},
                    timeout_seconds=timeout_seconds,
                    transport=transport,
                )
                video_asset.status = "pose_sampled"
                processed_count += 1
            else:
                video_asset.status = "pose_no_subject"
                skipped_count += 1
            video_asset.frame_rate = video_asset.frame_rate or extracted.get("frame_rate")
            video_asset.duration_seconds = video_asset.duration_seconds or extracted.get("duration_seconds")
            video_asset.pose_analysis_json = json.dumps(
                {
                    "worker": "endpoint_video_pose",
                    "source_provider": extracted["source_provider"],
                    "model_policy": extracted["model_policy"],
                    "decoded_frame_count": extracted["decoded_frame_count"],
                    "processed_frame_count": extracted["processed_frame_count"],
                    "posted_sample_count": len(samples),
                    "endpoint_sample_count": endpoint_response.get("sample_count") if endpoint_response else 0,
                    "warnings": extracted["warnings"],
                }
            )
            await db.commit()
            await db.refresh(video_asset)
            results.append(
                {
                    "video_asset_id": str(video_asset.id),
                    "status": video_asset.status,
                    "sample_count": len(samples),
                    "processed_frame_count": extracted["processed_frame_count"],
                    "decoded_frame_count": extracted["decoded_frame_count"],
                    "warning_count": len(extracted["warnings"]),
                    "ingest_endpoint": f"/api/v1/performance/videos/{video_asset.id}/pose-samples",
                }
            )
        except HTTPException as exc:
            await db.rollback()
            video_asset.status = "pose_failed"
            video_asset.pose_analysis_json = json.dumps({"worker": "endpoint_video_pose", "error": exc.detail})
            await db.commit()
            failed_count += 1
            results.append({"video_asset_id": str(video_asset.id), "status": "pose_failed", "error": str(exc.detail)})
        except Exception as exc:
            await db.rollback()
            video_asset.status = "pose_failed"
            video_asset.pose_analysis_json = json.dumps({"worker": "endpoint_video_pose", "error": str(exc)})
            await db.commit()
            failed_count += 1
            results.append({"video_asset_id": str(video_asset.id), "status": "pose_failed", "error": str(exc)})
    return {
        "organization_id": str(organization_id) if organization_id else None,
        "eligible_count": len(videos),
        "processed_count": processed_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "ingest_mode": "api_endpoint",
        "results": results,
    }


async def run() -> None:
    args = parse_args()
    async with SessionLocal() as db:
        if args.api_base_url:
            result = await run_performance_video_pose_endpoint_worker(
                db,
                api_base_url=args.api_base_url,
                organization_id=args.organization_id,
                limit=args.limit,
                max_frames=args.max_frames,
                sample_every_seconds=args.sample_every_seconds,
                request_headers=worker_api_headers(args),
                timeout_seconds=args.api_timeout,
            )
        else:
            result = await run_performance_video_pose_worker(
                db,
                organization_id=args.organization_id,
                limit=args.limit,
                max_frames=args.max_frames,
                sample_every_seconds=args.sample_every_seconds,
            )
    print(json.dumps(result, indent=2 if args.pretty else None))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
