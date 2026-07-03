from .loader import load_instruments

_INSTRUMENTS_DF = load_instruments()


def list_instruments(exchange=None):
    df = _INSTRUMENTS_DF

    if exchange:
        df = df[df["exchange"] == exchange]

    # Drop NaN and force string
    names = (
        df["search_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    return sorted(names)





def resolve_symbol(search_name, exchange=None):
    if not isinstance(search_name, str):
        raise ValueError("Invalid instrument selected")

    df = _INSTRUMENTS_DF

    if exchange:
        df = df[df["exchange"] == exchange]

    row = df[df["search_name"] == search_name]

    if row.empty:
        raise ValueError(f"Unknown instrument: {search_name} ({exchange})")

    return row.iloc[0]["yahoo_symbol"]



