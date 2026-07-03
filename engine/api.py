from .services.backtest_service import BacktestService
from .services.comparison_service import ComparisonService
from .services.tuned_service import TunedService
from .strategies.registry import STRATEGY_REGISTRY
from .strategies.core import STRATEGY_EXECUTION_MAP
from .instruments.registry import list_instruments as _list_instruments, resolve_symbol as _resolve_symbol
from .services.chart_service import ChartService
from .visualization import plot_equity_and_drawdown, plot_price_with_signals, plot_equity_overlay
from .strategies.chart_config import STRATEGY_CHART_CONFIG, INDICATOR_PANELS


def run_backtest(
    ticker: str,
    strategy_key: str,
    strategy_params: dict | None,
    start_date,
    end_date,
    capital: float,
    asset_type: str = "stock",
) -> dict:
    fn = STRATEGY_EXECUTION_MAP[strategy_key]
    svc = BacktestService()
    return svc.run_equity_backtest(
        ticker=ticker,
        strategy_fn=fn,
        strategy_params=strategy_params or {},
        start_date=start_date,
        end_date=end_date,
        capital=capital,
        asset_type=asset_type,
    )


def run_comparison(
    ticker: str,
    start_date,
    end_date,
    capital: float,
    asset_type: str = "stock",
) -> dict:
    svc = ComparisonService()
    return svc.build_standard_comparison(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        capital=capital,
        strategy_registry=STRATEGY_REGISTRY,
        strategy_execution_map=STRATEGY_EXECUTION_MAP,
        asset_type=asset_type,
    )


def run_tuned_comparison(
    ticker: str,
    start_date,
    end_date,
    capital: float,
    tuned_runs: dict,
    include_buy_hold: bool,
    asset_type: str = "stock",
) -> dict:
    svc = TunedService()
    return svc.build_tuned_comparison(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        capital=capital,
        tuned_runs=tuned_runs,
        include_buy_hold=include_buy_hold,
        strategy_execution_map=STRATEGY_EXECUTION_MAP,
        strategy_registry=STRATEGY_REGISTRY,
        asset_type=asset_type,
    )


def list_strategies() -> dict:
    return STRATEGY_REGISTRY


def list_instruments(exchange: str | None = None) -> list:
    return _list_instruments(exchange=exchange)


def resolve_symbol(search_name: str, exchange: str | None = None) -> str:
    return _resolve_symbol(search_name, exchange=exchange)


def prepare_price_chart_json(price_df) -> str:
    return ChartService().prepare_price_chart_json(price_df)


__all__ = [
    "run_backtest",
    "run_comparison",
    "run_tuned_comparison",
    "list_strategies",
    "STRATEGY_REGISTRY",
    "STRATEGY_EXECUTION_MAP",
    "list_instruments",
    "resolve_symbol",
    "prepare_price_chart_json",
    "plot_equity_and_drawdown",
    "plot_price_with_signals",
    "plot_equity_overlay",
    "STRATEGY_CHART_CONFIG",
    "INDICATOR_PANELS",
]
