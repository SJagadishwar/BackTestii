import pandas as pd
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_instruments():
    dfs = []

    for file in [
        "nse_equities.csv",
        "nse_indices.csv",
        "bse_equities.csv",
        "bse_indices.csv",
    ]:

        path = DATA_DIR / file
        if path.exists():
            dfs.append(pd.read_csv(path))

    if not dfs:
        raise RuntimeError("No instrument data files found")

    df = pd.concat(dfs, ignore_index=True)

    # Normalize
    df["display_name"] = df["display_name"].astype(str).str.strip().str.upper()
    df["yahoo_symbol"] = df["yahoo_symbol"].astype(str).str.strip()


    return df
