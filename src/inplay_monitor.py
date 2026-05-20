"""
ScoreTrader -- In-Play Monitor
Polls Betfair every 30 seconds per active match.
Phase 1B: implementation target.
"""

import time
from config.config import config


def monitor_match(market_id: str, selections: list):
    """Main in-play monitoring loop. Phase 1B: stub."""
    poll_interval = config["poll_interval_seconds"]
    while True:
        # TODO: Phase 1B -- poll market, check exit engine, place lays
        time.sleep(poll_interval)
