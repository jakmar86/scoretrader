"""
ScoreTrader -- Odds Fetcher
Fetches correct score market odds from Betfair API.
Phase 1A: Stub -- requires Betfair API credentials.
"""


def find_market(home_team: str, away_team: str):
    """Find correct score market for a fixture. Phase 1A: stub."""
    pass


def fetch_odds(market_id: str) -> dict:
    """Fetch best back odds per scoreline. Phase 1A: stub."""
    pass


def get_implied_probability(odds: float) -> float:
    if odds <= 1.0:
        return 0.0
    return 1.0 / odds
