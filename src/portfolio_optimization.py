"""
portfolio_optimization.py
==========================
Core portfolio construction and risk analysis logic:

  1. Efficient frontier optimization (Modern Portfolio Theory) via PyPortfolioOpt
  2. Risk-tier portfolio assignment (Conservative / Moderate / Aggressive)
  3. Value-at-Risk (VaR) and Sharpe ratio calculation per tier
  4. Rebalancing rule simulation (5% drift threshold)
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

# 60/40 benchmark proxies (no bond ETF in this universe).
# Equity sleeve: equal-weighted Tech / Consumer / Industrials growth-cyclical basket.
EQUITY_PROXY_TICKERS = [
    "AAPL", "ADBE", "AMZN", "GOOGL", "MSFT",  # Tech
    "DIS", "MCD", "NKE", "SBUX", "WMT",  # Consumer
    "BA", "HON", "MMM",  # Industrials
]

# Bond sleeve PROXY — NOT real bonds / NOT a bond ETF.
# Lowest-vol defensive equities (Utilities / Healthcare / Telecom) used only as a
# stand-in for the 40% "bond" allocation because the dataset has no fixed-income
# securities. Treat results as illustrative, not a true 60/40 stocks/bonds mix.
BOND_PROXY_TICKERS = ["DUK", "SO", "JNJ", "T", "VZ"]

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
    cleaned = ef.clean_weights(cutoff=weight_cutoff, rounding=4)
    weights = {t: float(w) for t, w in cleaned.items() if w > 0}
    total = sum(weights.values())
    if total > 0 and abs(total - 1.0) > 1e-8:
        weights = {t: round(w / total, 4) for t, w in weights.items()}
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


def _weight_vector(
    returns: pd.DataFrame, weights: dict[str, float]
) -> tuple[pd.DataFrame, pd.Series]:
    """Align target weights to the returns columns; renormalise to sum to 1."""
    tickers = [t for t in weights if t in returns.columns and weights[t] > 0]
    if not tickers:
        raise ValueError("No overlapping tickers between weights and returns")
    w = pd.Series({t: float(weights[t]) for t in tickers}, dtype=float)
    w = w / w.sum()
    return returns[tickers].astype(float), w


def portfolio_daily_returns(
    returns: pd.DataFrame, weights: dict[str, float]
) -> pd.Series:
    """Constant-mix (daily-rebalanced) portfolio return series."""
    r, w = _weight_vector(returns, weights)
    return r.fillna(0.0).mul(w, axis=1).sum(axis=1)


def realized_annualized_stats(
    portfolio_returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE
) -> tuple[float, float, float]:
    """Annualized return, vol, and Sharpe from a daily portfolio return series."""
    daily_mean = float(portfolio_returns.mean())
    daily_std = float(portfolio_returns.std(ddof=1))
    ann_return = daily_mean * 252
    ann_vol = daily_std * np.sqrt(252)
    sharpe = (ann_return - risk_free_rate) / ann_vol if ann_vol > 0 else float("nan")
    return ann_return, ann_vol, sharpe


def calculate_var(
    returns: pd.DataFrame,
    weights: dict[str, float],
    confidence: float = 0.95,
) -> float:
    """
    Historical (empirical) VaR of the weighted portfolio return series.

    Uses the (1 - confidence) quantile of daily portfolio returns — not a
    parametric/Gaussian VaR. Returns a positive percentage loss figure
    (e.g. 1.85 means a 1.85% one-day loss at the given confidence).
    """
    port_rets = portfolio_daily_returns(returns, weights)
    alpha = (1.0 - confidence) * 100.0
    quantile = float(np.percentile(port_rets.to_numpy(), alpha))
    return abs(min(quantile, 0.0)) * 100.0


def calculate_sharpe_ratio(
    returns: pd.DataFrame,
    weights: dict[str, float],
    risk_free_rate: float = RISK_FREE_RATE,
) -> float:
    """
    Annualized Sharpe from realized daily portfolio returns over the sample
    window: (mean * 252 - rf) / (std * sqrt(252)).
    """
    port_rets = portfolio_daily_returns(returns, weights)
    _, _, sharpe = realized_annualized_stats(port_rets, risk_free_rate=risk_free_rate)
    return float(sharpe)


def simulate_rebalancing(
    returns: pd.DataFrame,
    target_weights: dict[str, float],
    drift_threshold: float = 0.05,
) -> dict:
    """
    Walk forward day by day: let weights drift with asset returns (no trading).
    Whenever any single asset's weight drifts more than `drift_threshold` from
    its target, log the date and reset to target weights.

    Returns dict with:
      - n_rebalances
      - rebalance_dates
      - avg_holding_period_days (mean trading days between consecutive
        rebalance events; if one event, days from start to that event; if
        none, full sample length)
      - events: list of {date, drifted_asset, drift_amount} for the asset
        with the largest absolute drift on each trigger day
    """
    r, target = _weight_vector(returns, target_weights)
    r = r.fillna(0.0)
    dates = list(r.index)
    current = target.copy()
    rebalance_dates: list = []
    events: list[dict] = []

    for dt in dates:
        day_ret = r.loc[dt]
        current = current * (1.0 + day_ret)
        total = float(current.sum())
        if total <= 0:
            current = target.copy()
            continue
        current = current / total

        drift = current - target
        abs_drift = drift.abs()
        if float(abs_drift.max()) > drift_threshold:
            asset = str(abs_drift.idxmax())
            events.append(
                {
                    "date": dt,
                    "drifted_asset": asset,
                    "drift_amount": float(drift.loc[asset]),
                }
            )
            rebalance_dates.append(dt)
            current = target.copy()

    n_rebalances = len(rebalance_dates)
    if n_rebalances == 0:
        avg_holding = float(len(dates))
    elif n_rebalances == 1:
        avg_holding = float(dates.index(rebalance_dates[0]) + 1)
    else:
        locs = [dates.index(d) for d in rebalance_dates]
        avg_holding = float(np.diff(locs).mean())

    return {
        "n_rebalances": n_rebalances,
        "rebalance_dates": rebalance_dates,
        "avg_holding_period_days": avg_holding,
        "events": events,
    }


def evaluate_tier_risk_metrics(
    returns: pd.DataFrame,
    tier_portfolios: dict[str, dict],
    confidence: float = 0.95,
    risk_free_rate: float = RISK_FREE_RATE,
    drift_threshold: float = 0.05,
) -> pd.DataFrame:
    """Run VaR, Sharpe, and rebalancing simulation for each tier; return summary."""
    rows = []
    for tier in RISK_TIER_TARGET_VOLATILITY:
        weights = tier_portfolios[tier]["weights"]
        port_rets = portfolio_daily_returns(returns, weights)
        ann_ret, ann_vol, _ = realized_annualized_stats(
            port_rets, risk_free_rate=risk_free_rate
        )
        sharpe = calculate_sharpe_ratio(returns, weights, risk_free_rate=risk_free_rate)
        var_pct = calculate_var(returns, weights, confidence=confidence)
        reb = simulate_rebalancing(
            returns, weights, drift_threshold=drift_threshold
        )
        rows.append(
            {
                "tier": tier,
                "annualized_return": ann_ret,
                "annualized_vol": ann_vol,
                "sharpe": sharpe,
                "var_95_pct": var_pct,
                "n_rebalances": reb["n_rebalances"],
                "avg_holding_days": reb["avg_holding_period_days"],
            }
        )
    return pd.DataFrame(rows)


def _equal_weight_basket_returns(
    returns: pd.DataFrame, tickers: list[str]
) -> pd.Series:
    """Equal-weighted daily returns for a ticker basket (missing names skipped)."""
    cols = [t for t in tickers if t in returns.columns]
    if not cols:
        raise ValueError(f"None of {tickers} found in returns columns")
    return returns[cols].fillna(0.0).mean(axis=1)


def build_60_40_benchmark(returns: pd.DataFrame) -> pd.Series:
    """
    Daily returns for a 60/40 proxy portfolio from the equity universe.

    60% equal-weighted Tech/Consumer/Industrials basket + 40% defensive
    equity "bond proxy" (DUK, SO, JNJ, T, VZ). The bond sleeve is a proxy,
    not real fixed income — see BOND_PROXY_TICKERS comment.
    """
    equity = _equal_weight_basket_returns(returns, EQUITY_PROXY_TICKERS)
    bond_proxy = _equal_weight_basket_returns(returns, BOND_PROXY_TICKERS)
    benchmark = 0.60 * equity + 0.40 * bond_proxy
    benchmark.name = "60/40_proxy"
    return benchmark


def max_drawdown(returns: pd.Series) -> float:
    """Maximum drawdown of a return series (negative fraction, e.g. -0.25)."""
    wealth = (1.0 + returns.fillna(0.0)).cumprod()
    drawdown = wealth / wealth.cummax() - 1.0
    return float(drawdown.min())


def performance_metrics(
    returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE
) -> dict[str, float]:
    """Cumulative return, ann. return/vol, Sharpe, and max drawdown."""
    rets = returns.dropna()
    ann_return, ann_vol, sharpe = realized_annualized_stats(
        rets, risk_free_rate=risk_free_rate
    )
    cumulative = float((1.0 + rets).prod() - 1.0)
    return {
        "cumulative_return": cumulative,
        "annualized_return": ann_return,
        "annualized_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(rets),
    }


def compare_to_60_40_benchmark(
    tier_returns: dict[str, pd.Series],
    benchmark_returns: pd.Series,
    risk_free_rate: float = RISK_FREE_RATE,
) -> pd.DataFrame:
    """
    Compare each tier's cumulative return, annualized return, annualized vol,
    Sharpe, and max drawdown against the 60/40 proxy over the same window.
    """
    rows = []
    aligned_bench = benchmark_returns.dropna()
    series_map = {**tier_returns, "60/40_proxy": aligned_bench}

    for name, series in series_map.items():
        # Align each series to the shared date intersection with the benchmark
        common = series.dropna().index.intersection(aligned_bench.index)
        metrics = performance_metrics(series.loc[common], risk_free_rate=risk_free_rate)
        rows.append({"tier": name, **metrics})

    order = list(RISK_TIER_TARGET_VOLATILITY.keys()) + ["60/40_proxy"]
    df = pd.DataFrame(rows)
    df["tier"] = pd.Categorical(df["tier"], categories=order, ordered=True)
    return df.sort_values("tier").reset_index(drop=True)


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
            f"PyPortfolioOpt E[r]/vol/Sharpe: "
            f"{perf['expected_annual_return']:.2%} / "
            f"{perf['annual_volatility']:.2%} / "
            f"{perf['sharpe_ratio']:.3f}"
        )
        if max_w > 0.40:
            top = max(portfolio["weights"], key=portfolio["weights"].get)
            print(
                f"NOTE: {top} weight is {max_w:.1%} (>40%). "
                "This is required by long-only efficient_risk at this "
                "volatility target (concentrated high-return names)."
            )
        print()

    summary = evaluate_tier_risk_metrics(returns_wide, tier_portfolios)
    print("=" * 60)
    print("Risk & rebalancing summary (realized 2013–2018)")
    print(
        f"{'tier':<13} {'ann_return':>10} {'ann_vol':>8} {'Sharpe':>7} "
        f"{'95% VaR':>8} {'# rebal':>8} {'avg hold':>9}"
    )
    for _, row in summary.iterrows():
        print(
            f"{row['tier']:<13} {row['annualized_return']:>9.2%} "
            f"{row['annualized_vol']:>7.2%} {row['sharpe']:>7.3f} "
            f"{row['var_95_pct']:>7.2f}% {int(row['n_rebalances']):>8} "
            f"{row['avg_holding_days']:>8.1f}d"
        )
    print()
    print(
        "VaR is historical 1-day 95% VaR as a positive % loss; "
        "avg hold = mean trading days between rebalance events "
        "(drift threshold 5%)."
    )
    print()

    # --- 60/40 proxy benchmark comparison ---
    benchmark = build_60_40_benchmark(returns_wide)
    equity_sleeve = _equal_weight_basket_returns(returns_wide, EQUITY_PROXY_TICKERS)
    bond_sleeve = _equal_weight_basket_returns(returns_wide, BOND_PROXY_TICKERS)
    eq_vol = float(equity_sleeve.std(ddof=1) * np.sqrt(252))
    bond_vol = float(bond_sleeve.std(ddof=1) * np.sqrt(252))
    bench_vol = float(benchmark.std(ddof=1) * np.sqrt(252))

    tier_returns = {
        tier: portfolio_daily_returns(returns_wide, tier_portfolios[tier]["weights"])
        for tier in RISK_TIER_TARGET_VOLATILITY
    }
    comparison = compare_to_60_40_benchmark(tier_returns, benchmark)

    print("=" * 60)
    print("60/40 PROXY benchmark vs risk tiers (same 2013–2018 window)")
    print(
        "NOTE: 40% sleeve is a DEFENSIVE-EQUITY bond proxy "
        f"({', '.join(BOND_PROXY_TICKERS)}) — not real bonds."
    )
    print(
        f"Sleeve vols — equity basket: {eq_vol:.2%} | "
        f"bond proxy: {bond_vol:.2%} | 60/40 combo: {bench_vol:.2%}"
    )
    print(
        f"{'tier':<13} {'cumul':>8} {'ann_ret':>9} {'ann_vol':>8} "
        f"{'Sharpe':>7} {'maxDD':>8}"
    )
    for _, row in comparison.iterrows():
        print(
            f"{row['tier']:<13} {row['cumulative_return']:>7.1%} "
            f"{row['annualized_return']:>8.2%} {row['annualized_vol']:>7.2%} "
            f"{row['sharpe']:>7.3f} {row['max_drawdown']:>7.1%}"
        )

    cons_vol = float(
        comparison.loc[comparison["tier"] == "Conservative", "annualized_vol"].iloc[0]
    )
    if bond_vol >= cons_vol:
        print(
            f"\nFLAG: bond-proxy sleeve vol ({bond_vol:.2%}) is "
            f"{'above' if bond_vol > cons_vol else 'at/near'} the Conservative "
            f"tier vol ({cons_vol:.2%}). This is expected with equity stand-ins "
            "for bonds — revisit proxy choice if a true fixed-income series "
            "becomes available."
        )
    if bond_vol >= eq_vol:
        print(
            f"\nFLAG: bond-proxy vol ({bond_vol:.2%}) >= equity-sleeve vol "
            f"({eq_vol:.2%}) — proxy choice needs revisiting."
        )

    print()
    print(f"Assigned {len(clients)} clients to tier portfolios:")
    print(clients.groupby("risk_tier").size().to_string())


if __name__ == "__main__":
    main()
