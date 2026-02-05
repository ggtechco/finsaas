"""Objective functions for optimization."""

from __future__ import annotations

import abc
from decimal import Decimal

from finsaas.engine.runner import BacktestResult


class ObjectiveFunction(abc.ABC):
    """Base class for optimization objective functions."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the objective."""

    @property
    def maximize(self) -> bool:
        """Whether to maximize (True) or minimize (False)."""
        return True

    @abc.abstractmethod
    def evaluate(self, result: BacktestResult) -> Decimal:
        """Evaluate the backtest result and return the objective value."""


class SharpeObjective(ObjectiveFunction):
    @property
    def name(self) -> str:
        return "sharpe"

    def evaluate(self, result: BacktestResult) -> Decimal:
        return result.metrics.get("sharpe_ratio", Decimal("0"))


class SortinoObjective(ObjectiveFunction):
    @property
    def name(self) -> str:
        return "sortino"

    def evaluate(self, result: BacktestResult) -> Decimal:
        return result.metrics.get("sortino_ratio", Decimal("0"))


class ReturnObjective(ObjectiveFunction):
    @property
    def name(self) -> str:
        return "return"

    def evaluate(self, result: BacktestResult) -> Decimal:
        return result.metrics.get("total_return_pct", Decimal("0"))


class MaxDrawdownObjective(ObjectiveFunction):
    """Minimize maximum drawdown."""

    @property
    def name(self) -> str:
        return "max_dd"

    @property
    def maximize(self) -> bool:
        return False

    def evaluate(self, result: BacktestResult) -> Decimal:
        return result.metrics.get("max_drawdown_pct", Decimal("0"))


class ProfitFactorObjective(ObjectiveFunction):
    @property
    def name(self) -> str:
        return "profit_factor"

    def evaluate(self, result: BacktestResult) -> Decimal:
        return result.metrics.get("profit_factor", Decimal("0"))


class CalmarObjective(ObjectiveFunction):
    @property
    def name(self) -> str:
        return "calmar"

    def evaluate(self, result: BacktestResult) -> Decimal:
        return result.metrics.get("calmar_ratio", Decimal("0"))


OBJECTIVES: dict[str, type[ObjectiveFunction]] = {
    "sharpe": SharpeObjective,
    "sortino": SortinoObjective,
    "return": ReturnObjective,
    "max_dd": MaxDrawdownObjective,
    "profit_factor": ProfitFactorObjective,
    "calmar": CalmarObjective,
}


def get_objective(name: str) -> ObjectiveFunction:
    """Get an objective function by name."""
    if name not in OBJECTIVES:
        raise ValueError(f"Unknown objective '{name}'. Available: {list(OBJECTIVES.keys())}")
    return OBJECTIVES[name]()
