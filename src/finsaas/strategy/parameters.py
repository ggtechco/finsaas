"""Strategy parameter descriptors for the Python DSL.

Parameters are defined as class attributes on Strategy subclasses
and support range/constraint definitions for optimization.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Generic, Sequence, TypeVar

T = TypeVar("T")


class ParamDescriptor:
    """Base class for strategy parameter descriptors."""

    def __init__(self, default: Any, description: str = "") -> None:
        self.default = default
        self.description = description
        self.name: str = ""  # Set by metaclass or registry

    def validate(self, value: Any) -> Any:
        """Validate and return the value."""
        return value

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return obj.__dict__.get(f"_param_{self.name}", self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        obj.__dict__[f"_param_{self.name}"] = self.validate(value)


class IntParam(ParamDescriptor):
    """Integer parameter with optional min/max range."""

    def __init__(
        self,
        default: int = 0,
        min_val: int | None = None,
        max_val: int | None = None,
        step: int = 1,
        description: str = "",
    ) -> None:
        super().__init__(default, description)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

    def validate(self, value: Any) -> int:
        value = int(value)
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"{self.name}: {value} < min {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"{self.name}: {value} > max {self.max_val}")
        return value

    def range(self) -> range:
        """Return the parameter range for optimization."""
        lo = self.min_val if self.min_val is not None else self.default
        hi = self.max_val if self.max_val is not None else self.default
        return range(lo, hi + 1, self.step)


class FloatParam(ParamDescriptor):
    """Float/Decimal parameter with optional min/max range."""

    def __init__(
        self,
        default: float | Decimal = 0.0,
        min_val: float | Decimal | None = None,
        max_val: float | Decimal | None = None,
        step: float | Decimal | None = None,
        description: str = "",
    ) -> None:
        super().__init__(Decimal(str(default)), description)
        self.min_val = Decimal(str(min_val)) if min_val is not None else None
        self.max_val = Decimal(str(max_val)) if max_val is not None else None
        self.step = Decimal(str(step)) if step is not None else Decimal("0.1")

    def validate(self, value: Any) -> Decimal:
        value = Decimal(str(value))
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"{self.name}: {value} < min {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"{self.name}: {value} > max {self.max_val}")
        return value


class EnumParam(ParamDescriptor):
    """Enumeration parameter - selects from a list of values."""

    def __init__(
        self,
        default: Any,
        choices: Sequence[Any] = (),
        description: str = "",
    ) -> None:
        super().__init__(default, description)
        self.choices = list(choices) if choices else [default]

    def validate(self, value: Any) -> Any:
        if value not in self.choices:
            raise ValueError(f"{self.name}: {value} not in {self.choices}")
        return value


class BoolParam(ParamDescriptor):
    """Boolean parameter."""

    def __init__(self, default: bool = False, description: str = "") -> None:
        super().__init__(default, description)

    def validate(self, value: Any) -> bool:
        return bool(value)
