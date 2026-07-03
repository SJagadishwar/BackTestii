"""
engine/data/ingestion/bhavcopy_parser.py
=========================================
Parses NSE CM Bhavcopy ZIP or CSV files into a clean OHLCV DataFrame.

NSE Bhavcopy formats handled
-----------------------------
1. Pre-2019 (legacy)  : cm{DD}{MMM}{YYYY}bhav.csv inside a zip
2. Post-2019 (new)    : sec_bhavdata_final_{YYYY-MM-DD}.csv (no zip in some years)
3. New UDiFF format   : BhavCopy_NSE_CM_0_0_0_{YYYY}{MM}{DD}_F_0000.csv.zip

All normalised to columns: symbol, date, open, high, low, close, volume,
                           prev_close, trades, deliverable_qty
"""

import io
import re
import zipfile
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# ── Column name mappings for different Bhavcopy CSV formats ──────────────────

# Legacy format (until ~2019/2020)
_LEGACY_COLS = {
    "SYMBOL":    "symbol",
    "SERIES":    "series",
    "OPEN":      "open",
    "HIGH":      "high",
    "LOW":       "low",
    "CLOSE":     "close",
    "LAST":      "last",
    "PREVCLOSE": "prev_close",
    "TOTTRDQTY": "volume",
    "TOTTRDVAL": "turnover",
    "TIMESTAMP": "date_str",
    "TOTALTRADES": "trades",
    "ISIN":      "isin",
}

# New UDiFF format (post-2020 approx.)
_UDIFF_COLS = {
    "TradDt":       "date_str",
    "Sgmt":         "segment",
    "Src":          "source",
    "FinInstrmTp":  "inst_type",
    "TckrSymb":     "symbol",
    "ISIN":         "isin",
    "SctySrs":      "series",
    "OpnPric":      "open",
    "HghPric":      "high",
    "LwPric":       "low",
    "ClsPric":      "close",
    "LastPric":     "last",
    "PrvsClsgPric": "prev_close",
    "TtlTradgVol":  "volume",
    "TtlTrfVal":    "turnover",
    "TtlNbOfTxsExctd": "trades",
    "DlvryQty":     "deliverable_qty",
}


def _detect_format(df: pd.DataFrame) -> str:
    """Return 'legacy' or 'udiff' based on column names."""
    cols = set(df.columns)
    if "SYMBOL" in cols and "TOTTRDQTY" in cols:
        return "legacy"
    if "TckrSymb" in cols or "FinInstrmId" in cols:
        return "udiff"
    return "unknown"


def _parse_legacy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=_LEGACY_COLS)

    # Keep EQ series only
    if "series" in df.columns:
        df = df[df["series"].str.strip().str.upper() == "EQ"]

    # Parse date
    if "date_str" in df.columns:
        df["date"] = pd.to_datetime(df["date_str"], dayfirst=True, errors="coerce")
    else:
        df["date"] = pd.NaT

    return df


def _parse_udiff(df: pd.DataFrame) -> pd.DataFrame:
    # Rename all known columns
    df = df.rename(columns={k: v for k, v in _UDIFF_COLS.items() if k in df.columns})

    # symbol: prefer TckrSymb; already renamed
    if "symbol" not in df.columns and "isin" in df.columns:
        df["symbol"] = df["isin"]

    # Keep EQ series
    if "series" in df.columns:
        df = df[df["series"].str.strip().str.upper() == "EQ"]
    elif "inst_type" in df.columns:
        df = df[df["inst_type"].str.strip().str.upper().isin(["EQ", "ES"])]

    # Parse date
    if "date_str" in df.columns:
        df["date"] = pd.to_datetime(df["date_str"], errors="coerce")
    else:
        df["date"] = pd.NaT

    return df


def _extract_csv_from_zip(zip_bytes: bytes) -> pd.DataFrame | None:
    """Open zip bytes, find the first CSV inside, return as DataFrame."""
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                logger.warning("No CSV found inside zip")
                return None
            with zf.open(csv_names[0]) as f:
                raw = f.read()
                # Try UTF-8 then latin-1
                for enc in ("utf-8", "latin-1"):
                    try:
                        return pd.read_csv(io.BytesIO(raw), encoding=enc)
                    except Exception:
                        continue
    except Exception as e:
        logger.error(f"Failed to open zip: {e}")
    return None


def _finalise(df: pd.DataFrame, bhavcopy_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Common cleanup applied after format-specific parsing."""

    # Drop rows with no date; fill from filename date if available
    if "date" not in df.columns:
        df["date"] = pd.NaT

    if bhavcopy_date is not None:
        df["date"] = df["date"].fillna(bhavcopy_date)

    df = df[df["date"].notna()].copy()

    # Ensure numeric columns
    for col in ["open", "high", "low", "close", "volume", "prev_close", "trades", "deliverable_qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = None

    # Clean symbol
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()

    # Drop rows missing critical data
    df = df.dropna(subset=["symbol", "date", "close"])
    df = df[df["close"] > 0]

    # Deduplicate (keep first occurrence per symbol/date)
    df = df.drop_duplicates(subset=["symbol", "date"], keep="first")

    return df[[
        "symbol", "date", "open", "high", "low", "close",
        "volume", "prev_close", "trades", "deliverable_qty",
    ]].reset_index(drop=True)


def parse_bhavcopy_bytes(
    data: bytes,
    bhavcopy_date: pd.Timestamp | None = None,
    is_zip: bool | None = None,
) -> pd.DataFrame:
    """
    Parse Bhavcopy raw bytes (zip or CSV).

    Parameters
    ----------
    data : bytes
        Raw file contents (zip or CSV).
    bhavcopy_date : pd.Timestamp, optional
        Date inferred from filename, used as fallback if CSV has no date col.
    is_zip : bool, optional
        If None, auto-detect by checking for PK magic bytes.

    Returns
    -------
    pd.DataFrame  with columns:
        symbol, date, open, high, low, close, volume,
        prev_close, trades, deliverable_qty
    """
    # Auto-detect zip
    if is_zip is None:
        is_zip = data[:4] == b"PK\x03\x04"

    if is_zip:
        raw_df = _extract_csv_from_zip(data)
        if raw_df is None:
            return pd.DataFrame()
    else:
        for enc in ("utf-8", "latin-1"):
            try:
                raw_df = pd.read_csv(io.StringIO(data.decode(enc)))
                break
            except Exception:
                continue
        else:
            return pd.DataFrame()

    fmt = _detect_format(raw_df)
    if fmt == "legacy":
        df = _parse_legacy(raw_df)
    elif fmt == "udiff":
        df = _parse_udiff(raw_df)
    else:
        logger.warning(f"Unknown Bhavcopy format. Columns: {list(raw_df.columns)}")
        return pd.DataFrame()

    return _finalise(df, bhavcopy_date)


def parse_bhavcopy_file(path: str | Path) -> pd.DataFrame:
    """
    Convenience wrapper: parse a Bhavcopy file on disk (zip or CSV).

    Date is inferred from the filename if possible.
    """
    path = Path(path)
    data = path.read_bytes()

    # Try to extract date from filename patterns:
    #   cm07MAR2024bhav.csv.zip  OR  2024-03-07.zip  etc.
    bhavcopy_date = None
    m = re.search(r"(\d{2})([A-Z]{3})(\d{4})", path.name.upper())
    if m:
        bhavcopy_date = pd.to_datetime(f"{m.group(1)}-{m.group(2)}-{m.group(3)}", format="%d-%b-%Y", errors="coerce")

    if bhavcopy_date is None:
        m2 = re.search(r"(\d{4})[_\-]?(\d{2})[_\-]?(\d{2})", path.name)
        if m2:
            bhavcopy_date = pd.to_datetime(f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}", errors="coerce")

    return parse_bhavcopy_bytes(data, bhavcopy_date, is_zip=path.suffix.lower() == ".zip")
