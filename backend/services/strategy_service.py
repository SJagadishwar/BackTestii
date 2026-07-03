# backend/services/strategy_service.py
"""
Service layer that wraps engine.api calls and returns
JSON-serializable Python dictionaries.

This is the single abstraction point between the engine
(core quantitative library) and any consumer (FastAPI, Streamlit, CLI).

Rules:
  - Receives plain Python parameters
  - Calls engine.api
  - Converts all results to JSON-serializable dicts/lists
  - Never exposes pandas DataFrames, numpy types, or lambdas
"""

import pandas as pd
from engine.api import (
    run_backtest as _engine_run_backtest,
    run_comparison as _engine_run_comparison,
    run_tuned_comparison as _engine_run_tuned_comparison,
    list_strategies as _engine_list_strategies,
    list_instruments as _engine_list_instruments,
    resolve_symbol as _engine_resolve_symbol,
)


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _serialize_timestamp(val):
    """Convert pandas Timestamp / datetime to ISO string."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    return str(val)


def _safe_float(val):
    """Convert numpy/pandas numeric to plain Python float."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return float(val)


def _safe_int(val):
    """Convert numpy/pandas int to plain Python int."""
    if val is None:
        return None
    return int(val)


def _serialize_trades(trades_df: pd.DataFrame) -> list[dict]:
    """Convert trades DataFrame to a list of JSON-safe dicts."""
    if trades_df is None or trades_df.empty:
        return []

    rows = []
    for _, row in trades_df.iterrows():
        rows.append({
            "entry_date": _serialize_timestamp(row.get("entry_date")),
            "exit_date": _serialize_timestamp(row.get("exit_date")),
            "entry_price": _safe_float(row.get("entry_price")),
            "exit_price": _safe_float(row.get("exit_price")),
            "entry_volume": _safe_float(row.get("entry_volume")),
            "pnl": _safe_float(row.get("pnl")),
            "return_pct": _safe_float(row.get("return_pct")),
            "holding_days": _safe_int(row.get("holding_days")),
        })

    return rows


def _serialize_open_trade(open_trade: dict | None) -> dict | None:
    """Convert open trade dict to JSON-safe dict."""
    if open_trade is None:
        return None

    return {
        "entry_date": _serialize_timestamp(open_trade.get("entry_date")),
        "entry_price": _safe_float(open_trade.get("entry_price")),
        "entry_volume": _safe_float(open_trade.get("entry_volume")),
        "current_price": _safe_float(open_trade.get("current_price")),
        "holding_days": _safe_int(open_trade.get("holding_days")),
    }


def _serialize_metrics(metrics: dict) -> dict:
    """Ensure all metric values are plain Python types."""
    if metrics is None:
        return {}

    return {k: _safe_float(v) if isinstance(v, (int, float)) else v
            for k, v in metrics.items()}


def _serialize_equity_curve(portfolio_df: pd.DataFrame) -> list[dict]:
    """Convert portfolio DataFrame to a JSON-safe equity curve."""
    if portfolio_df is None or portfolio_df.empty:
        return []

    df = portfolio_df.reset_index()
    records = []
    for _, row in df.iterrows():
        records.append({
            "date": _serialize_timestamp(row.get("date")),
            "close": _safe_float(row.get("close")),
            "equity": _safe_float(row.get("equity")),
        })

    return records


def _serialize_price_data(price_df: pd.DataFrame) -> list[dict]:
    """Convert price DataFrame (OHLCV) to a JSON-safe list of dicts."""
    if price_df is None or price_df.empty:
        return []

    df = price_df.reset_index()
    records = []
    for _, row in df.iterrows():
        records.append({
            "date": _serialize_timestamp(row.get("date")),
            "open": _safe_float(row.get("open")),
            "high": _safe_float(row.get("high")),
            "low": _safe_float(row.get("low")),
            "close": _safe_float(row.get("close")),
            "volume": _safe_float(row.get("volume")),
        })

    return records


def _serialize_signals(signal_df: pd.DataFrame, price_df: pd.DataFrame) -> list[dict]:
    """Extract BUY/SELL signal transitions from the signal DataFrame.

    A BUY occurs when signal transitions from 0 → 1.
    A SELL occurs when signal transitions from 1 → 0.
    """
    if signal_df is None or signal_df.empty:
        return []
    if "signal" not in signal_df.columns:
        return []

    df = signal_df.reset_index().copy()
    price = price_df.reset_index() if price_df is not None else df

    signals = []
    prev = 0
    for i, row in df.iterrows():
        curr = int(row["signal"]) if pd.notna(row["signal"]) else 0
        if curr == 1 and prev == 0:
            signals.append({
                "date": _serialize_timestamp(row.get("date")),
                "signal": "BUY",
                "price": _safe_float(row.get("close", price.iloc[i]["close"] if i < len(price) else None)),
            })
        elif curr == 0 and prev == 1:
            signals.append({
                "date": _serialize_timestamp(row.get("date")),
                "signal": "SELL",
                "price": _safe_float(row.get("close", price.iloc[i]["close"] if i < len(price) else None)),
            })
        prev = curr

    return signals


# ---------------------------------------------------------------------------
# Public Service Functions
# ---------------------------------------------------------------------------

def list_strategies() -> dict:
    """
    Return a JSON-serializable registry of all available strategies.

    Strips non-serializable fields (e.g. label_builder lambdas) and
    returns a clean dict keyed by strategy key.

    Returns
    -------
    dict
        {
            "STRATEGY_KEY": {
                "display_name": str,
                "short_name": str | None,
                "category": str,
                "signal_type": str,
                "description": str | None,
                "is_baseline": bool,
                "tunable": bool,
                "params": { param_name: {default, min, max, step} }
            },
            ...
        }
    """
    raw = _engine_list_strategies()

    serialized = {}
    for key, meta in raw.items():
        serialized[key] = {
            "display_name": meta.get("display_name", key),
            "short_name": meta.get("short_name"),
            "category": meta.get("category", "Uncategorized"),
            "signal_type": meta.get("signal_type", "position"),
            "description": meta.get("description"),
            "is_baseline": meta.get("is_baseline", False),
            "tunable": meta.get("tunable", True),
            "params": {
                param_name: {
                    "default": cfg.get("default"),
                    "min": cfg.get("min"),
                    "max": cfg.get("max"),
                    "step": cfg.get("step", 1),
                }
                for param_name, cfg in meta.get("params", {}).items()
            },
        }

    return serialized


def run_backtest(
    ticker: str,
    strategy_key: str,
    strategy_params: dict | None,
    start_date,
    end_date,
    capital: float,
    asset_type: str = "stock",
) -> dict:
    """
    Run a full equity backtest and return JSON-serializable results.

    Returns
    -------
    dict
        {
            "metrics": { ... },
            "trade_metrics": { ... },
            "trades": [ {...}, ... ],
            "open_trade": { ... } | None,
            "equity_curve": [ {date, close, equity}, ... ],
            "price_data": [ {date, open, high, low, close, volume}, ... ],
            "signals": [ {date, signal, price}, ... ],
            "chart_config": { ... } | None,
            "overlay_data": { overlays: [...], data: [...] } | None,
            "oscillator_data": { panel, range, lines, data } | None,
        }
    """
    result = _engine_run_backtest(
        ticker=ticker,
        strategy_key=strategy_key,
        strategy_params=strategy_params or {},
        start_date=start_date,
        end_date=end_date,
        capital=capital,
        asset_type=asset_type,
    )

    # Chart config + indicator data
    from engine.strategies.chart_config import STRATEGY_CHART_CONFIG, INDICATOR_PANELS

    chart_cfg = STRATEGY_CHART_CONFIG.get(strategy_key, {})
    indicator_cfg = INDICATOR_PANELS.get(strategy_key)
    signal_df = result.get("signal_df")

    # Serialize overlay data (SMA/EMA/Bollinger bands)
    overlay_data = None
    overlay_cfgs = chart_cfg.get("price_overlays")
    if overlay_cfgs and signal_df is not None:
        overlay_cols = {o["column"] for o in overlay_cfgs}
        if overlay_cols.issubset(signal_df.columns):
            overlay_df = signal_df[list(overlay_cols)].reset_index().dropna()
            overlay_df["date"] = overlay_df["date"].dt.strftime("%Y-%m-%d")
            overlay_data = {
                "overlays": [
                    {"column": o["column"], "label": o["label"], "color": o["color"]}
                    for o in overlay_cfgs
                ],
                "data": overlay_df.to_dict(orient="records"),
            }

    # Serialize oscillator data (RSI/Z-Score/Stochastic)
    oscillator_data = None
    if indicator_cfg and signal_df is not None:
        lines = indicator_cfg["lines"]
        required_cols = {l["column"] for l in lines if "column" in l}
        if required_cols.issubset(signal_df.columns):
            ind_df = signal_df[list(required_cols)].reset_index().dropna()
            ind_df["date"] = ind_df["date"].dt.strftime("%Y-%m-%d")
            oscillator_data = {
                "panel": indicator_cfg["panel"],
                "range": indicator_cfg["range"],
                "lines": lines,
                "data": ind_df.to_dict(orient="records"),
            }

    return {
        "metrics": _serialize_metrics(result.get("metrics")),
        "trade_metrics": _serialize_metrics(result.get("trade_metrics")),
        "trades": _serialize_trades(result.get("trades_df")),
        "open_trade": _serialize_open_trade(result.get("open_trade")),
        "equity_curve": _serialize_equity_curve(result.get("portfolio_df")),
        "price_data": _serialize_price_data(result.get("price_df")),
        "signals": _serialize_signals(result.get("signal_df"), result.get("price_df")),
        "chart_config": chart_cfg if chart_cfg else None,
        "overlay_data": overlay_data,
        "oscillator_data": oscillator_data,
    }



def get_results_summary(
    ticker: str,
    strategy_key: str,
    strategy_params: dict | None,
    start_date,
    end_date,
    capital: float,
    asset_type: str = "stock",
) -> dict:
    """
    Run a backtest and return only the summary metrics (no curves or trades).

    This is a lightweight alternative to run_backtest() when the caller
    only needs the headline numbers.

    Returns
    -------
    dict
        {
            "metrics": { ... },
            "trade_metrics": { ... },
            "open_trade": { ... } | None,
            "total_trades": int,
        }
    """
    result = _engine_run_backtest(
        ticker=ticker,
        strategy_key=strategy_key,
        strategy_params=strategy_params or {},
        start_date=start_date,
        end_date=end_date,
        capital=capital,
        asset_type=asset_type,
    )

    trades_df = result.get("trades_df")
    total_trades = len(trades_df) if trades_df is not None and not trades_df.empty else 0

    return {
        "metrics": _serialize_metrics(result.get("metrics")),
        "trade_metrics": _serialize_metrics(result.get("trade_metrics")),
        "open_trade": _serialize_open_trade(result.get("open_trade")),
        "total_trades": total_trades,
    }


def get_trades(
    ticker: str,
    strategy_key: str,
    strategy_params: dict | None,
    start_date,
    end_date,
    capital: float,
    asset_type: str = "stock",
) -> dict:
    """
    Run a backtest and return the trade log and open trade info.

    Returns
    -------
    dict
        {
            "trades": [ {...}, ... ],
            "open_trade": { ... } | None,
            "total_trades": int,
        }
    """
    result = _engine_run_backtest(
        ticker=ticker,
        strategy_key=strategy_key,
        strategy_params=strategy_params or {},
        start_date=start_date,
        end_date=end_date,
        capital=capital,
        asset_type=asset_type,
    )

    trades_df = result.get("trades_df")
    total_trades = len(trades_df) if trades_df is not None and not trades_df.empty else 0

    return {
        "trades": _serialize_trades(trades_df),
        "open_trade": _serialize_open_trade(result.get("open_trade")),
        "total_trades": total_trades,
    }


def list_instruments(exchange: str | None = None) -> list[str]:
    """
    Return a sorted list of available instrument display names.

    Parameters
    ----------
    exchange : str | None
        Filter by exchange (e.g. "NSE", "BSE"). None returns all.

    Returns
    -------
    list[str]
        Sorted list of instrument search names.
    """
    return _engine_list_instruments(exchange=exchange)


def resolve_symbol(search_name: str, exchange: str | None = None) -> str:
    """
    Resolve a display/search name to a Yahoo Finance ticker symbol.

    Parameters
    ----------
    search_name : str
        The instrument display name selected by the user.
    exchange : str | None
        Exchange filter.

    Returns
    -------
    str
        Yahoo Finance ticker symbol.
    """
    return _engine_resolve_symbol(search_name, exchange=exchange)


def _serialize_comparison_df(df: pd.DataFrame) -> list:
    """Convert a comparison DataFrame to a list of JSON-safe dicts."""
    if df is None or df.empty:
        return []
    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if isinstance(val, str):
                record[col] = val
            elif isinstance(val, (int,)):
                record[col] = int(val)
            else:
                try:
                    record[col] = round(float(val), 4)
                except (TypeError, ValueError):
                    record[col] = str(val)
        records.append(record)
    return records


def _serialize_equity_curves_dict(equity_curves: dict) -> dict:
    """Convert {strategy_name: DataFrame} to {strategy_name: [{date, equity}]}."""
    result = {}
    for name, df in equity_curves.items():
        result[name] = _serialize_equity_curve(df)
    return result


def run_comparison(ticker: str, start_date, end_date, capital: float, asset_type: str = "stock") -> dict:
    """
    Run all registered strategies and return a comparison table + equity curves.

    Returns
    -------
    dict
        {
            "comparison": [ {Strategy, Total Return (%), CAGR (%), ...}, ... ],
            "equity_curves": { "Strategy Name": [{date, equity}], ... },
        }
    """
    result = _engine_run_comparison(
        ticker=ticker,
        start_date=str(start_date),
        end_date=str(end_date),
        capital=capital,
        asset_type=asset_type,
    )

    return {
        "comparison": _serialize_comparison_df(result["comparison_df"]),
        "equity_curves": _serialize_equity_curves_dict(result["equity_curves"]),
    }


def run_tuned_comparison(
    ticker: str,
    start_date,
    end_date,
    capital: float,
    tuned_runs: dict,
    include_buy_hold: bool = False,
    asset_type: str = "stock",
) -> dict:
    """
    Run tuned strategy configurations and return results + equity curves.

    Parameters
    ----------
    tuned_runs : dict
        Maps label -> {"strategy_key": str, "params": dict}
    include_buy_hold : bool
        If True, include Buy & Hold baseline.

    Returns
    -------
    dict
        {
            "comparison": [ {Strategy, Total Return (%), CAGR (%), ...}, ... ],
            "equity_curves": { "Label": [{date, equity}], ... },
        }
    """
    result = _engine_run_tuned_comparison(
        ticker=ticker,
        start_date=str(start_date),
        end_date=str(end_date),
        capital=capital,
        tuned_runs=tuned_runs,
        include_buy_hold=include_buy_hold,
        asset_type=asset_type,
    )

    return {
        "comparison": _serialize_comparison_df(result["tuned_df"]),
        "equity_curves": _serialize_equity_curves_dict(result["equity_curves"]),
    }
