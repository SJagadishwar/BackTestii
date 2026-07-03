"""
engine/data/data_loader.py
===========================
Public API for loading OHLCV price data.

Data Source (controlled by DATA_SOURCE env var):
  "yahoo"  — Yahoo Finance via yfinance (default). All timeframes supported.
  "own_db" — Own PostgreSQL database (NSE Bhavcopy). 1D only.
"""

import logging
import os

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ================= TIMEFRAME CONFIG =================
TIMEFRAME_MAP = {
    "1D":  {"interval": "1d",   "max_days": None},
    "1H":  {"interval": "60m",  "max_days": 730},
    "30m": {"interval": "30m",  "max_days": 60},
    "15m": {"interval": "15m",  "max_days": 60},
    "5m":  {"interval": "5m",   "max_days": 60},
}

# ================= CONFIG ===========================

DATA_SOURCE = os.getenv("DATA_SOURCE", "yahoo").strip().lower()

# ================= HELPERS ==========================

def _strip_exchange_suffix(ticker: str) -> str:
    """'RELIANCE.NS' → 'RELIANCE',  'INFY.BO' → 'INFY'"""
    return ticker.split(".")[0].strip().upper()


# ================= PUBLIC API =======================

def load_price_data(ticker, start_date, end_date, timeframe="1D") -> pd.DataFrame:
    """
    Load OHLCV price data for a given ticker and date range.

    Parameters
    ----------
    ticker     : str   — Yahoo Finance symbol, e.g. "RELIANCE.NS"
    start_date : date-like
    end_date   : date-like
    timeframe  : str   — "1D" | "1H" | "30m" | "15m" | "5m"

    Returns
    -------
    pd.DataFrame  with DatetimeIndex (name='date') and columns:
        open, high, low, close, volume
    """
    if timeframe not in TIMEFRAME_MAP:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    cfg = TIMEFRAME_MAP[timeframe]
    start_date = pd.to_datetime(start_date)
    end_date   = pd.to_datetime(end_date)

    if cfg["max_days"] is not None:
        delta_days = (end_date - start_date).days
        if delta_days > cfg["max_days"]:
            raise ValueError(
                f"{timeframe} data is limited to {cfg['max_days']} days "
                f"due to Yahoo Finance restrictions."
            )

    # ── Route based on DATA_SOURCE ─────────────────────────────────
    if DATA_SOURCE == "own_db":
        return _load_from_own_db(ticker, start_date, end_date, timeframe)
    else:
        return _load_from_yahoo(ticker, start_date, end_date, cfg["interval"])


def _load_from_yahoo(ticker, start_date, end_date, interval) -> pd.DataFrame:
    """Fetch OHLCV from Yahoo Finance."""
    from .yahoo_loader import load_from_yahoo

    df = load_from_yahoo(ticker, start_date, end_date, interval=interval)
    if df is not None and not df.empty:
        logger.debug(f"[DataLoader] Served {ticker} from Yahoo ({len(df):,} rows)")
        required = {"open", "high", "low", "close", "volume"}
        if required.issubset(df.columns):
            return df[list(required | (set(df.columns) - required))]
        else:
            raise ValueError(f"Required columns missing from Yahoo for {ticker}")
    else:
        raise ValueError(f"No data returned for ticker: {ticker}")


def _load_from_own_db(ticker, start_date, end_date, timeframe) -> pd.DataFrame:
    """Fetch OHLCV from own PostgreSQL database (1D only)."""
    if timeframe != "1D":
        raise ValueError("Only 1D timeframe is supported by the internal database.")

    from .own_db_loader import load_from_own_db

    nse_symbol = _strip_exchange_suffix(ticker)
    try:
        df = load_from_own_db(nse_symbol, start_date, end_date, adjust=True)
        if df is not None and not df.empty:
            logger.debug(f"[DataLoader] Served {nse_symbol} from own DB ({len(df):,} rows)")
            required = {"open", "high", "low", "close", "volume"}
            if required.issubset(df.columns):
                return df[list(required | (set(df.columns) - required))]
            else:
                raise ValueError(f"Required columns missing in DB for {ticker}")
        else:
            raise ValueError(f"No data returned for ticker: {ticker}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[DataLoader] Own DB error for {ticker}: {e}")
        raise ValueError(f"No data returned for ticker: {ticker}")


# ================= INDEX DATA API =======================

def load_index_data(index_name: str, start_date, end_date) -> pd.DataFrame | None:
    """
    Load OHLCV data for an index, routing based on DATA_SOURCE.

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
    if DATA_SOURCE == "own_db":
        from .own_db_loader import load_index_data as _load_index_own_db
        return _load_index_own_db(index_name, start_date, end_date)
    else:
        from .yahoo_index_loader import load_index_from_yahoo
        return load_index_from_yahoo(index_name, start_date, end_date)


def get_available_indices() -> list[dict]:
    """
    Return list of available indices, routing based on DATA_SOURCE.
    """
    if DATA_SOURCE == "own_db":
        from .own_db_loader import get_available_indices as _get_indices_own_db
        return _get_indices_own_db()
    else:
        from .yahoo_index_loader import get_available_indices_yahoo
        return get_available_indices_yahoo()


__all__ = ["TIMEFRAME_MAP", "load_price_data", "load_index_data", "get_available_indices"]
