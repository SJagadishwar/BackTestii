import streamlit as st
import matplotlib.pyplot as plt
from engine.api import (
    plot_equity_and_drawdown,
    plot_price_with_signals,
)


def render():
    st.session_state.active_tab = "Performance"
    st.subheader("Performance")

    portfolio_df = st.session_state.get("portfolio_df")

    if portfolio_df is None or portfolio_df.empty:
        st.info("Run a backtest to see performance.")
    else:
        strategy_name = st.session_state.get("strategy", "Strategy")

        last_exit_date = None
        trades_df = st.session_state.get("trades_df")

        if trades_df is not None and not trades_df.empty:
            last_exit_date = trades_df["exit_date"].max()

        plot_df = portfolio_df
        if last_exit_date is not None:
            plot_df = portfolio_df.loc[:last_exit_date]

        fig = plot_equity_and_drawdown(
            plot_df,
            title=f"Equity Curve — {strategy_name}"
        )

        st.pyplot(fig)
        plt.close(fig)

    price_df = st.session_state.get("price_df")
    signal_df = st.session_state.get("signal_df")
    trades_df = st.session_state.get("trades_df")

    # ---------- SAFE DEFAULTS ----------
    show_entries = True
    show_exits = True

    if trades_df is None or trades_df.empty:
        show_entries = False
        show_exits = False

    
    if price_df is not None and signal_df is not None and trades_df is not None:

        st.markdown("#### 📍 Strategy Signal Verification")
        st.markdown("### 🎛️ Chart Display Controls")


        col1, col2, col3, col4 = st.columns(4)

        with col1:
            show_position = st.checkbox(
                "Show In-Position",
                value=True,
                key="show_position_toggle",
            )

        with col2:
            show_entries = st.checkbox(
                "Show Entry Markers",
                value=True,
                key="show_entry_toggle",
            )

        with col3:
            show_exits = st.checkbox(
                "Show Exit Markers",
                value=True,
                key="show_exit_toggle",
            )

        with col4:
            position_opacity = st.slider(
                "Position Opacity",
                min_value=0.05,
                max_value=0.3,
                value=0.08,
                step=0.01,
                key="position_opacity_slider",
            )
        
       
        is_buy_and_hold = (
            st.session_state.get("strategy_key") == "BUY_HOLD"
        )

        st.pyplot(
            plot_price_with_signals(
                price_df,
                signal_df,
                trades_df,
                is_buy_and_hold=is_buy_and_hold,   # 👈 PASS IT
                show_position=show_position,
                show_entries=show_entries,
                show_exits=show_exits,
                position_opacity=position_opacity,
            )
        )


    else:
        st.info("Run a backtest to see strategy signals.")
