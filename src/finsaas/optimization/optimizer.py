"""Top-level optimizer orchestrator."""

from __future__ import annotations

import structlog
from typing import Any

from finsaas.data.feed import DataFeed
from finsaas.engine.runner import BacktestConfig
from finsaas.optimization.genetic import GeneticOptimizer
from finsaas.optimization.grid import GridSearchOptimizer
from finsaas.optimization.objective import get_objective
from finsaas.optimization.result import OptimizationResult
from finsaas.optimization.space import ParameterSpace

logger = structlog.get_logger()


def run_optimization(
    strategy_cls: type,
    feed: DataFeed,
    config: BacktestConfig,
    method: str = "grid",
    objective: str = "sharpe",
    max_workers: int = 1,
    generations: int = 50,
    population_size: int = 50,
    seed: int | None = None,
    **kwargs: Any,
) -> OptimizationResult:
    """Run parameter optimization.

    Args:
        strategy_cls: The Strategy class to optimize.
        feed: Data feed with OHLCV bars.
        config: Backtest configuration.
        method: Optimization method ("grid" or "genetic").
        objective: Objective function name.
        max_workers: Number of parallel workers.
        generations: Number of generations (genetic only).
        population_size: Population size (genetic only).
        seed: Random seed (genetic only, for reproducibility).

    Returns:
        OptimizationResult with best parameters and all trial results.
    """
    obj_fn = get_objective(objective)
    space = ParameterSpace.from_strategy(strategy_cls)

    logger.info(
        "optimization_start",
        method=method,
        objective=objective,
        total_combinations=space.total_combinations,
        dimensions=space.dimension_names,
    )

    if method == "grid":
        optimizer = GridSearchOptimizer(
            strategy_cls=strategy_cls,
            feed=feed,
            config=config,
            objective=obj_fn,
            space=space,
            max_workers=max_workers,
        )
    elif method == "genetic":
        optimizer = GeneticOptimizer(  # type: ignore[assignment]
            strategy_cls=strategy_cls,
            feed=feed,
            config=config,
            objective=obj_fn,
            space=space,
            population_size=population_size,
            generations=generations,
            seed=seed,
        )
    else:
        raise ValueError(f"Unknown optimization method: {method}")

    return optimizer.run()
