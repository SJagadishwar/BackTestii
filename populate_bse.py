import pandas as pd
import yfinance as yf
from pathlib import Path
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def populate_bse():
    data_dir = Path("c:/Users/jagad/Desktop/equity_strategy/data")
    nse_file = data_dir / "nse_equities.csv"
    bse_file = data_dir / "bse_equities.csv"

    logging.info("Reading NSE equities...")
    nse_df = pd.read_csv(nse_file)
    
    # We will test downloading the last 1 day of data for all tickers to see which ones exist
    nse_symbols = nse_df["display_name"].dropna().unique().tolist()
    
    bse_tickers = [f"{sym.strip().upper()}.BO" for sym in nse_symbols]
    
    logging.info(f"Checking {len(bse_tickers)} tickers on Yahoo Finance for BSE listings...")
    
    # yfinance bulk download is much faster. 
    # Download 1 day of data for all tickers.
    data = yf.download(bse_tickers, period="5d", interval="1d", group_by="ticker", progress=False, threads=True)
    
    valid_bse_symbols = []
    
    # yfinance returns a MultiIndex DataFrame if multiple tickers are requested
    if len(bse_tickers) > 1 and isinstance(data.columns, pd.MultiIndex):
        for ticker in bse_tickers:
            if ticker in data:
                ticker_data = data[ticker]
                # If there's valid Close data, it exists
                if not ticker_data["Close"].dropna().empty:
                    valid_bse_symbols.append(ticker)
    elif len(bse_tickers) == 1:
        if not data["Close"].dropna().empty:
            valid_bse_symbols.append(bse_tickers[0])

    logging.info(f"Found {len(valid_bse_symbols)} valid BSE listings.")
    
    # Build the BSE dataframe
    bse_rows = []
    for _, row in nse_df.iterrows():
        base_sym = str(row["display_name"]).strip().upper()
        bse_sym = f"{base_sym}.BO"
        if bse_sym in valid_bse_symbols:
            bse_rows.append({
                "display_name": base_sym,
                "yahoo_symbol": bse_sym,
                "exchange": "BSE",
                "type": row["type"],
                "company_name": row["company_name"]
            })
            
    bse_df = pd.DataFrame(bse_rows)
    bse_df.to_csv(bse_file, index=False)
    logging.info(f"Saved {len(bse_df)} rows to {bse_file}")

if __name__ == "__main__":
    populate_bse()
