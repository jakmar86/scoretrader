"""
ScoreTrader -- Lay Placer
Executes lay orders to green up positions. Phase 1B: implementation target.
"""


def calculate_lay_stake(back_stake: float, back_odds: float,
                        lay_odds: float, lay_pct: float = 1.0) -> float:
    return round((back_stake * back_odds) / lay_odds * lay_pct, 2)


def place_lay(selection: dict, market_id: str, lay_pct: float = 1.0) -> dict:
    """Place lay order. Phase 1B: stub."""
    pass
