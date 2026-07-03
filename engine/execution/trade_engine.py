import pandas as pd


def run_backtest(
    price_df: pd.DataFrame,
    signal_df: pd.DataFrame,
    initial_capital: float = 100_000.0,
):
    """
    Event-based trade execution engine (Long-only).

    Entry : signal changes 0 -> 1
    Exit  : signal changes 1 -> 0

    Parameters
    ----------
    price_df : pd.DataFrame
        Must contain:
        - DatetimeIndex
        - 'close'

    signal_df : pd.DataFrame
        Must contain:
        - 'signal' column (0 or 1)

    initial_capital : float
        Starting cash

    Returns
    -------
    portfolio_df : pd.DataFrame
        Contains:
        - equity

    trades_df : pd.DataFrame
        Trade log
    """
    # ============================================================
    # CANONICAL EXECUTION ENGINE
    #
    # This function is the SINGLE source of truth for:
    # - Trade execution
    # - Equity curve generation
    # - Trade lifecycle handling
    #
    # All metrics, plots, and analytics MUST derive from
    # the output of this function.
    #
    # Any alternative execution or portfolio logic is
    # considered legacy or experimental.
    # ============================================================


    # ------------------ VALIDATION ------------------
    if "close" not in price_df.columns:
        raise ValueError("price_df must contain 'close' column")

    if "signal" not in signal_df.columns:
        raise ValueError("signal_df must contain 'signal' column")

    # ------------------ SIGNAL CONTRACT ------------------
    # Signal represents the desired position:
    #   1 = fully long
    #   0 = flat (no position)
    #
    # Entry  : signal changes 0 -> 1
    # Exit   : signal changes 1 -> 0
    #
    # Any other value is invalid and must fail loudly.
    # ----------------------------------------------------

    signal_series = signal_df["signal"].dropna()

    invalid = ~signal_series.isin([0, 1])
    if invalid.any():
        raise ValueError(
            "Invalid signal detected. Signal must be 0 (flat) or 1 (long)."
        )


    df = price_df.copy()
    df["signal"] = signal_df["signal"].reindex(df.index).fillna(0)

    # ------------------ STATE ------------------
    cash = initial_capital
    shares = 0
    in_trade = False

    equity_curve = []
    trades = []

    entry_date = None
    entry_price = None

    is_buy_and_hold = signal_df["signal"].fillna(0).eq(1).all()
    # ----------------------------------------------------
    # BUY & HOLD BASELINE RULE
    #
    # Buy & Hold is treated as a baseline:
    # - Signal must be 1 for the entire backtest
    # - Forced exit at end is allowed ONLY for Buy & Hold
    # - All other strategies must NOT be force-closed
    #
    # This preserves fair metrics and comparisons.
    # ----------------------------------------------------



    prev_signal = 0

    # ------------------ MAIN LOOP ------------------
    for date, row in df.iterrows():
        price = row["close"]
        signal = int(row["signal"])

        # -------- ENTRY --------
        if not in_trade and signal == 1:
            shares = int(cash // price)
            cash -= shares * price

            in_trade = True
            entry_date = date
            entry_price = price
            entry_volume = row["volume"]

        # -------- EXIT --------
        elif in_trade and signal == 0:
            cash += shares * price

            trades.append({
                "entry_date": entry_date,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": price,
                "entry_volume": entry_volume,
                "pnl": (price - entry_price) * shares,
                "return_pct": (price - entry_price) / entry_price * 100,
                "holding_days": (date - entry_date).days,
            })

            shares = 0
            in_trade = False
            entry_date = None
            entry_price = None

        equity = cash + shares * price
        equity_curve.append(equity)

        prev_signal = signal

    
    # -------- HANDLE OPEN TRADE AT END --------
    open_trade = None

    if in_trade:
        if is_buy_and_hold:
            # ✅ FORCE EXIT ONLY FOR BUY & HOLD
            final_date = df.index[-1]
            final_price = df["close"].iloc[-1]

            cash += shares * final_price

            trades.append({
                "entry_date": entry_date,
                "exit_date": final_date,
                "entry_price": entry_price,
                "exit_price": final_price,
                "entry_volume": entry_volume,
                "pnl": (final_price - entry_price) * shares,
                "return_pct": (final_price - entry_price) / entry_price * 100,
                "holding_days": (final_date - entry_date).days,
            })

            shares = 0
            in_trade = False

        else:
            # ✅ ALL OTHER STRATEGIES → DO NOT FORCE EXIT
            open_trade = {
                "entry_date": entry_date,
                "entry_price": entry_price,
                "entry_volume": entry_volume,
                "current_price": df["close"].iloc[-1],
                "holding_days": (df.index[-1] - entry_date).days,
            }



    # ------------------ OUTPUT ------------------
    portfolio_df = df.copy()
    portfolio_df["equity"] = equity_curve

    trades_df = pd.DataFrame(trades)
    
    return portfolio_df, trades_df, open_trade


      
__all__ = ["run_backtest"]
