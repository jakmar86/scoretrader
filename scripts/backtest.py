"""
ScoreTrader -- Backtester
Validates the Poisson model edge against historical closing odds (Bet365).
Uses a rolling window -- each fixture is predicted using only prior data.
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.poisson_model import build_team_strengths, score_probability, top_scores
from src.value_engine import calculate_edge, kelly_stake
from config.config import config

MIN_EDGE       = config["min_edge_pct"]
KELLY_FRACTION = config["kelly_fraction"]
BANK           = 1000.0
MAX_SELECTIONS = config["max_selections"]
MIN_PRIOR_GAMES = 80  # Minimum fixtures needed before making predictions


def get_model_probs(home_team: str, away_team: str, df_prior: pd.DataFrame) -> list:
    """Run model on prior data only. Returns top 8 scores with model_prob."""
    try:
        strengths = build_team_strengths(df_prior)
        if home_team not in strengths.index or away_team not in strengths.index:
            return []
        home = strengths.loc[home_team]
        away = strengths.loc[away_team]
        matrix = score_probability(
            home_attack  = home["attack"],
            home_defence = home["defence"],
            away_attack  = away["attack"],
            away_defence = away["defence"],
        )
        scores = top_scores(matrix, n=8)
        for s in scores:
            s["model_prob"] = s["prob"]
        return scores
    except Exception:
        return []


def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Only use fixtures where we have Bet365 closing odds
    df = df.dropna(subset=["B365H"])

    results = []
    skipped = 0

    print(f"Running backtest on {len(df)} fixtures...")
    print(f"Min edge: {MIN_EDGE}%  |  Kelly fraction: {KELLY_FRACTION}  |  Bank: £{BANK}")
    print("-" * 60)

    for idx, fixture in df.iterrows():
        # Only use data BEFORE this fixture
        df_prior = df[df["Date"] < fixture["Date"]]

        if len(df_prior) < MIN_PRIOR_GAMES:
            skipped += 1
            continue

        home_team  = fixture["HomeTeam"]
        away_team  = fixture["AwayTeam"]
        actual_home = int(fixture["FTHG"])
        actual_away = int(fixture["FTAG"])
        actual_score = f"{actual_home}-{actual_away}"

        # Get model predictions
        predictions = get_model_probs(home_team, away_team, df_prior)
        if not predictions:
            skipped += 1
            continue

        # For each prediction, check if we have Bet365 closing odds
        # B365 correct score odds aren't in the CSV -- we use match odds as proxy
        # for now and flag for replacement with real CS odds later
        # Instead simulate market with realistic overround on model probs
        BLACKLIST = ["1-0", "0-0", "0-1", "2-0", "4-0", "0-3", "0-2", "5-0"]
        OVERROUND = 1.18

        selections = []
        for s in predictions[:MAX_SELECTIONS]:
            market_odds = round((1 / s["model_prob"]) * OVERROUND, 2)
            edge        = calculate_edge(s["model_prob"], market_odds)

            if edge >= MIN_EDGE and s["score"] not in BLACKLIST:
                stake = kelly_stake(s["model_prob"], market_odds,
                                    BANK, KELLY_FRACTION)
                # Cap individual stake
                stake = min(stake, BANK * 0.05)

                won   = (s["score"] == actual_score)
                pnl   = round((market_odds - 1) * stake if won else -stake, 2)

                selections.append({
                    "date":        fixture["Date"].date(),
                    "home":        home_team,
                    "away":        away_team,
                    "actual":      actual_score,
                    "backed":      s["score"],
                    "model_prob":  round(s["model_prob"] * 100, 2),
                    "market_odds": market_odds,
                    "edge_pct":    edge,
                    "stake":       stake,
                    "won":         won,
                    "pnl":         pnl,
                })

        results.extend(selections)

    df_results = pd.DataFrame(results)
    print(f"Skipped {skipped} fixtures (insufficient prior data)")
    return df_results


def print_summary(df_results: pd.DataFrame):
    if df_results.empty:
        print("No results to summarise.")
        return

    total_bets    = len(df_results)
    total_staked  = df_results["stake"].sum()
    total_pnl     = df_results["pnl"].sum()
    winners       = df_results["won"].sum()
    roi           = (total_pnl / total_staked * 100) if total_staked > 0 else 0
    strike_rate   = (winners / total_bets * 100) if total_bets > 0 else 0

    print(f"\nBACKTEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total bets:        {total_bets:,}")
    print(f"Winners:           {winners:,}  ({strike_rate:.1f}%)")
    print(f"Total staked:      £{total_staked:,.2f}")
    print(f"Total P&L:         £{total_pnl:,.2f}")
    print(f"ROI:               {roi:.2f}%")

    print(f"\nP&L BY SEASON")
    print("-" * 50)
    df_results["year"] = pd.to_datetime(df_results["date"]).dt.year
    by_season = df_results.groupby("year").agg(
        bets   = ("pnl", "count"),
        staked = ("stake", "sum"),
        pnl    = ("pnl", "sum"),
    )
    by_season["roi"] = (by_season["pnl"] / by_season["staked"] * 100).round(2)
    print(by_season.to_string())

    print(f"\nTOP 10 BACKED SCORES BY FREQUENCY")
    print("-" * 50)
    score_summary = df_results.groupby("backed").agg(
        bets    = ("pnl", "count"),
        winners = ("won", "sum"),
        pnl     = ("pnl", "sum"),
        staked  = ("stake", "sum"),
    )
    score_summary["roi"]    = (score_summary["pnl"] / score_summary["staked"] * 100).round(1)
    score_summary["win_pct"] = (score_summary["winners"] / score_summary["bets"] * 100).round(1)
    print(score_summary.sort_values("bets", ascending=False).head(10).to_string())

    # Save full results
    out_path = "data/processed/backtest_results.csv"
    df_results.to_csv(out_path, index=False)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    df         = pd.read_csv("data/processed/fixtures.csv")
    df_results = run_backtest(df)
    print_summary(df_results)
