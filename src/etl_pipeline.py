"""
etl_pipeline.py
================
Loads real price data (data/raw/stock_prices.csv) and synthetic
client profiles (data/raw/client_profiles.csv), and writes them
into a local SQLite database (see sql/schema.sql).

STATUS: placeholder stub — logic to be filled in.

Usage (once implemented):
    python src/etl_pipeline.py
"""

import pandas as pd
import sqlite3
from pathlib import Path

PRICES_PATH = Path("data/raw/stock_prices.csv")
PROFILES_PATH = Path("data/raw/client_profiles.csv")
DB_PATH = Path("data/processed/portfolio.db")


def load_data():
    """Load both raw CSVs into DataFrames."""
    prices_df = pd.read_csv(PRICES_PATH, parse_dates=["date"])
    profiles_df = pd.read_csv(PROFILES_PATH)
    return prices_df, profiles_df


def compute_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily returns per ticker from closing prices.

    TODO:
      - Pivot to wide format (date x ticker) for return/covariance calcs
      - Compute daily pct_change() per ticker
      - Handle any missing trading days per ticker
    """
    raise NotImplementedError("Fill in returns calculation")


def load_to_sqlite(prices_df, profiles_df, db_path: Path):
    """Write both DataFrames into the SQLite database defined in sql/schema.sql."""
    raise NotImplementedError("Fill in database load logic")


def main():
    prices_df, profiles_df = load_data()
    print(f"Loaded {len(prices_df)} price rows across {prices_df['Name'].nunique() if 'Name' in prices_df.columns else prices_df['ticker'].nunique()} tickers")
    print(f"Loaded {len(profiles_df)} client profiles")

    # returns_df = compute_returns(prices_df)
    # load_to_sqlite(prices_df, profiles_df, DB_PATH)
    print("TODO: implement compute_returns() and load_to_sqlite()")


if __name__ == "__main__":
    main()
