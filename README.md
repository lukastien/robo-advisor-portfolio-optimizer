# Portfolio Risk & Robo-Advisor Allocation Engine

A Modern Portfolio Theory-based allocation engine simulating a robo-advisor's core function: building risk-tiered portfolios, quantifying downside risk (VaR, Sharpe ratio), and modeling a rebalancing rule — benchmarked against a **60/40 proxy** portfolio.

> **Status:** Core analysis complete (ETL → MPT tiers → VaR/Sharpe → 5% rebalancing → 60/40 proxy comparison → notebook + Tableau CSV exports). Tableau Public URL still TBD after manual publish.

## Business Question

Given a client's risk profile, what allocation across a diversified set of securities maximizes risk-adjusted return, and how does that compare to a standard benchmark portfolio?

## Data Note — What's Real vs. Synthetic

- **Stock price data is real**: 5 years of daily OHLCV data (2013–2018) for 30 well-known securities spanning 8 sectors (tech, healthcare, financials, consumer, energy, industrials, utilities, telecom), sourced from a public historical price dataset.
- **Client risk profiles are synthetic**: no real client data exists for this project. 200 synthetic client profiles (age, income bracket, investment horizon, risk tolerance score) were generated with a fixed random seed for reproducibility — see `generate_client_profiles.py`. This is disclosed clearly so the distinction between real market data and illustrative client segmentation is never ambiguous.

## Results (2013–2018 backtest)

Computed via `src/portfolio_optimization.py` (rf = 2%). The **60/40** row is this repo’s equity **proxy** (defensive stocks stand in for bonds — not a real bond allocation).

| Portfolio | Ann. return | Ann. vol | Sharpe | 95% VaR | Max drawdown | Cumulative |
|---|---:|---:|---:|---:|---:|---:|
| Conservative | 7.55% | 9.71% | 0.571 | 0.96% | −11.3% | 42.4% |
| Moderate | 28.38% | 14.02% | **1.881** | 1.27% | −15.7% | 292% |
| Aggressive | 36.47% | 22.00% | 1.567 | 1.96% | −26.7% | 447% |
| 60/40 proxy | 14.63% | 10.93% | **1.155** | — | −10.3% | 102% |

**Highlights**

- **Moderate** has the best realized Sharpe (**1.881** vs **1.155** for the 60/40 proxy).
- **Aggressive** leads on return but has the highest VaR and deepest drawdown; top weight is AMZN (~58%) by long-only `efficient_risk` at 22% vol.
- **Conservative** 8% vol target was infeasible (min frontier ≈ 9.71%); portfolio was built at that feasible floor.
- 5% drift rebalances in-sample: Conservative **1**, Moderate **5**, Aggressive **6**.

See `reports/strategy_brief.md` for full weights and `reports/market_research_brief.md` for industry fee / rebalancing context.

## Data

- `data/raw/stock_prices.csv` — real daily price data, 30 tickers, 2013–2018
- `data/raw/client_profiles.csv` — synthetic client profiles (generated via `generate_client_profiles.py`)
- `dashboard/data/*.csv` — Tableau-ready exports (`python src/export_for_tableau.py`)

## Project Structure

```
robo-advisor-portfolio-optimizer/
├── data/
│   ├── raw/                              # Real price data + synthetic client profiles
│   └── processed/                        # SQLite DB from ETL
├── generate_client_profiles.py
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── notebooks/
│   └── 01_portfolio_optimization.ipynb
├── src/
│   ├── etl_pipeline.py
│   ├── portfolio_optimization.py
│   └── export_for_tableau.py
├── reports/
│   ├── market_research_brief.md
│   └── strategy_brief.md
├── dashboard/
│   ├── data/                             # CSVs for Tableau
│   └── README.md
├── requirements.txt
└── README.md
```

## Methodology

1. **Data Processing** — daily returns from real prices; load into SQLite
2. **Portfolio Construction** — PyPortfolioOpt efficient frontier; Conservative / Moderate / Aggressive tiers
3. **Risk Metrics** — historical 95% VaR and annualized Sharpe per tier
4. **Rebalancing Simulation** — rebalance when any weight drifts more than 5% from target
5. **Benchmark Comparison** — 60/40 **proxy** vs each tier (cumulative return, vol, Sharpe, max drawdown)
6. **Dashboard** — Tableau-ready CSVs + build/publish steps in `dashboard/README.md`

## Tools

Python (pandas, NumPy, PyPortfolioOpt, SciPy), SQL (SQLite), Tableau

## Status / To Do

- [x] Repo structure + real price data sourced + synthetic client profiles generated
- [x] ETL pipeline (`src/etl_pipeline.py`)
- [x] SQL schema + exploratory queries (`sql/schema.sql`, `sql/queries.sql`)
- [x] Efficient frontier optimization
- [x] VaR / Sharpe ratio calculation by risk tier
- [x] Rebalancing rule simulation
- [x] 60/40 benchmark comparison (equity bond-proxy disclosed)
- [x] Tableau-ready CSV exports + dashboard build guide (`src/export_for_tableau.py`, `dashboard/`)
- [x] Strategy brief + market research brief write-ups
- [ ] Publish Tableau Public dashboard and paste URL into `dashboard/README.md`

---
*This is a self-directed portfolio project using real historical price data and clearly-disclosed synthetic client profiles, to demonstrate a portfolio-optimization and risk-analysis methodology.*
