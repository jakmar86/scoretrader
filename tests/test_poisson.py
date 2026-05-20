"""ScoreTrader -- Poisson Model Tests"""

import numpy as np
import pytest
from src.poisson_model import score_probability, top_scores


def test_matrix_sums_to_one():
    matrix = score_probability(1.3, 0.9, 1.1, 1.0, 1.15)
    assert abs(matrix.sum() - 1.0) < 0.01


def test_top_scores_returns_n():
    matrix = score_probability(1.2, 1.0, 1.0, 1.0, 1.1)
    assert len(top_scores(matrix, n=5)) == 5


def test_top_scores_sorted():
    matrix = score_probability(1.2, 1.0, 1.0, 1.0, 1.1)
    probs  = [s["prob"] for s in top_scores(matrix, n=8)]
    assert probs == sorted(probs, reverse=True)


def test_home_advantage():
    low  = score_probability(1.2, 1.0, 1.0, 1.0, 1.0)
    high = score_probability(1.2, 1.0, 1.0, 1.0, 1.3)
    assert high[1][0] > low[1][0]
