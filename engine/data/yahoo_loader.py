"""
engine/data/yahoo_loader.py
==============================
Data loader — fetches OHLCV price data from Yahoo Finance via yfinance.

Key behaviours
--------------
- Supports all timeframes: 1d, 60m, 30m, 15m, 5m.
- Returns auto-adjusted prices (splits & dividends handled by Yahoo).
- Returns a pandas DataFrame with DatetimeIndex (name='date') and columns:
      open, high, low, close, volume
"""

import logging
from datetime import timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def load_from_yahoo(
    ticker: str,
    start_date,
    end_date,
    interval: str = "1d",
) -> pd.DataFrame | None:
    """
    Download OHLCV data from Yahoo Finance.

    Parameters
    ----------
    ticker    : str   — Yahoo Finance symbol, e.g. "RELIANCE.NS"
    start_date: date-like
    end_date  : date-like
    interval  : str   — "1d" | "60m" | "30m" | "15m" | "5m"

    Returns
    -------
    pd.DataFrame with DatetimeIndex (name='date') and columns:
        open, high, low, close, volume
    or None if no data found.
    """
    ticker = ticker.strip()
    start = pd.to_datetime(start_date)
    # yfinance end_date is exclusive, so add one day for daily data
    end = pd.to_datetime(end_date) + timedelta(days=1)

    try:
        logger.debug(f"[Yahoo] Downloading {ticker} ({interval}) [{start.date()} → {end.date()}]")

        df = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            logger.warning(f"[Yahoo] No data returned for {ticker}")
            return None

        # yfinance may return MultiIndex columns for single ticker — flatten
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Normalise column names to lowercase
        df.columns = [c.lower() for c in df.columns]

        # Ensure required columns exist
        required = {"open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns):
            logger.warning(f"[Yahoo] Missing columns for {ticker}: {required - set(df.columns)}")
            return None

        # Keep only the columns we need
        df = df[["open", "high", "low", "close", "volume"]].copy()

        # Ensure numeric types
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype(float)

        # Set index name
        df.index.name = "date"

        # For daily data, ensure the index is date-only (no timezone)
        if interval == "1d":
            df.index = pd.to_datetime(df.index).tz_localize(None)

        logger.debug(f"[Yahoo] Loaded {len(df):,} rows for {ticker}")
        return df

    except Exception as e:
        logger.error(f"[Yahoo] Error downloading {ticker}: {e}")
        return None
