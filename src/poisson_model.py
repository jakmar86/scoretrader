"""
ScoreTrader -- Poisson Model
Generates score probability matrices for upcoming fixtures.
Phase 1A: Core implementation target.
"""

import numpy as np
from scipy.stats import poisson


def score_probability(home_attack: float, home_defence: float,
                      away_attack: float, away_defence: float,
                      home_adv: float, max_goals: int = 8) -> np.ndarray:
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
                "prob":  matrix[i][j],
            })
    results.sort(key=lambda x: x["prob"], reverse=True)
    return results[:n]


def build_team_strengths(df):
    """
    Calculate attack and defence strength ratings for each team.
    Phase 1A: Implementation target.
    """
    pass


def run_model(home_team: str, away_team: str, df) -> list:
    """
    Run full Poisson model for a fixture.
    Phase 1A: Implementation target.
    """
    pass


if __name__ == "__main__":
    matrix = score_probability(1.3, 0.9, 1.1, 1.0, 1.15)
    scores = top_scores(matrix, n=8)
    print("Top 8 predicted scores:")
    for s in scores:
        print(f"  {s['score']:>5}  {s['prob']*100:.2f}%")
