import streamlit as st


def render():
    st.subheader("Strategy Overview")

    if st.session_state["metrics"]:
        m = st.session_state["metrics"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Return (%)", round(m["Total Return (%)"], 2))
        c2.metric("CAGR (%)", round(m["CAGR (%)"], 2))
        c3.metric("Max Drawdown (%)", round(m["Max Drawdown (%)"], 2))
        c4.metric("Drawdown Duration (days)", m["Max Drawdown Duration (days)"])
    else:
        st.info("Run a backtest to see results.")