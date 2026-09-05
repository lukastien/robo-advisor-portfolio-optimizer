"""
portfolio_optimization.py
==========================
Core portfolio construction and risk analysis logic:

  1. Efficient frontier optimization (Modern Portfolio Theory) via PyPortfolioOpt
  2. Risk-tier portfolio assignment (Conservative / Moderate / Aggressive)
  3. Value-at-Risk (VaR) and Sharpe ratio calculation per tier (stub)
  4. Rebalancing rule simulation (stub)
  5. Benchmark comparison against a 60/40 portfolio (stub)

Usage:
    python src/portfolio_optimization.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models
from pypfopt.exceptions import OptimizationError

# Allow `python src/portfolio_optimization.py` from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from etl_pipeline import PROJECT_ROOT, load_data, compute_returns  # noqa: E402

PRICES_PATH = PROJECT_ROOT / "data" / "raw" / "stock_prices.csv"

RISK_TIER_TARGET_VOLATILITY = {
    "Conservative": 0.08,
    "Moderate": 0.14,
    "Aggressive": 0.22,
}

WEIGHT_CUTOFF = 0.01  # drop near-zero allocations below 1%
RISK_FREE_RATE = 0.02

# Populated by build_tier_portfolios() for get_tier_portfolio() convenience
_LAST_TIER_PORTFOLIOS: dict[str, dict] | None = None


def prices_to_wide(prices_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long OHLCV prices to wide close prices (date × ticker)."""
    ticker_col = "Name" if "Name" in prices_df.columns else "ticker"
    return (
        prices_df.sort_values("date")
        .pivot(index="date", columns=ticker_col, values="close")
        .sort_index()
    )


def compute_expected_returns_and_risk(returns_wide: pd.DataFrame):
    """
    Compute expected returns and sample covariance from a wide daily returns
    DataFrame (output of etl_pipeline.compute_returns).

    Uses PyPortfolioOpt with returns_data=True so callers can pass returns
    directly rather than prices.
    """
    mu = expected_returns.mean_historical_return(returns_wide, returns_data=True)
    cov_matrix = risk_models.sample_cov(returns_wide, returns_data=True)
    return mu, cov_matrix


def feasible_volatility_bounds(mu: pd.Series, cov_matrix: pd.DataFrame) -> tuple[float, float]:
    """
    Return (min_vol, max_vol) attainable on the long-only efficient frontier.

    min_vol comes from min_volatility(); max_vol is found by binary search on
    efficient_risk up to the largest single-asset volatility.
    """
    ef_min = EfficientFrontier(mu, cov_matrix)
    ef_min.min_volatility()
    _, min_vol, _ = ef_min.portfolio_performance(risk_free_rate=RISK_FREE_RATE)
    min_vol = float(min_vol)

    asset_max_vol = float(np.sqrt(np.diag(cov_matrix.to_numpy())).max())
    lo, hi = min_vol, asset_max_vol
    max_vol = min_vol
    for _ in range(40):
        mid = (lo + hi) / 2.0
        try:
            ef = EfficientFrontier(mu, cov_matrix)
            ef.efficient_risk(target_volatility=mid)
            max_vol = mid
            lo = mid
        except (OptimizationError, ValueError):
            hi = mid

    return min_vol, float(max_vol)


def optimize_for_target_volatility(
    mu: pd.Series,
    cov_matrix: pd.DataFrame,
    target_volatility: float,
    weight_cutoff: float = WEIGHT_CUTOFF,
    vol_bounds: tuple[float, float] | None = None,
) -> tuple[dict[str, float], tuple[float, float, float], float]:
    """
    Maximise return subject to a target volatility (efficient_risk).

    If target_volatility is outside the feasible frontier range, clamp it to
    the nearest feasible value and log the adjustment (does not fail silently).

    Returns
    -------
    weights : cleaned weights (near-zeros below cutoff dropped, renormalised)
    performance : (expected_annual_return, annual_volatility, sharpe_ratio)
    used_volatility : the target actually passed to efficient_risk
    """
    min_vol, max_vol = vol_bounds or feasible_volatility_bounds(mu, cov_matrix)
    used_vol = float(target_volatility)

    if used_vol < min_vol - 1e-12:
        print(
            f"WARNING: target volatility {used_vol:.2%} is infeasible "
            f"(min frontier vol is {min_vol:.2%}). "
            f"Adjusting to {min_vol:.2%} — long-only min-variance portfolio "
            f"on this 2013–2018 universe cannot go below that level."
        )
        used_vol = min_vol
    elif used_vol > max_vol + 1e-12:
        print(
            f"WARNING: target volatility {used_vol:.2%} is infeasible "
            f"(max frontier vol is {max_vol:.2%}). "
            f"Adjusting to {max_vol:.2%} — that is the highest volatility "
            f"attainable on the long-only efficient frontier."
        )
        used_vol = max_vol

    ef = EfficientFrontier(mu, cov_matrix)
    ef.efficient_risk(target_volatility=used_vol)
    performance = ef.portfolio_performance(risk_free_rate=RISK_FREE_RATE)
    # clean_weights drops allocations below cutoff and renormalises to 1
    cleaned = ef.clean_weights(cutoff=weight_cutoff, rounding=4)
    weights = {t: float(w) for t, w in cleaned.items() if w > 0}
    total = sum(weights.values())
    if total > 0 and abs(total - 1.0) > 1e-8:
        weights = {
            t: round(w / total, 4) for t, w in weights.items()
        }
        # Fix residual rounding so weights sum exactly to 1
        top = max(weights, key=weights.get)
        weights[top] = round(weights[top] + (1.0 - sum(weights.values())), 4)
    return weights, tuple(float(x) for x in performance), used_vol


def build_tier_portfolios(
    mu: pd.Series,
    cov_matrix: pd.DataFrame,
    targets: dict[str, float] | None = None,
) -> dict[str, dict]:
    """
    Build Conservative / Moderate / Aggressive portfolios via efficient_risk.

    Each value is a dict with keys: weights, performance, target_volatility,
    used_volatility.
    """
    global _LAST_TIER_PORTFOLIOS
    targets = targets or RISK_TIER_TARGET_VOLATILITY
    portfolios: dict[str, dict] = {}
    vol_bounds = feasible_volatility_bounds(mu, cov_matrix)

    for tier, target_vol in targets.items():
        weights, performance, used_vol = optimize_for_target_volatility(
            mu, cov_matrix, target_vol, vol_bounds=vol_bounds
        )
        portfolios[tier] = {
            "weights": weights,
            "performance": {
                "expected_annual_return": performance[0],
                "annual_volatility": performance[1],
                "sharpe_ratio": performance[2],
            },
            "target_volatility": target_vol,
            "used_volatility": used_vol,
        }

    _LAST_TIER_PORTFOLIOS = portfolios
    return portfolios


def get_tier_portfolio(
    tier_name: str,
    tier_portfolios: dict[str, dict] | None = None,
) -> dict:
    """
    Return the portfolio dict for a risk tier.

    Uses `tier_portfolios` if provided; otherwise the last result from
    build_tier_portfolios().
    """
    portfolios = tier_portfolios if tier_portfolios is not None else _LAST_TIER_PORTFOLIOS
    if portfolios is None:
        raise RuntimeError(
            "No tier portfolios available. Call build_tier_portfolios() first "
            "or pass tier_portfolios=..."
        )
    if tier_name not in portfolios:
        raise KeyError(
            f"Unknown tier {tier_name!r}. Available: {sorted(portfolios)}"
        )
    return portfolios[tier_name]


def assign_clients_to_portfolios(
    profiles_df: pd.DataFrame,
    tier_portfolios: dict[str, dict],
) -> pd.DataFrame:
    """
    Merge synthetic clients onto their matching tier portfolio by risk_tier.

    Adds expected return / vol / Sharpe columns and a weights dict column.
    """
    tier_rows = []
    for tier, payload in tier_portfolios.items():
        perf = payload["performance"]
        tier_rows.append(
            {
                "risk_tier": tier,
                "expected_annual_return": perf["expected_annual_return"],
                "annual_volatility": perf["annual_volatility"],
                "sharpe_ratio": perf["sharpe_ratio"],
                "target_volatility": payload["target_volatility"],
                "used_volatility": payload["used_volatility"],
                "weights": payload["weights"],
            }
        )
    tier_df = pd.DataFrame(tier_rows)
    return profiles_df.merge(tier_df, on="risk_tier", how="left")


def calculate_var(portfolio_returns: pd.Series, confidence: float = 0.95) -> float:
    """Calculate historical Value-at-Risk at the given confidence level."""
    raise NotImplementedError


def calculate_sharpe_ratio(
    portfolio_returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE
) -> float:
    """Calculate the annualized Sharpe ratio for a portfolio's return series."""
    raise NotImplementedError


def simulate_rebalancing(
    weights_over_time: pd.DataFrame, drift_threshold: float = 0.05
) -> int:
    """
    Simulate a rebalancing rule: count how many times allocation would have
    drifted more than `drift_threshold` from target weights.
    """
    raise NotImplementedError


def compare_to_60_40_benchmark(tier_returns: dict, benchmark_returns: pd.Series):
    """Compare each risk tier's risk-adjusted return against a 60/40 benchmark."""
    raise NotImplementedError


def _format_weights(weights: dict[str, float]) -> str:
    lines = []
    for ticker, weight in sorted(weights.items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"  {ticker:6s} {weight:6.2%}")
    return "\n".join(lines)


def main():
    prices_df, profiles_df = load_data()
    returns_wide = compute_returns(prices_df)
    print(
        f"Universe: {returns_wide.shape[1]} tickers, "
        f"{returns_wide.shape[0]:,} daily return rows"
    )

    mu, cov_matrix = compute_expected_returns_and_risk(returns_wide)
    min_vol, max_vol = feasible_volatility_bounds(mu, cov_matrix)
    print(
        f"Feasible long-only frontier volatility range: "
        f"{min_vol:.2%} – {max_vol:.2%}"
    )
    print()

    tier_portfolios = build_tier_portfolios(mu, cov_matrix)
    clients = assign_clients_to_portfolios(profiles_df, tier_portfolios)

    for tier in RISK_TIER_TARGET_VOLATILITY:
        portfolio = get_tier_portfolio(tier, tier_portfolios)
        perf = portfolio["performance"]
        max_w = max(portfolio["weights"].values()) if portfolio["weights"] else 0.0
        print("=" * 60)
        print(f"{tier} portfolio")
        print(
            f"Target vol: {portfolio['target_volatility']:.2%} | "
            f"Used vol: {portfolio['used_volatility']:.2%}"
        )
        print("Weights (desc, cleaned, cutoff 1%):")
        print(_format_weights(portfolio["weights"]))
        print(
            f"Expected annual return: {perf['expected_annual_return']:.2%}\n"
            f"Annual volatility:      {perf['annual_volatility']:.2%}\n"
            f"Sharpe ratio (rf={RISK_FREE_RATE:.0%}): {perf['sharpe_ratio']:.3f}"
        )
        if max_w > 0.40:
            top = max(portfolio["weights"], key=portfolio["weights"].get)
            print(
                f"NOTE: {top} weight is {max_w:.1%} (>40%). "
                "This is required by long-only efficient_risk at this "
                "volatility target (concentrated high-return names)."
            )
        print()

    print("=" * 60)
    print(f"Assigned {len(clients)} clients to tier portfolios:")
    print(clients.groupby("risk_tier").size().to_string())
    print()
    print("Sample merged clients:")
    print(
        clients[
            [
                "client_id",
                "risk_tier",
                "expected_annual_return",
                "annual_volatility",
                "sharpe_ratio",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
