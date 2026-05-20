"""
ScoreTrader -- Backtester
Validates the Poisson model against historical closing odds.
Phase 1A: implementation target.
"""

import pandas as pd
from config.config import config


def run_backtest(fixtures: pd.DataFrame):
    """Simulate selections and P&L against historical data. Phase 1A: stub."""
    pass


if __name__ == "__main__":
    df = pd.read_csv(config["processed_data_path"] + "fixtures.csv")
    run_backtest(df)
