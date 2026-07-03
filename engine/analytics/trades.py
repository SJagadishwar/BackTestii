import pandas as pd


def build_trade_log(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build trade log from signal transitions (long-only).

    Entry  : signal 0 -> 1
    Exit   : signal 1 -> 0
    Final open trade (if any) is closed on last available date.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - 'close'
        - 'signal'
        - DatetimeIndex

    Returns
    -------
    pd.DataFrame
        Trade log with:
        - entry_date
        - exit_date
        - entry_price
        - exit_price
        - pnl
        - return_pct
        - holding_days
    """

    required = {"close", "signal"}
    if not required.issubset(df.columns):
        raise ValueError("DataFrame must contain 'close' and 'signal' columns")

    trades = []
    in_trade = False
    entry_date = entry_price = None

    for date, row in df.iterrows():
        signal = row["signal"]
        price = row["close"]

        # Entry
        if signal == 1 and not in_trade:
            in_trade = True
            entry_date = date
            entry_price = price

        # Exit
        elif signal == 0 and in_trade:
            exit_date = date
            exit_price = price

            pnl = exit_price - entry_price
            return_pct = pnl / entry_price * 100
            holding_days = (exit_date - entry_date).days

            trades.append({
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl,
                "return_pct": return_pct,
                "holding_days": holding_days,
            })

            in_trade = False

    # -----------------------------
    # Close open trade at end
    # -----------------------------
    if in_trade:
        exit_date = df.index[-1]
        exit_price = df["close"].iloc[-1]

        pnl = exit_price - entry_price
        return_pct = pnl / entry_price * 100
        holding_days = (exit_date - entry_date).days

        trades.append({
            "entry_date": entry_date,
            "exit_date": exit_date,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "return_pct": return_pct,
            "holding_days": holding_days,
        })

    return pd.DataFrame(trades)
