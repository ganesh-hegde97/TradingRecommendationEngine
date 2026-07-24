"""Transparent scoring rules shared by the desktop UI and Excel export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Factor:
    name: str
    key: str
    weight: float
    low: float
    high: float


FACTORS = (
    Factor("1-month momentum", "return_1m_pct", 18, -5, 15),
    Factor("3-month momentum", "return_3m_pct", 18, -10, 35),
    Factor("Price vs 50DMA", "price_vs_50dma_pct", 12, -5, 12),
    Factor("Price vs 200DMA", "price_vs_200dma_pct", 12, -10, 25),
    Factor("Revenue growth YoY", "revenue_growth_yoy_pct", 12, -5, 25),
    Factor("Profit growth YoY", "profit_growth_yoy_pct", 10, -10, 30),
    Factor("Return on equity", "roe_pct", 8, 5, 25),
    Factor("Debt to equity", "debt_to_equity", 5, 0, 2),
    Factor("Volume ratio", "volume_ratio", 5, 0.7, 2),
)
REQUIRED = ("symbol", "company_name", "sector", "last_price", *(factor.key for factor in FACTORS))


def _number(value: Any) -> float | None:
    try:
        value = float(value)
        return value if value == value else None  # rejects NaN
    except (TypeError, ValueError):
        return None


def _normalise(value: float | None, low: float, high: float, inverse: bool = False) -> float:
    if value is None:
        return 0.0
    scaled = max(0.0, min(1.0, (value - low) / (high - low)))
    return 1 - scaled if inverse else scaled


def score_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate explainable scores. Percent input fields use percentage points, e.g. 12.5."""
    results: list[dict[str, Any]] = []
    for raw in candidates:
        row = dict(raw)
        for key in REQUIRED:
            if key not in {"symbol", "company_name", "sector"}:
                row[key] = _number(row.get(key))
        row["market_cap_cr"] = _number(row.get("market_cap_cr"))
        missing = [key for key in REQUIRED if row.get(key) in (None, "")]
        row["data_complete"] = not missing
        row["missing_fields"] = ", ".join(missing)
        factor_scores = {}
        for factor in FACTORS:
            factor_scores[f"score_{factor.key}"] = round(
                factor.weight * _normalise(row[factor.key], factor.low, factor.high, factor.key == "debt_to_equity"), 2
            )
        row.update(factor_scores)
        row["score"] = round(sum(factor_scores.values()), 2)
        flags: list[str] = []
        if missing:
            flags.append("Missing required data")
        if (row["debt_to_equity"] or 0) > 1.5:
            flags.append("High leverage")
        if (row["roe_pct"] or 0) < 10:
            flags.append("Low ROE")
        if (row["volume_ratio"] or 0) < 1:
            flags.append("Below-average volume")
        if (row["return_1m_pct"] or 0) <= 0 or (row["return_3m_pct"] or 0) <= 0:
            flags.append("Momentum not positive")
        if (row["price_vs_50dma_pct"] or 0) <= 0 or (row["price_vs_200dma_pct"] or 0) <= 0:
            flags.append("Trend not positive")
        row["eligible"] = bool(
            row["data_complete"] and row["score"] >= 65 and row["return_1m_pct"] > 0 and row["return_3m_pct"] > 0
            and row["price_vs_50dma_pct"] > 0 and row["price_vs_200dma_pct"] > 0 and row["volume_ratio"] >= 1
        )
        row["decision"] = "RECOMMEND" if row["eligible"] else "WATCH / EXCLUDE"
        row["risk_flags"] = "; ".join(flags) or "None"
        results.append(row)
    return sorted(results, key=lambda item: item["score"], reverse=True)
