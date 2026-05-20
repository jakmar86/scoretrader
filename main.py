"""
ScoreTrader -- Main Orchestrator
Entry point for the pre-match pipeline.

Usage:
    python main.py
    python main.py --date 2025-08-17
"""

import argparse
import datetime
from config.config import config
from src.logger import initialise_db


def run(match_date: str = None):
    if match_date is None:
        match_date = datetime.date.today().isoformat()

    print(f"\nScoreTrader -- {match_date}")
    print("=" * 50)

    initialise_db()

    # Phase 1A: data pipeline -> poisson model -> odds fetch -> value engine
    # Phase 1B: bet placement -> inplay monitor

    print("\nPipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ScoreTrader")
    parser.add_argument("--date", type=str, default=None)
    args = parser.parse_args()
    run(args.date)
