from __future__ import annotations

from typing import Any

from python_app.indicators.technical import TechnicalIndicators
from python_app.recommendations.engine import (
    TechnicalSnapshot,
    FundamentalAssessment,
)


class SnapshotBuilder:
    """
    Converts raw market data into strongly typed domain snapshots.

    This is the only place responsible for transforming Stock objects
    into the objects consumed by RecommendationEngine.
    """

    def __init__(self) -> None:
        self._technical = TechnicalIndicators()

    # ----------------------------------------------------
    # Public API
    # ----------------------------------------------------

    def build_technical_snapshot(self, stock: Any) -> TechnicalSnapshot:
        """
        Build TechnicalSnapshot from Stock.

        Parameters
        ----------
        stock
            Current Stock model produced by MarketDataService.
        """

        indicators = self._technical.calculate(stock)

        return TechnicalSnapshot(
            symbol=stock.symbol,
            current_price=stock.last_price,
            sma20=indicators.get("sma20"),
            sma50=indicators.get("sma50"),
            sma200=indicators.get("sma200"),
            ema20=indicators.get("ema20"),
            ema50=indicators.get("ema50"),
            ema200=indicators.get("ema200"),
            rsi14=indicators.get("rsi14"),
            macd=indicators.get("macd"),
            macd_signal=indicators.get("macd_signal"),
            macd_histogram=indicators.get("macd_histogram"),
            atr14=indicators.get("atr14"),
            adx14=indicators.get("adx14"),
            volume_ratio=stock.volume_ratio,
            one_month_return=stock.return_1m_pct,
            three_month_return=stock.return_3m_pct,
            six_month_return=stock.return_6m_pct,
        )

    def build_fundamental_snapshot(
        self,
        stock: Any,
    ) -> FundamentalAssessment:
        """
        Build FundamentalAssessment from Stock.
        """

        return FundamentalAssessment(
            pe=stock.pe_ratio,
            roe=stock.roe_pct,
            debt_to_equity=stock.debt_to_equity,
            market_cap=stock.market_cap_cr,
            sector=stock.sector,
        )
