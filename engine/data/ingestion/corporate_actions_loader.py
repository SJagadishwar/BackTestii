"""
engine/data/ingestion/corporate_actions_loader.py
===================================================
Downloads and ingests NSE corporate actions (splits, bonuses, dividends)
so that the own_db_loader can compute adjusted prices.

Data source
-----------
NSE provides corporate actions via their API and also publishes them in the
security archives. We use two sources:

1.  NSE corporate actions JSON API (recent, up to 10 years)
    https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date=dd-mm-yyyy&to_date=dd-mm-yyyy

2.  Manual CSV import (if user provides their own corporate actions data)
"""

import os
import io
import json
import time
import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
import psycopg
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    return url.replace("postgresql+psycopg://", "postgresql://")


NSE_CORP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-actions",
    "X-Requested-With": "XMLHttpRequest",
}


def _nse_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(NSE_CORP_HEADERS)
    try:
        s.get("https://www.nseindia.com", timeout=10)
        time.sleep(1)
    except Exception:
        pass
    return s


def _parse_action_type(purpose: str) -> tuple[str, float | None, float | None]:
    """
    Parse NSE purpose string into (action_type, ratio, amount).

    Examples
    --------
    "Bonus 1:1"           → (BONUS, 2.0, None)   total shares after / before
    "Stock Split 10:2"    → (SPLIT, 5.0, None)   old face / new face
    "Dividend - Re 1/- "  → (DIVIDEND, None, 1.0)
    "Dividend - Rs.5.5/-" → (DIVIDEND, None, 5.5)
    """
    import re
    p = purpose.strip().upper()

    if "SPLIT" in p or "SUB-DIVISION" in p:
        m = re.search(r"(\d+)\s*:\s*(\d+)", purpose)
        if m:
            old, new = int(m.group(1)), int(m.group(2))
            ratio = old / new if new else None
        else:
            ratio = None
        return ("SPLIT", ratio, None)

    if "BONUS" in p:
        # Format: "Bonus 1:1" (bonus : existing)
        m = re.search(r"(\d+)\s*:\s*(\d+)", purpose)
        if m:
            bonus, existing = int(m.group(1)), int(m.group(2))
            ratio = (bonus + existing) / existing if existing else None
        else:
            ratio = None
        return ("BONUS", ratio, None)

    if "DIVIDEND" in p or "DIV" in p:
        m = re.search(r"[\d]+\.?\d*", purpose.replace(",", ""))
        amount = float(m.group()) if m else None
        return ("DIVIDEND", None, amount)

    if "RIGHT" in p:
        # Format: "Rights 1:15 @ Premium Rs 1247"
        # Ratio X:Y means X new share for every Y held
        m = re.search(r"(\d+)\s*:\s*(\d+)", purpose)
        ratio = None
        if m:
            new_shares, existing = int(m.group(1)), int(m.group(2))
            ratio = (new_shares + existing) / existing if existing else None
        return ("RIGHTS", ratio, None)

    return ("OTHER", None, None)


def fetch_nse_corporate_actions(
    from_date: date,
    to_date: date,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """
    Fetch corporate actions from NSE API for a date range.
    NSE API returns a max of 3 months per call — we chunk automatically.
    """
    if session is None:
        session = _nse_session()

    all_records = []
    cur_start = from_date

    while cur_start <= to_date:
        chunk_end = min(
            date(cur_start.year, cur_start.month, 1) + timedelta(days=89),
            to_date,
        )
        fmt = "%d-%m-%Y"
        url = (
            f"https://www.nseindia.com/api/corporates-corporateActions"
            f"?index=equities"
            f"&from_date={cur_start.strftime(fmt)}"
            f"&to_date={chunk_end.strftime(fmt)}"
        )
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    all_records.extend(data)
        except Exception as e:
            logger.warning(f"Failed to fetch corporate actions {cur_start}–{chunk_end}: {e}")

        cur_start = chunk_end + timedelta(days=1)
        time.sleep(0.5)

    if not all_records:
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    return df


def _normalise_nse_ca(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Convert NSE API response to our canonical format."""
    records = []
    for _, row in raw_df.iterrows():
        symbol = str(row.get("symbol", "")).strip().upper()
        purpose = str(row.get("subject", row.get("purpose", "")))
        ex_date_str = str(row.get("exDate", row.get("ex_date", "")))

        try:
            ex_date = pd.to_datetime(ex_date_str, dayfirst=True).date()
        except Exception:
            continue

        action_type, ratio, amount = _parse_action_type(purpose)
        if action_type == "OTHER":
            continue

        records.append({
            "symbol": symbol,
            "ex_date": ex_date,
            "action_type": action_type,
            "ratio": ratio,
            "amount": amount,
            "remarks": purpose,
        })

    return pd.DataFrame(records)


def import_corporate_actions_from_csv(csv_path: str | Path) -> pd.DataFrame:
    """
    Import corporate actions from a user-provided CSV.

    Expected columns (case-insensitive):
        symbol, ex_date, action_type, ratio, amount, remarks
    """
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df["ex_date"] = pd.to_datetime(df["ex_date"], dayfirst=True, errors="coerce").dt.date
    df = df.dropna(subset=["symbol", "ex_date", "action_type"])
    return df


def upsert_corporate_actions(df: pd.DataFrame, conn: psycopg.Connection | None = None):
    """Write parsed corporate actions rows to nse_corporate_actions."""
    if df.empty:
        return 0
    close_conn = conn is None
    if conn is None:
        conn = psycopg.connect(_get_dsn())
    count = 0
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute("""
                    INSERT INTO nse_corporate_actions
                        (symbol, ex_date, action_type, ratio, amount, remarks)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, ex_date, action_type) DO UPDATE SET
                        ratio   = EXCLUDED.ratio,
                        amount  = EXCLUDED.amount,
                        remarks = EXCLUDED.remarks
                """, (
                    row["symbol"],
                    row["ex_date"],
                    row["action_type"],
                    row.get("ratio"),
                    row.get("amount"),
                    row.get("remarks"),
                ))
                count += 1
        conn.commit()
        return count
    finally:
        if close_conn:
            conn.close()


def run_corporate_actions_load(
    from_date: date | None = None,
    to_date: date | None = None,
    user_csv: str | None = None,
):
    """
    Main entry-point for loading corporate actions.

    Downloads from NSE API (last 10 years or specified range) and optionally
    supplements with a user-provided CSV for older data.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")

    from_date = from_date or date(2015, 1, 1)
    to_date   = to_date   or date.today()

    logger.info(f"Fetching corporate actions from NSE API: {from_date} to {to_date}")
    session = _nse_session()
    raw_df = fetch_nse_corporate_actions(from_date, to_date, session)

    if not raw_df.empty:
        ca_df = _normalise_nse_ca(raw_df)
        count = upsert_corporate_actions(ca_df)
        logger.info(f"Upserted {count:,} corporate actions from NSE API ✅")
    else:
        logger.warning("No corporate actions returned from NSE API")

    if user_csv:
        logger.info(f"Importing corporate actions from CSV: {user_csv}")
        csv_df = import_corporate_actions_from_csv(user_csv)
        count2 = upsert_corporate_actions(csv_df)
        logger.info(f"Upserted {count2:,} rows from CSV ✅")


if __name__ == "__main__":
    run_corporate_actions_load()
