from dataclasses import dataclass

from python_app.models.factor import Factor


@dataclass(frozen=True)
class RecommendationThresholds:
    """Recommendation score thresholds."""

    STRONG_BUY = 90
    BUY = 75
    HOLD = 55
    SELL = 35


@dataclass(frozen=True)
class ExcelSheets:
    SUMMARY = "Summary"
    RECOMMENDATIONS = "Recommendations"


@dataclass(frozen=True)
class Rating:
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


@dataclass(frozen=True)
class Defaults:
    UNKNOWN = "N/A"
    SECTOR_UNKNOWN = "Unknown"
    MAX_RETRIES = 3


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

REQUIRED_FIELDS = (
    "symbol",
    "company_name",
    "sector",
    "last_price",
    *(factor.key for factor in FACTORS),
)

HIGH_DEBT_TO_EQUITY = 1.5
MIN_ROE = 10
MIN_VOLUME_RATIO = 1
MIN_SCORE = 65

thresholds = RecommendationThresholds()
rating = Rating()
excel = ExcelSheets()
defaults = Defaults()
