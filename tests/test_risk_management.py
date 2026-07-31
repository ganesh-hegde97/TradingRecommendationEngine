import pytest

from python_app.risk import RiskManagementEngine, RiskSettings


def test_creates_cash_limited_atr_risk_plan() -> None:
    plan = RiskManagementEngine().plan(
        100,
        RiskSettings(capital=100_000, risk_per_trade_pct=1, atr=4),
    )

    assert plan.entry == 100
    assert plan.stop_loss == 92  # max of 8% and 1.5 ATR loss
    assert plan.trailing_stop == 96
    assert (plan.target_1, plan.target_2, plan.target_3) == (112, 116, 124)
    assert plan.risk_pct == 8
    assert plan.reward_pct == 24
    assert plan.risk_reward_ratio == 3
    assert plan.position_size == 125
    assert plan.capital_at_risk == 1_000
    assert plan.position_value <= 100_000


def test_position_size_never_exceeds_available_cash() -> None:
    plan = RiskManagementEngine().plan(
        100, RiskSettings(capital=500, risk_per_trade_pct=10, stop_loss_pct=1)
    )

    assert plan.position_size == 5
    assert plan.position_value == 500


def test_rejects_invalid_risk_inputs() -> None:
    with pytest.raises(ValueError, match="entry"):
        RiskManagementEngine().plan(0, RiskSettings(capital=1_000))
    with pytest.raises(ValueError, match="ascending"):
        RiskManagementEngine().plan(
            100, RiskSettings(capital=1_000, target_r_multiples=(2, 1, 3))
        )
