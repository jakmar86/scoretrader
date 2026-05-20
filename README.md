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
