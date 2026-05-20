#!/bin/bash
# ScoreTrader -- Full repo setup script
# Run this from ~/scoretrader on the LXC

set -e
echo "Setting up ScoreTrader repo..."

# ── Folder structure ──────────────────────────────────────────────────────────
mkdir -p config data/raw data/processed data/db src dashboard/frontend dashboard/backend tests scripts

# ── .gitignore ────────────────────────────────────────────────────────────────
cat > .gitignore << 'EOF'
.env
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
venv/
.venv/
data/raw/
data/processed/
data/db/
certs/
.vscode/
.idea/
.DS_Store
Thumbs.db
*.log
EOF

# ── .env.example ─────────────────────────────────────────────────────────────
cat > .env.example << 'EOF'
# ScoreTrader -- Environment Variables
# Copy to .env and fill in your values. NEVER commit .env to GitHub.

BETFAIR_USERNAME=your_betfair_username
BETFAIR_PASSWORD=your_betfair_password
BETFAIR_APP_KEY=your_app_key
BETFAIR_CERT_PATH=/home/scoretrader/certs/client-2048.crt
BETFAIR_KEY_PATH=/home/scoretrader/certs/client-2048.key

WHATSAPP_NUMBER=+447XXXXXXXXX
EOF

# ── requirements.txt ──────────────────────────────────────────────────────────
cat > requirements.txt << 'EOF'
betfairlightweight==3.8.2
pandas==2.2.2
numpy==1.26.4
scipy==1.13.0
requests==2.31.0
python-dotenv==1.0.1
fastapi==0.111.0
uvicorn==0.29.0
pytest==8.2.0
EOF

# ── README.md ─────────────────────────────────────────────────────────────────
cat > README.md << 'EOF'
# ScoreTrader

An automated correct score trading system for Betfair, built in Python with a React dashboard.

## Overview

ScoreTrader uses a Poisson probability model to identify value in the Betfair correct score
market across Premier League and European football. It calculates edge against market-implied
odds, sizes stakes using Half Kelly, places back bets via the Betfair API, monitors matches
in-play, and executes optimal lay bets to green up positions.

## Architecture

```
data_pipeline     ->  Historical fixture and goal data (football-data.co.uk)
poisson_model     ->  Per-fixture score probability matrix
odds_fetcher      ->  Live correct score odds via Betfair API
value_engine      ->  Edge calculation and Half Kelly staking
bet_placer        ->  Supervised/autonomous back bet placement
inplay_monitor    ->  30-second in-play polling loop
exit_engine       ->  Dynamic green-up scoring model
lay_placer        ->  Optimal lay order execution
settler           ->  Post-match P&L calculation
logger            ->  SQLite trade history
dashboard         ->  React frontend + FastAPI backend
```

## Setup

```bash
git clone git@github.com:jakmar86/scoretrader.git
cd scoretrader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Betfair credentials
```

## Build Phases

- Phase 1A -- Data pipeline + Poisson model
- Phase 1B -- Trading engine + bet placement
- Phase 1C -- Web dashboard
- Phase 2  -- Season validation at low stakes
- Phase 3  -- Scale + additional leagues

## License

Private -- Dellally Limited
EOF

# ── config/__init__.py ────────────────────────────────────────────────────────
touch config/__init__.py

# ── config/config.py ──────────────────────────────────────────────────────────
cat > config/config.py << 'EOF'
"""
ScoreTrader -- Configuration
Single control panel for all settings.
"""

config = {

    # Mode
    "supervised": True,
    
    # Staking
    "betting_bank":                1000,
    "kelly_fraction":              0.5,
    "supervised_stake_multiplier": 0.5,
    "max_fixture_stake_supervised": 60,
    "max_fixture_stake_live":      150,
    "max_selections":              5,

    # Value filter
    "min_edge_pct":               1.0,
    "odds_drift_threshold":       0.15,

    # In-play exit engine
    "poll_interval_seconds":      30,
    "exit_threshold":             0.70,
    "partial_exit_pct_early":     0.40,
    "partial_exit_pct_mid":       0.70,
    "full_exit_pct_late":         1.00,
    "max_loss_cut_pct":           0.80,

    # Leagues
    "leagues": [
        "Premier League",
        # "La Liga",
        # "Bundesliga",
        # "Serie A",
        # "Ligue 1",
        # "Eredivisie",
        # "Championship",
    ],

    # Data
    "seasons":                    3,
    "data_source":                "football-data.co.uk",
    "raw_data_path":              "data/raw/",
    "processed_data_path":        "data/processed/",
    "db_path":                    "data/db/scoretrader.db",

    # Betfair API (loaded from .env)
    "betfair_username_env":       "BETFAIR_USERNAME",
    "betfair_password_env":       "BETFAIR_PASSWORD",
    "betfair_app_key_env":        "BETFAIR_APP_KEY",
    "betfair_cert_path_env":      "BETFAIR_CERT_PATH",
    "betfair_key_path_env":       "BETFAIR_KEY_PATH",

    # Notifications
    "whatsapp_number_env":        "WHATSAPP_NUMBER",
    "notify_on_placement":        True,
    "notify_on_exit":             True,
    "notify_on_error":            True,

    # Dashboard
    "dashboard_host":             "0.0.0.0",
    "dashboard_port":             8000,
}
EOF

# ── src/__init__.py ───────────────────────────────────────────────────────────
touch src/__init__.py

# ── src/betfair_auth.py ───────────────────────────────────────────────────────
cat > src/betfair_auth.py << 'EOF'
"""
ScoreTrader -- Betfair Authentication
Handles certificate-based login and session token management.
Phase 1A: Stub -- implement once Betfair API credentials are obtained.
"""

import os
import betfairlightweight
from dotenv import load_dotenv

load_dotenv()


def get_client():
    """Authenticate with Betfair API. Returns authenticated client."""
    username  = os.getenv("BETFAIR_USERNAME")
    password  = os.getenv("BETFAIR_PASSWORD")
    app_key   = os.getenv("BETFAIR_APP_KEY")
    cert_path = os.getenv("BETFAIR_CERT_PATH")
    key_path  = os.getenv("BETFAIR_KEY_PATH")

    if not all([username, password, app_key, cert_path, key_path]):
        raise EnvironmentError(
            "Missing Betfair credentials. Check your .env file."
        )

    client = betfairlightweight.APIClient(
        username=username,
        password=password,
        app_key=app_key,
        certs=(cert_path, key_path),
    )
    client.login()
    return client


if __name__ == "__main__":
    try:
        client = get_client()
        print("Betfair authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
EOF

# ── src/data_pipeline.py ──────────────────────────────────────────────────────
cat > src/data_pipeline.py << 'EOF'
"""
ScoreTrader -- Data Pipeline
Downloads and cleans historical fixture data from football-data.co.uk.
Phase 1A: Core implementation target.
"""

import os
import requests
import pandas as pd
from pathlib import Path

LEAGUE_CODES = {
    "Premier League": "E0",
    "Championship":   "E1",
    "League One":     "E2",
    "League Two":     "E3",
    "La Liga":        "SP1",
    "Bundesliga":     "D1",
    "Serie A":        "I1",
    "Ligue 1":        "F1",
    "Eredivisie":     "N1",
}

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"

REQUIRED_COLS = [
    "Div", "Date", "HomeTeam", "AwayTeam",
    "FTHG", "FTAG", "FTR",
    "HTHG", "HTAG", "HTR",
    "B365H", "B365D", "B365A",
]


def season_code(year: int) -> str:
    return f"{str(year)[2:]}{str(year + 1)[2:]}"


def download_season(league: str, year: int, raw_path: str) -> str:
    code   = LEAGUE_CODES[league]
    season = season_code(year)
    url    = BASE_URL.format(season=season, league=code)
    fname  = f"{code}_{season}.csv"
    fpath  = os.path.join(raw_path, fname)

    if os.path.exists(fpath):
        print(f"  Already exists: {fname}")
        return fpath

    print(f"  Downloading: {url}")
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    with open(fpath, "wb") as f:
        f.write(response.content)

    print(f"  Saved: {fname}")
    return fpath


def load_and_clean(fpath: str) -> pd.DataFrame:
    df   = pd.read_csv(fpath, encoding="latin1")
    cols = [c for c in REQUIRED_COLS if c in df.columns]
    df   = df[cols].copy()
    df   = df.dropna(subset=["FTHG", "FTAG"])
    df["FTHG"] = df["FTHG"].astype(int)
    df["FTAG"] = df["FTAG"].astype(int)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df


def run_pipeline(leagues: list, seasons: int, raw_path: str, processed_path: str):
    Path(raw_path).mkdir(parents=True, exist_ok=True)
    Path(processed_path).mkdir(parents=True, exist_ok=True)

    import datetime
    current_year = datetime.datetime.now().year
    years        = list(range(current_year - seasons, current_year))
    all_frames   = []

    for league in leagues:
        print(f"\nProcessing: {league}")
        for year in years:
            try:
                fpath = download_season(league, year, raw_path)
                df    = load_and_clean(fpath)
                df["League"] = league
                all_frames.append(df)
                print(f"  Loaded {len(df)} fixtures for {year}/{year+1}")
            except Exception as e:
                print(f"  Warning: {league} {year} -- {e}")

    if not all_frames:
        raise ValueError("No data loaded.")

    combined = pd.concat(all_frames, ignore_index=True)
    out_path = os.path.join(processed_path, "fixtures.csv")
    combined.to_csv(out_path, index=False)
    print(f"\nCombined dataset: {len(combined)} fixtures -> {out_path}")
    return combined


if __name__ == "__main__":
    from config.config import config
    run_pipeline(
        leagues        = config["leagues"],
        seasons        = config["seasons"],
        raw_path       = config["raw_data_path"],
        processed_path = config["processed_data_path"],
    )
EOF

# ── src/poisson_model.py ──────────────────────────────────────────────────────
cat > src/poisson_model.py << 'EOF'
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
EOF

# ── src/value_engine.py ───────────────────────────────────────────────────────
cat > src/value_engine.py << 'EOF'
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
EOF

# ── src/logger.py ─────────────────────────────────────────────────────────────
cat > src/logger.py << 'EOF'
"""
ScoreTrader -- Logger
SQLite-based trade and event logger.
"""

import sqlite3
import datetime
from config.config import config

DB_PATH = config["db_path"]


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialise_db():
    conn = get_connection()
    c    = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS fixtures (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT, league TEXT, home_team TEXT, away_team TEXT,
        match_date TEXT, market_id TEXT UNIQUE, status TEXT DEFAULT 'pending'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS backs (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        fixture_id INTEGER, placed_at TEXT, score TEXT,
        stake REAL, odds REAL, bet_id TEXT, status TEXT DEFAULT 'open',
        FOREIGN KEY (fixture_id) REFERENCES fixtures(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lays (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        back_id INTEGER, fixture_id INTEGER, placed_at TEXT, score TEXT,
        lay_stake REAL, lay_odds REAL, lay_pct REAL,
        trigger TEXT, minute INTEGER, bet_id TEXT,
        FOREIGN KEY (back_id) REFERENCES backs(id),
        FOREIGN KEY (fixture_id) REFERENCES fixtures(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS settlements (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        fixture_id   INTEGER, settled_at TEXT, final_score TEXT,
        total_backed REAL, total_laid REAL,
        gross_pnl REAL, commission REAL, net_pnl REAL,
        FOREIGN KEY (fixture_id) REFERENCES fixtures(id)
    )""")

    conn.commit()
    conn.close()
    print(f"Database initialised: {DB_PATH}")


def log_fixture(league, home, away, match_date, market_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO fixtures
        (created_at, league, home_team, away_team, match_date, market_id)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (datetime.datetime.utcnow().isoformat(), league, home, away, match_date, market_id))
    conn.commit()
    fid = c.lastrowid
    conn.close()
    return fid


def log_back(fixture_id, score, stake, odds, bet_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO backs (fixture_id, placed_at, score, stake, odds, bet_id)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (fixture_id, datetime.datetime.utcnow().isoformat(), score, stake, odds, bet_id))
    conn.commit()
    bid = c.lastrowid
    conn.close()
    return bid


def log_lay(back_id, fixture_id, score, lay_stake, lay_odds, lay_pct, trigger, minute, bet_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO lays
        (back_id, fixture_id, placed_at, score, lay_stake, lay_odds, lay_pct, trigger, minute, bet_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (back_id, fixture_id, datetime.datetime.utcnow().isoformat(),
         score, lay_stake, lay_odds, lay_pct, trigger, minute, bet_id))
    conn.commit()
    conn.close()


def log_settlement(fixture_id, final_score, total_backed, total_laid, gross_pnl, commission, net_pnl):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO settlements
        (fixture_id, settled_at, final_score, total_backed, total_laid, gross_pnl, commission, net_pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (fixture_id, datetime.datetime.utcnow().isoformat(), final_score,
         total_backed, total_laid, gross_pnl, commission, net_pnl))
    c.execute("UPDATE fixtures SET status='settled' WHERE id=?", (fixture_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialise_db()
EOF

# ── src/odds_fetcher.py ───────────────────────────────────────────────────────
cat > src/odds_fetcher.py << 'EOF'
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
EOF

# ── src/bet_placer.py ─────────────────────────────────────────────────────────
cat > src/bet_placer.py << 'EOF'
"""
ScoreTrader -- Bet Placer
Places back bets on Betfair. Phase 1B: implementation target.
"""


def place_backs(selections: list, market_id: str) -> list:
    """Place back bets for all selections. Phase 1B: stub."""
    pass
EOF

# ── src/inplay_monitor.py ─────────────────────────────────────────────────────
cat > src/inplay_monitor.py << 'EOF'
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
EOF

# ── src/exit_engine.py ────────────────────────────────────────────────────────
cat > src/exit_engine.py << 'EOF'
"""
ScoreTrader -- Exit Engine
Calculates exit score for open positions. Phase 1B: implementation target.
"""


def calculate_exit_score(selection: dict, current_score: tuple,
                         minute: int, market_odds: float) -> dict:
    """Score a position for exit suitability. Phase 1B: stub."""
    pass
EOF

# ── src/lay_placer.py ─────────────────────────────────────────────────────────
cat > src/lay_placer.py << 'EOF'
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
EOF

# ── src/settler.py ────────────────────────────────────────────────────────────
cat > src/settler.py << 'EOF'
"""
ScoreTrader -- Settler
Post-match P&L calculation. Phase 1B: implementation target.
"""


def settle_fixture(fixture_id: str) -> dict:
    """Calculate final P&L for a fixture. Phase 1B: stub."""
    pass


def format_settlement_message(settlement: dict) -> str:
    """Format WhatsApp settlement summary. Phase 1B: stub."""
    pass
EOF

# ── main.py ───────────────────────────────────────────────────────────────────
cat > main.py << 'EOF'
"""
ScoreTrader -- Main Orchestrator
Entry point for the pre-match pipeline.

Usage:
    python main.py
    python main.py --date 2025-08-17
"""

import argparse
import datetime
from config.config import config
from src.logger import initialise_db


def run(match_date: str = None):
    if match_date is None:
        match_date = datetime.date.today().isoformat()

    print(f"\nScoreTrader -- {match_date}")
    print("=" * 50)

    initialise_db()

    # Phase 1A: data pipeline -> poisson model -> odds fetch -> value engine
    # Phase 1B: bet placement -> inplay monitor

    print("\nPipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ScoreTrader")
    parser.add_argument("--date", type=str, default=None)
    args = parser.parse_args()
    run(args.date)
EOF

# ── scripts/backtest.py ───────────────────────────────────────────────────────
cat > scripts/backtest.py << 'EOF'
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
EOF

# ── tests/test_poisson.py ─────────────────────────────────────────────────────
cat > tests/test_poisson.py << 'EOF'
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
EOF

# ── Git config and initial commit ─────────────────────────────────────────────
git config user.name "Mark"
git config user.email "jakmar86@github.com"
git add .
git commit -m "Initial scaffold -- Phase 1A"
git branch -M main
git push -u origin main

echo ""
echo "================================================"
echo "ScoreTrader repo scaffold complete and pushed!"
echo "================================================"
