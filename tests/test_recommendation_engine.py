from python_app.fundamentals import FundamentalMetrics, FundamentalScoringEngine
from python_app.recommendations import RecommendationEngine, TechnicalSnapshot


def _fundamentals():
    return FundamentalScoringEngine().assess(
        FundamentalMetrics(
            roe_pct=24,
            roce_pct=23,
            debt_to_equity=0.2,
            peg_ratio=0.8,
            eps_growth_pct=24,
            revenue_growth_pct=22,
            operating_margin_pct=22,
            promoter_holding_pct=55,
            institutional_holding_pct=30,
            free_cash_flow_cr=1_500,
            market_cap_cr=45_000,
        )
    )


def test_returns_explainable_composite_recommendation() -> None:
    technical = TechnicalSnapshot(
        close=120,
        ema_20=115,
        ema_50=110,
        ema_200=100,
        rsi_14=64,
        macd=2,
        macd_signal=1,
        adx=31,
        supertrend_direction=1,
        return_1m_pct=10,
        return_3m_pct=24,
        volume_ratio=1.8,
        atr_pct=2.5,
    )
    recommendation = RecommendationEngine().recommend(technical, _fundamentals())

    assert recommendation.overall_score >= 85
    assert recommendation.recommendation == "STRONG BUY"
    assert recommendation.confidence_pct >= 80
    assert recommendation.technical_score > 80
    assert recommendation.as_display_dict()["Overall Score"].endswith("/100")
    assert any("MACD" in item for item in recommendation.explanation)


def test_low_data_confidence_is_not_actionable() -> None:
    recommendation = RecommendationEngine().recommend(
        TechnicalSnapshot(), _fundamentals()
    )

    assert recommendation.confidence_pct < 55
    assert recommendation.recommendation == "INSUFFICIENT CONFIDENCE"
    assert "Weak technical signal" in recommendation.risk_flags
