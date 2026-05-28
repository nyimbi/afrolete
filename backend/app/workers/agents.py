import argparse
import asyncio
import json
from uuid import UUID

from app.db.session import SessionLocal
from app.services.agents import run_agent_task_worker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute queued AfroLete agent tasks.")
    parser.add_argument("--organization-id", type=UUID, default=None)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    async with SessionLocal() as db:
        result = await run_agent_task_worker(
            db,
            organization_id=args.organization_id,
            limit=args.limit,
        )
    print(json.dumps(result.model_dump(mode="json"), indent=2 if args.pretty else None))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
