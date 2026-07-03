"""
engine/data/ingestion/fo_bhavcopy_downloader.py
================================================
Downloads NSE F&O Bhavcopy files from NSE archives.

URL patterns
------------
Legacy (~2016 - July 2024):
  https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{YYYY}/{MMM}/fo{DD}{MMM}{YYYY}bhav.csv.zip

New UDiFF format (July 2024 onwards):
  https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{YYYYMMDD}_F_0000.csv.zip
"""

import time
import logging
import calendar
from datetime import date, timedelta
from pathlib import Path

from .bhavcopy_downloader import _build_session  # Reuse existing session builder

logger = logging.getLogger(__name__)

_MONTH_ABBR = {m: calendar.month_abbr[m].upper() for m in range(1, 13)}

# The UDiFF format was introduced around July 8, 2024
UDIFF_CUTOVER = date(2024, 7, 8)


def _legacy_fo_url(d: date) -> str:
    mmm = _MONTH_ABBR[d.month]
    return (
        f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/"
        f"{d.year}/{mmm}/fo{d.strftime('%d')}{mmm}{d.year}bhav.csv.zip"
    )


def _udiff_fo_url(d: date) -> str:
    return (
        f"https://nsearchives.nseindia.com/content/fo/"
        f"BhavCopy_NSE_FO_0_0_0_{d.strftime('%Y%m%d')}_F_0000.csv.zip"
    )


def download_fo_bhavcopy(
    target_date: date,
    session=None,
    timeout: int = 30,
) -> bytes | None:
    """
    Download F&O Bhavcopy zip for a single trading date.

    Tries UDiFF URL first for dates >= July 2024, then falls back to legacy.
    For dates before July 2024, tries legacy first.

    Returns
    -------
    bytes -- zip file contents, or None if not available / weekend
    """
    if session is None:
        session = _build_session()

    # Build URL list based on date
    if target_date >= UDIFF_CUTOVER:
        urls = [_udiff_fo_url(target_date), _legacy_fo_url(target_date)]
    else:
        urls = [_legacy_fo_url(target_date)]

    for url in urls:
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 500:
                logger.debug(f"Downloaded {len(resp.content):,} bytes from {url}")
                return resp.content
            elif resp.status_code == 404:
                continue
            else:
                logger.debug(f"HTTP {resp.status_code} from {url}")
        except Exception as e:
            logger.debug(f"Request failed for {url}: {e}")
            continue

    return None


def date_range(start: date, end: date):
    """Yield each calendar date from start to end (inclusive)."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def download_fo_date_range(
    start: date,
    end: date,
    save_dir: Path | None = None,
    delay_seconds: float = 0.5,
) -> dict[date, bytes]:
    """
    Download F&O Bhavcopy files for a range of dates.
    """
    session = _build_session()
    results: dict[date, bytes] = {}

    for d in date_range(start, end):
        if d.weekday() >= 5:
            continue

        # Check disk cache
        if save_dir is not None:
            cached = save_dir / f"fo_bhav_{d.strftime('%Y%m%d')}.zip"
            if cached.exists():
                data = cached.read_bytes()
                results[d] = data
                continue

        data = download_fo_bhavcopy(d, session=session, timeout=30)
        if data:
            results[d] = data
            if save_dir is not None:
                save_dir.mkdir(parents=True, exist_ok=True)
                (save_dir / f"fo_bhav_{d.strftime('%Y%m%d')}.zip").write_bytes(data)
            time.sleep(delay_seconds)

    return results
