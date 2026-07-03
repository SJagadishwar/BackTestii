# engine/strategies/core.py

import pandas as pd
import numpy as np

#-------------------------------------------------------------------------------BUY & HOLD FUNCTION--------------------------------------------------------------------------------------------#
def buy_and_hold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Buy & Hold strategy.

    Rules
    -----
    - Always stay long
    - Invest on first available day
    - Never exit

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - DatetimeIndex
        - column: 'close'

    Returns
    -------
    pd.DataFrame
        Original DataFrame with:
        - column: 'signal'
          signal = 1 for all rows
    """

    if "close" not in df.columns:
        raise ValueError("DataFrame must contain 'close' column")

    out = df.copy()
    out["signal"] = 1

    return out

#----------------------------------------------------------------------------------SMA CROSS_OVER STRATEGY--------------------------------------------------------------------------------------------#
def sma_crossover(
    df: pd.DataFrame,
    fast: int = 50,
    slow: int = 200,
) -> pd.DataFrame:
    """
    SMA Crossover strategy (Long + Cash).

    Rules
    -----
    - Signal = 1 when fast SMA > slow SMA
    - Signal = 0 otherwise

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - DatetimeIndex
        - column: 'close'

    fast : int
        Fast SMA window (e.g. 9, 20, 50)

    slow : int
        Slow SMA window (e.g. 50, 200, 300)

    Returns
    -------
    pd.DataFrame
        Original DataFrame with:
        - 'sma_fast'
        - 'sma_slow'
        - 'signal'
    """

    if "close" not in df.columns:
        raise ValueError("DataFrame must contain 'close' column")

    if not isinstance(fast, int) or not isinstance(slow, int):
        raise ValueError("SMA windows must be integers")

    if fast <= 0 or slow <= 0:
        raise ValueError("SMA windows must be positive")

    if fast >= slow:
        raise ValueError("Fast SMA must be smaller than slow SMA")

    out = df.copy()

    out["sma_fast"] = out["close"].rolling(window=fast).mean()
    out["sma_slow"] = out["close"].rolling(window=slow).mean()

    out["signal"] = 0
    out.loc[out["sma_fast"] > out["sma_slow"], "signal"] = 1

    out["signal"] = out["signal"].fillna(0)

    return out

#----------------------------------------------------------------------------------RSI MEAN REVERSION STRATEGY--------------------------------------------------------------------------------------------#
def rsi_mean_reversion(
    df: pd.DataFrame,
    period: int = 14,
    oversold: int = 30,
    overbought: int = 70,
) -> pd.DataFrame:
    """
    RSI Mean Reversion (Classic, Regime-based)

    Entry  : RSI < oversold
    Exit   : RSI > overbought
    Hold   : Between oversold and overbought
    """

    if "close" not in df.columns:
        raise ValueError("DataFrame must contain 'close' column")

    out = df.copy()

    # -----------------------------
    # RSI (Wilder)
    # -----------------------------
    delta = out["close"].diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    out["rsi"] = 100 - (100 / (1 + rs))

    # -----------------------------
    # RSI Mean Reversion (STRICT REGIME LOGIC)
    # -----------------------------
    out["signal"] = 0
    in_trade = False

    for i in range(len(out)):
        rsi = out["rsi"].iloc[i]

        if not in_trade:
            # ENTRY: RSI < oversold
            if rsi < oversold:
                in_trade = True
                out.iloc[i, out.columns.get_loc("signal")] = 1
        else:
            # EXIT: RSI > overbought
            if rsi > overbought:
                in_trade = False
                out.iloc[i, out.columns.get_loc("signal")] = 0
            else:
                # HOLD
                out.iloc[i, out.columns.get_loc("signal")] = 1

    return out

#----------------------------------------------------------------------------------RSI WITH TREND FILTER STRATEGY--------------------------------------------------------------------------------------------#
def rsi_with_trend_filter(
    df: pd.DataFrame,
    rsi_period: int = 14,
    oversold: int = 30,
    overbought: int = 70,
    trend_sma: int = 200,
) -> pd.DataFrame:
    """
    RSI Mean Reversion with SMA Trend Filter (Long + Cash).

    Entry:
    - RSI crosses below oversold
    - AND close > SMA(trend_sma)

    Exit:
    - RSI crosses above overbought

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - DatetimeIndex
        - column: 'close'

    rsi_period : int
        RSI lookback period

    oversold : int
        Oversold threshold

    overbought : int
        Overbought threshold

    trend_sma : int
        SMA period used as trend filter (e.g. 100, 200, 300)

    Returns
    -------
    pd.DataFrame
        Original DataFrame with:
        - 'rsi'
        - 'sma_trend'
        - 'signal'
    """

    if "close" not in df.columns:
        raise ValueError("DataFrame must contain 'close' column")

    for name, val in {
        "rsi_period": rsi_period,
        "oversold": oversold,
        "overbought": overbought,
        "trend_sma": trend_sma,
    }.items():
        if not isinstance(val, int):
            raise ValueError(f"{name} must be an integer")

    if rsi_period <= 1:
        raise ValueError("rsi_period must be greater than 1")

    if not (0 < oversold < overbought < 100):
        raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100")

    if trend_sma <= 1:
        raise ValueError("trend_sma must be greater than 1")

    out = df.copy()

    # -----------------------------
    # RSI calculation
    # -----------------------------
    delta = out["close"].diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()

    rs = avg_gain / avg_loss
    out["rsi"] = 100 - (100 / (1 + rs))

    # -----------------------------
    # Trend filter SMA
    # -----------------------------
    out["sma_trend"] = out["close"].rolling(window=trend_sma).mean()

    # -----------------------------
    # Signal generation
    # -----------------------------
    out["signal"] = 0

    enter = (
        (out["rsi"] <= oversold)
        & (out["rsi"].shift(1) > oversold)
        & (out["close"] > out["sma_trend"])
    )

    exit_ = (
        (out["rsi"] >= overbought)
        & (out["rsi"].shift(1) < overbought)
    )

    out.loc[enter, "signal"] = 1
    out.loc[exit_, "signal"] = 0

    # Maintain position state
    out["signal"] = out["signal"].replace(0, np.nan).ffill().fillna(0)

    return out

def _compute_rsi(series, period):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ===================== TREND FOLLOWING =====================

def ema_crossover(df, fast=12, slow=26):
    out = df.copy()
    out["ema_fast"] = out["close"].ewm(span=fast).mean()
    out["ema_slow"] = out["close"].ewm(span=slow).mean()
    out["signal"] = (out["ema_fast"] > out["ema_slow"]).astype(int)
    return out


def price_above_sma(df, period=200):
    out = df.copy()
    out["sma"] = out["close"].rolling(period).mean()
    out["signal"] = (out["close"] > out["sma"]).astype(int)
    return out


def triple_ma(df, fast=20, mid=50, slow=200):
    out = df.copy()
    out["ma_fast"] = out["close"].rolling(fast).mean()
    out["ma_mid"] = out["close"].rolling(mid).mean()
    out["ma_slow"] = out["close"].rolling(slow).mean()
    out["signal"] = (
        (out["ma_fast"] > out["ma_mid"]) &
        (out["ma_mid"] > out["ma_slow"])
    ).astype(int)
    return out


def supertrend(df, atr_period=10, multiplier=3.0):
    """
    SuperTrend Strategy (Trend Following).

    Uses ATR-based dynamic bands around (High+Low)/2.
    Signal = 1 when price is above SuperTrend (bullish).
    Signal = 0 when price is below SuperTrend (bearish).
    """
    out = df.copy()

    high = out["high"]
    low  = out["low"]
    close = out["close"]
    prev_close = close.shift(1)

    # True Range
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)

    # ATR via EMA (Wilder smoothing)
    atr = tr.ewm(span=atr_period, adjust=False).mean()

    # Basic bands
    hl2          = (high + low) / 2
    basic_upper  = hl2 + multiplier * atr
    basic_lower  = hl2 - multiplier * atr

    # Final bands with locking logic
    n             = len(out)
    final_upper   = np.zeros(n)
    final_lower   = np.zeros(n)
    supertrend_v  = np.zeros(n)
    direction     = np.zeros(n)   # +1 = bullish, -1 = bearish

    final_upper[0]  = basic_upper.iloc[0]
    final_lower[0]  = basic_lower.iloc[0]
    supertrend_v[0] = basic_upper.iloc[0]
    direction[0]    = -1

    for i in range(1, n):
        # Lock upper band
        if basic_upper.iloc[i] < final_upper[i-1] or close.iloc[i-1] > final_upper[i-1]:
            final_upper[i] = basic_upper.iloc[i]
        else:
            final_upper[i] = final_upper[i-1]

        # Lock lower band
        if basic_lower.iloc[i] > final_lower[i-1] or close.iloc[i-1] < final_lower[i-1]:
            final_lower[i] = basic_lower.iloc[i]
        else:
            final_lower[i] = final_lower[i-1]

        # Flip direction
        if supertrend_v[i-1] == final_upper[i-1]:   # was bearish
            if close.iloc[i] > final_upper[i]:
                supertrend_v[i] = final_lower[i]
                direction[i]    = 1
            else:
                supertrend_v[i] = final_upper[i]
                direction[i]    = -1
        else:                                         # was bullish
            if close.iloc[i] < final_lower[i]:
                supertrend_v[i] = final_upper[i]
                direction[i]    = -1
            else:
                supertrend_v[i] = final_lower[i]
                direction[i]    = 1

    out["supertrend"]           = supertrend_v
    out["supertrend_upper"]     = final_upper
    out["supertrend_lower"]     = final_lower
    out["supertrend_direction"] = direction
    out["signal"]               = (direction == 1).astype(int)

    return out


# ===================== MEAN REVERSION =====================

def rsi_2_mean_reversion(
    df,
    period=2,
    oversold=10,
    exit_level=50,
):
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(period).mean() / loss.rolling(period).mean()
    rsi = 100 - (100 / (1 + rs))

    out = df.copy()
    out["rsi"] = rsi

    # ---- Position-style signal ----
    signal = []
    in_position = False

    for v in rsi:
        if not in_position and v < oversold:
            in_position = True
        elif in_position and v > exit_level:
            in_position = False

        signal.append(1 if in_position else 0)

    out["signal"] = signal
    return out

def williams_r(
    df,
    period=14,
    oversold=-80,
    exit_level=-50,
):
    out = df.copy()

    high = out["high"].rolling(period).max()
    low = out["low"].rolling(period).min()

    wr = -100 * (high - out["close"]) / (high - low)
    out["williams_r"] = wr

    # ---- Position-style signal ----
    signal = []
    in_position = False

    for v in wr:
        if not in_position and v < oversold:
            in_position = True
        elif in_position and v > exit_level:
            in_position = False

        signal.append(1 if in_position else 0)

    out["signal"] = signal

    return out


# ===================== BREAKOUT =====================

def high_breakout(df, lookback=252):
    out = df.copy()
    out["high"] = out["close"].rolling(lookback).max()
    out["signal"] = (out["close"] >= out["high"]).astype(int)
    return out


# ===================== MOMENTUM =====================

def roc_momentum(df, period=20):
    out = df.copy()
    out["roc"] = df["close"].pct_change(period)
    out["signal"] = (out["roc"] > 0).astype(int)
    return out


def momentum_12_1(df):
    out = df.copy()
    out["ret"] = df["close"].pct_change(252) - df["close"].pct_change(21)
    out["signal"] = (out["ret"] > 0).astype(int)
    return out

def bollinger_mean_reversion(df, period=20, std_dev=2):
    out = df.copy()

    # ---- Bollinger Bands ----
    out["bb_mid"] = out["close"].rolling(period).mean()
    std = out["close"].rolling(period).std()

    out["bb_upper"] = out["bb_mid"] + std_dev * std
    out["bb_lower"] = out["bb_mid"] - std_dev * std

    # ---- Position-style signal ----
    signal = []
    in_position = False

    for close, lower, mid in zip(
        out["close"], out["bb_lower"], out["bb_mid"]
    ):
        if not in_position and close < lower:
            in_position = True
        elif in_position and close > mid:
            in_position = False

        signal.append(1 if in_position else 0)

    out["signal"] = signal

    return out


def donchian_breakout(df, lookback=20):
    out = df.copy()

    donchian_high = out["close"].rolling(lookback).max()

    out["signal"] = (out["close"] >= donchian_high).astype(int)

    return out

def stochastic_mean_reversion(
    df,
    k_period=14,
    d_period=3,
    oversold=20,
    exit_level=50,
):
    out = df.copy()

    # -----------------------------
    # Stochastic Oscillator (SAFE)
    # -----------------------------
    low_min = out["low"].rolling(k_period).min()
    high_max = out["high"].rolling(k_period).max()

    range_ = high_max - low_min

    # Prevent division by zero
    range_ = range_.replace(0, pd.NA)

    stoch_k = 100 * (out["close"] - low_min) / range_
    stoch_k = stoch_k.clip(lower=0, upper=100)

    stoch_d = stoch_k.rolling(d_period).mean()

    out["stoch_k"] = stoch_k
    out["stoch_d"] = stoch_d


    # -----------------------------
    # Position-style signal
    # -----------------------------
    signal = []
    in_position = False

    for k in stoch_k:
        if not in_position and k < oversold:
            in_position = True
        elif in_position and k > exit_level:
            in_position = False

        signal.append(1 if in_position else 0)

    out["signal"] = signal

    return out



def zscore_mean_reversion(
    df,
    lookback=20,
    entry_z=-2.0,
    exit_z=-0.25,
):
    out = df.copy()

    mean = out["close"].rolling(lookback).mean()
    std = out["close"].rolling(lookback).std()

    z = (out["close"] - mean) / std
    out["zscore"] = z

    # ✅ PRICE-SPACE BANDS FOR CHART
    out["z_mean"] = mean
    out["z_upper"] = mean + abs(entry_z) * std
    out["z_lower"] = mean - abs(entry_z) * std

    # ---- Position-style signal ----
    signal = []
    in_position = False

    for v in z:
        if not in_position and v < entry_z:
            in_position = True
        elif in_position and v > exit_z:
            in_position = False

        signal.append(1 if in_position else 0)

    out["signal"] = signal
    return out


def ma_slope_momentum(df, lookback=50):
    out = df.copy()

    ma = out["close"].rolling(lookback).mean()
    slope = ma.diff()

    out["ma_slope"] = slope
    out["signal"] = (slope > 0).astype(int)

    return out

def price_high_momentum(df, lookback=50):
    out = df.copy()

    prior_high = out["close"].shift(1).rolling(lookback).max()
    out["prior_high"] = prior_high

    out["signal"] = (out["close"] > prior_high).astype(int)

    return out

def absolute_momentum(df, lookback=252):
    out = df.copy()

    returns = out["close"].pct_change(lookback)
    out["abs_momentum"] = returns

    out["signal"] = (returns > 0).astype(int)

    return out



STRATEGY_EXECUTION_MAP = {
    "BUY_HOLD": buy_and_hold,
    "SMA_CROSSOVER": sma_crossover,
    "RSI_MEAN_REVERSION": rsi_mean_reversion,
    "EMA_CROSSOVER": ema_crossover,
    "PRICE_ABOVE_SMA": price_above_sma,
    "TRIPLE_MA": triple_ma,
    "RSI_2_MR": rsi_2_mean_reversion,
    "WILLIAMS_R": williams_r,
    "HIGH_BREAKOUT": high_breakout,
    "ROC_MOMENTUM": roc_momentum,
    "MOMENTUM_12_1": momentum_12_1,
    "BOLLINGER_MEAN_REVERSION": bollinger_mean_reversion,
    "DONCHIAN_BREAKOUT": donchian_breakout,
    "STOCHASTIC_MEAN_REVERSION": stochastic_mean_reversion,
    "ZSCORE_MEAN_REVERSION": zscore_mean_reversion,
    "MA_SLOPE_MOMENTUM": ma_slope_momentum,
    "PRICE_HIGH_MOMENTUM": price_high_momentum,
    "ABSOLUTE_MOMENTUM": absolute_momentum,
    "SUPERTREND": supertrend,
}
__all__ = [
    "buy_and_hold",
    "sma_crossover",
    "rsi_mean_reversion",
    "rsi_with_trend_filter",
    "ema_crossover",
    "price_above_sma",
    "triple_ma",
    "rsi_2_mean_reversion",
    "williams_r",
    "high_breakout",
    "roc_momentum",
    "momentum_12_1",
    "bollinger_mean_reversion",
    "donchian_breakout",
    "stochastic_mean_reversion",
    "zscore_mean_reversion",
    "ma_slope_momentum",
    "price_high_momentum",
    "absolute_momentum",
    "supertrend",
    "STRATEGY_EXECUTION_MAP",
]
