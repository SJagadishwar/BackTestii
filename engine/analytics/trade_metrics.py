import pandas as pd


def calculate_trade_metrics(trades: pd.DataFrame) -> dict:
    """
    Calculate trade-level performance metrics.

    Parameters
    ----------
    trades : pd.DataFrame
        Output of build_trade_log()

    Returns
    -------
    dict
        Trade metrics
    """

    if trades.empty:
        return {
            "Total Trades": 0,
            "Win Rate (%)": 0.0,
            "Avg Win (%)": 0.0,
            "Avg Loss (%)": 0.0,
            "Expectancy (%)": 0.0,
            "Avg Holding Days": 0.0,
        }

    total_trades = len(trades)
    wins = trades[trades["return_pct"] > 0]
    losses = trades[trades["return_pct"] <= 0]

    win_rate = len(wins) / total_trades * 100

    avg_win = wins["return_pct"].mean() if not wins.empty else 0.0
    avg_loss = losses["return_pct"].mean() if not losses.empty else 0.0

    expectancy = (
        (win_rate / 100) * avg_win
        + ((100 - win_rate) / 100) * avg_loss
    )

    avg_holding = trades["holding_days"].mean()

    return {
        "Total Trades": total_trades,
        "Win Rate (%)": round(win_rate, 2),
        "Avg Win (%)": round(avg_win, 2),
        "Avg Loss (%)": round(avg_loss, 2),
        "Expectancy (%)": round(expectancy, 2),
        "Avg Holding Days": round(avg_holding, 1),
    }
__all__ = ["calculate_trade_metrics"]
