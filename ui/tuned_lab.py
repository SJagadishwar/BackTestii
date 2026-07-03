import streamlit as st
from engine.api import run_tuned_comparison, list_strategies, plot_equity_overlay


def render(ticker, start_date, end_date, capital):
    st.markdown("## 🧪 Tuned Strategy Lab")
    st.caption("Experiment with parameters and compare tuned strategies.")

    # ---------- SESSION STATE ----------
    if "tuned_runs" not in st.session_state:
        st.session_state["tuned_runs"] = {}

    # ---------- CONTROLS ----------
    tuned_sort_metric = st.selectbox(
        "Sort tuned strategies by",
        ["CAGR (%)", "Total Return (%)", "Max Drawdown (%)"],
        index=0,
        key="tuned_sort_metric",
    )

    include_buy_hold = st.checkbox(
        "Include Buy & Hold baseline",
        value=False,
    )
    st.caption("Buy & Hold is a global baseline, not a tuned strategy.")


    
    add_strategy = st.button("➕ Add current tuned strategy")
    clear_all = st.button("🧹 Clear all tuned strategies")

    
    # ---------- ADD STRATEGY ----------
    if add_strategy:

        snapshot = st.session_state.get("current_strategy_snapshot")

        if not snapshot:
            st.warning("No strategy snapshot available.")
            st.stop()

        skey = snapshot["strategy_key"]
        safe_params = snapshot["params"]

        # ❌ Never add Buy & Hold as tuned
        if skey == "BUY_HOLD":
            st.info("Buy & Hold is a baseline and does not need to be added.")
            st.stop()

        STRATEGY_REGISTRY = list_strategies()
        meta = STRATEGY_REGISTRY[skey]

        label = meta["label_builder"](safe_params)

        if label in st.session_state["tuned_runs"]:
            st.warning("This tuned configuration already exists.")
            st.stop()

        st.session_state["tuned_runs"][label] = {
            "strategy_key": skey,
            "params": safe_params,
        }

        st.rerun()



    # ---------- CLEAR ----------
    if clear_all:
        st.session_state["tuned_runs"].clear()
        st.rerun()

    # ---------- RUN STRATEGIES ----------
    try:
        result = run_tuned_comparison(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            capital=capital,
            tuned_runs=st.session_state["tuned_runs"],
            include_buy_hold=include_buy_hold,
        )

        tuned_df = result["tuned_df"]
        tuned_equity_curves = result["equity_curves"]

        # ---------- DISPLAY ----------
        if not tuned_df.empty:

            ascending = tuned_sort_metric == "Max Drawdown (%)"
            tuned_df = tuned_df.sort_values(
                by=tuned_sort_metric,
                ascending=ascending,
            ).reset_index(drop=True)

            tuned_df.insert(0, "Rank", tuned_df.index + 1)
            tuned_df["Remove"] = False

            edited_df = st.data_editor(
                tuned_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Remove": st.column_config.CheckboxColumn(
                        "Remove", help="Remove strategy"
                    )
                },
                disabled=[c for c in tuned_df.columns if c != "Remove"],
            )

            # ---------- HANDLE REMOVALS ----------
            to_remove = edited_df.loc[
                edited_df["Remove"], "Strategy"
            ].tolist()

            for name in to_remove:
                if name != "Buy & Hold":
                    st.session_state["tuned_runs"].pop(name, None)

            if to_remove:
                st.rerun()

            st.session_state["tuned_results_df"] = edited_df.drop(columns=["Remove"])

            st.session_state["tuned_equity_curves"] = tuned_equity_curves

            st.markdown("### 📈 Tuned Equity Curve Overlay")
            st.pyplot(plot_equity_overlay(tuned_equity_curves))

        else:
            st.info("No tuned strategies to compare.")

    except Exception as e:
        st.error(f"Error in tuned strategy lab: {e}")
