"""
engine/data/own_db_loader.py
==============================
Data Access Layer — serves OHLCV price data from our own PostgreSQL database.

Key behaviours
--------------
- Only handles 1D (daily) timeframe — Bhavcopy is daily-only.
- Applies corporate action adjustments (splits, bonuses) to produce
  backward-adjusted prices so strategy signals are consistent.
- Dividends are NOT applied to price (no total-return adjustment) — this
  matches Yahoo Finance's default `auto_adjust=False` behaviour.
- Returns a pandas DataFrame with columns matching load_price_data() exactly:
      open, high, low, close, volume  (DatetimeIndex named 'date')
"""

import os
import logging
from datetime import date
from functools import lru_cache

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    return url.replace("postgresql+psycopg://", "postgresql://")


# ─────────────────────────────────────────────────────────────────────────────
#  Symbol alias resolution (for NSE ticker renames)
# ─────────────────────────────────────────────────────────────────────────────

def _get_all_symbols(symbol: str, conn: psycopg.Connection) -> list[str]:
    """
    Return a list containing the symbol itself plus all its old names
    from the symbol_aliases table (handles NSE ticker renames like
    ZOMATO -> ETERNAL, TATAGLOBAL -> TATACONSUM, etc.).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT old_symbol FROM symbol_aliases WHERE current_symbol = %s",
            (symbol,),
        )
        old_names = [r[0] for r in cur.fetchall()]
    return [symbol] + old_names


# ─────────────────────────────────────────────────────────────────────────────
#  Corporate action adjustment
# ─────────────────────────────────────────────────────────────────────────────

# Hardcoded overrides for massive historical demergers that are missing or
# un-computable from NSE's raw corporate actions data.
# Format: {"SYMBOL": [list of ex_dates]}
KNOWN_DEMERGERS = {
    "RELIANCE": [
        date(2006, 1, 18),  # Reliance Industries demerger (RCOM, REL, RCAP, RPIG)
        date(2023, 7, 20),  # Jio Financial Services demerger
    ]
}

def _get_adj_factors(symbols: list[str], conn: psycopg.Connection) -> pd.DataFrame:
    """
    Fetch all SPLIT and BONUS corporate actions for a list of symbols
    (current name + all old names), AND dynamically calculate explicit 
    adjustment ratios for known historical demergers.

    Returns a DataFrame with columns: ex_date, ratio
    (one row per corporate event, sorted ascending by ex_date)
    """
    placeholders = ",".join(["%s"] * len(symbols))
    with conn.cursor() as cur:
        # 1. Fetch splits & bonuses
        cur.execute(f"""
            SELECT ex_date, action_type, ratio
            FROM nse_corporate_actions
            WHERE symbol IN ({placeholders})
              AND action_type IN ('SPLIT', 'BONUS')
              AND ratio IS NOT NULL
            ORDER BY ex_date ASC
        """, symbols)
        rows = cur.fetchall()

    if not rows:
        df = pd.DataFrame(columns=["ex_date", "ratio"])
    else:
        df = pd.DataFrame(rows, columns=["ex_date", "action_type", "ratio"])
        df["ex_date"] = pd.to_datetime(df["ex_date"]).dt.date
        df["ratio"] = pd.to_numeric(df["ratio"], errors="coerce").astype(float)
        df = df.dropna(subset=["ratio"])
        df = df[["ex_date", "ratio"]]

    # 2. Inject override demergers dynamically computed from price gaps
    demerger_rows = []
    for sym in symbols:
        if sym in KNOWN_DEMERGERS:
            with conn.cursor() as cur:
                for d_date in KNOWN_DEMERGERS[sym]:
                    # Find T-1 close and T open
                    cur.execute("""
                        SELECT date, open, close 
                        FROM nse_price_data 
                        WHERE symbol = %s 
                          AND date >= %s::date - interval '10 days'
                          AND date <= %s::date
                        ORDER BY date DESC LIMIT 2
                    """, (sym, d_date, d_date))
                    p_rows = cur.fetchall()
                    # Expecting exactly 2 rows: [0] is the demerger day (T), [1] is T-1
                    if len(p_rows) == 2 and p_rows[0][0] == d_date:
                        t_open = float(p_rows[0][1])
                        t_minus_1_close = float(p_rows[1][2])
                        if t_open > 0:
                            ratio = t_minus_1_close / t_open
                            demerger_rows.append({"ex_date": d_date, "ratio": ratio})
    
    if demerger_rows:
        dem_df = pd.DataFrame(demerger_rows)
        df = pd.concat([df, dem_df], ignore_index=True)

    df["ex_date"] = pd.to_datetime(df["ex_date"])
    return df.sort_values("ex_date")


def _apply_adjustments(price_df: pd.DataFrame, adj_df: pd.DataFrame) -> pd.DataFrame:
    """
    Backward-adjust price data so that all historical prices are on the
    same scale as the most recent (current) price.

    For each price row, the adjustment divisor = product of all split/bonus
    ratios for events that occurred ON OR AFTER that price date.
    This is computed in a single vectorized pass.
    """
    if adj_df.empty:
        return price_df

    price_df = price_df.copy()

    # Build a sorted array of (ex_date, cumulative_factor_from_that_event_onwards)
    # cumulative from the LAST event backward.
    # E.g. events (2x in 1997, 2x in 2009, 2x in 2017, 2x in 2024):
    # price in 1997-10-24 needs to be divided by 2*2*2*2 = 16 (all 4 events)
    # price in 2000-01-01 needs to be divided by 2*2*2 = 8 (events after 1997)
    # price in 2010-01-01 needs to be divided by 2*2 = 4 (events after 2009)
    # price AFTER last event needs divisor 1 (no further adjustments)
    
    events = adj_df.sort_values("ex_date", ascending=False).reset_index(drop=True)
    # cumulative product from most-recent to oldest event
    events["cum_factor"] = events["ratio"].cumprod()
    
    def get_factor(date):
        # We want the cumulative factor of the OLDEST event that is > price date.
        # Since events is sorted descending, the events > date are at the top,
        # and the oldest among them is the last one in the matched subset (iloc[-1]).
        mask = events["ex_date"] > date
        if mask.any():
            return float(events.loc[mask, "cum_factor"].iloc[-1])
        return 1.0
        
    factors = price_df.index.to_series().apply(get_factor)
    
    for col in ["open", "high", "low", "close"]:
        price_df[col] = price_df[col] / factors
        
    price_df["volume"] = price_df["volume"] * factors
    return price_df



# ─────────────────────────────────────────────────────────────────────────────
#  Main public function
# ─────────────────────────────────────────────────────────────────────────────

def load_from_own_db(
    nse_symbol: str,
    start_date,
    end_date,
    adjust: bool = True,
) -> pd.DataFrame | None:
    """
    Load daily OHLCV price data from the own NSE database.

    Parameters
    ----------
    nse_symbol  : str  — raw NSE symbol, e.g. "RELIANCE", "INFY"
    start_date  : date-like
    end_date    : date-like
    adjust      : bool — apply split/bonus adjustment (default True)

    Returns
    -------
    pd.DataFrame  with DatetimeIndex (name='date') and columns:
        open, high, low, close, volume
    or None if no data found for this symbol.
    """
    nse_symbol = nse_symbol.strip().upper()
    start = pd.to_datetime(start_date).date()
    end   = pd.to_datetime(end_date).date()

    dsn = _get_dsn()

    try:
        with psycopg.connect(dsn) as conn:
            # ── Resolve all historical symbol names ────────────────────────
            all_symbols = _get_all_symbols(nse_symbol, conn)
            if len(all_symbols) > 1:
                logger.debug(f"[OwnDB] Symbol aliases for {nse_symbol}: {all_symbols}")

            # ── Fetch raw OHLCV from DB (all symbol names) ─────────────────
            placeholders = ",".join(["%s"] * len(all_symbols))
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT date, open, high, low, close, volume
                    FROM nse_price_data
                    WHERE symbol IN ({placeholders})
                      AND date BETWEEN %s AND %s
                    ORDER BY date ASC
                """, all_symbols + [start, end])
                rows = cur.fetchall()

            if not rows:
                logger.debug(f"[OwnDB] No data for {nse_symbol} in [{start}, {end}]")
                return None

            df = pd.DataFrame(
                rows,
                columns=["date", "open", "high", "low", "close", "volume"],
            )
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.index.name = "date"

            for col in ["open", "high", "low", "close"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype(float)

            # ── Apply corporate action adjustments ─────────────────────────
            if adjust:
                adj_df = _get_adj_factors(all_symbols, conn)
                df = _apply_adjustments(df, adj_df)

            logger.debug(f"[OwnDB] Loaded {len(df):,} rows for {nse_symbol}")
            return df

    except psycopg.OperationalError as e:
        logger.warning(f"[OwnDB] Connection error: {e}")
        return None
    except Exception as e:
        logger.warning(f"[OwnDB] Unexpected error for {nse_symbol}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_available_symbols() -> list[str]:
    """Return sorted list of NSE symbols that have data in our DB."""
    try:
        with psycopg.connect(_get_dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT symbol
                    FROM nse_price_data
                    ORDER BY symbol
                """)
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.warning(f"[OwnDB] Could not fetch symbols: {e}")
        return []


def get_db_coverage() -> dict:
    """Return summary statistics of the database."""
    try:
        with psycopg.connect(_get_dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(DISTINCT symbol) AS symbols,
                        COUNT(*)               AS total_rows,
                        MIN(date)              AS earliest,
                        MAX(date)              AS latest
                    FROM nse_price_data
                """)
                row = cur.fetchone()
                return {
                    "symbols": row[0],
                    "total_rows": row[1],
                    "earliest": str(row[2]),
                    "latest": str(row[3]),
                }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
#  Index data access
# ─────────────────────────────────────────────────────────────────────────────

def load_index_data(
    index_name: str,
    start_date,
    end_date,
) -> pd.DataFrame | None:
    """
    Load OHLCV data for an NSE index from the nse_index_data table.

    Parameters
    ----------
    index_name : str  — e.g. "NIFTY 50", "NIFTY BANK"
    start_date : date-like
    end_date   : date-like

    Returns
    -------
    pd.DataFrame with DatetimeIndex (name='date') and columns:
        open, high, low, close, volume
    """
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    index_name = index_name.strip().upper()

    try:
        with psycopg.connect(_get_dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT date, open, high, low, close, volume
                    FROM nse_index_data
                    WHERE index_name = %s
                      AND date >= %s
                      AND date <= %s
                    ORDER BY date ASC
                """, (index_name, start_date.date(), end_date.date()))
                rows = cur.fetchall()

        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df.sort_index()

        # Convert to float
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

        logger.debug(f"[OwnDB] Served index {index_name} ({len(df):,} rows)")
        return df

    except Exception as e:
        logger.warning(f"[OwnDB] Error loading index {index_name}: {e}")
        return None


def get_available_indices() -> list[dict]:
    """Return list of available indices with their date ranges."""
    try:
        with psycopg.connect(_get_dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT index_name,
                           COUNT(*) AS total_rows,
                           MIN(date) AS earliest,
                           MAX(date) AS latest
                    FROM nse_index_data
                    GROUP BY index_name
                    ORDER BY index_name
                """)
                rows = cur.fetchall()
                return [
                    {
                        "index_name": r[0],
                        "total_rows": r[1],
                        "earliest": str(r[2]),
                        "latest": str(r[3]),
                    }
                    for r in rows
                ]
    except Exception as e:
        logger.warning(f"[OwnDB] Could not fetch indices: {e}")
        return []

