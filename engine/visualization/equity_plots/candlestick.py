# engine/equity_plots/candlestick.py

import pandas as pd
import mplfinance as mpf


def plot_candlestick_chart(
    price_df: pd.DataFrame,
    title: str = "Price Chart",
):
    """
    Candlestick chart (price only).

    Parameters
    ----------
    price_df : pd.DataFrame
        Must contain:
        - DatetimeIndex
        - open, high, low, close

    title : str
        Chart title

    Returns
    -------
    matplotlib.figure.Figure
    """

    # ------------------ VALIDATION ------------------
    required_cols = {"open", "high", "low", "close"}
    if not required_cols.issubset(price_df.columns):
        raise ValueError(
            f"price_df must contain columns: {required_cols}"
        )

    if not isinstance(price_df.index, pd.DatetimeIndex):
        raise ValueError("price_df index must be a DatetimeIndex")

    # ------------------ PREP DATA ------------------
    ohlc_df = price_df[["open", "high", "low", "close"]].copy()
    ohlc_df.index.name = "Date"

    # ------------------ STYLE ------------------
    mc = mpf.make_marketcolors(
        up="green",
        down="red",
        wick="inherit",
        edge="inherit",
        volume="inherit",
    )

    style = mpf.make_mpf_style(
        base_mpf_style="classic",
        marketcolors=mc,
        gridstyle=":",
        gridcolor="lightgray",
    )

    # ------------------ PLOT ------------------
    fig, _ = mpf.plot(
        ohlc_df,
        type="candle",
        style=style,
        title=title,
        ylabel="Price",
        figsize=(12, 6),
        returnfig=True,
        xrotation=15,
        tight_layout=True,
        show_nontrading=False,
    )

    return fig
