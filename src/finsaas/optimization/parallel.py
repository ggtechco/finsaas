"""Multiprocessing management for parallel optimization."""

from __future__ import annotations

import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from decimal import Decimal
from typing import Any, Callable

import structlog

from finsaas.optimization.result import TrialResult

logger = structlog.get_logger()


def run_parallel_trials(
    trial_fn: Callable[[dict[str, Any], int], TrialResult],
    param_sets: list[dict[str, Any]],
    max_workers: int = 1,
) -> list[TrialResult]:
    """Run optimization trials in parallel.

    Args:
        trial_fn: Function that takes (params, trial_index) and returns TrialResult.
        param_sets: List of parameter combinations to evaluate.
        max_workers: Number of parallel workers.

    Returns:
        List of TrialResults.
    """
    if max_workers <= 1:
        # Sequential execution (deterministic order)
        results: list[TrialResult] = []
        for i, params in enumerate(param_sets):
            result = trial_fn(params, i)
            results.append(result)
            if (i + 1) % 10 == 0:
                logger.info("trial_progress", completed=i + 1, total=len(param_sets))
        return results

    # Parallel execution
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(trial_fn, params, i): i
            for i, params in enumerate(param_sets)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error("trial_failed", trial_index=idx, error=str(e))
                results.append(TrialResult(
                    trial_index=idx,
                    parameters=param_sets[idx],
                    objective_value=Decimal("-999"),
                ))

    # Sort by trial index for deterministic ordering
    results.sort(key=lambda r: r.trial_index)
    return results
