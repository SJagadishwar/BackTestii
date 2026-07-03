# engine/equity_plots/interactive_candlestick.py

import pandas as pd
import plotly.graph_objects as go


def plot_interactive_candlestick(
    price_df: pd.DataFrame,
    title: str = "Price Chart",
):
    """
    Interactive candlestick chart (Plotly).

    Features:
    - Zoom / pan
    - Hover OHLC
    - Full price history

    Parameters
    ----------
    price_df : pd.DataFrame
        Must contain:
        - DatetimeIndex
        - open, high, low, close

    Returns
    -------
    plotly.graph_objects.Figure
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
    df = price_df.copy().reset_index()

    price_min = price_df["low"].min()
    price_max = price_df["high"].max()
    padding = (price_max - price_min) * 0.05


    # ------------------ CANDLESTICK ------------------
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                increasing_line_color="#2ECC71",   # premium green
                decreasing_line_color="#E74C3C",   # premium red
                increasing_fillcolor="#2ECC71",
                decreasing_fillcolor="#E74C3C",
                name="Price",
            )
        ]
    )

    # ------------------ LAYOUT ------------------
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",

        dragmode="pan",
        hovermode="x unified",
        uirevision="price-chart",
        yaxis_range=[price_min - padding, price_max + padding],

        xaxis=dict(
            rangeslider_visible=False,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=True,
        ),

        yaxis=dict(
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=True,
            autorange=False,
            fixedrange=False,
            rangemode="normal",
        ),

        template="plotly_dark",
        height=650,
        margin=dict(l=60, r=40, t=60, b=50),
    )


    return fig
