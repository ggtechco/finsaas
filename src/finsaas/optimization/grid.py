"""Grid search optimizer."""

from __future__ import annotations

import structlog
from decimal import Decimal
from typing import Any

from finsaas.data.feed import DataFeed
from finsaas.engine.runner import BacktestConfig, BacktestRunner
from finsaas.optimization.objective import ObjectiveFunction
from finsaas.optimization.parallel import run_parallel_trials
from finsaas.optimization.result import OptimizationResult, TrialResult
from finsaas.optimization.space import ParameterSpace

logger = structlog.get_logger()


class GridSearchOptimizer:
    """Exhaustive grid search over all parameter combinations."""

    def __init__(
        self,
        strategy_cls: type,
        feed: DataFeed,
        config: BacktestConfig,
        objective: ObjectiveFunction,
        space: ParameterSpace,
        max_workers: int = 1,
    ) -> None:
        self._strategy_cls = strategy_cls
        self._feed = feed
        self._config = config
        self._objective = objective
        self._space = space
        self._max_workers = max_workers

    def run(self) -> OptimizationResult:
        """Run the grid search."""
        param_sets = list(self._space.grid_iter())
        total = len(param_sets)
        logger.info("grid_search_start", total_combinations=total)

        def trial_fn(params: dict[str, Any], index: int) -> TrialResult:
            return self._evaluate_trial(params, index)

        results = run_parallel_trials(
            trial_fn, param_sets, max_workers=self._max_workers
        )

        # Find best
        if self._objective.maximize:
            best = max(results, key=lambda r: r.objective_value)
        else:
            best = min(results, key=lambda r: r.objective_value)

        logger.info("grid_search_complete", best_value=str(best.objective_value),
                     best_params=best.parameters)

        return OptimizationResult(
            method="grid",
            objective_name=self._objective.name,
            total_trials=total,
            best_params=best.parameters,
            best_value=best.objective_value,
            all_trials=results,
        )

    def _evaluate_trial(
        self, params: dict[str, Any], trial_index: int
    ) -> TrialResult:
        """Run a single backtest with given parameters."""
        strategy = self._strategy_cls()
        strategy.set_parameters(params)

        runner = BacktestRunner(self._feed, self._config)
        result = runner.run(strategy)

        obj_value = self._objective.evaluate(result)

        return TrialResult(
            trial_index=trial_index,
            parameters=params,
            objective_value=obj_value,
            metrics=result.metrics,
            run_hash=result.run_hash,
        )
