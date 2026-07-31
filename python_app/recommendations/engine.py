"""Version 2.3 composite recommendation engine.

The engine combines technical, fundamental, momentum, liquidity, and volatility
evidence into an explainable research score. It deliberately does not place orders or
provide personalised financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from python_app.fundamentals import FundamentalAssessment


@dataclass(frozen=True, slots=True)
class TechnicalSnapshot:
    """Latest technical observations used by the composite recommendation engine."""

    close: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    adx: float | None = None
    supertrend_direction: float | None = None
    return_1m_pct: float | None = None
    return_3m_pct: float | None = None
    volume_ratio: float | None = None
    atr_pct: float | None = None

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "TechnicalSnapshot":
        normalized: dict[str, float | None] = {}
        for field in cls.__dataclass_fields__:
            try:
                value = float(values.get(field))
                normalized[field] = value if value == value else None
            except (TypeError, ValueError):
                normalized[field] = None
        return cls(**normalized)


@dataclass(frozen=True, slots=True)
class CompositeRecommendation:
    overall_score: float
    technical_score: float
    fundamental_score: float
    momentum_score: float
    liquidity_score: float
    volatility_score: float
    confidence_pct: int
    recommendation: str
    explanation: tuple[str, ...]
    risk_flags: tuple[str, ...]

    def as_display_dict(self) -> dict[str, str | int | float | tuple[str, ...]]:
        """Return stable presentation labels for a UI, API, or Excel export."""
        return {
            "Overall Score": f"{self.overall_score:.0f}/100",
            "Technical": round(self.technical_score),
            "Fundamental": round(self.fundamental_score),
            "Momentum": round(self.momentum_score),
            "Liquidity": round(self.liquidity_score),
            "Volatility": round(self.volatility_score),
            "Confidence": f"{self.confidence_pct}%",
            "Recommendation": self.recommendation,
            "Explanation": self.explanation,
            "Risk Flags": self.risk_flags,
        }


class RecommendationEngine:
    """Combine independent research signals using documented, adjustable weights."""

    WEIGHTS = {
        "technical": 0.30,
        "fundamental": 0.30,
        "momentum": 0.18,
        "liquidity": 0.12,
        "volatility": 0.10,
    }

    def recommend(
        self,
        technical: TechnicalSnapshot,
        fundamentals: FundamentalAssessment,
    ) -> CompositeRecommendation:
        technical_score, technical_notes, technical_missing = self._technical(technical)
        momentum_score, momentum_notes, momentum_missing = self._momentum(technical)
        liquidity_score, liquidity_notes, liquidity_missing = self._liquidity(technical)
        volatility_score, volatility_notes, volatility_missing = self._volatility(
            technical
        )
        fundamental_score = fundamentals.score
        category_scores = {
            "technical": technical_score,
            "fundamental": fundamental_score,
            "momentum": momentum_score,
            "liquidity": liquidity_score,
            "volatility": volatility_score,
        }
        overall = round(
            sum(
                category_scores[name] * weight for name, weight in self.WEIGHTS.items()
            ),
            2,
        )
        flags = list(fundamentals.risk_flags)
        for name, score in category_scores.items():
            if score < 45:
                flags.append(f"Weak {name} signal")
        missing = (
            technical_missing
            + momentum_missing
            + liquidity_missing
            + volatility_missing
            + len(fundamentals.missing_fields)
        )
        confidence = self._confidence(category_scores, missing, len(flags))
        explanation = self._explanation(
            category_scores,
            technical_notes + momentum_notes + liquidity_notes + volatility_notes,
            fundamentals,
            flags,
        )
        return CompositeRecommendation(
            overall_score=overall,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            momentum_score=momentum_score,
            liquidity_score=liquidity_score,
            volatility_score=volatility_score,
            confidence_pct=confidence,
            recommendation=self._label(overall, confidence),
            explanation=tuple(explanation),
            risk_flags=tuple(dict.fromkeys(flags)),
        )

    @staticmethod
    def _technical(snapshot: TechnicalSnapshot) -> tuple[float, list[str], int]:
        checks = [
            (
                snapshot.close is not None
                and snapshot.ema_20 is not None
                and snapshot.close > snapshot.ema_20,
                "price is above the 20-day EMA",
            ),
            (
                snapshot.ema_20 is not None
                and snapshot.ema_50 is not None
                and snapshot.ema_20 > snapshot.ema_50,
                "20-day EMA is above the 50-day EMA",
            ),
            (
                snapshot.ema_50 is not None
                and snapshot.ema_200 is not None
                and snapshot.ema_50 > snapshot.ema_200,
                "50-day EMA is above the 200-day EMA",
            ),
            (
                snapshot.macd is not None
                and snapshot.macd_signal is not None
                and snapshot.macd > snapshot.macd_signal,
                "MACD is above its signal line",
            ),
            (
                snapshot.supertrend_direction is not None
                and snapshot.supertrend_direction > 0,
                "SuperTrend is bullish",
            ),
            (
                snapshot.adx is not None and snapshot.adx >= 25,
                "ADX confirms a meaningful trend",
            ),
        ]
        available = [passed for passed, _ in checks if passed or True]
        missing = sum(
            value is None
            for value in (
                snapshot.close,
                snapshot.ema_20,
                snapshot.ema_50,
                snapshot.ema_200,
                snapshot.macd,
                snapshot.macd_signal,
                snapshot.supertrend_direction,
                snapshot.adx,
            )
        )
        score = 100 * sum(passed for passed, _ in checks) / len(checks)
        return round(score, 2), [note for passed, note in checks if passed], missing

    @staticmethod
    def _momentum(snapshot: TechnicalSnapshot) -> tuple[float, list[str], int]:
        components = [
            (snapshot.return_1m_pct, 0, 12, "one-month return is positive"),
            (snapshot.return_3m_pct, 0, 30, "three-month return is positive"),
            (snapshot.rsi_14, 50, 70, "RSI shows constructive momentum"),
        ]
        values, notes, missing = [], [], 0
        for value, low, high, note in components:
            if value is None:
                missing += 1
                continue
            values.append(100 * max(0, min(1, (value - low) / (high - low))))
            if value >= low:
                notes.append(note)
        return round(sum(values) / len(values), 2) if values else 0.0, notes, missing

    @staticmethod
    def _liquidity(snapshot: TechnicalSnapshot) -> tuple[float, list[str], int]:
        if snapshot.volume_ratio is None:
            return 0.0, [], 1
        score = 100 * max(0, min(1, (snapshot.volume_ratio - 0.5) / 1.5))
        notes = (
            ["trading volume is above its recent average"]
            if snapshot.volume_ratio >= 1
            else []
        )
        return round(score, 2), notes, 0

    @staticmethod
    def _volatility(snapshot: TechnicalSnapshot) -> tuple[float, list[str], int]:
        if snapshot.atr_pct is None:
            return 0.0, [], 1
        score = 100 * max(0, min(1, (8 - snapshot.atr_pct) / 6))
        notes = (
            ["ATR indicates contained price volatility"]
            if snapshot.atr_pct <= 3
            else []
        )
        return round(score, 2), notes, 0

    @staticmethod
    def _confidence(scores: dict[str, float], missing: int, flags: int) -> int:
        spread_penalty = min(15, (max(scores.values()) - min(scores.values())) / 4)
        return max(0, min(100, round(100 - missing * 4 - flags * 2 - spread_penalty)))

    @staticmethod
    def _label(score: float, confidence: int) -> str:
        if confidence < 55:
            return "INSUFFICIENT CONFIDENCE"
        if score >= 85:
            return "STRONG BUY"
        if score >= 70:
            return "BUY"
        if score >= 55:
            return "HOLD"
        if score >= 40:
            return "SELL"
        return "STRONG SELL"

    @staticmethod
    def _explanation(
        scores: dict[str, float],
        notes: list[str],
        fundamentals: FundamentalAssessment,
        flags: list[str],
    ) -> list[str]:
        explanation = [
            f"{name.title()} scored {score:.0f}/100." for name, score in scores.items()
        ]
        explanation.extend(notes)
        explanation.append(
            f"Fundamental profile is {fundamentals.grade.lower()} and classified as {fundamentals.market_cap_class.value}."
        )
        if flags:
            explanation.append("Review risks: " + "; ".join(dict.fromkeys(flags)) + ".")
        return explanation
