"""Version 2.4 long-position risk management.

This module calculates a deterministic plan; it does not submit orders, guarantee fills,
or replace an investor's risk assessment.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor


@dataclass(frozen=True, slots=True)
class RiskSettings:
    """Risk-budget and price-level assumptions for one long trade plan."""

    capital: float
    risk_per_trade_pct: float = 1.0
    atr: float | None = None
    support_price: float | None = None
    stop_loss_pct: float = 8.0
    stop_atr_multiplier: float = 1.5
    trailing_atr_multiplier: float = 1.0
    target_r_multiples: tuple[float, float, float] = (1.5, 2.0, 3.0)


@dataclass(frozen=True, slots=True)
class RiskPlan:
    entry: float
    stop_loss: float
    trailing_stop: float
    target_1: float
    target_2: float
    target_3: float
    risk_pct: float
    reward_pct: float
    risk_reward_ratio: float
    position_size: int
    position_value: float
    capital_at_risk: float
    risk_budget: float

    def as_display_dict(self) -> dict[str, str | int | float]:
        """Stable labels for a future UI, API response, or workbook sheet."""
        return {
            "Entry": self.entry,
            "Stop Loss": self.stop_loss,
            "Trailing Stop": self.trailing_stop,
            "Target 1": self.target_1,
            "Target 2": self.target_2,
            "Target 3": self.target_3,
            "Risk %": f"{self.risk_pct:.2f}%",
            "Reward %": f"{self.reward_pct:.2f}%",
            "Risk/Reward ratio": f"1:{self.risk_reward_ratio:.2f}",
            "Position size": self.position_size,
            "Position value": self.position_value,
            "Capital at risk": self.capital_at_risk,
            "Risk budget": self.risk_budget,
        }


class RiskManagementEngine:
    """Create a cash-only long-position plan from an entry price and risk settings."""

    def plan(self, entry: float, settings: RiskSettings) -> RiskPlan:
        self._validate(entry, settings)
        stop_loss = self._stop_loss(entry, settings)
        risk_per_share = entry - stop_loss
        trailing_stop = self._trailing_stop(entry, stop_loss, settings)
        target_1, target_2, target_3 = tuple(
            entry + risk_per_share * multiple
            for multiple in settings.target_r_multiples
        )
        risk_budget = settings.capital * settings.risk_per_trade_pct / 100
        # Never exceed either the cash risk budget or available capital (no leverage).
        position_size = floor(
            min(risk_budget / risk_per_share, settings.capital / entry)
        )
        position_value = round(position_size * entry, 2)
        capital_at_risk = round(position_size * risk_per_share, 2)
        reward_pct = (target_3 - entry) / entry * 100
        return RiskPlan(
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            trailing_stop=round(trailing_stop, 2),
            target_1=round(target_1, 2),
            target_2=round(target_2, 2),
            target_3=round(target_3, 2),
            risk_pct=round(risk_per_share / entry * 100, 2),
            reward_pct=round(reward_pct, 2),
            risk_reward_ratio=round((target_3 - entry) / risk_per_share, 2),
            position_size=position_size,
            position_value=position_value,
            capital_at_risk=capital_at_risk,
            risk_budget=round(risk_budget, 2),
        )

    @staticmethod
    def _stop_loss(entry: float, settings: RiskSettings) -> float:
        percentage_stop = entry * (1 - settings.stop_loss_pct / 100)
        atr_stop = (
            entry - settings.atr * settings.stop_atr_multiplier
            if settings.atr
            else percentage_stop
        )
        # When supplied, support is respected only if it creates a valid stop below entry.
        candidates = [percentage_stop, atr_stop]
        if settings.support_price is not None and 0 < settings.support_price < entry:
            candidates.append(settings.support_price)
        return min(candidates)

    @staticmethod
    def _trailing_stop(entry: float, stop_loss: float, settings: RiskSettings) -> float:
        if settings.atr:
            # Initial trailing stop is deliberately not below the protective stop.
            return max(
                stop_loss, entry - settings.atr * settings.trailing_atr_multiplier
            )
        return stop_loss

    @staticmethod
    def _validate(entry: float, settings: RiskSettings) -> None:
        if entry <= 0:
            raise ValueError("entry must be positive")
        if settings.capital <= 0:
            raise ValueError("capital must be positive")
        if not 0 < settings.risk_per_trade_pct <= 100:
            raise ValueError("risk_per_trade_pct must be between 0 and 100")
        if not 0 < settings.stop_loss_pct < 100:
            raise ValueError("stop_loss_pct must be between 0 and 100")
        if settings.atr is not None and settings.atr <= 0:
            raise ValueError("atr must be positive when supplied")
        if any(multiplier <= 0 for multiplier in settings.target_r_multiples):
            raise ValueError("target risk multiples must be positive")
        if tuple(sorted(settings.target_r_multiples)) != settings.target_r_multiples:
            raise ValueError("target risk multiples must be ascending")
