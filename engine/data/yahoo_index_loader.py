"""
engine/data/yahoo_index_loader.py
===================================
Data loader — fetches index OHLCV data from Yahoo Finance via yfinance.

Maps known Indian index names (e.g. "NIFTY 50") to their Yahoo Finance
ticker symbols (e.g. "^NSEI") and downloads data.

This module is the Yahoo counterpart of the index-related functions in
own_db_loader.py.  It is used when DATA_SOURCE=yahoo.
"""

import logging
from datetime import timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Index name → Yahoo ticker mapping
# ─────────────────────────────────────────────────────────────────────────────

INDEX_YAHOO_MAP: dict[str, str] = {
    # NSE Broad Market
    "NIFTY 50":                "^NSEI",
    "NIFTY NEXT 50":           "^NSMIDCP50",
    "NIFTY 100":               "^CNX100",
    "NIFTY 200":               "^CNX200",
    "NIFTY 500":               "^CRSLDX",
    "NIFTY MIDCAP 50":         "^NSEMDCP50",
    "NIFTY MIDCAP 100":        "NIFTY_MIDCAP_100.NS",
    "NIFTY SMALLCAP 100":      "^CNXSC",

    # NSE Sectoral
    "NIFTY BANK":              "^NSEBANK",
    "NIFTY IT":                "^CNXIT",
    "NIFTY FINANCIAL SERVICES": "NIFTY_FIN_SERVICE.NS",
    "NIFTY AUTO":              "^CNXAUTO",
    "NIFTY PHARMA":            "^CNXPHARMA",
    "NIFTY FMCG":              "^CNXFMCG",
    "NIFTY METAL":             "^CNXMETAL",
    "NIFTY REALTY":            "^CNXREALTY",
    "NIFTY ENERGY":            "^CNXENERGY",
    "NIFTY INFRASTRUCTURE":    "^CNXINFRA",
    "NIFTY PSE":               "^CNXPSE",
    "NIFTY MEDIA":             "^CNXMEDIA",
    "NIFTY PRIVATE BANK":      "NIFTY_PVT_BANK.NS",
    "NIFTY PSU BANK":          "^CNXPSUBANK",
    "NIFTY COMMODITIES":       "^CNXCMDT",
    "NIFTY CONSUMPTION":       "^CNXCONSUM",
    "NIFTY CPSE":              "^CNXCPSE",
    "NIFTY FIN SERVICE":       "NIFTY_FIN_SERVICE.NS",
    "NIFTY HEALTHCARE":        "NIFTY_HEALTHCARE.NS",
    "NIFTY OIL AND GAS":       "NIFTY_OIL_AND_GAS.NS",

    # BSE
    "SENSEX":                  "^BSESN",
    "BSE SENSEX":              "^BSESN",
}

# Reverse map for quick lookup
_YAHOO_TO_INDEX = {v: k for k, v in INDEX_YAHOO_MAP.items()}


def _resolve_yahoo_ticker(index_name: str) -> str | None:
    """Resolve an index name to a Yahoo Finance ticker symbol."""
    name = index_name.strip().upper()
    return INDEX_YAHOO_MAP.get(name)


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_index_from_yahoo(
    index_name: str,
    start_date,
    end_date,
) -> pd.DataFrame | None:
    """
    Download OHLCV data for an Indian index from Yahoo Finance.

    Parameters
    ----------
    index_name : str  — e.g. "NIFTY 50", "NIFTY BANK", "SENSEX"
    start_date : date-like
    end_date   : date-like

    Returns
    -------
    pd.DataFrame with DatetimeIndex (name='date') and columns:
        open, high, low, close, volume
    or None if no data found.
    """
    yahoo_ticker = _resolve_yahoo_ticker(index_name)
    if yahoo_ticker is None:
        logger.warning(f"[YahooIndex] Unknown index: {index_name}")
        return None

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date) + timedelta(days=1)  # yfinance end is exclusive

    try:
        logger.debug(
            f"[YahooIndex] Downloading {index_name} ({yahoo_ticker}) "
            f"[{start.date()} → {end.date()}]"
        )

        df = yf.download(
            yahoo_ticker,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            logger.warning(f"[YahooIndex] No data returned for {index_name}")
            return None

        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [c.lower() for c in df.columns]

        required = {"open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns):
            logger.warning(
                f"[YahooIndex] Missing columns for {index_name}: "
                f"{required - set(df.columns)}"
            )
            return None

        df = df[["open", "high", "low", "close", "volume"]].copy()

        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype(float)

        df.index.name = "date"
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.sort_index()

        logger.debug(f"[YahooIndex] Loaded {len(df):,} rows for {index_name}")
        return df

    except Exception as e:
        logger.error(f"[YahooIndex] Error downloading {index_name}: {e}")
        return None


def get_available_indices_yahoo() -> list[dict]:
    """
    Return list of indices available via Yahoo Finance.

    Returns the same format as own_db_loader.get_available_indices():
    [{"index_name": str, "total_rows": int, "earliest": str, "latest": str}]

    Since we don't have pre-computed coverage stats from Yahoo, we return
    placeholder values indicating Yahoo is the source.
    """
    results = []
    for name, ticker in INDEX_YAHOO_MAP.items():
        # Avoid duplicates (e.g. "SENSEX" and "BSE SENSEX" both map to ^BSESN)
        if any(r["index_name"] == name for r in results):
            continue
        results.append({
            "index_name": name,
            "yahoo_ticker": ticker,
            "total_rows": None,       # Unknown until fetched
            "earliest": "2000-01-01", # Yahoo generally has data from ~2000
            "latest": "present",
            "source": "yahoo",
        })
    return sorted(results, key=lambda x: x["index_name"])
