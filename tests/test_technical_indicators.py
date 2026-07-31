import numpy as np
import pandas as pd
import pytest

from python_app.indicators import TechnicalIndicators


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=260, freq="D")
    close = pd.Series(
        np.linspace(100, 180, len(index)) + np.sin(np.arange(len(index))), index=index
    )
    return pd.DataFrame(
        {
            "High": close + 2,
            "Low": close - 2,
            "Close": close,
            "Volume": np.arange(1_000, 1_000 + len(index)),
        },
        index=index,
    )


def test_all_indicators_return_expected_columns(ohlcv: pd.DataFrame) -> None:
    result = TechnicalIndicators.calculate_all(ohlcv)
    expected = {
        "rsi_14",
        "macd",
        "macd_signal",
        "ema_20",
        "ema_50",
        "ema_200",
        "sma_20",
        "atr_14",
        "adx",
        "bb_upper",
        "supertrend",
        "vwap",
        "obv",
        "stoch_rsi_k",
        "ichimoku_span_a",
    }
    assert expected.issubset(result.columns)
    assert result.index.equals(ohlcv.index)
    assert result["ema_200"].notna().any()
    assert result["vwap"].notna().all()


def test_invalid_ohlcv_is_rejected(ohlcv: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="missing columns"):
        TechnicalIndicators.calculate_all(ohlcv.drop(columns="Volume"))
    with pytest.raises(ValueError, match="high cannot"):
        TechnicalIndicators.atr(ohlcv["Low"], ohlcv["High"], ohlcv["Close"])
