-- ============================================================
-- Portfolio Risk & Robo-Advisor Allocation Engine — Schema
-- ============================================================
-- Loads real price data + synthetic client profiles into
-- linked tables.

DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS client_profiles;

CREATE TABLE prices (
    date        TEXT,
    ticker      TEXT,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      INTEGER,
    PRIMARY KEY (date, ticker)
);

CREATE TABLE client_profiles (
    client_id                  INTEGER PRIMARY KEY,
    age                        INTEGER,
    income_bracket             TEXT,
    investment_horizon_years   INTEGER,
    risk_tolerance_score       INTEGER,
    risk_tier                  TEXT
);

-- ============================================================
-- TODO: Example exploratory queries to build out
-- ============================================================

-- 1. Date range and ticker count sanity check
-- SELECT MIN(date) AS start_date, MAX(date) AS end_date, COUNT(DISTINCT ticker) AS n_tickers
-- FROM prices;

-- 2. Average daily closing price by ticker (sanity check)
-- SELECT ticker, ROUND(AVG(close), 2) AS avg_close
-- FROM prices
-- GROUP BY ticker
-- ORDER BY avg_close DESC;

-- 3. Client distribution by risk tier
-- SELECT risk_tier, COUNT(*) AS num_clients, ROUND(AVG(age), 1) AS avg_age
-- FROM client_profiles
-- GROUP BY risk_tier;

-- 4. Client distribution by risk tier and income bracket
-- SELECT risk_tier, income_bracket, COUNT(*) AS num_clients
-- FROM client_profiles
-- GROUP BY risk_tier, income_bracket
-- ORDER BY risk_tier, income_bracket;

-- 5. Simple daily return calculation for one ticker (to validate before doing this in pandas)
-- SELECT
--     date,
--     ticker,
--     close,
--     close - LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS daily_change
-- FROM prices
-- WHERE ticker = 'AAPL'
-- ORDER BY date
-- LIMIT 20;
