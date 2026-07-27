"""Scoring Service

Responsible for calculating recommendation scores for stocks.
This service contains no UI or data download logic.
"""

from __future__ import annotations
from typing import Any
from python_app.config.logging_config import logger
from python_app.core.constants import (
    FACTORS,
    REQUIRED_FIELDS,
    HIGH_DEBT_TO_EQUITY,
    MIN_ROE,
    MIN_VOLUME_RATIO,
    MIN_SCORE,
)
from python_app.models import recommendation


class ScoringService:
    """Calculates recommendation scores for candidate stocks."""

    def score_candidates(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Calculate explainable scores for all candidate stocks."""
        logger.info("Scoring %d candidate stocks", len(candidates))
        results: list[dict[str, Any]] = []
        for raw in candidates:
            row = self._prepare_candidate(raw)
            factor_scores = self._calculate_factor_scores(row)
            row.update(factor_scores)
            recommendation.score = round(sum(factor_scores.values()), 2)
            flags = self._build_risk_flags(row)
            row["eligible"] = self._is_eligible(row)
            recommendation.decision = (
                "RECOMMEND" if row["eligible"] else "WATCH / EXCLUDE"
            )
            row["risk_flags"] = "; ".join(flags) if flags else "None"
            results.append(row)
        logger.info("Completed scoring")
        return sorted(
            results,
            key=lambda item: item["score"],
            reverse=True,
        )

    ####################################################################
    # Private Methods
    ####################################################################

    def _prepare_candidate(
        self,
        raw: dict[str, Any],
    ) -> dict[str, Any]:
        row = dict(raw)
        for key in REQUIRED_FIELDS:
            if key not in {"symbol", "company_name", "sector"}:
                row[key] = self._number(row.get(key))
        row["market_cap_cr"] = self._number(row.get("market_cap_cr"))
        missing = [key for key in REQUIRED_FIELDS if row.get(key) in (None, "")]
        row["data_complete"] = not missing
        row["missing_fields"] = ", ".join(missing)
        return row

    def _calculate_factor_scores(
        self,
        row: dict[str, Any],
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        for factor in FACTORS:
            scores[f"score_{factor.key}"] = round(
                factor.weight
                * self._normalise(
                    row.get(factor.key),
                    factor.low,
                    factor.high,
                    factor.key == "debt_to_equity",
                ),
                2,
            )
        return scores

    def _build_risk_flags(
        self,
        row: dict[str, Any],
    ) -> list[str]:
        flags: list[str] = []
        if not row["data_complete"]:
            flags.append("Missing required data")
        if (row["debt_to_equity"] or 0) > HIGH_DEBT_TO_EQUITY:
            flags.append("High leverage")
        if (row["roe_pct"] or 0) < MIN_ROE:
            flags.append("Low ROE")
        if (row["volume_ratio"] or 0) < MIN_VOLUME_RATIO:
            flags.append("Below-average volume")
        if (row["return_1m_pct"] or 0) <= 0 or (row["return_3m_pct"] or 0) <= 0:
            flags.append("Momentum not positive")
        if (row["price_vs_50dma_pct"] or 0) <= 0 or (
            row["price_vs_200dma_pct"] or 0
        ) <= 0:
            flags.append("Trend not positive")
        return flags

    def _is_eligible(
        self,
        row: dict[str, Any],
    ) -> bool:
        return bool(
            row["data_complete"]
            and row["score"] >= MIN_SCORE
            and row["return_1m_pct"] > 0
            and row["return_3m_pct"] > 0
            and row["price_vs_50dma_pct"] > 0
            and row["price_vs_200dma_pct"] > 0
            and row["volume_ratio"] >= MIN_VOLUME_RATIO
        )

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            value = float(value)
            return value if value == value else None
        except (TypeError, ValueError):

            return None

    @staticmethod
    def _normalise(
        value: float | None,
        low: float,
        high: float,
        inverse: bool = False,
    ) -> float:
        if value is None:
            return 0.0
        scaled = max(
            0.0,
            min(
                1.0,
                (value - low) / (high - low),
            ),
        )
        return 1 - scaled if inverse else scaled
