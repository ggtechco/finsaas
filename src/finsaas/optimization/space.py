"""Parameter space definitions for optimization."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterator

from finsaas.strategy.parameters import (
    BoolParam,
    EnumParam,
    FloatParam,
    IntParam,
    ParamDescriptor,
)


@dataclass
class ParameterRange:
    """A single parameter's search range."""

    name: str
    values: list[Any]
    param_type: str  # "int", "float", "enum", "bool"

    def __len__(self) -> int:
        return len(self.values)


class ParameterSpace:
    """Defines the multi-dimensional parameter search space.

    Automatically extracted from Strategy class parameter descriptors.
    """

    def __init__(self, ranges: list[ParameterRange] | None = None) -> None:
        self._ranges = ranges or []

    @classmethod
    def from_strategy(cls, strategy_cls: type) -> ParameterSpace:
        """Extract parameter space from a Strategy class's descriptors."""
        ranges: list[ParameterRange] = []

        for name, desc in getattr(strategy_cls, "_param_descriptors", {}).items():
            if isinstance(desc, IntParam):
                vals = list(desc.range())
                ranges.append(ParameterRange(name=name, values=vals, param_type="int"))
            elif isinstance(desc, FloatParam):
                vals = _float_range(desc.min_val, desc.max_val, desc.step)
                ranges.append(ParameterRange(name=name, values=vals, param_type="float"))
            elif isinstance(desc, EnumParam):
                ranges.append(
                    ParameterRange(name=name, values=list(desc.choices), param_type="enum")
                )
            elif isinstance(desc, BoolParam):
                ranges.append(
                    ParameterRange(name=name, values=[True, False], param_type="bool")
                )

        return cls(ranges)

    @property
    def ranges(self) -> list[ParameterRange]:
        return list(self._ranges)

    @property
    def dimension_names(self) -> list[str]:
        return [r.name for r in self._ranges]

    @property
    def total_combinations(self) -> int:
        """Total number of parameter combinations for grid search."""
        if not self._ranges:
            return 0
        result = 1
        for r in self._ranges:
            result *= len(r)
        return result

    def grid_iter(self) -> Iterator[dict[str, Any]]:
        """Iterate over all combinations (for grid search)."""
        if not self._ranges:
            yield {}
            return

        names = [r.name for r in self._ranges]
        value_lists = [r.values for r in self._ranges]

        for combo in itertools.product(*value_lists):
            yield dict(zip(names, combo))

    def random_sample(self) -> dict[str, Any]:
        """Generate a random parameter combination."""
        import random

        result: dict[str, Any] = {}
        for r in self._ranges:
            result[r.name] = random.choice(r.values)
        return result

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict (for DB storage)."""
        return {
            "ranges": [
                {
                    "name": r.name,
                    "values": [str(v) for v in r.values],
                    "param_type": r.param_type,
                }
                for r in self._ranges
            ],
            "total_combinations": self.total_combinations,
        }


def _float_range(
    min_val: Decimal | None,
    max_val: Decimal | None,
    step: Decimal,
) -> list[Decimal]:
    """Generate a list of Decimal values from min to max with given step."""
    if min_val is None or max_val is None:
        return [min_val or max_val or Decimal("0")]

    values: list[Decimal] = []
    current = min_val
    while current <= max_val:
        values.append(current)
        current += step
    return values
