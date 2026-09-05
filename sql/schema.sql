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

-- Exploratory / sanity-check queries live in sql/queries.sql
-- (date range, avg close, client tiers, income cross-tab, AAPL LAG returns).
