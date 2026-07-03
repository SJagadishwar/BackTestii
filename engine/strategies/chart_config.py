# engine/strategies/chart_config.py

"""
Defines how each strategy should be visualized on the Chart tab.

This file is the SINGLE source of truth for:
- Which indicators appear on price chart
- Which toggles apply

The chart engine must remain generic.
"""

STRATEGY_CHART_CONFIG = {

    # ================= TREND FOLLOWING =================

    "SMA_CROSSOVER": {
        "price_overlays": [
            {"column": "sma_fast", "label": "SMA Fast", "color": "#3DA5FF"},
            {"column": "sma_slow", "label": "SMA Slow", "color": "#FF4D4D"},
        ],
        "overlay_label": "SMA Lines",
    },

    "EMA_CROSSOVER": {
        "price_overlays": [
            {"column": "ema_fast", "label": "EMA Fast", "color": "#00C2FF"},
            {"column": "ema_slow", "label": "EMA Slow", "color": "#FF6B6B"},
        ],
        "overlay_label": "EMA Lines",
    },

    "PRICE_ABOVE_SMA": {
        "price_overlays": [
            {"column": "sma", "label": "SMA", "color": "#FFD166"},
        ],
        "overlay_label": "SMA Lines",
    },

    "TRIPLE_MA": {
        "price_overlays": [
            {"column": "ma_fast", "label": "MA Fast", "color": "#3DA5FF"},
            {"column": "ma_mid",  "label": "MA Mid",  "color": "#FFD166"},
            {"column": "ma_slow", "label": "MA Slow", "color": "#FF4D4D"},
        ],
        "overlay_label": "MA Lines",
    },

    "BOLLINGER_MEAN_REVERSION": {
        "overlay_label": "Bollinger Bands",
        "price_overlays": [
            {"column": "bb_upper", "label": "BB Upper", "color": "#FF6B6B"},
            {"column": "bb_mid",   "label": "BB Middle", "color": "#FFD166"},
            {"column": "bb_lower", "label": "BB Lower", "color": "#06D6A0"},
        ],
    },

    "SUPERTREND": {
        "overlay_label": "SuperTrend",
        "price_overlays": [
            {"column": "supertrend", "label": "SuperTrend", "color": "#00E5A0"},
        ],
    },

    # ================= DEFAULT =================
    # Strategies not listed here → price only (no overlays)
}

INDICATOR_PANELS = {

    # ================= RSI =================

    "RSI_MEAN_REVERSION": {
        "panel": "rsi",
        "lines": [
            {"column": "rsi", "label": "RSI", "color": "#F5C542", "isPrimary": True},
            {"level": 70, "label": "Overbought", "color": "#FF4D4D"},
            {"level": 30, "label": "Oversold", "color": "#2ECC71"},
        ],
        "range": [0, 100],
    },

    "RSI_2_MR": {
        "panel": "rsi",
        "lines": [
            {"column": "rsi", "label": "RSI(2)", "color": "#F5C542", "isPrimary": True},
            {"level": 70, "label": "Overbought", "color": "#FF4D4D"},
            {"level": 30, "label": "Oversold", "color": "#2ECC71"},
        ],
        "range": [0, 100],
    },

    # ================= Z-SCORE =================

    "ZSCORE_MEAN_REVERSION": {
        "panel": "zscore",
        "lines": [
            {"column": "zscore", "label": "Z-Score", "color": "#3DA5FF", "isPrimary": True},
            {"level": 0.0, "label": "Mean", "color": "#FFD166"},
            {"level": 2.0, "label": "+2σ", "color": "#EF476F"},
            {"level": -2.0, "label": "-2σ", "color": "#06D6A0"},
        ],
        "range": [-3, 3],
    },

    # ================= WILLIAMS %R =================

    "WILLIAMS_R": {
        "panel": "williams",
        "lines": [
            {"column": "williams_r", "label": "Williams %R", "color": "#9B5DE5", "isPrimary": True},
            {"level": -20, "label": "Overbought", "color": "#FF4D4D"},
            {"level": -80, "label": "Oversold", "color": "#2ECC71"},
        ],
        "range": [-100, 0],
    },

    # ================= STOCHASTIC =================

    "STOCHASTIC_MEAN_REVERSION": {
        "panel": "oscillator",
        "range": [0, 100],
        "lines": [
            {
                "label": "%K",
                "column": "stoch_k",
                "color": "#FFD166",
                "isPrimary": True,
            },
            {
                "label": "%D",
                "column": "stoch_d",
                "color": "#4D96FF",
            },
            {
                "label": "Overbought",
                "level": 80,
                "color": "#FF6B6B",
            },
            {
                "label": "Oversold",
                "level": 20,
                "color": "#06D6A0",
            },
        ],
    },
}

