-- ============================================================
-- Exploratory queries against data/processed/portfolio.db
-- Run from the notebook (section 2) or: sqlite3 data/processed/portfolio.db < sql/queries.sql
-- ============================================================

-- 1. Date range and ticker count sanity check
SELECT
    MIN(date) AS start_date,
    MAX(date) AS end_date,
    COUNT(DISTINCT ticker) AS n_tickers,
    COUNT(*) AS n_rows
FROM prices;

-- 2. Average daily closing price by ticker
SELECT
    ticker,
    ROUND(AVG(close), 2) AS avg_close
FROM prices
GROUP BY ticker
ORDER BY avg_close DESC;

-- 3. Client counts and average age by risk tier
SELECT
    risk_tier,
    COUNT(*) AS num_clients,
    ROUND(AVG(age), 1) AS avg_age
FROM client_profiles
GROUP BY risk_tier
ORDER BY risk_tier;

-- 4. Cross-tab of risk tier × income bracket
SELECT
    risk_tier,
    income_bracket,
    COUNT(*) AS num_clients
FROM client_profiles
GROUP BY risk_tier, income_bracket
ORDER BY risk_tier, income_bracket;

-- 5. Windowed daily change for AAPL (LAG) — SQL-side check vs pandas returns
SELECT
    date,
    ticker,
    close,
    LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS prev_close,
    close - LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS daily_change,
    (close - LAG(close) OVER (PARTITION BY ticker ORDER BY date))
        / LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS daily_return
FROM prices
WHERE ticker = 'AAPL'
ORDER BY date;
