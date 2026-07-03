"""
Visualization public API layer.

This module exposes all visualization functions
so the app layer never imports internal modules directly.
"""

from .plots import (
    plot_equity_and_drawdown,
    plot_equity_overlay,
)

from .equity_plots.candlestick import (
    plot_candlestick_chart,
)

from .equity_plots.interactive_candlestick import (
    plot_interactive_candlestick,
)

from .charts.candlestick import (
    plot_candlestick,
)

from .signal_plots import (
    plot_price_with_signals,
)
