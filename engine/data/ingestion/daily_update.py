"""
engine/data/ingestion/daily_update.py
=======================================
Downloads and ingests the most recent Bhavcopy (today's or last trading day).

Usage (run from project root after market close ~5:00 PM IST):
    python -m engine.data.ingestion.daily_update

Can be scheduled via Windows Task Scheduler or cron.
"""

import logging
import time
from datetime import date, timedelta

import pandas as pd
from dotenv import load_dotenv

from .bhavcopy_downloader import download_bhavcopy, _build_session
from .bhavcopy_parser import parse_bhavcopy_bytes
from .db_writer import get_connection, upsert_price_df, log_ingestion, get_ingested_dates

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _last_n_trading_days(n: int = 5) -> list[date]:
    """Return the last n weekdays up to and including today."""
    days = []
    d = date.today()
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return days


def run_daily_update(lookback_days: int = 5):
    """
    Check and ingest the most recent trading days that are not yet in the DB.
    Looks back `lookback_days` trading days to handle weekend/holiday gaps.
    """
    done = get_ingested_dates()
    candidates = _last_n_trading_days(lookback_days)
    missing = [d for d in candidates if d not in done]

    if not missing:
        logger.info("Daily update: all recent dates already ingested. ✅")
        return

    logger.info(f"Daily update: fetching {len(missing)} date(s): {missing}")

    session = _build_session()
    conn = get_connection()

    try:
        for d in sorted(missing):
            raw = download_bhavcopy(d, session=session)
            if not raw:
                logger.info(f"  {d}: not available (holiday or future date)")
                continue

            df = parse_bhavcopy_bytes(raw, bhavcopy_date=pd.Timestamp(d))
            if df.empty:
                logger.warning(f"  {d}: parsed empty DataFrame")
                continue

            rows = upsert_price_df(df, conn=conn)
            log_ingestion(d, rows, conn)
            logger.info(f"  {d}: {rows:,} rows upserted ✅")
            time.sleep(0.5)
    finally:
        conn.close()


if __name__ == "__main__":
    run_daily_update()
