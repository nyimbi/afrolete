import argparse
import asyncio
import json
from uuid import UUID

from app.db.session import SessionLocal
from app.services.developer import run_developer_webhook_retry_due


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run due developer webhook retries.")
    parser.add_argument("--organization-id", type=UUID, default=None)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--include-recorded", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    async with SessionLocal() as db:
        result = await run_developer_webhook_retry_due(
            db,
            organization_id=args.organization_id,
            max_attempts=args.max_attempts,
            limit=args.limit,
            include_recorded=args.include_recorded,
        )
    print(json.dumps(result.model_dump(mode="json"), indent=2 if args.pretty else None))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
