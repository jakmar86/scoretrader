"""
ScoreTrader -- Poisson Model
Generates score probability matrices for upcoming fixtures.
"""

import numpy as np
import pandas as pd
from scipy.stats import poisson


# Recency weights per season (oldest to newest)
SEASON_WEIGHTS = {0: 0.20, 1: 0.35, 2: 0.45}  # 3 seasons
HOME_ADVANTAGE = 1.35  # Applied to home attack expectation


def score_probability(home_attack: float, home_defence: float,
                      away_attack: float, away_defence: float,
                      home_adv: float = HOME_ADVANTAGE,
                      max_goals: int = 8) -> np.ndarray:
    """Generate probability matrix where matrix[i][j] = P(home i, away j)."""
    home_exp = home_attack * away_defence * home_adv
    away_exp = away_attack * home_defence

    matrix = np.outer(
        poisson.pmf(range(max_goals + 1), home_exp),
        poisson.pmf(range(max_goals + 1), away_exp),
    )
    return matrix


def top_scores(matrix: np.ndarray, n: int = 5) -> list:
    """Return top N most probable scorelines."""
    results = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            results.append({
                "score": f"{i}-{j}",
                "home":  i,
                "away":  j,
                "prob":  round(float(matrix[i][j]), 6),
            })
    results.sort(key=lambda x: x["prob"], reverse=True)
    return results[:n]


def build_team_strengths(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate attack and defence strength ratings for each team
    using weighted Poisson approach across multiple seasons.

    Returns DataFrame with columns:
        team | attack | defence
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    # Assign season index (0 = oldest, 2 = most recent)
    seasons = sorted(df["Date"].dt.year.unique())
    # Group by season year (use August cutoff for football seasons)
    df["season_year"] = df["Date"].apply(
        lambda d: d.year if d.month >= 8 else d.year - 1
    )
    season_years = sorted(df["season_year"].unique())
    season_index = {yr: i for i, yr in enumerate(season_years)}
    df["season_idx"] = df["season_year"].map(season_index)
    df["weight"] = df["season_idx"].map(SEASON_WEIGHTS)

    # League averages (weighted)
    total_weight  = df["weight"].sum()
    avg_home_goal = (df["FTHG"] * df["weight"]).sum() / total_weight
    avg_away_goal = (df["FTAG"] * df["weight"]).sum() / total_weight

    # Per-team weighted totals
    teams = sorted(set(df["HomeTeam"].unique()) | set(df["AwayTeam"].unique()))
    strengths = []

    for team in teams:
        home_games = df[df["HomeTeam"] == team]
        away_games = df[df["AwayTeam"] == team]

        # Weighted goals
        hw = home_games["weight"].sum()
        aw = away_games["weight"].sum()

        if hw == 0 or aw == 0:
            continue

        home_scored   = (home_games["FTHG"] * home_games["weight"]).sum() / hw
        home_conceded = (home_games["FTAG"] * home_games["weight"]).sum() / hw
        away_scored   = (away_games["FTAG"] * away_games["weight"]).sum() / aw
        away_conceded = (away_games["FTHG"] * away_games["weight"]).sum() / aw

        # Combine home and away into single attack/defence rating
        attack  = ((home_scored / avg_home_goal) + (away_scored / avg_away_goal)) / 2
        defence = ((home_conceded / avg_away_goal) + (away_conceded / avg_home_goal)) / 2

        strengths.append({
            "team":    team,
            "attack":  round(attack, 4),
            "defence": round(defence, 4),
        })

    return pd.DataFrame(strengths).set_index("team")


def run_model(home_team: str, away_team: str, df: pd.DataFrame,
              n: int = 5) -> list:
    """
    Run full Poisson model for a fixture.
    Returns top N scorelines with probabilities.
    """
    strengths = build_team_strengths(df)

    if home_team not in strengths.index:
        raise ValueError(f"Unknown team: {home_team}")
    if away_team not in strengths.index:
        raise ValueError(f"Unknown team: {away_team}")

    home = strengths.loc[home_team]
    away = strengths.loc[away_team]

    matrix = score_probability(
        home_attack  = home["attack"],
        home_defence = home["defence"],
        away_attack  = away["attack"],
        away_defence = away["defence"],
    )

    return top_scores(matrix, n=n)


if __name__ == "__main__":
    df = pd.read_csv("data/processed/fixtures.csv")

    print("Team strength ratings (sample):")
    strengths = build_team_strengths(df)
    print(strengths.sort_values("attack", ascending=False).head(10).to_string())

    print("\nExample fixture: Man City vs Arsenal")
    scores = run_model("Man City", "Arsenal", df)
    print(f"\n{'Score':<8} {'Probability':>12}")
    print("-" * 22)
    for s in scores:
        print(f"{s['score']:<8} {s['prob']*100:>11.2f}%")
