import streamlit as st


def render(ticker):
    st.subheader("Download Results")

# -------------------------------
# Equity Curve
# -------------------------------
    portfolio_df = st.session_state.get("portfolio_df")

    if portfolio_df is not None and not portfolio_df.empty:
        export_df = portfolio_df.reset_index()
        export_df = export_df.rename(columns={"date": "Date"})

        simple_equity = export_df[["Date", "equity"]].rename(
            columns={"equity": "portfolio_value"}
        )


        st.download_button(
            "📥 Download Equity Curve (Simple)",
            simple_equity.to_csv(index=False),
            file_name=f"equity_curve_{ticker}.csv",
            mime="text/csv",
            key="download_equity_curve",
        )

        detailed_equity = export_df.rename(columns={
            "close": "close_price",
            "signal": "position",
            "equity": "portfolio_value",
        })

        detailed_equity["daily_pnl"] = detailed_equity["portfolio_value"].diff()

        st.download_button(
            label="📥 Download Equity Curve (Detailed)",
            data=detailed_equity.to_csv(index=False),
            file_name=f"equity_curve_detailed_{ticker}.csv",
            mime="text/csv",
            key="download_equity_detailed",
        )

        st.markdown("## 🧪 Tuned Strategy Results")

        tuned_df = st.session_state.get("tuned_results_df")

        if tuned_df is not None and not tuned_df.empty:
            st.download_button(
                label="📥 Download Tuned Strategy Results (CSV)",
                data=tuned_df.to_csv(index=False),
                file_name="tuned_strategy_results.csv",
                mime="text/csv",
            )
        else:
            st.info("No tuned strategies available to download.")


        st.markdown("## 📈 Tuned Strategy Equity Curves")

        tuned_equity_curves = st.session_state.get("tuned_equity_curves", {})

        if tuned_equity_curves:
            for strategy_name, df in tuned_equity_curves.items():
                export_df = df.reset_index()
                export_df = export_df.rename(columns={"date": "Date"})

                equity_csv = export_df[["Date", "equity"]].rename(
                    columns={"equity": "portfolio_value"}
                )

                st.download_button(
                    label=f"📥 Download Equity Curve — {strategy_name}",
                    data=equity_csv.to_csv(index=False),
                    file_name=f"tuned_equity_{strategy_name.replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"download_tuned_{strategy_name}",
                )
        else:
            st.info("No tuned equity curves available.")


        st.markdown("## 📊 Strategy Comparison Results")

        comparison_df = st.session_state.get("comparison_df")

        if comparison_df is not None and not comparison_df.empty:
            st.download_button(
                label="📥 Download Strategy Comparison (CSV)",
                data=comparison_df.to_csv(index=False),
                file_name="strategy_comparison.csv",
                mime="text/csv",
            )
        else:
            st.info("No strategy comparison data available.")

        st.markdown("## 📈 Strategy Comparison Equity Curves")

        comparison_equity_curves = st.session_state.get(
            "comparison_equity_curves", {}
        )

        if comparison_equity_curves:
            for strategy_name, df in comparison_equity_curves.items():
                export_df = df.reset_index()
                export_df = export_df.rename(columns={"date": "Date"})

                equity_csv = export_df[["Date", "equity"]].rename(
                    columns={"equity": "portfolio_value"}
                )

                st.download_button(
                    label=f"📥 Download Equity Curve — {strategy_name}",
                    data=equity_csv.to_csv(index=False),
                    file_name=f"comparison_equity_{strategy_name.replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"download_comp_{strategy_name}",
                )
        else:
            st.info("No comparison equity curves available.")


    else:
        st.info("Equity curve not available.")
