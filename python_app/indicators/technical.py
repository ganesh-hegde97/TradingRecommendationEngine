"""Vectorized technical indicators for OHLCV market data.

Every method preserves the input index and returns pandas Series or DataFrames.  Values
before an indicator has enough history are ``NaN`` by design; callers should not treat
them as signals.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Stateless, reusable collection of common technical-analysis indicators."""

    @staticmethod
    def sma(close: pd.Series, period: int = 20) -> pd.Series:
        TechnicalIndicators._period(period)
        return (
            TechnicalIndicators._series(close, "close")
            .rolling(period, min_periods=period)
            .mean()
            .rename(f"sma_{period}")
        )

    @staticmethod
    def ema(close: pd.Series, period: int = 20) -> pd.Series:
        TechnicalIndicators._period(period)
        return (
            TechnicalIndicators._series(close, "close")
            .ewm(span=period, adjust=False, min_periods=period)
            .mean()
            .rename(f"ema_{period}")
        )

    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        TechnicalIndicators._period(period)
        change = TechnicalIndicators._series(close, "close").diff()
        gains = change.clip(lower=0)
        losses = -change.clip(upper=0)
        avg_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        relative_strength = avg_gain / avg_loss.replace(0, np.nan)
        result = 100 - (100 / (1 + relative_strength))
        return (
            result.where(~((avg_gain > 0) & (avg_loss == 0)), 100.0)
            .where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
            .rename(f"rsi_{period}")
        )

    @staticmethod
    def macd(
        close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        TechnicalIndicators._period(fast)
        TechnicalIndicators._period(slow)
        TechnicalIndicators._period(signal)
        if fast >= slow:
            raise ValueError("fast period must be smaller than slow period")
        values = TechnicalIndicators._series(close, "close")
        fast_ema = values.ewm(span=fast, adjust=False, min_periods=fast).mean()
        slow_ema = values.ewm(span=slow, adjust=False, min_periods=slow).mean()
        line = fast_ema - slow_ema
        signal_line = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
        return pd.DataFrame(
            {
                "macd": line,
                "macd_signal": signal_line,
                "macd_histogram": line - signal_line,
            }
        )

    @staticmethod
    def atr(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        TechnicalIndicators._period(period)
        high, low, close = TechnicalIndicators._ohlc(high, low, close)
        true_range = pd.concat(
            (high - low, (high - close.shift()).abs(), (low - close.shift()).abs()),
            axis=1,
        ).max(axis=1)
        return (
            true_range.ewm(alpha=1 / period, adjust=False, min_periods=period)
            .mean()
            .rename(f"atr_{period}")
        )

    @staticmethod
    def adx(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.DataFrame:
        TechnicalIndicators._period(period)
        high, low, close = TechnicalIndicators._ohlc(high, low, close)
        upward = high.diff()
        downward = -low.diff()
        plus_dm = upward.where((upward > downward) & (upward > 0), 0.0)
        minus_dm = downward.where((downward > upward) & (downward > 0), 0.0)
        atr = TechnicalIndicators.atr(high, low, close, period)
        plus_di = (
            100
            * plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
            / atr.replace(0, np.nan)
        )
        minus_di = (
            100
            * minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
            / atr.replace(0, np.nan)
        )
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        return pd.DataFrame({"adx": adx, "plus_di": plus_di, "minus_di": minus_di})

    @staticmethod
    def bollinger_bands(
        close: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> pd.DataFrame:
        TechnicalIndicators._period(period)
        if std_dev <= 0:
            raise ValueError("std_dev must be positive")
        values = TechnicalIndicators._series(close, "close")
        middle = values.rolling(period, min_periods=period).mean()
        deviation = values.rolling(period, min_periods=period).std(ddof=0)
        return pd.DataFrame(
            {
                "bb_lower": middle - std_dev * deviation,
                "bb_middle": middle,
                "bb_upper": middle + std_dev * deviation,
            }
        )

    @staticmethod
    def supertrend(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 10,
        multiplier: float = 3.0,
    ) -> pd.DataFrame:
        TechnicalIndicators._period(period)
        if multiplier <= 0:
            raise ValueError("multiplier must be positive")
        high, low, close = TechnicalIndicators._ohlc(high, low, close)
        atr = TechnicalIndicators.atr(high, low, close, period)
        midpoint = (high + low) / 2
        upper = midpoint + multiplier * atr
        lower = midpoint - multiplier * atr
        final_upper, final_lower = upper.copy(), lower.copy()
        trend = pd.Series(np.nan, index=close.index, dtype=float)
        direction = pd.Series(np.nan, index=close.index, dtype=float)
        for index in range(1, len(close)):
            if pd.isna(atr.iloc[index]):
                continue
            previous = index - 1
            final_upper.iloc[index] = (
                upper.iloc[index]
                if upper.iloc[index] < final_upper.iloc[previous]
                or close.iloc[previous] > final_upper.iloc[previous]
                else final_upper.iloc[previous]
            )
            final_lower.iloc[index] = (
                lower.iloc[index]
                if lower.iloc[index] > final_lower.iloc[previous]
                or close.iloc[previous] < final_lower.iloc[previous]
                else final_lower.iloc[previous]
            )
            if pd.isna(direction.iloc[previous]):
                direction.iloc[index] = 1.0
            elif close.iloc[index] > final_upper.iloc[previous]:
                direction.iloc[index] = 1.0
            elif close.iloc[index] < final_lower.iloc[previous]:
                direction.iloc[index] = -1.0
            else:
                direction.iloc[index] = direction.iloc[previous]
            trend.iloc[index] = (
                final_lower.iloc[index]
                if direction.iloc[index] > 0
                else final_upper.iloc[index]
            )
        return pd.DataFrame(
            {
                "supertrend": trend,
                "supertrend_direction": direction,
                "supertrend_upper": final_upper,
                "supertrend_lower": final_lower,
            }
        )

    @staticmethod
    def vwap(
        high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series
    ) -> pd.Series:
        high, low, close = TechnicalIndicators._ohlc(high, low, close)
        volume = TechnicalIndicators._series(volume, "volume")
        if (volume < 0).any():
            raise ValueError("volume cannot be negative")
        typical_price = (high + low + close) / 3
        return (
            (typical_price * volume).cumsum() / volume.cumsum().replace(0, np.nan)
        ).rename("vwap")

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        close, volume = TechnicalIndicators._series(
            close, "close"
        ), TechnicalIndicators._series(volume, "volume")
        if (volume < 0).any():
            raise ValueError("volume cannot be negative")
        direction = np.sign(close.diff()).fillna(0)
        return (direction * volume).cumsum().rename("obv")

    @staticmethod
    def stochastic_rsi(
        close: pd.Series,
        rsi_period: int = 14,
        stochastic_period: int = 14,
        k_period: int = 3,
        d_period: int = 3,
    ) -> pd.DataFrame:
        for period in (rsi_period, stochastic_period, k_period, d_period):
            TechnicalIndicators._period(period)
        rsi = TechnicalIndicators.rsi(close, rsi_period)
        low = rsi.rolling(stochastic_period, min_periods=stochastic_period).min()
        high = rsi.rolling(stochastic_period, min_periods=stochastic_period).max()
        raw = 100 * (rsi - low) / (high - low).replace(0, np.nan)
        k = raw.rolling(k_period, min_periods=k_period).mean()
        d = k.rolling(d_period, min_periods=d_period).mean()
        return pd.DataFrame({"stoch_rsi": raw, "stoch_rsi_k": k, "stoch_rsi_d": d})

    @staticmethod
    def ichimoku(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        conversion_period: int = 9,
        base_period: int = 26,
        span_b_period: int = 52,
        displacement: int = 26,
    ) -> pd.DataFrame:
        for period in (conversion_period, base_period, span_b_period, displacement):
            TechnicalIndicators._period(period)
        high, low, close = TechnicalIndicators._ohlc(high, low, close)
        midpoint = (
            lambda period: (
                high.rolling(period, min_periods=period).max()
                + low.rolling(period, min_periods=period).min()
            )
            / 2
        )
        conversion = midpoint(conversion_period)
        base = midpoint(base_period)
        span_a = ((conversion + base) / 2).shift(displacement)
        span_b = midpoint(span_b_period).shift(displacement)
        return pd.DataFrame(
            {
                "ichimoku_conversion": conversion,
                "ichimoku_base": base,
                "ichimoku_span_a": span_a,
                "ichimoku_span_b": span_b,
                "ichimoku_lagging": close.shift(-displacement),
            }
        )

    @staticmethod
    def calculate_all(data: pd.DataFrame) -> pd.DataFrame:
        """Return the Version 2.1 indicator set for an OHLCV DataFrame.

        ``data`` must contain case-sensitive ``High``, ``Low``, ``Close``, and ``Volume`` columns.
        """
        required = {"High", "Low", "Close", "Volume"}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(
                f"OHLCV data is missing columns: {', '.join(sorted(missing))}"
            )
        high, low, close, volume = (
            data["High"],
            data["Low"],
            data["Close"],
            data["Volume"],
        )
        return pd.concat(
            (
                TechnicalIndicators.rsi(close),
                TechnicalIndicators.macd(close),
                TechnicalIndicators.ema(close, 20),
                TechnicalIndicators.ema(close, 50),
                TechnicalIndicators.ema(close, 200),
                TechnicalIndicators.sma(close, 20),
                TechnicalIndicators.atr(high, low, close),
                TechnicalIndicators.adx(high, low, close),
                TechnicalIndicators.bollinger_bands(close),
                TechnicalIndicators.supertrend(high, low, close),
                TechnicalIndicators.vwap(high, low, close, volume),
                TechnicalIndicators.obv(close, volume),
                TechnicalIndicators.stochastic_rsi(close),
                TechnicalIndicators.ichimoku(high, low, close),
            ),
            axis=1,
        )

    @staticmethod
    def _series(values: pd.Series, name: str) -> pd.Series:
        if not isinstance(values, pd.Series):
            raise TypeError(f"{name} must be a pandas Series")
        return pd.to_numeric(values, errors="coerce").astype(float)

    @classmethod
    def _ohlc(
        cls, high: pd.Series, low: pd.Series, close: pd.Series
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        high, low, close = (
            cls._series(high, "high"),
            cls._series(low, "low"),
            cls._series(close, "close"),
        )
        if (high < low).any():
            raise ValueError("high cannot be lower than low")
        return high, low, close

    @staticmethod
    def _period(period: int) -> None:
        if not isinstance(period, int) or period <= 0:
            raise ValueError("period must be a positive integer")
