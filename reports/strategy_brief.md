# Strategy Brief — Risk-Tier Allocation Recommendation

## Key Finding

Over 2013–2018, risk-tiered MPT portfolios (especially Moderate) delivered higher realized Sharpe ratios than a **60/40 proxy** built from the same equity universe. The Aggressive tier earned the highest cumulative return but with the largest drawdowns and 1-day VaR.

## 60/40 Benchmark — Bond Proxy Disclosure

This dataset has **no bond ETF or fixed-income securities**. The “60/40” benchmark is therefore a **proxy**, not a true stocks/bonds mix:

- **60% equity sleeve:** equal-weighted Tech / Consumer / Industrials basket (e.g. AAPL, AMZN, MSFT, MCD, BA, …).
- **40% “bond” sleeve:** equal-weighted defensive equities — **DUK, SO, JNJ, T, VZ** (Utilities / Healthcare / Telecom).

These names are lower-volatility equities used only as a stand-in for bonds. Their realized volatility is still equity-like and can approach or exceed a true Conservative equity-optimized portfolio. Treat 60/40 comparisons as illustrative until a real fixed-income series is available.

## Recommended Allocation Approach

- Assign clients by `risk_tier` (Conservative / Moderate / Aggressive) from the synthetic profile scores.
- Rebalance when any position drifts more than **5%** from target weight; Conservative rarely triggers, while concentrated Aggressive books rebalance more often.
- Prefer Moderate for balanced risk-adjusted return in this sample; use Aggressive only for clients who can tolerate deeper drawdowns.

## Projected Impact

Relative to the one-size-fits-all 60/40 **proxy**, tiered allocation lets Conservative clients sit closer to the minimum-variance frontier while Moderate/Aggressive clients capture higher realized returns — with the caveat that the proxy’s defensive sleeve is not real bonds.

## Methodology Note

Findings are based on real historical price data (2013–2018) for 30 securities; client profiles used to assign risk tiers are synthetic (see README.md "Data Note").
