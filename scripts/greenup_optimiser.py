"""
ScoreTrader -- Green-Up Threshold Optimiser
Sweeps green-up profit thresholds to find the optimal value.
Uses half-time scores as goal timing proxy.

Logic:
  - If HT score matches a backed selection -> goal event simulated at ~40 mins
  - If FT score matches but not HT         -> goal event simulated at ~75 mins
  - At each goal event, check if combined position exceeds threshold
  - If yes -> green up all, lock in profit
  - If no  -> hold to full time
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.poisson_model import build_team_strengths, score_probability, top_scores
from src.value_engine import calculate_edge, kelly_stake
from config.config import config

MIN_PRIOR_GAMES = 80
KELLY_FRACTION  = config["kelly_fraction"]
BANK            = 1000.0
MAX_SELECTIONS  = config["max_selections"]
MIN_EDGE        = config["min_edge_pct"]
OVERROUND       = 1.18
BLACKLIST       = ["1-0", "0-0", "0-1", "2-0", "4-0", "0-3", "0-2", "5-0"]

# Thresholds to test: green up when combined position > X% of total stake
THRESHOLDS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00, 9999]
THRESHOLD_LABELS = ["5%", "10%", "15%", "20%", "30%", "40%", "50%", "75%", "100%", "Never"]

# Minute-based decay multipliers
# Threshold is multiplied by this based on when goal occurs
MINUTE_DECAY = {
    40: 1.0,   # HT goal -- full threshold applies
    75: 0.5,   # Late goal -- threshold halved (more urgent to green up)
}

# In-play odds model
# When a score is hit, odds shorten based on time remaining
# Simple model: odds compress toward 1.0 as time runs out
def estimate_inplay_odds(back_odds: float, minute: int) -> float:
    """
    Estimate in-play odds when backed score is hit.
    Odds compress as time remaining decreases.
    
    At minute 0:  in-play odds ~= back_odds * 0.85 (market efficient)
    At minute 45: in-play odds ~= back_odds * 0.55
    At minute 75: in-play odds ~= back_odds * 0.30
    At minute 85: in-play odds ~= back_odds * 0.18
    """
    time_remaining = 90 - minute
    # Compression factor based on time remaining
    compression = 0.10 + (time_remaining / 90) * 0.75
    raw = back_odds * compression
    # Odds can't go below 1.01
    return max(round(raw, 2), 1.01)


def calculate_green_up_value(back_stake: float, back_odds: float,
                              inplay_odds: float) -> float:
    """
    Calculate guaranteed profit from greening up now.
    green_up_profit = (back_stake * back_odds / inplay_odds) - back_stake
    """
    lay_stake = (back_stake * back_odds) / inplay_odds
    green_profit = lay_stake - back_stake
    return round(green_profit, 2)


def simulate_fixture(selections: list, ht_score: str, ft_score: str,
                     threshold: float) -> dict:
    """
    Simulate in-play trading for a single fixture.
    
    Returns dict with pnl and whether green-up was triggered.
    """
    total_staked    = sum(s["stake"] for s in selections)
    green_threshold = total_staked * threshold

    # --- Check for half-time green-up opportunity ---
    minute = 40
    decay  = MINUTE_DECAY[minute]
    adjusted_threshold = green_threshold * decay

    ht_matched = [s for s in selections if s["score"] == ht_score]

    if ht_matched:
        # Calculate combined green-up value across ALL selections
        total_greenup = 0
        for s in selections:
            if s["score"] == ht_score:
                # This selection is winning -- calculate green-up value
                inplay_odds = estimate_inplay_odds(s["market_odds"], minute)
                gu_value    = calculate_green_up_value(s["stake"], s["market_odds"], inplay_odds)
                total_greenup += gu_value
            else:
                # This selection is losing at HT -- can recover some value
                # Estimate remaining value at ~15% of stake (still 50 mins left)
                total_greenup += s["stake"] * 0.15

        if total_greenup >= adjusted_threshold:
            # Green up everything
            return {
                "pnl":         round(total_greenup, 2),
                "greened_up":  True,
                "green_minute": minute,
                "total_staked": total_staked,
            }

    # --- Check for second-half green-up opportunity ---
    minute = 75
    decay  = MINUTE_DECAY[minute]
    adjusted_threshold = green_threshold * decay

    ft_matched = [s for s in selections if s["score"] == ft_score]

    if ft_matched and ft_score != ht_score:
        total_greenup = 0
        for s in selections:
            if s["score"] == ft_score:
                inplay_odds = estimate_inplay_odds(s["market_odds"], minute)
                gu_value    = calculate_green_up_value(s["stake"], s["market_odds"], inplay_odds)
                total_greenup += gu_value
            else:
                # Late in game, losing selections worth ~5% of stake
                total_greenup += s["stake"] * 0.05

        if total_greenup >= adjusted_threshold:
            return {
                "pnl":          round(total_greenup, 2),
                "greened_up":   True,
                "green_minute": minute,
                "total_staked": total_staked,
            }

    # --- No green-up triggered -- settle at full time ---
    pnl = 0
    for s in selections:
        if s["score"] == ft_score:
            pnl += round((s["market_odds"] - 1) * s["stake"], 2)
        else:
            pnl -= s["stake"]

    return {
        "pnl":          round(pnl, 2),
        "greened_up":   False,
        "green_minute": None,
        "total_staked": total_staked,
    }


def run_optimiser(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"]  = pd.to_datetime(df["Date"])
    df          = df.sort_values("Date").reset_index(drop=True)
    df          = df.dropna(subset=["HTHG", "HTAG", "B365H"])

    # Pre-compute all fixture selections (same for every threshold)
    print("Pre-computing model predictions for all fixtures...")
    fixture_data = []
    skipped      = 0

    for idx, fixture in df.iterrows():
        df_prior = df[df["Date"] < fixture["Date"]]
        if len(df_prior) < MIN_PRIOR_GAMES:
            skipped += 1
            continue

        home_team   = fixture["HomeTeam"]
        away_team   = fixture["AwayTeam"]
        ht_score    = f"{int(fixture['HTHG'])}-{int(fixture['HTAG'])}"
        ft_score    = f"{int(fixture['FTHG'])}-{int(fixture['FTAG'])}"

        try:
            strengths = build_team_strengths(df_prior)
            if home_team not in strengths.index or away_team not in strengths.index:
                skipped += 1
                continue

            home   = strengths.loc[home_team]
            away   = strengths.loc[away_team]
            matrix = score_probability(
                home_attack  = home["attack"],
                home_defence = home["defence"],
                away_attack  = away["attack"],
                away_defence = away["defence"],
            )
            predictions = top_scores(matrix, n=8)
            for s in predictions:
                s["model_prob"] = s["prob"]

            selections = []
            for s in predictions[:MAX_SELECTIONS]:
                if s["score"] in BLACKLIST:
                    continue
                market_odds = round((1 / s["model_prob"]) * OVERROUND, 2)
                edge        = calculate_edge(s["model_prob"], market_odds)
                if edge >= MIN_EDGE:
                    stake = kelly_stake(s["model_prob"], market_odds,
                                       BANK, KELLY_FRACTION)
                    stake = min(stake, BANK * 0.05)
                    selections.append({
                        "score":       s["score"],
                        "model_prob":  s["model_prob"],
                        "market_odds": market_odds,
                        "stake":       stake,
                    })

            if selections:
                fixture_data.append({
                    "date":       fixture["Date"].date(),
                    "home":       home_team,
                    "away":       away_team,
                    "ht_score":   ht_score,
                    "ft_score":   ft_score,
                    "selections": selections,
                })

        except Exception:
            skipped += 1
            continue

    print(f"Fixtures with selections: {len(fixture_data)} (skipped {skipped})")
    print(f"\nSweeping {len(THRESHOLDS)} thresholds...\n")

    # Now sweep thresholds
    summary_rows = []

    for threshold, label in zip(THRESHOLDS, THRESHOLD_LABELS):
        total_pnl        = 0
        total_staked     = 0
        total_greenups   = 0
        total_fixtures   = len(fixture_data)
        ht_greenups      = 0
        late_greenups    = 0

        for fd in fixture_data:
            result = simulate_fixture(
                selections = fd["selections"],
                ht_score   = fd["ht_score"],
                ft_score   = fd["ft_score"],
                threshold  = threshold,
            )
            total_pnl    += result["pnl"]
            total_staked += result["total_staked"]

            if result["greened_up"]:
                total_greenups += 1
                if result["green_minute"] == 40:
                    ht_greenups += 1
                else:
                    late_greenups += 1

        roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0

        summary_rows.append({
            "threshold":     label,
            "roi":           round(roi, 2),
            "total_pnl":     round(total_pnl, 2),
            "total_staked":  round(total_staked, 2),
            "greenup_pct":   round(total_greenups / total_fixtures * 100, 1),
            "ht_greenups":   ht_greenups,
            "late_greenups": late_greenups,
        })

        print(f"  Threshold {label:>6}:  ROI {roi:>7.2f}%  "
              f"P&L £{total_pnl:>8,.2f}  "
              f"Green-ups: {total_greenups}/{total_fixtures} "
              f"({round(total_greenups/total_fixtures*100,1)}%)")

    df_summary = pd.DataFrame(summary_rows)

    print(f"\n{'='*65}")
    print("OPTIMISER RESULTS")
    print(f"{'='*65}")
    best = df_summary.loc[df_summary["roi"].idxmax()]
    print(f"\nOptimal threshold: {best['threshold']}")
    print(f"ROI:               {best['roi']}%")
    print(f"Total P&L:         £{best['total_pnl']:,.2f}")
    print(f"Green-up rate:     {best['greenup_pct']}% of fixtures")

    out_path = "data/processed/greenup_optimiser.csv"
    df_summary.to_csv(out_path, index=False)
    print(f"\nFull results saved to {out_path}")

    return df_summary


if __name__ == "__main__":
    df = pd.read_csv("data/processed/fixtures.csv")
    run_optimiser(df)
