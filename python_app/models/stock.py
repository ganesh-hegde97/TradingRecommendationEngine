"""Domain model for normalized market data."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Stock:
    symbol: str
    company_name: str
    sector: str
    last_price: float | None
    market_cap_cr: float | None
    volume_ratio: float | None
    return_1m_pct: float | None
    return_3m_pct: float | None
    price_vs_50dma_pct: float | None
    price_vs_200dma_pct: float | None
    revenue_growth_yoy_pct: float | None
    profit_growth_yoy_pct: float | None
    roe_pct: float | None
    debt_to_equity: float | None
    source_url: str = ""
    as_of_date: str = ""

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "Stock":
        """Create a normalized Stock at the data-adapter boundary."""
        numeric_fields = (
            "last_price",
            "market_cap_cr",
            "volume_ratio",
            "return_1m_pct",
            "return_3m_pct",
            "price_vs_50dma_pct",
            "price_vs_200dma_pct",
            "revenue_growth_yoy_pct",
            "profit_growth_yoy_pct",
            "roe_pct",
            "debt_to_equity",
        )
        normalized = dict(values)
        for field in numeric_fields:
            try:
                value = float(normalized.get(field))
                normalized[field] = value if value == value else None
            except (TypeError, ValueError):
                normalized[field] = None
        return cls(
            symbol=str(normalized.get("symbol") or "").strip().upper(),
            company_name=str(normalized.get("company_name") or "").strip(),
            sector=str(normalized.get("sector") or "").strip(),
            source_url=str(normalized.get("source_url") or ""),
            as_of_date=str(normalized.get("as_of_date") or ""),
            **{field: normalized[field] for field in numeric_fields},
        )

    def to_mapping(self) -> dict[str, Any]:
        """Serialize only at an external/output boundary."""
        return asdict(self)
