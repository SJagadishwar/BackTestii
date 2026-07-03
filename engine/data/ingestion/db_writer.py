"""
engine/data/ingestion/db_writer.py
=====================================
Low-level helpers for writing parsed Bhavcopy DataFrames into PostgreSQL.

Uses psycopg3 (psycopg) with COPY for maximum bulk-insert speed.
"""

import os
import io
import logging
from datetime import date

import pandas as pd
import psycopg
from psycopg.copy import Copy
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    return url.replace("postgresql+psycopg://", "postgresql://")


def get_connection() -> psycopg.Connection:
    return psycopg.connect(_get_dsn())


# ─────────────────────────────────────────────────────────────────────────────
#  Price data writer
# ─────────────────────────────────────────────────────────────────────────────

def upsert_price_df(df: pd.DataFrame, conn: psycopg.Connection | None = None) -> int:
    """
    Upsert a parsed Bhavcopy DataFrame into nse_price_data.

    Uses COPY + ON CONFLICT DO UPDATE for high performance.

    Returns
    -------
    int  -- number of rows affected
    """
    if df.empty:
        return 0

    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    try:
        # Build CSV in-memory for COPY
        cols = ["symbol", "date", "open", "high", "low", "close",
                "volume", "prev_close", "trades", "deliverable_qty"]

        buf = io.StringIO()
        for _, row in df[cols].iterrows():
            parts = []
            for c in cols:
                v = row[c]
                if pd.isna(v):
                    parts.append("\\N")
                else:
                    parts.append(str(v))
            buf.write("\t".join(parts) + "\n")
        buf.seek(0)

        tmp_table = "tmp_bhav_insert"
        with conn.cursor() as cur:
            # Create temp table matching structure
            cur.execute(f"""
                CREATE TEMP TABLE IF NOT EXISTS {tmp_table} (
                    symbol VARCHAR(20),
                    date DATE,
                    open NUMERIC(14,4),
                    high NUMERIC(14,4),
                    low NUMERIC(14,4),
                    close NUMERIC(14,4),
                    volume BIGINT,
                    prev_close NUMERIC(14,4),
                    trades BIGINT,
                    deliverable_qty BIGINT
                ) ON COMMIT DROP
            """)

            # COPY into temp table
            with cur.copy(
                f"COPY {tmp_table} (symbol, date, open, high, low, close, "
                f"volume, prev_close, trades, deliverable_qty) FROM STDIN"
            ) as copy:
                copy.write(buf.read())

            # Upsert from temp → main table
            cur.execute(f"""
                INSERT INTO nse_price_data
                    (symbol, date, open, high, low, close, volume,
                     prev_close, trades, deliverable_qty)
                SELECT symbol, date, open, high, low, close, volume,
                       prev_close, trades, deliverable_qty
                FROM {tmp_table}
                ON CONFLICT (symbol, date)
                DO UPDATE SET
                    open            = EXCLUDED.open,
                    high            = EXCLUDED.high,
                    low             = EXCLUDED.low,
                    close           = EXCLUDED.close,
                    volume          = EXCLUDED.volume,
                    prev_close      = EXCLUDED.prev_close,
                    trades          = EXCLUDED.trades,
                    deliverable_qty = EXCLUDED.deliverable_qty
            """)
            count = cur.rowcount

        conn.commit()
        return count

    finally:
        if close_conn:
            conn.close()


def log_ingestion(bhavcopy_date: date, rows: int, conn: psycopg.Connection | None = None):
    """Record successful ingestion in nse_ingestion_log."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nse_ingestion_log (date, rows_loaded, loaded_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (date) DO UPDATE
                    SET rows_loaded = EXCLUDED.rows_loaded,
                        loaded_at   = NOW()
            """, (bhavcopy_date, rows))
        conn.commit()
    finally:
        if close_conn:
            conn.close()


def get_ingested_dates(conn: psycopg.Connection | None = None) -> set[date]:
    """Return the set of dates already ingested (from nse_ingestion_log)."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT date FROM nse_ingestion_log")
            return {row[0] for row in cur.fetchall()}
    finally:
        if close_conn:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  Index data writer
# ─────────────────────────────────────────────────────────────────────────────

def upsert_index_df(df: pd.DataFrame, conn: psycopg.Connection | None = None) -> int:
    """
    Upsert a parsed Index DataFrame into nse_index_data.
    Uses COPY + ON CONFLICT DO UPDATE for high performance.
    """
    if df.empty:
        return 0

    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    try:
        cols = ["index_name", "date", "open", "high", "low", "close", "volume", "turnover_cr"]

        buf = io.StringIO()
        for _, row in df[cols].iterrows():
            parts = []
            for c in cols:
                v = row[c]
                if pd.isna(v):
                    parts.append("\\N")
                else:
                    parts.append(str(v))
            buf.write("\t".join(parts) + "\n")
        buf.seek(0)

        tmp_table = "tmp_index_insert"
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TEMP TABLE IF NOT EXISTS {tmp_table} (
                    index_name VARCHAR(50),
                    date DATE,
                    open NUMERIC(14,4),
                    high NUMERIC(14,4),
                    low NUMERIC(14,4),
                    close NUMERIC(14,4),
                    volume BIGINT,
                    turnover_cr NUMERIC(14,4)
                ) ON COMMIT DROP
            """)

            with cur.copy(
                f"COPY {tmp_table} (index_name, date, open, high, low, close, "
                f"volume, turnover_cr) FROM STDIN"
            ) as copy:
                copy.write(buf.read())

            cur.execute(f"""
                INSERT INTO nse_index_data
                    (index_name, date, open, high, low, close, volume, turnover_cr)
                SELECT index_name, date, open, high, low, close, volume, turnover_cr
                FROM {tmp_table}
                ON CONFLICT (index_name, date)
                DO UPDATE SET
                    open        = EXCLUDED.open,
                    high        = EXCLUDED.high,
                    low         = EXCLUDED.low,
                    close       = EXCLUDED.close,
                    volume      = EXCLUDED.volume,
                    turnover_cr = EXCLUDED.turnover_cr
            """)
            count = cur.rowcount

        conn.commit()
        return count

    finally:
        if close_conn:
            conn.close()


def log_index_ingestion(ingestion_date: date, rows: int, conn: psycopg.Connection | None = None):
    """Record successful index ingestion in nse_index_ingestion_log."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nse_index_ingestion_log (date, rows_loaded, loaded_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (date) DO UPDATE
                    SET rows_loaded = EXCLUDED.rows_loaded,
                        loaded_at   = NOW()
            """, (ingestion_date, rows))
        conn.commit()
    finally:
        if close_conn:
            conn.close()


def get_index_ingested_dates(conn: psycopg.Connection | None = None) -> set[date]:
    """Return the set of dates already ingested for indices (from nse_index_ingestion_log)."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            # First check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'nse_index_ingestion_log'
                );
            """)
            exists = cur.fetchone()[0]
            if not exists:
                return set()
                
            cur.execute("SELECT date FROM nse_index_ingestion_log")
            return {row[0] for row in cur.fetchall()}
    finally:
        if close_conn:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  Shared helper: DataFrame → TSV in-memory buffer for COPY
# ─────────────────────────────────────────────────────────────────────────────

def _df_to_tsv(df: pd.DataFrame, cols: list[str]) -> io.StringIO:
    """Convert a DataFrame to a tab-separated in-memory buffer for COPY."""
    buf = io.StringIO()
    for _, row in df[cols].iterrows():
        parts = []
        for c in cols:
            v = row[c]
            if pd.isna(v):
                parts.append("\\N")
            else:
                parts.append(str(v))
        buf.write("\t".join(parts) + "\n")
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────────────────
#  F&O data writer (COPY-based bulk upsert)
# ─────────────────────────────────────────────────────────────────────────────

_FO_COLS = [
    "symbol", "date", "instrument", "expiry_date", "strike_price", "option_type",
    "open", "high", "low", "close", "settle_price", "underlying_close",
    "contracts", "value_in_lakh", "open_interest", "change_in_oi", "lot_size",
]

def upsert_fo_df(df: pd.DataFrame, conn: psycopg.Connection | None = None) -> int:
    """
    Bulk-upsert F&O data DataFrame into nse_fo_data using COPY + temp table.
    """
    if df.empty:
        return 0

    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    try:
        buf = _df_to_tsv(df, _FO_COLS)
        tmp_table = f"tmp_fo_insert_{os.getpid()}"

        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TEMP TABLE IF NOT EXISTS {tmp_table} (
                    symbol VARCHAR(20),
                    date DATE,
                    instrument VARCHAR(10),
                    expiry_date DATE,
                    strike_price NUMERIC(14,2),
                    option_type VARCHAR(2),
                    open NUMERIC(14,4),
                    high NUMERIC(14,4),
                    low NUMERIC(14,4),
                    close NUMERIC(14,4),
                    settle_price NUMERIC(14,4),
                    underlying_close NUMERIC(14,4),
                    contracts BIGINT,
                    value_in_lakh NUMERIC(18,4),
                    open_interest BIGINT,
                    change_in_oi BIGINT,
                    lot_size INTEGER
                ) ON COMMIT DROP
            """)

            col_list = ", ".join(_FO_COLS)
            with cur.copy(
                f"COPY {tmp_table} ({col_list}) FROM STDIN"
            ) as copy:
                copy.write(buf.read())

            cur.execute(f"""
                INSERT INTO nse_fo_data
                    ({col_list})
                SELECT {col_list}
                FROM {tmp_table}
                ON CONFLICT (symbol, date, instrument, expiry_date, strike_price, option_type)
                DO UPDATE SET
                    open             = EXCLUDED.open,
                    high             = EXCLUDED.high,
                    low              = EXCLUDED.low,
                    close            = EXCLUDED.close,
                    settle_price     = EXCLUDED.settle_price,
                    underlying_close = EXCLUDED.underlying_close,
                    contracts        = EXCLUDED.contracts,
                    value_in_lakh    = EXCLUDED.value_in_lakh,
                    open_interest    = EXCLUDED.open_interest,
                    change_in_oi     = EXCLUDED.change_in_oi,
                    lot_size         = EXCLUDED.lot_size
            """)
            count = cur.rowcount

        conn.commit()
        return count

    finally:
        if close_conn:
            conn.close()


def log_fo_ingestion(ingestion_date: date, rows: int, conn: psycopg.Connection | None = None):
    """Record successful F&O ingestion in nse_fo_ingestion_log."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nse_fo_ingestion_log (date, rows_loaded, loaded_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (date) DO UPDATE
                    SET rows_loaded = EXCLUDED.rows_loaded,
                        loaded_at   = NOW()
            """, (ingestion_date, rows))
        conn.commit()
    finally:
        if close_conn:
            conn.close()


def get_fo_ingested_dates(conn: psycopg.Connection | None = None) -> set[date]:
    """Return the set of dates already ingested for F&O."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'nse_fo_ingestion_log'
                );
            """)
            exists = cur.fetchone()[0]
            if not exists:
                return set()

            cur.execute("SELECT date FROM nse_fo_ingestion_log")
            return {row[0] for row in cur.fetchall()}
    finally:
        if close_conn:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  Instruments master writer
# ─────────────────────────────────────────────────────────────────────────────

def upsert_instruments_from_df(df: pd.DataFrame, conn: psycopg.Connection | None = None):
    """
    Upsert instrument metadata rows.

    Expected columns: symbol, isin, company_name, series, listing_date
    """
    if df.empty:
        return
    close_conn = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute("""
                    INSERT INTO nse_instruments_master
                        (symbol, isin, company_name, series, listing_date)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (symbol) DO UPDATE SET
                        isin         = EXCLUDED.isin,
                        company_name = EXCLUDED.company_name,
                        series       = EXCLUDED.series,
                        listing_date = COALESCE(EXCLUDED.listing_date,
                                                nse_instruments_master.listing_date),
                        updated_at   = NOW()
                """, (
                    str(row.get("symbol", "")).strip().upper(),
                    row.get("isin"),
                    row.get("company_name"),
                    row.get("series", "EQ"),
                    row.get("listing_date"),
                ))
        conn.commit()
    finally:
        if close_conn:
            conn.close()
