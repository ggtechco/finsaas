"""Genetic algorithm optimizer using DEAP."""

from __future__ import annotations

import random
import structlog
from decimal import Decimal
from typing import Any

from finsaas.data.feed import DataFeed
from finsaas.engine.runner import BacktestConfig, BacktestRunner
from finsaas.optimization.objective import ObjectiveFunction
from finsaas.optimization.result import OptimizationResult, TrialResult
from finsaas.optimization.space import ParameterSpace

logger = structlog.get_logger()


class GeneticOptimizer:
    """Genetic algorithm-based optimizer using DEAP.

    Uses evolutionary strategies to efficiently search the parameter space.
    """

    def __init__(
        self,
        strategy_cls: type,
        feed: DataFeed,
        config: BacktestConfig,
        objective: ObjectiveFunction,
        space: ParameterSpace,
        population_size: int = 50,
        generations: int = 50,
        crossover_prob: float = 0.7,
        mutation_prob: float = 0.2,
        seed: int | None = None,
    ) -> None:
        self._strategy_cls = strategy_cls
        self._feed = feed
        self._config = config
        self._objective = objective
        self._space = space
        self._pop_size = population_size
        self._generations = generations
        self._cx_prob = crossover_prob
        self._mut_prob = mutation_prob
        self._seed = seed
        self._all_trials: list[TrialResult] = []
        self._trial_counter = 0

    def run(self) -> OptimizationResult:
        """Run the genetic optimization."""
        from deap import algorithms, base, creator, tools

        if self._seed is not None:
            random.seed(self._seed)

        ranges = self._space.ranges
        if not ranges:
            raise ValueError("No parameter ranges defined for optimization")

        # Setup DEAP
        if hasattr(creator, "FitnessMax"):
            del creator.FitnessMax  # type: ignore[attr-defined]
        if hasattr(creator, "Individual"):
            del creator.Individual  # type: ignore[attr-defined]

        weight = 1.0 if self._objective.maximize else -1.0
        creator.create("FitnessMax", base.Fitness, weights=(weight,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()

        # Gene generators for each parameter
        for i, r in enumerate(ranges):
            toolbox.register(f"attr_{i}", random.choice, r.values)

        def create_individual() -> Any:
            genes = [toolbox.__getattribute__(f"attr_{i}")() for i in range(len(ranges))]
            return creator.Individual(genes)

        toolbox.register("individual", create_individual)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("evaluate", self._evaluate_individual)
        toolbox.register("mate", self._crossover)
        toolbox.register("mutate", self._mutate)
        toolbox.register("select", tools.selTournament, tournsize=3)

        # Run evolution
        pop = toolbox.population(n=self._pop_size)
        logger.info("genetic_start", population=self._pop_size,
                     generations=self._generations)

        for gen in range(self._generations):
            # Evaluate fitness for individuals without fitness
            invalid = [ind for ind in pop if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid)
            for ind, fit in zip(invalid, fitnesses):
                ind.fitness.values = fit

            # Select next generation
            offspring = toolbox.select(pop, len(pop))
            offspring = list(map(toolbox.clone, offspring))

            # Crossover
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < self._cx_prob:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # Mutation
            for mutant in offspring:
                if random.random() < self._mut_prob:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            pop = offspring

            # Log progress
            fits = [ind.fitness.values[0] for ind in pop if ind.fitness.valid]
            if fits:
                best_gen = max(fits) if self._objective.maximize else min(fits)
                logger.debug("generation_complete", gen=gen, best=f"{best_gen:.4f}")

        # Final evaluation
        for ind in pop:
            if not ind.fitness.valid:
                ind.fitness.values = toolbox.evaluate(ind)

        # Find best
        if self._objective.maximize:
            best_ind = max(pop, key=lambda ind: ind.fitness.values[0])
        else:
            best_ind = min(pop, key=lambda ind: ind.fitness.values[0])

        best_params = self._genes_to_params(best_ind)
        best_value = Decimal(str(best_ind.fitness.values[0]))

        logger.info("genetic_complete", best_value=str(best_value),
                     best_params=best_params, total_evaluations=self._trial_counter)

        return OptimizationResult(
            method="genetic",
            objective_name=self._objective.name,
            total_trials=self._trial_counter,
            best_params=best_params,
            best_value=best_value,
            all_trials=self._all_trials,
        )

    def _evaluate_individual(self, individual: list) -> tuple[float]:
        """Evaluate a single individual (DEAP requires tuple return)."""
        params = self._genes_to_params(individual)

        strategy = self._strategy_cls()
        strategy.set_parameters(params)

        runner = BacktestRunner(self._feed, self._config)
        result = runner.run(strategy)
        obj_value = self._objective.evaluate(result)

        trial = TrialResult(
            trial_index=self._trial_counter,
            parameters=params,
            objective_value=obj_value,
            metrics=result.metrics,
            run_hash=result.run_hash,
        )
        self._all_trials.append(trial)
        self._trial_counter += 1

        return (float(obj_value),)

    def _genes_to_params(self, individual: list) -> dict[str, Any]:
        """Convert gene values to parameter dict."""
        ranges = self._space.ranges
        return {ranges[i].name: individual[i] for i in range(len(ranges))}

    def _crossover(self, ind1: list, ind2: list) -> tuple[list, list]:
        """Uniform crossover."""
        for i in range(len(ind1)):
            if random.random() < 0.5:
                ind1[i], ind2[i] = ind2[i], ind1[i]
        return ind1, ind2

    def _mutate(self, individual: list) -> tuple[list]:
        """Mutate by randomly replacing a gene with a valid value."""
        ranges = self._space.ranges
        idx = random.randrange(len(individual))
        individual[idx] = random.choice(ranges[idx].values)
        return (individual,)
