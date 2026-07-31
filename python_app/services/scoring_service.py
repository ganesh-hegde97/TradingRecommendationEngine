"""Pure domain scoring: Stock objects in, Recommendation objects out."""

from __future__ import annotations

from python_app.config.logging_config import logger
from python_app.core.constants import (
    FACTORS,
    HIGH_DEBT_TO_EQUITY,
    MIN_ROE,
    MIN_SCORE,
    MIN_VOLUME_RATIO,
)
from python_app.models import Recommendation, Stock


class ScoringService:
    def score_candidates(self, candidates: list[Stock]) -> list[Recommendation]:
        logger.info("Scoring %d candidate stocks", len(candidates))
        recommendations = [self._score(stock) for stock in candidates]
        return sorted(recommendations, key=lambda item: item.score, reverse=True)

    def _score(self, stock: Stock) -> Recommendation:
        factor_scores = {
            factor.key: round(
                factor.weight
                * self._normalise(
                    getattr(stock, factor.key),
                    factor.low,
                    factor.high,
                    factor.key == "debt_to_equity",
                ),
                2,
            )
            for factor in FACTORS
        }
        missing = [
            field
            for field in (
                "symbol",
                "company_name",
                "sector",
                "last_price",
                *(factor.key for factor in FACTORS),
            )
            if getattr(stock, field) in (None, "")
        ]
        reasons: list[str] = []
        if missing:
            reasons.append("Missing required data")
        if (stock.debt_to_equity or 0) > HIGH_DEBT_TO_EQUITY:
            reasons.append("High leverage")
        if (stock.roe_pct or 0) < MIN_ROE:
            reasons.append("Low ROE")
        if (stock.volume_ratio or 0) < MIN_VOLUME_RATIO:
            reasons.append("Below-average volume")
        if (stock.return_1m_pct or 0) <= 0 or (stock.return_3m_pct or 0) <= 0:
            reasons.append("Momentum not positive")
        if (stock.price_vs_50dma_pct or 0) <= 0 or (
            stock.price_vs_200dma_pct or 0
        ) <= 0:
            reasons.append("Trend not positive")
        score = round(sum(factor_scores.values()), 2)
        eligible = (
            not missing
            and score >= MIN_SCORE
            and all(
                (
                    stock.return_1m_pct > 0,
                    stock.return_3m_pct > 0,
                    stock.price_vs_50dma_pct > 0,
                    stock.price_vs_200dma_pct > 0,
                    stock.volume_ratio >= MIN_VOLUME_RATIO,
                )
            )
        )
        return Recommendation(
            stock=stock,
            score=score,
            decision="RECOMMEND" if eligible else "WATCH / EXCLUDE",
            confidence=round(score if not missing else score * 0.5, 2),
            reasons=tuple(reasons),
            factor_scores=factor_scores,
            eligible=eligible,
        )

    @staticmethod
    def _normalise(
        value: float | None, low: float, high: float, inverse: bool = False
    ) -> float:
        if value is None:
            return 0.0
        scaled = max(0.0, min(1.0, (value - low) / (high - low)))
        return 1 - scaled if inverse else scaled
