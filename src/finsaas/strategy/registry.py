"""Strategy registry - discover and instantiate strategies by name."""

from __future__ import annotations

from typing import Any

from finsaas.core.errors import StrategyError

_REGISTRY: dict[str, type] = {}


def register_strategy(cls: type) -> type:
    """Register a strategy class in the global registry."""
    name = cls.__name__
    _REGISTRY[name] = cls
    return cls


def get_strategy(name: str) -> type:
    """Get a registered strategy class by name."""
    if name not in _REGISTRY:
        raise StrategyError(
            f"Strategy '{name}' not found. Available: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[name]


def list_strategies() -> list[str]:
    """List all registered strategy names."""
    return list(_REGISTRY.keys())


def create_strategy(name: str, **params: Any) -> object:
    """Create an instance of a registered strategy with given parameters."""
    cls = get_strategy(name)
    instance = cls()
    for key, value in params.items():
        if hasattr(instance, key):
            setattr(instance, key, value)
        else:
            raise StrategyError(f"Strategy '{name}' has no parameter '{key}'")
    return instance
