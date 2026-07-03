import streamlit as st
from engine.api import run_comparison, plot_equity_overlay


def render(ticker, start_date, end_date, capital):
    st.subheader("Strategy Comparison")
    st.markdown("## 🅰️ Standard Strategy Comparison")
    st.caption("Uses fixed default parameters for fair, reproducible comparison.")

    sort_metric = st.selectbox(
        "Sort strategies by",
        ["CAGR (%)", "Total Return (%)", "Max Drawdown (%)"],
        index=0,
    )

    try:
        result = run_comparison(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            capital=capital,
        )

        comparison_df = result["comparison_df"]
        equity_curves = result["equity_curves"]

        ascending = sort_metric == "Max Drawdown (%)"
        comparison_df = comparison_df.sort_values(
            by=sort_metric, ascending=ascending
        ).reset_index(drop=True)

        comparison_df.insert(0, "Rank", comparison_df.index + 1)

        st.markdown("### 📈 Equity Curve Overlay")

        # Default: Top 3 strategies by selected metric
        default_strategies = comparison_df["Strategy"].head(3).tolist()

        selected_strategies = st.multiselect(
            "Select strategies to visualize",
            options=comparison_df["Strategy"].tolist(),
            default=default_strategies,
        )


        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.markdown("### 📈 Equity Curve Overlay")
        filtered_equity_curves = {
            name: equity_curves[name]
            for name in selected_strategies
            if name in equity_curves
        }

        if filtered_equity_curves:
            st.pyplot(plot_equity_overlay(filtered_equity_curves))
        else:
            st.info("Select at least one strategy to display the equity curve.")
        
        st.session_state["comparison_df"] = comparison_df
        st.session_state["comparison_equity_curves"] = filtered_equity_curves

        
    except Exception as e:
        st.error(f"Error building standard comparison: {e}")
