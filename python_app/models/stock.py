from dataclasses import dataclass


@dataclass
class Stock:
    symbol: str
    company_name: str
    sector: str
    last_price: float
    volume_ratio: float | None
    return_1m_pct: float | None
    return_3m_pct: float | None
    return_6m_pct: float | None
    price_vs_50dma_pct: float | None
    pe_ratio: float | None
    roe: float | None
    debt_to_equity: float | None
    market_cap: float | None
