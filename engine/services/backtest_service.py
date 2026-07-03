from ..data.data_loader import load_price_data, load_index_data
from ..execution.trade_engine import run_backtest
from ..analytics.metrics import calculate_metrics
from ..analytics.trade_metrics import calculate_trade_metrics


class BacktestService:

    def run_equity_backtest(
        self,
        ticker,
        strategy_fn,
        strategy_params,
        start_date,
        end_date,
        capital,
        asset_type="stock",
    ):
        """
        Orchestrates a full equity backtest.

        Parameters
        ----------
        ticker : str
            Yahoo Finance symbol for the instrument.
        strategy_fn : callable
            Strategy function that accepts (price_df, **params) and returns a
            DataFrame with a 'signal' column.
        strategy_params : dict
            Keyword arguments forwarded to strategy_fn.
        start_date : date or str
            Backtest start date.
        end_date : date or str
            Backtest end date.
        capital : float
            Initial capital for the backtest.

        Returns
        -------
        dict
            {
                "price_df": price_df,
                "signal_df": signal_df,
                "portfolio_df": portfolio_df,
                "trades_df": trades_df,
                "metrics": metrics,
                "trade_metrics": trade_metrics,
                "open_trade": open_trade,
            }
        """
        # 1. Load data
        if asset_type == "index":
            price_df = load_index_data(ticker, start_date, end_date)
        else:
            price_df = load_price_data(ticker, start_date, end_date)

        # 2. Execute strategy to generate signals
        signal_df = strategy_fn(price_df, **strategy_params)

        # 3. Run backtest via trade engine
        portfolio_df, trades_df, open_trade = run_backtest(
            price_df=price_df,
            signal_df=signal_df,
            initial_capital=capital,
        )

        # 4. Calculate portfolio-level metrics
        last_exit_date = None
        if trades_df is not None and not trades_df.empty:
            last_exit_date = trades_df["exit_date"].max()

        metrics = calculate_metrics(
            portfolio_df,
            cutoff_date=last_exit_date,
        )

        # 5. Calculate trade-level metrics
        trade_metrics = calculate_trade_metrics(trades_df)

        return {
            "price_df": price_df,
            "signal_df": signal_df,
            "portfolio_df": portfolio_df,
            "trades_df": trades_df,
            "metrics": metrics,
            "trade_metrics": trade_metrics,
            "open_trade": open_trade,
        }
__all__ = ["BacktestService"]
