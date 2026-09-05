# Market Research Brief — Robo-Advisor Benchmarks

Industry context for interpreting this project’s MPT tiers, 5% drift rebalancing rule, and 60/40 **proxy** comparison. Project numbers below are from this repo’s 2013–2018 backtest; fee / product facts cite external sources.

## Industry Benchmarks

### Typical robo-advisor fee ranges

| Provider | Stated advisory fee (retail automated advice) | Source |
|---|---|---|
| Betterment (Digital) | **0.25%/year** on investing balances that meet plan rules (alternative monthly fee may apply for smaller households without qualifying deposits) | [Betterment — What are Betterment’s fees?](https://www.betterment.com/help/fees) |
| Wealthfront | **0.25%/year** flat advisory fee (commonly cited for its Automated Investing product) | [Morningstar — Robo-Advisor 2025 report](https://www.morningstar.com/content/cs-assets/v3/assets/blt9415ea4cc4157833/blt436d717849ef7d27/680a4c1554e9cb2bcaac7287/Robo-Advisor_2025-final.pdf) |
| Schwab Intelligent Portfolios | **$0** stated advisory fee (portfolio includes a mandatory cash allocation; cash drag is separate from an AUM fee) | Same Morningstar 2025 overview; also summarized in third-party fee comparisons |

**Takeaway for this project:** A ~0.25% AUM fee is a common digital-advice price point; this repo does **not** model fees in the backtest returns.

### Typical risk-tier / equity–bond mixes in the industry

Robo-advisors usually map a questionnaire to a glide of portfolios from conservative (more bonds) to aggressive (more equities):

- **Retail “balanced / moderate”** profiles often cluster near a classic **~60% equity / ~40% fixed income** mix — the industry reference this project’s benchmark *name* alludes to (even though this repo must proxy the bond sleeve with defensive equities).
- Published examples of labeled risk profiles (illustrative, one provider): RBC InvestEase lists Very Conservative ~20% equity / 80% fixed income through Aggressive Growth **100% equity** ([RBC InvestEase — portfolio profiles](https://www.rbcinvestease.com/topics-trends/how-to-get-investment-portfolio.html)).
- Morningstar’s comparative testing of U.S. robos found **recommended equity exposure for similar middle-of-the-road profiles can vary widely by provider** (e.g., from the mid-40%s to ~90% in one hypothetical-investor exercise) ([Morningstar — Not All Robo-Advisors Are Created Equal](https://www.morningstar.com/financial-advisors/not-all-robo-advisors-are-created-equal)).

**Vs this project:** Tiers here are defined by **target volatility** on a **100% equity** universe (Conservative ~9.7% used vol, Moderate 14%, Aggressive 22%), not by an equity/bond mix — so industry stock/bond percentages are context, not a like-for-like mapping.

### 60/40 historical Sharpe (2013–2018) — **this repo’s computation**

For the project’s **60/40 proxy** over the same window as the price data:

| Metric | Value (repo output) |
|---|---:|
| Annualized return | 14.63% |
| Annualized volatility | 10.93% |
| Sharpe (rf = 2%) | **1.155** |
| Cumulative return | 101.5% |
| Max drawdown | −10.3% |

Source: `compare_to_60_40_benchmark()` / `build_60_40_benchmark()` in `src/portfolio_optimization.py` (Prompt 5). This is **not** an external claim about a real bond-inclusive 60/40 ETF portfolio.

### Common rebalancing-trigger norms

- **Betterment** discloses a default **~3%** drift-tolerance threshold for many Betterment-constructed portfolios (with higher thresholds such as **7%** for some custom / crypto offerings); rebalancing also uses cash flows ([Betterment — How and when will my portfolio be rebalanced?](https://www.betterment.com/help/portfolio-rebalancing)).
- **Wealthfront** monitors drift **daily** and rebalances when deviations are large enough that benefits outweigh tax costs; leeway can scale with target weight ([Wealthfront Support — How often do you rebalance](https://support.wealthfront.com/hc/en-us/articles/209353766-How-often-do-you-rebalance-my-Automated-Investing-Account)).
- Industry explainers commonly describe threshold bands on the order of **~3–5%** for drift-based rebalancing ([BestRoboAdvisors — Automatic Portfolio Rebalancing](https://www.bestroboadvisors.org/automatic-portfolio-rebalancing/)).

**Vs this project:** The engine uses a **5% absolute per-asset weight drift** rule. In-sample trigger counts: Conservative **1**, Moderate **5**, Aggressive **6**.

## Comparison to Project Findings

| Portfolio | Sharpe (rf=2%) | Ann. vol | 95% VaR | Notes |
|---|---:|---:|---:|---|
| Conservative | 0.571 | 9.71% | 0.96% | Lowest vol; below proxy Sharpe |
| Moderate | **1.881** | 14.02% | 1.27% | Best Sharpe vs proxy 1.155 |
| Aggressive | 1.567 | 22.00% | 1.96% | Highest return & VaR |
| 60/40 proxy | **1.155** | 10.93% | — | Repo-computed proxy |

Moderate’s Sharpe advantage over the proxy is the clearest risk-adjusted win in-sample; Aggressive wins on raw growth. Fee drag (~0.25% AUM at many robos) is **not** subtracted here.

## Sources

1. Betterment — [What are Betterment’s fees?](https://www.betterment.com/help/fees)
2. Betterment — [How and when will my portfolio be rebalanced?](https://www.betterment.com/help/portfolio-rebalancing)
3. Wealthfront Support — [How often do you rebalance my Automated Investing Account?](https://support.wealthfront.com/hc/en-us/articles/209353766-How-often-do-you-rebalance-my-Automated-Investing-Account)
4. Morningstar — [Robo-Advisor 2025 overview (PDF)](https://www.morningstar.com/content/cs-assets/v3/assets/blt9415ea4cc4157833/blt436d717849ef7d27/680a4c1554e9cb2bcaac7287/Robo-Advisor_2025-final.pdf)
5. Morningstar — [Not All Robo-Advisors Are Created Equal](https://www.morningstar.com/financial-advisors/not-all-robo-advisors-are-created-equal)
6. RBC InvestEase — [Which Investment Portfolio is Right for Me?](https://www.rbcinvestease.com/topics-trends/how-to-get-investment-portfolio.html)
7. BestRoboAdvisors.org — [Automatic Portfolio Rebalancing](https://www.bestroboadvisors.org/automatic-portfolio-rebalancing/)
8. This repository — `src/portfolio_optimization.py` backtest outputs (2013–2018)
