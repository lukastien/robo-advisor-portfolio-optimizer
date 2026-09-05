# Tableau Dashboard

Clean CSVs for Tableau Public live in [`dashboard/data/`](data/).
Regenerate anytime with:

```bash
python src/export_for_tableau.py
# or: .venv/bin/python src/export_for_tableau.py
```

## Which CSV feeds which chart

| CSV | Suggested chart | Purpose |
|---|---|---|
| `data/tier_performance_timeseries.csv` | **Line** | Cumulative return over time by tier vs **60/40 Benchmark** (`date`, `tier`, `cumulative_return`) |
| `data/risk_return_summary.csv` | **Scatter** | Risk/return map: X = `annualized_vol`, Y = `annualized_return`, detail/color = `tier`, size or tooltip = `sharpe` / `var_95_pct` |
| `data/rebalance_events.csv` | **Bar** (or timeline) | Rebalance frequency: count of rows by `tier`; optional detail by `date` / `drifted_asset` / `drift_amount` |

## Manual steps — build & publish on Tableau Public

1. **Connect to CSV** — Open Tableau Public → *Connect* → *Text file* → select a file under `dashboard/data/` (repeat or union/add the other two as needed).
2. **Build chart 1 (line)** — From `tier_performance_timeseries.csv`: Columns = `date`, Rows = `cumulative_return`, Color = `tier`. Mark type = Line. Title: “Cumulative return by risk tier vs 60/40 Benchmark”.
3. **Build chart 2 (scatter)** — From `risk_return_summary.csv`: Columns = `annualized_vol`, Rows = `annualized_return`, Color/Label = `tier`. Mark type = Circle. Add `sharpe` and `var_95_pct` to Tooltip.
4. **Build chart 3 (bar)** — From `rebalance_events.csv`: Columns = `tier`, Rows = `CNT(date)` (or Number of Records). Mark type = Bar. Title: “Rebalance triggers (5% drift) by tier”.
5. **Add to dashboard** — *Dashboard* → *New Dashboard* → drag the three sheets onto one canvas; keep titles/legends readable.
6. **Publish** — *Server* → *Tableau Public* → *Save to Tableau Public…* → copy the viz URL.
7. **Paste the URL below** — replace the TBD link so the repo points at the live dashboard.

**Link:** _TBD — paste Tableau Public URL here after publishing_

**Screenshot:** _TBD — optional PNG export of the dashboard_

## Notes

- The **60/40 Benchmark** 40% sleeve is a defensive-equity **bond proxy** (not real bonds) — see `reports/strategy_brief.md`.
- `var_95_pct` is historical 1-day 95% VaR as a **positive % loss**.
- `drift_amount` is the signed weight drift of the asset that breached the 5% threshold on that date.
