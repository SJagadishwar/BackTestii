"""
engine/data/ingestion/fo_bhavcopy_parser.py
============================================
Parses NSE F&O Bhavcopy ZIP or CSV files into a clean DataFrame.

NSE F&O Bhavcopy formats handled
----------------------------------
1. Legacy (~2016 - July 2024):
   Columns: INSTRUMENT, SYMBOL, EXPIRY_DT, STRIKE_PR, OPTION_TYP,
            OPEN, HIGH, LOW, CLOSE, SETTLE_PR, CONTRACTS, VAL_INLAKH,
            OPEN_INT, CHG_IN_OI, TIMESTAMP

2. New UDiFF format (July 2024 onwards):
   Columns: FinInstrmTp, TckrSymb, XpryDt, StrkPric, OptnTp,
            OpnPric, HghPric, LwPric, ClsPric, SttlmPric, UndrlygPric,
            OpnIntrst, ChngInOpnIntrst, TtlTradgVol, TtlTrfVal, NewBrdLotQty

All normalised to: symbol, date, instrument, expiry_date, strike_price,
    option_type, open, high, low, close, settle_price, underlying_close,
    contracts, value_in_lakh, open_interest, change_in_oi, lot_size
"""

import io
import re
import zipfile
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# ── Instrument type normalisation ────────────────────────────────────────────
# UDiFF uses short codes (STF/STO/IDF/IDO), legacy uses long names.
# We normalise everything to the short UDiFF codes.
INSTRUMENT_MAP = {
    "FUTSTK": "STF",
    "OPTSTK": "STO",
    "FUTIDX": "IDF",
    "OPTIDX": "IDO",
    # UDiFF codes map to themselves
    "STF": "STF",
    "STO": "STO",
    "IDF": "IDF",
    "IDO": "IDO",
}

# Valid F&O instrument types (after normalisation)
VALID_INSTRUMENTS = {"STF", "STO", "IDF", "IDO"}


def _detect_fo_format(df: pd.DataFrame) -> str:
    """Return 'legacy' or 'udiff' based on column names."""
    cols = set(df.columns)
    if "INSTRUMENT" in cols and "SYMBOL" in cols and "STRIKE_PR" in cols:
        return "legacy"
    if "FinInstrmTp" in cols and "TckrSymb" in cols:
        return "udiff"
    return "unknown"


def _parse_legacy_fo(df: pd.DataFrame) -> pd.DataFrame:
    """Parse legacy F&O bhavcopy format."""
    col_map = {
        "INSTRUMENT":   "instrument",
        "SYMBOL":       "symbol",
        "EXPIRY_DT":    "expiry_date_str",
        "STRIKE_PR":    "strike_price",
        "OPTION_TYP":   "option_type",
        "OPEN":         "open",
        "HIGH":         "high",
        "LOW":          "low",
        "CLOSE":        "close",
        "SETTLE_PR":    "settle_price",
        "CONTRACTS":    "contracts",
        "VAL_INLAKH":   "value_in_lakh",
        "OPEN_INT":     "open_interest",
        "CHG_IN_OI":    "change_in_oi",
        "TIMESTAMP":    "date_str",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Parse dates
    if "date_str" in df.columns:
        df["date"] = pd.to_datetime(df["date_str"], dayfirst=True, errors="coerce")
    else:
        df["date"] = pd.NaT

    if "expiry_date_str" in df.columns:
        df["expiry_date"] = pd.to_datetime(df["expiry_date_str"], dayfirst=True, errors="coerce")
    else:
        df["expiry_date"] = pd.NaT

    # Legacy format does NOT have underlying_close or lot_size
    df["underlying_close"] = None
    df["lot_size"] = None

    return df


def _parse_udiff_fo(df: pd.DataFrame) -> pd.DataFrame:
    """Parse UDiFF F&O bhavcopy format."""
    col_map = {
        "FinInstrmTp":      "instrument",
        "TckrSymb":         "symbol",
        "XpryDt":           "expiry_date_str",
        "StrkPric":         "strike_price",
        "OptnTp":           "option_type",
        "OpnPric":          "open",
        "HghPric":          "high",
        "LwPric":           "low",
        "ClsPric":          "close",
        "SttlmPric":        "settle_price",
        "UndrlygPric":      "underlying_close",
        "TtlTradgVol":      "contracts",
        "TtlTrfVal":        "value_in_lakh",  # Actually in full value, will convert
        "OpnIntrst":        "open_interest",
        "ChngInOpnIntrst":  "change_in_oi",
        "TradDt":           "date_str",
        "NewBrdLotQty":     "lot_size",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Parse dates
    if "date_str" in df.columns:
        df["date"] = pd.to_datetime(df["date_str"], errors="coerce")
    else:
        df["date"] = pd.NaT

    if "expiry_date_str" in df.columns:
        df["expiry_date"] = pd.to_datetime(df["expiry_date_str"], errors="coerce")
    else:
        df["expiry_date"] = pd.NaT

    # UDiFF TtlTrfVal is in full INR, convert to lakhs for consistency
    if "value_in_lakh" in df.columns:
        df["value_in_lakh"] = pd.to_numeric(df["value_in_lakh"], errors="coerce") / 100000

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
                for enc in ("utf-8", "latin-1"):
                    try:
                        return pd.read_csv(io.BytesIO(raw), encoding=enc)
                    except Exception:
                        continue
    except Exception as e:
        logger.error(f"Failed to open zip: {e}")
    return None


def _finalise_fo(df: pd.DataFrame, bhavcopy_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Common cleanup for F&O data after format-specific parsing."""

    # Fill missing dates from bhavcopy_date
    if "date" not in df.columns:
        df["date"] = pd.NaT
    if bhavcopy_date is not None:
        df["date"] = df["date"].fillna(bhavcopy_date)

    df = df[df["date"].notna()].copy()

    # Normalise instrument type
    if "instrument" in df.columns:
        df["instrument"] = df["instrument"].astype(str).str.strip().str.upper()
        df["instrument"] = df["instrument"].map(INSTRUMENT_MAP)
        # Only keep valid F&O instruments
        df = df[df["instrument"].isin(VALID_INSTRUMENTS)]

    # Clean symbol
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()

    # Clean option_type: CE, PE, or XX for futures
    if "option_type" in df.columns:
        df["option_type"] = df["option_type"].astype(str).str.strip().str.upper()
        # Futures have NaN or '-' or 'XX' for option_type
        df["option_type"] = df["option_type"].replace({"NAN": "XX", "-": "XX", "": "XX", "NONE": "XX"})
        df["option_type"] = df["option_type"].fillna("XX")
    else:
        df["option_type"] = "XX"

    # Ensure numeric columns
    num_cols = ["open", "high", "low", "close", "settle_price", "underlying_close",
                "strike_price", "contracts", "value_in_lakh", "open_interest", "change_in_oi", "lot_size"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = None

    # Default strike_price to 0 for futures
    df["strike_price"] = df["strike_price"].fillna(0)

    # Drop rows missing critical data
    df = df.dropna(subset=["symbol", "date", "instrument", "expiry_date"])

    # Deduplicate
    df = df.drop_duplicates(
        subset=["symbol", "date", "instrument", "expiry_date", "strike_price", "option_type"],
        keep="first"
    )

    out_cols = [
        "symbol", "date", "instrument", "expiry_date", "strike_price", "option_type",
        "open", "high", "low", "close", "settle_price", "underlying_close",
        "contracts", "value_in_lakh", "open_interest", "change_in_oi", "lot_size",
    ]
    return df[out_cols].reset_index(drop=True)


def parse_fo_bhavcopy_bytes(
    data: bytes,
    bhavcopy_date: pd.Timestamp | None = None,
    is_zip: bool | None = None,
) -> pd.DataFrame:
    """
    Parse F&O Bhavcopy raw bytes (zip or CSV).

    Returns
    -------
    pd.DataFrame with columns:
        symbol, date, instrument, expiry_date, strike_price, option_type,
        open, high, low, close, settle_price, underlying_close,
        contracts, value_in_lakh, open_interest, change_in_oi, lot_size
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

    fmt = _detect_fo_format(raw_df)
    if fmt == "legacy":
        df = _parse_legacy_fo(raw_df)
    elif fmt == "udiff":
        df = _parse_udiff_fo(raw_df)
    else:
        logger.warning(f"Unknown F&O Bhavcopy format. Columns: {list(raw_df.columns)}")
        return pd.DataFrame()

    return _finalise_fo(df, bhavcopy_date)


def parse_fo_bhavcopy_file(path: str | Path) -> pd.DataFrame:
    """Convenience wrapper: parse an F&O Bhavcopy file from disk."""
    path = Path(path)
    data = path.read_bytes()

    # Try to extract date from filename
    bhavcopy_date = None
    m = re.search(r"(\d{2})([A-Z]{3})(\d{4})", path.name.upper())
    if m:
        bhavcopy_date = pd.to_datetime(f"{m.group(1)}-{m.group(2)}-{m.group(3)}", format="%d-%b-%Y", errors="coerce")

    if bhavcopy_date is None:
        m2 = re.search(r"(\d{4})[_\-]?(\d{2})[_\-]?(\d{2})", path.name)
        if m2:
            bhavcopy_date = pd.to_datetime(f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}", errors="coerce")

    is_zip = path.suffix.lower() == ".zip" or data[:4] == b"PK\x03\x04"
    return parse_fo_bhavcopy_bytes(data, bhavcopy_date, is_zip=is_zip)
