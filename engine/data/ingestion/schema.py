"""
engine/data/ingestion/schema.py
================================
Creates (or verifies) the NSE price database tables in the existing
PostgreSQL database (equitylab_auth).

Run once:
    python -m engine.data.ingestion.schema

Tables created
--------------
nse_price_data          -- raw OHLCV per symbol per date (EQ series only)
nse_corporate_actions   -- splits, bonuses, dividends (for adj-close calc)
nse_instruments_master  -- symbol metadata (ISIN, listing date, etc.)
"""

import os
import sys
import psycopg
from dotenv import load_dotenv

load_dotenv()


def _get_raw_dsn() -> str:
    """Convert SQLAlchemy URL to psycopg3 DSN."""
    url = os.getenv("DATABASE_URL", "")
    # Strip the SQLAlchemy driver prefix
    return url.replace("postgresql+psycopg://", "postgresql://")


DDL = """
-- ─────────────────────────────────────────────────────────────────────────────
-- 1.  NSE Instruments Master
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nse_instruments_master (
    symbol          VARCHAR(20)  PRIMARY KEY,
    isin            VARCHAR(12),
    company_name    VARCHAR(300),
    series          VARCHAR(5)   DEFAULT 'EQ',
    listing_date    DATE,
    updated_at      TIMESTAMP    DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2.  NSE Daily Price Data  (EQ series Bhavcopy)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nse_price_data (
    id          BIGSERIAL    PRIMARY KEY,
    symbol      VARCHAR(20)  NOT NULL,
    date        DATE         NOT NULL,
    open        NUMERIC(14,4),
    high        NUMERIC(14,4),
    low         NUMERIC(14,4),
    close       NUMERIC(14,4),
    volume      BIGINT,
    -- Bhavcopy extras (useful for later analysis)
    prev_close  NUMERIC(14,4),
    trades      BIGINT,
    deliverable_qty BIGINT,
    CONSTRAINT nse_price_data_uk UNIQUE (symbol, date)
);

CREATE INDEX IF NOT EXISTS idx_nse_price_symbol_date
    ON nse_price_data (symbol, date DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3.  Corporate Actions  (splits, bonuses, dividends)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nse_corporate_actions (
    id          SERIAL       PRIMARY KEY,
    symbol      VARCHAR(20)  NOT NULL,
    ex_date     DATE         NOT NULL,
    action_type VARCHAR(20)  NOT NULL,   -- SPLIT | BONUS | DIVIDEND
    -- For SPLIT: ratio = old_face / new_face  (e.g. 10→2 = 5.0)
    -- For BONUS: ratio = total_shares_after / shares_before (1:1 bonus = 2.0)
    -- For DIVIDEND: amount in INR per share
    ratio       NUMERIC(12,6),
    amount      NUMERIC(12,4),
    remarks     TEXT,
    CONSTRAINT nse_ca_uk UNIQUE (symbol, ex_date, action_type)
);

CREATE INDEX IF NOT EXISTS idx_nse_ca_symbol
    ON nse_corporate_actions (symbol, ex_date DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4.  NSE Index Data  (Broad-based / Sectoral / Thematic indices)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nse_index_data (
    id          BIGSERIAL    PRIMARY KEY,
    index_name  VARCHAR(50)  NOT NULL,
    date        DATE         NOT NULL,
    open        NUMERIC(14,4),
    high        NUMERIC(14,4),
    low         NUMERIC(14,4),
    close       NUMERIC(14,4) NOT NULL,
    volume      BIGINT,
    turnover_cr NUMERIC(14,4),
    CONSTRAINT nse_index_data_uk UNIQUE (index_name, date)
);

CREATE INDEX IF NOT EXISTS idx_nse_index_name_date
    ON nse_index_data (index_name, date DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 5.  Ingestion progress tracker  (so bulk_load can resume safely)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nse_ingestion_log (
    date        DATE    PRIMARY KEY,
    rows_loaded INTEGER,
    loaded_at   TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS nse_index_ingestion_log (
    date        DATE    PRIMARY KEY,
    rows_loaded INTEGER,
    loaded_at   TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 6.  NSE F&O Data  (Futures & Options daily contract data)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nse_fo_data (
    id                  BIGSERIAL       PRIMARY KEY,
    symbol              VARCHAR(20)     NOT NULL,          -- Underlying symbol (RELIANCE, NIFTY, etc.)
    date                DATE            NOT NULL,          -- Trading date
    instrument          VARCHAR(10)     NOT NULL,          -- STF/STO/IDF/IDO (or legacy FUTSTK/OPTSTK/FUTIDX/OPTIDX)
    expiry_date         DATE            NOT NULL,          -- Contract expiry
    strike_price        NUMERIC(14,2)   DEFAULT 0,         -- Strike price (0 for futures)
    option_type         VARCHAR(2)      NOT NULL,          -- CE / PE / XX (XX = futures)
    open                NUMERIC(14,4),
    high                NUMERIC(14,4),
    low                 NUMERIC(14,4),
    close               NUMERIC(14,4),
    settle_price        NUMERIC(14,4),
    underlying_close    NUMERIC(14,4),                     -- Underlying asset closing price
    contracts           BIGINT,                            -- Number of contracts traded
    value_in_lakh       NUMERIC(18,4),                     -- Traded value in lakhs
    open_interest       BIGINT,                            -- Open Interest
    change_in_oi        BIGINT,                            -- Change in OI
    lot_size            INTEGER,                           -- Contract lot size
    CONSTRAINT nse_fo_data_uk UNIQUE (symbol, date, instrument, expiry_date, strike_price, option_type)
);

CREATE INDEX IF NOT EXISTS idx_fo_symbol_date
    ON nse_fo_data (symbol, date DESC);
CREATE INDEX IF NOT EXISTS idx_fo_expiry
    ON nse_fo_data (expiry_date);
CREATE INDEX IF NOT EXISTS idx_fo_instrument
    ON nse_fo_data (instrument, symbol, date DESC);
CREATE INDEX IF NOT EXISTS idx_fo_option_chain
    ON nse_fo_data (symbol, expiry_date, strike_price, option_type);

-- ─────────────────────────────────────────────────────────────────────────────
-- 7.  F&O ingestion progress tracker
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nse_fo_ingestion_log (
    date        DATE    PRIMARY KEY,
    rows_loaded INTEGER,
    loaded_at   TIMESTAMP DEFAULT NOW()
);
"""


def create_schema():
    dsn = _get_raw_dsn()
    print("[schema] Connecting to PostgreSQL …")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
        conn.commit()
    print("[schema] ✅ All tables created / verified.")


if __name__ == "__main__":
    create_schema()
