def plot_price_with_signals(
    price_df,
    signal_df,
    trades_df,
    is_buy_and_hold=False, 
    show_position=True,
    show_entries=True,
    show_exits=True,
    position_opacity=0.08,
):

    import matplotlib.pyplot as plt
    import pandas as pd

    fig, ax = plt.subplots(figsize=(12, 4))

    # ---- Price ----
    ax.plot(
        price_df.index,
        price_df["close"],
        label="Price",
        linewidth=1.2,
    )

    
    
    if show_position:

        if is_buy_and_hold:
            # 🔒 Buy & Hold = ONE continuous position
            ax.axvspan(
                price_df.index[0],
                price_df.index[-1],
                color="green",
                alpha=position_opacity,
                label="In Position",
                zorder=0,
            )
        else:
            position = signal_df["signal"].reindex(price_df.index).fillna(0)

            ax.fill_between(
                price_df.index,
                price_df["close"].min(),
                price_df["close"].max(),
                where=(position == 1),
                color="green",
                alpha=position_opacity,
                label="In Position",
                zorder=0,
            )


    # ---- Entry markers (from trades) ----
    if trades_df is not None and not trades_df.empty and "entry_date" in trades_df:
        entry_dates = trades_df["entry_date"]
    else:
        entry_dates = []

    # ---- Exit markers (from trades) ----
    if trades_df is not None and not trades_df.empty and "exit_date" in trades_df:
        exit_dates = trades_df["exit_date"]
    else:
        exit_dates = []


    if show_entries:
        ax.scatter(
            entry_dates,
            price_df.loc[entry_dates, "close"],
            marker="^",
            color="green",
            s=80,
            label="Entry",
            zorder=5,
        )


   

    if show_exits:
        ax.scatter(
            exit_dates,
            price_df.loc[exit_dates, "close"],
            marker="v",
            color="red",
            s=80,
            label="Exit",
            zorder=5,
        )


    ax.set_title("Price with Strategy Signals")
    ax.legend()
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)

    return fig
