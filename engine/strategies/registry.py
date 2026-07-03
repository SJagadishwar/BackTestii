# engine/strategies/registry.py

STRATEGY_REGISTRY = {
    "BUY_HOLD": {
        "display_name": "Buy & Hold",
        "short_name": "Buy & Hold",
        "category": "Buy & Hold",
        "signal_type": "position",

        # 🔒 BASELINE LOCK
        "is_baseline": True,
        "tunable": False,

        "description": "Always invested. Benchmark strategy.",
        "params": {},
        "label_builder": lambda p: "Buy & Hold",
    },


    "SMA_CROSSOVER": {
        "display_name": "SMA Crossover",
        "short_name": "SMA",
        "category": "Trend Following",
        "signal_type": "position",
        "description": "Long when fast SMA is above slow SMA.",
        "params": {
            "fast": {"default": 50, "min": 5, "max": 100, "step": 5},
            "slow": {"default": 200, "min": 20, "max": 300, "step": 10},
        },
        "label_builder": lambda p: f"SMA ({p['fast']} / {p['slow']})",
    },


    "RSI_MEAN_REVERSION": {
        "display_name": "RSI Mean Reversion",
        "short_name": "RSI MR",
        "category": "Mean Reversion",
        "signal_type": "position",
        "description": "Buys oversold and exits on overbought.",
        "params": {
            "period": {"default": 14, "min": 2, "max": 50},
            "oversold": {"default": 30, "min": 10, "max": 40},
            "overbought": {"default": 70, "min": 60, "max": 90},
        },
        "label_builder": lambda p: (
            f"RSI MR ({p['period']} | {p['oversold']}–{p['overbought']})"
        ),
    },

    "EMA_CROSSOVER": {
        "display_name": "EMA Crossover",
        "short_name": "EMA",
        "category": "Trend Following",
        "signal_type": "position",
        "params": {
            "fast": {"default": 12, "min": 5, "max": 50},
            "slow": {"default": 26, "min": 20, "max": 100},
        },
        "label_builder": lambda p: f"EMA ({p['fast']} / {p['slow']})",
    },

    "PRICE_ABOVE_SMA": {
        "display_name": "Price Above SMA",
        "short_name": "Price > SMA",
        "category": "Trend Following",
        "signal_type": "position",
        "params": {
            "period": {"default": 200, "min": 50, "max": 300},
        },
        "label_builder": lambda p: f"Price > SMA({p['period']})",
    },

    "TRIPLE_MA": {
        "display_name": "Triple Moving Average",
        "short_name": "3MA",
        "category": "Trend Following",
        "signal_type": "position",
        "params": {
            "fast": {"default": 20, "min": 5, "max": 50},
            "mid":  {"default": 50, "min": 20, "max": 100},
            "slow": {"default": 200, "min": 100, "max": 300},
        },
        "label_builder": lambda p: f"3MA ({p['fast']}/{p['mid']}/{p['slow']})",
    },

    "SUPERTREND": {
        "display_name": "SuperTrend",
        "short_name": "ST",
        "category": "Trend Following",
        "signal_type": "position",
        "description": "ATR-based dynamic support/resistance that flips when price crosses the band.",
        "params": {
            "atr_period": {"default": 10, "min": 5, "max": 50, "step": 1},
            "multiplier":  {"default": 3.0, "min": 1.0, "max": 5.0, "step": 0.5},
        },
        "label_builder": lambda p: f"SuperTrend ({p['atr_period']} | {p['multiplier']}x)",
    },

    "RSI_2_MR": {
        "display_name": "RSI(2) Mean Reversion",
        "short_name": "RSI(2)",
        "category": "Mean Reversion",
        "signal_type": "position",
        "params": {
            "period":     {"default": 2,  "min": 2, "max": 5},
            "oversold":   {"default": 10, "min": 5, "max": 30},
            "exit_level": {"default": 50, "min": 30, "max": 70},
        },
        "label_builder": lambda p: f"RSI(2) ({p['oversold']})",
    },

    "WILLIAMS_R": {
        "display_name": "Williams %R Mean Reversion",
        "short_name": "Williams %R",
        "category": "Mean Reversion",
        "signal_type": "position",
        "params": {
            "period": {"default": 14, "min": 5, "max": 30},
            "oversold": {"default": -80, "min": -95, "max": -50},
            "exit_level": {"default": -20, "min": -70, "max": -20},
        },
        "label_builder": lambda p: (
            f"W%R MR ({p['period']} | {p['oversold']} → {p['exit_level']})"
        ),
    },

    "HIGH_BREAKOUT": {
        "display_name": "52-Week High Breakout",
        "short_name": "52W High",
        "category": "Breakout",
        "signal_type": "position",
        "params": {
            "lookback": {"default": 252, "min": 100, "max": 300},
        },
        "label_builder": lambda p: f"52W High ({p['lookback']})",
    },

    "ROC_MOMENTUM": {
        "display_name": "Rate of Change Momentum",
        "short_name": "ROC",
        "category": "Momentum",
        "signal_type": "position",
        "params": {
            "period": {"default": 20, "min": 5, "max": 60},
        },
        "label_builder": lambda p: f"ROC ({p['period']})",
    },

    "MOMENTUM_12_1": {
        "display_name": "12–1 Momentum",
        "short_name": "12–1 Mom",
        "category": "Momentum",
        "signal_type": "position",
        "params": {},
        "label_builder": lambda p: "12–1 Momentum",
    },

    "BOLLINGER_MEAN_REVERSION": {
        "display_name": "Bollinger Mean Reversion",
        "category": "Mean Reversion",
        "signal_type": "position",
        "params": {
            "period": {"default": 20, "min": 10, "max": 50},
            "std_dev": {"default": 2, "min": 1, "max": 3},
        },
        "label_builder": lambda p: f"BB MR ({p['period']} | {p['std_dev']}σ)",
    },

    "DONCHIAN_BREAKOUT": {
        "display_name": "Donchian Breakout",
        "category": "Breakout",
        "signal_type": "position",
        "params": {
            "lookback": {"default": 20, "min": 10, "max": 100},
        },
        "label_builder": lambda p: f"Donchian ({p['lookback']})",
    },

    "STOCHASTIC_MEAN_REVERSION": {
        "display_name": "Stochastic Mean Reversion",
        "category": "Mean Reversion",
        "signal_type": "position",
        "params": {
            "k_period": {"default": 14, "min": 5, "max": 50},
            "oversold": {"default": 20, "min": 5, "max": 30},
            "exit_level": {"default": 80, "min": 30, "max": 100},
        },
        "label_builder": lambda p: (
            f"Stoch MR ({p['k_period']} | {p['oversold']} → {p['exit_level']})"
        ),
    },

    "ZSCORE_MEAN_REVERSION": {
        "display_name": "Z-Score Mean Reversion",
        "category": "Mean Reversion",
        "signal_type": "position",
        "params": {
            "lookback": {
                "default": 20,
                "min": 10,
                "max": 100,
                "step": 1,
            },
            "entry_z": {
                "default": -2.0,
                "min": -4.0,
                "max": -0.5,
                "step": 0.1,
            },
            "exit_z": {
                "default": -0.25,
                "min": -1.0,
                "max": 1.0,
                "step": 0.05,
            },
        },
        "label_builder": lambda p: (
            f"Z-MR ({p['lookback']} | {p['entry_z']} → {p['exit_z']})"
        ),
    },

    "MA_SLOPE_MOMENTUM": {
        "display_name": "MA Slope Momentum",
        "category": "Momentum",
        "signal_type": "position",
        "params": {
            "lookback": {
                "default": 50,
                "min": 10,
                "max": 200,
                "step": 1,
            },
        },
        "label_builder": lambda p: f"MA Slope ({p['lookback']})",
    },

    "PRICE_HIGH_MOMENTUM": {
        "display_name": "Price vs N-Day High",
        "category": "Momentum",
        "signal_type": "position",
        "params": {
            "lookback": {
                "default": 50,
                "min": 20,
                "max": 252,
                "step": 1,
            },
        },
        "label_builder": lambda p: f"Price > {p['lookback']}D High",
    },

    "ABSOLUTE_MOMENTUM": {
        "display_name": "Absolute Momentum",
        "category": "Momentum",
        "signal_type": "position",
        "params": {
            "lookback": {
                "default": 252,
                "min": 60,
                "max": 252,
                "step": 1,
            },
        },
        "label_builder": lambda p: f"Abs Mom ({p['lookback']})",
    },


}
__all__ = ["STRATEGY_REGISTRY"]
