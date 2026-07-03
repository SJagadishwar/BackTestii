"""
engine/data/ingestion/master_csv_loader.py
============================================
Parses the official NSE 'nse_all_corporate_actions.csv' master file
and enriches the `nse_corporate_actions` table with deep historical
splits and bonuses.
"""

import os
import re
import logging
import psycopg
import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger("NSE_Master_Loader")

# Regex to extract split ratios from unstructured text (e.g. "Fv Split Rs.10/- To Rs.2/")
# We look for numbers around "to"
SPLIT_PATTERN = re.compile(r'(?:rs|rs\.|re)[\.\s]*([0-9\.]+)[a-z/ \-]+(?:to)[a-z/ \-]+(?:rs|rs\.|re)[\.\s]*([0-9\.]+)', re.IGNORECASE)

# Regex to extract bonus ratios (e.g. "Bonus 1:1", "Bonus 3:2")
BONUS_PATTERN = re.compile(r'bonus.*?([0-9\.]+)\s*:\s*([0-9\.]+)', re.IGNORECASE)


def parse_split_ratio(subject: str) -> float:
    """
    Parses "Fv Split Rs.10/- To Rs.5/" -> returns 2.0
    Returns None if parsing fails.
    """
    match = SPLIT_PATTERN.search(subject)
    if match:
        old_fv = float(match.group(1))
        new_fv = float(match.group(2))
        if new_fv > 0 and old_fv > new_fv:
            return old_fv / new_fv
    return None

def parse_bonus_ratio(subject: str) -> float:
    """
    Parses "Bonus 3:2" -> returns 2.5 (3 bonus shares for every 2 held = 5 total)
    Returns None if parsing fails.
    """
    match = BONUS_PATTERN.search(subject)
    if match:
        bonus_qty = float(match.group(1)) # Number of new shares
        held_qty = float(match.group(2))  # Number of existing shares required
        if held_qty > 0:
            # Adjustment factor = (New Total Shares) / (Old Total Shares)
            # = (held_qty + bonus_qty) / held_qty
            return (held_qty + bonus_qty) / held_qty
    return None

def main():
    csv_path = "nse_all_corporate_actions.csv"
    if not os.path.exists(csv_path):
        logger.error(f"Cannot find {csv_path}")
        return

    logger.info(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Needs valid exDate
    df = df.dropna(subset=['exDate'])
    df['exDate'] = pd.to_datetime(df['exDate'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['exDate'])
    
    # Filter for Series EQ or empty (to be safe, though most historical ones might have messy series)
    if 'series' in df.columns:
        df = df[df['series'].isin(['EQ', 'BE', 'SM', 'ST']) | df['series'].isna()]
        
    records_to_insert = []
    
    for idx, row in df.iterrows():
        symbol = str(row['symbol']).strip()
        if symbol == 'nan' or not symbol: continue
        
        ex_date = row['exDate'].date()
        subject = str(row['subject']).strip()
        
        # 1. Check for stock splits
        if 'split' in subject.lower():
            ratio = parse_split_ratio(subject)
            if ratio and ratio > 1.0:
                records_to_insert.append((symbol, ex_date, 'SPLIT', ratio, None))
                
        # 2. Check for bonuses
        elif 'bonus' in subject.lower():
            ratio = parse_bonus_ratio(subject)
            if ratio and ratio > 1.0:
                records_to_insert.append((symbol, ex_date, 'BONUS', ratio, None))

        # 3. Check for rights issues
        elif 'right' in subject.lower():
            m = re.search(r'(\d+)\s*:\s*(\d+)', subject)
            if m:
                new_shares = float(m.group(1))
                existing = float(m.group(2))
                if existing > 0:
                    ratio = (new_shares + existing) / existing
                    records_to_insert.append((symbol, ex_date, 'RIGHTS', ratio, None))
                
    logger.info(f"Parsed {len(records_to_insert)} valid SPLIT/BONUS events.")
    
    if not records_to_insert:
        logger.info("Nothing to insert.")
        return
        
    # Upsert into PostgreSQL
    load_dotenv()
    dsn = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
    
    inserted = 0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for rec in records_to_insert:
                symbol, ex_date, action_type, ratio, amount = rec
                cur.execute("""
                    INSERT INTO nse_corporate_actions (symbol, ex_date, action_type, ratio, amount)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, ex_date, action_type) DO NOTHING
                """, (symbol, ex_date, action_type, ratio, amount))
                if cur.rowcount > 0:
                    inserted += 1
        conn.commit()
        
    logger.info(f"Successfully UPSERTED {inserted} new historical corporate actions into the database.")

if __name__ == "__main__":
    main()
