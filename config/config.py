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
