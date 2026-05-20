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
