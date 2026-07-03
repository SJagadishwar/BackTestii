import pandas as pd
from .backtest_service import BacktestService
from ..strategy import buy_and_hold


class TunedService:

    def build_tuned_comparison(
        self,
        ticker,
        start_date,
        end_date,
        capital,
        tuned_runs,
        include_buy_hold,
        strategy_execution_map,
        strategy_registry,
        asset_type="stock",
    ):
        """
        Run each tuned strategy configuration and optionally a Buy & Hold
        baseline, returning a results DataFrame and equity curves.

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
        tuned_runs : dict
            Maps label -> {"strategy_key": str, "params": dict}.
        include_buy_hold : bool
            If True, append a Buy & Hold baseline row.
        strategy_execution_map : dict
            Maps strategy keys to callable strategy functions.
        strategy_registry : dict
            Maps strategy keys to metadata dicts.

        Returns
        -------
        dict
            {
                "tuned_df": pd.DataFrame,
                "equity_curves": dict[str, pd.DataFrame],
            }
        """
        tuned_results = []
        equity_curves = {}

        # --- Tuned strategies ---
        for label, run in tuned_runs.items():
            skey = run["strategy_key"]
            params = run["params"]

            fn = strategy_execution_map[skey]

            result = BacktestService().run_equity_backtest(
                ticker=ticker,
                strategy_fn=fn,
                strategy_params=params,
                start_date=start_date,
                end_date=end_date,
                capital=capital,
                asset_type=asset_type,
            )

            portfolio_df = result["portfolio_df"]
            trades_df = result["trades_df"]
            metrics = result["metrics"]

            tuned_results.append({"Strategy": label, **metrics})

            last_exit_date = None
            if trades_df is not None and not trades_df.empty:
                last_exit_date = trades_df["exit_date"].max()

            plot_df = portfolio_df
            if last_exit_date is not None:
                plot_df = portfolio_df.loc[:last_exit_date]

            equity_curves[label] = plot_df

        # --- Buy & Hold (ONCE, GLOBAL) ---
        if include_buy_hold:
            bh_result = BacktestService().run_equity_backtest(
                ticker=ticker,
                strategy_fn=buy_and_hold,
                strategy_params={},
                start_date=start_date,
                end_date=end_date,
                capital=capital,
                asset_type=asset_type,
            )

            bh_metrics = bh_result["metrics"]
            bh_portfolio = bh_result["portfolio_df"]

            tuned_results.append({"Strategy": "Buy & Hold", **bh_metrics})
            equity_curves["Buy & Hold"] = bh_portfolio

        tuned_df = pd.DataFrame(tuned_results)

        return {
            "tuned_df": tuned_df,
            "equity_curves": equity_curves,
        }
__all__ = ["TunedService"]
