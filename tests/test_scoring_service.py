from python_app.models import Stock
from python_app.services.scoring_service import ScoringService


def _stock(**overrides: object) -> Stock:
    values = {
        "symbol": "TEST",
        "company_name": "Test Ltd",
        "sector": "Technology",
        "last_price": 100.0,
        "market_cap_cr": 1000.0,
        "volume_ratio": 1.4,
        "return_1m_pct": 8.0,
        "return_3m_pct": 18.0,
        "price_vs_50dma_pct": 6.0,
        "price_vs_200dma_pct": 12.0,
        "revenue_growth_yoy_pct": 18.0,
        "profit_growth_yoy_pct": 20.0,
        "roe_pct": 18.0,
        "debt_to_equity": 0.4,
    }
    values.update(overrides)
    return Stock(**values)


def test_scoring_returns_typed_recommendation() -> None:
    recommendation = ScoringService().score_candidates([_stock()])[0]
    assert recommendation.stock.symbol == "TEST"
    assert recommendation.eligible is True
    assert recommendation.decision == "RECOMMEND"
    assert recommendation.score > 65


def test_missing_input_is_not_eligible() -> None:
    recommendation = ScoringService().score_candidates([_stock(roe_pct=None)])[0]
    assert recommendation.eligible is False
    assert "Missing required data" in recommendation.reasons
