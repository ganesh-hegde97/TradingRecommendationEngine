"""Domain model returned by the scoring layer."""

from dataclasses import dataclass

from python_app.models.stock import Stock


@dataclass(frozen=True, slots=True)
class Recommendation:
    stock: Stock
    score: float
    decision: str
    confidence: float
    reasons: tuple[str, ...]
    factor_scores: dict[str, float]
    eligible: bool

    @property
    def risk_flags(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "None"
