"""
engine/data/ingestion/daily_index_update.py
===========================================
Downloads and ingests the most recent index OHLCV data from NSE.
Since NSE index API provides the current snapshot for all indices, we can fetch
the `/api/allIndices` endpoint at the end of the day.

Usage (run from project root after market close ~5:00 PM IST):
    python -m engine.data.ingestion.daily_index_update
"""

import logging
import time
from datetime import date, timedelta
import pandas as pd
from dotenv import load_dotenv

from .bhavcopy_downloader import _build_session
from .db_writer import get_connection, upsert_index_df, log_index_ingestion, get_index_ingested_dates
from engine.data.own_db_loader import get_available_indices

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def fetch_all_indices(session=None) -> tuple[dict | None, date | None]:
    """Fetch the allIndices snapshot from NSE using nsepython."""
    try:
        from nsepython import nsefetch
    except ImportError:
        logger.error("nsepython package not installed. Cannot fetch index data.")
        return None, None

    url = "https://www.nseindia.com/api/allIndices"
    
    try:
        data = nsefetch(url)
        
        if data and isinstance(data, dict):
            # Try to determine the date from the response
            # NSE usually puts "timestamp": "26-Mar-2026 16:00:00" in the response
            timestampStr = data.get("timestamp", "")
            d = None
            if timestampStr:
                try:
                    ts = pd.to_datetime(timestampStr)
                    d = ts.date()
                except Exception:
                    pass
            
            if not d:
                d = date.today()
                
            return data.get("data", []), d
        else:
            logger.warning(f"Unexpected response format from nsefetch: {type(data)}")
            return None, None
            
    except Exception as e:
        logger.error(f"Failed to fetch indices via nsepython: {e}")
        return None, None
            



def _clean_numeric(val):
    if pd.isna(val) or val == "-" or val == "":
        return None
    try:
        return float(str(val).replace(",", ""))
    except ValueError:
        return None
        
def _clean_int(val):
    v = _clean_numeric(val)
    return int(v) if v is not None else None


def run_daily_index_update():
    """
    Check and ingest the most recent index data.
    """
    session = _build_session()
    conn = get_connection()
    
    # Wait to avoid rate-limits if run right after bhavcopy
    time.sleep(2)
    
    try:
        logger.info("Fetching allIndices from NSE...")
        indices_data, nse_date = fetch_all_indices(session)
        
        if not indices_data:
            logger.warning("Empty or invalid response from NSE API.")
            return
        
        # We only really care about getting the data for the current trading day
        # If NSE's timestamp date is already in our DB, skip it.
        done_dates = get_index_ingested_dates(conn=conn)
        if nse_date in done_dates:
            logger.info(f"Daily Index Update: Data for {nse_date} is already ingested. ✅")
            return
            
        logger.info(f"Daily Index Update: Processing data for {nse_date}...")
            
        # Get the list of indices we actually track in our database
        tracked_indices = [idx["index_name"].upper() for idx in get_available_indices()]
        if not tracked_indices:
            # Fallback if DB is completely empty for some reason
            tracked_indices = ["NIFTY 50", "NIFTY BANK"]
            
        # NSE sometimes uses different names in the allIndices API than what we track
        # Let's map their API names to our standard DB names
        # We can also map our DB names to their API names if needed
        # Mapping: API Name -> Our DB Name
        NSE_NAME_MAP = {
            "NIFTY50": "NIFTY 50",
            "NIFTY FIN SERVICE": "NIFTY FINANCIAL SERVICES",
            "NIFTY FINSRV25 50": "NIFTY FINANCIAL SERVICES 25-50",
            "NIFTY FINANCIAL SERVICES EX-BANK": "NIFTY FINANCIAL SERVICES EX-BANK", # sometimes it matches
            "NIFTY FINSRV EX BK": "NIFTY FINANCIAL SERVICES EX-BANK",
            "NIFTY HEALTHCARE": "NIFTY HEALTHCARE INDEX",
            "NIFTY LARGEMID250": "NIFTY LARGEMIDCAP 250",
            "NIFTY MID SELECT": "NIFTY MIDCAP SELECT",
            "NIFTY MID SML 400": "NIFTY MIDSMALLCAP 400",
            "NIFTY MIDSML FIN": "NIFTY MIDSMALL FINANCIAL SERVICES",
            "NIFTY MIDSML HLTH": "NIFTY MIDSMALL HEALTHCARE",
            "NIFTY MIDSML IT": "NIFTY MIDSMALL IT & TELECOM",
            "NIFTY PVT BANK": "NIFTY PRIVATE BANK",
            "NIFTY SMLCAP 100": "NIFTY SMALLCAP 100",
            "NIFTY SMLCAP 250": "NIFTY SMALLCAP 250",
            "NIFTY SMLCAP 50": "NIFTY SMALLCAP 50",
            "NIFTY TOT MARKET": "NIFTY TOTAL MARKET",
            "NIFTY TOTAL MKT": "NIFTY TOTAL MARKET",
            "NIFTY MICROCAP250": "NIFTY MICROCAP 250",
            "NIFTY CONSR DURBL": "NIFTY CONSUMER DURABLES",
            "NIFTY OIL AND GAS": "NIFTY OIL & GAS",
            "NIFTY FINSEREXBNK": "NIFTY FINANCIAL SERVICES EX-BANK",
            "NIFTY MS FIN SERV": "NIFTY MIDSMALL FINANCIAL SERVICES",
            "NIFTY MS IT TELCM": "NIFTY MIDSMALL IT & TELECOM",
        }
            
        # Parse the JSON response into our schema
        rows = []
        for item in indices_data:
            idx_name = item.get("indexSymbol", item.get("index", "")).upper()
            
            # Map NIFTY 50 and other aliases
            if idx_name in NSE_NAME_MAP:
                db_idx_name = NSE_NAME_MAP[idx_name]
            else:
                db_idx_name = idx_name
            
            # We only track specific indices, skip the rest
            if db_idx_name not in tracked_indices:
                continue
                
            # Now we fetch the volume/turnover for this specific index
            # This requires hitting its specific endpoint
            volume = None
            turnover_cr = None
            try:
                # url-encode the spaces for the API
                from urllib.parse import quote
                encoded_name = quote(item.get("indexSymbol", item.get("index", "")))
                vol_url = f"https://www.nseindia.com/api/equity-stockIndices?index={encoded_name}"
                from nsepython import nsefetch
                vol_data = nsefetch(vol_url)
                if vol_data and "metadata" in vol_data:
                    volume = _clean_int(vol_data["metadata"].get("totalTradedVolume"))
                    raw_val = _clean_numeric(vol_data["metadata"].get("totalTradedValue"))
                    if raw_val is not None:
                        # NSE API totalTradedValue is in INR; convert to Crores
                        turnover_cr = round(raw_val / 10000000, 4)
                
                # Sleep a tiny bit to avoid hammering the API
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Could not fetch volume for {db_idx_name}: {e}")
                
            # NSE API allIndices maps:
            # previousClose, open, high, low, last (close), percentChange, yearHigh, yearLow, advances, declines
            
            rows.append({
                "index_name": db_idx_name,
                "date": nse_date,
                "open": _clean_numeric(item.get("open")),
                "high": _clean_numeric(item.get("high")),
                "low": _clean_numeric(item.get("low")),
                "close": _clean_numeric(item.get("last", item.get("currentValue"))),
                "volume": volume,
                "turnover_cr": turnover_cr
            })
            
        if not rows:
            logger.warning(f"No tracked indices found in the NSE response.")
            return
            
        df = pd.DataFrame(rows)
        inserted_count = upsert_index_df(df, conn=conn)
        log_index_ingestion(nse_date, inserted_count, conn)
        
        logger.info(f"  {nse_date}: {inserted_count} index rows upserted ✅")
        
    finally:
        conn.close()


if __name__ == "__main__":
    run_daily_index_update()
