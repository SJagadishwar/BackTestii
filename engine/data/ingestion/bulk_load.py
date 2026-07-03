"""
engine/data/ingestion/bulk_load.py
=====================================
Bulk-load ALL historical NSE Bhavcopy data from 1994 to today.

This script downloads every available trading-day Bhavcopy from NSE
archives and inserts the data into nse_price_data.

Usage (run from project root):
    python -m engine.data.ingestion.bulk_load

Options (env vars):
    BHAV_CACHE_DIR   - local directory to cache downloaded zip files
                       (default: data/bhav_cache)
    BHAV_START_DATE  - earliest date to fetch  (default: 1994-01-03)
    BHAV_END_DATE    - latest  date to fetch   (default: today)
    BHAV_WORKERS     - parallel download threads (default: 1, NSE is sensitive)

Resume:
    Re-running this script is safe — already-ingested dates are skipped via
    the nse_ingestion_log table.
"""

import os
import sys
import time
import logging
import concurrent.futures
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .schema import create_schema
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


def _default_cache_dir() -> Path:
    # Place cache next to the data/ folder
    here = Path(__file__).resolve()
    project_root = here.parents[4]  # project root
    cache = project_root / "data" / "bhav_cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def run_bulk_load(
    start_date: date | None = None,
    end_date: date | None = None,
    cache_dir: Path | None = None,
    delay: float = 0.35,
):
    """
    Main entry-point for bulk historical loading.

    Skips weekends and already-ingested dates.
    Downloads, parses, and upserts each Bhavcopy into PostgreSQL.
    """
    # ── Config ────────────────────────────────────────────────────────────────
    start_date = start_date or date(
        int(os.getenv("BHAV_START_DATE", "1994-01-03").split("-")[0]),
        int(os.getenv("BHAV_START_DATE", "1994-01-03").split("-")[1]),
        int(os.getenv("BHAV_START_DATE", "1994-01-03").split("-")[2]),
    )
    end_date   = end_date   or date.today()
    cache_dir  = cache_dir  or _default_cache_dir()

    # ── Ensure schema exists ───────────────────────────────────────────────────
    logger.info("Verifying database schema …")
    create_schema()

    # ── Load already-done dates ────────────────────────────────────────────────
    logger.info("Fetching ingested dates from DB …")
    done_dates = get_ingested_dates()
    logger.info(f"Already ingested: {len(done_dates):,} dates")

    # ── Build work list ────────────────────────────────────────────────────────
    all_dates = []
    cur = start_date
    while cur <= end_date:
        if cur.weekday() < 5 and cur not in done_dates:
            all_dates.append(cur)
        cur += timedelta(days=1)

    logger.info(f"Dates to process: {len(all_dates):,}  "
                f"(from {start_date} to {end_date})")

    if not all_dates:
        logger.info("Nothing to do — all dates already ingested.")
        return

    # ── Main loop ──────────────────────────────────────────────────────────────
    session = _build_session()
    conn = get_connection()

    total_rows = 0
    errors = 0
    skipped = 0  # holidays / no data

    try:
        for i, d in enumerate(all_dates, 1):
            # ---- Check disk cache first ----
            cache_path = cache_dir / f"bhav_{d.strftime('%Y%m%d')}.zip"
            if cache_path.exists():
                raw = cache_path.read_bytes()
            else:
                raw = download_bhavcopy(d, session=session)
                if raw:
                    cache_path.write_bytes(raw)
                else:
                    skipped += 1
                    log_ingestion(d, 0, conn)  # mark as attempted
                    if i % 100 == 0:
                        logger.info(f"Progress: {i}/{len(all_dates)}  "
                                    f"rows={total_rows:,}  skipped={skipped}  err={errors}")
                    time.sleep(delay)
                    continue

            # ---- Parse ----
            try:
                df = parse_bhavcopy_bytes(raw, bhavcopy_date=pd.Timestamp(d))
            except Exception as e:
                logger.warning(f"Parse error {d}: {e}")
                errors += 1
                continue

            if df.empty:
                skipped += 1
                log_ingestion(d, 0, conn)
                continue

            # ---- Write to DB ----
            try:
                rows = upsert_price_df(df, conn=conn)
                total_rows += rows
                log_ingestion(d, rows, conn)
            except Exception as e:
                logger.warning(f"DB write error {d}: {e}")
                conn.rollback()
                errors += 1
                continue

            # ---- Progress report every 50 dates ----
            if i % 50 == 0:
                logger.info(
                    f"Progress: {i}/{len(all_dates)} dates  |  "
                    f"rows={total_rows:,}  skipped={skipped}  err={errors}"
                )

            time.sleep(delay)

    finally:
        conn.close()

    logger.info(
        f"\n{'='*60}\n"
        f"  Bulk load complete!\n"
        f"  Dates processed : {len(all_dates) - skipped - errors:,}\n"
        f"  Rows inserted   : {total_rows:,}\n"
        f"  Skipped (holiday): {skipped}\n"
        f"  Errors          : {errors}\n"
        f"{'='*60}"
    )


if __name__ == "__main__":
    run_bulk_load()
