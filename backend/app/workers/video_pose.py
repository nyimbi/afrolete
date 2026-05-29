import argparse
import asyncio
import json
from uuid import UUID

from app.db.session import SessionLocal
from app.services.performance import run_performance_video_pose_worker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract pose landmarks from stored performance videos.")
    parser.add_argument("--organization-id", type=UUID, default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--sample-every-seconds", type=float, default=None)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    async with SessionLocal() as db:
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
