"""
engine/data/ingestion/fo_bulk_load.py
======================================
Bulk-loads historical NSE F&O Bhavcopy data into PostgreSQL.

Downloads day-by-day from NSE archives, parses, and upserts.
Has resume support: skips dates already in nse_fo_ingestion_log.

Usage:
    python -m engine.data.ingestion.fo_bulk_load [--start 2016-01-01] [--end 2026-03-25]
"""

import logging
import time
import argparse
from datetime import date, timedelta

from .fo_bhavcopy_downloader import download_fo_bhavcopy, _build_session
from .fo_bhavcopy_parser import parse_fo_bhavcopy_bytes
from .db_writer import get_connection, upsert_fo_df, log_fo_ingestion, get_fo_ingested_dates

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_fo_bulk_load(start_date: date, end_date: date, delay: float = 0.5):
    """
    Download and ingest F&O bhavcopies for a date range.
    Skips weekends, holidays (no data), and already-ingested dates.
    """
    session = _build_session()
    conn = get_connection()

    try:
        done_dates = get_fo_ingested_dates(conn=conn)
        logger.info(f"F&O Bulk Load: {start_date} → {end_date}")
        logger.info(f"  Already ingested: {len(done_dates)} dates")

        cur_date = start_date
        total_loaded = 0
        total_skipped = 0
        total_failed = 0

        while cur_date <= end_date:
            # Skip weekends
            if cur_date.weekday() >= 5:
                cur_date += timedelta(days=1)
                continue

            # Skip already ingested
            if cur_date in done_dates:
                cur_date += timedelta(days=1)
                total_skipped += 1
                continue

            # Download
            try:
                data = download_fo_bhavcopy(cur_date, session=session)
            except Exception as e:
                logger.warning(f"  {cur_date}: Download error: {e}")
                total_failed += 1
                cur_date += timedelta(days=1)
                time.sleep(delay)
                continue

            if data is None:
                # Holiday or weekend — no data available
                logger.debug(f"  {cur_date}: No data (holiday?)")
                cur_date += timedelta(days=1)
                time.sleep(delay * 0.5)
                continue

            # Parse
            bhavcopy_date = pd.Timestamp(cur_date)
            try:
                df = parse_fo_bhavcopy_bytes(data, bhavcopy_date=bhavcopy_date)
            except Exception as e:
                logger.warning(f"  {cur_date}: Parse error: {e}")
                total_failed += 1
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
                total_loaded += 1
                logger.info(f"  {cur_date}: {count:,} F&O rows upserted ✅")
            except Exception as e:
                logger.error(f"  {cur_date}: DB error: {e}")
                total_failed += 1
                # Rollback and get fresh connection
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                conn = get_connection()

            cur_date += timedelta(days=1)
            time.sleep(delay)

        logger.info(f"\nF&O Bulk Load Complete:")
        logger.info(f"  Days loaded: {total_loaded}")
        logger.info(f"  Days skipped (already done): {total_skipped}")
        logger.info(f"  Days failed: {total_failed}")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk-load NSE F&O data")
    parser.add_argument("--start", default="2016-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date (YYYY-MM-DD)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between downloads (seconds)")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    run_fo_bulk_load(start, end, delay=args.delay)
