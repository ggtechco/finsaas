"""Decorators for strategy definition."""

from __future__ import annotations

from typing import Any, Callable


def parameter(
    name: str | None = None,
    default: Any = None,
    min_val: Any = None,
    max_val: Any = None,
    description: str = "",
) -> Callable:  # type: ignore[type-arg]
    """Decorator to declare a strategy parameter.

    Can be used as an alternative to the descriptor-based approach:

        @parameter(default=10, min_val=5, max_val=50)
        def fast_length(self):
            pass
    """

    def decorator(func: Callable) -> Callable:  # type: ignore[type-arg]
        param_name = name or func.__name__
        func._param_meta = {  # type: ignore[attr-defined]
            "name": param_name,
            "default": default,
            "min_val": min_val,
            "max_val": max_val,
            "description": description,
        }
        return func

    return decorator


def on_bar(func: Callable) -> Callable:  # type: ignore[type-arg]
    """Mark a method as the bar handler (alternative to overriding on_bar)."""
    func._is_bar_handler = True  # type: ignore[attr-defined]
    return func
