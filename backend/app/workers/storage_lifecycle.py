import argparse
import json

from app.services.storage.lifecycle import run_object_storage_lifecycle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply AfroLete object storage lifecycle policy.")
    parser.add_argument("--retention-days", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_object_storage_lifecycle(
        retention_days=args.retention_days,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
