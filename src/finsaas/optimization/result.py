"""Optimization result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class TrialResult:
    """Result of a single optimization trial."""

    trial_index: int
    parameters: dict[str, Any]
    objective_value: Decimal
    metrics: dict[str, Decimal] = field(default_factory=dict)
    run_hash: str = ""


@dataclass
class OptimizationResult:
    """Complete result of an optimization run."""

    method: str
    objective_name: str
    total_trials: int
    best_params: dict[str, Any]
    best_value: Decimal
    all_trials: list[TrialResult] = field(default_factory=list)

    @property
    def top_trials(self) -> list[TrialResult]:
        """Return trials sorted by objective value (best first)."""
        return sorted(self.all_trials, key=lambda t: t.objective_value, reverse=True)
