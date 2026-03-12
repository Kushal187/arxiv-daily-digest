"""Run daily ingest directly (used by GitHub Actions).

Usage:
    DATABASE_URL=... python scripts/run-ingest.py [--force]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "worker"))

from app.services.ingest import run_daily_ingest  # noqa: E402


def main() -> None:
    force = "--force" in sys.argv
    result = run_daily_ingest(force=force)
    print(json.dumps(result, indent=2, default=str))

    if result.get("status") not in ("succeeded", "skipped"):
        sys.exit(1)


if __name__ == "__main__":
    main()
