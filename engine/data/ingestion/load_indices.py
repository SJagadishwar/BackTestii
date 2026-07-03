"""
engine/data/ingestion/load_indices.py
=======================================
Bulk-load historical NSE Index data from CSV files into the
`nse_index_data` PostgreSQL table.

Handles two CSV formats:
  Format A — Nifty 50 yearly CSVs  (Date, Open, High, Low, Close, ...)
  Format B — NSE website downloads  (index_name, Index Date, Open Index Value, ...)

Usage:
    python -m engine.data.ingestion.load_indices
"""

import os
import glob
import logging
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

# Root folder containing the downloaded CSVs
DATA_DIR = Path(__file__).resolve().parents[3] / "Broad_Based_Indices"

# Map filename patterns to the canonical index name
# (for Format B files that have an index_name column, we use the column value)
NIFTY50_GLOB = "NIFTY 50-*.csv"

# Files to skip (combined file — we process individual files instead)
SKIP_FILES = {"ALL_BROAD_BASED.csv"}


def _get_dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    return url.replace("postgresql+psycopg://", "postgresql://")


# ─── Format A: Nifty 50 yearly CSVs ─────────────────────────────────────────

def _parse_nifty50_csv(filepath: str) -> pd.DataFrame:
    """
    Parse a Nifty 50 yearly CSV with columns:
      Date ,Open ,High ,Low ,Close ,Shares Traded ,Turnover (₹ Cr)
    """
    df = pd.read_csv(filepath, skipinitialspace=True)

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Rename to our schema
    col_map = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Shares Traded": "volume",
    }
    # Find turnover column (may have special chars)
    for c in df.columns:
        if "turnover" in c.lower() or "Turnover" in c:
            col_map[c] = "turnover_cr"
            break

    df = df.rename(columns=col_map)
    df["index_name"] = "NIFTY 50"

    # Parse date: DD-MMM-YYYY  (e.g. 31-DEC-1997)
    df["date"] = pd.to_datetime(df["date"].str.strip(), format="%d-%b-%Y", errors="coerce")
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.date

    # Convert numeric columns
    for col in ["open", "high", "low", "close", "volume", "turnover_cr"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.strip().str.replace(",", ""), errors="coerce")

    return df[["index_name", "date", "open", "high", "low", "close", "volume", "turnover_cr"]].copy()


# ─── Format B: NSE website download CSVs ────────────────────────────────────

def _parse_nse_index_csv(filepath: str) -> pd.DataFrame:
    """
    Parse an NSE index CSV with columns:
      index_name, Index Date, Open Index Value, High Index Value,
      Low Index Value, Closing Index Value, ..., Volume, turnover_cr, ..., date
    """
    df = pd.read_csv(filepath, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]

    # Build the output DataFrame
    out = pd.DataFrame()

    # Index name
    if "index_name" in df.columns:
        out["index_name"] = df["index_name"].str.strip().str.upper()
    else:
        # Derive from filename
        stem = Path(filepath).stem.replace("_", " ").upper()
        out["index_name"] = stem

    # Date — prefer the ISO 'date' column if present
    if "date" in df.columns:
        out["date"] = pd.to_datetime(df["date"], errors="coerce")
    elif "Index Date" in df.columns:
        out["date"] = pd.to_datetime(df["Index Date"], format="%d-%m-%Y", errors="coerce")
    
    out = out.dropna(subset=["date"])
    out["date"] = out["date"].dt.date

    # OHLC
    def _safe_numeric(series):
        return pd.to_numeric(
            series.astype(str).str.strip().str.replace(",", "").replace("-", ""),
            errors="coerce"
        )

    ohlc_map = {
        "Open Index Value": "open",
        "High Index Value": "high",
        "Low Index Value": "low",
        "Closing Index Value": "close",
    }
    for src, dst in ohlc_map.items():
        if src in df.columns:
            out[dst] = _safe_numeric(df[src])
        else:
            out[dst] = None

    # Volume
    if "Volume" in df.columns:
        out["volume"] = _safe_numeric(df["Volume"])
    elif "volume" in df.columns:
        out["volume"] = _safe_numeric(df["volume"])
    else:
        out["volume"] = None

    # Turnover
    if "turnover_cr" in df.columns:
        out["turnover_cr"] = _safe_numeric(df["turnover_cr"])
    else:
        out["turnover_cr"] = None

    # Drop rows where close is missing
    out = out.dropna(subset=["close"])

    return out[["index_name", "date", "open", "high", "low", "close", "volume", "turnover_cr"]].copy()


# ─── Database insertion ──────────────────────────────────────────────────────

INSERT_SQL = """
    INSERT INTO nse_index_data (index_name, date, open, high, low, close, volume, turnover_cr)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (index_name, date) DO NOTHING
"""


def _insert_batch(conn, rows: list[tuple]) -> int:
    """Insert a batch of rows, return count of actually inserted rows."""
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.executemany(INSERT_SQL, rows)
    conn.commit()
    return len(rows)


def _df_to_tuples(df: pd.DataFrame) -> list[tuple]:
    """Convert DataFrame to list of tuples for insertion."""
    import math
    tuples = []
    for _, row in df.iterrows():
        def _val(v):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return None
            return v

        tuples.append((
            row["index_name"],
            row["date"],
            _val(row.get("open")),
            _val(row.get("high")),
            _val(row.get("low")),
            _val(row["close"]),
            _val(row.get("volume")),
            _val(row.get("turnover_cr")),
        ))
    return tuples


# ─── Main ────────────────────────────────────────────────────────────────────

def load_all_indices():
    """Load all index CSVs from the Broad_Based_Indices folder."""
    if not DATA_DIR.exists():
        print(f"[load_indices] ❌ Data directory not found: {DATA_DIR}")
        return

    dsn = _get_dsn()
    print(f"[load_indices] Connecting to PostgreSQL …")
    conn = psycopg.connect(dsn)

    summary = {}

    # --- 1. Nifty 50 yearly files (Format A or B — auto-detect) ---
    nifty50_files = sorted(glob.glob(str(DATA_DIR / NIFTY50_GLOB)))
    if nifty50_files:
        print(f"\n[load_indices] Found {len(nifty50_files)} NIFTY 50 files")
        all_n50 = []
        for fpath in nifty50_files:
            # Peek at headers to detect format
            peek = pd.read_csv(fpath, nrows=0)
            peek_cols = [c.strip() for c in peek.columns]
            
            if "index_name" in peek_cols or "Index Date" in peek_cols:
                # Format B (NSE website download)
                df = _parse_nse_index_csv(fpath)
                df["index_name"] = "NIFTY 50"
            else:
                # Format A (yearly CSV)
                df = _parse_nifty50_csv(fpath)
            
            all_n50.append(df)
            print(f"  ├── {Path(fpath).name}: {len(df)} rows")

        if all_n50:
            combined = pd.concat(all_n50, ignore_index=True)
            # Remove duplicates (keep first)
            combined = combined.drop_duplicates(subset=["index_name", "date"], keep="first")
            combined = combined.sort_values("date")
            tuples = _df_to_tuples(combined)
            _insert_batch(conn, tuples)
            summary["NIFTY 50"] = len(tuples)
            print(f"  └── Total NIFTY 50: {len(tuples)} rows inserted")

    # --- 2. Other index files (Format B) ---
    all_csvs = glob.glob(str(DATA_DIR / "*.csv"))
    nifty50_set = set(nifty50_files)

    for fpath in sorted(all_csvs):
        fname = Path(fpath).name
        if fname in SKIP_FILES:
            continue
        if fpath in nifty50_set:
            continue

        print(f"\n[load_indices] Processing {fname} …")
        try:
            df = _parse_nse_index_csv(fpath)
            if df.empty:
                print(f"  └── ⚠️  No valid rows")
                continue

            # Get unique index names in this file
            for idx_name in df["index_name"].unique():
                subset = df[df["index_name"] == idx_name]
                subset = subset.drop_duplicates(subset=["index_name", "date"], keep="first")
                subset = subset.sort_values("date")
                tuples = _df_to_tuples(subset)
                _insert_batch(conn, tuples)
                summary[idx_name] = summary.get(idx_name, 0) + len(tuples)
                print(f"  ├── {idx_name}: {len(tuples)} rows")

        except Exception as e:
            print(f"  └── ❌ Error: {e}")

    conn.close()

    # --- Summary ---
    print("\n" + "=" * 60)
    print("  INDEX DATA INGESTION SUMMARY")
    print("=" * 60)
    total = 0
    for name, count in sorted(summary.items()):
        print(f"  {name:35s} {count:>8,} rows")
        total += count
    print("-" * 60)
    print(f"  {'TOTAL':35s} {total:>8,} rows")
    print("=" * 60)


if __name__ == "__main__":
    load_all_indices()
