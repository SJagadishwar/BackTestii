"""
engine/data/ingestion/bhavcopy_downloader.py
=============================================
Downloads NSE CM Bhavcopy files from NSE archives.

URL patterns
------------
Legacy (1994-2019 approx.):
  https://archives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MMM}/cm{DD}{MMM}{YYYY}bhav.csv.zip

New UDiFF format (2021 onwards, available from NSE data portal):
  https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{YYYY}{MM}{DD}_F_0000.csv.zip

Notes
-----
- NSE blocks raw HTTP requests without proper browser headers.
- This module uses a session with realistic headers + retry logic.
- Rate-limit: 1 request / 0.5 seconds recommended to be polite.
"""

import time
import logging
import calendar
from datetime import date, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ── NSE Request Headers ──────────────────────────────────────────────────────
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com/",
}

# Month abbreviations used in NSE filenames (all caps)
_MONTH_ABBR = {m: calendar.month_abbr[m].upper() for m in range(1, 13)}


def _legacy_url(d: date) -> str:
    mmm = _MONTH_ABBR[d.month]
    return (
        f"https://archives.nseindia.com/content/historical/EQUITIES/"
        f"{d.year}/{mmm}/cm{d.strftime('%d')}{mmm}{d.year}bhav.csv.zip"
    )


def _udiff_url(d: date) -> str:
    return (
        f"https://nsearchives.nseindia.com/content/cm/"
        f"BhavCopy_NSE_CM_0_0_0_{d.strftime('%Y%m%d')}_F_0000.csv.zip"
    )


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # Warm up NSE cookie by hitting homepage
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except Exception:
        pass
    return session


def download_bhavcopy(
    target_date: date,
    session: requests.Session | None = None,
    timeout: int = 30,
) -> bytes | None:
    """
    Download Bhavcopy zip for a single trading date.

    Tries UDiFF URL first (2021+), then falls back to legacy URL.

    Parameters
    ----------
    target_date : date
    session     : requests.Session (reuse across calls for performance)
    timeout     : int, seconds

    Returns
    -------
    bytes  -- zip file contents, or None if not available / weekend
    """
    if session is None:
        session = _build_session()

    # Try UDiFF (newer format) first, then legacy
    urls = [_udiff_url(target_date), _legacy_url(target_date)]
    for url in urls:
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 500:
                logger.debug(f"Downloaded {len(resp.content):,} bytes from {url}")
                return resp.content
            elif resp.status_code == 404:
                continue  # try next URL
            else:
                logger.debug(f"HTTP {resp.status_code} from {url}")
        except requests.RequestException as e:
            logger.debug(f"Request failed for {url}: {e}")
            continue

    return None  # holiday, weekend, or unavailable


def date_range(start: date, end: date):
    """Yield each calendar date from start to end (inclusive)."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def download_date_range(
    start: date,
    end: date,
    save_dir: Path | None = None,
    delay_seconds: float = 0.4,
) -> dict[date, bytes]:
    """
    Download Bhavcopy files for a range of dates.

    Parameters
    ----------
    start, end   : date range (inclusive)
    save_dir     : if provided, save each zip to disk (for re-use / caching)
    delay_seconds: polite delay between NSE requests

    Returns
    -------
    dict[date, bytes]  -- only dates where data was successfully downloaded
    """
    session = _build_session()
    results: dict[date, bytes] = {}

    for d in date_range(start, end):
        # Skip weekends quickly
        if d.weekday() >= 5:
            continue

        # Check disk cache first
        if save_dir is not None:
            cached = save_dir / f"bhav_{d.strftime('%Y%m%d')}.zip"
            if cached.exists():
                data = cached.read_bytes()
                results[d] = data
                continue

        data = download_bhavcopy(d, session=session, timeout=30)
        if data:
            results[d] = data
            if save_dir is not None:
                save_dir.mkdir(parents=True, exist_ok=True)
                (save_dir / f"bhav_{d.strftime('%Y%m%d')}.zip").write_bytes(data)
            time.sleep(delay_seconds)

    return results
