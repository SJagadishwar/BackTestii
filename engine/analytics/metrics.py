import pandas as pd


def calculate_metrics(
    df: pd.DataFrame,
    cutoff_date: pd.Timestamp | None = None
) -> dict:

    """
    Calculate portfolio performance metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - 'equity' column
        - DatetimeIndex

    Returns
    -------
    dict
        Performance metrics
    """

    if "equity" not in df.columns:
        raise ValueError("DataFrame must contain 'equity' column")

    # -----------------------------
    # Truncate equity at last closed trade if cutoff_date is provided
    # -----------------------------
    if cutoff_date is not None:
        df = df.loc[:cutoff_date]

        if len(df) < 2:
            raise ValueError("Not enough data after applying cutoff_date")

    # Use truncated equity
    equity = df["equity"]



    # -----------------------------
    # Total Return
    # -----------------------------
    total_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100

    # -----------------------------
    # CAGR
    # -----------------------------
    days = (equity.index[-1] - equity.index[0]).days
    years = days / 365.25

    if years <= 0:
        cagr = 0.0
    else:
        cagr = ((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) * 100

    # -----------------------------
    # Drawdowns
    # -----------------------------
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max

    max_drawdown = drawdown.min() * 100

    # Drawdown duration
    drawdown_end = drawdown.idxmin()
    drawdown_start = equity.loc[:drawdown_end].idxmax()
    drawdown_duration = (drawdown_end - drawdown_start).days

    return {
        "Total Return (%)": float(round(total_return, 2)),
        "CAGR (%)": float(round(cagr, 2)),
        "Max Drawdown (%)": float(round(max_drawdown, 2)),
        "Max Drawdown Duration (days)": int(drawdown_duration),
    }
__all__ = ["calculate_metrics"]

