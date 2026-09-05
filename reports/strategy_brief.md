# Strategy Brief — Risk-Tier Allocation Recommendation

## Key Finding

Over the 2013–2018 backtest window, the **Moderate** tier delivered a realized Sharpe ratio of **1.881**, versus **1.155** for this project’s **60/40 proxy** benchmark (rf = 2%). Moderate also beat the proxy on cumulative return (**292%** vs **102%**) while keeping max drawdown milder than Aggressive (**−15.7%** vs **−26.7%**).

> **Benchmark caveat:** The 60/40 series is a *proxy* built from this equity-only universe (60% Tech/Consumer/Industrials basket + 40% defensive equities `DUK`, `SO`, `JNJ`, `T`, `VZ`) — **not** a true stocks/bonds mix. See below and `src/portfolio_optimization.py`.

## Recommended Allocation per Risk Tier

Target volatilities: Conservative 8% (adjusted to **9.71%** min-frontier), Moderate **14%**, Aggressive **22%**. Weights below are cleaned (≥1% cutoff) from `build_tier_portfolios()`.

### Conservative (used vol 9.71%)

Diversified defensive mix (17 names). Top holdings:

| Ticker | Weight |
|---|---:|
| SO | 20.3% |
| MCD | 13.2% |
| KO | 9.0% |
| T | 8.5% |
| PFE | 7.0% |
| WMT | 6.9% |
| PEP | 6.7% |
| JNJ | 6.6% |
| AAPL | 4.6% |
| DIS | 3.1% |
| XOM | 2.6% |
| MMM | 2.4% |
| DUK | 2.1% |
| UNH | 2.0% |
| VZ | 1.9% |
| GE | 1.7% |
| BAC | 1.4% |

### Moderate (14% vol)

| Ticker | Weight |
|---|---:|
| UNH | 26.3% |
| BA | 24.0% |
| ADBE | 14.3% |
| AMZN | 11.1% |
| PEP | 7.8% |
| MCD | 6.8% |
| MMM | 6.1% |
| MSFT | 3.6% |

### Aggressive (22% vol)

Concentrated long-only efficient-risk portfolio (AMZN dominates by construction):

| Ticker | Weight |
|---|---:|
| AMZN | 57.9% |
| ADBE | 33.1% |
| BA | 9.0% |

**Client assignment:** Map synthetic clients by `risk_tier` from `client_profiles.csv`. **Rebalancing:** reset to target when any weight drifts more than **5%** absolute; historically this fired **1 / 5 / 6** times for Conservative / Moderate / Aggressive over the sample.

## Projected Impact (grounded in this backtest)

Relative to assigning every client the one-size-fits-all **60/40 proxy** (ann. return **14.6%**, Sharpe **1.155**, max DD **−10.3%**):

- **Conservative** clients get lower realized return (**7.5%**) and Sharpe (**0.57**) but also lower vol (**9.7%** vs proxy **10.9%**) — appropriate when minimizing variance matters more than matching the proxy’s return.
- **Moderate** clients capture the best risk-adjusted outcome in-sample: Sharpe **1.881** (+0.73 vs proxy) and cumulative wealth far above the proxy, with 1-day 95% VaR **1.27%**.
- **Aggressive** clients maximize growth (ann. return **36.5%**, cumulative **447%**) at the cost of VaR **1.96%** and max DD **−26.7%** — only suitable for long horizons and high risk tolerance.

These figures are **in-sample** on 2013–2018 equities and should not be treated as forecasts.

## 60/40 Benchmark — Bond Proxy Disclosure

This dataset has **no bond ETF or fixed-income securities**. The “60/40” benchmark is therefore a **proxy**:

- **60% equity sleeve:** equal-weighted Tech / Consumer / Industrials basket.
- **40% “bond” sleeve:** equal-weighted defensive equities — **DUK, SO, JNJ, T, VZ**.

Treat comparisons as illustrative until a real fixed-income series is available.

## Methodology Note

Findings are based on **real** historical price data (2013–2018) for 30 securities; client profiles used to assign risk tiers are **synthetic** (see README.md “Data Note”).
