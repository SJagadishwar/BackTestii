import pandas as pd
from .backtest_service import BacktestService


class ComparisonService:

    def build_standard_comparison(
        self,
        ticker,
        start_date,
        end_date,
        capital,
        strategy_registry,
        strategy_execution_map,
        asset_type="stock",
    ):
        """
        Run every registered strategy with default parameters and return a
        comparison DataFrame plus per-strategy equity curves.

        Parameters
        ----------
        ticker : str
            Yahoo Finance symbol.
        start_date : date or str
            Backtest start date.
        end_date : date or str
            Backtest end date.
        capital : float
            Initial capital for each backtest.
        strategy_registry : dict
            Maps strategy keys to metadata dicts (must contain 'params' and
            'display_name').
        strategy_execution_map : dict
            Maps strategy keys to callable strategy functions.

        Returns
        -------
        dict
            {
                "comparison_df": pd.DataFrame,
                "equity_curves": dict[str, pd.DataFrame],
            }
        """
        strategies = []
        equity_curves = {}

        for strategy_key, meta in strategy_registry.items():
            strategy_fn = strategy_execution_map.get(strategy_key)
            if strategy_fn is None:
                continue

            # Use DEFAULT parameters for fair comparison
            default_params = {
                k: v["default"] for k, v in meta["params"].items()
            }

            result = BacktestService().run_equity_backtest(
                ticker=ticker,
                strategy_fn=strategy_fn,
                strategy_params=default_params,
                start_date=start_date,
                end_date=end_date,
                capital=capital,
                asset_type=asset_type,
            )

            portfolio_df = result["portfolio_df"]
            trades_df = result["trades_df"]
            metrics = result["metrics"]

            label = meta["display_name"]
            strategies.append({"Strategy": label, **metrics})

            last_exit_date = None
            if trades_df is not None and not trades_df.empty:
                last_exit_date = trades_df["exit_date"].max()

            plot_df = portfolio_df
            if last_exit_date is not None:
                plot_df = portfolio_df.loc[:last_exit_date]

            equity_curves[label] = plot_df

        comparison_df = pd.DataFrame(strategies)

        return {
            "comparison_df": comparison_df,
            "equity_curves": equity_curves,
        }
__all__ = ["ComparisonService"]
