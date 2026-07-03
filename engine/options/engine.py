import logging
from datetime import date
from typing import List, Dict, Optional

from engine.options.data_provider import OptionsDataProvider

logger = logging.getLogger(__name__)

class OptionsBacktester:
    def __init__(self, data_provider: OptionsDataProvider, initial_capital: float = 1000000.0):
        self.dp = data_provider
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades_history = []
        
    def run_weekly_long_straddle(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        entry_price_type: str = "open",  # "open" or "close" on Friday
        what_if_premium_target: Optional[float] = None,
        what_if_spot_move_pct: Optional[float] = None
    ):
        """
        Runs a backtest for a weekly long straddle.
        Rules:
        - Enter on Friday (the day after previous Thursday expiry).
        - Buy 1 ATM CE and 1 ATM PE.
        - Exit on Expiry day (the actual expiry from the DB), at Close.
        - Checks what-if stop losses daily.
        """
        self.trades_history = []
        self.current_capital = self.initial_capital
        
        trade_days = self._get_trade_days(symbol, start_date, end_date)
        if not trade_days:
            logger.warning("No trading days found in the given range.")
            return []
            
        current_idx = 0
        while current_idx < len(trade_days):
            current_day = trade_days[current_idx]
            
            # Entry on Friday (weekday == 4)
            if current_day.weekday() == 4:
                
                spot_close = self.dp.get_spot_closing_price(current_day, symbol)
                if not spot_close:
                    current_idx += 1
                    continue
                    
                expiries = self.dp.get_nearest_expiries(current_day, symbol)
                if not expiries:
                    current_idx += 1
                    continue
                    
                target_expiry = expiries[0] 
                atm_strike = self.dp.get_atm_strike(spot_close, symbol)
                
                ce_data = self.dp.get_contract_prices(symbol, current_day, atm_strike, "CE", target_expiry)
                pe_data = self.dp.get_contract_prices(symbol, current_day, atm_strike, "PE", target_expiry)
                
                if not ce_data or not pe_data:
                    current_idx += 1
                    continue
                    
                ce_entry = ce_data["open"] if entry_price_type == "open" else ce_data["close"]
                pe_entry = pe_data["open"] if entry_price_type == "open" else pe_data["close"]
                
                if not ce_entry or not pe_entry:
                    current_idx += 1
                    continue
                    
                combined_premium_entry = ce_entry + pe_entry
                
                # Active trade dict (Unit-Based)
                trade = {
                    "entry_date": current_day,
                    "expiry_date": target_expiry,
                    "strike": atm_strike,
                    "entry_type": entry_price_type,
                    "ce_entry_price": ce_entry,
                    "pe_entry_price": pe_entry,
                    "combined_premium_entry": combined_premium_entry,
                    "spot_at_entry": spot_close,
                    "exit_date": None,
                    "ce_exit_price": None,
                    "pe_exit_price": None,
                    "combined_premium_exit": None,
                    "spot_at_exit": None,
                    "pnl": 0.0,
                    "exit_reason": "active"
                }
                
                in_trade_idx = current_idx + 1
                exited = False
                
                while in_trade_idx < len(trade_days) and not exited:
                    track_day = trade_days[in_trade_idx]
                    
                    if track_day > target_expiry:
                        break # Missed expiry, skip logic error handling for now
                        
                    daily_ce = self.dp.get_contract_prices(symbol, track_day, atm_strike, "CE", target_expiry)
                    daily_pe = self.dp.get_contract_prices(symbol, track_day, atm_strike, "PE", target_expiry)
                    daily_spot = self.dp.get_spot_closing_price(track_day, symbol)
                    
                    if daily_ce and daily_pe and daily_spot:
                        current_combined = daily_ce["close"] + daily_pe["close"]
                        
                        # What-if 1: Target Premium Hit
                        if what_if_premium_target and current_combined >= what_if_premium_target:
                            self._close_trade(trade, track_day, daily_ce["close"], daily_pe["close"], daily_spot, "premium_target")
                            exited = True
                            
                        # What-if 2: Spot Moved X%
                        elif what_if_spot_move_pct:
                            move_pct = abs((daily_spot - spot_close) / spot_close) * 100
                            if move_pct >= what_if_spot_move_pct:
                                self._close_trade(trade, track_day, daily_ce["close"], daily_pe["close"], daily_spot, "spot_move")
                                exited = True
                                
                        # Exit on Expiry Day
                        if not exited and track_day == target_expiry:
                            self._close_trade(trade, track_day, daily_ce["close"], daily_pe["close"], daily_spot, "expiry")
                            exited = True
                            
                    if exited:
                        # Once trade is closed, resume main loop from the very next day
                        current_idx = in_trade_idx
                        break
                        
                    in_trade_idx += 1
                
            current_idx += 1
            
        return self.trades_history

    def _close_trade(self, trade: dict, exit_date: date, ce_exit: float, pe_exit: float, spot_exit: float, reason: str):
        trade["exit_date"] = exit_date
        trade["ce_exit_price"] = ce_exit
        trade["pe_exit_price"] = pe_exit
        trade["combined_premium_exit"] = ce_exit + pe_exit
        trade["spot_at_exit"] = spot_exit
        trade["exit_reason"] = reason
        
        # Unit-Based PnL: (Exit Premium - Entry Premium)
        # Represents pure Points Captured per 1x Quantity.
        pnl = (ce_exit + pe_exit) - trade["combined_premium_entry"]
        trade["pnl"] = pnl
        
        self.trades_history.append(trade)
        self.current_capital += pnl

    def _get_trade_days(self, symbol: str, start_date: date, end_date: date) -> List[date]:
        # Map F&O symbol to index name
        index_name = symbol.upper()
        if index_name == "NIFTY": index_name = "NIFTY 50"
        elif index_name == "BANKNIFTY": index_name = "NIFTY BANK"
        elif index_name == "FINNIFTY": index_name = "NIFTY FINANCIAL SERVICES"
        elif index_name == "NIFTYNXT50": index_name = "NIFTY NEXT 50"
        
        query = "SELECT date FROM nse_index_data WHERE index_name = %s AND date >= %s AND date <= %s ORDER BY date ASC"
        with self.dp._conn.cursor() as cur:
            cur.execute(query, (index_name, start_date, end_date))
            res = cur.fetchall()
            
        # fallback to price data if symbol is not an index
        if not res:
            query = "SELECT date FROM nse_price_data WHERE symbol = %s AND date >= %s AND date <= %s ORDER BY date ASC"
            with self.dp._conn.cursor() as cur:
                cur.execute(query, (symbol.upper(), start_date, end_date))
                res = cur.fetchall()
                
        return [r[0] for r in res] if res else []
