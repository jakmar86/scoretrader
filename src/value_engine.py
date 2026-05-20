"""
ScoreTrader -- Value Engine
Calculates edge and Half Kelly stakes for each selection.
Phase 1A: Core implementation target.
"""

from config.config import config


def calculate_edge(model_prob: float, market_odds: float) -> float:
    implied_prob = 1.0 / market_odds
    return round((model_prob - implied_prob) * 100, 2)


def kelly_stake(model_prob: float, market_odds: float,
                bank: float, fraction: float = 0.5) -> float:
    b = market_odds - 1
    p = model_prob
    q = 1 - p
    if b <= 0 or p <= 0:
        return 0.0
    raw = (b * p - q) / b
    if raw <= 0:
        return 0.0
    return round(raw * fraction * bank, 2)


def select_and_size(scored_selections: list, bank: float) -> list:
    min_edge   = config["min_edge_pct"]
    fraction   = config["kelly_fraction"]
    supervised = config["supervised"]
    multiplier = config["supervised_stake_multiplier"] if supervised else 1.0
    max_stake  = (config["max_fixture_stake_supervised"] if supervised
                  else config["max_fixture_stake_live"])

    results = []
    for s in scored_selections:
        edge  = calculate_edge(s["model_prob"], s["market_odds"])
        stake = kelly_stake(s["model_prob"], s["market_odds"], bank, fraction)
        stake = round(stake * multiplier, 2)
        if edge >= min_edge:
            results.append({**s, "edge_pct": edge, "kelly_stake": stake})

    if not results:
        return []

    results.sort(key=lambda x: x["edge_pct"], reverse=True)
    results = results[:config["max_selections"]]

    total = sum(r["kelly_stake"] for r in results)
    if total > max_stake:
        scale = max_stake / total
        for r in results:
            r["final_stake"] = round(r["kelly_stake"] * scale, 2)
    else:
        for r in results:
            r["final_stake"] = r["kelly_stake"]

    return results


if __name__ == "__main__":
    test = [
        {"score": "1-1", "model_prob": 0.142, "market_odds": 8.40},
        {"score": "2-1", "model_prob": 0.114, "market_odds": 10.0},
        {"score": "1-0", "model_prob": 0.128, "market_odds": 7.60},
        {"score": "0-1", "model_prob": 0.098, "market_odds": 11.5},
        {"score": "2-0", "model_prob": 0.089, "market_odds": 13.5},
    ]
    sized = select_and_size(test, bank=1000)
    print(f"\n{'Score':<8} {'Model%':>8} {'Odds':>6} {'Edge%':>7} {'Stake':>8}")
    print("-" * 45)
    for s in sized:
        print(f"{s['score']:<8} {s['model_prob']*100:>7.1f}% "
              f"{s['market_odds']:>6.2f} {s['edge_pct']:>6.1f}%  "
              f"£{s['final_stake']:>6.2f}")
    print(f"\nTotal: £{sum(s['final_stake'] for s in sized):.2f}")
