import json


class ChartService:

    def prepare_price_chart_json(self, price_df):
        """
        Convert a price DataFrame into a JSON string suitable for charting.

        Parameters
        ----------
        price_df : pd.DataFrame
            DataFrame with a DatetimeIndex (or 'date' column) and OHLCV columns.

        Returns
        -------
        str
            JSON string of records with keys: date, open, high, low, close, volume.
        """
        df = price_df.reset_index().copy()
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        records = df[["date", "open", "high", "low", "close", "volume"]].to_dict(
            orient="records"
        )

        return json.dumps(records)
