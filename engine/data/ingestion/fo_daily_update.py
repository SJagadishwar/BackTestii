"""
engine/data/ingestion/fo_daily_update.py
=========================================
Daily incremental F&O data update.
Downloads the most recent F&O bhavcopy and upserts into nse_fo_data.

Usage (run from project root after market close ~5:00 PM IST):
    python -m engine.data.ingestion.fo_daily_update
"""

import logging
import time
from datetime import date, timedelta

import pandas as pd

from .fo_bhavcopy_downloader import download_fo_bhavcopy, _build_session
from .fo_bhavcopy_parser import parse_fo_bhavcopy_bytes
from .db_writer import get_connection, upsert_fo_df, log_fo_ingestion, get_fo_ingested_dates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# How many days to look back for missed updates
LOOKBACK_DAYS = 5


def run_fo_daily_update():
    """
    Download and ingest the most recent F&O bhavcopy data.
    Looks back up to LOOKBACK_DAYS to catch any missed trading days.
    """
    session = _build_session()
    conn = get_connection()

    try:
        done_dates = get_fo_ingested_dates(conn=conn)
        today = date.today()
        start = today - timedelta(days=LOOKBACK_DAYS)

        logger.info(f"F&O Daily Update: checking {start} → {today}")

        loaded = 0
        cur_date = start

        while cur_date <= today:
            # Skip weekends
            if cur_date.weekday() >= 5:
                cur_date += timedelta(days=1)
                continue

            # Skip already ingested
            if cur_date in done_dates:
                cur_date += timedelta(days=1)
                continue

            logger.info(f"  Fetching F&O bhavcopy for {cur_date}...")

            try:
                data = download_fo_bhavcopy(cur_date, session=session)
            except Exception as e:
                logger.warning(f"  {cur_date}: Download error: {e}")
                cur_date += timedelta(days=1)
                time.sleep(1)
                continue

            if data is None:
                logger.debug(f"  {cur_date}: No data (holiday?)")
                cur_date += timedelta(days=1)
                continue

            # Parse
            bhavcopy_date = pd.Timestamp(cur_date)
            try:
                df = parse_fo_bhavcopy_bytes(data, bhavcopy_date=bhavcopy_date)
            except Exception as e:
                logger.warning(f"  {cur_date}: Parse error: {e}")
                cur_date += timedelta(days=1)
                continue

            if df.empty:
                logger.debug(f"  {cur_date}: Empty after parsing")
                cur_date += timedelta(days=1)
                continue

            # Upsert
            try:
                count = upsert_fo_df(df, conn=conn)
                log_fo_ingestion(cur_date, count, conn)
                loaded += 1
                logger.info(f"  {cur_date}: {count:,} F&O rows upserted ✅")
            except Exception as e:
                logger.error(f"  {cur_date}: DB error: {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass

            cur_date += timedelta(days=1)
            time.sleep(1)

        if loaded == 0:
            logger.info("F&O Daily Update: All dates already up to date ✅")
        else:
            logger.info(f"F&O Daily Update: {loaded} day(s) loaded ✅")

    finally:
        conn.close()


if __name__ == "__main__":
    run_fo_daily_update()
