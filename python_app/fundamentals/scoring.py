"""Transparent fundamental-quality scoring for Indian listed equities.

The engine is intentionally independent of data retrieval and technical scoring. Input
data is normalized at its boundary and every score component remains inspectable.
Scores are research signals, not investment advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MarketCapClass(StrEnum):
    LARGE = "Large cap"
    MID = "Mid cap"
    SMALL = "Small cap"
    MICRO = "Micro cap"
    UNKNOWN = "Unknown"


@dataclass(frozen=True, slots=True)
class FundamentalMetrics:
    """Normalized annual or trailing-twelve-month fundamental inputs.

    Percentage values are stored as percentages, market cap and free cash flow as INR
    crore, and PEG as a plain ratio.
    """

    roe_pct: float | None = None
    roce_pct: float | None = None
    debt_to_equity: float | None = None
    peg_ratio: float | None = None
    eps_growth_pct: float | None = None
    revenue_growth_pct: float | None = None
    operating_margin_pct: float | None = None
    promoter_holding_pct: float | None = None
    institutional_holding_pct: float | None = None
    free_cash_flow_cr: float | None = None
    market_cap_cr: float | None = None

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "FundamentalMetrics":
        normalized: dict[str, float | None] = {}
        for field in cls.__dataclass_fields__:
            try:
                value = float(values.get(field))
                normalized[field] = value if value == value else None
            except (TypeError, ValueError):
                normalized[field] = None
        return cls(**normalized)


@dataclass(frozen=True, slots=True)
class FundamentalAssessment:
    score: float
    grade: str
    market_cap_class: MarketCapClass
    factor_scores: dict[str, float]
    risk_flags: tuple[str, ...]
    missing_fields: tuple[str, ...]

    @property
    def data_complete(self) -> bool:
        return not self.missing_fields


@dataclass(frozen=True, slots=True)
class _Factor:
    field: str
    label: str
    weight: float
    low: float
    high: float
    inverse: bool = False


class FundamentalScoringEngine:
    """Score fundamental quality on a transparent 100-point scale."""

    FACTORS = (
        _Factor("roe_pct", "ROE", 14, 8, 25),
        _Factor("roce_pct", "ROCE", 14, 8, 25),
        _Factor("debt_to_equity", "Debt / Equity", 12, 0, 2, inverse=True),
        _Factor("peg_ratio", "PEG ratio", 10, 0.5, 3, inverse=True),
        _Factor("eps_growth_pct", "EPS growth", 10, 0, 25),
        _Factor("revenue_growth_pct", "Revenue growth", 10, 0, 25),
        _Factor("operating_margin_pct", "Operating margin", 8, 5, 25),
        _Factor("promoter_holding_pct", "Promoter holding", 7, 25, 75),
        _Factor("institutional_holding_pct", "Institutional holding", 5, 5, 50),
        _Factor("free_cash_flow_cr", "Free cash flow", 10, 0, 1),
    )

    def assess(self, metrics: FundamentalMetrics) -> FundamentalAssessment:
        """Return a factor breakdown, quality grade, cap class, and review flags."""
        scores = {
            factor.field: round(
                factor.weight * self._normalise(getattr(metrics, factor.field), factor),
                2,
            )
            for factor in self.FACTORS
        }
        missing = tuple(
            factor.field
            for factor in self.FACTORS
            if getattr(metrics, factor.field) is None
        ) + (() if metrics.market_cap_cr is not None else ("market_cap_cr",))
        score = round(sum(scores.values()), 2)
        return FundamentalAssessment(
            score=score,
            grade=self._grade(score, bool(missing)),
            market_cap_class=self.market_cap_class(metrics.market_cap_cr),
            factor_scores=scores,
            risk_flags=tuple(self._risk_flags(metrics)),
            missing_fields=missing,
        )

    @staticmethod
    def market_cap_class(market_cap_cr: float | None) -> MarketCapClass:
        """Classify market capitalization using widely used India-oriented bands."""
        if market_cap_cr is None or market_cap_cr < 0:
            return MarketCapClass.UNKNOWN
        if market_cap_cr >= 20_000:
            return MarketCapClass.LARGE
        if market_cap_cr >= 5_000:
            return MarketCapClass.MID
        if market_cap_cr >= 500:
            return MarketCapClass.SMALL
        return MarketCapClass.MICRO

    @staticmethod
    def _normalise(value: float | None, factor: _Factor) -> float:
        if value is None:
            return 0.0
        # Positive free cash flow receives its full quality score; scale is not used
        # because absolute cash flow varies naturally with company size.
        if factor.field == "free_cash_flow_cr":
            return 1.0 if value > 0 else 0.0
        # Negative/zero PEG is not economically meaningful for valuation scoring.
        if factor.field == "peg_ratio" and value <= 0:
            return 0.0
        scaled = max(0.0, min(1.0, (value - factor.low) / (factor.high - factor.low)))
        return 1 - scaled if factor.inverse else scaled

    @staticmethod
    def _grade(score: float, incomplete: bool) -> str:
        if incomplete:
            return "INCOMPLETE DATA"
        if score >= 75:
            return "STRONG FUNDAMENTALS"
        if score >= 55:
            return "MODERATE FUNDAMENTALS"
        return "WEAK FUNDAMENTALS"

    @staticmethod
    def _risk_flags(metrics: FundamentalMetrics) -> list[str]:
        flags: list[str] = []
        if (metrics.debt_to_equity or 0) > 2:
            flags.append("High leverage")
        if metrics.peg_ratio is not None and (
            metrics.peg_ratio <= 0 or metrics.peg_ratio > 3
        ):
            flags.append("PEG requires valuation review")
        if (metrics.eps_growth_pct or 0) <= 0:
            flags.append("EPS growth is non-positive")
        if (metrics.revenue_growth_pct or 0) <= 0:
            flags.append("Revenue growth is non-positive")
        if metrics.free_cash_flow_cr is not None and metrics.free_cash_flow_cr <= 0:
            flags.append("Free cash flow is non-positive")
        if (metrics.promoter_holding_pct or 0) < 25:
            flags.append("Low promoter holding")
        return flags
