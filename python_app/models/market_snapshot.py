from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from python_app.models.stock import Stock


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """Holds the normalized Stock together with its historical
    OHLCV data.

    This object is the bridge between the data layer and the
    recommendation engine.
    """

    stock: Stock
    history: pd.DataFrame
