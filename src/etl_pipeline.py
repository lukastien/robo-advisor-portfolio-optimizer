"""
etl_pipeline.py
================
Loads real price data (data/raw/stock_prices.csv) and synthetic
client profiles (data/raw/client_profiles.csv), and writes them
into a local SQLite database (see sql/schema.sql).

Usage:
    python src/etl_pipeline.py
"""

from pathlib import Path

import pandas as pd
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRICES_PATH = PROJECT_ROOT / "data" / "raw" / "stock_prices.csv"
PROFILES_PATH = PROJECT_ROOT / "data" / "raw" / "client_profiles.csv"
DB_PATH = PROJECT_ROOT / "data" / "processed" / "portfolio.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def load_data(
    prices_path: Path = PRICES_PATH,
    profiles_path: Path = PROFILES_PATH,
):
    """Load both raw CSVs into DataFrames."""
    prices_df = pd.read_csv(prices_path, parse_dates=["date"])
    profiles_df = pd.read_csv(profiles_path)
    return prices_df, profiles_df


def compute_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot closing prices to wide format (date x ticker), compute daily
    percentage returns, and drop the first all-NaN row from pct_change.
    """
    ticker_col = "Name" if "Name" in prices_df.columns else "ticker"
    prices_wide = (
        prices_df.sort_values("date")
        .pivot(index="date", columns=ticker_col, values="close")
        .sort_index()
    )
    returns = prices_wide.pct_change().dropna(how="all")
    returns.columns.name = None
    return returns


def load_to_sqlite(
    prices_df: pd.DataFrame,
    profiles_df: pd.DataFrame,
    db_path: Path = DB_PATH,
    schema_path: Path = SCHEMA_PATH,
) -> Path:
    """
    Create the SQLite database (and parent folder if needed), apply
    sql/schema.sql, and load both raw tables. Returns the db path.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = Path(schema_path).read_text()

    prices_out = prices_df.rename(columns={"Name": "ticker"}).copy()
    prices_out["date"] = pd.to_datetime(prices_out["date"]).dt.strftime("%Y-%m-%d")
    prices_out = prices_out[["date", "ticker", "open", "high", "low", "close", "volume"]]

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        prices_out.to_sql("prices", conn, if_exists="append", index=False)
        profiles_df.to_sql("client_profiles", conn, if_exists="append", index=False)
        conn.commit()

    return db_path


def main():
    prices_df, profiles_df = load_data()
    returns_df = compute_returns(prices_df)
    db_path = load_to_sqlite(prices_df, profiles_df)

    ticker_col = "Name" if "Name" in prices_df.columns else "ticker"
    n_tickers = prices_df[ticker_col].nunique()
    date_min = prices_df["date"].min()
    date_max = prices_df["date"].max()
    tier_counts = profiles_df["risk_tier"].value_counts().sort_index()

    print(f"Loaded {len(prices_df):,} price rows across {n_tickers} tickers")
    print(f"Loaded {len(profiles_df):,} client profiles")
    print(f"Date range: {date_min.date()} → {date_max.date()}")
    print(f"Daily returns shape: {returns_df.shape[0]:,} days × {returns_df.shape[1]} tickers")
    print(f"Wrote SQLite DB → {db_path}")
    print("Clients per risk tier:")
    for tier, count in tier_counts.items():
        print(f"  {tier}: {count}")


if __name__ == "__main__":
    main()
