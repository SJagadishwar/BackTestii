import sys
import os
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

# -------------------------------------------------------#
from ui.overview import render as render_overview
from ui.performance import render as render_performance
from ui.chart import render as render_chart
from ui.trades import render as render_trades
from ui.comparison import render as render_comparison
from ui.tuned_lab import render as render_tuned_lab
from ui.download import render as render_download
from ui.landing import render as render_landing

# -------------------------------------------------------#

# --------------------------------------------------
# Tuned Strategy Storage (Session State)
if "tuned_strategy_store" not in st.session_state:
    st.session_state["tuned_strategy_store"] = {}
# --------------------------------------------------

# ---------------- PATH FIX ----------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------- SNAPSHOT CURRENT STRATEGY ----------
if "current_strategy_snapshot" not in st.session_state:
    st.session_state["current_strategy_snapshot"] = {}



# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="BackTestii",
    page_icon="📈",
    layout="wide",
)


# ---------------- LANDING ROUTING ----------------
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = None

if st.session_state["app_mode"] is None:
    render_landing()
    st.stop()

if st.session_state["app_mode"] in ["candlestick", "options"]:
    render_landing()
    st.stop()



# ---------------- HEADER ----------------
st.markdown(
    """
    <style>
      /* Reduce default top padding so header sits higher */
      section[data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0.75rem;
        padding-bottom: 2rem;
      }

      /* Reduce sidebar top padding so its header aligns with main header */
      section[data-testid="stSidebar"] > div {
        padding-top: 0.75rem;
      }

      .app-header {
        padding: 0.1rem 0 0.35rem 0;
        margin-bottom: 0.35rem;
        border-bottom: 1px solid rgba(49, 51, 63, 0.20);
      }
      .app-header h2 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
      }

      .sidebar-header {
        padding: 0.1rem 0 0.35rem 0;
        margin: 0 0 0.35rem 0;
        border-bottom: 1px solid rgba(49, 51, 63, 0.20);
      }
      .sidebar-header h2 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
      }
    </style>
    <div class="app-header">
      <h2>BackTestii</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION STATE INIT ----------------
for key in ["portfolio_df", "metrics", "trades_df", "comparison_df"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------- SIDEBAR ----------------
st.sidebar.markdown(
    """
    <div class="sidebar-header">
      <h2>Strategy Controls</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- BACK TO LANDING ----------------
if st.sidebar.button("← Back to Home"):
    st.session_state["app_mode"] = None
    st.rerun()

st.sidebar.divider()

# ---------------- ASSET TYPE ----------------
strategy_type = st.sidebar.selectbox(
    "Asset Type",
    ["Equity", "Options"]
)

# ---------------- EXCHANGE & INSTRUMENT ----------------
if strategy_type == "Equity":

    exchange = st.sidebar.selectbox(
        "Exchange",
        ["NSE", "BSE"]
    )

    from ui.api_client import get_instruments, resolve_symbol

    instrument_options = get_instruments(exchange=exchange)

    instrument_name = st.sidebar.selectbox(
        "Instrument",
        options=instrument_options if instrument_options else [],
    )

    ticker = None
    if instrument_name:
        ticker = resolve_symbol(instrument_name, exchange=exchange)
    else:
        st.sidebar.caption("No instrument available for selected exchange")

else:
    ticker = None

# ---------------- STRATEGY REGISTRY ----------------
from ui.api_client import get_strategies
STRATEGY_REGISTRY = get_strategies()

# ---------------- STRATEGY CATEGORY ----------------
all_categories = sorted(
    {meta["category"] for meta in STRATEGY_REGISTRY.values()}
)

selected_category = st.sidebar.selectbox(
    "Strategy Category",
    ["All"] + all_categories,
)

# ---------------- EQUITY STRATEGY SELECTOR ----------------
if strategy_type == "Equity":

    if selected_category == "All":
        filtered_strategy_keys = list(STRATEGY_REGISTRY.keys())
    else:
        filtered_strategy_keys = [
            k for k, v in STRATEGY_REGISTRY.items()
            if v["category"] == selected_category
        ]

    strategy_key = st.sidebar.selectbox(
        "Equity Strategy",
        options=filtered_strategy_keys,
        format_func=lambda k: STRATEGY_REGISTRY[k]["display_name"],
        key="strategy_key",
    )

# ---------------- CAPITAL & DATES ----------------
if strategy_type == "Equity":
    capital = st.sidebar.number_input(
        "Initial Capital",
        min_value=10_000,
        value=100_000,
        step=10_000
    )

    from datetime import date, timedelta

    end_date = st.sidebar.date_input(
        "End Date",
        value=date.today()
    )

    start_date = st.sidebar.date_input(
        "Start Date",
        value=date(2000, 1, 1),
        max_value=end_date - timedelta(days=1)
    )
   
# ---------------- STRATEGY PARAMETERS ----------------
strategy_config = STRATEGY_REGISTRY[strategy_key]

if "strategy_params" not in st.session_state:
    st.session_state["strategy_params"] = {}

strategy_params = st.session_state["strategy_params"]
strategy_params.clear()

if strategy_config["params"]:
    st.sidebar.markdown("### Strategy Parameters")

    for param, cfg in strategy_config["params"].items():
        strategy_params[param] = st.sidebar.number_input(
            label=param.replace("_", " ").title(),
            value=cfg["default"],
            min_value=cfg.get("min"),
            max_value=cfg.get("max"),
            step=cfg.get("step", 1),
            key=f"param_{param}",
        )
    # -----------------------------
    # FINAL snapshot for Tuned Lab
    # (MUST be after params are populated)
    # -----------------------------
    st.session_state["current_strategy_snapshot"] = {
        "strategy_key": strategy_key,
        "params": strategy_params.copy(),
    }

# ---------------- RUN BACKTEST ----------------
if strategy_type == "Equity":
    run_btn = st.sidebar.button("Run Backtest")
else:
    run_btn = None



# =====================================================================
# ============================ RUN BACKTEST ============================
# =====================================================================
if run_btn:

    if strategy_type == "Equity":
        try:
            import pandas as pd
            from ui.api_client import run_backtest as api_run_backtest

            result = api_run_backtest(
                ticker=ticker,
                strategy_key=strategy_key,
                strategy_params=strategy_params,
                start_date=start_date,
                end_date=end_date,
                capital=capital,
            )

            # ---- Metrics (plain dicts, no conversion needed) ----
            st.session_state["strategy"] = STRATEGY_REGISTRY[strategy_key]["display_name"]
            st.session_state["strategy_key"] = strategy_key
            st.session_state["metrics"] = result.get("metrics")
            st.session_state["trade_metrics"] = result.get("trade_metrics")
            st.session_state["open_trade"] = result.get("open_trade")

            # ---- Trades → DataFrame ----
            trades_raw = result.get("trades", [])
            if trades_raw:
                trades_df = pd.DataFrame(trades_raw)
                for col in ("entry_date", "exit_date"):
                    if col in trades_df.columns:
                        trades_df[col] = pd.to_datetime(trades_df[col])
            else:
                trades_df = pd.DataFrame()
            st.session_state["trades_df"] = trades_df

            # ---- Equity Curve → portfolio_df (DatetimeIndex) ----
            equity_raw = result.get("equity_curve", [])
            if equity_raw:
                portfolio_df = pd.DataFrame(equity_raw)
                portfolio_df["date"] = pd.to_datetime(portfolio_df["date"])
                portfolio_df = portfolio_df.set_index("date")
            else:
                portfolio_df = pd.DataFrame()
            st.session_state["portfolio_df"] = portfolio_df

            # ---- Price Data → price_df (DatetimeIndex) ----
            price_raw = result.get("price_data", [])
            if price_raw:
                price_df = pd.DataFrame(price_raw)
                price_df["date"] = pd.to_datetime(price_df["date"])
                price_df = price_df.set_index("date")
            else:
                price_df = pd.DataFrame()
            st.session_state["price_df"] = price_df

            # ---- Signals → signal_df ----
            signals_raw = result.get("signals", [])
            if signals_raw:
                signal_df = pd.DataFrame(signals_raw)
                signal_df["date"] = pd.to_datetime(signal_df["date"])
            else:
                signal_df = pd.DataFrame()
            st.session_state["signal_df"] = signal_df

            # ---- Chart JSON (for Lightweight Charts candlestick) ----
            import json
            st.session_state["chart_json"] = json.dumps(price_raw) if price_raw else None

            st.success("✅ Equity backtest completed successfully (via backend)")

        except Exception as e:
            st.error(f"❌ Equity backtest failed: {e}")



# =================================================================================================
# EQUITY NAVIGATION (STREAMLIT-SAFE, NO TAB JUMPING)
# =================================================================================================
if strategy_type == "Equity":
    
    page = st.radio(
        "Go to",
        ["Overview", "Performance", "Chart", "Trades", "Comparison", "Tuned Lab", "Download"],
        horizontal=True,
        key="equity_navigation",
        label_visibility="collapsed",
    )

    PAGE_ROUTES = {
        "Overview": lambda: render_overview(),
        "Performance": lambda: render_performance(),
        "Chart": lambda: render_chart(),
        "Trades": lambda: render_trades(),
        "Comparison": lambda: render_comparison(ticker, start_date, end_date, capital),
        "Tuned Lab": lambda: render_tuned_lab(ticker, start_date, end_date, capital),
        "Download": lambda: render_download(ticker),
    }

    PAGE_ROUTES[page]()
