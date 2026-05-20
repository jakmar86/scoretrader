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
