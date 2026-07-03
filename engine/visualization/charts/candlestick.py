# engine/charts/candlestick.py

import plotly.graph_objects as go


def plot_candlestick(price_df, title="Price Chart"):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=price_df.index,
                open=price_df["open"],
                high=price_df["high"],
                low=price_df["low"],
                close=price_df["close"],
                increasing_line_color="#2ECC71",
                decreasing_line_color="#E74C3C",
                increasing_fillcolor="#2ECC71",
                decreasing_fillcolor="#E74C3C",
                whiskerwidth=0.4,
            )
        ]
    )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        height=600,
        margin=dict(l=60, r=40, t=50, b=40),
        xaxis_rangeslider_visible=False,

        # ✅ mouse drag only
        dragmode="pan",

        # ❌ prevent zoom distortion
        xaxis_fixedrange=False,
        yaxis_fixedrange=False,
    )

    # ❌ remove zoom & autoscale tools
    fig.update_layout(
        modebar=dict(
            remove=[
                "zoom",
                "zoomin",
                "zoomout",
                "autoscale",
                "resetScale",
                "lasso2d",
                "select2d",
            ]
        )
    )

    return fig

