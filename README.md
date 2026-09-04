# Portfolio Risk & Robo-Advisor Allocation Engine

A Modern Portfolio Theory-based allocation engine simulating a robo-advisor's core function: building risk-tiered portfolios, quantifying downside risk (VaR, Sharpe ratio), and modeling a rebalancing rule — benchmarked against a standard 60/40 portfolio.

> **Status:** 🚧 Placeholder scaffold — full analysis in progress. This repo currently contains the project structure, real market data, synthetic client profiles, and stub code to be filled in.

## Business Question

Given a client's risk profile, what allocation across a diversified set of securities maximizes risk-adjusted return, and how does that compare to a standard benchmark portfolio?

## Data Note — What's Real vs. Synthetic

- **Stock price data is real**: 5 years of daily OHLCV data (2013–2018) for 30 well-known securities spanning 8 sectors (tech, healthcare, financials, consumer, energy, industrials, utilities, telecom), sourced from a public historical price dataset.
- **Client risk profiles are synthetic**: no real client data exists for this project. 200 synthetic client profiles (age, income bracket, investment horizon, risk tolerance score) were generated with a fixed random seed for reproducibility — see `generate_client_profiles.py`. This is disclosed clearly so the distinction between real market data and illustrative client segmentation is never ambiguous.

## Data

- `data/raw/stock_prices.csv` — real daily price data, 30 tickers, 2013–2018
- `data/raw/client_profiles.csv` — synthetic client profiles (generated via `generate_client_profiles.py`)

## Project Structure

```
robo-advisor-portfolio-optimizer/
├── data/
│   ├── raw/                              # Real price data + synthetic client profiles
│   └── processed/                        # Cleaned/joined data, computed returns
├── generate_client_profiles.py            # Synthetic client profile generator (documented, seeded)
├── sql/
│   └── schema.sql                         # Relational schema + exploratory queries
├── notebooks/
│   └── 01_portfolio_optimization.ipynb    # Returns, efficient frontier, VaR/Sharpe, rebalancing
├── src/
│   ├── etl_pipeline.py                    # Data cleaning / loading script
│   └── portfolio_optimization.py          # MPT optimizer, risk metrics, rebalancing logic
├── reports/
│   ├── market_research_brief.md
│   └── strategy_brief.md
├── dashboard/
│   └── README.md                          # Link to published Tableau dashboard
├── requirements.txt
└── README.md
```

## Methodology (planned)

1. **Data Processing** — compute daily/monthly returns and rolling volatility from real price data; load into SQLite
2. **Portfolio Construction** — build the efficient frontier using Modern Portfolio Theory (`PyPortfolioOpt`); assign each synthetic client to a risk-tier portfolio (Conservative/Moderate/Aggressive)
3. **Risk Metrics** — calculate Value-at-Risk (VaR) and Sharpe ratio per portfolio tier
4. **Rebalancing Simulation** — model a rule that rebalances when allocation drifts more than 5% from target weights; measure how often it would trigger historically
5. **Benchmark Comparison** — compare each risk tier's historical risk-adjusted performance against a standard 60/40 (stocks/bonds proxy) portfolio
6. **Dashboard** — Tableau dashboard comparing risk-tier performance and volatility

## Tools

Python (pandas, NumPy, PyPortfolioOpt, SciPy), SQL (SQLite), Tableau

## Status / To Do

- [x] Repo structure + real price data sourced + synthetic client profiles generated
- [ ] ETL pipeline (`src/etl_pipeline.py`)
- [ ] SQL schema + exploratory queries (`sql/schema.sql`)
- [ ] Efficient frontier optimization
- [ ] VaR / Sharpe ratio calculation by risk tier
- [ ] Rebalancing rule simulation
- [ ] 60/40 benchmark comparison
- [ ] Tableau dashboard
- [ ] Strategy brief write-up

---
*This is a self-directed portfolio project using real historical price data and clearly-disclosed synthetic client profiles, to demonstrate a portfolio-optimization and risk-analysis methodology.*
