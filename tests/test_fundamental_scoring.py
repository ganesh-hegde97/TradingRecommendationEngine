from python_app.fundamentals import (
    FundamentalMetrics,
    FundamentalScoringEngine,
    MarketCapClass,
)


def test_scores_complete_high_quality_fundamentals() -> None:
    metrics = FundamentalMetrics(
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
    assessment = FundamentalScoringEngine().assess(metrics)

    assert assessment.score >= 75
    assert assessment.grade == "STRONG FUNDAMENTALS"
    assert assessment.market_cap_class is MarketCapClass.LARGE
    assert assessment.data_complete
    assert assessment.risk_flags == ()


def test_flags_missing_and_risky_fundamentals() -> None:
    metrics = FundamentalMetrics(
        roe_pct=4,
        debt_to_equity=3,
        peg_ratio=4,
        eps_growth_pct=-5,
        revenue_growth_pct=-2,
        promoter_holding_pct=10,
        free_cash_flow_cr=-10,
        market_cap_cr=400,
    )
    assessment = FundamentalScoringEngine().assess(metrics)

    assert assessment.grade == "INCOMPLETE DATA"
    assert assessment.market_cap_class is MarketCapClass.MICRO
    assert "roce_pct" in assessment.missing_fields
    assert "High leverage" in assessment.risk_flags
    assert "Free cash flow is non-positive" in assessment.risk_flags


def test_market_cap_boundaries() -> None:
    engine = FundamentalScoringEngine()
    assert engine.market_cap_class(20_000) is MarketCapClass.LARGE
    assert engine.market_cap_class(5_000) is MarketCapClass.MID
    assert engine.market_cap_class(500) is MarketCapClass.SMALL
    assert engine.market_cap_class(None) is MarketCapClass.UNKNOWN
