import logging
from datetime import date
import pandas as pd

from engine.data.ingestion.db_writer import get_connection

logger = logging.getLogger(__name__)

class OptionsDataProvider:
    """
    Interface to fetch F&O database data dynamically for the Options Backtester.
    Handles dynamic expiry days and missing lot sizes for legacy data.
    """
    def __init__(self, conn=None):
        self._conn = conn if conn else get_connection()
        self._owns_conn = conn is None
        
    def __del__(self):
        if self._owns_conn and getattr(self, '_conn', None):
            try:
                self._conn.close()
            except Exception:
                pass
    
    def get_nearest_expiries(self, current_date: date, symbol: str) -> list[date]:
        """
        Dynamically fetches valid expiry dates for a symbol starting from a given date.
        Uses the FO database to see what expiries were actually trading.
        """
        # We look ahead up to 60 days to find upcoming expiries
        # because the query relies on actual trading data in the FO table.
        lookahead = pd.Timestamp(current_date) + pd.Timedelta(days=60)
        
        query = '''
            SELECT DISTINCT expiry_date
            FROM nse_fo_data
            WHERE date >= %s AND date <= %s AND symbol = %s AND option_type IN ('CE', 'PE')
            ORDER BY expiry_date ASC
        '''
        
        with self._conn.cursor() as cur:
            cur.execute(query, (current_date, lookahead.date(), symbol))
            res = cur.fetchall()
            
        return [r[0] for r in res] if res else []
        
    def get_spot_closing_price(self, target_date: date, symbol: str) -> float | None:
        """
        Gets the closing price of the underlying index or stock for a specific date.
        """
        index_name = symbol.upper()
        if index_name == "NIFTY": index_name = "NIFTY 50"
        elif index_name == "BANKNIFTY": index_name = "NIFTY BANK"
        elif index_name == "FINNIFTY": index_name = "NIFTY FINANCIAL SERVICES"
        elif index_name == "NIFTYNXT50": index_name = "NIFTY NEXT 50"
        
        query = '''
            SELECT close FROM nse_index_data WHERE index_name = %s AND date = %s
        '''
        with self._conn.cursor() as cur:
            cur.execute(query, (index_name, target_date))
            res = cur.fetchone()
            if res:
                return float(res[0])
                
        # Fallback to price_data if it's a stock
        query_stk = '''
            SELECT close FROM nse_price_data WHERE symbol = %s AND date = %s
        '''
        with self._conn.cursor() as cur:
            cur.execute(query_stk, (symbol, target_date))
            res = cur.fetchone()
            if res:
                return float(res[0])
                
        return None

    def get_atm_strike(self, spot_price: float, symbol: str) -> float:
        """
        Rounds the spot price to the nearest valid strike for the symbol.
        """
        symbol = symbol.upper()
        if symbol == "NIFTY":
            step = 50
        elif symbol == "BANKNIFTY":
            step = 100
        elif symbol == "FINNIFTY":
            step = 50
        elif symbol == "MIDCPNIFTY":
            step = 25
        else:
            step = 10 # generic fallback
            
        return round(spot_price / step) * step

    def get_contract_prices(self, symbol: str, target_date: date, strike: float, option_type: str, expiry_date: date) -> dict | None:
        """
        Fetches the Open and Close prices for a specific option contract on a specific day.
        Returns a dict with prices and the correctly resolved lot_size.
        """
        query = '''
            SELECT open, high, low, close, settle_price, lot_size
            FROM nse_fo_data
            WHERE date = %s AND symbol = %s AND strike_price = %s 
              AND option_type = %s AND expiry_date = %s
        '''
        with self._conn.cursor() as cur:
            cur.execute(query, (target_date, symbol, strike, option_type, expiry_date))
            res = cur.fetchone()
            
        if not res:
            return None
            
        open_p, high_p, low_p, close_p, settle_p, lot_size = res
        
        # Return what the database has. If missing (legacy data), just return None.
        # We no longer forcefully derive legacy lot sizes to keep metrics unit-based.
        return {
            "open": float(open_p) if open_p else None,
            "high": float(high_p) if high_p else None,
            "low": float(low_p) if low_p else None,
            "close": float(close_p) if close_p else None,
            "settle": float(settle_p) if settle_p else None,
            "lot_size": int(lot_size) if pd.notna(lot_size) and lot_size is not None else None
        }
