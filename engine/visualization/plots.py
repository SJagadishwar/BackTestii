import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_and_drawdown(
    df: pd.DataFrame,
    title: str = "Equity Curve",
):
    """
    Plot equity curve with drawdown shading.
    Streamlit-safe version.
    """

    import matplotlib.pyplot as plt

    if "equity" not in df.columns:
        raise ValueError("DataFrame must contain 'equity' column")

    equity = df["equity"]

    # ---- Drawdown calculation ----
    rolling_max = equity.cummax()

    # ---- Create isolated figure (CRITICAL) ----
    fig, ax = plt.subplots(figsize=(12, 5))

    # ---- Equity curve ----
    ax.plot(equity.index, equity.values, label="Equity", color="blue")

    # ---- Drawdown shading ----
    ax.fill_between(
        equity.index,
        equity.values,
        rolling_max.values,
        where=equity.values < rolling_max.values,
        color="red",
        alpha=0.3,
        label="Drawdown",
    )

    ax.set_title(title)
    ax.set_ylabel("Portfolio Value")
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig



#-----------------------------------------------------------------------------------------------------PLOT EQUITY OVERLAY--------------------------------------------------------------------------------------------------------#
def plot_equity_overlay(
    equity_curves: dict,
    title: str = "Multi-Strategy Equity Curve Comparison",
):
    """
    Plot multiple equity curves on a single chart.

    Parameters
    ----------
    equity_curves : dict
        Dictionary of {strategy_name: DataFrame}
        Each DataFrame must contain an 'equity' column

    title : str
        Plot title
    """

    if not isinstance(equity_curves, dict) or len(equity_curves) == 0:
        raise ValueError("equity_curves must be a non-empty dictionary")

    plt.figure(figsize=(12, 6))

    for name, df in equity_curves.items():
        if "equity" not in df.columns:
            raise ValueError(f"DataFrame for '{name}' must contain 'equity' column")

        plt.plot(df.index, df["equity"], label=name)

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

#-------------------------------------------------------------------------------HELPER FUNCTION--------------------------------------------------------------------------------#
def plot_equity_overlay(equity_dict):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))

    for strategy_name, df in equity_dict.items():
        ax.plot(df.index, df["equity"], label=strategy_name)

    ax.set_title("Equity Curve Comparison")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value")
    ax.legend()
    ax.grid(alpha=0.3)

    return fig
