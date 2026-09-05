"""
export_for_tableau.py
=====================
Build tidy, dashboard-ready CSV exports for Tableau Public.

Writes to dashboard/data/:
  1. tier_performance_timeseries.csv
  2. risk_return_summary.csv
  3. rebalance_events.csv

Usage (from repo root):
    python src/export_for_tableau.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from etl_pipeline import PROJECT_ROOT, load_data, compute_returns  # noqa: E402
from portfolio_optimization import (  # noqa: E402
    RISK_FREE_RATE,
    RISK_TIER_TARGET_VOLATILITY,
    build_60_40_benchmark,
    build_tier_portfolios,
    calculate_sharpe_ratio,
    calculate_var,
    compute_expected_returns_and_risk,
    performance_metrics,
    portfolio_daily_returns,
    realized_annualized_stats,
    simulate_rebalancing,
)

OUTPUT_DIR = PROJECT_ROOT / "dashboard" / "data"
BENCHMARK_LABEL = "60/40 Benchmark"


def _historical_var_pct(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical VaR as a positive percentage loss (same convention as calculate_var)."""
    alpha = (1.0 - confidence) * 100.0
    quantile = float(np.percentile(returns.dropna().to_numpy(), alpha))
    return abs(min(quantile, 0.0)) * 100.0


def build_timeseries(
    tier_returns: dict[str, pd.Series], benchmark: pd.Series
) -> pd.DataFrame:
    """Long/tidy cumulative return series for line charts."""
    frames = []
    series_map = {**tier_returns, BENCHMARK_LABEL: benchmark}
    for name, rets in series_map.items():
        cumul = (1.0 + rets.fillna(0.0)).cumprod() - 1.0
        frames.append(
            pd.DataFrame(
                {
                    "date": cumul.index,
                    "tier": name,
                    "cumulative_return": cumul.to_numpy(),
                }
            )
        )
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out.sort_values(["tier", "date"]).reset_index(drop=True)


def build_risk_return_summary(
    returns: pd.DataFrame,
    tier_portfolios: dict[str, dict],
    tier_returns: dict[str, pd.Series],
    benchmark: pd.Series,
) -> pd.DataFrame:
    """One row per tier + benchmark for a risk/return scatter."""
    rows = []
    for tier, series in tier_returns.items():
        weights = tier_portfolios[tier]["weights"]
        ann_ret, ann_vol, _ = realized_annualized_stats(series)
        rows.append(
            {
                "tier": tier,
                "annualized_return": ann_ret,
                "annualized_vol": ann_vol,
                "sharpe": calculate_sharpe_ratio(returns, weights),
                "var_95_pct": calculate_var(returns, weights),
            }
        )

    bench_metrics = performance_metrics(benchmark, risk_free_rate=RISK_FREE_RATE)
    rows.append(
        {
            "tier": BENCHMARK_LABEL,
            "annualized_return": bench_metrics["annualized_return"],
            "annualized_vol": bench_metrics["annualized_vol"],
            "sharpe": bench_metrics["sharpe"],
            "var_95_pct": _historical_var_pct(benchmark),
        }
    )
    order = list(RISK_TIER_TARGET_VOLATILITY.keys()) + [BENCHMARK_LABEL]
    df = pd.DataFrame(rows)
    df["tier"] = pd.Categorical(df["tier"], categories=order, ordered=True)
    return df.sort_values("tier").reset_index(drop=True)


def build_rebalance_events(
    returns: pd.DataFrame, tier_portfolios: dict[str, dict]
) -> pd.DataFrame:
    """Rebalance trigger rows: tier, date, drifted_asset, drift_amount."""
    rows = []
    for tier in RISK_TIER_TARGET_VOLATILITY:
        reb = simulate_rebalancing(
            returns, tier_portfolios[tier]["weights"], drift_threshold=0.05
        )
        for event in reb["events"]:
            rows.append(
                {
                    "tier": tier,
                    "date": pd.Timestamp(event["date"]).strftime("%Y-%m-%d"),
                    "drifted_asset": event["drifted_asset"],
                    "drift_amount": event["drift_amount"],
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=["tier", "date", "drifted_asset", "drift_amount"]
        )
    return pd.DataFrame(rows).sort_values(["tier", "date"]).reset_index(drop=True)


def export_all(output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prices_df, _ = load_data()
    returns = compute_returns(prices_df)
    mu, cov = compute_expected_returns_and_risk(returns)
    tier_portfolios = build_tier_portfolios(mu, cov)
    benchmark = build_60_40_benchmark(returns)
    tier_returns = {
        tier: portfolio_daily_returns(returns, tier_portfolios[tier]["weights"])
        for tier in RISK_TIER_TARGET_VOLATILITY
    }

    paths = {}
    timeseries = build_timeseries(tier_returns, benchmark)
    paths["tier_performance_timeseries"] = output_dir / "tier_performance_timeseries.csv"
    timeseries.to_csv(paths["tier_performance_timeseries"], index=False)

    summary = build_risk_return_summary(
        returns, tier_portfolios, tier_returns, benchmark
    )
    paths["risk_return_summary"] = output_dir / "risk_return_summary.csv"
    summary.to_csv(paths["risk_return_summary"], index=False)

    events = build_rebalance_events(returns, tier_portfolios)
    paths["rebalance_events"] = output_dir / "rebalance_events.csv"
    events.to_csv(paths["rebalance_events"], index=False)

    return paths


def main():
    paths = export_all()
    print(f"Wrote Tableau-ready CSVs → {OUTPUT_DIR}")
    for name, path in paths.items():
        df = pd.read_csv(path)
        print(f"  {path.name}: {len(df):,} rows × {df.shape[1]} cols")


if __name__ == "__main__":
    main()
