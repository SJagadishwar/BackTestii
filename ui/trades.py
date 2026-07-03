import streamlit as st
import pandas as pd


def render():
    st.subheader("Trades")

    trades_df = st.session_state.get("trades_df")
    open_trade = st.session_state.get("open_trade")

    # ✅ Buy & Hold safe exit
    if trades_df is None or trades_df.empty:
        st.info("Buy & Hold has no individual trades (single continuous position).")
        st.stop()

    display_trades_df = trades_df.copy()

    # -------- CLEAN TRADES TABLE FOR DISPLAY --------
    # Convert dates to date-only (remove 00:00:00)
    display_trades_df["entry_date"] = pd.to_datetime(
        display_trades_df["entry_date"]
    ).dt.date

    display_trades_df["exit_date"] = pd.to_datetime(
        display_trades_df["exit_date"]
    ).dt.date
   

    if open_trade is not None:
        open_trade_row = {
            "entry_date": open_trade["entry_date"],
            "exit_date": None,
            "entry_price": open_trade["entry_price"],
            "exit_price": None,
            "pnl": None,
            "return_pct": None,
            "holding_days": open_trade["holding_days"],
        }

        display_trades_df = pd.concat(
            [display_trades_df, pd.DataFrame([open_trade_row])],
            ignore_index=True
        )

    # Clean open trade date as well
    display_trades_df["entry_date"] = pd.to_datetime(
        display_trades_df["entry_date"]
    ).dt.date


    if trades_df is None or trades_df.empty:
        st.info("Run a backtest to see trade logs.")
    else:
    # -------------------------
    # Trade Metrics
    # -------------------------
        total_trades = len(trades_df)   # metrics only use CLOSED trades


        winning_trades = trades_df[trades_df["pnl"] > 0]
        losing_trades = trades_df[trades_df["pnl"] <= 0]

        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades else 0
        avg_win = winning_trades["return_pct"].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades["return_pct"].mean() if not losing_trades.empty else 0

        expectancy = (
            (win_rate / 100) * avg_win
            + ((100 - win_rate) / 100) * avg_loss
            if total_trades else 0
        )

        avg_holding = trades_df["holding_days"].mean()

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Total Trades", total_trades)
        col2.metric("Win Rate (%)", round(win_rate, 2))
        col3.metric("Avg Win (%)", round(avg_win, 2))
        col4.metric("Avg Loss (%)", round(avg_loss, 2))
        col5.metric("Expectancy (%)", round(expectancy, 2))
        col6.metric("Avg Holding (days)", round(avg_holding, 1))

        st.markdown("---")
        # Add Trade Number (1,2,3...)
        display_trades_df.insert(
            0, "Trade No", range(1, len(display_trades_df) + 1)
        )

        # Ensure no dataframe index is shown
        display_trades_df.reset_index(drop=True, inplace=True)


        st.dataframe(
            display_trades_df,
            use_container_width=True,
            hide_index=True
        )

    # -------------------------
    # Download Trades
    # -------------------------
        st.download_button(
            label="📥 Download Trades CSV",
            data=display_trades_df.to_csv(index=False),
            file_name="trade_log.csv",
            mime="text/csv",
        )
