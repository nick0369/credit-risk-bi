"""Run from the repository root: credit-risk build."""
import argparse
import json
import logging
import os
from pathlib import Path

from credit_risk.pipeline import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        print(json.dumps(run(args.root.resolve(), args.database_url), indent=2))
    except Exception:
        logging.getLogger(__name__).exception('Pipeline failed; inspect source and validation before retrying')
        raise SystemExit(1)


if __name__ == "__main__":
    main()
